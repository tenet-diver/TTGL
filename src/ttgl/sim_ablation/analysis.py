"""Audit run evidence, summarize paired outcomes and export replay manifests."""
from csv import DictWriter
from datetime import datetime
from html import escape
from itertools import product
import random
from statistics import mean, stdev

from ..experience_routing.io import canonical, digest, file_digest, read
from .memory import CONDITIONS

COMPARISONS = (("C1", "C0"), ("C2", "C1"), ("C3", "C2"), ("C3", "C0"))


def paired(values):
    """Resample independent optimization repetitions, keeping task pairings intact."""
    count = len(values)
    result = {"n_pairs": count, "differences": values, "mean": mean(values) if count else None,
              "sd": None, "standardized_mean": None, "bootstrap_95": None, "signflip_p_two_sided": None}
    if count < 2:
        return result
    deviation = stdev(values)
    threshold = abs(sum(values))
    signs = list(product((-1, 1), repeat=count))
    p = sum(abs(sum(value * sign for value, sign in zip(values, pattern))) >= threshold - 1e-12
            for pattern in signs) / len(signs)
    rng = random.Random(261118856)
    samples = sorted(mean(rng.choices(values, k=count)) for _ in range(10000))
    return {**result, "sd": deviation, "standardized_mean": mean(values) / deviation if deviation else None,
            "bootstrap_95": [samples[249], samples[9749]], "signflip_p_two_sided": p}


def _totals(entries):
    usage = [row["usage"].get("total_tokens") for row in entries]
    costs = [row.get("scenario_cost") for row in entries]
    elapsed = sum(row["elapsed_seconds"] for row in entries)
    return {"completed_native_receipts": len(entries), "unknown_usage_receipts": usage.count(None),
            "measured_tokens": sum(value for value in usage if value is not None),
            "native_tokens": sum(usage) if all(v is not None for v in usage) else None,
            "scenario_usd": sum(costs) if all(v is not None for v in costs) else None,
            "summed_invocation_seconds": elapsed, "subscription_cash_usd": None}


def _duration(entries, started):
    if not entries:
        return None
    end = max(datetime.fromisoformat(row["finished_at"]) for row in entries)
    start = min(datetime.fromisoformat(started[row["call_id"]]["started_at"]) for row in entries)
    return (end - start).total_seconds()


def _load_map(folder, pattern="*.json"):
    return {path.stem: read(path) for path in sorted(folder.glob(pattern))}


def _write(path, data):
    path.write_text(canonical(data) + "\n", encoding="utf-8")


def audit(run):
    registration = read(run / "registration.json")
    manifest = registration["identity"]
    invoked, started = {}, {}
    for entry in (run / "invocations").glob("*"):
        if (entry / "started.json").is_file():
            started[entry.name] = read(entry / "started.json")
        if (entry / "completed.json").is_file():
            row = read(entry / "completed.json")
            pending = read(entry / "pending.json")
            if not all(row[key] == value for key, value in pending.items()) or row["call_id"] != entry.name:
                raise ValueError(f"Native invocation receipt did not reconcile: {entry.name}")
            if started[entry.name]["identity_sha256"] != digest(pending):
                raise ValueError(f"Started invocation identity changed: {entry.name}")
            invoked[entry.name] = row
    grades, rounds, final = [_load_map(run / name) for name in ("cases", "rounds", "heldout")]
    for key, row in grades.items():
        actual = invoked[key]
        if not all(row[name] == actual[name] for name in
                   ("candidate_sha256", "events_sha256", "usage", "scenario_cost", "elapsed_seconds")):
            raise ValueError(f"Grade provenance did not reconcile: {key}")
    ledger_path = run / "accounting" / "usage-ledger.jsonl"
    if ledger_path.exists():
        from ..model_delegation.accounting import reconcile
        accounting = reconcile([ledger_path])
        if any(issue != "unknown_or_nonpositive_native_usage" for issue in accounting["issues"]):
            raise ValueError(f"Native accounting overlaps: {accounting['issues']}")
        ledger_refs = {row["thread_id"]: row["delta"] for row in accounting["records"]}
        if any(row["usage"] != ledger_refs.get(row["thread_id"]) for row in invoked.values()):
            raise ValueError("Native completion receipts do not match ledger counters")
    return registration, manifest, invoked, started, grades, rounds, final


