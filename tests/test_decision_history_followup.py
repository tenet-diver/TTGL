import io
import json
import tomllib
from types import SimpleNamespace

import pytest

from ttgl.decision_history.memory import export_episode
from ttgl.decision_history_followup import HistoryView, codex_config, decision_records, prepare, serve
from ttgl.decision_history_followup_trial import TRIAL_ID, _invoke
from ttgl.experience_routing.io import canonical, digest, file_digest, read, write_new
from ttgl.sim_ablation.runtime import AmbiguousInvocation


@pytest.fixture
def predecessor(tmp_path):
    pilot = tmp_path / "pilot"
    source_id = "l2m-c1-source"
    folder = pilot / "invocations" / source_id
    native = folder / "native" / source_id
    native.mkdir(parents=True)
    (native / "prompt.txt").write_text("Implement the public requirement.")
    observed = {"exit_code": 0, "timed_out": False, "stdout": "ordering passes", "stderr": "",
                "output_may_be_clipped": False}
    shell = {"type": "mcp_tool_call", "id": "item_7", "server": "worker", "tool": "shell",
             "arguments": {"command": "python3 -m unittest ordering"},
             "result": {"content": [{"type": "text", "text": canonical(observed)}]}}
    events = [
        {"type": "item.completed", "item": {"type": "agent_message", "id": "item_1", "text": "transcriptonly " * 900}},
        {"type": "item.started", "item": {**shell, "id": "item_6"}},
        {"type": "item.completed", "item": shell},
        {"type": "item.completed", "item": {**shell, "id": "item_8", "server": "history"}},
    ]
    trace = "".join(canonical(event) + "\n" for event in events).encode()
    (native / "events.jsonl").write_bytes(trace)
    completion = {"call_id": source_id, "events_sha256": digest(trace), "answer": {"summary": "Use a structural parse"}}
    write_new(folder / "completed.json", completion)
    episode = export_episode(folder, "l2m", 1, completion)
    write_new(pilot / "bundles/l2m-c2.json", [episode])
    declaration = {"decision": "Preserve source ordering", "rationale": "The output order is observable",
                   "alternatives": ["Sort by key"], "applies_when": "Ordering is part of the public contract",
                   "check_item_id": "item_7"}
    return pilot, episode, trace, observed, declaration


def test_decision_resolves_exact_observation(predecessor):
    _, episode, trace, observed, declaration = predecessor
    record, = decision_records(episode, trace, [declaration, declaration])
    assert record["applies_when"] == declaration["applies_when"]
    assert record["source_event_sha256"] == digest(trace)
    assert record["supporting_check"] == {
        "item_id": "item_7", "trace_line": 3, "command_preview": "python3 -m unittest ordering",
        "command_sha256": digest(b"python3 -m unittest ordering"), "command_truncated": False,
        "result_sha256": digest(observed), "exit_code": 0, "timed_out": False,
        "stdout_preview": "ordering passes", "stderr_preview": "", "output_may_be_clipped": False,
    }
    assert decision_records(episode, trace, [{**declaration, "check_item_id": None}])[0]["supporting_check"] is None


@pytest.mark.parametrize("item_id", ["item_6", "item_8", "invented"])
def test_only_retained_completed_public_checks_can_be_cited(predecessor, item_id):
    _, episode, trace, _, declaration = predecessor
    with pytest.raises(ValueError, match="completed public shell result"):
        decision_records(episode, trace, [{**declaration, "check_item_id": item_id}])


