"""Validate pinned LiveCodeBench outcomes and create grouped temporal splits.

Only standard-library dependencies are used. Outcome values never determine
eligibility, split assignment, or routing features.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any


SOURCE_COMMIT = "6ca212e9c2039373f6e5069d37ffa9db66e23736"
SOURCE_REPOSITORY = "https://github.com/LiveCodeBench/submissions"
LOCAL_MODEL = "Qwen2.5-Coder-Ins-7B"
TEACHER_MODEL = "DeepSeek-V3"
SOURCE_HASHES = {
    LOCAL_MODEL: "586707158f8d1648964f54f0290dc42c94806b12684ea03b537202008170c992",
    TEACHER_MODEL: "88548117b84bf567fdadb159cfc65f9c0a6bf7da8b2fe5679829c95334abd661",
}
SAMPLES_PER_TASK = 10
MATCH_FIELDS = (
    "question_content", "question_title", "starter_code", "platform",
    "question_id", "contest_id", "contest_date", "difficulty",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def task_key(row: dict[str, Any]) -> tuple[str, str]:
    """The publisher's question ID is unique only within a platform."""
    return str(row["platform"]), str(row["question_id"])


def load_source(raw_dir: Path, model: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Reject changed input bytes, even if a provenance sidecar is modified."""
    source = raw_dir / f"{model}.json"
    data = source.read_bytes()
    actual_hash = sha256_bytes(data)
    if actual_hash != SOURCE_HASHES[model]:
        raise ValueError(f"Source checksum mismatch for {model}")
    provenance = json.loads((raw_dir / f"{model}.provenance.json").read_text())
    if provenance.get("source_commit") != SOURCE_COMMIT:
        raise ValueError(f"Unexpected source commit for {model}")
    if provenance.get("sha256") != actual_hash:
        raise ValueError(f"Provenance checksum mismatch for {model}")
    if provenance.get("model") != model:
        raise ValueError(f"Provenance model mismatch for {model}")
    expected_url = (
        f"https://raw.githubusercontent.com/LiveCodeBench/submissions/{SOURCE_COMMIT}/"
        f"{model}/Scenario.codegeneration_10_0.2_eval_all.json"
    )
    if provenance.get("pinned_url") != expected_url:
        raise ValueError(f"Unexpected pinned source URL for {model}")
    rows = json.loads(data)
    if not isinstance(rows, list):
        raise ValueError(f"Source is not a list for {model}")
    return rows, {
        "model": model,
        "file": source.name,
        "bytes": len(data),
        "sha256": actual_hash,
        "pinned_url": expected_url,
        "source_rows": len(rows),
    }


def index_source(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    index = {}
    for row in rows:
        key = task_key(row)
        if key in index:
            raise ValueError(f"Duplicate task key: {key}")
        if not all(key):
            raise ValueError("Empty platform or task ID")
        index[key] = row
    return index


def validate_shared_row(row: dict[str, Any], model: str) -> None:
    key = task_key(row)
    for field in MATCH_FIELDS:
        if field not in row:
            raise ValueError(f"Missing {field} for {model} {key}")
    if not isinstance(row["question_content"], str) or not row["question_content"].strip():
        raise ValueError(f"Empty prompt for {model} {key}")
    if not str(row["contest_id"]):
        raise ValueError(f"Empty contest ID for {model} {key}")
    datetime.fromisoformat(row["contest_date"])
    for field in ("output_list", "code_list", "graded_list"):
        values = row.get(field)
        if not isinstance(values, list) or len(values) != SAMPLES_PER_TASK:
            raise ValueError(f"Expected {SAMPLES_PER_TASK} {field} entries for {model} {key}")
    if not all(isinstance(v, str) and v.strip() for v in row["output_list"]):
        raise ValueError(f"Missing raw generation for {model} {key}")
    if not all(isinstance(v, str) for v in row["code_list"]):
        raise ValueError(f"Non-string sanitized code for {model} {key}")
    if not all(type(v) is bool for v in row["graded_list"]):
        raise ValueError(f"Non-boolean grade for {model} {key}")
    # Empty sanitized code is retained as an observed failure, not excluded.
    # Even malformed observed grade values must never silently disappear.


def prepare_pair(
    local_rows: list[dict[str, Any]], teacher_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    local_index, teacher_index = index_source(local_rows), index_source(teacher_rows)
    shared = sorted(local_index.keys() & teacher_index.keys())
    if not shared:
        raise ValueError("No shared tasks")
    output = []
    for key in shared:
        local, teacher = local_index[key], teacher_index[key]
        validate_shared_row(local, LOCAL_MODEL)
        validate_shared_row(teacher, TEACHER_MODEL)
        for field in MATCH_FIELDS:
            if local[field] != teacher[field]:
                raise ValueError(f"Mismatched task metadata {field}: {key}")
        output.append({
            "task_id": ":".join(key),
            "prompt": local["question_content"],
            "platform": local["platform"],
            "contest_id": str(local["contest_id"]),
            "contest_date": local["contest_date"],
            "difficulty": local["difficulty"],
            "local_outputs": local["code_list"],
            "local_grades": local["graded_list"],
            "teacher_outputs": teacher["code_list"],
            "teacher_grades": teacher["graded_list"],
        })
    return output, {
        "shared_tasks": len(shared),
        "local_only_excluded": len(local_index.keys() - teacher_index.keys()),
        "teacher_only_excluded": len(teacher_index.keys() - local_index.keys()),
        "shared_tasks_excluded": 0,
    }


def grouped_temporal_split(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["platform"], row["contest_id"])].append(row)
    if len(groups) < 3:
        raise ValueError("At least three contest groups are required")
    group_dates = {key: max(row["contest_date"] for row in values) for key, values in groups.items()}
    ordered = sorted(groups, key=lambda key: (group_dates[key], key))
    cumulative = [0]
    for key in ordered:
        cumulative.append(cumulative[-1] + len(groups[key]))
    n = len(rows)
    # Ties choose the earlier boundary. Each split retains at least one group.
    first = min(range(1, len(ordered) - 1), key=lambda i: (abs(cumulative[i] - 0.6 * n), i))
    second = min(range(first + 1, len(ordered)), key=lambda i: (abs(cumulative[i] - 0.8 * n), i))
    split_groups = {
        "train": ordered[:first],
        "calibration": ordered[first:second],
        "test": ordered[second:],
    }
    splits = {}
    details = {}
    for split, keys in split_groups.items():
        splits[split] = [
            {**row, "split": split}
            for key in keys
            for row in sorted(groups[key], key=lambda item: item["task_id"])
        ]
        details[split] = {
            "tasks": len(splits[split]),
            "groups": len(keys),
            "contest_date_min": min(row["contest_date"] for row in splits[split]),
            "contest_date_max": max(row["contest_date"] for row in splits[split]),
            "group_max_date_min": min(group_dates[key] for key in keys),
            "group_max_date_max": max(group_dates[key] for key in keys),
            "group_ids": [list(key) for key in keys],
        }
    task_sets = [set(row["task_id"] for row in splits[name]) for name in splits]
    group_sets = [set(keys) for keys in split_groups.values()]
    task_disjoint = all(not task_sets[i] & task_sets[j] for i in range(3) for j in range(i + 1, 3))
    group_disjoint = all(not group_sets[i] & group_sets[j] for i in range(3) for j in range(i + 1, 3))
    if not task_disjoint or not group_disjoint or sum(map(len, splits.values())) != n:
        raise ValueError("Split leakage or loss of tasks")
    return splits, {
        "split_rule": "platform+contest_id groups; group max date then stable group key; closest cumulative 60% and 80%; earlier-boundary tie break",
        "target_proportions": [0.6, 0.2, 0.2],
        "total_tasks": n,
        "total_groups": len(groups),
        "boundary_group_indices": [first, second],
        "task_sets_disjoint": task_disjoint,
        "contest_groups_disjoint": group_disjoint,
        "outcomes_used_for_split": False,
        "splits": details,
    }


def prepare_dataset(raw_dir: Path, output_dir: Path) -> dict[str, Any]:
    local, local_provenance = load_source(raw_dir, LOCAL_MODEL)
    teacher, teacher_provenance = load_source(raw_dir, TEACHER_MODEL)
    paired, alignment = prepare_pair(local, teacher)
    splits, manifest = grouped_temporal_split(paired)
    manifest.update({
        "schema_version": 1,
        "source_repository": SOURCE_REPOSITORY,
        "source_commit": SOURCE_COMMIT,
        "local_model": LOCAL_MODEL,
        "teacher_model": TEACHER_MODEL,
        "samples_per_task": SAMPLES_PER_TASK,
        "sources": [local_provenance, teacher_provenance],
        "alignment": alignment,
        "feature_policy": "prompt is question_content only; metadata/difficulty are audit-only; outputs and grades are not prompt-routing features",
    })
    output_dir.mkdir(parents=True, exist_ok=True)
    for split, rows in splits.items():
        content = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows).encode()
        destination = output_dir / f"{split}.jsonl"
        temporary = destination.with_suffix(".jsonl.tmp")
        temporary.write_bytes(content)
        temporary.replace(destination)
        manifest["splits"][split].update({"file": destination.name, "sha256": sha256_bytes(content), "bytes": len(content)})
    (output_dir / "split-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/livecodebench"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    manifest = prepare_dataset(args.raw_dir, args.output_dir)
    print(json.dumps({
        "validated_tasks": manifest["total_tasks"],
        "contest_groups": manifest["total_groups"],
        "split_counts": {name: item["tasks"] for name, item in manifest["splits"].items()},
        "task_sets_disjoint": manifest["task_sets_disjoint"],
        "contest_groups_disjoint": manifest["contest_groups_disjoint"],
        "source_commit": manifest["source_commit"],
    }, indent=2))


if __name__ == "__main__":
    main()
