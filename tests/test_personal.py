import json
import os
from pathlib import Path
import signal
import time

import pytest

from ttgl.personal import (
    ACTION_SCHEMA, CodexBackend, Request, Response, USAGE_FIELDS,
    parse_codex_events, run_task, validate_task,
)


class ScriptedBackend:
    """Control-flow fixture, not a substitute for model-quality measurement."""

    def __init__(self, *responses):
        self.responses = iter(responses)
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        if callable(response):
            return response(request)
        return response


def reply(action="complete", *, question="", context="", summary="done", thread="thread-small", usage=None):
    return Response(text=json.dumps(dict(action=action, question=question, context=context, summary=summary)),
                    thread_id=thread, usage=usage or {})


@pytest.fixture
def task(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "code.py").write_text("value = 1\n")
    return {"task_id": "repair-1", "workspace": str(workspace),
            "prompt": "Repair the value conversion and execute its tests.",
            "memory": [{"id": "constraint-1", "text": "Preserve backwards-compatible public names."}],
            "allowed_paths": ["code.py"]}


def test_personal_resumes_actor_after_context_bounded_expert(task, tmp_path):
    backend = ScriptedBackend(
        reply("ask_expert", question="Which conversion preserves None?", context="def f(x): return int(x)",
              summary="I inspected the function."),
        Response(text=json.dumps({"action": "answer", "message": "Check for None first; run the regression test."}), thread_id="expert"),
        reply(summary="Applied the guarded conversion and ran tests."),
    )
    result = run_task(task, tmp_path / "run", condition="personal", backend=backend)
    assert result["status"] == "completed_ungraded"
    assert result["accepted"] is None
    assert result["expert_calls"] == 1
    assert [r.kind for r in backend.requests] == ["controller", "expert", "controller"]
    assert [r.model for r in backend.requests] == ["gpt-6-luna", "gpt-6.1-sol", "gpt-6-luna"]
    assert backend.requests[2].thread_id == "thread-small"
    assert backend.requests[1].read_only
    assert not backend.requests[2].read_only
    assert backend.requests[1].workspace != Path(task["workspace"])
    assert task["memory"][0]["text"] not in backend.requests[1].prompt
    assert "verify" in backend.requests[2].prompt.lower()
    assert result["cost_usd"] is None
    assert all(value is None for value in result["usage"].values())
    events = [json.loads(line) for line in (tmp_path / "run/events.jsonl").read_text().splitlines()]
    assert len(events) == 6
    assert [event["event"] for event in events] == ["request", "response"] * 3


@pytest.mark.parametrize("expert_action", ["request_context", "challenge"])
def test_two_way_conversation_keeps_both_threads_and_verifies(task, tmp_path, expert_action):
    backend = ScriptedBackend(
        reply("ask_expert", question="Should this helper accept None?", context="The annotation accepts int or None."),
        Response(text=json.dumps({"action": expert_action,
                                  "message": "Show the callers and expected behavior before changing the contract."}),
                 thread_id="expert-conversation"),
        reply("ask_expert", question="I checked callers; None means unset. Please revise your proposal.",
              context="caller.py preserves None; the existing regression expects None, not zero."),
        Response(text=json.dumps({"action": "answer", "message": "Preserve None and convert non-None values."}),
                 thread_id="expert-conversation"),
        reply(summary="Verified the guarded conversion with caller and regression tests."),
    )
    result = run_task(task, tmp_path / "run", condition="personal", backend=backend)
    assert result["status"] == "completed_ungraded"
    assert result["expert_calls"] == 2
    assert result["turns"] == 5
    assert [r.kind for r in backend.requests] == ["controller", "expert", "controller", "expert", "controller"]
    assert [r.thread_id for r in backend.requests] == [None, None, "thread-small", "expert-conversation", "thread-small"]
    assert expert_action in backend.requests[2].prompt
    assert "I checked callers" in backend.requests[3].prompt
    assert "verify" in backend.requests[4].prompt.lower()
    assert result["expert_thread_id"] == "expert-conversation"
    assert result["controller_thread_id"] == "thread-small"


