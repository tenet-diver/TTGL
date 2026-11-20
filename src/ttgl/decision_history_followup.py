"""Prepare and serve matched, read-only views of frozen predecessor history."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
import time

from .decision_history.grade import PROBLEMS
from .decision_history.memory import TOOLS, export_episode, lookup
from .experience_routing.io import canonical, digest, file_digest, read, write_new
from .sim_ablation.study import ROOT, create_once, matrix_lock

ARMS = ("summary-only", "full-history")
MODULE = "ttgl.decision_history_followup"
PRIVATE_ROOT = ROOT / "work/security"


def _public_checks(trace):
    """Index only completed shell results exposed to the predecessor."""
    checks = {}
    for line_number, line in enumerate(trace.splitlines(), 1):
        event = json.loads(line)
        item = event.get("item", {})
        if event.get("type") != "item.completed" or (
            item.get("type"), item.get("server"), item.get("tool")
        ) != ("mcp_tool_call", "worker", "shell"):
            continue
        arguments, result = item.get("arguments"), item.get("result")
        if not isinstance(arguments, dict) or not isinstance(result, dict):
            continue
        content = result.get("content", [])
        if (not isinstance(content, list) or len(content) != 1 or not isinstance(content[0], dict)
                or content[0].get("type") != "text"):
            continue
        try:
            observed = json.loads(content[0]["text"])
        except (ValueError, TypeError, KeyError):
            continue
        if not isinstance(observed, dict):
            continue
        item_id, command = item.get("id"), arguments.get("command")
        code, timed_out = observed.get("exit_code"), observed.get("timed_out")
        if not isinstance(item_id, str) or not isinstance(command, str) or not command:
            continue
        if type(timed_out) is not bool or (timed_out and code is not None) or (not timed_out and type(code) is not int):
            continue
        if item_id in checks:
            raise ValueError("Ambiguous public check item ID")
        checks[item_id] = {
            "item_id": item_id,
            "trace_line": line_number,
            "command_preview": command[:2000],
            "command_sha256": digest(command.encode()),
            "command_truncated": len(command) > 2000,
            "result_sha256": digest(observed),
            "exit_code": code,
            "timed_out": timed_out,
            "stdout_preview": observed["stdout"][:800] if isinstance(observed.get("stdout"), str) else None,
            "stderr_preview": observed["stderr"][:400] if isinstance(observed.get("stderr"), str) else None,
            "output_may_be_clipped": observed.get("output_may_be_clipped"),
        }
    return checks


def decision_records(episode, trace, declarations):
    """Resolve declared evidence references against the identified source bytes."""
    if digest(trace) != episode["source_event_sha256"]:
        raise ValueError("Predecessor trace digest differs")
    if not isinstance(declarations, list) or len(declarations) > 20:
        raise ValueError("Expected at most 20 decisions per predecessor")
    checks = _public_checks(trace) if declarations else {}
    records = {}
    for entry in declarations:
        if not isinstance(entry, dict) or set(entry) != {
            "decision", "rationale", "alternatives", "applies_when", "check_item_id"
        }:
            raise ValueError("Invalid decision record fields")
        if any(not isinstance(entry[key], str) or not entry[key].strip() or len(entry[key]) > 1500
               for key in ("decision", "rationale", "applies_when")):
            raise ValueError("Decision, rationale and applicability must be bounded nonempty text")
        alternatives = entry["alternatives"]
        if not isinstance(alternatives, list) or len(alternatives) > 8 or any(
            not isinstance(text, str) or not text.strip() or len(text) > 300 for text in alternatives
        ):
            raise ValueError("Invalid decision alternatives")
        item_id = entry["check_item_id"]
        if item_id is not None and (not isinstance(item_id, str) or item_id not in checks):
            raise ValueError("Supporting check must identify a completed public shell result in this trace")
        record = {
            "session_id": episode["id"],
            "checkpoint": episode["checkpoint"],
            "source_event_sha256": episode["source_event_sha256"],
            "decision": entry["decision"],
            "rationale": entry["rationale"],
            "alternatives": alternatives,
            "applies_when": entry["applies_when"],
            "supporting_check": checks.get(item_id),
        }
        record_id = "decision-" + digest(record)
        records[record_id] = {"id": record_id, **record}
    return list(records.values())


def prepare(pilot, output, problem, checkpoint, declarations):
    """Use only the selected pilot handoff's registered predecessor lineage."""
    if problem not in PROBLEMS or type(checkpoint) is not int or checkpoint not in (2, 3):
        raise ValueError("Unknown SlopCodeBench handoff")
    pilot, output = pilot.resolve(), output.resolve()
    if pilot.is_relative_to(output) or output.is_relative_to(pilot):
        raise ValueError("Use a separate follow-up directory")
    handoff = f"{problem}-c{checkpoint}"
    bundle_path = pilot / "bundles" / f"{handoff}.json"
    frozen = bundle_path.read_bytes()
    episodes = json.loads(frozen)
    predecessors = [f"{problem}-c1-source", *([f"{problem}-c2-baseline"] if checkpoint == 3 else [])]
    if not isinstance(episodes, list) or [row["id"] for row in episodes] != predecessors:
        raise ValueError("Unexpected predecessor roster")
    if not isinstance(declarations, dict) or set(declarations) - set(predecessors):
        raise ValueError("Decision declarations must belong to the registered predecessors")

    summary = []
    for number, episode in enumerate(episodes, 1):
        source_id = episode["id"]
        folder = pilot / "invocations" / source_id
        completed_path = folder / "completed.json"
        completion = read(completed_path)
        trace_path = folder / "native" / source_id / "events.jsonl"
        trace = trace_path.read_bytes()
        if (completion["call_id"] != source_id or completion["events_sha256"] != digest(trace)
                or export_episode(folder, problem, number, completion) != episode):
            raise ValueError("Frozen predecessor bundle disagrees with the retained native session")
        summary.append({
            "id": source_id, "checkpoint": number, "source_event_sha256": episode["source_event_sha256"],
            "summary": episode["summary"], "decisions": decision_records(episode, trace, declarations.get(source_id, [])),
        })

    payloads = {
        "summary-only": summary,
        "full-history": [{**record, "conversation": episode["conversation"]}
                         for record, episode in zip(summary, episodes, strict=True)],
    }
    manifest = {
        "version": 1, "handoff": handoff, "predecessors": predecessors,
        "pilot_bundle_sha256": digest(frozen), "search_index_sha256": digest(summary),
        "implementation_sha256": file_digest(__file__),
        "arms": {arm: digest(canonical(records).encode() + b"\n") for arm, records in payloads.items()},
    }
    with matrix_lock(output):
        manifest_path = output / "manifest.json"
        if manifest_path.exists() and read(manifest_path) != manifest:
            raise ValueError("Immutable follow-up manifest differs")
        for arm, records in payloads.items():
            create_once(output / f"{arm}.json", records)
        create_once(manifest_path, manifest)
    return manifest


