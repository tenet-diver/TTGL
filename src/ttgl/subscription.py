"""Collect optional Codex per-thread billing estimates without model inference.

This is a narrow client of the existing Codex app-server, not a billing model.
Token usage, estimated credits, estimated dollars and subscription invoices are
different quantities. Missing backend estimates remain unknown.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import selectors
import signal
import subprocess
import tempfile
import time
from typing import Any


class MeterUnavailable(Exception):
    """An intentionally sanitized error safe to put in experiment metadata."""


class AppServer:
    """Bounded stdio JSON-RPC client with no inference or login methods."""

    def __init__(self, executable: str = "codex", timeout: float = 20):
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        self.timeout = timeout
        self.executable = executable
        self.process = None
        self.selector = None
        self.stderr = None
        self.buffer = b""
        self.next_id = 0

    def __enter__(self):
        self.stderr = tempfile.TemporaryFile()
        try:
            self.process = subprocess.Popen(
                [self.executable, "app-server", "--listen", "stdio://"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr,
                start_new_session=True,
            )
            self.selector = selectors.DefaultSelector()
            self.selector.register(self.process.stdout, selectors.EVENT_READ)
            self.request("initialize", {
                "clientInfo": {"name": "ttgl_usage_collector", "title": None,
                               "version": "0.1.0"},
                "capabilities": {"experimentalApi": False, "requestAttestation": False,
                                 "explicitGatewayOauth": True},
            })
            self._send({"method": "initialized", "params": {}})
            return self
        except BaseException as exc:
            self.close()
            if isinstance(exc, MeterUnavailable):
                raise
            if isinstance(exc, OSError):
                raise MeterUnavailable("app_server_start_failed") from None
            raise

    def _send(self, message: dict) -> None:
        try:
            self.process.stdin.write((json.dumps(message) + "\n").encode())
            self.process.stdin.flush()
        except (OSError, ValueError):
            raise MeterUnavailable("app_server_disconnected") from None

    def _failure(self) -> MeterUnavailable:
        # Do not persist arbitrary stderr: it can include account information.
        self.stderr.seek(0)
        message = self.stderr.read(65536)
        code = ("read_only_state_directory" if b"Read-only file system" in message
                else "app_server_disconnected")
        return MeterUnavailable(code)

    def request(self, method: str, params: dict) -> dict:
        if method not in ("initialize", "account/usage/read"):
            raise ValueError("Only initialization and per-thread usage are allowed")
        if method == "account/usage/read" and not valid_thread(params.get("threadId")):
            raise ValueError("Account-wide history is deliberately unsupported")
        self.next_id += 1
        request_id = self.next_id
        self._send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise MeterUnavailable("app_server_timeout")
            if b"\n" not in self.buffer:
                if not self.selector.select(remaining):
                    raise MeterUnavailable("app_server_timeout")
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    raise self._failure()
                self.buffer += chunk
                if len(self.buffer) > 8 * 1024 * 1024:
                    raise MeterUnavailable("oversized_app_server_response")
                continue
            line, self.buffer = self.buffer.split(b"\n", 1)
            if not line.strip():
                continue
            try:
                message = json.loads(line)
            except (ValueError, UnicodeError):
                raise MeterUnavailable("invalid_app_server_json") from None
            if not isinstance(message, dict):
                raise MeterUnavailable("invalid_app_server_response")
            if "method" in message:
                # No tool approval, interactive login or other server request
                # is supported by this read-only collector. Ignore notifications.
                if "id" in message:
                    self._send({"id": message["id"], "error": {
                        "code": -32601, "message": "Method not supported by usage collector"}})
                continue
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise MeterUnavailable("usage_rpc_error" if method == "account/usage/read"
                                       else "initialization_rpc_error")
            if not isinstance(message.get("result"), dict):
                raise MeterUnavailable("invalid_app_server_result")
            return message["result"]

    def close(self) -> None:
        if self.process is not None:
            # Stop only this collector's subprocess group. A leader can exit
            # while a descendant remains, so always try both group signals.
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            except PermissionError:
                # Darwin can return EPERM for a process group after its leader
                # has exited. Do not turn an observed startup failure into a
                # collector crash; a live owned process must still be killable.
                if self.process.poll() is None:
                    raise
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError:
                if self.process.poll() is None:
                    raise
            self.process.wait()
            for stream in (self.process.stdin, self.process.stdout):
                if stream is not None:
                    stream.close()
            self.process = None
        if self.selector is not None:
            self.selector.close()
            self.selector = None
        if self.stderr is not None:
            self.stderr.close()
            self.stderr = None

    def __exit__(self, *_):
        self.close()


def valid_thread(value: Any) -> bool:
    return isinstance(value, str) and 0 < len(value) <= 256 and value.strip() == value


def _count(value: Any, *, nullable: bool = False) -> int | None:
    if value is None and nullable:
        return None
    if type(value) is not int or value < 0:
        raise MeterUnavailable("invalid_usage_counter")
    return value


def sanitize_usage(result: dict, thread_id: str) -> dict:
    """Retain only the documented thread estimate, never account summaries."""
    usage = result.get("threadUsage")
    if usage is None:
        return {"thread_id": thread_id, "status": "unavailable",
                "reason": "backend_thread_estimate_unavailable", "usage": None}
    if not isinstance(usage, dict) or usage.get("threadId") != thread_id:
        raise MeterUnavailable("mismatched_usage_thread")
    output = {
        "threadId": thread_id,
        "estimatedUsageCreditsMicros": _count(usage.get("estimatedUsageCreditsMicros")),
        "estimatedUsageUsdMicros": _count(usage.get("estimatedUsageUsdMicros"), nullable=True),
        "groups": [],
    }
    if not isinstance(usage.get("groups"), list):
        raise MeterUnavailable("invalid_usage_groups")
    for group in usage["groups"]:
        if not isinstance(group, dict):
            raise MeterUnavailable("invalid_usage_groups")
        item = {}
        for field in ("model", "reasoningEffort", "speed"):
            value = group.get(field)
            if value is not None and not isinstance(value, str):
                raise MeterUnavailable("invalid_usage_group_label")
            item[field] = value
        item["estimatedUsageCreditsMicros"] = _count(group.get("estimatedUsageCreditsMicros"))
        for field in ("netNewInputTokens", "cachedInputTokens", "inputTokens",
                      "outputTokens", "totalTokens"):
            item[field] = _count(group.get(field), nullable=True)
        output["groups"].append(item)
    return {"thread_id": thread_id, "status": "available", "reason": None, "usage": output}


def read_threads(paths: list[Path], explicit: list[str]) -> tuple[list[str], list[dict], bool]:
    """Read only caller-selected local harness states; do not scan session history."""
    threads = list(explicit)
    sources = []
    finalized = True
    for path in paths:
        raw = path.read_bytes()
        state = json.loads(raw)
        if not isinstance(state, dict) or state.get("schema_version") != 3:
            raise ValueError("Expected a version-3 ttgl.personal state.json")
        ledger = state.get("usage_threads", {})
        if not isinstance(ledger, dict):
            raise ValueError("State usage_threads must be an object")
        threads.extend(ledger)
        for role in ("controller_thread_id", "expert_thread_id"):
            if state.get(role) is not None:
                threads.append(state[role])
        complete = state.get("status") not in (None, "running") and not state.get("inflight")
        finalized = finalized and complete
        accounting_issues = state.get("usage_accounting_issues")
        # A terminal run can still contain a billed invocation whose thread ID
        # was never observed. Known-thread estimates are then only a subtotal.
        # Conservatively require the state ledger to have no accounting issues;
        # do not interpret terminal status as complete billing attribution.
        ledger_complete = (isinstance(accounting_issues, list) and not accounting_issues
                           and (bool(ledger) or state.get("turns") == 0))
        sources.append({"path": str(path.resolve()), "sha256": hashlib.sha256(raw).hexdigest(),
                        "run_id": state.get("run_id"), "task_id": state.get("task_id"),
                        "status": state.get("status"), "finalized": complete,
                        "usage_ledger_complete": ledger_complete,
                        "usage_accounting_issue_count": len(accounting_issues)
                            if isinstance(accounting_issues, list) else None})
    if any(not valid_thread(thread) for thread in threads):
        raise ValueError("Invalid thread identifier")
    return list(dict.fromkeys(threads)), sources, finalized


def collect(thread_ids: list[str], *, independent_roots: bool = False,
            finalized: bool = True, ledger_complete: bool = True,
            client_factory=AppServer) -> dict:
    if not thread_ids or any(not valid_thread(thread) for thread in thread_ids):
        raise ValueError("At least one valid thread ID is required; account-wide reads are disabled")
    threads = list(dict.fromkeys(thread_ids))
    records = []
    try:
        with client_factory() as client:
            for thread in threads:
                try:
                    records.append(sanitize_usage(client.request(
                        "account/usage/read", {"threadId": thread}), thread))
                except MeterUnavailable as exc:
                    records.append({"thread_id": thread, "status": "unavailable",
                                    "reason": str(exc), "usage": None})
    except MeterUnavailable as exc:
        records = [{"thread_id": thread, "status": "unavailable", "reason": str(exc),
                    "usage": None} for thread in threads]
    complete = all(record["status"] == "available" for record in records)
    can_sum = independent_roots and finalized and ledger_complete and complete
    totals = {"estimated_usage_credits_micros": None, "estimated_usage_usd_micros": None}
    if can_sum:
        totals["estimated_usage_credits_micros"] = sum(
            record["usage"]["estimatedUsageCreditsMicros"] for record in records)
        dollars = [record["usage"]["estimatedUsageUsdMicros"] for record in records]
        if all(value is not None for value in dollars):
            totals["estimated_usage_usd_micros"] = sum(dollars)
    return {
        "schema_version": 1,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "collector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "app_server_protocol_source_commit": "970111f6cb62cc02fe36a82ea7d71b37a2889c97",
        "status": "available" if complete and ledger_complete else "incomplete",
        "method": "account/usage/read",
        "new_model_inference_requested": False,
        "independent_root_threads_attested": independent_roots,
        "selected_states_finalized": finalized,
        "selected_states_usage_ledger_complete": ledger_complete,
        "threads": records,
        "totals": totals,
        "totals_status": ("available_estimates" if can_sum else
                          "independent_roots_not_attested" if not independent_roots else
                          "states_unfinished" if not finalized else
                          "state_usage_ledger_incomplete" if not ledger_complete else
                          "missing_thread_estimates"),
        "limitations": [
            "These are provider estimates, not subscription invoices or a promise of quota availability.",
            "Backend estimates may lag recent activity; repeat with a new output path after settlement.",
            "Explicit thread IDs without a state file have no independently checked completion status.",
            "Known-thread estimates cannot establish whole-task spend when a state ledger is incomplete.",
            "Never add nested parent and child bills without a documented accounting boundary.",
            "Cached tokens are included in input; token categories must not all be summed.",
            "No inference compute, hardware, evaluator or human labor costs are added here.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, action="append", default=[])
    parser.add_argument("--thread-id", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--timeout-seconds", type=float, default=20)
    parser.add_argument("--independent-roots", action="store_true",
                        help="Attest selected threads are independent roots, not nested parent/child bills")
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Output exists; use a new path to preserve previous observations")
    try:
        threads, sources, finalized = read_threads(args.state, args.thread_id)
        result = collect(threads, independent_roots=args.independent_roots, finalized=finalized,
                         ledger_complete=all(source["usage_ledger_complete"] for source in sources),
                         client_factory=lambda: AppServer(args.codex, args.timeout_seconds))
    except (ValueError, OSError) as exc:
        # Never serialize raw exception text, local state or account responses.
        parser.error(f"Invalid collector input ({type(exc).__name__})")
    result["sources"] = sources
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "threads": len(result["threads"]),
                      "totals_status": result["totals_status"], "output": str(args.output)}))
    return 0 if result["status"] == "available" else 2


if __name__ == "__main__":
    raise SystemExit(main())
