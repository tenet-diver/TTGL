"""Local MCP workflow for proposing and running bounded Observatory harness trials."""
from __future__ import annotations

import argparse
import difflib
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from .experience_routing.io import canonical, digest, file_digest, now, read, write_new
from .sim_ablation.benchmark import VERSION, load_tasks
from .sim_ablation.study import HARNESS, MODEL, ROOT, cases, create_once, feedback, harness_text, select

ID = re.compile(r"[0-9a-f]{64}\Z")
SETTINGS = {"type": "object", "additionalProperties": False, "required": list(HARNESS),
            "properties": {k: {"type": "string", "enum": list(v)} for k, v in HARNESS.items()}}
RATES = {MODEL: {"input": 0.10, "cached": 0.01, "output": 0.50}}


def tool(name, description, readonly, **fields):
    return {"name": name, "description": description,
            "inputSchema": {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False},
            "annotations": {"readOnlyHint": readonly, "destructiveHint": False, "openWorldHint": False}}


TEXT = {"type": "string", "minLength": 1, "maxLength": 2000}
KEY = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
TOOLS = [
    tool("list_harness_settings", "List supported native coding harness settings and fixed trial budgets.", True),
    tool("plan_harness_trial", "Freeze a reversible change to one harness setting and its public evidence. No model call.",
         False, before=SETTINGS, after=SETTINGS, hypothesis=TEXT, evidence_ids={"type": "array", "items": TEXT, "maxItems": 8}),
    tool("run_harness_trial", "Start the exact registered native comparison on the host-approved subject. Return a durable trial ID.",
         False, trial_id=KEY),
    tool("get_harness_trial", "Read progress, independent outcomes, native usage, receipts and decision for one trial ID.",
         True, trial_id=KEY),
    tool("record_harness_decision", "Record a keep, reject or inconclusive decision after measurement.",
         False, trial_id=KEY, decision={"type": "string", "enum": ["keep", "reject", "inconclusive"]}, rationale=TEXT),
]


def trial_path(root, identity):
    if not isinstance(identity, str) or not ID.fullmatch(identity):
        raise ValueError("Invalid trial ID")
    path = root / identity
    if not path.resolve().is_relative_to(root):
        raise ValueError("Trial path escapes the local store")
    return path


def _text(value):
    if not isinstance(value, str) or not value.strip() or len(value.encode()) > 2000:
        raise ValueError("Expected bounded nonempty text")
    return value.strip()


def _implementation():
    files = [
        Path(__file__), *(ROOT / "src/ttgl/sim_ablation" / name for name in
                         ("study.py", "runtime.py", "benchmark.py", "benchmark_tasks.py")),
    ]
    return {str(p.relative_to(ROOT)): file_digest(p) for p in files}


def plan(root, before, after, hypothesis, evidence_ids):
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise ValueError("Harness settings must be objects")
    prior, proposed = harness_text(before), harness_text(after)
    if sum(before[key] != after[key] for key in HARNESS) != 1:
        raise ValueError("A trial changes exactly one registered harness setting")
    if not isinstance(evidence_ids, list) or len(evidence_ids) > 8:
        raise ValueError("At most eight evidence citations are supported")
    subject = {task.id: task.fingerprint for task in load_tasks().values() if task.split == "optimization"}
    protocol = {"benchmark": VERSION, "tasks": subject, "model": MODEL, "effort": "low",
                "maximum_native_calls": len(subject) * 2, "timeout_seconds": 100, "maximum_parallel_calls": 1,
                "sources": _implementation(), "automatic_retries": 0, "selector": "sim-development-001",
                "before": before, "after": after, "hypothesis": _text(hypothesis),
                "evidence_ids": [_text(value) for value in evidence_ids],
                "prompt_diff": "".join(difflib.unified_diff(prior.splitlines(True), proposed.splitlines(True),
                                                            fromfile="baseline", tofile="candidate"))}
    identity = digest(protocol)
    path = trial_path(root, identity)
    create_once(path / "plan.json", protocol)
    return {"trial_id": identity, "status": "planned", "protocol": protocol}


def inspect(root, identity):
    path = trial_path(root, identity)
    protocol = read(path / "plan.json")
    if digest(protocol) != identity:
        raise ValueError("Trial registration identity changed")
    result = {"trial_id": identity, "status": "planned", "protocol": protocol}
    for filename, status in (("launch.json", "queued"), ("started.json", "running"),
                             ("stopped.json", "stopped"), ("result.json", "measured")):
        if (path / filename).is_file():
            result.update(status=status, receipt=read(path / filename))
    if (path / "decision.json").is_file():
        result["decision"] = read(path / "decision.json")
    return result


def decide(root, identity, decision, rationale):
    path = trial_path(root, identity)
    current = inspect(root, identity)
    if current["status"] != "measured" or decision not in ("keep", "reject", "inconclusive"):
        raise ValueError("A measured trial and valid decision are required")
    if decision == "keep" and not current["receipt"]["acceptance_passed"]:
        raise ValueError("Candidate did not pass the frozen acceptance rule")
    return create_once(path / "decision.json", {"trial_id": identity, "decision": decision,
                                               "rationale": _text(rationale),
                                               "result_sha256": file_digest(path / "result.json")})