def test_resumed_expert_cannot_silently_switch_conversation(task, tmp_path):
    backend = ScriptedBackend(
        reply("ask_expert", question="Help", context="Code"),
        Response(text=json.dumps({"action": "request_context", "message": "Show the caller"}), thread_id="expert-1"),
        reply("ask_expert", question="Here is the caller", context="Relevant caller"),
        Response(text=json.dumps({"action": "answer", "message": "Use a guard"}), thread_id="unexpected-new-thread"),
    )
    result = run_task(task, tmp_path / "run", condition="personal", backend=backend)
    assert result["status"] == "protocol_failed"
    assert result["expert_thread_id"] == "expert-1"


@pytest.mark.parametrize("resumed_thread", [None, "", " ", "unexpected-new-controller"])
def test_resumed_controller_requires_same_nonempty_thread(task, tmp_path, resumed_thread):
    backend = ScriptedBackend(
        reply("ask_expert", question="Help", context="Relevant code"),
        Response(text=json.dumps({"action": "answer", "message": "Preserve None with a guard."}),
                 thread_id="expert-1"),
        reply(summary="Claimed completion", thread=resumed_thread),
    )
    result = run_task(task, tmp_path / "run", condition="personal", backend=backend)
    assert backend.requests[2].thread_id == "thread-small"
    assert result["status"] == "protocol_failed"
    assert result["controller_thread_id"] == "thread-small"
    assert result["summary"] == ""


@pytest.mark.parametrize("initial_thread", [None, "", " "])
def test_initial_controller_requires_nonempty_thread(task, tmp_path, initial_thread):
    result = run_task(task, tmp_path / "run", condition="small",
                      backend=ScriptedBackend(reply(thread=initial_thread)))
    assert result["status"] == "protocol_failed"
    assert result["controller_thread_id"] is None


def test_solo_and_personal_receive_same_initial_memory(task, tmp_path):
    for condition in ("small", "large", "personal"):
        backend = ScriptedBackend(reply())
        run_task(task, tmp_path / condition, condition=condition, backend=backend)
        assert task["memory"][0]["text"] in backend.requests[0].prompt
        assert str(task["allowed_paths"][0]) in backend.requests[0].prompt


def test_pre_call_router_selects_before_attempt_and_counts_usage(task, tmp_path):
    usage = {name: 3 for name in USAGE_FIELDS}
    backend = ScriptedBackend(
        Response(text=json.dumps({"model": "large", "reason": "Cross-module ambiguity"}), usage=usage),
        reply(usage=usage),
    )
    result = run_task(task, tmp_path / "run", condition="precall_router", backend=backend)
    assert result["selected_model"] == "gpt-6.1-sol"
    assert result["turns"] == 2
    assert result["usage"] == {name: 6 for name in USAGE_FIELDS}
    assert backend.requests[0].kind == "router"
    assert backend.requests[0].read_only
    assert backend.requests[1].thread_id is None
    assert backend.requests[1].model == "gpt-6.1-sol"


def test_failed_attempt_is_retained_and_missing_usage_is_not_zero(task, tmp_path):
    backend = ScriptedBackend(Response(status="failed", error_type="provider_error",
                                      usage={"input_tokens": 20}, elapsed_seconds=1.5))
    result = run_task(task, tmp_path / "run", condition="small", backend=backend)
    assert result["status"] == "failed"
    assert result["turns"] == 1
    assert result["usage"]["input_tokens"] == 20
    assert result["usage"]["output_tokens"] is None
    assert result["elapsed_seconds"] == 1.5
    assert result["cost_usd"] is None
    assert len((tmp_path / "run/events.jsonl").read_text().splitlines()) == 2


def test_missing_usage_in_one_turn_keeps_total_null_but_retains_partial(task, tmp_path):
    backend = ScriptedBackend(
        Response(text=json.dumps({"model": "small", "reason": "routine"}), usage={"input_tokens": 10}),
        reply(),
    )
    result = run_task(task, tmp_path / "run", condition="precall_router", backend=backend)
    assert result["usage"]["input_tokens"] is None
    assert result["observed_usage_partial"]["input_tokens"] == 10


def test_completed_run_resume_does_not_repeat_model_calls(task, tmp_path):
    backend = ScriptedBackend(reply())
    original = run_task(task, tmp_path / "run", condition="small", backend=backend)
    resumed = run_task(task, tmp_path / "run", condition="small", backend=backend, resume=True)
    assert original == resumed
    assert len(backend.requests) == 1
    with pytest.raises(FileExistsError):
        run_task(task, tmp_path / "run", condition="small", backend=backend)


