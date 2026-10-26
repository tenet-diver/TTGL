"""Auditable records and paired descriptive analysis for externally run agent trials.

This does not run an LLM or infer token usage from text. The Codex collaboration
UI and the standalone Codex CLI are separate execution backends.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

import numpy as np


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def validate_record(record: dict) -> None:
    for key in ("task_id", "arm", "status", "model_id"):
        if not isinstance(record.get(key), str) or not record[key]:
            raise ValueError(f"Missing {key}")
    if record.get("resolved") is not None and type(record["resolved"]) is not bool:
        raise ValueError("resolved must be a grader's boolean or null")
    for key in ("wall_seconds", "cost_usd", "input_tokens", "output_tokens", "expert_calls"):
        value = record.get(key)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                  or not math.isfinite(value) or value < 0):
            raise ValueError(f"Invalid {key}")
    if record.get("resolved") is not None and not record.get("grader_report_sha256"):
        raise ValueError("A graded outcome requires grader report provenance")
    if record.get("cost_usd") is not None and not record.get("cost_source"):
        raise ValueError("A dollar cost requires a source; missing usage is not zero cost")


def summarize(records: list[dict], task_ids: list[str], arms: list[str],
              reference: str, seed: int = 1729) -> dict:
    if not task_ids or len(set(task_ids)) != len(task_ids) or not arms or len(set(arms)) != len(arms):
        raise ValueError("Task and arm lists must be nonempty and unique")
    if reference not in arms:
        raise ValueError("Unknown reference arm")
    index = {}
    for row in records:
        validate_record(row)
        key = row["task_id"], row["arm"]
        if key in index:
            raise ValueError(f"Duplicate assigned trial: {key}")
        if key[0] not in task_ids or key[1] not in arms:
            raise ValueError(f"Unregistered trial: {key}")
        index[key] = row
    expected = {(task, arm) for task in task_ids for arm in arms}
    if set(index) != expected:
        raise ValueError("Incomplete assigned matrix: record failures explicitly before analysis")
    result = {
        "status": "descriptive_feasibility_analysis", "assigned_tasks": len(task_ids),
        "seed": seed, "reference": reference, "arms": {}, "paired_differences": {},
        "limitations": ["Not a powered confirmatory evaluation", "Task bootstrap is conditional on the chosen issues, which may share repositories or bug families", "Models may have seen public tasks",
                        "Unknown prices and usage remain null", "Wall time includes orchestration and contention"],
    }
    for arm in arms:
        rows = [index[task, arm] for task in task_ids]
        graded = [r for r in rows if r.get("resolved") is not None]
        solved = sum(r.get("resolved") is True for r in rows)
        costs = [r.get("cost_usd") for r in rows]
        times = [r.get("wall_seconds") for r in rows]
        total = sum(costs) if all(c is not None for c in costs) else None
        result["arms"][arm] = {
            "assigned": len(rows), "graded": len(graded), "resolved": solved,
            "ungraded": len(rows) - len(graded),
            "resolved_per_assigned": solved / len(rows),
            "mean_wall_seconds": mean(times) if all(t is not None for t in times) else None,
            "total_cost_usd": total,
            "cost_per_assigned_usd": total / len(rows) if total is not None else None,
            "cost_per_resolved_usd": total / solved if total is not None and solved else None,
            "reported_expert_calls": sum(r.get("expert_calls") or 0 for r in rows),
            "expert_call_count_complete": all(r.get("expert_calls") is not None for r in rows),
        }
    rng = np.random.default_rng(seed)
    for arm in arms:
        if arm == reference:
            continue
        # Keep the task pairing, and do not treat repeated model calls as new tasks.
        pairs = [(index[t, arm], index[t, reference]) for t in task_ids]
        if any(a.get("resolved") is None or b.get("resolved") is None for a, b in pairs):
            result["paired_differences"][arm] = {"status": "unavailable_ungraded_pairs"}
            continue
        diffs = np.array([int(a["resolved"]) - int(b["resolved"]) for a, b in pairs])
        samples = diffs[rng.integers(0, len(diffs), size=(10000, len(diffs)))].mean(axis=1)
        result["paired_differences"][arm] = {
            "status": "descriptive_only", "quality_difference": float(diffs.mean()),
            "bootstrap_percentile_95": np.quantile(samples, [0.025, 0.975]).tolist(),
            "discordant_tasks": int(np.count_nonzero(diffs)),
            "warning": "Tiny-sample bootstrap can be degenerate; a zero-width interval does not establish equivalence",
        }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True, help="JSON list of assigned trial records")
    parser.add_argument("--design", type=Path, required=True, help="JSON with task_ids, arms, reference")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    design = json.loads(args.design.read_text())
    report = summarize(json.loads(args.records.read_text()), design["task_ids"], design["arms"], design["reference"])
    report.update(records_sha256=digest(args.records), design_sha256=digest(args.design),
                  analyzed_at=datetime.now(timezone.utc).isoformat())
    write_new(args.output, report)
    print(json.dumps({"status": report["status"], "tasks": report["assigned_tasks"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
