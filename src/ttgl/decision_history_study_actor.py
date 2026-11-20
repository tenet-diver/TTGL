"""Expose actionable timeout feedback over the frozen offline worker bridge."""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import sys

from .experience_routing.io import digest, read, write_new
from .sim_ablation.runtime import _bridge

TIMEOUT_HELP = "timeout_seconds must be an integer from 1 through 30 seconds. Omit it to use the 15-second default."


def serve(config, source, sink):
    for line in source:
        try:
            request = json.loads(line) if len(line.encode()) <= 100000 else None
        except (ValueError, UnicodeError):
            request = None
        if isinstance(request, dict) and request.get("jsonrpc") == "2.0" and "id" in request:
            params = request.get("params", {})
            if (request.get("method") == "tools/call" and isinstance(params, dict)
                    and params.get("name") == "shell" and isinstance(args := params.get("arguments"), dict)):
                timeout = args.get("timeout_seconds", 15)
                if type(timeout) is not int or not 1 <= timeout <= 30:
                    ident = request["id"]
                    path = Path(config["invalid_requests"]) / (digest(ident) + ".json")
                    row = {"id": ident, "args": args, "error": TIMEOUT_HELP}
                    if path.exists() and read(path) != row:
                        raise ValueError("Conflicting rejected tool request")
                    if not path.exists():
                        write_new(path, row)
                    reply = {"jsonrpc": "2.0", "id": ident, "result": {
                        "content": [{"type": "text", "text": TIMEOUT_HELP}], "isError": True}}
                    sink.write(json.dumps(reply) + "\n")
                    sink.flush()
                    continue
        response = io.StringIO()
        _bridge(config, (line,), response)
        if reply := response.getvalue():
            result = json.loads(reply)
            if isinstance(request, dict) and request.get("method") == "tools/list" and "result" in result:
                shell = result["result"]["tools"][0]
                shell["description"] += " " + TIMEOUT_HELP
                shell["inputSchema"]["properties"]["timeout_seconds"]["default"] = 15
                reply = json.dumps(result) + "\n"
            sink.write(reply)
            sink.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge", type=Path, required=True)
    serve(read(parser.parse_args().bridge), sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
