#!/usr/bin/env python3
"""Freeze and execute the existing six-arm study with offline container tools.

Environment exclusions are determined from independent base/gold controls before
model outcomes. The full original panel and failed controls remain recorded.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ttgl import benchmark, isolated


def sources():
    paths = [Path(__file__), Path(isolated.__file__), isolated.SERVER,
             isolated.SERVER.parent / 'package-lock.json']
    return {str(p.relative_to(isolated.ROOT)): benchmark.digest(p) for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'preflight', 'run'])
    parser.add_argument('--study-dir', type=Path, required=True)
    parser.add_argument('--controls', type=Path)
    parser.add_argument('--worker-validation', type=Path)
    parser.add_argument('--tasks', type=Path, default=Path('experiments/swe-bench-verified-001/tasks.json'))
    parser.add_argument('--workspace-root', type=Path)
    parser.add_argument('--small-model', default='gpt-6-luna')
    parser.add_argument('--large-model', default='gpt-6.1-sol')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    study = args.study_dir.resolve()
    if args.command == 'init':
        if not args.controls or not args.workspace_root or not args.worker_validation:
            parser.error('init requires --controls, --worker-validation and --workspace-root')
        controls = json.loads((args.controls / 'summary.json').read_text())
        panel = benchmark.read_tasks(args.tasks)
        lookup = {r['instance_id']: r for r in controls['tasks']}
        workers = json.loads(args.worker_validation.read_text())
        readiness = {r['instance_id']: r for r in workers['tasks']}
        if set(lookup) != {r['instance_id'] for r in panel['tasks']}:
            raise ValueError('Controls must account for the complete frozen panel')
        if set(readiness) != set(lookup):
            raise ValueError('Worker validation must account for the complete original panel')
        for key, record in readiness.items():
            if record['controls_record_sha256'] != benchmark.digest(args.controls / (key + '.json')):
                raise ValueError('Worker validation refers to different controls')
            if record['ready'] and record.get('image_id') != lookup[key]['image']['image_id']:
                raise ValueError('Validated worker image differs from controls')
        eligible = [r for r in panel['tasks'] if lookup[r['instance_id']]['eligible']
                    and readiness[r['instance_id']]['ready']]
        if not eligible:
            raise ValueError('No valid evaluator environment; do not spend model quota')
        filtered = {**panel, 'tasks': eligible}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'tasks.json'
            path.write_text(json.dumps(filtered, indent=2, ensure_ascii=False) + '\n')
            benchmark.initialize(path, study, args.workspace_root,
                small_model=args.small_model, large_model=args.large_model,
                assignment_ordering='task_blocked',
                worker_environment='Official task image dependencies; exact-base source with shallow Git history',
                isolation='Unmounted offline Docker workers; host native tools disabled; context-only expert/router')
        environment = {
            'schema_version': 1, 'source_sha256': sources(),
            'backend': isolated.ContainerBackend().describe(),
            'original_tasks_sha256': benchmark.digest(args.tasks),
            'controls_summary_sha256': benchmark.digest(args.controls / 'summary.json'),
            'worker_validation_sha256': benchmark.digest(args.worker_validation),
            'eligibility': 'gold passes, base fails, staged public smoke passes before scored attempts',
            'excluded_environment_ids': [key for key, row in lookup.items()
                                        if not row['eligible'] or not readiness[key]['ready']],
            'images': {r['instance_id']: lookup[r['instance_id']]['image'] for r in eligible},
            'worker_boundary': 'unmounted offline Docker; native host tools disabled; MCP SDK shell only',
            'limitations': ['12-task engineering panel; no powered noninferiority claim',
                'Requested model IDs are not immutable model weights',
                'Model usage excludes setup, controls and evaluation overhead',
                'Unknown subscription credits and dollar costs remain null'],
        }
        benchmark.write_new(study / 'environment.json', environment)
        (study / 'environment.sha256').write_text(benchmark.digest(study / 'environment.json') + '\n')
        print(json.dumps({'status': 'frozen_not_run', 'tasks': len(eligible), 'assignments': len(eligible)*6}))
        return
    if benchmark.digest(study / 'environment.json') != (study / 'environment.sha256').read_text().strip():
        raise ValueError('Frozen environment changed')
    environment = json.loads((study / 'environment.json').read_text())
    if environment['source_sha256'] != sources():
        raise ValueError('Execution source changed; create a new study')
    backend = isolated.ContainerBackend()
    if backend.describe() != environment['backend']:
        raise ValueError('Codex backend identity changed; create a new study')
    if args.command == 'preflight':
        print(json.dumps(benchmark.preflight(study, backend=backend)))
    else:
        workers = isolated.DockerWorkers(backend, environment['images'], study / 'environments')
        benchmark.run_study(study, resume=args.resume, backend=backend, worker_runtime=workers)


if __name__ == '__main__':
    main()
