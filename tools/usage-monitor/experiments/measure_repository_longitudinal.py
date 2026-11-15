"""Immutable native/CLI/capture accounting; no hidden grades during generation.

Active snapshots are lower bounds. Compare only complete matched task blocks;
unstarted, active or uncertain calls never become zero inference costs.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path

from measure_repository_memory import (REPO, KEYS, RATES, Store, capture_index, one_cell, read_capture)


def namespace(root, state):
    return root / 'namespaces' / state['repository'].replace('/', '__') / state['lineage'] / state['arm']


def allocations(root, state):
    cell = Path(state['cell'])
    result = [('solver', cell / 'solver')] if (cell / 'solver/agent.jsonl').exists() else []
    for role in ('preparation', 'reflection'):
        result += [(role, p.parent) for p in sorted(cell.glob(role + '/call-*/agent.jsonl'))]
    if state['arm'] in ('mem0_luna', 'graphiti_luna'):
        calls = namespace(root, state) / 'backend/maintenance'
        for phase in ('query', 'update'):
            complete = cell / (phase + '-backend/complete.json')
            if complete.exists():
                operation = json.loads(complete.read_text())
                result += [(phase, calls / f'call-{index + 1:03d}')
                           for index in range(operation['call_start'], operation['call_end'])]
            else:
                started = cell / (phase + '-backend/started.json')
                if started.exists():
                    # Registered worker is sequential and stops at its first
                    # ambiguity. Thus an unfinished operation is the last in
                    # this pool; retain completed and uncertain calls after it.
                    stamp = datetime.fromisoformat(json.loads(started.read_text())['at'])
                    for p in sorted(calls.glob('call-*/intent.json')):
                        at = datetime.fromisoformat(json.loads(p.read_text())['at'])
                        if at >= stamp and (p.parent / 'agent.jsonl').exists():
                            result.append((phase, p.parent))
    return result


def measure(root, capture_root, output, active):
    if output.exists():
        raise ValueError('Never overwrite an accounting snapshot')
    if not active and not (root / 'complete.json').exists():
        raise ValueError('Final accounting requires study completion')
    states = json.loads((root / 'assignments.json').read_text())
    captured, stream_unknown = capture_index(capture_root)
    unknown_by_sid = defaultdict(list)
    long_unknown = []
    for row in stream_unknown:
        capture = read_capture(capture_root / row['capture'])
        sid = capture.get('request', {}).get('prompt_cache_key')
        if sid:
            unknown_by_sid[sid].append(row)
        if str(root) in json.dumps(capture.get('request')):
            long_unknown.append(row)
    store = Store(REPO / 'work/security/workspace', Path.home() / '.codex', 'http://localhost:3000')
    calls, rows, used, unknown = [], [], set(), []
    for state in states:
        cell = Path(state['cell'])
        generation_done = (cell / 'generation-complete.json').exists()
        if not cell.exists():
            unknown.append(dict(instance_id=state['instance_id'], arm=state['arm'],
                 status='unstarted_or_active_or_failed', full_credit_scenario=None))
            continue
        local, errors = [], []
        for role, call in allocations(root, state):
            tentative = set(used)
            try:
                value = one_cell(store, call, captured, tentative)
                if unknown_by_sid[value['session_id']]:
                    raise ValueError('Additional failed/truncated HTTP attempt; full inference unknown')
                used = tentative
                local.append(dict(instance_id=state['instance_id'], arm=state['arm'], role=role, **value))
            except (ValueError, KeyError, StopIteration) as error:
                if not active:
                    raise
                errors.append(dict(role=role, cell=str(call), reason=str(error), inference_cost=None))
        calls += local
        usage = {k: sum(c['usage'][k] for c in local) for k in KEYS}
        row = dict(**state, completed_generation=generation_done, fully_reconciled=generation_done and not errors,
             observed_usage=usage, observed_credit_scenario_lower_bound=sum(c['credit_rate_scenario'] for c in local),
             full_credit_scenario=sum(c['credit_rate_scenario'] for c in local) if generation_done and not errors else None,
             roles={role: sum(c['credit_rate_scenario'] for c in local if c['role'] == role)
                    for role in sorted({c['role'] for c in local})}, unresolved_calls=errors)
        rows.append(row)
        unknown += [dict(instance_id=state['instance_id'], arm=state['arm'], **e) for e in errors]
        if not generation_done:
            unknown.append(dict(instance_id=state['instance_id'], arm=state['arm'],
                 status='started_generation_or_maintenance_not_complete', full_credit_scenario=None))
    arms = sorted({s['arm'] for s in states})
    matched = [iid for iid in sorted({s['instance_id'] for s in states})
               if {r['arm'] for r in rows if r['instance_id'] == iid and r['fully_reconciled']} == set(arms)]
    totals = {}
    for arm in arms:
        group = [r for r in rows if r['arm'] == arm and r['instance_id'] in matched]
        totals[arm] = dict(matched_tasks=len(group), usage={k: sum(r['observed_usage'][k] for r in group) for k in KEYS},
             matched_task_credit_scenario=sum(r['full_credit_scenario'] for r in group),
             maintenance_scenario=sum(sum(v for role, v in r['roles'].items() if role != 'solver') for r in group))
    # Hidden labels are read only after the whole registered generation/replay.
    grades = json.loads((root / 'complete.json').read_text())['grades'] if (root / 'complete.json').exists() else None
    value = dict(at=datetime.now(timezone.utc).isoformat(), active_snapshot=active,
         completed_generations=sum(r['completed_generation'] for r in rows), registered_assignments=len(states), unique_reconciled_responses=len(used),
         completed_calls=calls, completed_assignments=rows, unstarted_active_or_unknown=unknown,
         matched_completed_task_ids=matched, matched_completed_totals=totals,
         hidden_grades=grades, study_unknown_http_attempts=long_unknown,
         unrelated_unknown_http_attempts_not_task_cost=[x for x in stream_unknown if x not in long_unknown],
         accounting_complete=not active and not unknown and not long_unknown,
         total_observed_scenario_lower_bound=sum(c['credit_rate_scenario'] for c in calls),
         current_snapshot_is_lower_bound=active or bool(unknown) or bool(long_unknown),
         rates=RATES, rates_date='2026-11-10', source_url='https://learn.chatgpt.com/docs/pricing',
         actual_cash_expense=None, actual_account_credits=None, quota_saving=None, local_compute_monetary_cost=None,
         research_overhead='Separate native/TE/Smallville preflights, parent and implementation overhead not included here and not assumed zero; no net first-use claim',
         timing='Process wall times include tools/waits; concurrent diagnostics/preparation prevent clean causal speed comparisons')
    with output.open('x') as handle:
        json.dump(value, handle, indent=2)
    print(json.dumps(dict(completed=sum(r['completed_generation'] for r in rows), registered=len(states), matched_tasks=len(matched),
                          responses=len(used), accounting_complete=value['accounting_complete'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--capture-root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--active', action='store_true')
    args = parser.parse_args()
    measure(args.root.resolve(), args.capture_root.resolve(), args.output.resolve(), args.active)