def _verify_complete(run, manifest, grades, invoked, rounds, final):
    from .benchmark import evaluate, load_tasks

    freeze = read(run / "heldout-freeze.json")
    tasks = load_tasks()
    if {key: task.fingerprint for key, task in tasks.items()} != {
        key: record["sha256"] for key, record in manifest["tasks"].items()
    }:
        raise ValueError("Independent verification requires the registered benchmark source")
    allowed_holdout = {key for key, task in tasks.items() if task.split == "heldout"}
    if len(rounds) != len(final) * manifest["protocol"]["rounds"]:
        raise ValueError("Completed study is missing registered rounds")
    for prefix, assessment in final.items():
        if freeze["selections"][prefix]["harness"]["sha256"] != assessment["selected_harness_sha256"]:
            raise ValueError("Held-out assessment differs from the sealed policy")
        rows = [grades[identity] for identity in assessment["cases"]]
        if (assessment["assigned"] != len(allowed_holdout)
                or {row["task_id"] for row in rows} != allowed_holdout
                or len(rows) != len(allowed_holdout)
                or sum(row["grade"]["passed"] for row in rows) != assessment["passed"]):
            raise ValueError("Held-out denominator or grades disagree")
        for row in rows:
            if row["harness_sha256"] != assessment["selected_harness_sha256"]:
                raise ValueError("Held-out call used a different policy")
    for identity, row in grades.items():
        native = invoked[identity]
        if native["status"] == "completed" and native["candidate_integrity"]:
            actual = evaluate(tasks[row["task_id"]], native["candidate"]).to_dict()
            if actual != row["grade"]:
                raise ValueError(f"Independent grade replay disagrees: {identity}")


