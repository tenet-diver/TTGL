#!/usr/bin/env python3
"""Run explicitly separate prompt treatments on already validated environments.

The source study supplies environment/control provenance, never model answers.
An explicit public task manifest selects development or held-out tasks. Only
environments previously validated by that source study may be reused here.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ttgl import benchmark, evaluation, isolated, policy


def extension_sources():
    return {str(p.relative_to(isolated.ROOT)): benchmark.digest(p)
            for p in [Path(__file__), Path(policy.__file__),
                      *sorted(policy.PROMPTS.glob('controller-v2-*.txt'))]}


def verify_sources(environment):
    for name, expected in environment['source_sha256'].items():
        if benchmark.digest(isolated.ROOT / name) != expected:
            raise ValueError('Frozen execution source changed: ' + name)
    if environment['policy_source_sha256'] != extension_sources():
        raise ValueError('Frozen policy treatment changed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'preflight', 'run', 'grade'])
    parser.add_argument('--study-dir', type=Path, required=True)
    parser.add_argument('--source-study', type=Path)
    parser.add_argument('--tasks', type=Path)
    parser.add_argument('--workspace-root', type=Path)
    parser.add_argument('--mode', choices=policy.MODES, default='adaptive')
    parser.add_argument('--purpose', choices=['development', 'held_out'], default='development')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    study = args.study_dir.resolve()
    if args.command == 'init':
        if not all([args.source_study, args.tasks, args.workspace_root]):
            parser.error('init requires --source-study, --tasks and --workspace-root')
        source = args.source_study.resolve()
        original = json.loads((source / 'environment.json').read_text())
        if benchmark.digest(source / 'environment.json') != (source / 'environment.sha256').read_text().strip():
            raise ValueError('Source environment changed')
        for name, expected in original['source_sha256'].items():
            if benchmark.digest(isolated.ROOT / name) != expected:
                raise ValueError('Source execution file changed: ' + name)
        _, original_tasks = benchmark.load_design(source)
        rows = {row['instance_id']: row for row in original_tasks['tasks']}
        selected = benchmark.read_tasks(args.tasks)
        for row in selected['tasks']:
            if rows.get(row['instance_id']) != row:
                raise ValueError('Task was not validated in the source environment')
        backend = policy.PolicyBackend(args.mode)
        benchmark.initialize(args.tasks, study, args.workspace_root,
            small_model='gpt-6-luna', large_model='gpt-6.1-sol',
            conditions=('small', 'large', 'personal'), assignment_ordering='task_blocked',
            worker_environment=original['backend']['worker_tools'],
            isolation=original['worker_boundary'])
        environment = {**original, 'backend': backend.describe(),
            'policy_mode': args.mode, 'purpose': args.purpose,
            'source_study': str(source),
            'source_environment_sha256': benchmark.digest(source / 'environment.json'),
            'policy_source_sha256': extension_sources(),
            'analysis_scope': 'Independent new assignments; do not pool development and held-out outcomes'}
        benchmark.write_new(study / 'environment.json', environment)
        (study / 'environment.sha256').write_text(benchmark.digest(study / 'environment.json') + '\n')
        (study / 'rate-scenario.json').write_bytes((source / 'rate-scenario.json').read_bytes())
        print(json.dumps({'status': 'frozen_not_run', 'mode': args.mode,
                          'purpose': args.purpose, 'assignments': len(selected['tasks'])*3}))
        return
    if benchmark.digest(study / 'environment.json') != (study / 'environment.sha256').read_text().strip():
        raise ValueError('Frozen environment changed')
    environment = json.loads((study / 'environment.json').read_text())
    verify_sources(environment)
    backend = policy.PolicyBackend(environment['policy_mode'], audit_root=study / 'effective-prompts')
    if backend.describe() != environment['backend']:
        raise ValueError('Backend identity changed')
    if args.command == 'preflight':
        print(json.dumps(benchmark.preflight(study, backend=backend)))
        return
    dataset = Path(environment['private_grading_dataset'])
    if benchmark.digest(dataset) != environment['private_grading_dataset_sha256']:
        raise ValueError('Private grading dataset changed')
    grader = evaluation.OfficialEvaluator(study, Path(environment['private_evaluator_root']),
        environment['evaluator_image_id'], dataset,
        timeout_seconds=environment['grading_timeout_seconds'])
    if args.command == 'grade':
        design, _ = benchmark.load_design(study)
        for assignment in design['assignment_order']:
            arm, key = assignment['arm'], assignment['instance_id']
            if (study / 'patches' / arm / (key + '.json')).exists():
                grader(arm, key)
        return
    workers = isolated.DockerWorkers(backend, environment['images'], study / 'environments')
    benchmark.run_study(study, resume=args.resume, backend=backend,
                        worker_runtime=workers, assignment_callback=grader)


if __name__ == '__main__':
    main()
