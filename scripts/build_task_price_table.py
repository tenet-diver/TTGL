#!/usr/bin/env python3
"""Recompute attributed historical costs and illustrative token-cost scenarios.

No model calls are made. --verify-upstream downloads the pinned public benchmark
JSON and verifies its hash and all selected per-instance cost sums.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "thesis"
MILLION = Decimal(1_000_000)
SCENARIOS = {
    "A_short_text_episode": (20_000, 0, 4_000),
    "B_long_text_episode": (100_000, 400_000, 20_000),
}


def token_cost(row: dict[str, str], counts: tuple[int, int, int]) -> Decimal | None:
    total = Decimal(0)
    columns = ("price_input_usd_per_1m", "price_cache_read_usd_per_1m", "price_output_usd_per_1m")
    for column, count in zip(columns, counts, strict=True):
        if count < 0:
            raise ValueError("Token counts must be nonnegative")
        if not count:
            continue
        if not row[column]:
            return None
        rate = Decimal(row[column])
        if not rate.is_finite() or rate < 0:
            raise ValueError("Rates must be finite and nonnegative")
        total += rate * count / MILLION
    return total


def write_csv(name: str, rows: list[dict]) -> None:
    with (DOCS / name).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-upstream", action="store_true")
    args = parser.parse_args()
    history_path = DOCS / "accuracy-context-sources.json"
    catalog_path = DOCS / "model-catalog.csv"
    source = json.loads(history_path.read_text(), parse_float=Decimal)
    selected = source["selected_historical_leaderboard_entries"]
    verification = {"status": "not_requested", "model_inference": False}
    if args.verify_upstream:
        with urlopen(source["leaderboards_url"], timeout=45) as response:
            raw = response.read()
        actual_hash = hashlib.sha256(raw).hexdigest()
        if actual_hash != source["leaderboards_sha256"]:
            raise ValueError("Pinned leaderboard content hash changed")
        board = json.loads(raw, parse_float=Decimal)
        entries = {r["folder"]: r for b in board["leaderboards"] if b["name"] == "Verified"
                   for r in b["results"] if r.get("folder")}
        for recorded in selected:
            entry = entries[recorded["folder"]]
            details = list(entry["per_instance_details"].values())
            if len(details) != recorded["per_instance_count"]:
                raise ValueError("Task denominator differs from recorded evidence")
            if any(Decimal(d["cost"]) < 0 for d in details):
                raise ValueError("Negative recorded task cost")
            summed = sum((Decimal(d["cost"]) for d in details), Decimal(0))
            if abs(summed - Decimal(recorded["cost"])) > Decimal("0.000001"):
                raise ValueError("Reported total differs from per-instance cost sum")
            if sum(d["resolved"] is True for d in details) != recorded["count_resolved_from_published_details"]:
                raise ValueError("Resolution numerator differs from recorded evidence")
        verification = {"status": "passed", "sha256": actual_hash, "rows": len(selected),
                        "task_records_checked": sum(r["per_instance_count"] for r in selected),
                        "model_inference": False}
    historical = []
    for row in selected:
        n, k, total = row["per_instance_count"], row["count_resolved_from_published_details"], Decimal(row["cost"])
        mean = total / n
        if abs(mean - Decimal(row["instance_cost"])) > Decimal("0.000001"):
            raise ValueError("Reported mean differs from total divided by task count")
        historical.append({
            "evidence_class": "historical_benchmark_reported_not_ttgl_results",
            "submission_date": row["date"], "model": row["name"], "weight_access": "open" if row["os_model"] else "closed",
            "benchmark": "SWE-bench Verified", "harness": "mini-SWE-agent 2.0.0", "assigned_tasks": n,
            "resolved_tasks": k, "resolution_percent": Decimal(k) * 100 / n,
            "reported_total_usd": total, "reported_usd_per_assigned_task": mean,
            "derived_usd_per_resolved_task": total / k if k else "",
            "cost_scope": "benchmark_reported_cost_not_invoice_or_full_infrastructure_cost",
            "source_folder": row["folder"], "source_url": source["leaderboards_url"],
        })
    write_csv("task-price-comparisons.csv", historical)
    with catalog_path.open(newline="") as stream:
        catalog = list(csv.DictReader(stream))
    illustrative = []
    for row in catalog:
        if not row["price_input_usd_per_1m"]:
            continue
        for name, counts in SCENARIOS.items():
            cost = token_cost(row, counts)
            illustrative.append({
                "evidence_class": "illustrative_token_volume_arithmetic_not_measured_task_cost",
                "as_of_utc": row["as_of_utc"], "model_id": row["model_id"], "price_service": row["price_service"],
                "scenario": name, "uncached_input_tokens": counts[0], "cache_read_tokens": counts[1],
                "output_tokens": counts[2], "api_token_cost_usd": cost if cost is not None else "",
                "cost_status": "secondary_rate_scenario" if cost is not None else "unknown_cache_read_rate",
                "accuracy": "not_measured", "price_source": row["price_source"],
            })
    write_csv("task-price-scenarios.csv", illustrative)
    report = {
        "historical_rows": len(historical), "illustrative_rows": len(illustrative),
        "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (history_path, catalog_path)},
        "upstream_verification": verification,
        "unknown_positive_token_rate_remains_unknown": token_cost({
            "price_input_usd_per_1m": "1", "price_cache_read_usd_per_1m": "", "price_output_usd_per_1m": "1"}, (1, 1, 1)) is None,
    }
    (DOCS / "task-price-checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
