"""Read-only response reconciliation; scenarios are never actual account charges."""
import argparse
from collections import defaultdict
from datetime import datetime
import json
from pathlib import Path
import sys

from smallville_native_mechanism import GLOBAL, HERE
from cost_context_study import REPO, price
from native_jsonl import records, validate_native_completion
from workspace import Store
from capture_objects import read_capture

KEYS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens')
RATES = {
    'gpt-6-luna': dict(fresh_input_per_million=2.5, cached_input_per_million=.25, output_per_million=12.5),
    'gpt-6.1-sol': dict(fresh_input_per_million=50, cached_input_per_million=2.5, output_per_million=250),
}


def measure(root, output, capture_root, *, diagnostic=False, standalone=False, reference_results=None):
    if output.exists():
        raise ValueError('Preserve immutable measurements')
    if (root / 'continuation-started.json').exists() and not any(
            (root / name).exists() for name in ('continuation-complete.json', 'continuation-stopped.json')):
        raise ValueError('Active continuation cannot be finalized')
    if not any((root / name).exists() for name in ('complete.json', 'stopped.json', 'continuation-complete.json')):
        raise ValueError('Active experiment cannot be finalized')
    captured = {}
    for p in capture_root.glob('*.json'):
        c = read_capture(p)
        for ident in c.get('response_ids', []):
            if ident in captured:
                raise ValueError('Duplicate capture')
            captured[ident] = c
    store = Store(REPO / 'work/security/workspace', Path.home() / '.codex', 'http://localhost:3000')
    store.scan()
    if standalone:
        cells = [(root, p.parent) for p in root.glob('solver/agent.jsonl')]
        cells += [(root, p.parent) for p in root.glob('maintenance/call-*/agent.jsonl')]
    elif diagnostic:
        cells = [(GLOBAL / name, cell) for name in ('smallville-luna-mechanism-002', 'smallville-luna-mechanism-004')
                 for cell in (GLOBAL / name).glob('*/call-*') if (cell / 'complete.json').exists()]
    else:
        cells = [(root, p.parent) for p in root.glob('*/task-*/solver/agent.jsonl')]
        cells += [(root, p.parent) for p in root.glob('*/maintenance/call-*/agent.jsonl')]
    measured = []
    used = set()
    for parent, cell in cells:
        sid = validate_native_completion(cell)
        with store.connection() as db:
            native = [dict(r) for r in db.execute(
                "SELECT id,usage FROM events WHERE session_id=? AND kind='generation'", (sid,))]
        if not native:
            raise ValueError('Missing native responses')
        responses = []
        aux_ids = []
        for row in native:
            ident = row['id'].split(':response:', 1)[1]
            if ident in used:
                raise ValueError('Response counted twice')
            used.add(ident)
            c = captured[ident]
            if c['status'] != 200 or c.get('response_truncated') or c['original_request_sha256'] != c['forwarded_request_sha256']:
                raise ValueError('Incomplete or transformed capture')
            end = next(e['response'] for e in c['response']['sse_events']
                       if e.get('type') == 'response.completed' and e['response']['id'] == ident)
            u = end['usage']
            transport = dict(input_tokens=u['input_tokens'],
                cached_input_tokens=u.get('input_tokens_details', {}).get('cached_tokens', 0),
                output_tokens=u['output_tokens'], total_tokens=u['total_tokens'])
            observed = json.loads(row['usage'])
            if transport != {k: observed[k] for k in KEYS}:
                raise ValueError('Native/transport mismatch')
            model = end['model']
            if model not in RATES:
                raise ValueError('Unexpected response model: ' + model)
            if any(x.get('type') == 'compaction_trigger' for x in c['request'].get('input', [])):
                aux_ids.append(ident)
            responses.append(dict(id=ident, usage=transport, model=model,
                                  credit_rate_scenario=price(transport, RATES[model])))
        usage = {k: sum(r['usage'][k] for r in responses) for k in KEYS}
        ordinary = {k: sum(r['usage'][k] for r in responses if r['id'] not in aux_ids) for k in KEYS}
        cli = next(r['usage'] for r in records(cell) if r.get('type') == 'turn.completed')
        if any(cli[k] != ordinary[k] for k in KEYS[:3]):
            raise ValueError('Native/CLI mismatch')
        relative = cell.relative_to(parent)
        arm = 'diagnostic_overhead' if diagnostic or standalone else relative.parts[0]
        role = 'solver' if cell.name == 'solver' else 'maintenance'
        process_receipt = cell / 'completion.json'
        if process_receipt.exists():
            wall = json.loads(process_receipt.read_text())['elapsed_seconds']
        elif (cell / 'recovery-verified.json').exists():
            if not json.loads((cell / 'recovery-verified.json').read_text())['native_cli_capture_reconciled']:
                raise ValueError('Unverified recovered response')
            wall = None  # Missing process lifecycle is never invented from response timing.
        else:
            raise ValueError('Missing process receipt without registered recovery evidence')
        measured.append(dict(cell=str(cell), arm=arm, role=role, session_id=sid,
            usage=usage, responses=responses, credit_rate_scenario=sum(r['credit_rate_scenario'] for r in responses),
            native_cli_transport_reconciled=True,
            started_at=json.loads((cell / 'started.json').read_text())['at'],
            wall_seconds=wall))
    totals = {}
    for arm in sorted({x['arm'] for x in measured}):
        rows = [r for r in measured if r['arm'] == arm]
        totals[arm] = dict(usage={k: sum(r['usage'][k] for r in rows) for k in KEYS},
            credit_rate_scenario=sum(r['credit_rate_scenario'] for r in rows),
            solver_scenario=sum(r['credit_rate_scenario'] for r in rows if r['role'] == 'solver'),
            maintenance_scenario=sum(r['credit_rate_scenario'] for r in rows if r['role'] == 'maintenance'),
            sum_cli_process_wall_seconds_nonadditive=(sum(r['wall_seconds'] for r in rows)
                if all(r['wall_seconds'] is not None for r in rows) else None),
            solver_cli_wall_seconds=(sum(r['wall_seconds'] for r in rows if r['role'] == 'solver')
                if all(r['wall_seconds'] is not None for r in rows if r['role'] == 'solver') else None),
            maintenance_cli_wall_seconds=(sum(r['wall_seconds'] for r in rows if r['role'] == 'maintenance')
                if all(r['wall_seconds'] is not None for r in rows if r['role'] == 'maintenance') else None),
            missing_process_lifecycle_receipts=sum(r['wall_seconds'] is None for r in rows))
    progress_path = root / ('continuation-progress.json' if (root / 'continuation-progress.json').exists() else 'progress.json')
    progress = [] if diagnostic or standalone else json.loads(progress_path.read_text())
    reference = json.loads(reference_results.read_text()) if reference_results else None
    paired = []
    if not diagnostic and not standalone:
        for arm in totals:
            assignments = sorted((x for x in progress if x['arm'] == arm), key=lambda x: x['index'])
            solver_starts = {x['index']: next(r['started_at'] for r in measured
                if r['session_id'] == x['session_id'] and r['role'] == 'solver') for x in assignments}
            for i, assignment in enumerate(assignments):
                start = solver_starts[assignment['index']]
                end = solver_starts[assignments[i + 1]['index']] if i + 1 < len(assignments) else None
                attributed = [r for r in measured if r['arm'] == arm and
                    r['started_at'] >= start and (end is None or r['started_at'] < end)]
                paired.append(dict(task=assignment['task'], arm=arm, passed=assignment['passed'],
                    credit_rate_scenario=sum(r['credit_rate_scenario'] for r in attributed),
                    solver_scenario=sum(r['credit_rate_scenario'] for r in attributed if r['role'] == 'solver'),
                    maintenance_scenario=sum(r['credit_rate_scenario'] for r in attributed if r['role'] == 'maintenance'),
                    native_processes=len(attributed)))
            if abs(sum(x['credit_rate_scenario'] for x in paired if x['arm'] == arm)
                   - totals[arm]['credit_rate_scenario']) > 1e-10:
                raise ValueError('Unattributed maintenance or solver cost')
    for arm, total in totals.items():
        assignments = [x for x in progress if x['arm'] == arm]
        total['assignments'] = len(assignments)
        total['passes'] = sum(x['passed'] for x in assignments)
        if not diagnostic and not standalone:
            baseline_total = totals.get('file_search') or (reference or {}).get('totals', {}).get('file_search')
            if baseline_total is None:
                raise ValueError('Explicit matched source-search reference required')
            total['reduction_vs_files'] = 1 - total['credit_rate_scenario'] / baseline_total['credit_rate_scenario']
            base = {x['task']: x for x in paired if x['arm'] == 'file_search'}
            if reference:
                for x in reference['per_task']:
                    if x['arm'] == 'file_search':
                        base.setdefault(x['task'], x)
            current = [x for x in paired if x['arm'] == arm]
            total['paired_cost_wins_vs_files'] = sum(x['credit_rate_scenario'] < base[x['task']]['credit_rate_scenario'] for x in current)
            total['matched_control_successes_lost'] = sum(base[x['task']]['passed'] and not x['passed'] for x in current)
            total['development_gate_passed'] = (len(current) == 8 and
                total['matched_control_successes_lost'] == 0 and
                total['reduction_vs_files'] >= .1 and total['paired_cost_wins_vs_files'] >= 5)
    embeddings = [json.loads(line) for parent in ({p for p, _ in cells} if diagnostic else [root])
                  for p in parent.rglob('embedding-inferences.jsonl') for line in p.read_text().splitlines()]
    result = dict(id=root.name, completed=root.joinpath('complete.json').exists() or root.joinpath('continuation-complete.json').exists(),
        cells=measured, per_task=paired, totals=totals, responses=len(used),
        local_embedding_operations=len(embeddings), local_embedding_seconds=sum(x['seconds'] for x in embeddings),
        rates_checked_at='2026-11-09', rate_source='https://learn.chatgpt.com/docs/pricing',
        cash_expense=None, actual_account_credits=None, quota_saving=None,
        scope='Diagnostic/research overhead' if diagnostic or standalone else 'Adapted HumanEval-derived development coding comparison; see protocol for full-native versus memory-ablation scope',
        accounting='All unique native responses and maintenance included; cached input is a subset of input. Research/diagnostics separate. Local embedding monetary cost and parent implementation overhead unknown.')
    result['timing_accounting'] = ('CLI process lifetimes, not native item.duration operation runtime or pure model latency. '
        'Synchronous TE sidecalls overlap their parent solver process; do not add parent/child wall time as task latency. '
        'No speedup claim. Source receipt timestamps and native tool runtimes remain separate raw evidence.')
    if (root / 'continuation-complete.json').exists():
        result['operational_continuation'] = json.loads((root / 'continuation-complete.json').read_text())
        result['late_seal_recovery_assignments'] = [dict(task=x['task'], arm=x['arm']) for x in progress if x.get('late_seal_recovery')]
    if reference_results:
        result['reference_results'] = str(reference_results)
        result['reference_scope'] = 'Earlier matched tasks/interface, separate later-period development arm; not randomized simultaneous assignment or independent validation.'
    with output.open('x') as f:
        json.dump(result, f, indent=2)
    print(json.dumps({k: result[k] for k in ('id', 'completed', 'responses', 'totals')}, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--capture-root', type=Path, default=Path('/tmp/ttgl-luna-tokeneconomizer-captures-002'))
    p.add_argument('--diagnostic', action='store_true')
    p.add_argument('--standalone', action='store_true')
    p.add_argument('--reference-results', type=Path)
    a = p.parse_args()
    measure(a.root, a.output, a.capture_root, diagnostic=a.diagnostic, standalone=a.standalone,
            reference_results=a.reference_results)
