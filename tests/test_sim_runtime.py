"""Docker-free actor boundaries and fail-closed native admission."""
import json
from pathlib import Path
import shutil
import time

import pytest

from ttgl.experience_routing.io import read, write_new
from ttgl.personal import Response
from ttgl.sim_ablation import runtime


PUBLIC = {"README.md": "Public task specification\n", "solution.py": "value = 0\n"}
SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"}},
    "required": ["summary"],
    "additionalProperties": False,
}


class ReceiptArchive:
    def __init__(self):
        self.receipts = []

    def retain_file(self, path, *, kind, identity):
        self.receipts.append((kind, identity, Path(path).read_bytes()))
        return {"kind": kind}


@pytest.fixture
def runner(tmp_path, monkeypatch):
    cli = tmp_path / "codex"
    cli.write_text("#!/bin/sh\nprintf 'test-only-cli\\n'\n")
    cli.chmod(0o700)
    monkeypatch.setattr(runtime.shutil, "which", lambda name: str(cli))
    source = tmp_path / "source"
    source.mkdir()
    write_new(source / "auth.json", {
        "auth_mode": "chatgpt",
        "tokens": {"account_id": "test-account", "access_token": "test-only", "refresh_token": "test-only"},
    })
    return runtime.NativeRuntime(tmp_path, tmp_path / "results", source_home=source, retention=ReceiptArchive())


@pytest.mark.skipif(shutil.which("bwrap") is None, reason="Bubblewrap is needed for native actor execution")
def test_actor_read_only_public_files_and_no_host_access(tmp_path):
    worktree, parent = runtime._worktree(tmp_path, PUBLIC)
    runtime.qualify_sandbox(worktree)
    witness = tmp_path / "unmounted.txt"
    witness.write_text("unmounted evidence")
    result = runtime.run_sandbox(
        worktree, ["/bin/sh", "-c",
                   f'test ! -e "{witness}" && test ! -s .git && '
                   'if printf changed > README.md; then exit 2; fi; '
                   "printf 'value = 1\\n' > solution.py"],
        timeout=10, protected=[".git", "README.md"],
    )
    assert result.returncode == 0, result.stderr
    assert len(parent) == 40
    candidate, intact, diff = runtime._candidate(worktree, PUBLIC, "solution.py")
    assert intact and candidate == "value = 1\n" and "+value = 1" in diff
    (worktree / "solution.py").unlink()
    (worktree / "solution.py").symlink_to(witness)
    assert runtime._candidate(worktree, PUBLIC, "solution.py") == (None, False, None)


@pytest.mark.skipif(shutil.which("bwrap") is None, reason="Bubblewrap is needed for native actor execution")
def test_actor_idempotence_and_changed_command_rejected(tmp_path):
    worktree, _ = runtime._worktree(tmp_path, PUBLIC)
    spool = tmp_path / "spool"
    config = {
        "workspace": str(worktree), "spool": str(spool),
        "protected": [".git", "README.md"], "deadline": time.monotonic() + 15,
    }
    args = {"command": "printf '# once\\n' >> solution.py"}
    first = runtime._actor_command(config, 7, args)
    assert first["exit_code"] == 0
    assert runtime._actor_command(config, 7, args) == first
    assert (worktree / "solution.py").read_text().count("# once") == 1
    with pytest.raises(ValueError, match="Conflicting"):
        runtime._actor_command(config, 7, {"command": "exit 7"})
    assert len(list(spool.glob("*/started.json"))) == 1


def test_exact_completed_receipt_reused_and_changed_input_rejected(runner, monkeypatch):
    calls = []

    def complete(backend, request):
        calls.append(request.request_id)
        home = backend.output / request.request_id
        home.mkdir(parents=True)
        (home / "prompt.txt").write_text(request.prompt)
        artifact = home / "events.jsonl"
        artifact.write_text('{"event":"fixture"}\n')
        backend.last_native_artifact_hash = runtime.file_digest(artifact)
        backend.artifacts["events.jsonl"] = {"kind": "test-only"}
        return Response(text='{"summary":"ok"}', thread_id="fixture-thread", usage_scope="turn",
                        usage={"input_tokens": 30, "cached_input_tokens": 11, "output_tokens": 4,
                               "reasoning_output_tokens": 0, "cache_write_input_tokens": 0, "total_tokens": 34})

    monkeypatch.setattr(runtime._SandboxSubscriptionBackend, "complete", complete)
    result = runner.invoke("once", prompt="Prompt", schema=SCHEMA)
    assert result["answer"] == {"summary": "ok"}
    assert result["usage"]["total_tokens"] == 34
    assert result["first_request_input_tokens"] is None
    assert runner.invoke("once", prompt="Prompt", schema=SCHEMA) == result
    with pytest.raises(ValueError, match="identity changed"):
        runner.invoke("once", prompt="Changed prompt", schema=SCHEMA)
    assert calls == ["once"]
    assert any(kind == "sim-parsed-response" for kind, _, _ in runner.retention.receipts)


def test_resumes_only_before_admission(runner, monkeypatch):
    calls = []

    def uncertain(backend, request):
        calls.append(request.request_id)
        raise OSError("cut during request")

    retain = runner.retention.retain_file

    def unavailable(*args, **kwargs):
        raise OSError("archive unavailable before admission")

    runner.retention.retain_file = unavailable
    monkeypatch.setattr(runtime._SandboxSubscriptionBackend, "complete", uncertain)
    with pytest.raises(OSError, match="before admission"):
        runner.invoke("once", prompt="Prompt", schema=SCHEMA)
    slot = runner.output / "invocations" / "once"
    assert read(slot / "pending.json")["call_id"] == "once"
    assert not (slot / "started.json").exists()
    runner.retention.retain_file = retain
    with pytest.raises(OSError, match="cut during request"):
        runner.invoke("once", prompt="Prompt", schema=SCHEMA)
    assert (slot / "started.json").is_file()
    with pytest.raises(runtime.AmbiguousInvocation, match="no terminal receipt"):
        runner.invoke("once", prompt="Prompt", schema=SCHEMA)
    assert calls == ["once"]


def test_first_native_provider_input_is_thread_scoped(tmp_path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    rows = [
        {"type": "event_msg", "payload": {"type": "token_count"}},
        {"type": "token_usage_record", "payload": {
            "thread_id": "other", "response_id": "response0", "usage": {"input_tokens": 100}
        }},
        {"type": "token_usage_record", "payload": {
            "thread_id": "root", "response_id": "response1", "usage": {"input_tokens": 190}
        }},
        {"type": "token_usage_record", "payload": {
            "thread_id": "root", "response_id": "response2", "usage": {"input_tokens": 290}
        }},
    ]
    (sessions / "first.jsonl").write_text("\n".join(json.dumps(row) for row in rows))
    assert runtime._first_input_tokens(tmp_path, "root") == 190
    assert runtime._first_input_tokens(tmp_path, "unknown") is None
