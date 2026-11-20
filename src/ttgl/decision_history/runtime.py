"""Use the qualified native actor with a separate, study-scoped memory MCP server."""
import json
from pathlib import Path
import sys
import tempfile
import time

from ..experience_routing.backend import NativeCallFailure
from ..experience_routing.io import digest, file_digest, now, read, write_new
from ..personal import Request
from ..sim_ablation.runtime import (AmbiguousInvocation, MODEL, NativeRuntime,
    _SandboxSubscriptionBackend, _candidate, _decode_answer, _worktree, qualify_sandbox)


class HistoryBackend(_SandboxSubscriptionBackend):
    def __init__(self, *, history_path, history_spool, **kwargs):
        super().__init__(**kwargs)
        self.history_path = history_path
        self.history_spool = history_spool

    def command(self, request, schema):
        command = super().command(request, schema)
        if self.history_path is None:
            return command
        settings = {
            "mcp_servers.history.command": sys.executable,
            "mcp_servers.history.args": ["-m", "ttgl.decision_history.memory", str(self.history_path), str(self.history_spool)],
            "mcp_servers.history.required": True,
            "mcp_servers.history.tool_timeout_sec": 8,
        }
        for key, value in settings.items():
            command[-1:-1] = ["--config", key + "=" + json.dumps(value)]
        path = json.dumps(str(Path(__file__).resolve().parents[2]))
        command[-1:-1] = ["--config", "mcp_servers.history.env={\"PYTHONPATH\"=" + path + "}"]
        return command


class DecisionRuntime(NativeRuntime):
    def __init__(self, *args, history=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.history = history

    def _invoke(self, folder, call_id, *, prompt, schema, files, editable, stage):
        identity = {"call_id": call_id, "stage": stage, "model": MODEL, "effort": self.effort,
                    "timeout_seconds": self.timeout_seconds, "codex_version": self.version,
                    "codex_sha256": self.codex_sha256, "source_account_hash": self.binding["account_hash"],
                    "prompt_sha256": digest(prompt.encode()), "schema_sha256": digest(schema),
                    "public_roster_sha256": digest(files), "editable": editable,
                    "history_sha256": file_digest(self.history) if self.history else None, "automatic_retries": 0}
        pending, started, completed = (folder / f"{key}.json" for key in ("pending", "started", "completed"))
        if pending.exists() and read(pending) != identity:
            raise ValueError("Frozen call input differs")
        if completed.exists():
            return read(completed)
        if started.exists():
            raise AmbiguousInvocation(f"{call_id} started without a terminal receipt")
        if not pending.exists():
            write_new(pending, identity)
        self.retention.retain_file(pending, kind="decision-history-registration", identity=call_id)
        with tempfile.TemporaryDirectory(prefix="observatory-decision-actor-") as path:
            root = Path(path)
            workspace = root / "client"
            workspace.mkdir(mode=0o700)
            qualify_sandbox(workspace)
            worktree, base = _worktree(root, files)
            config, spool = root / "actor.json", folder / "history-spool"
            write_new(config, {"workspace": str(worktree), "spool": str(folder / "actor-spool"),
                               "protected": [".git", *(key for key in files if key != editable)],
                               "deadline": time.monotonic() + self.timeout_seconds})
            backend = HistoryBackend(history_path=self.history, history_spool=spool, bridge_config=config,
                executable=self.executable, executable_sha256=self.codex_sha256, source_home=self.binding["codex_home"],
                source_account_hash=self.binding["account_hash"], output=folder / "native", client=self.retention)
            request = Request(call_id, MODEL, stage, prompt, workspace, schema, self.timeout_seconds,
                              read_only=False, reasoning_effort=self.effort)
            backend.preflight(request)
            write_new(started, {"at": now(), "base_commit": base, "registration_sha256": digest(identity)})
            try:
                response = backend.complete(request)
            except NativeCallFailure as error:
                response = error.response
            usage = self._record_usage(request, response, backend, stage)
            candidate, integrity, diff = _candidate(worktree, files, editable)
            self._retain_tools(folder, call_id)
            history_rows = []
            for path in sorted(spool.glob("*.json"), key=lambda item: item.stat().st_mtime_ns):
                archive = self.retention.retain_file(path, kind="decision-history-retrieval", identity=f"{call_id}:{path.stem}")
                row = read(path)
                history_rows.append({"tool": row["tool"], "error": row["error"],
                                     "returned_bytes": row["returned_bytes"], "elapsed_seconds": row["elapsed_seconds"],
                                     "no_hits": row["answer"].get("hits") == [] if row["tool"] == "search" and not row["error"] else None,
                                     "source_id": row["answer"].get("id"),
                                     "view": row["args"].get("view"), "archive": archive})
            result = {**identity, "status": response.status, "error_type": response.error_type, "base_commit": base,
                      "thread_id": response.thread_id, "elapsed_seconds": response.elapsed_seconds, "finished_at": now(),
                      "answer": _decode_answer(response.text), "candidate": candidate, "candidate_integrity": integrity,
                      "diff": diff, "usage": usage["delta"], "scenario_cost": usage["scenario_cost"],
                      "events_sha256": backend.last_native_artifact_hash, "events_ref": backend.artifacts.get("events.jsonl"),
                      "rollout_refs": backend.rollout_artifacts, "history_requests": history_rows}
            write_new(completed, result)
            return result
