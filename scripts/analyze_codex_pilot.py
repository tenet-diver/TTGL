#!/usr/bin/env python3
"""Reconstruct descriptive pilot results from immutable grading and assignment records."""
import argparse
import hashlib
import json
from pathlib import Path

from ttgl.pilot import summarize, write_new

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source = ROOT / "experiments/codex-pilot-001"
    events_path = ROOT / "results/codex-pilot-001/execution-log.jsonl"
    protocol = json.loads((source / "protocol.json").read_text())
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    assigned, finished = {}, {}
    for event in events:
        key = event["task_id"], event["arm"]
        if event["event"] == "assigned":
            if key in assigned:
                raise ValueError(f"Duplicate assignment {key}")
            assigned[key] = event
        elif event["event"] == "worker_completed":
            if key in finished:
                raise ValueError(f"Duplicate completion {key}")
            finished[key] = event
    records = []
    for task in protocol["task_ids"]:
        for arm in protocol["arms"]:
            assignment, completion = assigned[task, arm], finished[task, arm]
            path = source / "grades" / arm / task / "report.json"
            grade = json.loads(path.read_text())
            if (grade["task_id"], grade["arm"]) != (task, arm):
                raise ValueError("Grade identity mismatch")
            if grade["protocol_sha256"] != sha(source / "protocol.json"):
                raise ValueError("Grade protocol mismatch")
            for kind in ("stdout", "junit"):
                artifact = Path(grade["test"][kind + "_path"])
                # Artifact names are fixed by the grader; resolve in the cloned repository.
                local = path.parent / artifact.name
                if sha(local) != grade["test"][kind + "_sha256"]:
                    raise ValueError(f"Changed grading artifact {local}")
            functional = grade["returncode"] == 0 and grade["testcounts"]["tests"] > 0
            records.append({
                "task_id": task, "arm": arm, "model_id": assignment["model_id"],
                "agent_id": assignment["agent_id"], "status": "graded",
                "resolved": grade["resolved"], "functional_success": functional,
                "artifact_policy_violations": grade["prohibited_edits"],
                "expert_calls": completion.get("expert_calls", 0),
                "input_tokens": None, "output_tokens": None, "cost_usd": None,
                "wall_seconds": None,
                "timing_note": "Root log is a delayed observation/batch envelope, not a comparable per-task latency measurement",
                "patch_sha256": grade["patch_sha256"], "grader_report_sha256": sha(path),
                "grader_report": str(path.relative_to(ROOT)),
            })
    report = summarize(records, protocol["task_ids"], protocol["arms"], "sol")
    report["repository_clusters"] = 2
    report["conditions"] = {"luna": "single Luna", "sol": "single Sol",
                            "precall": "untrained task-only Luna router", "personal": "optional conversational Luna controller"}
    for arm in protocol["arms"]:
        rows = [r for r in records if r["arm"] == arm]
        report["arms"][arm]["functional_successes"] = sum(r["functional_success"] for r in rows)
        report["arms"][arm]["artifact_policy_failures"] = sum(bool(r["artifact_policy_violations"]) for r in rows)
    report["interpretation"] = [
        "All four task routers selected Luna; no learned-router performance claim.",
        "All four optional conversational controllers chose zero expert turns; this matrix did not exercise dialogue.",
        "Original-test-file edits fail the frozen artifact policy even when additive and functionally correct.",
        "Unknown usage and prices prevent testing the dollar-saving hypothesis.",
        "Forced-dialogue smoke is separate and cannot be added as a fifth performance arm.",
    ]
    report["provenance"] = {"protocol_sha256": sha(source / "protocol.json"), "event_log_sha256": sha(events_path)}
    args.output_dir.mkdir(parents=True, exist_ok=False)
    with (args.output_dir / "records.json").open("x") as stream:
        json.dump(records, stream, indent=2)
        stream.write("\n")
    write_new(args.output_dir / "summary.json", report)
    print(json.dumps(report["arms"], indent=2))


if __name__ == "__main__":
    main()
