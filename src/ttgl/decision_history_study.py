"""Run and audit the registered decision-history comparison on two dependent tasks."""
from __future__ import annotations

import argparse
from collections import Counter
import io
import json
from pathlib import Path
import tempfile
import time

from . import decision_history_followup as memory
from .decision_history.memory import export_episode
from .decision_history_study_actor import TIMEOUT_HELP, serve as serve_actor
from .decision_history_study_native import invoke
from .decision_history_study_tasks import tasks
from .experience_routing.io import canonical, digest, file_digest, read
from .sim_ablation.benchmark import evaluate, qualify
from .sim_ablation.runtime import MODEL, NativeRuntime, _worktree, qualify_sandbox
from .sim_ablation.study import ROOT, create_once, matrix_lock

STUDY_ID = "decision-history-three-arm-001"
ORDER = {"seats": ("code-only", "summary-only", "full-history"),
         "flags": ("full-history", "summary-only", "code-only")}
PUBLIC_TEST = "python3 -m unittest -q test_public"
COMMON = (
    "Read README.md and implement the current request in solution.py. Use only the assigned worker shell. "
    "Its timeout_seconds is in seconds, ranges from 1 to 30, and may be omitted for the 15-second default. "
    "If the worker rejects the timeout, omit it and try that useful command again. Only modify solution.py. "
)
PARENT_PROMPT = COMMON + (
    f"Run `{PUBLIC_TEST}` on its own after your final edit. Return a concise summary and one consequential "
    "decision, its rationale, alternatives considered and conditions under which it applies. Describe the actual verification."
)
TARGET_PROMPT = COMMON + (
    "Read checkpoint_1.md and preserve earlier behavior. Verify with `python3 -m unittest -q test_public test_previous`. "
    "If predecessor history is available, you may inspect it when useful. Use its evidence only where applicable. "
    "State which evidence actually influenced your choices and what you verified."
)
EXPOSURE_PROMPT = TARGET_PROMPT + " If a predecessor conversation excerpt is included, inspect its public evidence before editing."
PARENT_FIELDS = ("summary", "decision", "rationale", "alternatives", "applies_when", "verification")
TARGET_FIELDS = ("summary", "verification", "history_influence")


def _schema(fields):
    return {"type": "object", "properties": {field: {"type": "string"} for field in fields},
            "required": list(fields), "additionalProperties": False}


def _base(files):
    with tempfile.TemporaryDirectory(prefix="observatory-history-base-") as directory:
        return _worktree(Path(directory), files)[1]


def actor_control():
    with tempfile.TemporaryDirectory(prefix="observatory-history-actor-test-") as directory:
        root = Path(directory)
        qualify_sandbox(root)
        (root / "README.md").write_text("public acceptance\n")
        (root / "solution.py").write_text("answer = 0\n")
        script = "import unittest\nimport solution\n" \
                 "class Check(unittest.TestCase):\n    def test_answer(self):\n        self.assertEqual(solution.answer, 7)\n"
        (root / "test_public.py").write_text(script)
        config = {"workspace": str(root), "spool": str(root / "actor"), "invalid_requests": str(root / "invalid"),
                  "protected": ["README.md", "test_public.py"], "deadline": time.monotonic() + 30}

        def call(ident, arguments):
            request = {"jsonrpc": "2.0", "id": ident, "method": "tools/call",
                       "params": {"name": "shell", "arguments": arguments}}
            out = io.StringIO()
            serve_actor(config, [canonical(request)], out)
            return json.loads(out.getvalue())["result"]

        bad = call(1, {"command": "cat README.md", "timeout_seconds": 10000})
        if not bad["isError"] or bad["content"][0]["text"] != TIMEOUT_HELP or (root / "actor").exists():
            raise ValueError("Invalid timeout did not receive actionable rejection")
        good = call(2, {"command": "cat README.md && printf 'answer = 7\\n' > solution.py && " + PUBLIC_TEST})
        result = json.loads(good["content"][0]["text"])
        if good["isError"] or result["exit_code"] != 0 or result["stdout"] != "public acceptance\n":
            raise ValueError("Offline read, edit and public check control failed")
        return {"offline_boundary": True, "invalid_timeout_rejected": True, "valid_default_read_edit_check": True}


def _candidate(root, result):
    if result["candidate_sha256"] is None:
        return None
    data = read(root / "invocations" / result["call_id"] / "candidate.json")
    if digest(data["source"].encode()) != result["candidate_sha256"]:
        raise ValueError("Candidate bytes disagree with the native completion")
    return data["source"]


