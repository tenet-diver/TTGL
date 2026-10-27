"""Narrow, audited adaptations to the maintained Aider/Harbor conversion.

Not used by any active study. Original test assertions remain unchanged.
"""
import hashlib
import re
import shlex

UPSTREAM_REVISION = 'e77a18bfeed53f907f335b9132d87006e01b3dfd'
UPSTREAM_CPP_SNIPPET_SHA256 = 'fec758290f70682b2fc5df5a493e7b7f1adacd49e6339e64d505abd6cad2419b'


def strict_cpp_wrapper(upstream_snippet: str, exercise_name: str) -> str:
    """Keep upstream fixture staging, execute the declared test target strictly.

    CMake's exercise target is fixed by the upstream adapter from metadata.
    Enable all Exercism cases, as the original Aider cpp-test.sh does. Build
    just that target, then execute it once, preserving its actual exit status.
    Never guess executable names or treat a missing executable as a pass.
    """
    if hashlib.sha256(upstream_snippet.encode()).hexdigest() != UPSTREAM_CPP_SNIPPET_SHA256:
        raise ValueError('Unreviewed upstream C++ wrapper revision')
    if not re.fullmatch(r'[a-z][a-z0-9-]*', exercise_name):
        raise ValueError('Invalid declared exercise target')
    marker = 'echo "Building and running C++ tests..."'
    staging = upstream_snippet.split(marker)[0]
    target = shlex.quote(exercise_name)
    executable = shlex.quote('./build/' + exercise_name)
    return ('set -euo pipefail\n' + staging +
            '\ncmake -S . -B build -DEXERCISM_RUN_ALL_TESTS=1\n' +
            f'cmake --build build --target {target}\n' +
            f'test -x {executable}\nexec {executable}\n')
