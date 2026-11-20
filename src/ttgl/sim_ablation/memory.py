"""Freeze measured Observatory experiments and project their historical memory."""
from pathlib import Path

from ..experience_routing.io import canonical, digest, file_digest, read, write_new

CONDITIONS = ("C0", "C1", "C2", "C3")
STUDIES = Path("tools/usage-monitor/studies")


def _record(root, result_file, result, *, study_id, parent, model, cli,
            benchmark, modification, prediction, hypothesis, rationale, lesson):
    cells = result["cells"]
    if not cells or not all(c["captures_complete"] for c in cells):
        raise ValueError(f"Incomplete observed evidence for {study_id}")
    protocol = STUDIES / f"{study_id.removesuffix('-001')}-protocol-001.json"
    if study_id.startswith("progress"):
        protocol = STUDIES / f"progress-replay-protocol-{study_id[-3:]}.json"
    protocol_sha = file_digest(root / protocol)
    if protocol_sha != result["protocol_sha256"]:
        raise ValueError(f"Protocol hash mismatch for {study_id}")
    baseline = [c for c in cells if c["condition"] == "raw"]
    candidate = [c for c in cells if c["condition"] == "compact"]
    if not baseline or sorted(c["case"] for c in baseline) != sorted(c["case"] for c in candidate):
        raise ValueError(f"Unmatched observing tasks for {study_id}")
    for arm, name in ((baseline, "raw"), (candidate, "compact")):
        if sum(c["usage"]["total_tokens"] for c in arm) != result[f"{name}_total_tokens"]:
            raise ValueError(f"Usage mismatch for {study_id}")
    outcome = {
        "baseline_passed": sum(c["quality"]["passed"] for c in baseline),
        "candidate_passed": sum(c["quality"]["passed"] for c in candidate),
        "tasks": len(candidate),
        "baseline_tokens": result["raw_total_tokens"],
        "candidate_tokens": result["compact_total_tokens"],
        "baseline_seconds": round(result["raw_wall_seconds"], 3),
        "candidate_seconds": round(result["compact_wall_seconds"], 3),
    }
    return {
        "experiment_id": study_id,
        "parent_id": parent,
        "benchmark": benchmark,
        "task_ids": sorted(c["case"] for c in baseline),
        "starting_harness": "historical native Codex with the registered raw tool-result path",
        "modification": modification,
        "observed": outcome,
        "classification": "success" if result["acceptance_passed"] else "failure",
        "model": model,
        "cli": cli,
        "prediction": prediction,
        "hypothesis": hypothesis,
        "rationale": rationale,
        "lesson": lesson,
        "annotation_provenance": "Investigator synopsis of registered protocols and measured reports. Hypotheses are interpretations.",
        "evidence": {
            "result": str(result_file),
            "result_sha256": file_digest(root / result_file),
            "protocol": str(protocol),
            "protocol_sha256": protocol_sha,
            "trace_refs": [c["task_id"] for c in cells],
            "implementation": result.get("implementation", result.get("candidate_sha256")),
        },
    }


def build_bank(root):
    live_file = STUDIES / "live-harness-results-001.json"
    live = read(root / live_file)
    replay_file = STUDIES / "progress-replay-results-002.json"
    replay = read(root / replay_file)
    first, second = replay["evaluations"]
    replay_fields = {
        "model": replay["model"], "cli": replay["codex_cli"],
        "benchmark": "Observatory log-diagnosis development replay, including explicit synthetic input variants",
    }
    records = [
        _record(root, replay_file, first, study_id="progress-replay-001", parent=None, **replay_fields,
                modification="Suppress repeated transient progress rows while keeping a raw evidence path.",
                prediction="Reduce pooled tokens by at least 10% and pass every registered check in both arms.",
                hypothesis="Repeated progress can crowd out the diagnostic signal and source coverage indicators.",
                rationale="Use exact-format filtering to preserve diagnostic events and maintain access to original evidence.",
                lesson="A smaller representation is insufficient when scope warnings are missed. Two raw-arm answers missed incomplete-source evidence."),
        _record(root, replay_file, second, study_id="progress-replay-002", parent="progress-replay-001", **replay_fields,
                modification="Keep the progress filter and add explicit source coverage metadata to both arms.",
                prediction="Reduce pooled tokens by at least 10% and pass every registered check in both arms.",
                hypothesis="The earlier quality gate failed because disclosure of missing source context was hard to locate.",
                rationale="Put coverage by the evidence to keep it accessible when tool output is large.",
                lesson="Explicit coverage makes bounded evidence easier to interpret. Fresh transfer remains unmeasured."),
        _record(root, live_file, live, study_id="live-harness-001", parent=None,
                model=live["model"], cli="0.166.0",
                benchmark="Observatory code-edit-and-test development fixtures",
                modification="Group repetitive shell results reversibly with exact inverse checks; allow access to the original.",
                prediction="Both compact tasks use real transforms, all independent checks pass and pooled native tokens drop at least 5%.",
                hypothesis="Repeated long results are presented again in subsequent requests and inflate token consumption.",
                rationale="Keep source detail accessible while avoiding repeated transmission of equivalent text.",
                lesson="Choose focused test and inspection output with access to detail on failure. This small trial showed no speedup."),
    ]
    if {r["classification"] for r in records} != {"success", "failure"}:
        raise ValueError("Both historical outcomes are required")
    return {"schema": 1, "records": records, "classification_rule": "Passed the source trial's preregistered quality and token gates"}


def freeze_bank(root, path):
    bank = build_bank(root)
    document = {**bank, "sha256": digest(bank)}
    if path.exists():
        if read(path) != document:
            raise ValueError("Frozen historical bank differs")
    else:
        write_new(path, document)
    return document


def read_bank(path):
    document = read(path)
    body = {key: value for key, value in document.items() if key != "sha256"}
    if body.get("schema") != 1 or digest(body) != document.get("sha256"):
        raise ValueError("Invalid frozen historical bank")
    return document


def project(bank, condition):
    """Use positive field selection so traces and excluded explanations cannot leak."""
    if condition not in CONDITIONS:
        raise ValueError("Unknown memory condition")
    if condition == "C0":
        return []
    fields = ("experiment_id", "benchmark", "modification", "observed", "classification", "model")
    if condition == "C3":
        fields += ("parent_id", "prediction", "hypothesis", "rationale", "lesson")
    return [{key: row[key] for key in fields}
            for row in bank["records"] if condition != "C1" or row["classification"] == "success"]


def memory_text(bank, condition):
    return "\n".join(canonical(row) for row in project(bank, condition))
