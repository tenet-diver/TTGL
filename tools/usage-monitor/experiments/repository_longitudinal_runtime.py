"""Offline three-repository runtime; no model calls or hidden feedback export.

Reuses the reviewed upstream parser. Primary pass requires every prescribed
test to pass; other observed outcomes and command exits are retained separately.
The earlier frozen exact-match result is never rewritten.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

import repository_memory_runtime as prior

REPO, PRIVATE, TEMP, IMAGE = prior.REPO, prior.PRIVATE, prior.TEMP, prior.IMAGE


def task(instance):
    return next(r for r in json.loads((PRIVATE / 'longitudinal-private-targets-002.json').read_text()) if r['instance_id'] == instance)


def source_root(instance):
    receipt = json.loads((PRIVATE / (instance + '-long-source.json')).read_text())
    if task(instance)['base_commit'] not in receipt['url']:
        raise ValueError('Unpinned source')
    return Path(receipt['path'])


def container_args(work, instance):
    row = task(instance)
    common = ['docker', 'run', '--rm', '--network=none', '--read-only', '--user=1000:1000',
              '--cap-drop=ALL', '--security-opt=no-new-privileges', '--pids-limit=128',
              '--memory=3g', '--cpus=2', '--tmpfs=/tmp:rw,nosuid,nodev,size=256m',
              '--mount', f'type=bind,src={Path(work).resolve()},dst=/app', '-w', '/app',
              '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
              '-e', 'PATH=/task-bin:/usr/local/bin:/usr/bin:/bin', '-e', 'HOME=/tmp',
              '-e', 'HTTP_PROXY=', '-e', 'HTTPS_PROXY=', '-e', 'ALL_PROXY=']
    if row['repo'] == 'aws-cloudformation/cfn-lint':
        deps, extra = TEMP / 'cfn-deps', TEMP / 'cfn-modern-extra-deps'
        import tomllib
        entry = tomllib.loads((source_root(instance) / 'pyproject.toml').read_text())['project']['scripts']['cfn-lint']
        if entry not in ('cfnlint.runner:main', 'cfnlint.__main__:main'):
            raise ValueError('Unregistered entrypoint')
        module, function = entry.split(':')
        bins = TEMP / 'long-bins' / instance
        bins.mkdir(parents=True, exist_ok=True)
        script = bins / 'cfn-lint'
        body = f'#!/usr/bin/env python3\nfrom {module} import {function}\nraise SystemExit({function}())\n'
        if script.exists() and script.read_text() != body:
            raise ValueError('Entrypoint changed')
        script.write_text(body)
        script.chmod(0o755)
        common += ['--mount', f'type=bind,src={bins},dst=/task-bin,readonly',
                   '--mount', f'type=bind,src={extra},dst=/task-extra,readonly',
                   '-e', 'PYTHONPATH=/app/src:/task-deps:/task-extra',
                   '-e', 'AWS_DEFAULT_REGION=us-east-1', '-e', 'AWS_EC2_METADATA_DISABLED=true',
                   '-e', 'AWS_ACCESS_KEY_ID=benchmark-placeholder', '-e', 'AWS_SECRET_ACCESS_KEY=benchmark-placeholder']
    else:
        deps = TEMP / 'attrs-deps'
        common += ['-e', 'PYTHONPATH=/app/src:/task-metadata:/task-deps',
                   '-e', 'HYPOTHESIS_STORAGE_DIRECTORY=/tmp/hypothesis']
        metadata = TEMP / 'long-package-metadata' / instance
        if not metadata.exists():
            raise ValueError('Source-built distribution metadata required')
        common += ['--mount', f'type=bind,src={metadata},dst=/task-metadata,readonly']
    return common + ['--mount', f'type=bind,src={deps},dst=/task-deps,readonly', IMAGE]


def grade(instance, patch, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    row = task(instance)
    work = TEMP / 'long-replay' / hashlib.sha256(str(output.resolve()).encode()).hexdigest()[:20]
    shutil.copytree(source_root(instance), work)
    prior.checked(['git', 'init', '-q', str(work)])
    prior.checked(['git', '-C', str(work), '-c', 'core.hooksPath=/dev/null', 'add', '--force', '.'])
    for path in [work] + list(work.rglob('*')):
        if not path.is_symlink():
            import os
            os.chown(path, 1000, 1000)
    if not prior.apply_patch(work, patch, output, 'candidate') or not prior.apply_patch(work, row['test_patch'], output, 'hidden-tests'):
        value = dict(instance_id=instance, passed=False, replay_prepared=False, reason='Patch application failed; no retry')
    else:
        commands = row['install_config']['test_cmd']
        commands = [commands] if isinstance(commands, str) else commands
        if any(not re.match(r'^pytest(?:\s|$)', c) for c in commands):
            raise ValueError('Unsupported test-command adaptation')
        commands = [re.sub(r'^pytest(?=\s|$)', 'python3 -m pytest', c) for c in commands]
        cmd = container_args(work, instance) + ['bash', '-c', 'set -e\n' + '\n'.join(commands)]
        prior.write(output / 'intent.json', dict(command=cmd, model_calls=0, hidden_to_actor=True))
        start = time.perf_counter()
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        text = run.stdout + run.stderr
        (output / 'test.log').write_text(text)
        upstream = prior.upstream()
        parsed = upstream.get_parser(row['install_config']['log_parser'])(text)
        passed = {upstream._normalize_test_name(k) for k, v in parsed.items() if v == 'PASSED'}
        expected = {upstream._normalize_test_name(k) for k in row['FAIL_TO_PASS'] + row['PASS_TO_PASS']}
        value = dict(instance_id=instance, passed=bool(expected) and expected <= passed,
                     replay_prepared=True, exit_code=run.returncode, missing_expected=sorted(expected - passed),
                     additional_passed=sorted(passed - expected), expected_count=len(expected),
                     other_nonpassing={upstream._normalize_test_name(k): v for k, v in parsed.items()
                                       if v != 'PASSED' and upstream._normalize_test_name(k) not in expected},
                     seconds=time.perf_counter() - start, model_calls=0, official_benchmark_score=False)
    prior.write(output / 'grade.json', value)
    return value


def controls(instance, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    empty = grade(instance, '', output / 'empty')
    reference = grade(instance, task(instance)['patch'], output / 'reference')
    value = dict(instance_id=instance, passed=empty['replay_prepared'] and not empty['passed'] and reference['passed'],
                 empty_passed=empty['passed'], reference_passed=reference['passed'], model_calls=0)
    prior.write(output / 'controls.json', value)
    print(json.dumps(value), flush=True)
    return value
