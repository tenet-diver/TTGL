"""Pinned SWE-bench dependency containers for development workers.

The existing Codex agent still runs on its normal host. This helper gives it a
per-assignment Python/test environment; it does not claim to isolate Codex's host
reads or grant Codex access to the Docker socket. No model or credential enters
the container. Official evaluation remains independent.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time
from typing import Callable


DOCKER_SOCKET = "unix:///var/run/docker.sock"
LABEL = "org.ttgl.worker-owner"
IMAGE = re.compile(r"(?:docker\.io/)?swebench/sweb\.eval\.[a-zA-Z0-9_.-]+@sha256:[0-9a-f]{64}")
PYTHON = "/opt/miniconda3/envs/testbed/bin/python"


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def validate_config(config: dict, task_ids: list[str]) -> dict:
    """Require pinned images and a real public probe for every assigned task."""
    if (not isinstance(config, dict) or config.get("schema_version") != 1
            or config.get("mode") != "official_image_development_tools"
            or not isinstance(config.get("tasks"), dict)):
        raise ValueError("Expected version-1 official_image_development_tools configuration")
    if set(config["tasks"]) != set(task_ids):
        raise ValueError("Worker configuration must cover exactly the frozen task IDs")
    for task_id, entry in config["tasks"].items():
        if not isinstance(entry, dict) or set(entry) != {"image", "probe_argv", "probe_timeout_seconds"}:
            raise ValueError(f"Unexpected worker fields for {task_id}")
        if not isinstance(entry["image"], str) or not IMAGE.fullmatch(entry["image"]):
            raise ValueError("Official SWE-bench image must be pinned by repository SHA-256 digest")
        argv = entry["probe_argv"]
        if (not isinstance(argv, list) or len(argv) < 3 or argv[0] != PYTHON
                or argv[1] not in ("-c", "-m")
                or any(not isinstance(x, str) or not x or "\0" in x for x in argv)):
            raise ValueError("Probe must use the image's explicit testbed Python and nonempty argv")
        timeout = entry["probe_timeout_seconds"]
        if type(timeout) is not int or not 1 <= timeout <= 600:
            raise ValueError("Public dependency probe requires a bounded 1..600 second timeout")
    return config


def _git(path: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True,
                            text=True, timeout=30)
    if result.returncode:
        raise RuntimeError("Worker Git identity check failed")
    return result.stdout.strip()


def _checkout_state(path: Path) -> str:
    untracked = {}
    for relative in _git(path, "ls-files", "--others", "--exclude-standard", "-z").split("\0"):
        if not relative:
            continue
        file = path / relative
        if file.is_symlink():
            untracked[relative] = {"symlink": os.readlink(file)}
        elif file.is_file():
            untracked[relative] = hashlib.sha256(file.read_bytes()).hexdigest()
        else:
            raise ValueError("Unexpected untracked filesystem object in worker")
    return digest({"head": _git(path, "rev-parse", "HEAD"),
                   "diff": _git(path, "diff", "--binary", "--no-ext-diff", "HEAD", "--", "."),
                   "untracked": untracked})


class ToolContainer:
    """One task-owned, network-disabled dependency container; never auto-pulls."""

    def __init__(self, workspace: Path, task: dict, config_entry: dict, run_id: str,
                 *, execute: Callable = subprocess.run, allow_dirty: bool = False):
        self.workspace = Path(workspace).resolve(strict=True)
        if not self.workspace.is_dir() or any(x in str(self.workspace) for x in (",", "\n", "\0")):
            raise ValueError("Invalid bind-mount workspace")
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("Assignment run ID is required")
        if not re.fullmatch(r"[0-9a-f]{40}", task.get("base_commit", "")):
            raise ValueError("Task requires exact base commit")
        self.task = task
        self.entry = validate_config({"schema_version": 1,
            "mode": "official_image_development_tools", "tasks": {task["instance_id"]: config_entry}},
            [task["instance_id"]])["tasks"][task["instance_id"]]
        self.owner = digest({"run_id": run_id, "workspace": str(self.workspace),
                             "task_id": task["instance_id"], "entry": self.entry})
        self.name = "ttgl-worker-" + self.owner[:24]
        self.execute = execute
        self.allow_dirty = allow_dirty
        self.container_id = None
        self.image_id = None
        self.started = False

    def _docker(self, args: list[str], *, timeout: int = 30, check: bool = True):
        # Explicit local daemon per cloud-runtime skill. Registry configuration
        # and inherited HTTP(S) proxy/CA variables are otherwise untouched.
        environment = os.environ.copy()
        for key in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"):
            environment.pop(key, None)
        try:
            result = self.execute(["docker", "--host=" + DOCKER_SOCKET, *args],
                                  env=environment, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise RuntimeError("Worker Docker command timed out; reconcile task-owned container") from None
        if check and result.returncode:
            # Docker diagnostics may contain registry/account data. Retain only
            # a fixed classification; callers must not publish arbitrary stderr.
            raise RuntimeError(f"Worker Docker {args[0]} failed (exit {result.returncode})")
        return result

    def start(self) -> "ToolContainer":
        if self.started or self.container_id:
            raise RuntimeError("Worker container is already started")
        if _git(self.workspace, "rev-parse", "HEAD") != self.task["base_commit"]:
            raise ValueError("Worker checkout does not match task base")
        if not self.allow_dirty and _git(self.workspace, "status", "--porcelain"):
            raise ValueError("Initial worker checkout must be clean")
        self.image_id = self._docker(["image", "inspect", "--format", "{{.Id}}",
                                     self.entry["image"]]).stdout.strip()
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", self.image_id):
            raise RuntimeError("Invalid local image identity")
        # No automatic image pull: upstream images are large and must be
        # explicitly acquired/control-checked before this helper is invoked.
        created = self._docker([
            "create", "--name", self.name, "--label", f"{LABEL}={self.owner}",
            "--network", "none", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--pids-limit", "512", "--memory", "4g", "--cpus", "2",
            "--user", f"{os.getuid()}:{os.getgid()}", "--workdir", "/testbed",
            "--mount", f"type=bind,src={self.workspace},dst=/testbed",
            "--entrypoint", "/bin/sleep", self.entry["image"], "infinity",
        ])
        self.container_id = created.stdout.strip()
        if not re.fullmatch(r"[0-9a-f]{64}", self.container_id):
            raise RuntimeError("Invalid created container ID; reconcile by its recorded owner label")
        try:
            self._docker(["start", self.container_id])
            self.started = True
        except BaseException:
            self.stop()
            raise
        return self

    def probe(self) -> dict:
        if not self.started:
            raise RuntimeError("Start the dependency container before probing")
        before = _checkout_state(self.workspace)
        started = time.monotonic()
        result = self._docker(["exec", "--workdir", "/testbed", self.container_id,
                               *self.entry["probe_argv"]],
                              timeout=self.entry["probe_timeout_seconds"], check=False)
        unchanged = (_checkout_state(self.workspace) == before
                     and _git(self.workspace, "rev-parse", "HEAD") == self.task["base_commit"])
        report = {
            "schema_version": 1, "scope": "dependency_environment_only",
            "task_id": self.task["instance_id"], "base_commit": self.task["base_commit"],
            "workspace": str(self.workspace), "config_sha256": digest(self.entry),
            "image": self.entry["image"], "image_id": self.image_id,
            "container_id": self.container_id, "owner": self.owner,
            "probe_argv": self.entry["probe_argv"], "probe_exit_code": result.returncode,
            "probe_stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
            "probe_stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
            "elapsed_seconds": time.monotonic() - started,
            "checkout_unchanged": unchanged,
            "dependency_ready": result.returncode == 0 and unchanged,
            "controller_docker_access_verified": False,
            "host_read_isolation_verified": False,
            "confirmatory_study_ready": False,
            "limits": ["Only the configured public dependency probe ran; no full test-suite guarantee",
                       "Codex host read isolation and access to this Docker socket are separate checks",
                       "The network-disabled tool container is not a model endpoint or evaluator"],
        }
        return report

    def instructions(self) -> str:
        if not self.started:
            raise RuntimeError("Worker container must be running")
        # The prompt must remain byte-stable across a safe resume: a newly
        # created container has a different ID but the same owned name.
        prefix = ["docker", "--host=" + DOCKER_SOCKET, "exec", "--workdir", "/testbed", self.name]
        return ("Project dependencies are installed in a task-owned container. Source edits in "
                "your workspace are shared at /testbed. Run project Python commands with "
                + shlex.join(prefix + [PYTHON]) +
                " followed by the Python arguments. Do not use host Python for repository checks. "
                "Container networking is disabled. Report access/dependency failures; do not "
                "change the sandbox, proxy, Docker daemon or container configuration.")

    def stop(self) -> None:
        if not self.container_id:
            return
        owned = self._docker(["inspect", "--format", '{{ index .Config.Labels "' + LABEL + '" }}',
                              self.container_id], check=False)
        if owned.returncode or owned.stdout.strip() != self.owner:
            raise RuntimeError("Refusing cleanup: cannot verify task-owned container label")
        self._docker(["rm", "--force", self.container_id], timeout=30)
        self.started = False
        self.container_id = None

    def __enter__(self):
        return self.start()

    def __exit__(self, *_):
        self.stop()


def assert_dependency_ready(report: dict, task: dict, workspace: Path, config_entry: dict) -> None:
    """Gate model work on an attributable passing probe, without claiming isolation."""
    expected = {"scope": "dependency_environment_only", "task_id": task["instance_id"],
                "base_commit": task["base_commit"], "workspace": str(Path(workspace).resolve()),
                "config_sha256": digest(config_entry), "image": config_entry["image"],
                "probe_exit_code": 0, "checkout_unchanged": True, "dependency_ready": True}
    if any(report.get(key) != value for key, value in expected.items()):
        raise ValueError("Worker dependency readiness is absent, failed, or bound to different inputs")
    if report.get("confirmatory_study_ready") is not False:
        raise ValueError("A dependency probe cannot certify confirmatory isolation readiness")