def test_changed_memory_cannot_silently_resume_existing_condition(task, tmp_path):
    run_task(task, tmp_path / "run", condition="small", backend=ScriptedBackend(reply()))
    task["memory"][0]["text"] = "A different preference"
    with pytest.raises(ValueError, match="changed"):
        run_task(task, tmp_path / "run", condition="small", resume=True)


def test_interrupted_inflight_turn_never_replays(task, tmp_path):
    def crash(request):
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        run_task(task, tmp_path / "run", condition="personal", backend=ScriptedBackend(crash))
    state = json.loads((tmp_path / "run/state.json").read_text())
    assert state["inflight"]["phase"] == "controller"
    with pytest.raises(RuntimeError, match="manual reconciliation"):
        run_task(task, tmp_path / "run", condition="personal", resume=True)


def test_turn_cap_does_not_launch_unfunded_extra_call(task, tmp_path):
    backend = ScriptedBackend(reply("ask_expert", question="Help?", context="Relevant code"))
    result = run_task(task, tmp_path / "run", condition="personal", max_turns=1, backend=backend)
    assert result["status"] == "budget_exhausted"
    assert result["failure_type"] == "turn_limit"
    assert len(backend.requests) == 1


def test_expert_cap_is_enforced(task, tmp_path):
    backend = ScriptedBackend(reply("ask_expert", question="Help?", context="Relevant code"))
    result = run_task(task, tmp_path / "run", condition="personal", max_expert_calls=0, backend=backend)
    assert result["status"] == "budget_exhausted"
    assert result["failure_type"] == "expert_limit"


@pytest.mark.parametrize("response", [
    reply("ask_expert", question="Help?", context="code", thread=None),
    reply("ask_expert", question="Help?", context=""),
    Response(text="not JSON"),
    Response(text=json.dumps({"action": "complete"})),
])
def test_invalid_protocol_fails_without_help_call(task, tmp_path, response):
    backend = ScriptedBackend(response)
    result = run_task(task, tmp_path / "run", condition="personal", backend=backend)
    assert result["status"] == "protocol_failed"
    assert len(backend.requests) == 1


def test_oversize_context_rejected_not_silently_truncated(task, tmp_path):
    backend = ScriptedBackend(reply("ask_expert", question="Help?", context="x" * 100))
    result = run_task(task, tmp_path / "run", condition="personal", backend=backend, max_context_characters=30)
    assert result["status"] == "protocol_failed"


def test_solo_cannot_obtain_unregistered_help(task, tmp_path):
    result = run_task(task, tmp_path / "run", condition="large",
                      backend=ScriptedBackend(reply("ask_expert", question="Help", context="Code")))
    assert result["status"] == "protocol_failed"


def test_parser_retains_usage_and_tool_failures_but_not_reasoning():
    events = [
        {"type": "thread.started", "thread_id": "abc"},
        {"type": "item.completed", "item": {"type": "reasoning", "text": "DO NOT STORE"}},
        {"type": "item.completed", "item": {"id": "c1", "type": "command_execution", "command": "pytest",
                                               "aggregated_output": "Sensitive test output", "status": "failed", "exit_code": 1}},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "final JSON here"}},
        {"type": "turn.completed", "usage": {"input_tokens": 31, "cached_input_tokens": 4, "output_tokens": 6}},
    ]
    response = parse_codex_events([json.dumps(event) for event in events])
    assert response.status == "completed"
    assert response.thread_id == "abc"
    assert response.text == "final JSON here"
    assert response.usage["input_tokens"] == 31
    assert response.usage["reasoning_output_tokens"] is None
    assert response.tool_events[0]["exit_code"] == 1
    assert "DO NOT STORE" not in repr(response)
    assert "Sensitive test output" not in repr(response)
    assert "command" not in response.tool_events[0]


@pytest.mark.parametrize("events,code,error", [
    (["garbage"], 0, "invalid_jsonl"),
    ([json.dumps({"type": "turn.started"})], 0, "turn_failed_or_incomplete"),
    ([], 1, "codex_exit"),
    ([json.dumps({"type": "turn.completed", "usage": {"input_tokens": -1}})], 0, "invalid_usage"),
])
def test_parser_distinguishes_transport_and_usage_failure(events, code, error):
    response = parse_codex_events(events, returncode=code)
    assert response.status == "failed"
    assert response.error_type == error


