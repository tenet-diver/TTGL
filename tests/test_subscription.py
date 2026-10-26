import json
from pathlib import Path
import sys
import time

import pytest

from ttgl.subscription import (AppServer, MeterUnavailable, collect, main,
                               read_threads, sanitize_usage)


def usage(thread="root-one", credits=100, dollars=200):
    return {"summary": {"private_account_history": "MUST_NOT_PERSIST"},
            "threadUsage": {"threadId": thread, "estimatedUsageCreditsMicros": credits,
                            "estimatedUsageUsdMicros": dollars, "groups": [{
                                "model": "model-a", "reasoningEffort": "medium", "speed": None,
                                "estimatedUsageCreditsMicros": credits,
                                "inputTokens": 100, "cachedInputTokens": 40,
                                "netNewInputTokens": 60, "outputTokens": 10,
                                "totalTokens": 110, "private": "MUST_NOT_PERSIST"}]}}


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def request(self, method, params):
        self.calls.append((method, params))
        value = self.responses[params["threadId"]]
        if isinstance(value, Exception):
            raise value
        return value


def test_sanitizes_account_history_and_does_not_add_overlapping_tokens():
    result = sanitize_usage(usage(), "root-one")
    assert result["usage"]["groups"][0]["totalTokens"] == 110
    assert "MUST_NOT_PERSIST" not in json.dumps(result)
    assert result["usage"]["estimatedUsageCreditsMicros"] == 100


def test_deduplicates_independent_threads_and_requires_attestation():
    client = FakeClient({"root-one": usage(), "root-two": usage("root-two", 300, 400)})
    report = collect(["root-one", "root-one", "root-two"], client_factory=lambda: client)
    assert len(client.calls) == 2
    assert report["status"] == "available"
    assert report["totals"]["estimated_usage_credits_micros"] is None
    report = collect(["root-one", "root-two"], independent_roots=True,
                     client_factory=lambda: client)
    assert report["totals"] == {"estimated_usage_credits_micros": 400,
                                "estimated_usage_usd_micros": 600}
    assert all(method == "account/usage/read" for method, _ in client.calls)


def test_partial_and_nullable_estimates_stay_unknown():
    client = FakeClient({"root-one": usage(dollars=None), "root-two": {"threadUsage": None}})
    report = collect(["root-one"], independent_roots=True, client_factory=lambda: client)
    assert report["totals"]["estimated_usage_credits_micros"] == 100
    assert report["totals"]["estimated_usage_usd_micros"] is None
    report = collect(["root-one", "root-two"], independent_roots=True,
                     client_factory=lambda: client)
    assert report["status"] == "incomplete"
    assert all(value is None for value in report["totals"].values())
    assert report["threads"][1]["usage"] is None


@pytest.mark.parametrize("mutate", [
    lambda v: v["threadUsage"].update(threadId="another-thread"),
    lambda v: v["threadUsage"].update(estimatedUsageCreditsMicros=True),
    lambda v: v["threadUsage"].update(estimatedUsageCreditsMicros=-1),
    lambda v: v["threadUsage"].update(estimatedUsageUsdMicros=3.5),
    lambda v: v["threadUsage"].update(groups=None),
    lambda v: v["threadUsage"]["groups"][0].update(inputTokens=float("nan")),
])
def test_malformed_estimate_cannot_become_a_cost(mutate):
    response = usage()
    mutate(response)
    client = FakeClient({"root-one": response})
    report = collect(["root-one"], independent_roots=True, client_factory=lambda: client)
    assert report["status"] == "incomplete"
    assert report["threads"][0]["usage"] is None
    assert all(value is None for value in report["totals"].values())


def test_state_collection_includes_router_and_preserves_unfinished_status(tmp_path):
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"schema_version": 3, "run_id": "run-one", "task_id": "task-one",
                                "status": "running", "inflight": {"request_id": "unfinished"},
                                "controller_thread_id": "root-one", "expert_thread_id": "root-two",
                                "usage_threads": {"router": {}, "root-one": {}}}))
    threads, sources, finalized = read_threads([state], ["root-two"])
    assert threads == ["root-two", "router", "root-one"]
    assert sources[0]["sha256"] and finalized is False
    client = FakeClient({thread: usage(thread) for thread in threads})
    report = collect(threads, independent_roots=True, finalized=finalized,
                     client_factory=lambda: client)
    assert report["totals_status"] == "states_unfinished"
    assert report["totals"]["estimated_usage_credits_micros"] is None


