#!/usr/bin/env python3
"""Summarize retained official controls; never grade model predictions."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def write(name, data):
    (ROOT / name).write_text(json.dumps(data, indent=2) + '\n')


protocol = json.loads((ROOT / 'protocol.json').read_text())
prior = json.loads((ROOT.parent / 'swe-bench-verified-001/controls/summary.json').read_text())
records = []
pairs = []
for path in sorted(ROOT.glob('*.execution.json')):
    state = json.loads(path.read_text())
    instance = state['instance_id']
    controls = {}
    for execution in state['controls']:
        report_path = ROOT / execution['report']
        if not report_path.is_file():
            continue
        digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
        if digest != execution['report_sha256']:
            raise ValueError(f'Official report changed: {report_path}')
        report = json.loads(report_path.read_text())[instance]
        counts = {k: {key: len(value) for key, value in group.items()}
                  for k, group in report['tests_status'].items()}
        record = {'instance_id': instance, 'control': execution['control'],
                  'resolved': report['resolved'], 'tests': counts,
                  'patch_successfully_applied': report['patch_successfully_applied'],
                  'official_infra_failure': report.get('infra_failure'),
                  'report': execution['report'], 'report_sha256': digest}
        records.append(record)
        controls[execution['control']] = record
    valid = False
    if set(controls) == {'base', 'gold'}:
        base, gold = controls['base'], controls['gold']
        bf, gf = base['tests']['FAIL_TO_PASS'], gold['tests']['FAIL_TO_PASS']
        bp, gp = base['tests']['PASS_TO_PASS'], gold['tests']['PASS_TO_PASS']
        valid = (not base['resolved'] and gold['resolved']
                 and all(x['patch_successfully_applied'] and not x['official_infra_failure']
                         for x in (base, gold))
                 and bf['success'] == 0 and bf['failure'] > 0
                 and gf['failure'] == 0 and gf['success'] == bf['failure']
                 and bp['failure'] == gp['failure'] == 0
                 and bp['success'] == gp['success'])
    pairs.append({'instance_id': instance, 'control_pair_valid': valid,
                  'execution_status': state['status'],
                  'image_repo_digests': state.get('image_repo_digests', [])})

checked = {pair['instance_id'] for pair in pairs}
unstarted = [task for task in protocol['task_order'] if task not in checked]
summary = {
    'schema_version': 1,
    'evidence_class': 'executed_official_evaluator_controls_not_model_experiment',
    'model_inference_calls': 0,
    'control_runs_executed': len(records),
    'instances_control_checked': len(pairs),
    'control_pairs_valid': sum(pair['control_pair_valid'] for pair in pairs),
    'stop_reason': 'User requested a handover prompt for execution on a different host',
    'remaining_tasks_not_started': unstarted,
    'partial_evaluator_runs': 0,
    'quality_or_cost_savings_estimate': None,
    'pairs': pairs,
    'records': records,
    'combined_frozen_panel': {
        'selected_tasks': 12,
        'instances_control_checked': prior['instances_control_checked'] + len(pairs),
        'control_pairs_valid': prior['control_pairs_valid'] + sum(p['control_pair_valid'] for p in pairs),
        'control_pairs_invalid': 1,
        'selected_tasks_without_controls': len(unstarted),
        'all_selected_tasks_environment_validated': False,
        'prior_summary': '../swe-bench-verified-001/controls/summary.json',
        'invalid_instance': 'psf__requests-5414',
        'invalid_reason': prior['requests_diagnosis'],
    },
}
write('summary.json', summary)
write('artifact-sha256.json', {
    str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
    for path in sorted(ROOT.rglob('*'))
    if path.is_file() and path.name != 'artifact-sha256.json' and '__pycache__' not in path.parts
})
print(json.dumps(summary['combined_frozen_panel'], indent=2))
