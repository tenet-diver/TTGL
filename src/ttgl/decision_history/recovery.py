"""Recover the first stopped candidate from its two retained successful edit receipts."""
from __future__ import annotations

import ast
from pathlib import Path

from ..experience_routing.io import digest, file_digest, read, write_new


def recover_l2m(root):
    folder = root / "invocations" / "l2m-c2-baseline"
    completion = read(folder / "completed.json")
    if completion["candidate_integrity"] or completion["status"] != "completed" or completion["candidate"] is not None:
        raise ValueError("Unexpected source admission for the recorded recovery")
    path = root / "recovery" / "l2m-c2-baseline.json"
    if path.exists():
        receipt = read(path)
        if receipt["completion_sha256"] != file_digest(folder / "completed.json") or digest(receipt["candidate"].encode()) != receipt["candidate_sha256"]:
            raise ValueError("Recovery receipt disagrees with the original completion")
        return receipt
    calls = sorted((folder / "actor-spool").glob("*/started.json"), key=lambda p: p.stat().st_mtime_ns)
    if len(calls) != 5:
        raise ValueError("Unexpected original tool roster")
    commands = [read(path)["arguments"]["command"] for path in calls]
    if not commands[2].startswith("cat > l2m.py <<'PY'\n") or not commands[4].startswith("python3 - <<'PY'\np='l2m.py'\n"):
        raise ValueError("The retained source writes do not match the recovery")
    for call in (calls[2], calls[4]):
        status = read(call.with_name("result.json"))
        if status["exit_code"] != 0 or status["timed_out"]:
            raise ValueError("Source write did not finish successfully")
    initial, compile_cmd = commands[2].split("\n", 1)[1].split("\nPY\n", 1)
    if compile_cmd.strip() != "python3 -m py_compile l2m.py":
        raise ValueError("Unexpected trailing shell command")
    bare, checks = commands[4].split("\n", 1)[1].split("\nPY\n", 1)
    nodes = ast.parse(bare).body
    if (len(nodes) != 6 or [ast.unparse(n) for n in nodes[:4]] !=
            ["p = 'l2m.py'", "s = open(p).read()", "a = s.index('def process_list(')",
             "b = s.index('\\ndef convert_lists', a)"]
            or ast.unparse(nodes[-1]) != "open(p, 'w').write(s)"
            or not checks.startswith("python3 - <<'PY'\nimport l2m\ncases=[")):
        raise ValueError("Unexpected retained patch or post-write check")
    patch = nodes[4]
    if (not isinstance(patch, ast.Assign) or [ast.unparse(x) for x in patch.targets] != ["s"]
            or not isinstance(patch.value, ast.BinOp) or not isinstance(patch.value.op, ast.Add)
            or ast.unparse(patch.value.right) != "s[b:]" or not isinstance(patch.value.left, ast.BinOp)
            or not isinstance(patch.value.left.op, ast.Add) or ast.unparse(patch.value.left.left) != "s[:a]"):
        raise ValueError("Unexpected patch operation")
    text = ast.literal_eval(patch.value.left.right)
    if not isinstance(text, str):
        raise ValueError("Replacement must be literal text")
    initial += "\n"
    start = initial.index("def process_list(")
    end = initial.index("\ndef convert_lists", start)
    source = initial[:start] + text + initial[end:]
    ast.parse(source)
    receipt = {"call_id": completion["call_id"], "candidate": source, "candidate_sha256": digest(source.encode()),
               "completion_sha256": file_digest(folder / "completed.json"),
               "source_receipts": [file_digest(c) for c in calls],
               "method": "Exact heredoc bytes plus literal text splice from retained successful writes. No agent command or inference replay."}
    write_new(path, receipt)
    return receipt
