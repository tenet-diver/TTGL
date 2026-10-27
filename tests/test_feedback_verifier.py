import hashlib
import os
import subprocess

import pytest

from ttgl import feedback_verifier


def test_unknown_upstream_is_rejected():
    with pytest.raises(ValueError, match='Unreviewed'):
        feedback_verifier.strict_cpp_wrapper('unknown upstream', 'phone-number')


def test_target_cannot_inject_shell_commands(monkeypatch):
    snippet = 'echo "Building and running C++ tests..."\n'
    monkeypatch.setattr(feedback_verifier, 'UPSTREAM_CPP_SNIPPET_SHA256',
                        hashlib.sha256(snippet.encode()).hexdigest())
    with pytest.raises(ValueError, match='target'):
        feedback_verifier.strict_cpp_wrapper(snippet, 'exercise; echo injected')


@pytest.mark.parametrize('configure_exit,build_exit,test_exit,exists,expected', [
    (0, 0, 0, True, 0), (0, 0, 7, True, 7),
    (9, 0, 0, True, 9), (0, 11, 0, True, 11), (0, 0, 0, False, 1),
])
def test_shell_propagates_failures_and_requires_the_declared_test(
        tmp_path, monkeypatch, configure_exit, build_exit, test_exit, exists, expected):
    # Model-free process fixture: test the generated wrapper's observable exit
    # behavior, without compiling or changing any benchmark assertion.
    snippet = 'echo "Building and running C++ tests..."\n'
    monkeypatch.setattr(feedback_verifier, 'UPSTREAM_CPP_SNIPPET_SHA256',
                        hashlib.sha256(snippet.encode()).hexdigest())
    (tmp_path/'bin').mkdir()
    (tmp_path/'build').mkdir()
    cmake = tmp_path/'bin/cmake'
    cmake.write_text('#!/bin/sh\nif [ "$1" = "--build" ]; then\n'
                     f'exit {build_exit}\nfi\nexit {configure_exit}\n')
    cmake.chmod(0o755)
    if exists:
        executable = tmp_path/'build/phone-number'
        executable.write_text(f'#!/bin/sh\necho TEST_EXECUTED\nexit {test_exit}\n')
        executable.chmod(0o755)
    result = subprocess.run(['bash', '-c', feedback_verifier.strict_cpp_wrapper(snippet, 'phone-number')],
                            cwd=tmp_path, capture_output=True, text=True,
                            env={**os.environ, 'PATH': str(tmp_path/'bin')+':/usr/bin:/bin'}, timeout=10)
    assert result.returncode == expected
    assert ('TEST_EXECUTED' in result.stdout) == (configure_exit == build_exit == 0 and exists)
