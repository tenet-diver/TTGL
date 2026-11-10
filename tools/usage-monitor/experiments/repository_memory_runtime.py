"""Patched, offline repository runtime; reuse upstream SWE-rebench log grading.

No model invocation. The actor never mounts grading material. Commands run as
UID1000 with dropped capabilities; benchmark image/install commands are unused.
Downloaded task dependencies require the dated private pre-install receipt.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

REPO = Path(__file__).resolve().parents[3]
PRIVATE = REPO / 'work/security/repository-memory-20261110'
TEMP = Path('/tmp/ttgl-repository-memory-20261110')
IMAGE = 'sha256:9ed8bd351e618aa9075306abee2a94a14954f35c23dbdc22902080e0dfbb930e'


def write(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def checked(cmd, **kwargs):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs)


def task(instance):
    rows = json.loads((PRIVATE / 'pinned-private-targets.json').read_text())
    return next(r for r in rows if r['instance_id'] == instance)


def source_root(instance):
    row = task(instance)
    receipt = PRIVATE / ('source-download.json' if instance.endswith('-2387')
                          else instance + '-source-download.json')
    value = json.loads(receipt.read_text())
    if row['base_commit'] not in value['url']:
        raise ValueError('Unpinned source archive')
    return Path(value['path'])


def prepare_work(instance, destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Never overwrite an existing attempt or workspace')
    shutil.copytree(source_root(instance), destination)
    if (destination / '.git').exists():
        raise ValueError('Source archive must not contain a Git control directory')
    checked(['git', 'init', '-q', str(destination)])
    git = ['git', '-C', str(destination), '-c', 'core.hooksPath=/dev/null']
    checked(git + ['add', '.'])
    checked(git + ['-c', 'user.name=TTGL benchmark', '-c',
                   'user.email=benchmark@example.invalid', 'commit', '-qm', 'prescribed base archive'])
    # Actor edits only this copy, never the immutable original or host grader.
    for parent, directories, files in os.walk(destination):
        os.chown(parent, 1000, 1000)
        for name in files:
            path = Path(parent) / name
            if not path.is_symlink():
                os.chown(path, 1000, 1000)
    destination.chmod(0o755)
    return destination


def container_args(work, instance, *, writable=True):
    receipt = json.loads((PRIVATE / 'pre-install-receipt.json').read_text())
    if receipt['known_findings']:
        raise ValueError('Known dependency findings block execution')
    deps = TEMP / 'cfn-deps'
    extra = TEMP / 'cfn-modern-extra-deps'
    bins = PRIVATE / 'task-bins' / instance
    bins.mkdir(parents=True, exist_ok=True, mode=0o755)
    bins.chmod(0o755)
    metadata = source_root(instance) / 'pyproject.toml'
    if metadata.exists():
        import tomllib
        entry = tomllib.loads(metadata.read_text())['project']['scripts']['cfn-lint']
    else:
        entry = 'cfnlint.__main__:main'
    if entry not in ('cfnlint.__main__:main', 'cfnlint.runner:main'):
        raise ValueError('Unregistered source console entrypoint')
    module, function = entry.split(':')
    shim = bins / 'cfn-lint'
    body = f'#!/usr/bin/env python3\nimport sys\nfrom {module} import {function}\nsys.exit({function}())\n'
    if shim.exists() and shim.read_text() != body:
        raise ValueError('Existing console entrypoint changed')
    shim.write_text(body)
    shim.chmod(0o755)
    # The target folder is not a normal site-packages directory. No .pth startup
    # hook is processed. Data/extension imports occur only in the task container.
    suffix = '' if writable else ',readonly'
    return ['docker', 'run', '--rm', '--network=none', '--read-only',
            '--user=1000:1000', '--cap-drop=ALL', '--security-opt=no-new-privileges',
            '--pids-limit=128', '--memory=3g', '--cpus=2',
            '--tmpfs=/tmp:rw,nosuid,nodev,size=256m',
            '--mount', f'type=bind,src={Path(work).resolve()},dst=/app{suffix}',
            '--mount', f'type=bind,src={deps},dst=/task-deps,readonly',
            '--mount', f'type=bind,src={extra},dst=/task-extra,readonly',
            '--mount', f'type=bind,src={bins},dst=/task-bin,readonly',
            '-w', '/app', '-e', 'PYTHONPATH=/app/src:/task-deps:/task-extra',
            '-e', 'PATH=/task-bin:/usr/local/bin:/usr/bin:/bin',
            '-e', 'HTTP_PROXY=', '-e', 'HTTPS_PROXY=', '-e', 'ALL_PROXY=',
            '-e', 'http_proxy=', '-e', 'https_proxy=', '-e', 'all_proxy=',
            '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD=1',
            '-e', 'AWS_DEFAULT_REGION=us-east-1', '-e', 'AWS_EC2_METADATA_DISABLED=true',
            '-e', 'AWS_ACCESS_KEY_ID=benchmark-placeholder',
            '-e', 'AWS_SECRET_ACCESS_KEY=benchmark-placeholder',
            IMAGE]


def upstream():
    receipt = json.loads((PRIVATE / 'vendor-pre-execution-receipt.json').read_text())
    for item in receipt['files']:
        path = PRIVATE / 'vibemem-source' / item['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('Reviewed upstream grading code changed')
    path = PRIVATE / 'vibemem-source/VibeMemBench/scripts/vendor/eval.py'
    spec = importlib.util.spec_from_file_location('ttgl_repository_upstream_eval', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_patch(work, patch, output, label):
    path = output / (label + '.diff')
    path.write_text(patch)
    if not patch.strip():
        return True
    result = subprocess.run(['git', '-C', str(work), 'apply', '--recount',
                             '--ignore-space-change', '--whitespace=nowarn', str(path.resolve())],
                            capture_output=True, text=True)
    write(output / (label + '-apply.json'), dict(exit_code=result.returncode,
          stdout=result.stdout, stderr=result.stderr))
    return result.returncode == 0


def grade(instance, candidate, output):
    """Fresh private replay. Hidden patches/logs never enter live memory."""
    row = task(instance)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    replay_id = hashlib.sha256(str(output.resolve()).encode()).hexdigest()[:16]
    work = prepare_work(instance, TEMP / 'grader-work' / (replay_id + '-' + output.name))
    start = time.perf_counter()
    if not apply_patch(work, candidate, output, 'candidate') or not apply_patch(
            work, row['test_patch'], output, 'hidden-tests'):
        result = dict(instance_id=instance, passed_match=False, replay_prepared=False,
                      reason='Patch application failed; no automatic retry')
        write(output / 'grade.json', result)
        return result
    config = row['install_config']
    commands = config['test_cmd']
    if isinstance(commands, str):
        commands = [commands]
    if any(not re.match(r'^pytest(?:\s|$)', cmd) for cmd in commands):
        raise ValueError('Register unsupported test-command adaptation before execution')
    commands = [re.sub(r'^pytest(?=\s|$)', 'python3 -m pytest', cmd) for cmd in commands]
    cmd = container_args(work, instance) + ['bash', '-c', 'set -e\n' + '\n'.join(commands)]
    write(output / 'intent.json', dict(at=datetime.now(timezone.utc).isoformat(), command=cmd,
          adaptation='Patched runtime and dependencies, source archive, no git3way; python -m pytest. Unchanged upstream parser, exact expected-pass matching. Not official released-image execution.'))
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired as error:
        write(output / 'timeout.json', dict(seconds=time.perf_counter() - start,
              model_calls=0, reason=str(error), no_retry=True))
        raise
    text = (run.stdout or '') + (run.stderr or '')
    (output / 'test.log').write_text(text)
    evaluator = upstream()
    parsed = evaluator.get_parser(config['log_parser'])(text)
    parsed = {evaluator._normalize_test_name(k): v for k, v in parsed.items()}
    passed = sorted(k for k, v in parsed.items() if v == 'PASSED')
    expected = sorted(evaluator._normalize_test_name(n)
                      for n in row['PASS_TO_PASS'] + row['FAIL_TO_PASS'])
    result = dict(instance_id=instance, passed_match=passed == expected,
          replay_prepared=True, exit_code=run.returncode, seconds=time.perf_counter() - start,
          passed_count=len(passed), expected_count=len(expected),
          fail_to_pass_count=len(row['FAIL_TO_PASS']),
          pass_to_pass_count=len(row['PASS_TO_PASS']),
          missing_expected=sorted(set(expected) - set(passed)),
          unexpected_passed=sorted(set(passed) - set(expected)), parsed=parsed,
          model_calls=0, official_benchmark_score=False)
    write(output / 'grade.json', result)
    return result


def controls(instance, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    rows = []
    for label in ('empty', 'reference'):
        value = grade(instance, '' if label == 'empty' else task(instance)['patch'],
                      directory / (instance + '-' + label))
        rows.append(dict(condition=label, resolved=value['passed_match'],
                         replay_prepared=value['replay_prepared'],
                         exit_code=value.get('exit_code')))
    passed = (rows[0]['replay_prepared'] and not rows[0]['resolved']
              and rows[1]['replay_prepared'] and rows[1]['resolved'])
    result = dict(instance_id=instance, passed=passed, controls=rows, model_calls=0,
                  scope='Actual adapted environment controls; not model-quality evidence')
    write(directory / 'controls.json', result)
    print(json.dumps(result), flush=True)
    if not passed:
        raise ValueError('Empty/reference controls fail; preserve and diagnose before model inference')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['controls'])
    parser.add_argument('instance')
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    controls(args.instance, args.directory)
