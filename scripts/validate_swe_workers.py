#!/usr/bin/env python3
"""Check prepared solver dependencies/public tests without any model calls."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ttgl import benchmark, isolated

# Fixed public smoke modules, unrelated to the private regression patches.
SMOKES = {
    'scikit-learn/scikit-learn': 'python -m pytest -q sklearn/utils/tests/test_show_versions.py',
    'django/django': 'python tests/runtests.py --verbosity 0 utils_tests.test_dateformat',
    'pydata/xarray': 'python -m pytest -q xarray/tests/test_options.py',
    'sympy/sympy': 'python bin/test sympy/core/tests/test_numbers.py -k test_Integer',
    'astropy/astropy': 'python -m pytest -q astropy/units/tests/test_quantity.py -k test_unit',
    'psf/requests': 'python -m pytest -q tests/test_utils.py',
    'mwaskom/seaborn': 'if [ -f seaborn/tests/test_palettes.py ]; then python -m pytest -q seaborn/tests/test_palettes.py; else python -m pytest -q tests/test_palettes.py; fi',
    'sphinx-doc/sphinx': 'if [ -f tests/test_util.py ]; then python -m pytest -q tests/test_util.py; else python -m pytest -q tests/test_util/test_util.py; fi',
}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--controls', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--workspace-root', type=Path, required=True)
    p.add_argument('--tasks', type=Path, default=Path('experiments/swe-bench-verified-001/tasks.json'))
    p.add_argument('--wait-for-controls', action='store_true', help='Pipeline probes after each completed control pair')
    args = p.parse_args()
    if args.output.exists() or args.workspace_root.exists():
        raise ValueError('Use new validation records and workspace roots')
    args.output.mkdir(parents=True)
    controls = (json.loads((args.controls / 'summary.json').read_text())
                if not args.wait_for_controls else {'tasks': []})
    lookup = {r['instance_id']: r for r in controls['tasks']}
    tasks = benchmark.read_tasks(args.tasks)
    benchmark.write_new(args.output / 'protocol.json', {
        'script_sha256': benchmark.digest(Path(__file__)), 'smoke_commands': SMOKES,
        'controls_protocol_sha256': benchmark.digest(args.controls / 'protocol.json'),
        'tasks_sha256': benchmark.digest(args.tasks), 'inference_calls': 0,
    })
    backend = isolated.ContainerBackend()
    runtime = isolated.DockerWorkers(backend, {}, args.output / 'environments')
    rows = []
    for task in tasks['tasks']:
        key = task['instance_id']
        record = args.controls / (key + '.json')
        if args.wait_for_controls:
            deadline = time.monotonic() + 2400
            while not record.exists() or time.time()-record.stat().st_mtime < 2:
                if time.monotonic() > deadline:
                    raise RuntimeError('No completed control pair within 40 minutes; preserve partial probes')
                time.sleep(2)
            lookup[key] = json.loads(record.read_text())
        runtime.images[key] = lookup[key]['image']
        if not lookup[key]['eligible']:
            rows.append({'instance_id': key, 'ready': False, 'reason': 'invalid_official_controls',
                         'controls_record_sha256': benchmark.digest(record)})
            continue
        workspace = args.workspace_root.resolve() / key
        benchmark.prepare_workspace(task, workspace)
        runtime.prepare(task, workspace, args.output.resolve() / 'runs' / key)
        command = 'export PATH=/opt/miniconda3/envs/testbed/bin:$PATH; ' + SMOKES[task['repo']]
        result = subprocess.run(['docker', 'exec', '--workdir', '/testbed', backend.container,
                                 'timeout', '--signal=KILL', '180', 'bash', '-lc', command],
                                capture_output=True, text=True, timeout=200)
        (args.output / (key + '.stdout.txt')).write_text(result.stdout + '\n' + result.stderr)
        row = {'instance_id': key, 'command': command, 'returncode': result.returncode,
               'image_id': lookup[key]['image']['image_id'],
               'controls_record_sha256': benchmark.digest(record),
               'ready': result.returncode == 0, 'reason': 'public_smoke_pass' if result.returncode == 0 else 'public_smoke_failed',
               'stdout_sha256': benchmark.digest(args.output / (key + '.stdout.txt'))}
        benchmark.write_new(args.output / (key + '.json'), row)
        rows.append(row)
        runtime.close()
        print(json.dumps(row), flush=True)
    benchmark.write_new(args.output / 'summary.json', {'tasks': rows})


if __name__ == '__main__':
    main()
