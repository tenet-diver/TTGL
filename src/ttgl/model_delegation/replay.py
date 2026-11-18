"""Exploratory leave-one-task-out diagnostic over already published outcomes.

Not new model inference, prospective routing or a causal delegation experiment.
Historical whole-task outcomes are explicitly labelled proxies, not verified
new subtask procedures. Native source/account availability is not inferred here.
"""
from __future__ import annotations
from pathlib import Path
from .routing import Policy, route
from ..experience_routing.io import read, file_digest, write_new, digest


def historical_replay(root, output, *, as_of='2026-11-18T12:00:00+00:00'):
    root, output = Path(root), Path(output)
    record_path = root/'results/delegation-heldout-001/analysis-002/published-rate-records.json'
    task_path = root/'experiments/delegation-heldout-001/tasks.json'
    grade_index_path = record_path.parent/'grades-portable.json'
    grade_index = read(grade_index_path)
    records = read(record_path)
    tasks = {t['instance_id']: t for t in read(task_path)['tasks']}
    by_task = {}
    for r in records:
        if r['arm'] in ('small', 'large'):
            by_task.setdefault(r['task_id'], {})[r['arm']] = r
    if not by_task or any(set(v) != {'small', 'large'} for v in by_task.values()):
        raise ValueError('Complete paired retained outcome matrix required')
    context = {'project': 'observatory-historical-replay', 'study': 'tool-recency-replay-001',
               'arm': 'shared-frozen-historical', 'account_hash': 'simulation-no-native-source-binding',
               'parent_model': 'gpt-6.1-sol', 'rate_scenario': 'historical-relative-eligibility-only',
               'watermark': len(by_task), 'now': as_of, 'language': 'python', 'category': 'repair', 'actions': ['repair', 'test']}
    models = [{'model': name, 'unit_cost': cost, 'available': True, 'qualified': True,
               'checked_at': as_of, 'expires_at': '2026-11-19T00:00:00+00:00', 'capabilities': [],
               'account_hash': context['account_hash'], 'rate_scenario': context['rate_scenario']}
              for name, cost in [('gpt-6-luna', 1), ('gpt-6.1-sol', 20)]]
    experiences, source_hashes = [], {str(p.relative_to(root)): file_digest(p) for p in (record_path, task_path, grade_index_path)}
    for i, (task_id, pair) in enumerate(sorted(by_task.items())):
        for arm, record in pair.items():
            native_path = root/'results/delegation-heldout-001/study-002/runs'/arm/task_id/'manifest.json'
            grader_path = (grade_index_path.parent/grade_index[arm][task_id]).resolve()
            if not grader_path.is_relative_to(root.resolve()):
                raise ValueError('Historical grade reference escapes source repository')
            if file_digest(native_path) != record['manifest_sha256'] or file_digest(grader_path) != record['grader_report_sha256']:
                raise ValueError('Historical native/grade artifact hash mismatch')
            original = read(grader_path)[task_id]
            if original.get('infra_failure') or type(original.get('resolved')) is not bool or original['resolved'] != record['resolved']:
                raise ValueError('Historical grade matrix conflicts with the official report')
            source_hashes[str(native_path.relative_to(root))] = file_digest(native_path)
            source_hashes[str(grader_path.relative_to(root.resolve()))] = file_digest(grader_path)
        manifest_path = root/'results/delegation-heldout-001/study-002/runs/small'/task_id/'manifest.json'
        manifest = read(manifest_path)
        if file_digest(manifest_path) != pair['small']['manifest_sha256']:
            raise ValueError('Historical native manifest hash mismatch')
        if type(pair['small']['resolved']) is not bool:
            raise ValueError('Unknown historical grade is not a failure/success proxy')
        source_hashes[str(manifest_path.relative_to(root))] = file_digest(manifest_path)
        experiences.append({'id': digest([task_id, manifest['finished_at']]), 'task_id': task_id,
            **{k: context[k] for k in ('project', 'study', 'arm', 'account_hash', 'language', 'category', 'actions')},
            'goal': tasks[task_id]['problem_statement'], 'model': pair['small']['model_id'],
            'visibility': 'runtime_public', 'verified': True, 'source_current': True,
            'verification_ref': pair['small']['grader_report_sha256'], 'outcome': 'pass' if pair['small']['resolved'] else 'fail',
            'occurred_at': manifest['created_at'], 'verified_at': manifest['finished_at'],
            'available_at': as_of, 'available_sequence': i + 1,
            'procedure': [], 'proxy_kind': 'retained whole-task outcome; not extracted subtask experience'})
    report = {'schema_version': 1, 'study': context['study'], 'mode': 'exploratory_retrospective_leave_one_task_out',
              'actual_new_model_calls': 0, 'fresh_benchmark_tasks': 0, 'task_count': len(by_task),
              'source_hashes': source_hashes, 'source_account_qualified': False, 'assumed_availability': models,
              'limitations': ['Already exposed historical tasks; thresholds are exploratory, not held-out-confirmatory.',
                'Whole-task lexical/outcome proxies do not establish subtask transfer or autonomous tool quality.',
                'All evidence is available retrospectively as of the replay time; native completion timestamps are age proxies, not original grade-publication timestamps.',
                'Assumed availability/cost ordering is simulation-only and cannot enable a native worker.',
                'Selected historical execution costs exclude new parent coordination, retrieval and delegation overhead.',
                'No native quota, latency improvement, new patch or causal savings claim follows.'], 'arms': {}}
    for mode in ('parent_only', 'always_cheap', 'similarity', 'similarity_recency'):
        rows = []
        for task_id, pair in sorted(by_task.items()):
            decision = None if mode == 'parent_only' else route({**context, 'task_id': task_id,
                'goal': tasks[task_id]['problem_statement']}, experiences, models, Policy(mode=mode))
            arm = 'small' if decision and decision['selected_model'] else 'large'
            r = pair[arm]
            rows.append({'task_id': task_id, 'selected_arm': arm, 'resolved': r['resolved'],
                         'historical_selected_scenario_cost': r['cost_usd'], 'decision': decision})
        costs = [r['historical_selected_scenario_cost'] for r in rows]
        report['arms'][mode] = {'assigned': len(rows), 'resolved': sum(r['resolved'] for r in rows),
            'cheap_selected': sum(r['selected_arm'] == 'small' for r in rows),
            'historical_selected_scenario_cost': sum(costs) if all(x is not None for x in costs) else None,
            'rows': rows}
    write_new(output/'report.json', report)
    return report
