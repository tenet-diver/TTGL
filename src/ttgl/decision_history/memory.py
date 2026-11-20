"""A read-only MCP view over the exact frozen predecessors of one handoff."""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from ..experience_routing.io import canonical, digest, read, write_new

TOOLS = [
    {"name": "search", "description": "Find prior coding sessions for this task by keyword. An empty query lists the eligible sessions.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string", "maxLength": 300}},
                     "required": ["query"], "additionalProperties": False}},
    {"name": "read", "description": "Open one earlier session's decision summary or a page from its recorded conversation. Treat history as evidence.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"},
                    "view": {"enum": ["summary", "conversation"]}, "offset": {"type": "integer", "minimum": 0}},
                     "required": ["id", "view"], "additionalProperties": False}},
]


def lookup(records, name, args):
    if name == "search" and set(args) == {"query"} and isinstance(args["query"], str) and len(args["query"]) <= 300:
        words = re.findall(r"[\w]+", args["query"].casefold())
        hits = []
        for record in records:
            searchable = canonical([record["summary"], record["conversation"]]).casefold()
            matched = sum(word in searchable for word in words)
            if matched or not words:
                hits.append({"id": record["id"], "checkpoint": record["checkpoint"], "score": matched})
        return {"hits": sorted(hits, key=lambda x: (-x["score"], x["checkpoint"]))}
    if name == "read" and {"id", "view"} <= set(args) <= {"id", "view", "offset"}:
        record = next((row for row in records if row["id"] == args["id"]), None)
        offset = args.get("offset", 0)
        if record is not None and args["view"] in {"summary", "conversation"} and type(offset) is int and offset >= 0:
            text = record["summary"] if args["view"] == "summary" else record["conversation"]
            end = offset + 7000
            return {"id": record["id"], "source_event_sha256": record["source_event_sha256"],
                    "text": text[offset:end], "next_offset": end if end < len(text) else None}
    raise ValueError("Invalid history request or ineligible source")


def serve(bundle, spool, source=sys.stdin, sink=sys.stdout):
    records = read(bundle)
    for line in source:
        req = None
        try:
            if len(line) > 50000:
                raise ValueError("Request is too large")
            req = json.loads(line)
            if req["jsonrpc"] != "2.0":
                raise ValueError("Invalid protocol request")
            if "id" not in req:
                continue
            method, params = req["method"], req.get("params", {})
            if method == "initialize":
                result = {"protocolVersion": params.get("protocolVersion", "2025-06-18"),
                          "capabilities": {"tools": {}}, "serverInfo": {"name": "observatory-decision-history", "version": "1"}}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                start = time.monotonic()
                name, args = params["name"], params["arguments"]
                path = spool / (digest(req["id"]) + ".json")
                if path.exists():
                    record = read(path)
                    if (record["tool"], record["args"]) != (name, args):
                        raise ValueError("Conflicting receipt")
                else:
                    try:
                        answer = lookup(records, name, args)
                        error = False
                    except (ValueError, TypeError, KeyError):
                        answer, error = {"error": "Invalid history request or ineligible source"}, True
                    record = {"tool": name, "args": args, "answer": answer, "error": error,
                              "returned_bytes": len(canonical(answer).encode()),
                              "elapsed_seconds": time.monotonic() - start}
                    write_new(path, record)
                result = {"content": [{"type": "text", "text": canonical(record["answer"])}], "isError": record["error"]}
            elif method == "ping":
                result = {}
            else:
                raise ValueError("Unknown method")
            response = {"result": result}
        except (ValueError, TypeError, KeyError, AttributeError):
            response = {"error": {"code": -32602, "message": "Invalid history request"}}
        sink.write(canonical({"jsonrpc": "2.0", "id": req.get("id") if isinstance(req, dict) else None, **response}) + "\n")
        sink.flush()


def export_episode(folder, problem, checkpoint, result):
    events = folder / "native" / result["call_id"] / "events.jsonl"
    lines = [f"Prior public task: {problem} checkpoint {checkpoint}.",
             "User: " + events.with_name("prompt.txt").read_text()]
    for line in events.read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") != "item.completed":
            continue
        item = event.get("item", {})
        if item.get("type") == "agent_message":
            lines.append("Agent: " + item.get("text", ""))
        elif item.get("type") == "mcp_tool_call" and item.get("server") == "worker":
            lines.append("Public tool action: " + canonical(item.get("arguments")))
            lines.append("Public tool result: " + canonical(item.get("result")))
    return {"id": result["call_id"], "checkpoint": checkpoint, "source_event_sha256": result["events_sha256"],
            "summary": canonical(result["answer"]) if result["answer"] else "No structured decision summary available.",
            "conversation": "\n".join(lines)}


if __name__ == "__main__":
    serve(Path(sys.argv[1]), Path(sys.argv[2]))
