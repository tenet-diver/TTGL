"""Preregistered routing replay on paired, published coding outcomes.

This module does not call models or execute benchmark code. Each task's ten
upstream samples estimate its pass@1. Splits and policies are fixed before test
outcomes are summarized. All routing features are observable before inference.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import time
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.special import logit
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning

SEED = 1729


def read_rows(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f if line.strip()]


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def outcome(rows: list[dict], name: str) -> np.ndarray:
    result = []
    for row in rows:
        values = row[name]
        if len(values) != 10 or any(type(v) is not bool for v in values):
            raise ValueError("Expected exactly ten boolean published grades per task")
        result.append(np.mean(values))
    return np.asarray(result, dtype=float)


def fit_soft_logistic(x, y, seed: int = SEED):
    """Bernoulli log loss with one unit of weight per task, not per sample."""
    if len(y) < 2 or np.all(y == y[0]) and y[0] in (0, 1):
        raise ValueError("Nondegenerate training outcomes are required")
    xx = sparse.vstack([x, x]) if sparse.issparse(x) else np.vstack([x, x])
    labels = np.r_[np.zeros(len(y)), np.ones(len(y))]
    weights = np.r_[1 - y, y]
    model = LogisticRegression(C=1.0, solver="liblinear", max_iter=2000,
                               random_state=seed)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        model.fit(xx, labels, sample_weight=weights)
    return model


def log_odds(p):
    return logit(np.clip(p, 1e-6, 1 - 1e-6)).reshape(-1, 1)


def calibrated_predictions(model, x_cal, y_cal, x_test):
    p_cal = model.predict_proba(x_cal)[:, 1]
    calibrator = fit_soft_logistic(log_odds(p_cal), y_cal)
    p_test_raw = model.predict_proba(x_test)[:, 1]
    p_test = calibrator.predict_proba(log_odds(p_test_raw))[:, 1]
    return p_test, p_test_raw, calibrator


def exact_budget_mask(scores, fraction: float, task_ids: list[str]):
    if not 0 <= fraction <= 1:
        raise ValueError("Budget fraction must be in [0,1]")
    scores = np.asarray(scores)
    if len(scores) != len(task_ids) or not np.all(np.isfinite(scores)):
        raise ValueError("Invalid routing scores")
    k = int(np.floor(len(scores) * fraction + 1e-12))
    # A stable identifier only breaks score ties; it is not a model feature.
    order = np.lexsort((np.asarray(task_ids), -scores))
    mask = np.zeros(len(scores), dtype=float)
    mask[order[:k]] = 1
    return mask


def policy_outcomes(local, remote, allocation):
    return (1 - allocation) * local + allocation * remote


def cluster_bootstrap_indices(groups, repeats: int, seed: int = SEED):
    groups = np.asarray(groups)
    keys = np.unique(groups)
    members = {key: np.flatnonzero(groups == key) for key in keys}
    rng = np.random.default_rng(seed)
    for _ in range(repeats):
        yield np.concatenate([members[key] for key in rng.choice(keys, len(keys), replace=True)])


def bootstrap_interval(values, indices):
    means = np.asarray([np.mean(values[i]) for i in indices])
    return {"estimate": float(np.mean(values)),
            "ci95": np.quantile(means, [0.025, 0.975]).tolist(),
            "one_sided_lower95": float(np.quantile(means, 0.05))}


def reliability(p, y):
    boundaries = np.unique(np.quantile(p, np.linspace(0, 1, 6)))
    bins = np.digitize(p, boundaries[1:-1])
    records = []
    for b in np.unique(bins):
        selected = bins == b
        records.append({"n_tasks": int(selected.sum()),
                        "predicted": float(p[selected].mean()),
                        "observed": float(y[selected].mean())})
    return records


def ece_ten_bins(p, y):
    bins = np.minimum((p * 10).astype(int), 9)
    return float(sum(np.mean(bins == b) * abs(np.mean(p[bins == b]) - np.mean(y[bins == b]))
                     for b in np.unique(bins)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/routing-pilot"))
    parser.add_argument("--protocol", type=Path, default=Path("docs/research/protocol.md"))
    parser.add_argument("--freeze", type=Path, default=Path("docs/research/protocol-freeze.json"))
    parser.add_argument("--bootstrap", type=int, default=2000)
    args = parser.parse_args(argv)
    if args.bootstrap != 2000:
        raise ValueError("The frozen pilot protocol uses 2000 bootstrap replicates")
    freeze = json.loads(args.freeze.read_text())
    if hash_file(args.protocol) != freeze["protocol_sha256"]:
        raise ValueError("Protocol differs from the frozen pre-analysis document")
    if "amendment_sha256" not in freeze or hash_file(args.protocol.parent / "protocol-amendments.md") != freeze["amendment_sha256"]:
        raise ValueError("Pre-analysis amendment differs from the frozen version")
    if hash_file(args.data_dir / "split-manifest.json") != freeze["split_manifest_sha256"]:
        raise ValueError("Dataset split differs from the frozen allocation")
    split_manifest = json.loads((args.data_dir / "split-manifest.json").read_text())
    for name in ("train", "calibration", "test"):
        if hash_file(args.data_dir / f"{name}.jsonl") != split_manifest["splits"][name]["sha256"]:
            raise ValueError(f"Processed {name} data differ from the frozen manifest")
    if args.output_dir.exists():
        raise FileExistsError("Use a new output directory; do not overwrite recorded runs")
    started = time.perf_counter()
    rows = {s: read_rows(args.data_dir / f"{s}.jsonl") for s in ("train", "calibration", "test")}
    train, cal, test = (rows[s] for s in ("train", "calibration", "test"))
    # Only prompt text and its character length enter the fitted feature map.
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=5000,
                                 sublinear_tf=True)
    scaler = StandardScaler()
    x_train_text = vectorizer.fit_transform([r["prompt"] for r in train])
    train_lengths = np.log1p([len(r["prompt"]) for r in train]).reshape(-1, 1)
    x_train = sparse.hstack([x_train_text, scaler.fit_transform(train_lengths)], format="csr")

    def transform(part):
        lengths = np.log1p([len(r["prompt"]) for r in part]).reshape(-1, 1)
        return sparse.hstack([vectorizer.transform([r["prompt"] for r in part]),
                              scaler.transform(lengths)], format="csr")

    x_cal, x_test = transform(cal), transform(test)
    model_local = fit_soft_logistic(x_train, outcome(train, "local_grades"))
    model_remote = fit_soft_logistic(x_train, outcome(train, "teacher_grades"))
    p_local, raw_local, calibrator_local = calibrated_predictions(
        model_local, x_cal, outcome(cal, "local_grades"), x_test)
    p_remote, raw_remote, calibrator_remote = calibrated_predictions(
        model_remote, x_cal, outcome(cal, "teacher_grades"), x_test)
    # Freeze scores and fitted estimators before reading test labels.
    ids = [r["task_id"] for r in test]
    delta = p_remote - p_local
    fixed_scores = {"benefit_router": delta,
                    "local_failure_router": 1 - p_local,
                    "length_rule": np.asarray([len(r["prompt"]) for r in test]),
                    "seeded_random": np.random.default_rng(SEED).random(len(test))}
    allocations = {}
    for budget in (0.0, 0.25, 0.5, 0.75, 1.0):
        for name, scores in fixed_scores.items():
            allocations[(name, budget)] = exact_budget_mask(scores, budget, ids)
        b = np.floor(len(test) * budget) / len(test)
        allocations[("random_expected", budget)] = np.full(len(test), b)

    local, remote = outcome(test, "local_grades"), outcome(test, "teacher_grades")
    groups = [str(r["platform"]) + ":" + str(r["contest_id"]) for r in test]
    boot = list(cluster_bootstrap_indices(groups, args.bootstrap))
    # Oracle sees test labels solely as an explicitly nondeployable upper bound.
    for budget in (0.0, 0.25, 0.5, 0.75, 1.0):
        allocations[("oracle_upper_bound", budget)] = exact_budget_mask(remote - local, budget, ids)
    policy_records = []
    for (name, budget), allocation in allocations.items():
        value = policy_outcomes(local, remote, allocation)
        interval = bootstrap_interval(value, boot)
        b = float(allocation.mean())
        record = {"policy": name, "requested_remote_fraction": budget,
                  "actual_remote_fraction": b, "pass_at_1": interval["estimate"],
                  "ci95_low": interval["ci95"][0], "ci95_high": interval["ci95"][1]}
        for ratio in (0.0, 0.01, 0.05, 0.10, 0.25):
            # Remote per-call cost normalized to 1. Costs are scenarios, not measured.
            record[f"precall_cost_local_{ratio:.2f}"] = (1-b) * ratio + b
            record[f"postlocal_cost_local_{ratio:.2f}"] = ratio + b
        record["local_accepted_work_contribution"] = float(np.mean((1-allocation)*local))
        policy_records.append(record)
    primary = policy_outcomes(local, remote, allocations[("benefit_router", 0.5)])
    random_expected = policy_outcomes(local, remote, allocations[("random_expected", 0.5)])
    primary_contrast = bootstrap_interval(primary - random_expected, boot)
    vs_remote = bootstrap_interval(primary - remote, boot)
    summary = {
        "experiment_type": "published_output_replay_not_fresh_inference",
        "n_tasks": {key: len(value) for key, value in rows.items()},
        "n_test_contest_groups": len(set(groups)),
        "n_samples_per_model_per_task": 10, "seed": SEED,
        "local_model": "Qwen2.5-Coder-Ins-7B", "remote_model": "DeepSeek-V3",
        "local_test_pass_at_1": bootstrap_interval(local, boot),
        "remote_test_pass_at_1": bootstrap_interval(remote, boot),
        "primary_benefit_minus_expected_random_at_half_budget": primary_contrast,
        "primary_positive_two_sided95": bool(primary_contrast["ci95"][0] > 0),
        "exploratory_benefit_minus_remote_at_half_budget": vs_remote,
        "exploratory_noninferiority_margin": -0.05,
        "exploratory_noninferiority_supported": bool(vs_remote["one_sided_lower95"] > -0.05),
        "fixed_model_conditional_cluster_bootstrap_repeats": args.bootstrap,
        "calibration": {
            "local_sample_brier_raw": float(np.mean(raw_local**2 - 2*raw_local*local + local)),
            "local_sample_brier_platt": float(np.mean(p_local**2 - 2*p_local*local + local)),
            "remote_sample_brier_raw": float(np.mean(raw_remote**2 - 2*raw_remote*remote + remote)),
            "remote_sample_brier_platt": float(np.mean(p_remote**2 - 2*p_remote*remote + remote)),
            "local_ece_ten_equal_width_bins": ece_ten_bins(p_local, local),
            "remote_ece_ten_equal_width_bins": ece_ten_bins(p_remote, remote),
            "local_reliability": reliability(p_local, local),
            "remote_reliability": reliability(p_remote, remote),
        },
        "test_outcome_joint_counts": {
            "remote_mean_above_local": int(np.sum(remote > local)),
            "local_mean_above_remote": int(np.sum(local > remote)),
            "equal_means": int(np.sum(remote == local)),
        },
        "interpretation_limits": [
            "No measured inference latency, energy, GPU spend, or token costs.",
            "Uncertainty resamples contest groups conditional on fitted policies and published sample means.",
            "Historical benchmark contamination and generation settings limit causal/generalization claims.",
            "Oracle uses test outcomes and is not deployable.",
            "No LoRA, logits distillation, RLAIF or new agent execution measured in this run.",
        ],
    }
    args.output_dir.mkdir(parents=True)
    frame = pd.DataFrame(policy_records).sort_values(["policy", "requested_remote_fraction"])
    frame.to_csv(args.output_dir / "policies.csv", index=False)
    predictions = pd.DataFrame({"task_id": ids, "contest_group": groups,
                                "p_local": p_local, "p_remote": p_remote,
                                "predicted_remote_gain": delta,
                                "observed_local_pass_at_1": local,
                                "observed_remote_pass_at_1": remote})
    for name in fixed_scores:
        predictions[f"{name}_remote_at_half"] = allocations[(name, 0.5)].astype(int)
    predictions.to_csv(args.output_dir / "predictions.csv", index=False)
    subgroup_records = []
    for field in ("platform", "difficulty"):
        labels = np.asarray([str(r[field]) for r in test])
        for label in sorted(set(labels)):
            selected = labels == label
            subgroup_records.append({"field": field, "value": label, "n_tasks": int(selected.sum()),
                                     "local_pass_at_1": float(local[selected].mean()),
                                     "remote_pass_at_1": float(remote[selected].mean()),
                                     "benefit_router_pass_at_1": float(primary[selected].mean()),
                                     "benefit_remote_fraction": float(allocations[("benefit_router", 0.5)][selected].mean())})
    pd.DataFrame(subgroup_records).to_csv(args.output_dir / "subgroups.csv", index=False)
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    import joblib
    joblib.dump({"vectorizer": vectorizer, "scaler": scaler,
                 "local_model": model_local, "remote_model": model_remote,
                 "local_calibrator": calibrator_local, "remote_calibrator": calibrator_remote},
                args.output_dir / "fitted-router.joblib")
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
    for name in ("random_expected", "length_rule", "local_failure_router", "benefit_router", "oracle_upper_bound"):
        part = frame[frame.policy == name]
        axs[0].plot(part.actual_remote_fraction, part.pass_at_1, marker="o", label=name.replace("_", " "))
    axs[0].set(xlabel="Fraction routed to remote model", ylabel="Published-sample mean pass@1",
               title="Held-out chronological routing replay")
    axs[0].legend(fontsize=7)
    axs[0].grid(alpha=0.25)
    for name in ("local", "remote"):
        points = summary["calibration"][f"{name}_reliability"]
        axs[1].plot([p["predicted"] for p in points], [p["observed"] for p in points], marker="o", label=name)
    axs[1].plot([0, 1], [0, 1], "k--", alpha=0.4)
    axs[1].set(xlabel="Predicted probability (Platt calibrated)", ylabel="Observed sample pass rate",
               title="Test reliability (five quantile bins)", xlim=(0, 1), ylim=(0, 1))
    axs[1].legend()
    fig.tight_layout()
    for extension in ("png", "svg"):
        fig.savefig(args.output_dir / f"routing-and-calibration.{extension}", dpi=180)
    plt.close(fig)
    manifest = {"protocol_sha256": hash_file(args.protocol),
                "amendment_sha256": freeze["amendment_sha256"],
                "split_manifest_sha256": hash_file(args.data_dir / "split-manifest.json"),
                "code_sha256": hash_file(Path(__file__)),
                "python": platform.python_version(), "platform": platform.platform(),
                "packages": {name: importlib.metadata.version(name) for name in
                             ("numpy", "scipy", "pandas", "scikit-learn", "matplotlib")},
                "analysis_wall_seconds": time.perf_counter() - started,
                "input_sha256": {s: hash_file(args.data_dir / f"{s}.jsonl") for s in rows},
                "files": {p.name: hash_file(p) for p in sorted(args.output_dir.iterdir())}}
    (args.output_dir / "run-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