class HistoryView:
    def __init__(self, directory, arm, *, expected_manifest_sha256=None):
        if arm not in ARMS:
            raise ValueError("Unknown history arm")
        manifest_bytes = (directory / "manifest.json").read_bytes()
        self.manifest_sha256 = digest(manifest_bytes)
        if expected_manifest_sha256 is not None and self.manifest_sha256 != expected_manifest_sha256:
            raise ValueError("Follow-up manifest differs from the configured pin")
        manifest = json.loads(manifest_bytes)
        payload = (directory / f"{arm}.json").read_bytes()
        if (manifest["version"] != 1 or manifest["implementation_sha256"] != file_digest(__file__)
                or manifest["arms"][arm] != digest(payload)):
            raise ValueError("Frozen history view differs from its manifest")
        self.episodes = json.loads(payload)
        self.documents = []
        self.decisions = {}
        common = []
        for episode in self.episodes:
            public = {key: value for key, value in episode.items() if key != "conversation"}
            common.append(public)
            self.documents.append((episode["id"], episode["checkpoint"], "session", episode["summary"].casefold()))
            for decision in episode["decisions"]:
                record_id = decision["id"]
                self.decisions[record_id] = decision
                self.documents.append((record_id, episode["checkpoint"], "decision", canonical(decision).casefold()))
        if digest(common) != manifest["search_index_sha256"]:
            raise ValueError("History views must use the same search input")
        self.views = ["summary", "decision"]
        if arm == "full-history":
            self.views.append("conversation")
        elif any("conversation" in episode for episode in self.episodes):
            raise ValueError("Summary-only bundles cannot contain conversation pages")

    def tools(self):
        return [
            {**TOOLS[0], "description": "Find prior session summaries and individual decisions by keyword."},
            {"name": "read", "description": "Open a prior session or an individual decision with its evidence reference.",
             "inputSchema": {"type": "object", "required": ["id", "view"], "additionalProperties": False,
                             "properties": {"id": {"type": "string"}, "view": {"enum": self.views},
                                            "offset": {"type": "integer", "minimum": 0}}}},
        ]

    def call(self, name, args):
        if name == "search" and set(args) == {"query"} and isinstance(args["query"], str) and len(args["query"]) <= 300:
            words = re.findall(r"[\w]+", args["query"].casefold())
            hits = []
            for record_id, checkpoint, kind, searchable in self.documents:
                score = sum(word in searchable for word in words)
                if score or not words:
                    hits.append({"id": record_id, "checkpoint": checkpoint, "kind": kind, "score": score})
            return {"hits": sorted(hits, key=lambda item: (-item["score"], item["checkpoint"], item["id"]))}
        if name == "read" and {"id", "view"} <= set(args) <= {"id", "view", "offset"} and args["view"] in self.views:
            if args["view"] != "decision":
                return lookup(self.episodes, name, args)
            offset = args.get("offset", 0)
            if type(offset) is int and offset == 0 and args["id"] in self.decisions:
                return self.decisions[args["id"]]
        raise ValueError("Invalid history request or ineligible source")


