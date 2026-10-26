#!/usr/bin/env python3
"""Restore the frozen pilot without selecting tasks or changing its protocol."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'experiments/codex-pilot-001'
GRADER = ROOT / 'scripts/prepare_codex_pilot.py'
WORK = Path('/workspace/scratch/ttgl-codex-pilot')
EVALUATOR = Path('/workspace/scratch/ttgl-codex-pilot-evaluator')
PYTHON = Path('/workspace/.tools/ttgl-codex-pilot/bin/python')


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def load_plan(plan: Path = PLAN, grader_path: Path = GRADER):
    protocol = json.loads((plan / 'protocol.json').read_text())
    for path, key in [(plan / 'tasks.json', 'tasks_sha256'),
                      (plan / 'provenance.json', 'provenance_sha256'),
                      (grader_path, 'grader_sha256')]:
        if digest(path.read_bytes()) != protocol[key]:
            raise ValueError(f'Frozen input hash mismatch: {path.name}')
    spec = importlib.util.spec_from_file_location('ttgl_frozen_pilot_grader', grader_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if digest(module.MEMORY.encode()) != protocol['memory_sha256']:
        raise ValueError('Frozen memory hash mismatch')
    registry = json.loads((plan / 'tasks.json').read_text())
    if [t['task_id'] for t in registry['tasks']] != protocol['task_ids']:
        raise ValueError('Task selection differs from frozen protocol')
    if registry['arms'] != protocol['arms']:
        raise ValueError('Arm selection differs from frozen protocol')
    provenance = json.loads((plan / 'provenance.json').read_text())
    return module, protocol, registry, provenance


def tree_digest(module, path: Path) -> str:
    return digest(json.dumps(module.files(path), sort_keys=True).encode())


def verify_integrity(plan: Path = PLAN, evaluator: Path = EVALUATOR,
                     grader_path: Path = GRADER) -> dict:
    """Verify the exact source trees used by the frozen grader before each grade."""
    module, protocol, registry, _ = load_plan(plan, grader_path)
    checks = []
    for task in registry['tasks']:
        base = evaluator / task['task_id'] / 'base'
        tests = evaluator / task['task_id'] / 'fixed' / Path(task['test_file']).parent
        for path, key in [(base, 'base_tree_sha256'),
                          (tests, 'evaluation_test_tree_sha256')]:
            if not path.is_dir():
                raise ValueError(f'Missing evaluator tree: {path}')
            actual = tree_digest(module, path)
            if actual != task[key]:
                raise ValueError(f'Evaluator tree hash mismatch: {task["task_id"]} {key}')
            checks.append({'task_id': task['task_id'], 'field': key, 'sha256': actual})
    return {'status': 'verified', 'protocol_sha256': digest((plan / 'protocol.json').read_bytes()),
            'checks': checks}


def check_environment(python: Path, requirements: Path) -> dict:
    expected = {}
    for line in requirements.read_text().splitlines():
        if line and not line.startswith('#'):
            package, version = line.split('==', 1)
            expected[package] = version
    command = [str(python), '-c',
               'import json,sys,importlib.metadata as m; '
               'names=json.loads(sys.argv[1]); '
               'print(json.dumps({"python":".".join(map(str,sys.version_info[:3])), '
               '"packages":{name:m.version(name) for name in names}}))',
               json.dumps(list(expected))]
    actual = json.loads(subprocess.check_output(command, text=True))
    if actual['python'] != '3.8.20' or actual['packages'] != expected:
        raise ValueError('Pilot interpreter or dependencies differ from the pinned environment')
    return actual


def install_environment(python: Path, requirements: Path) -> None:
    """Install only if absent; never mutate an existing pilot environment."""
    if python.exists():
        check_environment(python, requirements)
        return
    uv = shutil.which('uv')
    if not uv:
        raise RuntimeError('uv is required for --install-env; install the supported uv CLI first')
    env = os.environ.copy()
    env['UV_CACHE_DIR'] = '/tmp/ttgl-uv-cache'
    env['UV_PYTHON_INSTALL_DIR'] = '/workspace/.tools/python'
    subprocess.run([uv, 'python', 'install', '3.8.20', '--no-bin'], env=env, check=True)
    version = subprocess.check_output([uv, 'python', 'find', '--managed-python', '3.8.20'],
                                      env=env, text=True).strip()
    subprocess.run([uv, 'venv', '--python', version, str(python.parent.parent)],
                   env=env, check=True)
    subprocess.run([uv, 'pip', 'sync', '--python', str(python), str(requirements)],
                   env=env, check=True)
    check_environment(python, requirements)


def restore(plan: Path = PLAN, work: Path = WORK, evaluator: Path = EVALUATOR,
            python: Path = PYTHON, grader_path: Path = GRADER,
            download: Callable[[str], bytes] | None = None) -> dict:
    """Download hash-verified archives, replay controls, then create fresh arms.

    A failed restore retains its own diagnostic trees. Existing destinations are
    never overwritten. A retry must use new destinations or explicitly remove
    only the previous failed restore's directories outside this program.
    """
    module, protocol, registry, provenance = load_plan(plan, grader_path)
    work, evaluator = work.resolve(), evaluator.resolve()
    if work == evaluator or work in evaluator.parents or evaluator in work.parents:
        raise ValueError('Worker and evaluator roots must be separate directories')
    for path in [work, evaluator]:
        if path.exists():
            raise FileExistsError(f'Refusing to overwrite existing restore destination: {path}')
    module.PYTHON = python
    source_records = {}
    for source in provenance['sources']:
        if source['url'] in source_records and source_records[source['url']] != source['sha256']:
            raise ValueError('Conflicting frozen source hashes')
        source_records[source['url']] = source['sha256']
    download = download or module.fetch
    cache = {}
    def checked_download(url: str) -> bytes:
        if url not in source_records:
            raise ValueError(f'Archive not recorded in frozen provenance: {url}')
        if url not in cache:
            data = download(url)
            if digest(data) != source_records[url]:
                raise ValueError(f'Download hash mismatch: {url}')
            cache[url] = data
        return cache[url]
    module.fetch = checked_download
    work.mkdir(parents=True, exist_ok=False)
    evaluator.mkdir(parents=True, exist_ok=False)
    report = {'status': 'restoring', 'protocol_sha256': digest((plan / 'protocol.json').read_bytes()),
              'workspace_root': str(work), 'evaluator_root': str(evaluator),
              'python': str(python), 'checks': [], 'tasks_reselected': False}
    report_path = evaluator / 'restore-report.json'
    try:
        for task in registry['tasks']:
            taskroot = evaluator / task['task_id']
            for kind, revision in [('base', task['base_commit']), ('fixed', task['fixed_commit'])]:
                module.archive(task['repo'], revision, taskroot / kind, [])
            if tree_digest(module, taskroot / 'base') != task['base_tree_sha256']:
                raise ValueError(f'Restored base tree hash mismatch: {task["task_id"]}')
            testdir = taskroot / 'fixed' / Path(task['test_file']).parent
            if tree_digest(module, testdir) != task['evaluation_test_tree_sha256']:
                raise ValueError(f'Restored evaluation tree hash mismatch: {task["task_id"]}')
            shutil.copytree(taskroot / 'base', taskroot / 'buggy-eval')
            module.overlay_tests(taskroot / 'fixed', taskroot / 'buggy-eval', task)
            expected = next(x for x in provenance['feasibility_screen']
                            if x['task_id'] == task['task_id'])
            controls = {}
            for label, tree in [('buggy', 'buggy-eval'), ('fixed', 'fixed')]:
                outcome = module.run_tests(taskroot / tree, task, taskroot / f'restore-control-{label}')
                if outcome['counts'] != expected[label]['counts'] or outcome['returncode'] != expected[label]['returncode']:
                    raise ValueError(f'Restored {label} control differs from frozen record: {task["task_id"]}')
                controls[label] = outcome
            report['checks'].append({'task_id': task['task_id'], 'controls': controls})
            write_json(report_path, report)
        verify_integrity(plan, evaluator, grader_path)
        for task in registry['tasks']:
            for arm in registry['arms']:
                destination = work / arm / task['task_id']
                shutil.copytree(evaluator / task['task_id'] / 'base', destination,
                                ignore=shutil.ignore_patterns('.git', '__pycache__', '.pytest_cache', '*.pyc'))
                (destination / 'USER_MEMORY.md').write_text(module.MEMORY)
                (destination / 'TASK.md').write_text(
                    '# Repository repair\n\n' + task['statement'] +
                    '\n\nRead USER_MEMORY.md. Work only in this checkout. Do not access network, '
                    'sibling workspaces, benchmark metadata, gold patches, or evaluator files. '
                    'You may run public tests and add your own tests. Preserve existing tests. '
                    'Do not use git history.\n\nPython: ' + str(python) + '\n')
        report.update(status='restored_and_controls_verified',
                      worker_count=len(registry['tasks']) * len(registry['arms']))
        write_json(report_path, report)
        return report
    except BaseException as exc:
        report.update(status='failed', error_type=type(exc).__name__, error=str(exc))
        write_json(report_path, report)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install-env', action='store_true')
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--workspace-root', type=Path, default=WORK)
    parser.add_argument('--evaluator-root', type=Path, default=EVALUATOR)
    parser.add_argument('--python', type=Path, default=PYTHON)
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify_integrity(evaluator=args.evaluator_root), indent=2))
        return 0
    for path in [args.workspace_root, args.evaluator_root]:
        if path.exists():
            raise FileExistsError(f'Refusing to overwrite existing restore destination: {path}')
    load_plan()
    if args.install_env:
        install_environment(args.python, PLAN / 'requirements.txt')
    environment = check_environment(args.python, PLAN / 'requirements.txt')
    result = restore(work=args.workspace_root, evaluator=args.evaluator_root, python=args.python)
    result['environment'] = environment
    write_json(args.evaluator_root / 'restore-report.json', result)
    print(json.dumps({'status': result['status'], 'worker_count': result['worker_count'],
                      'report': str(args.evaluator_root / 'restore-report.json')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
