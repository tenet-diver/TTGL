"""Native study invocation with the existing offline actor and durable receipts."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import time

from .decision_history_followup import codex_config
from .decision_history_followup_trial import FollowupBackend
from .experience_routing.backend import NativeCallFailure
from .experience_routing.io import digest, file_digest, now, read, write_new
from .personal import Request
from .sim_ablation.runtime import MODEL, AmbiguousInvocation, _decode_answer, _regular_bytes, _worktree, qualify_sandbox
from .sim_ablation.study import create_once


class StudyBackend(FollowupBackend):
    def command(self, request, schema):
        command = super().command(request, schema)
        for index, setting in enumerate(command):
            if setting.startswith("mcp_servers.worker.args="):
                command[index] = setting.replace("ttgl.sim_ablation.runtime", "ttgl.decision_history_study_actor")
        return command


def invoke(runtime, call_id, protocol, files, prompt, schema, *, base_commit, history=None, stage="heldout"):
    folder = runtime.output / "invocations" / call_id
    pending, started, completed = (folder / f"{name}.json" for name in ("pending", "started", "completed"))
    spool = folder / "history-spool"
    flags = codex_config(history[0], history[1], receipt_dir=spool, expected_manifest_sha256=history[2]) if history else []
    identity = {"call_id": call_id, "protocol_sha256": digest(protocol), "roster_sha256": digest(files),
                "base_commit": base_commit, "prompt_sha256": digest(prompt.encode()), "schema_sha256": digest(schema),
                "history_flags": flags, "stage": stage, "automatic_retries": 0}
    create_once(pending, identity)
    if completed.is_file():
        return read(completed)
    if started.is_file():
        raise AmbiguousInvocation(f"{call_id}: admission has no terminal receipt")
    runtime.retention.retain_file(pending, kind="decision-history-study-pending", identity=call_id)

    with tempfile.TemporaryDirectory(prefix="observatory-memory-study-") as temporary:
        root = Path(temporary)
        client = root / "client"
        client.mkdir(mode=0o700)
        qualify_sandbox(client)
        workspace, commit = _worktree(root, files)
        if commit != base_commit:
            raise ValueError("Study workspace differs from the sealed snapshot")
        config = root / "actor.json"
        rejected = folder / "rejected-shell-requests"
        write_new(config, {"workspace": str(workspace), "spool": str(folder / "actor-spool"),
                           "protected": [".git", *(name for name in files if name != "solution.py")],
                           "invalid_requests": str(rejected), "deadline": time.monotonic() + runtime.timeout_seconds})
        backend = StudyBackend(history_flags=flags, bridge_config=config, executable=runtime.executable,
                               executable_sha256=runtime.codex_sha256, source_home=runtime.binding["codex_home"],
                               source_account_hash=runtime.binding["account_hash"], output=folder / "native",
                               client=runtime.retention)
        request = Request(call_id, MODEL, stage, prompt, client, schema, runtime.timeout_seconds,
                          read_only=False, reasoning_effort=runtime.effort)
        backend.preflight(request)
        write_new(started, {"started_at": now(), "pending_sha256": file_digest(pending), "base_commit": commit})
        try:
            response = backend.complete(request)
        except NativeCallFailure as failure:
            response = failure.response
        candidate = None
        try:
            if all(_regular_bytes(workspace / name) == text.encode() for name, text in files.items() if name != "solution.py"):
                candidate = _regular_bytes(workspace / "solution.py").decode()
        except (OSError, UnicodeError, ValueError):
            pass
        if candidate is not None:
            snapshot = write_new(folder / "candidate.json", {"source": candidate, "sha256": digest(candidate.encode()),
                                "extra_paths_excluded": sorted(path.name for path in workspace.iterdir() if path.name not in {".git", *files})})
            runtime.retention.retain_file(snapshot, kind="decision-history-study-candidate", identity=call_id)
        usage = runtime._record_usage(request, response, backend, stage)
        runtime._retain_tools(folder, call_id)
        views = []
        for path in sorted(spool.glob("*.json")):
            row = read(path)
            views.append({"tool": row["tool"], "view": row["args"].get("view"), "error": row["error"],
                          "elapsed_seconds": row["elapsed_seconds"], "id": row["answer"].get("id")})
            runtime.retention.retain_file(path, kind="decision-history-study-retrieval", identity=f"{call_id}:{path.stem}")
        invalid = sorted(rejected.glob("*.json"))
        for path in invalid:
            runtime.retention.retain_file(path, kind="decision-history-study-shell-rejection", identity=f"{call_id}:{path.stem}")
        trace = folder / "native" / call_id / "events.jsonl"
        history_calls = []
        for line in trace.read_text().splitlines() if trace.exists() else []:
            event = json.loads(line)
            item = event.get("item", {})
            if event.get("type") == "item.completed" and item.get("server") == "history":
                history_calls.append({"tool": item["tool"], "status": item["status"], "error": item.get("error")})
        result = {"call_id": call_id, "base_commit": commit, "status": response.status, "error_type": response.error_type,
                  "thread_id": response.thread_id, "tokens": usage["delta"].get("total_tokens"),
                  "elapsed_seconds": response.elapsed_seconds, "events_sha256": backend.last_native_artifact_hash,
                  "candidate_sha256": digest(candidate.encode()) if candidate is not None else None,
                  "answer": _decode_answer(response.text), "retrieval": views, "native_history_calls": history_calls,
                  "invalid_timeout_requests": len(invalid)}
        write_new(completed, result)
        runtime.retention.retain_file(completed, kind="decision-history-study-completion", identity=call_id)
        return result
