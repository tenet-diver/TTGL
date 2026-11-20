"""Registered, resumable prompt-harness optimization over isolated Codex tasks."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import difflib
import fcntl
from pathlib import Path
import platform
import random
import subprocess

from ..experience_routing.io import canonical, digest, file_digest, now, read, write_new
from .benchmark import VERSION, evaluate, load_tasks
from .memory import CONDITIONS, memory_text, read_bank

ROOT = Path(__file__).resolve().parents[3]
MODEL = "gpt-6-luna"
HARNESS = {
    "planning": {
        "standard": "Inspect the requirements and existing implementation, then make a focused repair.",
        "contract": "Before editing, identify the invariants, edge cases and observable behavior specified by the task.",
        "counterexample": "Find an input that distinguishes the current and required behavior. Use it to guide a focused repair.",
        "direct": "Start with one bounded inspection of the task and source, then implement promptly.",
    },
    "verification": {
        "public": "Run the public checks after the edit and address failures.",
        "boundary": "Run the public checks and independently probe one consequential boundary case from the specification.",
        "matrix": "Verify the primary behavior, one boundary and one advertised error case where applicable. Batch checks into one tool call when practical.",
        "review": "Run the public checks and compare the final diff against each visible contract clause.",
    },
    "tool_use": {
        "ordinary": "Use the workspace tools as needed to inspect files, edit and test.",
        "scoped": "Read only relevant files and ranges. Keep diagnostic output concise and expand it when evidence is incomplete.",
        "grouped": "Combine related inexpensive inspection or verification commands when they are independent. Keep enough output to diagnose any failure.",
        "status": "Treat the tool exit status and any truncation marker as evidence. Retrieve narrower evidence before drawing conclusions from incomplete output.",
    },
    "completion": {
        "brief": "Finish with a brief summary of the change and verification.",
        "evidence": "Before finishing, confirm the change is saved and cite the checks that actually ran. Disclose gaps.",
        "reassess": "If a check fails, diagnose and make one distinct repair attempt before reporting the outcome and any remaining uncertainty.",
    },
}
SEED = {dimension: next(iter(options)) for dimension, options in HARNESS.items()}
POLICY_SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"}, "verification": {"type": "string"}},
    "required": ["summary", "verification"],
    "additionalProperties": False,
}
PROPOSER_SCHEMA = {
    "type": "object",
    "properties": {
        "settings": {"type": "object", "properties": {
            key: {"type": "string", "enum": list(choices)} for key, choices in HARNESS.items()
        }, "required": list(HARNESS), "additionalProperties": False},
        "hypothesis": {"type": "string"},
        "rationale": {"type": "string"},
        "prediction": {"type": "string"},
        "memory_used": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["settings", "hypothesis", "rationale", "prediction", "memory_used"],
    "additionalProperties": False,
}


def create_once(path, value):
    if path.exists():
        if read(path) != value:
            raise ValueError(f"Immutable record disagrees: {path.name}")
    else:
        write_new(path, value)
    return value


@contextmanager
def matrix_lock(run):
    run.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (run / "study.lock").open("ab") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def load_protocol(path):
    protocol = read(path)
    if (protocol.get("schema") != 1 or protocol.get("benchmark") != VERSION
            or protocol.get("model") != MODEL or protocol.get("starting_harness") != SEED
            or protocol.get("rounds") != 5 or protocol.get("candidate_limit") != 1
            or protocol.get("repetitions") not in (1, 5) or protocol.get("automatic_retries") != 0
            or type(protocol.get("workers")) is not int or not 1 <= protocol["workers"] <= 4
            or type(protocol.get("seed")) is not int or not 1 <= protocol.get("timeout_seconds", 0) <= 600
            or protocol.get("rates") != {"input": 0.10, "cached": 0.01, "output": 0.50}):
        raise ValueError("Invalid SIM study protocol")
    return protocol


def register(run, protocol, bank, tasks, runtime):
    path = run / "registration.json"
    identity = {
        "protocol": protocol, "bank_sha256": bank["sha256"],
        "tasks": {key: {"split": task.split, "sha256": task.fingerprint} for key, task in tasks.items()},
        "sources": {p.name: file_digest(p) for p in sorted(Path(__file__).parent.glob("*.py"))
                    if p.name in {"study.py", "memory.py", "runtime.py", "sandbox.py", "benchmark.py", "benchmark_tasks.py"}},
        "model": MODEL, "cli": runtime.version, "cli_sha256": runtime.codex_sha256,
        "source_account_hash": runtime.binding["account_hash"],
        "python": platform.python_version(), "environment": platform.platform(),
    }
    if path.exists():
        retained = read(path)
        if retained["identity"] != identity:
            raise ValueError("Registered environment, sources, tasks or historical bank changed")
        return retained
    git = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    return create_once(path, {"identity": identity, "git_commit": git, "registered_at": now()})


def harness_text(settings):
    if set(settings) != set(HARNESS) or any(settings[key] not in HARNESS[key] for key in HARNESS):
        raise ValueError("Invalid harness settings")
    return "\n".join(HARNESS[key][settings[key]] for key in HARNESS)


def agent_prompt(settings):
    return (
        "Repair solution.py according to README.md. Only solution.py may be modified. "
        "The workspace tools can read the public files, edit solution.py and execute checks. "
        "Return a short structured completion summary.\n\n" + harness_text(settings)
    )


def proposer_prompt(settings, observations, rounds, historical):
    # Projection is already complete here. No condition name, bank hash or hidden inputs.
    return (
        "Improve the instruction harness of a coding agent. Propose one general change among "
        "the allowed settings. The goal is increased independently checked correctness, with "
        "token efficiency as a secondary goal. Treat prior experience as testable evidence. "
        "Use only the supplied observations. Avoid repository- or task-specific tricks. "
        "Include a predicted result and a rationale. Include only cited historical experiment "
        "IDs that were actually supplied.\n\n"
        f"Allowed settings\n{canonical(HARNESS)}\n\n"
        f"Current settings\n{canonical(settings)}\n\n"
        f"Current run observations\n{canonical(observations)}\n\n"
        f"Earlier rounds of this run\n{canonical(rounds)}\n\n"
        f"Historical experiment records\n{historical}"
    )


def snapshot(run, settings):
    text = harness_text(settings)
    identifier = digest(settings)
    filename = run / "harnesses" / f"{identifier}.json"
    return create_once(filename, {"sha256": identifier, "settings": settings, "prompt_instructions": text})


def _review_case(runtime, run, call_id, stage, task, settings):
    grade_file = run / "cases" / (call_id + ".json")
    result = runtime.invoke(call_id, prompt=agent_prompt(settings), files=task.public_files(),
                            editable="solution.py", schema=POLICY_SCHEMA, stage=stage)
    if "quota" in str(result.get("error_type", "")).lower() or not (result.get("usage") or {}).get("total_tokens"):
        raise RuntimeError(f"Native source or metering interrupted at {call_id}. Inspect the retained native receipt.")
    if grade_file.exists():
        return read(grade_file)
    integrity = result["candidate_integrity"]
    if integrity and isinstance(result["candidate"], str):
        grade = evaluate(task, result["candidate"]).to_dict()
    else:
        grade = {"passed": False, "passed_checks": 0, "total_checks": len(task.hidden_tests),
                 "failure": "candidate_integrity"}
    if result["status"] != "completed":
        grade = {**grade, "passed": False, "failure": result.get("error_type") or result["status"]}
    create_once(grade_file, {"call_id": call_id, "task_id": task.id, "harness_sha256": digest(settings),
        "grade": grade, "usage": result["usage"], "elapsed_seconds": result["elapsed_seconds"],
        "scenario_cost": result["scenario_cost"], "tool_count": result["tool_count"],
        "tool_exits": [r.get("exit_code") for r in result["tool_summary"]],
        "candidate_sha256": result["candidate_sha256"], "events_sha256": result["events_sha256"]})
    return read(grade_file)


def cases(runtime, run, prefix, stage, tasks, settings, workers):
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending = [pool.submit(_review_case, runtime, run, f"{prefix}-{task.id}", stage, task, settings)
                   for task in tasks]
        return [future.result() for future in pending]


def feedback(cells):
    """Send the same observation fields in every arm. No raw output or task solution."""
    return [{"task": row["task_id"], "checks": row["grade"], "tokens": row["usage"]["total_tokens"],
             "tool_count": row["tool_count"], "tool_exits": row["tool_exits"]} for row in cells]


def select(incumbent, candidate):
    regressions = [before["task_id"] for before, after in zip(incumbent, candidate, strict=True)
                   if before["grade"]["passed"] and not after["grade"]["passed"]]
    if regressions:
        return False, "regression", regressions
    before, after = [sum(row["grade"]["passed"] for row in cells) for cells in (incumbent, candidate)]
    if after > before:
        return True, "more_tasks_passed", []
    before, after = [sum(row["usage"]["total_tokens"] for row in cells) for cells in (incumbent, candidate)]
    if before > 0 and after <= 0.90 * before:
        return True, "same_outcomes_at_least_ten_percent_fewer_tokens", []
    return False, "no_material_gain", []


def optimize(runtime, run, protocol, bank, rep, condition, tasks, seed_cells):
    prefix = f"r{rep:02}-{condition.lower()}"
    historical = memory_text(bank, condition)
    settings, incumbent, rounds = dict(SEED), seed_cells, []
    for number in range(1, protocol["rounds"] + 1):
        identifier = f"{prefix}-o{number:02}"
        memory_bytes = len(historical.encode())
        prompt = proposer_prompt(settings, feedback(incumbent), rounds, historical)
        proposal = runtime.invoke(identifier, prompt=prompt, schema=PROPOSER_SCHEMA, stage="optimization")
        if not (proposal.get("usage") or {}).get("total_tokens") or proposal["status"] != "completed" or not isinstance(proposal["answer"], dict):
            raise RuntimeError(f"Proposer invocation incomplete at {identifier}")
        answer = proposal["answer"]
        previous = settings
        candidate = answer["settings"]
        harness_text(candidate)
        decision, regressed, tested = "no_change", [], []
        if answer["settings"] != settings:
            snapshot(run, candidate)
            tested = cases(runtime, run, identifier, "optimization", tasks, candidate, protocol["workers"])
            accepted, decision, regressed = select(incumbent, tested)
            if accepted:
                settings, incumbent = candidate, tested
        else:
            accepted = False
        diff = "".join(difflib.unified_diff(
            harness_text(previous).splitlines(keepends=True),
            harness_text(candidate).splitlines(keepends=True), fromfile="incumbent", tofile="candidate"))
        record = {
            "round": number, "proposal_call": identifier, "proposal": answer, "harness_diff": diff,
            "candidate_cases": [row["call_id"] for row in tested], "candidate_observations": feedback(tested),
            "accepted": accepted, "decision": decision, "regressions": regressed,
            "retained": settings, "retained_passed": sum(row["grade"]["passed"] for row in incumbent),
            "memory_bytes": memory_bytes, "prompt_bytes": len(prompt.encode()),
            "first_request_input_tokens": proposal.get("first_request_input_tokens"),
        }
        create_once(run / "rounds" / f"{identifier}.json", record)
        # Never forward the model's memory citations or historical paraphrases as common observations.
        rounds.append({key: record[key] for key in ("round", "decision", "candidate_observations", "retained")}
                      | {"candidate": candidate})
        print(f"{identifier} {decision} {record['retained_passed']}/{len(tasks)}", flush=True)
    return create_once(run / "selections" / f"{prefix}.json", {
        "rep": rep, "condition": condition, "harness": snapshot(run, settings),
        "initial_optimization_cases": [row["call_id"] for row in seed_cells],
        "rounds": protocol["rounds"],
    })


def execute(runtime, run, protocol, bank, *, condition=None, phase="all"):
    tasks = load_tasks()
    register(run, protocol, bank, tasks, runtime)
    fit = [task for task in tasks.values() if task.split == "optimization"]
    test = [task for task in tasks.values() if task.split == "heldout"]
    if not fit or not test or set(t.id for t in fit) & set(t.id for t in test):
        raise ValueError("Disjoint optimization and holdout are required")
    snapshot(run, SEED)
    selections = {}
    reps = range(1, protocol["repetitions"] + 1)
    orders = {rep: random.Random(protocol["seed"] + rep).sample(list(CONDITIONS), len(CONDITIONS)) for rep in reps}
    freeze = run / "heldout-freeze.json"
    if phase != "heldout":
        for rep in reps:
            seed = cases(runtime, run, f"r{rep:02}-seed-fit", "optimization", fit, SEED, protocol["workers"])
            for arm in orders[rep]:
                if condition is None or condition == arm:
                    selected = run / "selections" / f"r{rep:02}-{arm.lower()}.json"
                    if not selected.exists():
                        optimize(runtime, run, protocol, bank, rep, arm, fit, seed)
    if phase == "optimization":
        return
    for rep in reps:
        for arm in CONDITIONS:
            selected = run / "selections" / f"r{rep:02}-{arm.lower()}.json"
            if not selected.exists():
                raise RuntimeError("Complete every optimization arm before held-out inference")
            selections[f"r{rep:02}-{arm.lower()}"] = read(selected)
    create_once(freeze, {"randomized_orders": {str(k): v for k, v in orders.items()},
                        "selections": selections})
    for rep in reps:
        cases(runtime, run, f"r{rep:02}-seed-test", "heldout", test, SEED, protocol["workers"])
        for arm in orders[rep]:
            prefix = f"r{rep:02}-{arm.lower()}"
            selected = selections[prefix]["harness"]["settings"]
            cells = cases(runtime, run, prefix + "-test", "heldout", test, selected, protocol["workers"])
            create_once(run / "heldout" / f"{prefix}.json", {
                "rep": rep, "condition": arm, "cases": [row["call_id"] for row in cells],
                "passed": sum(row["grade"]["passed"] for row in cells), "assigned": len(test),
                "selected_harness_sha256": digest(selected),
            })
            print(f"{prefix} heldout {sum(row['grade']['passed'] for row in cells)}/{len(test)}", flush=True)
