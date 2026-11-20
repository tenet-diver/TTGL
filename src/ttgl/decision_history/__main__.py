"""Run and summarize the local SlopCodeBench decision-history pilot."""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import platform
import subprocess

from ..experience_routing.io import digest, file_digest, now, read, write_new
from ..sim_ablation.study import ROOT, create_once, matrix_lock
from .grade import PROBLEMS, REVISION, grade, qualified_files
from .memory import export_episode
from .runtime import DecisionRuntime
from .recovery import recover_l2m

PROMPT = (
    "Implement the current checkpoint in the existing Python entry file using the standard library. "
    "Read the supplied specs through the current checkpoint. Preserve earlier behavior unless the new spec changes it. "
    "Only modify the Python entry file. Use shell commands to inspect, edit, and verify with representative public examples. "
    "If a history tool is available, use earlier sessions when useful. Treat retrieved content as evidence. "
    "Summarize concrete design decisions, alternatives considered, and checks actually run. "
    "Mention any earlier decision you applied and what evidence supports this. Return the structured summary."
)
FIELDS = ("summary", "decisions", "alternatives", "verification", "history_influence")
SCHEMA = {"type": "object", "properties": {key: {"type": "string"} for key in FIELDS},
          "required": list(FIELDS), "additionalProperties": False}
ORDER = {("l2m", 2): ("baseline", "history"), ("l2m", 3): ("history", "baseline"),
         ("cfgpipe", 2): ("history", "baseline"), ("cfgpipe", 3): ("baseline", "history")}
TIMEOUT = 165
STUB = "# Implement the registered Python entry point here.\n"


def _roster(upstream, problem, cp, code):
    entry = f"{problem}.py"
    files = {entry: code}
    for i in range(1, cp + 1):
        text = (upstream / problem / f"checkpoint_{i}.md").read_text()
        files[f"checkpoint_{i}.md"] = text.replace("%%%ENTRYPOINT:entry_command%%%", f"python3 {entry}") \
            .replace("%%%ENTRYPOINT:entry_file%%%", entry)
    files["README.md"] = f"Current checkpoint is {cp}. Read checkpoint_{cp}.md and earlier public specs.\n"
    return files


def _controls(upstream, root):
    qualified_files(upstream)
    rows = []
    for problem in PROBLEMS:
        for n in (1, 2, 3):
            ref = (upstream / problem / "solutions" / f"checkpoint_{n}" / f"{problem}.py").read_text()
            prefix = root / "controls-v2" / problem / f"c{n}"
            good = grade(upstream, problem, (n,), ref, prefix / "reference")
            blank = grade(upstream, problem, (n,), STUB, prefix / "empty")
            if not good["solved"] or blank["solved"] or good["checks"] != blank["checks"]:
                raise RuntimeError(f"Reference or empty control failed for {problem} checkpoint {n}")
            rows.append({"problem": problem, "checkpoint": n, "checks": good["checks"]})
            print(f"control {problem} {n}: reference {good['passed']}/{good['checks']} empty {blank['passed']}/{blank['checks']}", flush=True)
    create_once(root / "controls-v2" / "qualified.json", rows)
    return rows