def fake_executable(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "fake-codex"
    path.write_text(f"#!{sys.executable}\n" + body)
    path.chmod(0o755)
    return path


def test_real_stdio_handshake_rpc_notifications_and_sanitization(tmp_path):
    trace = tmp_path / "requests.jsonl"
    executable = fake_executable(tmp_path, f'''
import json, sys
trace = open({str(trace)!r}, 'w')
for line in sys.stdin:
    request = json.loads(line)
    trace.write(json.dumps(request) + '\\n'); trace.flush()
    if request.get('method') == 'initialize':
        print(json.dumps({{'id':request['id'], 'result':{{}}}}), flush=True)
    elif request.get('method') == 'account/usage/read':
        print(json.dumps({{'method':'unrelated/notification', 'params':{{'private':'SECRET'}}}}), flush=True)
        print(json.dumps({{'id':999, 'method':'unsafe/server/request', 'params':{{}}}}), flush=True)
        response = {usage()!r}
        print(json.dumps({{'id':request['id'], 'result':response}}), flush=True)
''')
    with AppServer(str(executable), timeout=5) as client:
        with pytest.raises(ValueError, match="Account-wide"):
            client.request("account/usage/read", {})
        with pytest.raises(ValueError, match="Only initialization"):
            client.request("turn/start", {})
        result = sanitize_usage(client.request("account/usage/read", {"threadId": "root-one"}),
                                "root-one")
    requests = [json.loads(line) for line in trace.read_text().splitlines()]
    assert [r.get("method") for r in requests[:3]] == [
        "initialize", "initialized", "account/usage/read"]
    assert "SECRET" not in json.dumps(result)
    assert "MUST_NOT_PERSIST" not in json.dumps(result)


def test_timeout_cleans_process_and_sanitizes_stderr(tmp_path):
    executable = fake_executable(tmp_path, "import time\ntime.sleep(30)\n")
    started = time.monotonic()
    client = AppServer(str(executable), timeout=0.1)
    with pytest.raises(MeterUnavailable, match="app_server_timeout"):
        with client:
            pass
    assert time.monotonic() - started < 3
    assert client.process is None and client.stderr is None
    executable = fake_executable(tmp_path, "import sys\nsys.stderr.write('secret-user: Read-only file system (os error 30)')\nsys.exit(1)\n")
    report = collect(["root-one"], client_factory=lambda: AppServer(str(executable), 5))
    assert report["threads"][0]["reason"] == "read_only_state_directory"
    assert "secret-user" not in json.dumps(report)


def test_cli_persists_unavailable_without_overwriting(tmp_path):
    executable = fake_executable(tmp_path, "import sys\nsys.stderr.write('Read-only file system')\nsys.exit(1)\n")
    output = tmp_path / "meter.json"
    args = ["--codex", str(executable), "--thread-id", "root-one", "--output", str(output),
            "--independent-roots"]
    assert main(args) == 2
    report = json.loads(output.read_text())
    assert report["totals"]["estimated_usage_credits_micros"] is None
    assert report["new_model_inference_requested"] is False
    original = output.read_bytes()
    with pytest.raises(SystemExit):
        main(args)
    assert output.read_bytes() == original


def test_no_threads_cannot_trigger_account_wide_collection():
    with pytest.raises(ValueError, match="account-wide"):
        collect([])


def test_terminal_failed_run_with_unknown_thread_cannot_report_complete_task_spend(tmp_path):
    state = tmp_path / "state.json"
    state.write_text(json.dumps({
        "schema_version": 3, "run_id": "failed-run", "task_id": "task-one",
        "status": "backend_failed", "inflight": None, "turns": 2,
        "controller_thread_id": "root-one", "expert_thread_id": None,
        "usage_threads": {"root-one": {}},
        "usage_accounting_issues": [{"request_id": "failed-run:2", "thread_id": None,
                                     "issues": [{"reason": "cumulative_usage_without_thread"}]}],
    }))
    executable = fake_executable(tmp_path, f'''
import json, sys
for line in sys.stdin:
    request = json.loads(line)
    if request.get('method') == 'initialize':
        print(json.dumps({{'id':request['id'], 'result':{{}}}}), flush=True)
    elif request.get('method') == 'account/usage/read':
        print(json.dumps({{'id':request['id'], 'result':{usage()!r}}}), flush=True)
''')
    output = tmp_path / "incomplete-task-meter.json"
    assert main(["--state", str(state), "--codex", str(executable), "--output", str(output),
                 "--independent-roots"]) == 2
    report = json.loads(output.read_text())
    assert report["selected_states_finalized"] is True
    assert report["selected_states_usage_ledger_complete"] is False
    assert report["status"] == "incomplete"
    assert report["threads"][0]["usage"]["estimatedUsageCreditsMicros"] == 100
    assert report["totals_status"] == "state_usage_ledger_incomplete"
    assert all(value is None for value in report["totals"].values())
    assert report["sources"][0]["usage_accounting_issue_count"] == 1
