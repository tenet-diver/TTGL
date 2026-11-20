import io
import json

from ttgl.decision_history.memory import lookup, serve


def episode():
    return {"id": "first", "checkpoint": 1, "source_event_sha256": "a" * 64,
            "summary": "Use an ordered structural parse", "conversation": "grammar " * 1100}


def test_only_frozen_predecessors_are_searchable():
    assert lookup([episode()], "search", {"query": "structural"})["hits"][0]["id"] == "first"
    assert lookup([episode()], "search", {"query": "later-checkpoint"})["hits"] == []
    text = lookup([episode()], "read", {"id": "first", "view": "conversation"})
    assert len(text["text"]) == 7000 and text["next_offset"] == 7000


def test_mcp_read_has_a_durable_observation(tmp_path):
    bundle = tmp_path / "bundle.json"
    bundle.write_text(json.dumps([episode()]))
    params = {"name": "read", "arguments": {"id": "first", "view": "summary"}}
    request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params})
    out = io.StringIO()
    spool = tmp_path / "spool"
    serve(bundle, spool, io.StringIO(request + "\n" + request + "\n"), out)
    rows = list(spool.glob("*.json"))
    assert len(rows) == 1
    receipt = json.loads(rows[0].read_text())
    assert receipt["answer"]["text"] == episode()["summary"]
    assert receipt["returned_bytes"] > 0
    replies = [json.loads(line) for line in out.getvalue().splitlines()]
    assert replies[0] == replies[1] and replies[0]["result"]["isError"] is False