def summarize(run):
    registration, manifest, invoked, started, grades, rounds, final = audit(run)
    protocol = manifest["protocol"]
    fit_tasks = sum(task["split"] == "optimization" for task in manifest["tasks"].values())
    heldout_tasks = sum(task["split"] == "heldout" for task in manifest["tasks"].values())
    per_run = []
    for repetition in range(1, protocol["repetitions"] + 1):
        rep = f"r{repetition:02}"
        initial_fit = [g for k, g in grades.items() if k.startswith(rep + "-seed-fit-")]
        initial_test = [g for k, g in grades.items() if k.startswith(rep + "-seed-test-")]
        base_passed = sum(g["grade"]["passed"] for g in initial_test) if len(initial_test) == heldout_tasks else None
        for condition in CONDITIONS:
            prefix = f"{rep}-{condition.lower()}"
            assessment = final.get(prefix)
            arm_rounds = [v for k, v in rounds.items() if k.startswith(prefix + "-o")]
            arm_native = [v for k, v in invoked.items() if k.startswith(prefix + "-")]
            optimizer = [v for v in arm_native if v["editable"] is None]
            candidate = [v for v in arm_native if v["editable"] is not None and v["stage"] == "optimization"]
            evaluation = [v for v in arm_native if v["stage"] == "heldout"]
            gain = (assessment["passed"] - base_passed) / heldout_tasks if assessment and base_passed is not None else None
            opt, final_eval, total = _totals(optimizer + candidate), _totals(evaluation), _totals(arm_native)
            arm_elapsed = _duration(arm_native, started)
            opt_elapsed = _duration(optimizer + candidate, started)
            if opt["native_tokens"]:
                gain_per_tokens = None if gain is None else gain * 1e6 / opt["native_tokens"]
            else:
                gain_per_tokens = None
            # Include shared baseline work in campaign totals only. Arms are incremental search costs.
            memory_usage = {row["round"]: {"bytes": row["memory_bytes"],
                "first_request_input_tokens": row["first_request_input_tokens"],
                "cumulative_proposer_input_tokens": invoked[row["proposal_call"]]["usage"]["input_tokens"]}
                for row in arm_rounds}
            per_run.append({
                "rep": repetition, "condition": condition, "completed": assessment is not None,
                "benchmark_passed": assessment["passed"] if assessment else None,
                "benchmark_assigned": heldout_tasks, "starting_passed": base_passed,
                "heldout_rate": assessment["passed"] / heldout_tasks if assessment else None, "gain": gain,
                "heldout_cases": [{"task_id": grades[key]["task_id"], "grade": grades[key]["grade"]}
                                   for key in assessment["cases"]] if assessment else [],
                "harness_sha256": assessment["selected_harness_sha256"] if assessment else None,
                "starting_optimization_passed": sum(g["grade"]["passed"] for g in initial_fit)
                                                if len(initial_fit) == fit_tasks else None,
                "optimization_assigned": fit_tasks, "rounds_completed": len(arm_rounds),
                "rounds": [{key: row[key] for key in ("round", "retained_passed", "accepted", "decision", "regressions", "proposal", "candidate_observations")}
                           for row in arm_rounds], "memory_cost_evidence": memory_usage,
                "candidates_tested": sum(bool(r["candidate_cases"]) for r in arm_rounds),
                "candidates_accepted": sum(r["accepted"] for r in arm_rounds),
                "candidate_regressions": sum(len(r["regressions"]) for r in arm_rounds),
                "proposal_metering": _totals(optimizer), "candidate_evaluation_metering": _totals(candidate),
                "optimization_metering": opt, "heldout_metering": final_eval, "total_metering": total,
                "optimization_wall_seconds": opt_elapsed, "first_to_last_arm_seconds": arm_elapsed,
                "heldout_wall_seconds": _duration(evaluation, started),
                "gain_per_million_optimization_tokens": gain_per_tokens,
                "gain_per_optimization_hour": gain * 3600 / opt_elapsed if gain is not None and opt_elapsed else None,
                "gain_per_optimization_scenario_usd": gain / opt["scenario_usd"]
                                                      if gain is not None and opt["scenario_usd"] else None,
            })
    comparisons = {}
    for first, second in COMPARISONS:
        pairs = [(a, b) for a in per_run for b in per_run if a["rep"] == b["rep"]
                 and a["condition"] == first and b["condition"] == second and a["completed"] and b["completed"]]
        valid = [a["heldout_rate"] - b["heldout_rate"] for a, b in pairs]
        efficiency = [a["gain_per_million_optimization_tokens"] - b["gain_per_million_optimization_tokens"]
                      for a, b in pairs if a["gain_per_million_optimization_tokens"] is not None
                      and b["gain_per_million_optimization_tokens"] is not None]
        comparisons[f"{first}-{second}"] = {"heldout_rate": paired(valid), "gain_per_million_tokens": paired(efficiency)}
    by_condition = {}
    for arm in CONDITIONS:
        rows = [r for r in per_run if r["condition"] == arm and r["completed"]]
        outcomes = [r["heldout_rate"] for r in rows]
        by_condition[arm] = {"completed_runs": len(rows), "mean_heldout_rate": mean(outcomes) if rows else None,
                             "sd_heldout_rate": stdev(outcomes) if len(rows) > 1 else None}
    completed = len(final) == protocol["repetitions"] * len(CONDITIONS) and set(started) == set(invoked)
    if completed:
        _verify_complete(run, manifest, grades, invoked, rounds, final)
    return {"id": protocol["id"], "complete": completed, "status": "completed" if completed else "incomplete",
            "protocol": protocol, "registration_sha256": file_digest(run / "registration.json"),
            "bank_sha256": manifest["bank_sha256"], "git_commit": registration["git_commit"],
            "cli": manifest["cli"], "cli_sha256": manifest["cli_sha256"], "benchmark": protocol["benchmark"],
            "by_condition": by_condition, "per_run": per_run, "paired_comparisons": comparisons,
            "historical": {"new_calls": 0, "source_trials": 3, "note": "Reused previously measured Observatory trials"},
            "ongoing_or_ambiguous": sorted(set(started) - set(invoked)),
            "stages": {name: _totals([v for v in invoked.values() if v["stage"] == name])
                       for name in ("optimization", "heldout")},
            "totals": _totals(list(invoked.values())),
            "pilot_wall_seconds": _duration(list(invoked.values()), started),
            "independent_grade_replays": sum(invoked[key]["status"] == "completed" and bool(invoked[key]["candidate_integrity"])
                                             for key in grades) if completed else None,
            "memory_accounting": "Bytes of model-prompt projection and first native request input are recorded. First input includes system context. Repeated memory and run observations are included in measured native tokens.",
            "scope": "Single-rollout objective Python repair evaluations. A paired repetition, not a task rollout, is the independent optimization unit."}


