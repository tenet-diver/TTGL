"""Native/CLI/capture reconciliation for the repository-memory comparison.

Immutable snapshots only. An active or uncertain call has unknown total cost,
not zero. Never sum CLI/session snapshots with per-response measurements.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'observability'))
from capture_objects import read_capture
from workspace import Store
from native_jsonl import records, validate_native_completion

REPO = HERE.parents[2]
KEYS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens')
RATES = {'gpt-6.1-sol': (50, 2.5, 250), 'gpt-6-luna': (2.5, .25, 12.5)}


def credit_scenario(usage, model):
    if model not in RATES:
        raise ValueError('Unregistered rate/model: ' + model)
    fresh, cached, output = RATES[model]
    if not 0 <= usage['cached_input_tokens'] <= usage['input_tokens']:
        raise ValueError('Cached input must be a subset')
    return ((usage['input_tokens'] - usage['cached_input_tokens']) * fresh
            + usage['cached_input_tokens'] * cached + usage['output_tokens'] * output) / 1e6


def capture_index(directory):
    by_response = defaultdict(list)
    unknown = []
    for path in Path(directory).glob('*.json'):
        record = read_capture(path)
        if record.get('operation') == 'catalog':
            continue
        if record.get('status') != 200 or record.get('response_truncated'):
            unknown.append(dict(capture=path.name, status=record.get('status'),
                                inference_cost=None, reason='Incomplete/failed response; not zero'))
        for ident in record.get('response_ids', []):
            by_response[ident].append(record)
    return by_response, unknown


def one_cell(store, cell, captured, used):
    sid = validate_native_completion(cell)
    source_paths = list(store.root.joinpath('sessions').rglob('*' + sid + '*.jsonl'))
    source_paths += list(store.root.joinpath('archived_sessions').rglob('*' + sid + '*.jsonl'))
    if len(source_paths) != 1:
        raise ValueError('Missing/ambiguous native rollout: ' + sid)
    store.ingest(source_paths[0])
    with store.connection() as db:
        native = [dict(r) for r in db.execute(
            "SELECT id,usage,model FROM events WHERE session_id=? AND kind='generation'", (sid,))]
    if not native:
        raise ValueError('Missing native per-response counters')
    responses = []
    auxiliary = set()
    for row in native:
        ident = row['id'].split(':response:', 1)[1]
        if ident in used:
            raise ValueError('A native response assigned to two cells')
        used.add(ident)
        matches = captured[ident]
        if not matches:
            raise ValueError('Missing capture: ' + ident)
        expected = {key: json.loads(row['usage'])[key] for key in KEYS}
        for capture in matches:
            if (capture.get('status') != 200 or capture.get('response_truncated')
                    or capture['original_request_sha256'] != capture['forwarded_request_sha256']):
                raise ValueError('Incomplete or transformed capture')
            end = next(e['response'] for e in capture['response']['sse_events']
                       if e.get('type') == 'response.completed' and e['response']['id'] == ident)
            u = end['usage']
            observed = dict(input_tokens=u['input_tokens'],
                            cached_input_tokens=u.get('input_tokens_details', {}).get('cached_tokens', 0),
                            output_tokens=u['output_tokens'], total_tokens=u['total_tokens'])
            if observed != expected:
                raise ValueError('Native/capture usage mismatch')
            if any(v.get('type') == 'compaction_trigger' for v in capture['request'].get('input', [])):
                auxiliary.add(ident)
        responses.append(dict(id=ident, model=end['model'], usage=expected,
            credit_rate_scenario=credit_scenario(expected, end['model']),
            duplicate_deliveries_deduplicated=len(matches) - 1))
    cli = next(r['usage'] for r in records(cell) if r.get('type') == 'turn.completed')
    ordinary = {k: sum(r['usage'][k] for r in responses if r['id'] not in auxiliary) for k in KEYS}
    if any(cli[k] != ordinary[k] for k in KEYS[:3]):
        raise ValueError('CLI/native response counters mismatch')
    usage = {k: sum(r['usage'][k] for r in responses) for k in KEYS}
    receipt = cell / 'completion.json'
    if not receipt.exists():
        raise ValueError('Missing process lifecycle receipt')
    return dict(cell=str(cell), session_id=sid, usage=usage, responses=responses,
                credit_rate_scenario=sum(r['credit_rate_scenario'] for r in responses),
                cli_process_wall_seconds=json.loads(receipt.read_text())['elapsed_seconds'],
                native_cli_capture_reconciled=True)


def measure(root, capture_root, output, *, active=False):
    if output.exists():
        raise ValueError('Never overwrite an accounting snapshot')
    if not active and not any((root / name).exists() for name in ('complete.json', 'stopped.json')):
        raise ValueError('Active study cannot be finalized')
    store = Store(REPO / 'work/security/workspace', Path.home() / '.codex', 'http://localhost:3000')
    captured, unknown_http = capture_index(capture_root)
    measured, unknown_calls, used = [], [], set()
    states = json.loads((root / 'assignments.json').read_text())
    for state in states:
        cell = Path(state['cell'])
        paths = [cell / 'solver'] if (cell / 'solver/agent.jsonl').exists() else []
        paths += sorted(p.parent for p in cell.glob('backend/maintenance/call-*/agent.jsonl'))
        for call in paths:
            role = 'solver' if call.name == 'solver' else 'maintenance'
            base = dict(instance_id=state['instance_id'], arm=state['arm'], role=role)
            try:
                row = one_cell(store, call, captured, used)
            except (ValueError, KeyError, StopIteration) as error:
                if not active:
                    raise
                unknown_calls.append(dict(base, cell=str(call), usage=None, credit_rate_scenario=None,
                                          reason=str(error), status='active_or_unreconciled'))
                continue
            measured.append(dict(base, **row))
    # Grades are only read after the complete generation/replay phase; never
    # used to affect the live memory/controller or initial assignment matrix.
    grade_rows = json.loads((root / 'complete.json').read_text())['grades'] if (root / 'complete.json').exists() else []
    paired = []
    for state in states:
        rows = [r for r in measured if r['instance_id'] == state['instance_id'] and r['arm'] == state['arm']]
        unresolved = any(r['instance_id'] == state['instance_id'] and r['arm'] == state['arm'] for r in unknown_calls)
        assigned = bool((Path(state['cell']) / 'generation-complete.json').exists())
        score = next((g['passed'] for g in grade_rows if g['instance_id'] == state['instance_id'] and g['arm'] == state['arm']), None)
        paired.append(dict(instance_id=state['instance_id'], arm=state['arm'],
            generation_complete=assigned, passed=score,
            fully_reconciled=assigned and not unresolved,
            usage={k: sum(r['usage'][k] for r in rows) for k in KEYS},
            observed_credit_scenario_lower_bound=sum(r['credit_rate_scenario'] for r in rows),
            full_credit_scenario=(sum(r['credit_rate_scenario'] for r in rows) if assigned and not unresolved else None),
            solver_scenario=sum(r['credit_rate_scenario'] for r in rows if r['role'] == 'solver'),
            maintenance_scenario=sum(r['credit_rate_scenario'] for r in rows if r['role'] == 'maintenance')))
    totals = {}
    for arm in sorted({s['arm'] for s in states}):
        rows = [r for r in paired if r['arm'] == arm]
        complete = all(r['fully_reconciled'] for r in rows)
        totals[arm] = dict(assignments=len(rows), generation_complete=sum(r['generation_complete'] for r in rows),
            graded=sum(r['passed'] is not None for r in rows),
            passes=sum(r['passed'] is True for r in rows),
            usage={k: sum(r['usage'][k] for r in rows) for k in KEYS},
            observed_credit_scenario_lower_bound=sum(r['observed_credit_scenario_lower_bound'] for r in rows),
            full_credit_scenario=sum(r['full_credit_scenario'] for r in rows) if complete else None,
            solver_scenario=sum(r['solver_scenario'] for r in rows),
            maintenance_scenario=sum(r['maintenance_scenario'] for r in rows))
    value = dict(id=root.name, at=datetime.now(timezone.utc).isoformat(),
        accounting_complete=not active and not unknown_calls and not unknown_http,
        study_complete=(root / 'complete.json').exists(), source='native response/CLI/capture',
        unique_responses=len(used), measured_calls=measured, unknown_calls=unknown_calls,
        unknown_http_attempts_for_capture_stream=unknown_http, totals=totals, per_task=paired,
        current_snapshot_is_lower_bound=active or bool(unknown_calls),
        rates=RATES, rates_date='2026-11-10', source_url='https://learn.chatgpt.com/docs/pricing',
        cash_expense=None, actual_account_credits=None, quota_saving=None,
        local_compute_monetary_cost=None,
        scope='Adapted two-target frozen-history development wave; no continual-learning result.',
        excluded_overhead='Native-memory, Mem0 and Graphiti preflights plus parent research/implementation separately; not zero and not net first-use savings.',
        timing='CLI process wall times include tools/waits and are not pure inference or operation runtime. Nested maintenance time not added to parent backend-worker elapsed time.')
    with output.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')
    print(json.dumps(dict(complete=value['accounting_complete'], unique_responses=len(used),
                         unknown_calls=len(unknown_calls), totals=totals)), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--capture-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--active', action='store_true')
    args = parser.parse_args()
    measure(args.root, args.capture_root, args.output, active=args.active)
