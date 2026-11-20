"""Admit the previously unstarted seat handoff using its verified public check."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import decision_history_followup as memory
from . import decision_history_study as study
from .decision_history.memory import export_episode
from .decision_history_study_native import invoke
from .decision_history_study_tasks import tasks
from .experience_routing.io import canonical, digest, file_digest, read
from .sim_ablation.benchmark import evaluate
from .sim_ablation.runtime import NativeRuntime
from .sim_ablation.study import ROOT, create_once, matrix_lock

ID = "decision-history-three-arm-continuation-002"


def verified_check(trace, candidate):
    """Verify that the final observed shell action writes and tests these exact bytes."""
    checks = list(memory._public_checks(trace).values())
    if not checks:
        raise ValueError("The predecessor trace has no recorded public shell action")
    check = checks[-1]
    event = json.loads(trace.splitlines()[check["trace_line"] - 1])
    command = event["item"]["arguments"]["command"]
    opening = "cat > solution.py <<'EOF'\n"
    source, separator, test = command.removeprefix(opening).partition("\nEOF\n")
    if (not command.startswith(opening) or not separator or source + "\n" != candidate
            or test.strip() != study.PUBLIC_TEST or check["exit_code"] != 0 or check["timed_out"]
            or not (check["stderr_preview"] or "").endswith("\nOK\n")):
        raise ValueError("No passing final write-and-test receipt tied to the exact predecessor candidate")
    return check


def _views(runtime, folder, parent, candidate):
    trace = (folder / "native" / parent["call_id"] / "events.jsonl").read_bytes()
    check = verified_check(trace, candidate)
    episode = export_episode(folder, "seats", 1, parent)
    answer = parent["answer"]
    declaration = {"decision": answer["decision"][:1500], "rationale": answer["rationale"][:1500],
                   "alternatives": [answer["alternatives"][:300]], "applies_when": answer["applies_when"][:1500],
                   "check_item_id": check["item_id"]}
    common = {key: episode[key] for key in ("id", "summary", "checkpoint", "source_event_sha256")}
    common["decisions"] = memory.decision_records(episode, trace, [declaration])
    views = {"summary-only": [common], "full-history": [{**common, "conversation": episode["conversation"]}]}
    directory = runtime.output / "history"
    for arm, rows in views.items():
        create_once(directory / f"{arm}.json", rows)
    manifest_path = directory / "manifest.json"
    create_once(manifest_path, {"version": 1, "handoff": "seats", "predecessors": [episode["id"]],
                               "search_index_sha256": digest([common]), "implementation_sha256": file_digest(memory.__file__),
                               "arms": {arm: file_digest(directory / f"{arm}.json") for arm in views}})
    line = check["trace_line"]
    events = trace.splitlines()
    item = json.loads(events[line - 1])["item"]
    messages = []
    for event_bytes in events[:line - 1]:
        event = json.loads(event_bytes)
        content = event.get("item", {})
        if event.get("type") == "item.completed" and content.get("type") == "agent_message" and content.get("text"):
            messages.append(content["text"])
    result = "Public tool result: " + canonical(item["result"])
    excerpt = "\n".join("Agent: " + text[:450] for text in messages[:2]) + "\n" + result[:1200]
    create_once(directory / "excerpt.json", {"trace_line": line, "source_event_sha256": episode["source_event_sha256"],
                                               "text": excerpt})
    for path in sorted(directory.glob("*.json")):
        runtime.retention.retain_file(path, kind="decision-history-study-bundle", identity=f"{ID}:{path.name}")
    return directory, file_digest(manifest_path), excerpt, check


def run(runtime):
    output = runtime.output
    earlier = memory.PRIVATE_ROOT / study.STUDY_ID
    original = read(earlier / "registration.json")
    current = study._registration(runtime, tasks())
    current["sources"].pop(Path(__file__).name)
    if current != original:
        raise ValueError("Original actor, prompts, fixture, CLI or source subscription differs")
    original_report = read(earlier / "report.json")
    if (original_report["registration_sha256"] != file_digest(earlier / "registration.json")
            or {row["case"] for row in original_report["main"]} != {"flags"} or original_report["exposure"]):
        raise ValueError("The original comparison must be sealed with seats unstarted")
    if list((earlier / "invocations").glob(f"{study.STUDY_ID}-seats-*only/started.json")) or (
        earlier / "invocations" / f"{study.STUDY_ID}-seats-full-history/started.json"
    ).exists():
        raise ValueError("A seat continuation was already admitted")
    case = next(case for case in tasks() if case.name == "seats")
    seed = original_report["predecessors"]["seats"]
    candidate = study._candidate(earlier, seed)
    if seed["eligible"] or seed["status"] != "completed" or not seed["tokens"] or not seed["grade"]["passed"]:
        raise ValueError("Unexpected terminal predecessor state")
    if evaluate(case.predecessor, candidate).to_dict() != seed["grade"]:
        raise ValueError("Original predecessor candidate fails replay")
    directory, pin, excerpt, check = _views(runtime, earlier / "invocations" / seed["call_id"], seed, candidate)
    public = case.continuation.public_files()
    public.update({"solution.py": candidate, "checkpoint_1.md": case.predecessor.prompt,
                   "test_previous.py": case.predecessor.public_tests})
    base = study._base(public)
    protocol = {"id": ID, "original_report_sha256": file_digest(earlier / "report.json"),
                "implementation_sha256": file_digest(__file__), "base_commit": base, "history_manifest_sha256": pin,
                "check_item_id": check["item_id"], "check_trace_line": check["trace_line"],
                "candidate_sha256": digest(candidate.encode()), "arm_order": list(study.ORDER["seats"]),
                "conditional_exposure": original["conditional_exposure"], "native_call_cap": 5, "automatic_retries": 0}
    path = output / "registration.json"
    create_once(path, protocol)
    runtime.retention.retain_file(path, kind="decision-history-study-registration", identity=ID)
    rows = []
    for arm in study.ORDER["seats"]:
        print(f"Processing seats {arm}", flush=True)
        result = invoke(runtime, f"{ID}-{arm}", protocol, public, study.TARGET_PROMPT, study._schema(study.TARGET_FIELDS),
                        base_commit=base, history=None if arm == "code-only" else (directory, arm, pin), stage="optimization")
        rows.append({"case": "seats", "arm": arm, **result, **study._grade(case, study._candidate(output, result))})
    pages = original_report["optional_conversation_pages"] + sum(
        entry["view"] == "conversation" and not entry["error"] for row in rows for entry in row["retrieval"])
    exposure = []
    if pages == 0:
        for arm in ("shared-records", "shared-records-and-excerpt"):
            print(f"Processing seats {arm}", flush=True)
            prompt = study.EXPOSURE_PROMPT
            if arm.endswith("and-excerpt"):
                prompt += "\n\nPredecessor conversation excerpt\n" + excerpt
            result = invoke(runtime, f"{ID}-{arm}", protocol, public, prompt, study._schema(study.TARGET_FIELDS),
                            base_commit=base, history=(directory, "summary-only", pin), stage="optimization")
            exposure.append({"case": "seats", "arm": arm, **result, **study._grade(case, study._candidate(output, result))})
    threads = [row["thread_id"] for row in [*original_report["predecessors"].values(), *original_report["main"], *rows, *exposure]]
    present = [thread for thread in threads if thread]
    if len(present) != len(set(present)):
        raise ValueError("A supposed fresh invocation reused a native thread")
    report = output / "report.json"
    create_once(report, {"study": ID, "registration_sha256": file_digest(path), "predecessors": {},
                         "planned_main": 3, "main": rows, "optional_conversation_pages": pages, "exposure": exposure})
    runtime.retention.retain_file(report, kind="decision-history-study-report", identity=ID)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "audit"))
    args = parser.parse_args()
    output = memory.PRIVATE_ROOT / ID
    if args.action == "audit":
        study.audit(output, tasks())
    else:
        with matrix_lock(output):
            run(NativeRuntime(ROOT, output, timeout_seconds=120))


if __name__ == "__main__":
    main()