def launch(root, identity, authorized):
    path = trial_path(root, identity)
    current = inspect(root, identity)
    if not authorized:
        raise ValueError("This MCP server lacks host authorization for native trials")
    if current["status"] != "planned":
        return {"trial_id": identity, "status": current["status"]}
    if current["protocol"]["sources"] != _implementation():
        raise ValueError("Trial source changed. Register a new version.")
    # A host-owned launch receipt prevents duplicate dispatch across MCP clients.
    try:
        write_new(path / "launch.json", {"trial_id": identity, "requested_at": now()})
    except FileExistsError:
        return {"trial_id": identity, "status": "already_requested"}
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    try:
        with (path / "worker.log").open("xb") as log:
            subprocess.Popen([sys.executable, "-m", "ttgl.experiment_mcp", "--root", str(root),
                              "--execute", "--worker", identity], cwd=ROOT, env=environment,
                             stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    except OSError as error:
        write_new(path / "stopped.json", {"reason": type(error).__name__, "native_calls_started": 0})
        raise
    return {"trial_id": identity, "status": "queued"}


def run_worker(root, identity):
    from .sim_ablation.runtime import NativeRuntime

    path = trial_path(root, identity)
    if inspect(root, identity)["status"] != "queued":
        raise ValueError("Trial is not queued or was already admitted")
    with (root / "worker.lock").open("ab") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            write_new(path / "stopped.json", {"reason": "another_trial_owns_source", "native_calls_started": 0})
            return
        current = inspect(root, identity)
        if current["status"] != "queued":
            raise ValueError("Another worker already admitted this trial")
        protocol = current["protocol"]
        tasks = [t for t in load_tasks().values() if t.split == "optimization"]
        if protocol["sources"] != _implementation() or protocol["tasks"] != {t.id: t.fingerprint for t in tasks}:
            raise ValueError("Trial source changed")
        write_new(path / "started.json", {"trial_id": identity, "started_at": now()})
        try:
            runtime = NativeRuntime(ROOT, path, rates=RATES, timeout_seconds=protocol["timeout_seconds"])
            order = ("before", "after") if int(identity[0], 16) % 2 == 0 else ("after", "before")
            rows = {arm: [] for arm in order}
            for index, task in enumerate(tasks):
                trial_order = order if index % 2 == 0 else tuple(reversed(order))
                for arm in trial_order:
                    rows[arm].extend(cases(runtime, path, arm, "optimization", [task], protocol[arm], 1))
            accepted, reason, regressions = select(rows["before"], rows["after"])
            result = {
                "trial_id": identity, "acceptance_passed": accepted, "selection_reason": reason,
                "regressions": regressions, "scope": "Three reused development tasks. No held-out inference.",
                "runtime": {"model": MODEL, "cli": runtime.version, "executable_sha256": runtime.codex_sha256},
                "cases": {arm: feedback(results) for arm, results in rows.items()},
                "tokens": {arm: sum(r["usage"]["total_tokens"] for r in results) for arm, results in rows.items()},
                "summed_invocation_seconds": {arm: sum(r["elapsed_seconds"] for r in results) for arm, results in rows.items()},
                "case_receipts": {arm: [r["call_id"] for r in results] for arm, results in rows.items()},
                "historical_rate_scenario_usd": {arm: sum(r["scenario_cost"] for r in results) for arm, results in rows.items()},
                "subscription_cash": None, "finished_at": now(),
            }
            measurement = write_new(path / "measurement.json", result)
            archive = runtime.retention.retain_file(measurement, kind="experiment-mcp-result", identity=identity)
            write_new(path / "result.json", {**result, "archive": archive})
        except Exception as error:
            write_new(path / "stopped.json", {"reason": type(error).__name__, "recorded_at": now()})
            raise


def handle(root, authorized, method, params):
    if method == "initialize":
        return {"protocolVersion": "2025-06-18", "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "observatory-harness-experiments", "version": "0.1.0"}}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "ping":
        return {}
    if method != "tools/call":
        raise ValueError("Unsupported MCP method")
    name, args = params["name"], params.get("arguments", {})
    apis = {"list_harness_settings": lambda: {"settings": HARNESS, "benchmark": VERSION, "execution_enabled": authorized},
            "plan_harness_trial": lambda **kwargs: plan(root, **kwargs),
            "run_harness_trial": lambda trial_id: launch(root, trial_id, authorized),
            "get_harness_trial": lambda trial_id: inspect(root, trial_id),
            "record_harness_decision": lambda trial_id, decision, rationale: decide(root, trial_id, decision, rationale)}
    try:
        result = apis[name](**args)
        return {"content": [{"type": "text", "text": canonical(result)}], "isError": False}
    except (OSError, TypeError, KeyError, ValueError) as error:
        return {"content": [{"type": "text", "text": f"{type(error).__name__}: {str(error)[:280]}"}], "isError": True}


def serve(root, authorized):
    for line in sys.stdin:
        request = None
        try:
            if len(line.encode()) > 100_000:
                raise ValueError("Input exceeds MCP message limit")
            request = json.loads(line)
            if request["jsonrpc"] != "2.0":
                raise ValueError("Expected JSON-RPC 2.0")
            if "id" not in request:
                continue
            result = {"result": handle(root, authorized, request["method"], request.get("params", {}))}
        except (TypeError, KeyError, ValueError) as error:
            result = {"error": {"code": -32602, "message": type(error).__name__}}
        print(canonical({"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None, **result}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "work/security/harness-experiments-mcp")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--worker")
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_relative_to((ROOT / "work/security").resolve()):
        parser.error("MCP trial data must stay in work/security")
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if args.worker:
        if not args.execute:
            parser.error("Worker requires explicit native authorization")
        run_worker(root, args.worker)
    else:
        serve(root, args.execute)


if __name__ == "__main__":
    main()
