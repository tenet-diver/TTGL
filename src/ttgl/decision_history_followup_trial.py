"""Run one registered summary-only versus full-history handoff on native Luna."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
import time

from .decision_history.__main__ import PROMPT, SCHEMA, STUB, _roster
from .decision_history.grade import grade, qualified_files
from .decision_history.recovery import recover_l2m
from .decision_history_followup import ARMS, PRIVATE_ROOT, HistoryView, codex_config
from .experience_routing.backend import NativeCallFailure
from .experience_routing.io import digest, file_digest, now, read, write_new
from .personal import Request
from .sim_ablation.runtime import (MODEL, AmbiguousInvocation, NativeRuntime, _SandboxSubscriptionBackend,
                                   _decode_answer, _git, _regular_bytes, _worktree, qualify_sandbox)
from .sim_ablation.study import ROOT, create_once, matrix_lock

TRIAL_ID = "followup-002"


class FollowupBackend(_SandboxSubscriptionBackend):
    def __init__(self, *, history_flags, **kwargs):
        super().__init__(**kwargs)
        self.history_flags = history_flags

    def command(self, request, schema):
        command = super().command(request, schema)
        return [*command[:-1], *self.history_flags, command[-1]]


def _invoke(runtime, directory, arm, registration, files, editable):
    call_id = f"{registration['handoff']}-{arm}-{registration['trial_id']}"
    folder = runtime.output / "invocations" / call_id
    pending, started, completed = (folder / f"{name}.json" for name in ("pending", "started", "completed"))
    spool = folder / "history-spool"
    flags = codex_config(directory, arm, receipt_dir=spool,
                         expected_manifest_sha256=registration["history_manifest_sha256"])
    create_once(pending, {"call_id": call_id, "arm": arm, "pair_sha256": digest(registration), "history_flags": flags})
    if completed.is_file():
        return read(completed)
    if started.is_file():
        raise AmbiguousInvocation(f"{call_id}: admission has no terminal receipt")
    runtime.retention.retain_file(pending, kind="decision-history-followup-registration", identity=call_id)

    with tempfile.TemporaryDirectory(prefix="observatory-history-followup-") as temporary:
        isolated = Path(temporary)
        client = isolated / "client"
        client.mkdir(mode=0o700)
        qualify_sandbox(client)
        worktree, base_commit = _worktree(isolated, files)
        actor = isolated / "actor.json"
        write_new(actor, {"workspace": str(worktree), "spool": str(folder / "actor-spool"),
                          "protected": [".git", *(path for path in files if path != editable)],
                          "deadline": time.monotonic() + runtime.timeout_seconds})
        backend = FollowupBackend(history_flags=flags, bridge_config=actor, executable=runtime.executable,
                                  executable_sha256=runtime.codex_sha256, source_home=runtime.binding["codex_home"],
                                  source_account_hash=runtime.binding["account_hash"], output=folder / "native",
                                  client=runtime.retention)
        request = Request(call_id, MODEL, "heldout", PROMPT, client, SCHEMA, runtime.timeout_seconds,
                          read_only=False, reasoning_effort=runtime.effort)
        backend.preflight(request)
        if base_commit != registration["base_commit"]:
            raise ValueError("Follow-up parent Git snapshot differs")
        write_new(started, {"started_at": now(), "base_commit": base_commit, "pending_sha256": file_digest(pending)})
        try:
            response = backend.complete(request)
        except NativeCallFailure as failure:
            response = failure.response

        candidate = None
        try:
            if all(_regular_bytes(worktree / path) == text.encode() for path, text in files.items() if path != editable):
                candidate = _regular_bytes(worktree / editable).decode()
        except (OSError, UnicodeError, ValueError):
            pass
        if candidate is not None:
            snapshot = write_new(folder / "candidate-source.json", {
                "source": candidate, "candidate_sha256": digest(candidate.encode()),
                "diff": _git(worktree, "diff", "--no-ext-diff", "HEAD", "--", editable).decode(),
                "extra_paths_excluded": sorted(path.name for path in worktree.iterdir() if path.name not in {".git", *files}),
            })
            runtime.retention.retain_file(snapshot, kind="decision-history-followup-candidate", identity=call_id)

        usage = runtime._record_usage(request, response, backend, "heldout")
        runtime._retain_tools(folder, call_id)
        requests = []
        for path in sorted(spool.glob("*.json")):
            receipt = read(path)
            runtime.retention.retain_file(path, kind="decision-history-followup-retrieval", identity=f"{call_id}:{path.stem}")
            requests.append({"tool": receipt["tool"], "view": receipt["args"].get("view"), "error": receipt["error"],
                             "bytes": receipt["returned_bytes"], "elapsed_seconds": receipt["elapsed_seconds"]})
        native_calls = []
        for line in (folder / "native" / call_id / "events.jsonl").read_text().splitlines():
            event = json.loads(line)
            item = event.get("item", {})
            if event.get("type") == "item.completed" and item.get("server") == "history":
                native_calls.append({"tool": item["tool"], "status": item["status"], "error": item.get("error")})
        result = {"call_id": call_id, "arm": arm, "base_commit": base_commit, "status": response.status,
                  "elapsed_seconds": response.elapsed_seconds, "tokens": usage["delta"].get("total_tokens"),
                  "thread_id": response.thread_id, "events_sha256": backend.last_native_artifact_hash,
                  "candidate_sha256": digest(candidate.encode()) if candidate is not None else None,
                  "reported_decisions": _decode_answer(response.text), "retrieval": requests, "native_history_calls": native_calls}
        write_new(completed, result)
        runtime.retention.retain_file(completed, kind="decision-history-followup-completion", identity=call_id)
        return result


def run(pilot, directory):
    views = [HistoryView(directory, arm) for arm in ARMS]
    manifest = read(directory / "manifest.json")
    problem, checkpoint = manifest["handoff"].split("-c")
    checkpoint = int(checkpoint)
    upstream = pilot / "upstream"
    identity = read(pilot / "registration.json")["identity"]
    if qualified_files(upstream) != identity["asset_hashes"]:
        raise ValueError("Registered benchmark assets differ")
    if file_digest(pilot / "bundles" / (manifest["handoff"] + ".json")) != manifest["pilot_bundle_sha256"]:
        raise ValueError("Registered predecessor bundle differs")

    parent = manifest["predecessors"][-1]
    anchor = read(pilot / "invocations" / parent / "completed.json")
    source = anchor["candidate"]
    if source is None and parent == "l2m-c2-baseline":
        source = recover_l2m(pilot)["candidate"]
    if not isinstance(source, str):
        raise ValueError("The registered parent has no sealed candidate")
    anchor_grade = read(pilot / "results" / (parent + ".json"))
    if digest(source.encode()) != anchor_grade["grade"]["candidate_sha256"]:
        raise ValueError("The registered parent differs from its independently graded bytes")
    files = _roster(upstream, problem, checkpoint, source)
    output = directory / "trial"
    runtime = NativeRuntime(ROOT, output, timeout_seconds=identity["timeout_seconds"])
    if ((runtime.version, runtime.codex_sha256, runtime.binding["account_hash"])
            != (identity["runtime"], identity["runtime_sha256"], identity["source_account_hash"])):
        raise ValueError("The originally registered Codex executable and source subscription are required")

    with matrix_lock(output), tempfile.TemporaryDirectory(prefix="observatory-history-pair-") as temporary:
        _, base = _worktree(Path(temporary), files)
        registration = {"trial_id": TRIAL_ID, "handoff": manifest["handoff"], "arms": list(ARMS), "automatic_retries": 0,
                        "history_manifest_sha256": views[0].manifest_sha256, "base_commit": base,
                        "public_roster_sha256": digest(files), "prompt_sha256": digest(PROMPT.encode()),
                        "schema_sha256": digest(SCHEMA), "trial_source_sha256": file_digest(__file__),
                        "model": MODEL, "effort": runtime.effort, "timeout_seconds": runtime.timeout_seconds,
                        "codex_sha256": runtime.codex_sha256, "source_account_hash": runtime.binding["account_hash"]}
        if any(view.manifest_sha256 != registration["history_manifest_sha256"] for view in views):
            raise ValueError("The history views disagree about the manifest")
        register_path = output / "registration.json"
        create_once(register_path, registration)
        trial_key = f"{manifest['handoff']}:{TRIAL_ID}"
        runtime.retention.retain_file(register_path, kind="decision-history-followup-trial", identity=trial_key)
        for name in ("manifest.json", *(f"{arm}.json" for arm in ARMS)):
            runtime.retention.retain_file(directory / name, kind="decision-history-followup-bundle",
                                          identity=f"{trial_key}:{name}")
        reference = (upstream / problem / "solutions" / f"checkpoint_{checkpoint}" / f"{problem}.py").read_text()
        good = grade(upstream, problem, (checkpoint,), reference, output / "controls/reference")
        blank = grade(upstream, problem, (checkpoint,), STUB, output / "controls/empty")
        if not good["solved"] or blank["solved"] or good["checks"] != blank["checks"]:
            raise ValueError("Independent follow-up controls failed")

        rows = []
        for arm in ARMS:
            print(f"Processing {arm} for {manifest['handoff']}", flush=True)
            row = _invoke(runtime, directory, arm, registration, files, f"{problem}.py")
            if row["candidate_sha256"] is not None:
                snapshot = read(output / "invocations" / row["call_id"] / "candidate-source.json")
                code = snapshot["source"]
                if digest(code.encode()) != row["candidate_sha256"]:
                    raise ValueError("Candidate bytes disagree with the terminal receipt")
                for name, checkpoints in (("target", (checkpoint,)), ("earlier", tuple(range(1, checkpoint)))):
                    row[name] = grade(upstream, problem, checkpoints, code, output / "grades" / arm / name)
            rows.append(row)
        if not rows[0]["thread_id"] or rows[0]["thread_id"] == rows[1]["thread_id"] or not rows[1]["thread_id"]:
            raise ValueError("The pair lacks two distinct native thread identifiers")
        report = output / "report.json"
        create_once(report, {"registration_sha256": file_digest(register_path), "controls": {"reference": good, "empty": blank},
                             "arms": rows})
        runtime.retention.retain_file(report, kind="decision-history-followup-report", identity=trial_key)
    print(f"Verified report at {report}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot", type=Path)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    pilot, directory = args.pilot.resolve(), args.directory.resolve()
    if (not all(path.is_relative_to(PRIVATE_ROOT.resolve()) for path in (pilot, directory))
            or pilot.is_relative_to(directory) or directory.is_relative_to(pilot)):
        parser.error("Use separate private pilot and follow-up directories under work/security")
    run(pilot, directory)


if __name__ == "__main__":
    main()