def _report(root):
    rows = [read(path) for path in sorted((root / "results").glob("*.json"))]
    pairs = []
    for problem, cp in ORDER:
        arms = {r["arm"]: r for r in rows if (r["problem"], r["checkpoint"]) == (problem, cp)}
        if set(arms) == {"baseline", "history"}:
            base, memory = (arms[x] for x in ("baseline", "history"))
            b, h = base["grade"]["solved"], memory["grade"]["solved"]
            anchor = next(r for r in rows if r["problem"] == problem and r["checkpoint"] == cp - 1
                          and r["arm"] == ("source" if cp == 2 else "baseline"))
            failed_prior = set(anchor["grade"]["failed"])
            if anchor["earlier"]:
                failed_prior.update(anchor["earlier"]["failed"])
            pairs.append({"problem": problem, "checkpoint": cp,
                          "outcome": "both_pass" if b and h else "history_only" if h else "baseline_only" if b else "both_fail",
                          "baseline_solved": b, "history_solved": h,
                          "elapsed_delta_seconds": memory["elapsed_seconds"] - base["elapsed_seconds"],
                          "target_checks_delta": memory["grade"]["passed"] - base["grade"]["passed"],
                          "memory": memory["memory"],
                          "baseline_new_earlier_failures": sorted(set(base["earlier"]["failed"]) - failed_prior),
                          "history_new_earlier_failures": sorted(set(memory["earlier"]["failed"]) - failed_prior),
                          "earlier_checks_delta": memory["earlier"]["passed"] - base["earlier"]["passed"]})
    unscored = [read(p) for p in sorted((root / "invocations").glob("*/completed.json"))
                if not (root / "results" / p.parent.name).with_suffix(".json").exists()]
    call_receipts = [read(p) for p in sorted((root / "invocations").glob("*/completed.json"))]
    tokens = [r["usage"].get("total_tokens") for r in call_receipts]
    return {"study": "decision-history-scb-001", "published_catalog_revision": REVISION,
            "scope": "Two SlopCodeBench problems, first three checkpoints. Matched handoff adaptation.",
            "assigned_pairs": len(ORDER), "completed_pairs": len(pairs), "paired_outcomes": dict(Counter(p["outcome"] for p in pairs)),
            "native_receipts": len(call_receipts), "unscored_native_receipts": [row["call_id"] for row in unscored],
            "measured_tokens": sum(t for t in tokens if t is not None),
            "unmetered_receipts": tokens.count(None), "pairs": pairs, "runs": rows}


def _cell(upstream, root, problem, cp, arm, starter, bundle=None):
    call_id = f"{problem}-c{cp}-{arm}"
    runtime = DecisionRuntime(ROOT, root, timeout_seconds=TIMEOUT, history=bundle)
    result = runtime.invoke(call_id, prompt=PROMPT, schema=SCHEMA,
                            files=_roster(upstream, problem, cp, starter), editable=f"{problem}.py",
                            stage="historical" if cp == 1 else "heldout")
    recovery = None
    if not result.get("candidate_integrity") and (root / "continuation-002.json").is_file() and call_id == "l2m-c2-baseline":
        recovery = recover_l2m(root)
        runtime.retention.retain_file(root / "recovery" / f"{call_id}.json",
                                     kind="decision-history-recovered-candidate", identity=call_id)
        result = {**result, "candidate": recovery["candidate"]}
    if not (result.get("usage") or {}).get("total_tokens") or (not result.get("candidate_integrity") and recovery is None):
        raise RuntimeError(f"Unqualified execution at {call_id}. Preserve the terminal receipt.")
    source = result["candidate"]
    row_path = root / "results" / f"{call_id}.json"
    if row_path.exists():
        recorded = read(row_path)
        if recorded["events_sha256"] != result["events_sha256"] or recorded["grade"]["candidate_sha256"] != digest(source.encode()):
            raise ValueError("Scored terminal receipt does not match the retained candidate")
        return result
    checks = root / "grades" / call_id
    target = grade(upstream, problem, (cp,), source, checks / "target")
    earlier = grade(upstream, problem, tuple(range(1, cp)), source, checks / "earlier") if cp > 1 else None
    raw = result["history_requests"]
    memory = {"searches": sum(r["tool"] == "search" for r in raw), "no_hits": sum(r["no_hits"] is True for r in raw),
              "reads": sum(r["tool"] == "read" and not r["error"] for r in raw),
              "summaries": sum(r["view"] == "summary" and not r["error"] for r in raw),
              "conversation_pages": sum(r["view"] == "conversation" and not r["error"] for r in raw),
              "bytes": sum(r["returned_bytes"] for r in raw), "local_service_seconds": sum(r["elapsed_seconds"] for r in raw),
              "reopened_source_ids": sorted({r["source_id"] for r in raw if r["source_id"]})}
    # Audit decisions as reported. Grading compares the exact candidate bytes; cutoff excludes current grades.
    row = {"call_id": call_id, "problem": problem, "checkpoint": cp, "arm": arm, "base_commit": result["base_commit"],
           "actor_status": result["status"], "tokens": result["usage"]["total_tokens"], "grade": target, "earlier": earlier,
           "elapsed_seconds": result["elapsed_seconds"], "memory": memory, "reported_decisions": result["answer"],
           "events_sha256": result["events_sha256"], "artifact_recovered": recovery is not None,
           "extra_paths_excluded": result.get("extra_paths_excluded")}
    create_once(row_path, row)
    print(f"{call_id}: {target['passed']}/{target['checks']} checks, {memory['searches']} searches, {memory['reads']} reads", flush=True)
    return result


