"""Independent checks for the Observatory Python repair pilot.

The actor receives exactly the files in ``Task.public_files()``. The grader
sends arguments to a candidate-only sandbox and compares answers on the host.
"""

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from textwrap import dedent
from typing import Any

from .benchmark_tasks import specifications


VERSION = "observatory-python-repair-001"


@dataclass(frozen=True)
class Task:
    id: str
    split: str
    title: str
    prompt: str
    function: str
    starter: str
    public_tests: str
    hidden_tests: tuple[tuple[list[Any], Any], ...]
    reference: str
    requires_detached_result: bool = False

    def public_files(self) -> dict[str, str]:
        return {"README.md": f"# {self.title}\n\n{self.prompt}\n",
                "solution.py": self.starter, "test_public.py": self.public_tests}

    @property
    def fingerprint(self) -> str:
        data = json.dumps(asdict(self), sort_keys=True, ensure_ascii=False).encode()
        return sha256(data).hexdigest()


@dataclass(frozen=True)
class Grade:
    passed: bool
    passed_checks: int
    total_checks: int
    failure: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _code(source: str) -> str:
    return dedent(source).strip() + "\n"


def load_tasks() -> dict[str, Task]:
    """Return a fresh task set in the registered order."""
    tasks = {}
    for identity, split, title, function, prompt, starter, reference, examples, checks in specifications():
        test_lines = ["import unittest", f"from solution import {function}", "",
                      "class PublicChecks(unittest.TestCase):", "    def test_examples(self):"]
        for arguments, expected in examples:
            call = ", ".join(repr(value) for value in arguments)
            test_lines.append(f"        self.assertEqual({function}({call}), {expected!r})")
        public_tests = "\n".join(test_lines) + "\n"
        public_prompt = _code(prompt).strip() + (
            "\n\nRepair `solution.py` using the standard library. Keep the public function "
            "signature and leave arguments unchanged. Public examples run with "
            "`python3 -m unittest -q test_public`."
        )
        if (identity in tasks or not checks
                or {_encoded(args) for args, _ in examples} & {_encoded(args) for args, _ in checks}):
            raise ValueError(f"Invalid benchmark specification for {identity}")
        tasks[identity] = Task(identity, split, title, public_prompt, function, _code(starter),
                               public_tests, tuple(checks), _code(reference),
                               requires_detached_result=identity == "overlay-bundles")
    return tasks


_WORKER = """\
import copy
import contextlib
import importlib.util
import json
import sys


def json_value(value):
    if value is None or type(value) in (str, bool, int, float):
        return True
    if type(value) is list:
        return all(json_value(item) for item in value)
    if type(value) is dict:
        return all(type(key) is str and json_value(item) for key, item in value.items())
    return False


def mutable_ids(value):
    if type(value) is list:
        return {id(value)}.union(*(mutable_ids(item) for item in value))
    if type(value) is dict:
        return {id(value)}.union(*(mutable_ids(item) for item in value.values()))
    return set()


def run(function, arguments, detached):
    original = copy.deepcopy(arguments)
    try:
        answer = function(*arguments)
        unchanged = json.dumps(arguments, sort_keys=True) == json.dumps(original, sort_keys=True)
        if unchanged and json_value(answer) and (
            not detached or not (mutable_ids(arguments) & mutable_ids(answer))
        ):
            return [True, answer]
    except Exception:
        pass
    return [False, None]


name, cases, detached = json.load(sys.stdin)
spec = importlib.util.spec_from_file_location('solution', '/testbed/solution.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
with open('/dev/null', 'w') as discard, contextlib.redirect_stdout(discard):
    spec.loader.exec_module(module)
    function = getattr(module, name)
    answers = [run(function, arguments, detached) for arguments in cases]
print(json.dumps(answers, allow_nan=False))
"""


def _encoded(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)


def evaluate(task: Task, candidate: str, *, timeout: float = 5) -> Grade:
    """Grade an isolated candidate, retaining only counts and a broad failure cause."""
    from .runtime import run_sandbox

    total = len(task.hidden_tests)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Evaluation timeout must be finite and positive")
    if len(candidate.encode()) > 128 * 1024:
        return Grade(False, 0, total, "candidate exceeds source size limit")
    payload = _encoded([task.function, [args for args, _ in task.hidden_tests],
                        task.requires_detached_result])
    with TemporaryDirectory(prefix="observatory-sim-grade-") as directory:
        workspace = Path(directory)
        (workspace / "solution.py").write_text(candidate, encoding="utf-8")
        try:
            process = run_sandbox(workspace, ["/usr/bin/python3", "-I", "-B", "-c", _WORKER],
                                  timeout=timeout, read_only=True, input_data=payload.encode())
        except subprocess.TimeoutExpired:
            return Grade(False, 0, total, "evaluation timeout")
    if process.returncode:
        return Grade(False, 0, total, "candidate execution failed")
    try:
        answers = json.loads(process.stdout)
        if not isinstance(answers, list) or len(answers) != total:
            raise ValueError("unexpected answer count")
        passed = sum(
            isinstance(answer, list) and len(answer) == 2 and answer[0] is True
            and _encoded(answer[1]) == _encoded(expected)
            for answer, (_, expected) in zip(answers, task.hidden_tests)
        )
    except (UnicodeError, ValueError, TypeError, OverflowError):
        return Grade(False, 0, total, "candidate returned unreadable results")
    return Grade(passed == total, passed, total, None if passed == total else "behavior mismatch")


def qualify(tasks: dict[str, Task]) -> dict[str, dict[str, Any]]:
    """Run and validate an empty-patch and a known-good control for every task."""
    from .runtime import qualify_sandbox

    with TemporaryDirectory(prefix="observatory-sim-boundary-") as directory:
        qualify_sandbox(Path(directory))
    controls = {}
    for identity, task in tasks.items():
        empty_patch = evaluate(task, task.starter)
        reference = evaluate(task, task.reference)
        if empty_patch.passed or not reference.passed:
            raise RuntimeError(f"Benchmark controls failed for {identity}")
        controls[identity] = {"fingerprint": task.fingerprint,
                              "empty_patch": empty_patch.to_dict(),
                              "reference": reference.to_dict()}
    return controls
