"""Run selected upstream SlopCodeBench checks against an isolated entrypoint."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from ..experience_routing.io import file_digest, read, write_new

REVISION = "ba1f7fec544dae4ff274d2447d9b65aebfbc5196"
PROBLEMS = ("l2m", "cfgpipe")
PYTEST = Path("/usr/local/py-utils/venvs/pytest/bin/python")
USERNS = ["/usr/bin/unshare", "--user", "--map-root-user", "--net", "--",
          "/bin/sh", "-c", '/usr/sbin/ip link set lo up && exec "$@"', "grader"]


def qualified_files(upstream):
    receipt = read(upstream.parent / "security-receipt.json")
    if receipt["revision"] != REVISION or any(row.get("vulns") for row in receipt["osv"].get("results", [])):
        raise ValueError("Benchmark dependency review failed")
    for name, digest in receipt["files"].items():
        if file_digest(upstream / name) != digest:
            raise ValueError(f"Benchmark asset differs from its verified source: {name}")
    for problem in PROBLEMS:
        actual = {str(p.relative_to(upstream)) for p in (upstream / problem).rglob("*") if p.is_file()}
        if actual != {name for name in receipt["files"] if name.startswith(problem + "/")}:
            raise ValueError("Unexpected fixture, test or reference file")
    return receipt["files"]


def _entry():
    """Mount only this test's inputs and candidate, preserving upstream CLI paths."""
    case_root = Path(os.environ["SCB_FIXTURES"])
    submission = Path(os.environ["SCB_SUBMISSION"])
    current = Path.cwd()
    if os.readlink("/proc/self/ns/net") == os.environ["SCB_HOST_NETNS"]:
        raise RuntimeError("Verifier candidate requires the confined network namespace")
    cases = set()
    for value in (*sys.argv[1:], str(current)):
        for token in value.split("=", 1):
            if token.startswith(str(case_root) + "/"):
                relative = Path(token).relative_to(case_root)
                cases.add(case_root / relative.parts[0])
    if len(cases) > 1 or any(p.is_symlink() or not p.is_dir() for p in cases):
        raise RuntimeError("Input paths must belong to one isolated test case")
    workspace = next(iter(cases), None)
    command = ["/usr/bin/bwrap", "--unshare-user", "--unshare-ipc", "--unshare-pid",
               "--unshare-uts", "--disable-userns", "--die-with-parent", "--clearenv",
               "--ro-bind", "/usr/bin", "/usr/bin", "--ro-bind", "/usr/lib", "/usr/lib",
               "--ro-bind", "/usr/lib64", "/usr/lib64", "--symlink", "usr/bin", "/bin",
               "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64",
               "--proc", "/proc", "--dev", "/dev", "--size", "16777216", "--tmpfs", "/tmp",
               "--ro-bind", str(submission), "/submission.py",
               "--setenv", "PATH", "/usr/bin:/bin", "--setenv", "HOME", "/tmp",
               "--setenv", "LC_ALL", "C", "--setenv", "PYTHONDONTWRITEBYTECODE", "1"]
    if workspace:
        command += ["--bind", str(workspace), str(workspace)]
    command += ["--chdir", str(current if workspace and current.is_relative_to(workspace) else "/tmp")]
    for key, value in os.environ.items():
        if key in {"LISTEN_PORT", "NEG_PORT", "BAD_PORT"} or key.startswith(("CFG", "APP_", "TEST_", "MY_", "ENV_", "SERVICE_", "PRIMARY_", "SECONDARY_")):
            command += ["--setenv", key, value]
    command += ["--", "/usr/bin/prlimit", "--core=0", "--as=1073741824",
                "--fsize=1048576", "--nofile=128", "--nproc=512", "--cpu=10", "--",
                "/usr/bin/python3", "-I", "-B", "/submission.py", *sys.argv[1:]]
    os.execv(command[0], command)


def grade(upstream, problem, checkpoints, candidate, output=None):
    if problem not in PROBLEMS or not checkpoints or any(i not in (1, 2, 3) for i in checkpoints):
        raise ValueError("Unknown checkpoint")
    if output and (output / "grade.json").exists():
        existing = read(output / "grade.json")
        from ..experience_routing.io import digest
        if existing["candidate_sha256"] != digest(candidate.encode()):
            raise ValueError("Registered candidate changed")
        return existing
    with tempfile.TemporaryDirectory(prefix="observatory-scb-grade-") as folder:
        root = Path(folder)
        source = root / "candidate.py"
        source.write_text(candidate, encoding="utf8")
        environment = {"PATH": "/usr/bin:/bin", "HOME": folder, "LC_ALL": "C.UTF-8",
                       "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONDONTWRITEBYTECODE": "1",
                       "PYTHONPATH": str(Path(__file__).resolve().parents[2]),
                       "SCB_SUBMISSION": str(source), "SCB_FIXTURES": str(root / "fixtures"),
                       "SCB_HOST_NETNS": os.readlink("/proc/self/ns/net")}
        tests = upstream / problem / "tests"
        xml = root / "junit.xml"
        result = subprocess.run([*USERNS, str(PYTEST), "-m", "pytest", "-q", "--tb=short",
                                 "--basetemp", str(root / "fixtures"), "--junitxml", str(xml),
                                 "--entrypoint", shlex.join([str(PYTEST), "-m", "ttgl.decision_history.grade"]),
                                 "--checkpoint", f"checkpoint_{max(checkpoints)}",
                                 *(str(tests / f"test_checkpoint_{i}.py") for i in checkpoints)],
                                cwd=root, env=environment, capture_output=True, timeout=85)
        if output:
            output.mkdir(parents=True, exist_ok=True)
            (output / "pytest.log").write_bytes(result.stdout + result.stderr)
        if not xml.exists() or result.returncode not in (0, 1):
            raise RuntimeError(f"Independent grader failed for {problem} {checkpoints}")
        cases = list(ET.parse(xml).getroot().iter("testcase"))
        failed = [x.attrib["classname"] + "::" + x.attrib["name"] for x in cases
                  if x.find("failure") is not None or x.find("error") is not None]
        skipped = sum(x.find("skipped") is not None for x in cases)
        if not cases or skipped:
            raise RuntimeError(f"Unexpected missing or skipped checks for {problem} {checkpoints}")
        receipt = {"problem": problem, "checkpoints": list(checkpoints), "candidate_sha256": file_digest(source),
                   "checks": len(cases), "passed": len(cases) - len(failed), "failed": failed,
                   "solved": not failed}
        if output:
            write_new(output / "grade.json", receipt)
        return receipt


if __name__ == "__main__":
    _entry()