def serve(view, spool, source=sys.stdin, sink=sys.stdout):
    for line in source:
        req = None
        try:
            req = json.loads(line) if len(line) <= 50000 else None
            if not isinstance(req, dict) or req.get("jsonrpc") != "2.0":
                raise ValueError("Invalid protocol request")
            if "id" not in req:
                continue
            method, params = req["method"], req.get("params", {})
            if method == "initialize":
                result = {"protocolVersion": params.get("protocolVersion", "2025-06-18"),
                          "capabilities": {"tools": {}}, "serverInfo": {"name": "observatory-decision-history", "version": "2"}}
            elif method == "tools/list":
                result = {"tools": view.tools()}
            elif method == "tools/call":
                start = time.monotonic()
                name, args = params["name"], params["arguments"]
                if not isinstance(name, str) or not isinstance(args, dict):
                    raise ValueError("Invalid tool request")
                path = spool / (digest(req["id"]) + ".json")
                if path.exists():
                    row = read(path)
                    if (row["tool"], row["args"]) != (name, args):
                        raise ValueError("Conflicting receipt")
                else:
                    try:
                        answer, error = view.call(name, args), False
                    except (ValueError, TypeError, KeyError):
                        answer, error = {"error": "Invalid history request or ineligible source"}, True
                    row = {"tool": name, "args": args, "answer": answer, "error": error,
                           "returned_bytes": len(canonical(answer).encode()), "elapsed_seconds": time.monotonic() - start}
                    write_new(path, row)
                result = {"content": [{"type": "text", "text": canonical(row["answer"])}], "isError": row["error"]}
            elif method == "ping":
                result = {}
            else:
                raise ValueError("Unknown method")
            response = {"result": result}
        except (ValueError, TypeError, KeyError, AttributeError):
            response = {"error": {"code": -32602, "message": "Invalid history request"}}
        sink.write(canonical({"jsonrpc": "2.0", "id": req.get("id") if isinstance(req, dict) else None, **response}) + "\n")
        sink.flush()


def codex_config(directory, arm, *, receipt_dir=None, expected_manifest_sha256=None):
    """Return arguments for a fresh Codex invocation's existing actor configuration."""
    view = HistoryView(directory, arm, expected_manifest_sha256=expected_manifest_sha256)
    arguments = ["-m", MODULE, "serve", str(directory.resolve()), arm, "--manifest-sha256", view.manifest_sha256]
    if receipt_dir is not None:
        arguments.extend(("--receipt-dir", str(receipt_dir.resolve())))
    values = {
        "mcp_servers.history.command": sys.executable,
        "mcp_servers.history.args": arguments,
        "mcp_servers.history.required": True,
        "mcp_servers.history.tool_timeout_sec": 8,
        "mcp_servers.history.enabled_tools": ["search", "read"],
        "mcp_servers.history.tools.search.approval_mode": "approve",
        "mcp_servers.history.tools.read.approval_mode": "approve",
    }
    flags = []
    for key, value in values.items():
        flags.extend(("--config", f"{key}={json.dumps(value)}"))
    flags.extend(("--config", "mcp_servers.history.env={PYTHONPATH=" + json.dumps(str(ROOT / "src")) + "}"))
    return flags


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    build = actions.add_parser("prepare")
    build.add_argument("pilot", type=Path)
    build.add_argument("directory", type=Path)
    build.add_argument("problem", choices=PROBLEMS)
    build.add_argument("checkpoint", type=int, choices=(2, 3))
    build.add_argument("--decisions", type=Path)
    for name in ("serve", "codex-config"):
        command = actions.add_parser(name)
        command.add_argument("directory", type=Path)
        command.add_argument("arm", choices=ARMS)
        if name == "serve":
            command.add_argument("--manifest-sha256", required=True)
            command.add_argument("--receipt-dir", type=Path)
    args = parser.parse_args()
    paths = [args.directory, args.pilot, args.decisions] if args.action == "prepare" else [args.directory, getattr(args, "receipt_dir", None)]
    if any(not path.resolve().is_relative_to(PRIVATE_ROOT.resolve()) for path in paths if path is not None):
        parser.error("Keep predecessor bundles, annotations and receipts under work/security")
    if args.action == "prepare":
        manifest = prepare(args.pilot, args.directory, args.problem, args.checkpoint,
                           read(args.decisions) if args.decisions else {})
        print(json.dumps(manifest, indent=2))
    elif args.action == "codex-config":
        print(json.dumps(codex_config(args.directory, args.arm), indent=2))
    else:
        view = HistoryView(args.directory, args.arm, expected_manifest_sha256=args.manifest_sha256)
        spool = args.receipt_dir
        if spool is None:
            parent = args.directory / "retrieval" / args.arm
            parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            spool = Path(tempfile.mkdtemp(prefix="session-", dir=parent))
        else:
            spool.mkdir(parents=True, exist_ok=False, mode=0o700)
        serve(view, spool)


if __name__ == "__main__":
    main()