def _run(upstream, root, *, continuation=False):
    controls = _controls(upstream, root)
    files = qualified_files(upstream)
    runtime = DecisionRuntime(ROOT, root, timeout_seconds=TIMEOUT)
    identity = {"dataset": "SlopCodeBench v1.0 problem catalog", "revision": REVISION, "problems": list(PROBLEMS),
        "asset_hashes": files, "controls": controls, "timeout_seconds": TIMEOUT, "calls": 10,
        "arms": {f"{p}-c{n}": list(arms) for (p, n), arms in ORDER.items()},
        "checkpoint_rule": "Common checkpoint 1 source, then always use checkpoint 2 code from no-memory arm as checkpoint 3 parent; never select by score.",
        "control": "Same combined public specs, same source commit; history arm adds read-only MCP.",
        "sources": {p.name: file_digest(p) for p in sorted(Path(__file__).parent.glob("*.py"))},
        "runtime": runtime.version, "runtime_sha256": runtime.codex_sha256,
        "source_account_hash": runtime.binding["account_hash"], "prompt_sha256": digest(PROMPT.encode()), "platform": platform.platform()}
    registration = root / "registration.json"
    if registration.exists():
        original = read(registration)["identity"]
        if original != identity:
            if not continuation or any(original[key] != value for key, value in identity.items() if key != "sources"):
                raise ValueError("Study identity drift")
            recovery = recover_l2m(root)
            amendment = root / "continuation-002.json"
            if not amendment.exists():
                admitted = {p.parent.name for p in (root / "invocations").glob("*/started.json")}
                if admitted != {"l2m-c1-source", "l2m-c2-baseline"}:
                    raise ValueError("Unexpected native admission before the amendment")
            create_once(amendment, {"id": "decision-history-scb-continuation-002",
                "original_registration_sha256": file_digest(registration),
                "original_stop_log_sha256": file_digest(root / "active-chat-run.log"),
                "original_native_attempts": ["l2m-c1-source", "l2m-c2-baseline"],
                "candidate_recovery_sha256": recovery["candidate_sha256"], "identity": identity,
                "change": "Recover the exact earlier source and project the one-file deliverable from subsequent workspaces after checking protected inputs. Exclude temporary test products.",
                "automatic_retries": 0})
            runtime.retention.retain_file(amendment, kind="decision-history-continuation", identity="decision-history-scb-002")
    else:
        if continuation:
            raise ValueError("Continuation requires the original registration")
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        write_new(registration, {"identity": identity, "git_commit": commit, "registered_at": now()})
    runtime.retention.retain_file(registration, kind="decision-history-study", identity="decision-history-scb-001")
    for problem in PROBLEMS:
        seed = _cell(upstream, root, problem, 1, "source", STUB)
        episodes = [export_episode(root / "invocations" / seed["call_id"], problem, 1, seed)]
        starter = seed["candidate"]
        for n in (2, 3):
            bundle = root / "bundles" / f"{problem}-c{n}.json"
            create_once(bundle, episodes)
            runtime.retention.retain_file(bundle, kind="decision-history-bundle", identity=f"{problem}-c{n}")
            results = {}
            for arm in ORDER[(problem, n)]:
                results[arm] = _cell(upstream, root, problem, n, arm, starter, bundle if arm == "history" else None)
            if results["baseline"]["base_commit"] != results["history"]["base_commit"]:
                raise RuntimeError("Paired workspace starts diverged")
            seed = results["baseline"]
            starter = seed["candidate"]
            episodes.append(export_episode(root / "invocations" / seed["call_id"], problem, n, seed))
    summary = root / "summary.json"
    create_once(summary, _report(root))
    runtime.retention.retain_file(summary, kind="decision-history-summary", identity="decision-history-scb-001")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("qualify", "run", "report"))
    parser.add_argument("--root", type=Path, default=ROOT / "work/security/decision-history-scb-001")
    parser.add_argument("--continue-002", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_relative_to((ROOT / "work/security").resolve()):
        parser.error("Native artifacts must remain within work/security")
    upstream = root / "upstream"
    if args.action == "report":
        import json
        print(json.dumps(_report(root), indent=2))
    else:
        with matrix_lock(root):
            if args.action == "qualify":
                _controls(upstream, root)
            else:
                _run(upstream, root, continuation=args.continue_002)


if __name__ == "__main__":
    main()
