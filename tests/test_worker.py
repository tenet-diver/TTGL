"""Dependency-container validation; fake Docker is not model evidence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

import pytest

from ttgl.worker import ToolContainer, assert_dependency_ready, validate_config, LABEL, PYTHON


IMAGE = "swebench/sweb.eval.x86_64.example_1776_project-1@sha256:" + "a" * 64
ID = "c" * 64


def config():
    return {"schema_version": 1, "mode": "official_image_development_tools", "tasks": {
        "example__project-1": {"image": IMAGE,
            "probe_argv": [PYTHON, "-c", "import package"], "probe_timeout_seconds": 30}}}


@pytest.fixture
def worker_task(tmp_path):
    workspace = tmp_path / "worker"
    workspace.mkdir()
    for command in (["init", "--quiet"], ["config", "user.name", "Fixture"],
                    ["config", "user.email", "fixture@example.invalid"]):
        subprocess.run(["git", "-C", str(workspace), *command], check=True)
    (workspace / "code.py").write_text("value = 1\n")
    subprocess.run(["git", "-C", str(workspace), "add", "."], check=True)
    subprocess.run(["git", "-C", str(workspace), "commit", "--quiet", "-m", "base"], check=True)
    base = subprocess.check_output(["git", "-C", str(workspace), "rev-parse", "HEAD"], text=True).strip()
    task = {"instance_id": "example__project-1", "base_commit": base}
    return workspace, task


class DockerFixture:
    def __init__(self, probe_exit=0, modify=None):
        self.calls = []
        self.owner = None
        self.probe_exit = probe_exit
        self.modify = modify

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        assert argv[:2] == ["docker", "--host=unix:///var/run/docker.sock"]
        command = argv[2]
        stdout, code = "", 0
        if command == "image":
            stdout = "sha256:" + "b" * 64
        elif command == "create":
            self.owner = argv[argv.index("--label") + 1].split("=", 1)[1]
            stdout = ID
        elif command == "exec":
            code = self.probe_exit
            if self.modify:
                self.modify()
            stdout = "public probe result"
        elif command == "inspect":
            stdout = self.owner
        return subprocess.CompletedProcess(argv, code, stdout + "\n", "")


def test_config_requires_complete_tasks_pinned_image_and_explicit_python():
    good = config()
    validate_config(good, ["example__project-1"])
    with pytest.raises(ValueError, match="exactly"):
        validate_config(good, ["example__project-1", "missing-2"])
    good["tasks"]["example__project-1"]["image"] = "swebench/example:latest"
    with pytest.raises(ValueError, match="pinned"):
        validate_config(good, ["example__project-1"])
    good = config()
    good["tasks"]["example__project-1"]["probe_argv"][0] = "python"
    with pytest.raises(ValueError, match="explicit"):
        validate_config(good, ["example__project-1"])


def test_successful_probe_is_scoped_and_container_is_cleaned(worker_task, monkeypatch):
    workspace, task = worker_task
    backend = DockerFixture()
    monkeypatch.setenv("DOCKER_HOST", "tcp://unintended.example:2375")
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example:8080")
    entry = config()["tasks"][task["instance_id"]]
    with ToolContainer(workspace, task, entry, "study/task/arm", execute=backend) as worker:
        report = worker.probe()
        assert_dependency_ready(report, task, workspace, entry)
        assert report["dependency_ready"] is True
        assert report["confirmatory_study_ready"] is False
        assert report["controller_docker_access_verified"] is False
        assert report["host_read_isolation_verified"] is False
        assert worker.name in worker.instructions() and PYTHON in worker.instructions()
        assert ID not in worker.instructions()
        assert "public probe result" not in json.dumps(report)
    assert [args[0][2] for args in backend.calls] == ["image", "create", "start", "exec", "inspect", "rm"]
    create = backend.calls[1][0]
    assert create[create.index("--network") + 1] == "none"
    assert create[create.index("--cap-drop") + 1] == "ALL"
    assert create.count("--mount") == 1
    assert str(workspace) in create[create.index("--mount") + 1]
    assert all("DOCKER_HOST" not in kwargs["env"] for _, kwargs in backend.calls)
    assert all(kwargs["env"]["HTTPS_PROXY"] == "http://proxy.example:8080" for _, kwargs in backend.calls)


def test_failed_probe_never_establishes_dependency_readiness(worker_task):
    workspace, task = worker_task
    entry = config()["tasks"][task["instance_id"]]
    with ToolContainer(workspace, task, entry, "run", execute=DockerFixture(1)) as worker:
        report = worker.probe()
        assert report["dependency_ready"] is False
        with pytest.raises(ValueError, match="readiness"):
            assert_dependency_ready(report, task, workspace, entry)


def test_probe_cannot_silently_modify_an_already_dirty_file(worker_task):
    workspace, task = worker_task
    (workspace / "code.py").write_text("value = 2\n")
    backend = DockerFixture(modify=lambda: (workspace / "code.py").write_text("value = 3\n"))
    entry = config()["tasks"][task["instance_id"]]
    with ToolContainer(workspace, task, entry, "resume", execute=backend, allow_dirty=True) as worker:
        report = worker.probe()
        assert report["checkout_unchanged"] is False
        assert report["dependency_ready"] is False
    assert (workspace / "code.py").read_text() == "value = 3\n"  # Preserve evidence, never reset.


def test_initial_dirty_worker_rejected_before_docker_and_cleanup_checks_owner(worker_task):
    workspace, task = worker_task
    entry = config()["tasks"][task["instance_id"]]
    (workspace / "untracked.py").write_text("uncertain state")
    backend = DockerFixture()
    worker = ToolContainer(workspace, task, entry, "run", execute=backend)
    with pytest.raises(ValueError, match="clean"):
        worker.start()
    assert not backend.calls
    (workspace / "untracked.py").unlink()
    worker.start()
    backend.owner = "someone-else"
    with pytest.raises(RuntimeError, match="Refusing cleanup"):
        worker.stop()
    assert backend.calls[-1][0][2] == "inspect"
    backend.owner = worker.owner
    worker.stop()


def test_readiness_cannot_be_transferred_to_other_task_or_configuration(worker_task):
    workspace, task = worker_task
    entry = config()["tasks"][task["instance_id"]]
    with ToolContainer(workspace, task, entry, "run", execute=DockerFixture()) as worker:
        report = worker.probe()
        with pytest.raises(ValueError, match="different inputs"):
            assert_dependency_ready(report, {**task, "instance_id": "other-2"}, workspace, entry)
        with pytest.raises(ValueError, match="different inputs"):
            assert_dependency_ready(report, task, workspace, {**entry, "probe_timeout_seconds": 60})
        report["confirmatory_study_ready"] = True
        with pytest.raises(ValueError, match="cannot certify"):
            assert_dependency_ready(report, task, workspace, entry)
