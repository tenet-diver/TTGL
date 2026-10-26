"""SWE-bench patch-generation bridge; evaluation remains in its official harness.

This module does not implement SWE-bench's tests. It freezes task assignments,
uses the existing Codex orchestrator, exports standard predictions, and imports
independent official reports. No missing meter is replaced with a zero price.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import re
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np

from . import personal
from .pilot import summarize


ARMS = ("small", "large", "precall_router", "oneway", "reset_expert", "personal")
TASK_FIELDS = {"instance_id", "repo", "base_commit", "problem_statement"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def write_new(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def read_tasks(path: Path) -> dict:
    data = json.loads(path.read_text())
    if data.get("schema_version") != 1 or not data.get("tasks"):
        raise ValueError("Expected a schema_version=1 task manifest")
    for field in ("dataset_id", "dataset_revision", "harness_commit"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError(f"Missing pinned {field}")
    seen = set()
    for row in data["tasks"]:
        if set(row) != TASK_FIELDS:
            raise ValueError("Public tasks require exactly instance_id/repo/base_commit/problem_statement")
        if any(not isinstance(value, str) or not value.strip() for value in row.values()):
            raise ValueError("Task fields must be nonempty strings")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", row["instance_id"]):
            raise ValueError("Unsafe instance ID")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", row["repo"]):
            raise ValueError("Repository must be an owner/name GitHub slug")
        if not re.fullmatch(r"[0-9a-f]{40}", row["base_commit"]):
            raise ValueError("A complete base commit SHA is required")
        if row["instance_id"] in seen:
            raise ValueError("Duplicate instance ID")
        seen.add(row["instance_id"])
    return data


def initialize(tasks_path: Path, output: Path, workspaces: Path, *, small_model: str,
               large_model: str, timeout_seconds: float = 900, seed: int = 1729,
               reasoning_effort: str = "medium", max_turns: int = 6,
               max_expert_calls: int = 2, conditions: tuple[str, ...] = ARMS) -> dict:
    data = read_tasks(tasks_path)
    output, workspaces = output.resolve(), workspaces.resolve()
    if output == workspaces or output.is_relative_to(workspaces) or workspaces.is_relative_to(output):
        raise ValueError("Study records and worker directories must be separate trees")
    if not small_model.strip() or not large_model.strip() or small_model == large_model:
        raise ValueError("Two distinct explicit model identifiers are required")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("Positive finite timeout required")
    if reasoning_effort not in ("low", "medium", "high") or max_turns < 1 or not 0 <= max_expert_calls <= 2:
        raise ValueError("Invalid orchestrator limits")
    if (not conditions or len(set(conditions)) != len(conditions) or "large" not in conditions
            or any(arm not in personal.CONDITIONS for arm in conditions)):
        raise ValueError("Conditions must be distinct supported conditions including the large reference")
    if output.exists() or workspaces.exists():
        raise ValueError("Choose new study and worker directories; existing directories are not reset")
    assignments = [{"instance_id": row["instance_id"], "arm": arm}
                   for row in data["tasks"] for arm in conditions]
    random.Random(seed).shuffle(assignments)
    design = {
        "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_id": data["dataset_id"], "dataset_revision": data["dataset_revision"],
        "harness_commit": data["harness_commit"], "tasks_sha256": digest(tasks_path),
        "task_ids": [row["instance_id"] for row in data["tasks"]],
        "arms": list(conditions), "reference": "large", "seed": seed,
        "assignment_order": assignments, "workspace_root": str(workspaces),
        "config": {"small_model": small_model, "large_model": large_model,
                   "timeout_seconds": timeout_seconds, "reasoning_effort": reasoning_effort,
                   "max_turns": max_turns, "max_expert_calls": max_expert_calls},
        "source_sha256": {"personal": digest(Path(personal.__file__)),
                          "benchmark": digest(Path(__file__))},
        "worker_environment": "Host Codex tools; dependencies must be provisioned before running",
        "model_identity": "Requested provider identifiers; immutable model revision not observed by this adapter",
        "isolation": "Independent shallow checkouts; not a hardened cross-role read boundary",
        "evaluation": "Independent official SWE-bench harness reports only",
        "economic_endpoint": "API-equivalent model cost; subscription credits and deployment cost separate",
    }
    output.mkdir(parents=True)
    workspaces.mkdir(parents=True)
    write_new(output / "design.json", design)
    (output / "design.sha256").write_text(digest(output / "design.json") + "\n")
    # Preserve exact bytes: the design hash identifies the supplied public manifest.
    (output / "tasks.json").write_bytes(tasks_path.read_bytes())
    return design


def load_design(study: Path) -> tuple[dict, dict]:
    if digest(study / "design.json") != (study / "design.sha256").read_text().strip():
        raise ValueError("Frozen design changed")
    design = json.loads((study / "design.json").read_text())
    if digest(study / "tasks.json") != design["tasks_sha256"]:
        raise ValueError("Frozen task manifest changed")
    if design["source_sha256"] != {"personal": digest(Path(personal.__file__)),
                                    "benchmark": digest(Path(__file__))}:
        raise ValueError("Runner source changed; preserve the frozen version or create a new study")
    return design, read_tasks(study / "tasks.json")


def preflight(study: Path, *, backend=None) -> dict:
    """Two tiny real model calls, separately recorded and excluded from scored costs."""
    study = study.resolve()
    design, _ = load_design(study)
    if (study / "preflight.json").exists():
        raise ValueError("Preflight already recorded; inspect it rather than repeating calls")
    checks = {}
    with personal._run_lock(study):
        for arm in ("small", "large"):
            workspace = Path(design["workspace_root"]) / f"preflight-{arm}"
            workspace.mkdir(exist_ok=False)
            task = {"task_id": f"metering-preflight-{arm}", "workspace": str(workspace),
                    "prompt": "Do not use tools. Return action complete, empty question/context, summary TTGL preflight.",
                    "allowed_paths": ["."], "memory": []}
            output = study / f"preflight-{arm}"
            config = {**design["config"], "timeout_seconds": min(90, design["config"]["timeout_seconds"]), "max_turns": 1}
            manifest = personal.run_task(task, output, condition=arm, backend=backend, **config)
            required = ("input_tokens", "cached_input_tokens", "output_tokens")
            usage = manifest["usage"]
            metered = all(type(usage.get(field)) is int for field in required) and usage["input_tokens"] > 0 and usage["output_tokens"] > 0
            checks[arm] = {"status": manifest["status"], "metering_ready": metered,
                           "manifest_sha256": digest(output / "manifest.json"),
                           "requested_model": design["config"][f"{arm}_model"]}
            # A proven startup failure should not spend another model call.
            if manifest["status"] != "completed_ungraded":
                break
        ready = len(checks) == 2 and all(row["status"] == "completed_ungraded" and row["metering_ready"] for row in checks.values())
        result = {"ready": ready, "design_sha256": digest(study / "design.json"), "checks": checks,
                  "cost_allocation": "preflight overhead; excluded from benchmark task model-cost endpoint",
                  "limitations": ["Does not establish worker dependency readiness, isolation, grading, or immutable model revision",
                                  "A later interrupted or unavailable meter must still remain incomplete"]}
        write_new(study / "preflight.json", result)
        return result


def git(workspace: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(workspace), *args], capture_output=True,
                            text=True, timeout=300, check=False)
    if result.returncode:
        # Do not save remote/auth diagnostics which could contain sensitive material.
        raise RuntimeError(f"Git {args[0]} failed with exit code {result.returncode}")
    return result.stdout


def prepare_workspace(task: dict, workspace: Path) -> None:
    if workspace.exists():
        raise ValueError("Refusing to overwrite an existing solver workspace")
    workspace.mkdir(parents=True)
    git(workspace, "init", "--quiet")
    git(workspace, "remote", "add", "origin", f"https://github.com/{task['repo']}.git")
    git(workspace, "fetch", "--quiet", "--depth=1", "origin", task["base_commit"])
    git(workspace, "checkout", "--quiet", "--detach", "FETCH_HEAD")
    if git(workspace, "rev-parse", "HEAD").strip() != task["base_commit"]:
        raise RuntimeError("Checkout does not match frozen task base")
    if git(workspace, "status", "--porcelain"):
        raise RuntimeError("Fresh checkout is unexpectedly dirty")


def export_patch(task: dict, workspace: Path) -> str:
    if git(workspace, "rev-parse", "HEAD").strip() != task["base_commit"]:
        raise ValueError("Agent changed repository HEAD; reconcile manually before exporting")
    # Intent-to-add includes new source/test files without committing or staging content.
    git(workspace, "add", "--intent-to-add", "--all")
    return git(workspace, "diff", "--binary", "--no-ext-diff", task["base_commit"], "--", ".")


def run_study(study: Path, *, resume: bool = False, backend=None) -> None:
    study = study.resolve()
    design, data = load_design(study)
    preflight_path = study / "preflight.json"
    if not preflight_path.exists():
        raise ValueError("Run the metering preflight before benchmark assignments")
    readiness = json.loads(preflight_path.read_text())
    if not readiness.get("ready") or readiness.get("design_sha256") != digest(study / "design.json"):
        raise ValueError("Metering preflight did not establish readiness for this design")
    lookup = {row["instance_id"]: row for row in data["tasks"]}
    with personal._run_lock(study):
        for assignment in design["assignment_order"]:
            task_id, arm = assignment["instance_id"], assignment["arm"]
            task = lookup[task_id]
            output = study / "runs" / arm / task_id
            workspace = Path(design["workspace_root"]) / arm / task_id
            finished = study / "patches" / arm / f"{task_id}.json"
            if finished.exists():
                if not resume:
                    raise ValueError("Study has completed assignments; use --resume")
                saved = json.loads(finished.read_text())
                if (saved["manifest_sha256"] != digest(output / "manifest.json")
                        or saved["patch_sha256"] != hashlib.sha256(saved["model_patch"].encode()).hexdigest()):
                    raise ValueError("Completed assignment artifacts changed")
                continue
            if output.exists() and not resume:
                raise ValueError("Study has started assignments; use --resume")
            if not workspace.exists():
                prepare_workspace(task, workspace)
            elif not output.exists():
                # A failed preparation never becomes an implicit partial checkout.
                if git(workspace, "rev-parse", "HEAD").strip() != task["base_commit"] or git(workspace, "status", "--porcelain"):
                    raise ValueError("Unregistered or dirty worker checkout; reconcile manually")
            metadata = {
                "task_id": task_id, "workspace": str(workspace), "memory": [], "allowed_paths": ["."],
                "prompt": task["problem_statement"] +
                    "\n\nRepair this repository at its assigned base. Preserve existing tests; "
                    "you may add tests. Do not commit, change HEAD, retrieve upstream fixes, "
                    "or access benchmark data, evaluator artifacts, or other workers. "
                    "Report unavailable test dependencies honestly.",
            }
            output.parent.mkdir(parents=True, exist_ok=True)
            manifest = personal.run_task(metadata, output, condition=arm, backend=backend,
                                         resume=output.exists(), **design["config"])
            patch = export_patch(task, workspace)
            write_new(finished, {
                "instance_id": task_id, "model_name_or_path": f"ttgl-{arm}", "model_patch": patch,
                "manifest_sha256": digest(output / "manifest.json"),
                "patch_sha256": hashlib.sha256(patch.encode()).hexdigest(),
                "status": manifest["status"],
            })
            export_predictions(study, design)
            if any(manifest["usage"].get(key) is None for key in ("input_tokens", "cached_input_tokens", "output_tokens")):
                raise RuntimeError("Assigned trial has incomplete metering; artifacts retained. Reconcile before continuing.")
        export_predictions(study, design)


def export_predictions(study: Path, design: dict) -> None:
    target = study / "predictions"
    target.mkdir(exist_ok=True)
    for arm in design["arms"]:
        records = []
        for task_id in design["task_ids"]:
            path = study / "patches" / arm / f"{task_id}.json"
            if path.exists():
                row = json.loads(path.read_text())
                records.append({key: row[key] for key in ("instance_id", "model_name_or_path", "model_patch")})
        temporary = target / f".{arm}.tmp"
        temporary.write_text("".join(canonical(row) + "\n" for row in records))
        temporary.replace(target / f"{arm}.jsonl")


def estimate_price(manifest: dict, prices: dict | None) -> dict:
    missing = []
    pieces = {}
    if not prices:
        return {"api_equivalent_usd": None, "status": "no_price_schedule", "by_model": {}}
    if (prices.get("kind") != "api_equivalent" or prices.get("currency") != "USD"
            or not prices.get("retrieved_at") or not prices.get("source_url")):
        raise ValueError("Prices require kind=api_equivalent, USD, retrieved_at and source_url")
    for model, record in manifest.get("usage_by_model", {}).items():
        rate = prices.get("models", {}).get(model)
        usage = record["usage"]
        counts = [usage.get(k) for k in ("input_tokens", "cached_input_tokens", "output_tokens")]
        if not rate or any(type(value) is not int or value < 0 for value in counts):
            missing.append(model)
            continue
        if counts[1] > counts[0]:
            raise ValueError("Cached input exceeds total input")
        fields = ("input_per_million", "cached_input_per_million", "output_per_million")
        if any(type(rate.get(key)) not in (int, float) or not math.isfinite(rate[key]) or rate[key] < 0 for key in fields):
            raise ValueError("Invalid per-million token prices")
        if rate.get("accounting") != "cached_within_input_reasoning_within_output_cache_write_at_input_rate":
            raise ValueError("Explicit supported token-accounting convention required")
        pieces[model] = ((counts[0] - counts[1]) * rate[fields[0]] + counts[1] * rate[fields[1]]
                         + counts[2] * rate[fields[2]]) / 1_000_000
    complete = bool(pieces) and not missing
    return {"api_equivalent_usd": sum(pieces.values()) if complete else None,
            "status": "estimated_from_reported_tokens" if complete else "missing_usage_or_model_price",
            "by_model": pieces, "incomplete_models": missing,
            "source_url": prices["source_url"], "retrieved_at": prices["retrieved_at"],
            "subscription_cash_usd": None, "subscription_credits": None, "deployment_cost_usd": None}


def read_grade(path: Path, task_id: str, expected_patch_sha256: str) -> tuple[bool, str, str]:
    report = json.loads(path.read_text())
    entry = report.get(task_id)
    if not isinstance(entry, dict) or type(entry.get("resolved")) is not bool:
        # The official evaluator skips empty patches and records them in its
        # aggregate report instead of creating a per-instance test report.
        # Only this explicit official category can supply the missing outcome.
        if (expected_patch_sha256 == hashlib.sha256(b"").hexdigest()
                and isinstance(report.get("empty_patch_ids"), list)
                and isinstance(report.get("submitted_ids"), list)
                and task_id in report["empty_patch_ids"] and task_id in report["submitted_ids"]
                and task_id not in report.get("resolved_ids", [])):
            return False, digest(path), "official_empty_patch_aggregate"
        raise ValueError(f"Expected official per-instance report for {task_id}")
    patch = path.parent / "patch.diff"
    if not patch.is_file() or digest(patch) != expected_patch_sha256:
        raise ValueError("Official grader patch.diff is missing or differs from the exported prediction")
    return entry["resolved"], digest(path), "official_per_instance_report"


def subscription_for_state(state: dict, report: dict | None, state_sha256: str) -> dict:
    unavailable = {"estimated_credits": None, "estimated_usd": None, "status": "not_collected"}
    if report is None:
        return unavailable
    if not report.get("independent_root_threads_attested") or not report.get("selected_states_finalized"):
        return {**unavailable, "status": "unverified_root_scope_or_unfinished_states"}
    sources = report.get("sources", [])
    if not any(row.get("sha256") == state_sha256 and row.get("run_id") == state.get("run_id")
               and row.get("finalized") is True for row in sources):
        return {**unavailable, "status": "selected_state_not_bound_to_provider_export"}
    thread_ids = set(state.get("usage_threads", {}))
    # Every invoked role must have a metered identity. Failed calls without a
    # reported thread can already consume quota and cannot be priced as zero.
    if not thread_ids or state.get("inflight") or state.get("status") == "running" or state.get("usage_accounting_issues"):
        return {**unavailable, "status": "incomplete_task_thread_accounting"}
    threads = report.get("threads", [])
    indexed = {row["thread_id"]: row for row in threads}
    if len(indexed) != len(threads):
        raise ValueError("Duplicate thread estimates in provider usage export")
    selected = [indexed.get(thread) for thread in thread_ids]
    if any(row is None or row.get("status") != "available" or not isinstance(row.get("usage"), dict) for row in selected):
        return {**unavailable, "status": "missing_thread_estimates"}
    values = [row["usage"] for row in selected]
    fields = ("estimatedUsageCreditsMicros", "estimatedUsageUsdMicros")
    for usage in values:
        for key in fields:
            if usage.get(key) is not None and (type(usage[key]) is not int or usage[key] < 0):
                raise ValueError("Invalid provider usage estimate")
    credits = [usage.get(fields[0]) for usage in values]
    usd = [usage.get(fields[1]) for usage in values]
    return {"estimated_credits": sum(credits) / 1_000_000 if all(v is not None for v in credits) else None,
            "estimated_usd": sum(usd) / 1_000_000 if all(v is not None for v in usd) else None,
            "status": "provider_estimates_not_invoice", "root_thread_count": len(thread_ids)}


def analyze(study: Path, grade_index: Path, output: Path, prices_path: Path | None = None,
            provider_usage_path: Path | None = None) -> dict:
    # Analysis need not run model code, but still binds frozen task and source provenance.
    design, _ = load_design(study)
    grades = json.loads(grade_index.read_text())
    prices = json.loads(prices_path.read_text()) if prices_path else None
    provider_usage = json.loads(provider_usage_path.read_text()) if provider_usage_path else None
    records = []
    for task_id in design["task_ids"]:
        for arm in design["arms"]:
            manifest_path = study / "runs" / arm / task_id / "manifest.json"
            if not manifest_path.exists():
                raise ValueError(f"Missing assigned manifest: {task_id}/{arm}; do not silently drop failures")
            manifest = json.loads(manifest_path.read_text())
            patch_path = study / "patches" / arm / f"{task_id}.json"
            if not patch_path.exists() or json.loads(patch_path.read_text())["manifest_sha256"] != digest(manifest_path):
                raise ValueError("Missing patch record or changed manifest")
            patch_record = json.loads(patch_path.read_text())
            if hashlib.sha256(patch_record["model_patch"].encode()).hexdigest() != patch_record["patch_sha256"]:
                raise ValueError("Archived prediction patch changed")
            grade_path = grades.get(arm, {}).get(task_id)
            resolved, grade_hash, grade_kind = None, None, "not_graded"
            if grade_path:
                grade_file = Path(grade_path)
                if not grade_file.is_absolute():
                    grade_file = grade_index.parent / grade_file
                resolved, grade_hash, grade_kind = read_grade(grade_file, task_id, patch_record["patch_sha256"])
            pricing = estimate_price(manifest, prices)
            state_path = manifest_path.parent / "state.json"
            state = json.loads(state_path.read_text())
            if state["run_id"] != manifest["run_id"] or state["identity_sha256"] != manifest["identity_sha256"]:
                raise ValueError("State and finalized manifest identities differ")
            subscription = subscription_for_state(state, provider_usage, digest(state_path))
            records.append({
                "task_id": task_id, "arm": arm, "status": manifest["status"],
                "model_id": manifest["selected_model"], "resolved": resolved,
                "grader_report_sha256": grade_hash, "manifest_sha256": digest(manifest_path),
                "grading_evidence": grade_kind,
                "wall_seconds": manifest["elapsed_seconds"], "expert_calls": manifest["expert_calls"],
                "input_tokens": manifest["usage"].get("input_tokens"),
                "output_tokens": manifest["usage"].get("output_tokens"),
                "cost_usd": pricing["api_equivalent_usd"], "cost_source": pricing.get("source_url"),
                "pricing": pricing,
                "subscription": subscription,
            })
    summary = summarize(records, design["task_ids"], design["arms"], design["reference"], design["seed"])
    summary["cost_definition"] = "API-equivalent model cost, not subscription bill, quota consumption, or full deployment cost"
    summary["savings"] = paired_savings(records, design)
    subscription_records = [{**row, "cost_usd": row["subscription"]["estimated_credits"]} for row in records]
    summary["estimated_subscription_credit_savings"] = paired_savings(subscription_records, design)
    summary["provenance"] = {"design_sha256": digest(study / "design.json"),
                             "grade_index_sha256": digest(grade_index),
                             "prices_sha256": digest(prices_path) if prices_path else None,
                             "provider_usage_sha256": digest(provider_usage_path) if provider_usage_path else None}
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / "records.json", records)
    write_new(output / "summary.json", summary)
    return summary


def paired_savings(records: list[dict], design: dict) -> dict:
    index = {(row["task_id"], row["arm"]): row for row in records}
    rng = np.random.default_rng(design["seed"])
    result = {}
    for arm in design["arms"]:
        if arm == design["reference"]:
            continue
        rows = [(index[task, arm], index[task, design["reference"]]) for task in design["task_ids"]]
        if any(a["cost_usd"] is None or b["cost_usd"] is None for a, b in rows):
            result[arm] = {"status": "unavailable_missing_costs", "estimated_savings_fraction": None}
            continue
        costs = np.array([[a["cost_usd"], b["cost_usd"]] for a, b in rows])
        if costs[:, 1].sum() <= 0:
            result[arm] = {"status": "unavailable_zero_reference", "estimated_savings_fraction": None}
            continue
        sampled = costs[rng.integers(0, len(rows), size=(10000, len(rows)))].sum(axis=1)
        valid = sampled[:, 1] > 0
        ratios = sampled[valid, 0] / sampled[valid, 1]
        ratio = float(costs[:, 0].sum() / costs[:, 1].sum())
        result[arm] = {"status": "descriptive_estimate", "estimated_cost_ratio": ratio,
                       "estimated_savings_fraction": 1 - ratio,
                       "paired_bootstrap_cost_ratio_95": np.quantile(ratios, [0.025, 0.975]).tolist(),
                       "valid_bootstrap_samples": int(valid.sum()),
                       "warning": "Conditional task bootstrap; tiny/clustered samples do not establish quality noninferiority"}
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Freeze public tasks, models, conditions and assignment order")
    init.add_argument("--tasks", type=Path, required=True)
    init.add_argument("--output-dir", type=Path, required=True)
    init.add_argument("--workspace-root", type=Path, required=True)
    init.add_argument("--small-model", required=True)
    init.add_argument("--large-model", required=True)
    init.add_argument("--timeout-seconds", type=float, default=900)
    init.add_argument("--seed", type=int, default=1729)
    init.add_argument("--reasoning-effort", choices=("low", "medium", "high"), default="medium")
    init.add_argument("--conditions", nargs="+", choices=personal.CONDITIONS, default=list(ARMS))
    run = commands.add_parser("run", help="Generate patches using authenticated Codex (uses plan/API quota)")
    run.add_argument("--study-dir", type=Path, required=True)
    run.add_argument("--resume", action="store_true")
    check = commands.add_parser("preflight", help="Validate model access and positive token meters (two tiny model calls)")
    check.add_argument("--study-dir", type=Path, required=True)
    analysis = commands.add_parser("analyze", help="Import independent official grades and estimate model cost")
    analysis.add_argument("--study-dir", type=Path, required=True)
    analysis.add_argument("--grades", type=Path, required=True, help="JSON {arm: {instance_id: official_report_path}}")
    analysis.add_argument("--prices", type=Path)
    analysis.add_argument("--provider-usage", type=Path, help="Output from collect_codex_usage.py with independent roots attested")
    analysis.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "init":
        initialize(args.tasks, args.output_dir, args.workspace_root, small_model=args.small_model,
                   large_model=args.large_model, timeout_seconds=args.timeout_seconds,
                   seed=args.seed, reasoning_effort=args.reasoning_effort, conditions=tuple(args.conditions))
        print(json.dumps({"status": "frozen_not_run", "study": str(args.output_dir.resolve())}))
    elif args.command == "run":
        run_study(args.study_dir, resume=args.resume)
        print(json.dumps({"status": "patch_generation_complete_ungraded"}))
    elif args.command == "preflight":
        result = preflight(args.study_dir)
        print(json.dumps(result))
        return 0 if result["ready"] else 1
    else:
        report = analyze(args.study_dir, args.grades, args.output_dir, args.prices, args.provider_usage)
        print(json.dumps({"status": report["status"], "assigned_tasks": report["assigned_tasks"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