def _sealed_memory(runtime, case, result):
    folder = runtime.output / "invocations" / result["call_id"]
    trace = (folder / "native" / result["call_id"] / "events.jsonl").read_bytes()
    checks = [row for row in memory._public_checks(trace).values()
              if row["command_preview"].strip() == PUBLIC_TEST and row["exit_code"] == 0]
    if not checks or not isinstance(result["answer"], dict):
        return None
    episode = export_episode(folder, case.name, 1, result)
    answer = result["answer"]
    if any(not isinstance(answer.get(field), str) or not answer[field].strip() for field in PARENT_FIELDS):
        return None
    check_id = checks[-1]["item_id"]
    declarations = [{"decision": answer["decision"][:1500], "rationale": answer["rationale"][:1500],
                     "applies_when": answer["applies_when"][:1500], "alternatives": [answer["alternatives"][:300]],
                     "check_item_id": check_id}]
    card, = memory.decision_records(episode, trace, declarations)
    summary = {key: episode[key] for key in ("id", "checkpoint", "summary", "source_event_sha256")}
    summary["decisions"] = [card]
    views = {"summary-only": [summary], "full-history": [{**summary, "conversation": episode["conversation"]}]}
    directory = runtime.output / "history" / case.name
    for arm, rows in views.items():
        create_once(directory / f"{arm}.json", rows)
    manifest = {"version": 1, "handoff": case.name, "predecessors": [episode["id"]],
                "search_index_sha256": digest([summary]), "implementation_sha256": file_digest(memory.__file__),
                "arms": {arm: file_digest(directory / f"{arm}.json") for arm in views}}
    create_once(directory / "manifest.json", manifest)
    for path in sorted(directory.glob("*.json")):
        runtime.retention.retain_file(path, kind="decision-history-study-bundle", identity=f"{STUDY_ID}:{case.name}:{path.name}")
    # Keep the public verification exchange verbatim and bounded. The excerpt
    # selector is fixed before the continuation arms are admitted.
    line = checks[-1]["trace_line"]
    events = trace.splitlines()
    item = json.loads(events[line - 1])["item"]
    messages = []
    for event_bytes in events[:line - 1]:
        event = json.loads(event_bytes)
        content = event.get("item", {})
        if event.get("type") == "item.completed" and content.get("type") == "agent_message" and content.get("text"):
            messages.append(content["text"])
    exchange = "Public tool action: " + canonical(item["arguments"]) + "\nPublic tool result: " + canonical(item["result"])
    excerpt = "\n".join("Agent: " + message[:450] for message in messages[:2]) + "\n" + exchange[:1200]
    create_once(runtime.output / "history" / f"{case.name}-excerpt.json",
                {"trace_line": line, "source_event_sha256": episode["source_event_sha256"], "text": excerpt})
    return directory, file_digest(directory / "manifest.json")


def _grade(case, candidate):
    if candidate is None:
        return {"target": None, "earlier": None}
    return {"target": evaluate(case.continuation, candidate).to_dict(),
            "earlier": evaluate(case.predecessor, candidate).to_dict()}


def _registration(runtime, suite):
    fixed_sources = [Path(__file__), *sorted(Path(__file__).parent.glob("decision_history_study_*.py")),
                     Path(memory.__file__), Path(__file__).with_name("decision_history_followup_trial.py"),
                     ROOT / "src/ttgl/sim_ablation/runtime.py", ROOT / "src/ttgl/sim_ablation/benchmark.py"]
    return {"id": STUDY_ID, "roster": {case: list(arms) for case, arms in ORDER.items()},
            "exposure_case": "seats", "conditional_exposure": "zero successful conversation reads",
            "sources": {path.name: file_digest(path) for path in fixed_sources}, "model": MODEL, "effort": runtime.effort,
            "codex": runtime.version, "codex_sha256": runtime.codex_sha256, "source_account_hash": runtime.binding["account_hash"],
            "timeout_seconds": runtime.timeout_seconds, "automatic_retries": 0, "native_call_cap": 10,
            "tasks": {case.name: [case.predecessor.fingerprint, case.continuation.fingerprint] for case in suite},
            "prompts": {name: digest(text.encode()) for name, text in
                        (("source", PARENT_PROMPT), ("target", TARGET_PROMPT), ("exposure", EXPOSURE_PROMPT))}}


