#!/usr/bin/env python3
"""Read-only factorial analysis; never feeds grades back to live agents."""
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics

from analyze_codex_team_scaling import mechanism


def contrast(treatment, control):
    result = dict(task=treatment['task'], treatment=treatment['directory'],
                  control=control['directory'],
                  success_difference=int(treatment['grade']['passed'])-int(control['grade']['passed']),
                  attempt_seconds_difference=treatment['wall_seconds']-control['wall_seconds'],
                  attempt_time_ratio=treatment['wall_seconds']/control['wall_seconds'])
    a, b = treatment['standard_credit_lower_bound'], control['standard_credit_lower_bound']
    exact_a, exact_b = treatment['inference_accounting_complete'], control['inference_accounting_complete']
    result.update(exact_credit_ratio=a/b if exact_a and exact_b and b else None,
                  credit_ratio_lower_bound=a/b if exact_b and b else None,
                  credit_ratio_upper_bound=a/b if exact_a and b else None)
    return result


def analyze(root, protocol_path, output):
    if output.exists():
        raise ValueError('Preserve all earlier analysis snapshots')
    protocol = json.loads(protocol_path.read_text())
    checkpoints = sorted(root.glob('checkpoint-*.json'))
    if not checkpoints:
        raise ValueError('No audited completed cells')
    assignments = json.loads(checkpoints[-1].read_text())['assignments']
    cells = []
    for assignment in assignments:
        evidence = mechanism(root/assignment['directory'])
        value = dict(assignment, **evidence)
        value['standard_credit_lower_bound'] = value.pop('standard_credit_scenario')
        value['api_equivalent_lower_bound_usd'] = value.pop('standard_api_equivalent_usd')
        value['wall_seconds'] = assignment['wall_seconds']
        value['full_standard_credits'] = value['standard_credit_lower_bound'] if value['inference_accounting_complete'] else None
        value['verified_source'] = value['grade']['passed']
        value['normally_completed_and_verified'] = value['verified_source'] and value['native_parent_turn_status']=='completed'
        cells.append(value)
    groups = defaultdict(list)
    for cell in cells:
        groups[(cell['condition'], cell['guidance'], cell['total_agent_capacity'])].append(cell)
    summaries = []
    for (condition, guidance, capacity), selected in sorted(groups.items()):
        successes = sum(x['verified_source'] for x in selected)
        cost = sum(x['standard_credit_lower_bound'] for x in selected)
        complete = all(x['inference_accounting_complete'] for x in selected)
        summaries.append(dict(condition=condition, guidance=guidance, capacity=capacity,
             tasks=len(selected), verified_source=successes,
             normally_completed_and_verified=sum(x['normally_completed_and_verified'] for x in selected),
             mean_attempt_seconds=statistics.mean(x['wall_seconds'] for x in selected),
             mean_actual_threads=statistics.mean(x['actual_threads'] for x in selected),
             standard_credit_lower_bound=cost, complete_cost=complete,
             full_standard_credits=cost if complete else None,
             cost_per_resolution_lower_bound=cost/successes if successes else None,
             full_cost_per_resolution=cost/successes if successes and complete else None))
    indexed = {(x['task'], x['condition'], x['guidance'], x['total_agent_capacity']): x for x in cells}
    pairs = []
    for x in cells:
        task, condition, guidance, capacity = x['task'], x['condition'], x['guidance'], x['total_agent_capacity']
        controls = []
        if condition == 'mcp_memory':
            controls.append(('added_store', indexed.get((task, 'native', guidance, capacity))))
        if guidance == 'explicit':
            controls.append(('explicit_guidance', indexed.get((task, condition, 'standard', capacity))))
        if capacity > 1:
            controls.append(('offered_capacity', indexed.get((task, condition, guidance, 1))))
        for label, control in controls:
            if control:
                pairs.append(dict(comparison=label, **contrast(x, control)))
    interactions = []
    for task in sorted({x['task'] for x in cells}):
        for capacity in [1, 2, 4, 8]:
            keys = [(task, c, g, capacity) for c, g in
                    [('mcp_memory','explicit'), ('native','explicit'), ('mcp_memory','standard'), ('native','standard')]]
            if not all(k in indexed for k in keys):
                continue
            a, b, c, d = [indexed[k] for k in keys]
            interactions.append(dict(task=task, capacity=capacity,
                success_difference_in_differences=int(a['verified_source'])-int(b['verified_source'])-int(c['verified_source'])+int(d['verified_source']),
                attempt_seconds_difference_in_differences=a['wall_seconds']-b['wall_seconds']-c['wall_seconds']+d['wall_seconds'],
                full_credit_difference_in_differences=(a['full_standard_credits']-b['full_standard_credits']-c['full_standard_credits']+d['full_standard_credits'])
                    if all(x['inference_accounting_complete'] for x in [a,b,c,d]) else None))
    result = dict(at=datetime.now(timezone.utc).isoformat(), planned=len(protocol['assignments']),
                  completed=len(cells), complete=(root/'completion.json').exists(),
                  cells=cells, groups=summaries, pairs=pairs, interactions=interactions,
                  subscription_cash_expense=None,
                  limitations=['Five admitted repositories; one attempt per cell; descriptive paired evidence',
                               'Capacity intervention does not force an exact actual worker count',
                               'Timing includes failed/stopped runs; not success-only time',
                               'Unknown usage is never zero; overlapping cost bounds do not rank totals',
                               'Primary source-only quality differs from secondary artifact-policy flags',
                               'Peer exposure is not proof of causal verified reuse'])
    output.mkdir(parents=True, exist_ok=False)
    (output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    fields = ['task','condition','guidance','total_agent_capacity','verified_source',
              'normally_completed_and_verified','wall_seconds','actual_threads',
              'inference_accounting_complete','standard_credit_lower_bound','full_standard_credits']
    with (output/'cells.csv').open('w') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for cell in cells:
            writer.writerow({k:cell[k] for k in fields})
    print(json.dumps(dict(completed=len(cells), complete=result['complete'], groups=summaries)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--protocol',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    analyze(args.root.resolve(),args.protocol.resolve(),args.output.resolve())