def _csv(path, rows):
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _chart(output, summary):
    colors = ("#5ba9f7", "#c59afc", "#55cd96", "#ffb959")
    w, h = 790, 345
    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title">',
                '<title id="title">Retained harness optimization pass rates and held-out performance</title>',
                '<rect width="100%" height="100%" fill="#111725"/>',
                '<g font-family="sans-serif" fill="#eef4fc">',
                '<text x="25" y="32" font-size="21">Retained harness performance</text>',
                '<text x="70" y="61" font-size="13">Optimization tasks</text>',
                '<text x="549" y="61" font-size="13">Held-out tasks</text>']
    top, bottom = 85, 272
    for pct in (0, 25, 50, 75, 100):
        y = bottom - (bottom - top) * pct / 100
        elements.append(f'<line x1="65" x2="735" y1="{y}" y2="{y}" stroke="#344056"/>')
        elements.append(f'<text x="20" y="{y+4}" font-size="12">{pct}%</text>')
    for i in range(6):
        x = 80 + i * 68
        elements.append(f'<text x="{x-4}" y="299" font-size="12">{i}</text>')
    elements.append('<text x="216" y="325" font-size="12">Optimization round</text>')
    elements.append('<path d="M500 70V305" stroke="#344056" fill="none"/>')
    for index, (arm, color) in enumerate(zip(CONDITIONS, colors)):
        rows = [r for r in summary["per_run"] if r["condition"] == arm and r["rounds"]]
        if rows:
            values = [mean(r["starting_optimization_passed"] / r["optimization_assigned"] for r in rows)]
            for position in range(5):
                later = [r for r in rows if len(r["rounds"]) > position]
                if later:
                    values.append(mean(r["rounds"][position]["retained_passed"] / r["optimization_assigned"] for r in later))
            points = " ".join(f"{80 + 68*i},{bottom-(bottom-top)*val}" for i, val in enumerate(values))
            dash = ("0", "8 3", "4 4", "1 5")[index]
            elements.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2" stroke-dasharray="{dash}"/>')
        value = summary["by_condition"][arm]["mean_heldout_rate"]
        x = 550 + 44*index
        if value is not None:
            height = (bottom - top) * value
            elements.append(f'<rect x="{x}" y="{bottom-height}" width="23" height="{height}" fill="{color}"/>')
        elements.append(f'<text x="{x}" y="299" font-size="12" fill="{color}">{escape(arm)}</text>')
    elements.append("</g></svg>")
    (output / "performance.svg").write_text("\n".join(elements) + "\n")


def report(run, output, *, reproduce=False):
    output.mkdir(exist_ok=True, parents=True)
    summary = summarize(run)
    _write(output / "summary.json", summary)
    _csv(output / "conditions.csv", [
        {**{key: row[key] for key in ("rep", "condition", "completed", "starting_passed", "benchmark_passed",
          "benchmark_assigned", "gain", "candidates_tested", "candidates_accepted", "candidate_regressions",
          "optimization_wall_seconds", "heldout_wall_seconds", "gain_per_million_optimization_tokens",
          "gain_per_optimization_hour", "gain_per_optimization_scenario_usd")},
         "optimization_tokens": row["optimization_metering"]["native_tokens"],
         "heldout_tokens": row["heldout_metering"]["native_tokens"],
         "scenario_usd": row["total_metering"]["scenario_usd"]}
        for row in summary["per_run"]])
    _csv(output / "rounds.csv", [
        {"rep": row["rep"], "condition": row["condition"], **{key: r[key] for key in ("round", "retained_passed", "accepted", "decision")},
         "assigned": row["optimization_assigned"], "regressions": len(r["regressions"]),
         **row["memory_cost_evidence"][r["round"]]} for row in summary["per_run"] for r in row["rounds"]])
    _chart(output, summary)
    if reproduce:
        # Retain trace receipts and content digests. Raw native bytes stay in local S3.
        paths = [run / "registration.json", *run.glob("heldout-freeze.json"),
                 *run.glob("harnesses/*.json"), *run.glob("rounds/*.json"), *run.glob("cases/*.json"),
                 *run.glob("invocations/*/pending.json"), *run.glob("invocations/*/started.json"),
                 *run.glob("invocations/*/completed.json"), *run.glob("retention/*.json")]
        manifest = [{"path": str(path.relative_to(run)), "sha256": file_digest(path)} for path in sorted(paths)]
        _write(output / "reproduction-manifest.json", {"artifacts": manifest, "summary_sha256": file_digest(output / "summary.json")})
        with (output / "observations.jsonl").open("w", encoding="utf-8") as stream:
            for key, row in _load_map(run / "cases").items():
                stream.write(canonical({"case": key, **row}) + "\n")
    print(f"{summary['id']}: {summary['status']}, {summary['totals']['completed_native_receipts']} native receipts")