def test_paired_views_share_search_and_only_full_opens_conversations(tmp_path, predecessor):
    pilot, episode, _, _, declaration = predecessor
    output = tmp_path / "followup"
    annotations = {episode["id"]: [declaration]}
    hash_before = file_digest(pilot / "bundles/l2m-c2.json")
    assert prepare(pilot, output, "l2m", 2, annotations) == prepare(pilot, output, "l2m", 2, annotations)
    assert file_digest(pilot / "bundles/l2m-c2.json") == hash_before
    with pytest.raises(ValueError, match="Immutable follow-up manifest"):
        prepare(pilot, output, "l2m", 2, {})

    summary = HistoryView(output, "summary-only")
    full = HistoryView(output, "full-history")
    assert "conversation" not in read(output / "summary-only.json")[0]
    for query in ("", "structural", "Source ordering", "transcriptonly"):
        assert summary.call("search", {"query": query}) == full.call("search", {"query": query})
    assert full.call("search", {"query": "transcriptonly"}) == {"hits": []}
    summary_args = {"id": episode["id"], "view": "summary"}
    assert summary.call("read", summary_args) == full.call("read", summary_args)
    hit, = summary.call("search", {"query": "ordering"})["hits"]
    assert hit["kind"] == "decision"
    decision_args = {"id": hit["id"], "view": "decision", "offset": 0}
    assert summary.call("read", decision_args) == full.call("read", decision_args)
    args = {"id": episode["id"], "view": "conversation"}
    with pytest.raises(ValueError, match="ineligible source"):
        summary.call("read", args)
    page = full.call("read", args)
    assert len(page["text"]) == 7000 and page["next_offset"] == 7000


def test_prepare_rejects_out_of_lineage_and_tampered_trace(tmp_path, predecessor):
    pilot, episode, trace, _, _ = predecessor
    output = tmp_path / "followup"
    with pytest.raises(ValueError, match="registered predecessors"):
        prepare(pilot, output, "l2m", 2, {"l2m-c2-baseline": []})
    path = pilot / "invocations" / episode["id"] / "native" / episode["id"] / "events.jsonl"
    path.write_bytes(trace + b"\n")
    with pytest.raises(ValueError, match="disagrees with the retained native session"):
        prepare(pilot, output, "l2m", 2, {})
    assert not output.exists()


def test_summary_server_rejects_forged_conversation_reads_and_receipts_them(tmp_path, predecessor):
    pilot, episode, _, _, _ = predecessor
    output = tmp_path / "followup"
    prepare(pilot, output, "l2m", 2, {})
    (output / "full-history.json").rename(output / "withheld")
    view = HistoryView(output, "summary-only")
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "read",
               "arguments": {"id": episode["id"], "view": "conversation", "offset": 0}}}
    stream = io.StringIO(canonical(request) + "\n" + canonical(request) + "\n")
    replies = io.StringIO()
    spool = tmp_path / "receipts"
    serve(view, spool, stream, replies)
    first, second = map(json.loads, replies.getvalue().splitlines())
    assert first == second and first["result"]["isError"]
    path, = spool.glob("*.json")
    assert read(path)["error"] and read(path)["returned_bytes"] > 0


def test_codex_flags_and_frozen_bundle_integrity(tmp_path, predecessor):
    pilot, _, _, _, _ = predecessor
    output = tmp_path / "followup"
    prepare(pilot, output, "l2m", 2, {})
    flags = codex_config(output, "summary-only")
    assert flags[::2] == ["--config"] * 8
    config = tomllib.loads("\n".join(flags[1::2]))["mcp_servers"]["history"]
    assert config["required"] and config["args"][3:5] == [str(output), "summary-only"]
    assert config["args"][-2:] == ["--manifest-sha256", file_digest(output / "manifest.json")]
    assert config["enabled_tools"] == ["search", "read"]
    assert config["tools"] == {tool: {"approval_mode": "approve"} for tool in ("search", "read")}
    tools = HistoryView(output, "summary-only").tools()
    assert tools[1]["inputSchema"]["properties"]["view"]["enum"] == ["summary", "decision"]
    (output / "summary-only.json").write_text("[]\n")
    with pytest.raises(ValueError, match="differs from its manifest"):
        HistoryView(output, "summary-only")


def test_trial_refuses_to_replay_an_admitted_call(tmp_path, predecessor):
    pilot, _, _, _, _ = predecessor
    output = tmp_path / "followup"
    prepare(pilot, output, "l2m", 2, {})
    runtime = SimpleNamespace(output=output / "trial")
    folder = runtime.output / "invocations" / f"l2m-c2-summary-only-{TRIAL_ID}"
    write_new(folder / "started.json", {"started_at": "registered"})
    registration = {"trial_id": TRIAL_ID, "handoff": "l2m-c2", "history_manifest_sha256": file_digest(output / "manifest.json")}
    with pytest.raises(AmbiguousInvocation, match="admission has no terminal receipt"):
        _invoke(runtime, output, "summary-only", registration, {}, "l2m.py")