def run(runtime, suite):
    output = runtime.output
    protocol = _registration(runtime, suite)
    registration = output / "registration.json"
    create_once(registration, protocol)
    runtime.retention.retain_file(registration, kind="decision-history-study-registration", identity=STUDY_ID)
    controls = qualify({task.id: task for case in suite for task in (case.predecessor, case.continuation)})
    controls["worker"] = actor_control()
    for case in suite:
        if not evaluate(case.predecessor, case.continuation.reference).passed:
            raise ValueError("Continuation reference regresses the prior checkpoint")
    create_once(output / "controls.json", controls)
    runtime.retention.retain_file(output / "controls.json", kind="decision-history-study-controls", identity=STUDY_ID)

    sources, admitted = {}, {}
    for case in suite:
        print(f"Processing {case.name} predecessor", flush=True)
        public = case.predecessor.public_files()
        source = invoke(runtime, f"{STUDY_ID}-{case.name}-source", protocol, public, PARENT_PROMPT, _schema(PARENT_FIELDS),
                        base_commit=_base(public), stage="historical")
        candidate = _candidate(output, source)
        parent_grade = evaluate(case.predecessor, candidate).to_dict() if candidate is not None else None
        history = (_sealed_memory(runtime, case, source) if source["status"] == "completed" and source["tokens"]
                   and parent_grade and parent_grade["passed"] else None)
        sources[case.name] = {**source, "grade": parent_grade, "eligible": history is not None}
        if history is None:
            print(f"{case.name} predecessor did not qualify; retain its assignment", flush=True)
            continue
        public = case.continuation.public_files()
        public.update({"solution.py": candidate, "checkpoint_1.md": case.predecessor.prompt,
                       "test_previous.py": case.predecessor.public_tests})
        admitted[case.name] = (public, _base(public), history)
    create_once(output / "parents.json", sources)

    rows = []
    for case in suite:
        if case.name not in admitted:
            continue
        public, base, (directory, pin) = admitted[case.name]
        for arm in ORDER[case.name]:
            print(f"Processing {case.name} {arm}", flush=True)
            result = invoke(runtime, f"{STUDY_ID}-{case.name}-{arm}", protocol, public, TARGET_PROMPT, _schema(TARGET_FIELDS),
                            base_commit=base, history=None if arm == "code-only" else (directory, arm, pin), stage="optimization")
            rows.append({"case": case.name, "arm": arm, **result, **_grade(case, _candidate(output, result))})

    pages = sum(r["view"] == "conversation" and not r["error"] for row in rows for r in row["retrieval"])
    exposure = []
    if pages == 0 and protocol["exposure_case"] in admitted:
        case = next(case for case in suite if case.name == protocol["exposure_case"])
        public, base, (directory, pin) = admitted[case.name]
        excerpt = read(output / "history" / f"{case.name}-excerpt.json")["text"]
        for arm in ("shared-records", "shared-records-and-excerpt"):
            print(f"Processing {case.name} {arm}", flush=True)
            prompt = EXPOSURE_PROMPT
            if arm == "shared-records-and-excerpt":
                prompt += "\n\nPredecessor conversation excerpt\n" + excerpt
            result = invoke(runtime, f"{STUDY_ID}-{case.name}-{arm}", protocol, public, prompt, _schema(TARGET_FIELDS),
                            base_commit=base, history=(directory, "summary-only", pin), stage="optimization")
            exposure.append({"case": case.name, "arm": arm, **result, **_grade(case, _candidate(output, result))})

    threads = [row["thread_id"] for row in [*sources.values(), *rows, *exposure] if row["thread_id"]]
    if len(set(threads)) != len(threads):
        raise ValueError("A supposed fresh invocation reused a native thread")
    path = output / "report.json"
    create_once(path, {"study": STUDY_ID, "registration_sha256": file_digest(registration), "predecessors": sources,
                       "planned_main": 6, "main": rows, "planned_exposure_case": protocol["exposure_case"],
                       "optional_conversation_pages": pages, "exposure": exposure})
    runtime.retention.retain_file(path, kind="decision-history-study-report", identity=STUDY_ID)


def audit(output, suite):
    path = output / "report.json"
    report = read(path)
    if report["registration_sha256"] != file_digest(output / "registration.json"):
        raise ValueError("Report registration differs")
    by_case = {case.name: case for case in suite}
    rows = [*report["predecessors"].values(), *report["main"], *report["exposure"]]
    for row in rows:
        call = row["call_id"]
        folder = output / "invocations" / call
        trace = folder / "native" / call / "events.jsonl"
        if file_digest(trace) != row["events_sha256"]:
            raise ValueError("Retained native trace differs")
        usage = [event["usage"] for line in trace.read_text().splitlines()
                 if (event := json.loads(line)).get("type") == "turn.completed"]
        if row["status"] == "completed" and (len(usage) != 1 or row["tokens"] != usage[0]["input_tokens"] + usage[0]["output_tokens"]):
            raise ValueError("Terminal native usage differs")
        candidate = _candidate(output, row)
        if "case" in row:
            expected = _grade(by_case[row["case"]], candidate)
            if any(row[key] != value for key, value in expected.items()):
                raise ValueError("Independent grade replay differs")
        elif candidate is not None:
            case = next(case for case in suite if call == f"{STUDY_ID}-{case.name}-source")
            if evaluate(case.predecessor, candidate).to_dict() != row["grade"]:
                raise ValueError("Predecessor grade replay differs")
        receipts = list((folder / "history-spool").glob("*.json"))
        if len(receipts) != len(row["retrieval"]):
            raise ValueError("History receipt count differs")
    print(json.dumps({"report_sha256": file_digest(path), "audited_invocations": len(rows),
                      "statuses": dict(Counter(row["status"] for row in rows)),
                      "main": len(report["main"]), "exposure": len(report["exposure"])}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "audit"))
    args = parser.parse_args()
    output = memory.PRIVATE_ROOT / STUDY_ID
    if args.action == "audit":
        audit(output, tasks())
    else:
        with matrix_lock(output):
            runtime = NativeRuntime(ROOT, output, timeout_seconds=120)
            pin = read(memory.PRIVATE_ROOT / "decision-history-scb-001/registration.json")["identity"]
            if (runtime.version, runtime.codex_sha256, runtime.binding["account_hash"]) != (
                pin["runtime"], pin["runtime_sha256"], pin["source_account_hash"]
            ):
                raise ValueError("Use the originally reviewed Codex executable and source subscription")
            run(runtime, tasks())


if __name__ == "__main__":
    main()
