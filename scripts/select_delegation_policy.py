#!/usr/bin/env python3
"""Apply the registered development-only selection rule before held-out trials."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ttgl import benchmark, frontier

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--candidate', action='append', required=True, help='adaptive=ANALYSIS_DIRECTORY or fallback=ANALYSIS_DIRECTORY')
parser.add_argument('--protocol', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
candidates = []
expected_tasks, expected_rates = None, None
for spec in args.candidate:
    mode, directory = spec.split('=', 1)
    if mode not in ('adaptive', 'fallback') or any(r['mode']==mode for r in candidates):
        raise ValueError('Candidate modes must be distinct and explicitly named')
    directory = Path(directory)
    validation = json.loads((directory/'validation.json').read_text())
    path = directory/'published-rate-records.json'
    if validation.get('status') != 'completed_officially_graded_engineering_panel' or validation['published_rate_records_sha256'] != benchmark.digest(path):
        raise ValueError('Candidate analysis is incomplete or changed')
    records = json.loads(path.read_text())
    result = frontier.compare(records, policy='personal')
    if result['cost_ratio'] is None:
        raise ValueError('Missing candidate cost observations; do not select on unknowns')
    tasks = sorted({r['task_id'] for r in records})
    rates = validation['published_rate_scenario_sha256']
    if expected_tasks is not None and (tasks != expected_tasks or rates != expected_rates):
        raise ValueError('Candidate task sets or pricing scenarios differ')
    expected_tasks, expected_rates = tasks, rates
    rows = [r for r in records if r['arm']=='personal']
    candidates.append({'mode':mode, 'resolved':sum(r['resolved'] for r in rows),
        'assigned':len(rows), 'total_model_cost_scenario_usd':sum(r['cost_usd'] for r in rows),
        'analysis_directory':str(directory), 'records_sha256':benchmark.digest(path),
        'target_comparison':result})
if {r['mode'] for r in candidates} != {'adaptive','fallback'}:
    raise ValueError('Both registered candidates are required')
ordered = sorted(candidates,key=lambda r:(-r['resolved'],r['total_model_cost_scenario_usd'],r['mode']))
benchmark.write_new(args.output, {
    'status':'selected_on_development_only_before_held_out_inference',
    'selected_mode':ordered[0]['mode'],
    'rule':'Highest assisted resolution count, then lowest absolute total model-cost scenario, then lexical tie-break',
    'protocol_sha256':benchmark.digest(args.protocol),
    'script_sha256':benchmark.digest(Path(__file__)),
    'candidates':candidates, 'development_task_ids':expected_tasks,
    'held_out_outcomes_used':False,
    'interpretation':'Selection is exploratory; all candidate attempts remain reported. A selected policy is not evidence that the 95/95 target has been achieved.'})
print(json.dumps({'selected_mode':ordered[0]['mode'],'candidates':candidates},indent=2))
