#!/usr/bin/env python3
"""Summarize executed official SWE-bench controls; makes no model calls."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {"psf__requests-5414": "requests5414", "sympy__sympy-17139": "sympy17139"}
IMAGES = {
    "psf__requests-5414": "swebench/sweb.eval.x86_64.psf_1776_requests-5414@sha256:71c78211f16803c111ed1807ded20f8defd5f6917fb958ace4e076d5ea7d8b10",
    "sympy__sympy-17139": "swebench/sweb.eval.x86_64.sympy_1776_sympy-17139@sha256:9a8111742e0548816d920a27ba259ebde7647f4e46e7522c61647990dd35713c",
}


def summarize(root: Path) -> dict:
    records, inputs, pairs = [], {}, []
    for instance, short in TARGETS.items():
        pair = {}
        for kind in ("base", "gold"):
            run_id = f"ttgl-verified-001-{kind}-{short}"
            folder = root / "logs/evaluation" / run_id / ("gold" if kind == "gold" else "base-control") / instance
            report = json.loads((folder / "report.json").read_text())[instance]
            status = report["tests_status"]
            row = {
                "instance_id": instance, "control": kind, "run_id": run_id,
                "resolved": report["resolved"], "patch_successfully_applied": report["patch_successfully_applied"],
                "official_infra_failure": report["infra_failure"],
                "tests": {name: {outcome: len(names) for outcome, names in values.items()}
                          for name, values in status.items()},
                "report": str((folder / "report.json").relative_to(root)),
                "image_observed_repo_digest": IMAGES[instance],
            }
            records.append(row)
            pair[kind] = row
            for path in sorted(folder.iterdir()):
                if path.is_file():
                    inputs[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
        valid = (pair["gold"]["resolved"] is True
                 and pair["base"]["resolved"] is False
                 and pair["base"]["tests"]["FAIL_TO_PASS"]["failure"] > 0
                 and pair["base"]["tests"]["PASS_TO_PASS"]["failure"] == 0)
        pairs.append({"instance_id": instance, "control_pair_valid": valid})
    return {
        "schema_version": 1,
        "evidence_class": "executed_official_evaluator_controls_not_model_experiment",
        "model_inference_calls": 0,
        "control_runs_executed": len(records),
        "instances_control_checked": len(pairs),
        "control_pairs_valid": sum(p["control_pair_valid"] for p in pairs),
        "selected_tasks": 12,
        "selected_tasks_without_controls": 12 - len(pairs),
        "all_selected_tasks_environment_validated": False,
        "quality_or_cost_savings_estimate": None,
        "requests_diagnosis": "Gold resolves the target regression but seven declared PASS_TO_PASS checks fail; full pytest log also contains 158 fixture setup errors. Proxy-sensitive behavior and missing httpbin fixture plugin prevent readiness. Original official artifacts retained; tests and proxy not weakened.",
        "pairs": pairs, "records": records, "input_sha256": inputs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "experiments/swe-bench-verified-001/controls")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = summarize(args.root.resolve())
    output = args.output or args.root / "summary.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"records", "input_sha256"}}, indent=2))


if __name__ == "__main__":
    main()