def test_codex_command_preserves_sandbox_and_resumes_exact_thread(tmp_path):
    request = Request("r1", "gpt-6-luna", "controller", "prompt", tmp_path,
                      ACTION_SCHEMA, 10, thread_id="known-thread")
    command = CodexBackend().command(request, tmp_path / "schema.json")
    assert command[-3:] == ["resume", "known-thread", "-"]
    assert command[command.index("--sandbox") + 1] == "workspace-write"
    assert "--ephemeral" not in command
    assert "--dangerously-bypass-approvals-and-sandbox" not in command


def test_codex_subprocess_timeout_stops_owned_process_group(tmp_path):
    fake = tmp_path / "fake-codex"
    fake.write_text("#!/usr/bin/env python3\nimport time\ntime.sleep(30)\n")
    fake.chmod(0o700)
    request = Request("r1", "model", "controller", "prompt", tmp_path, ACTION_SCHEMA, 0.1)
    start = time.monotonic()
    response = CodexBackend(str(fake)).complete(request)
    assert response.status == "timeout"
    assert response.error_type == "deadline"
    assert time.monotonic() - start < 5
    assert response.usage["input_tokens"] is None


def test_timeout_kills_child_even_when_parent_exits_on_term(tmp_path):
    fake = tmp_path / "fake-codex"
    child_pid = tmp_path / "child.pid"
    child_code = "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)"
    fake.write_text(
        "#!/usr/bin/env python3\nimport subprocess,sys,time\nfrom pathlib import Path\n"
        f"p=subprocess.Popen([sys.executable,'-c',{child_code!r}])\n"
        f"Path({str(child_pid)!r}).write_text(str(p.pid))\n"
        "time.sleep(30)\n"
    )
    fake.chmod(0o700)
    response = CodexBackend(str(fake)).complete(Request("r1", "model", "controller", "prompt",
                                                       tmp_path, ACTION_SCHEMA, 0.2))
    assert response.status == "timeout"
    pid = int(child_pid.read_text())
    try:
        # A terminated orphan can remain a zombie until the container's init
        # reaps it; it is no longer executing or consuming model resources.
        for _ in range(100):
            status_path = Path(f"/proc/{pid}/status")
            if not status_path.exists() or "\nState:\tZ" in status_path.read_text():
                break
            time.sleep(0.01)
        else:
            pytest.fail("Task-owned child remained live after the deadline")
    finally:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def test_codex_subprocess_accepts_documented_jsonl_protocol(tmp_path):
    fake = tmp_path / "fake-codex"
    final = json.dumps(dict(action="complete", question="", context="", summary="verified"))
    events = [
        {"type": "thread.started", "thread_id": "test-thread"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": final}},
        {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 3}},
    ]
    fake.write_text("#!/usr/bin/env python3\nimport sys\nsys.stdin.read()\n" +
                    "\n".join(f"print({json.dumps(json.dumps(event))})" for event in events) + "\n")
    fake.chmod(0o700)
    response = CodexBackend(str(fake)).complete(Request("r1", "model", "controller", "prompt",
                                                       tmp_path, ACTION_SCHEMA, 2))
    assert response.status == "completed"
    assert response.thread_id == "test-thread"
    assert response.usage["input_tokens"] == 10


def test_task_paths_cannot_escape_workspace(task):
    task["allowed_paths"] = ["../heldout-tests"]
    with pytest.raises(ValueError, match="escape"):
        validate_task(task)


def test_context_only_router_tool_use_invalidates_condition(task, tmp_path):
    backend = ScriptedBackend(Response(text=json.dumps({"model": "large", "reason": "peeked at code"}),
                                      tool_events=[{"type": "command_execution", "status": "completed"}]))
    result = run_task(task, tmp_path / "run", condition="precall_router", backend=backend)
    assert result["status"] == "failed"
    assert result["failure_type"] == "context_only_role_used_tools"
    assert len(backend.requests) == 1


def test_output_artifacts_cannot_be_created_inside_solver_workspace(task):
    with pytest.raises(ValueError, match="outside"):
        run_task(task, Path(task["workspace"]) / "results", condition="small")
