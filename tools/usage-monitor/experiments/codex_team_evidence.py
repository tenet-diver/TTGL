#!/usr/bin/env python3
"""Audit native team counters against owned rollout records; no model calls."""
import argparse
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path

FIELDS = {
    'inputTokens': 'input_tokens', 'cachedInputTokens': 'cached_input_tokens',
    'cacheWriteInputTokens': 'cache_write_input_tokens', 'outputTokens': 'output_tokens',
    'reasoningOutputTokens': 'reasoning_output_tokens', 'totalTokens': 'total_tokens',
}


def counters(snapshots):
    """Fresh-thread counters only; refuse carry-in, resets and missing evidence."""
    previous = dict.fromkeys(FIELDS, 0)
    summed = dict.fromkeys(FIELDS, 0)
    seen, errors = set(), []
    for index, snap in enumerate(snapshots):
        total, last = snap.get('total', {}), snap.get('last', {})
        if not all(type(part.get(k)) is int and part[k] >= 0 for part in (total, last) for k in FIELDS):
            errors.append(f'missing_or_invalid_counter:{index}')
            continue
        key = tuple(total[k] for k in FIELDS)
        if key in seen:
            continue
        seen.add(key)
        for k in FIELDS:
            if total[k] - previous[k] != last[k]:
                errors.append(f'carry_reset_or_unreconciled_delta:{index}:{k}')
            summed[k] += last[k]
        if total['inputTokens'] + total['outputTokens'] != total['totalTokens']:
            errors.append(f'invalid_total:{index}')
        if total['cachedInputTokens'] > total['inputTokens'] or total['reasoningOutputTokens'] > total['outputTokens']:
            errors.append(f'invalid_subset:{index}')
        previous = dict(total)
    if not seen or previous['totalTokens'] == 0:
        errors.append('no_positive_inference_evidence')
    return dict(complete=not errors, errors=errors, distinct_snapshots=len(seen),
                total=previous if not errors else None, summed_response_usage=summed)


def audit(root):
    messages = [json.loads(s).get('message', {}) for s in (root / 'rpc.jsonl').read_text().splitlines()]
    snapshots = {}
    for message in messages:
        if message.get('method') == 'thread/tokenUsage/updated':
            params = message['params']
            snapshots.setdefault(params['threadId'], []).append(params['tokenUsage'])
    checked = {sid: counters(values) for sid, values in snapshots.items()}
    independent, parents, models = {}, {}, {}
    for file in (root / 'home/sessions').rglob('*.jsonl'):
        rows = [json.loads(s) for s in file.read_text().splitlines()]
        meta = next(r['payload'] for r in rows if r['type'] == 'session_meta')
        sid = meta['id']
        parents[sid] = meta.get('parent_thread_id')
        models[sid] = sorted({r['payload']['model'] for r in rows if r['type'] == 'turn_context' and r['payload'].get('model')})
        values = [r['payload']['info'] for r in rows if r['type'] == 'event_msg'
                  and r['payload'].get('type') == 'token_count' and r['payload'].get('info')]
        independent[sid] = counters([{
            'total': {k: v['total_token_usage'].get(s) for k, s in FIELDS.items()},
            'last': {k: v['last_token_usage'].get(s) for k, s in FIELDS.items()},
        } for v in values])
    ids = set(checked) | set(independent)
    reconciled = bool(ids) and set(checked) == set(independent) and all(
        checked[s]['complete'] and independent[s]['complete'] and
        checked[s]['total'] == independent[s]['total'] for s in ids)
    manifest = json.loads((root / 'manifest.json').read_text())
    sid = json.loads((root / 'thread.json').read_text())['thread']['id']
    children = [s for s in parents if parents[s] == sid]
    actor = root / 'actor'
    witnesses = [actor / n for n in manifest.get('expected_witnesses',
        ['child.txt' if manifest['total_agent_limit'] > 1 else 'parent.txt'])]
    # The MCP diagnostic explicitly asks for the observation plus a newline;
    # public.txt itself ends in a newline. Preserve that original task contract.
    expected_bytes = (actor / 'public.txt').read_bytes() + (b'\n' if manifest.get('memory_entry') else b'')
    checks = {
        'native_shell_boundary_passed': json.loads((root / 'sandbox-check.json').read_text())['passed'],
        'protected_fixture_exists_outside_actor': (root / 'protected.txt').is_file(),
        'independent_final_file_match': all(f.is_file() and f.read_bytes() == expected_bytes for f in witnesses),
        'expected_direct_child_count': len(children) == manifest.get('expected_children', int(manifest['total_agent_limit'] > 1)),
        'all_owned_thread_counters_reconcile': reconciled,
        'same_model_observed_in_all_threads': bool(models) and all(v == ['gpt-6.1-sol'] for v in models.values()),
    }
    memory_calls = {}
    if manifest.get('memory_entry'):
        for message in messages:
            if message.get('method') != 'item/completed':
                continue
            params, item = message['params'], message['params']['item']
            if item.get('type') == 'mcpToolCall' and item.get('server') == 'team_memory':
                memory_calls.setdefault(params['threadId'], []).append(item)
        expected_note = (actor / 'public.txt').read_text()
        peer_reads = []
        for child in children:
            items = memory_calls.get(child, [])
            reads = [i for i in items if i.get('tool') in ('open_nodes', 'read_graph', 'search_nodes') and i.get('status') == 'completed']
            writes = [i for i in items if i.get('tool') == 'create_entities' and i.get('status') == 'completed']
            peer_reads.append(bool(reads) and bool(writes))
        entities = [json.loads(s) for s in (root / 'memory/knowledge.jsonl').read_text().splitlines() if s]
        entities = [e for e in entities if e.get('type') == 'entity']
        expected_names = {'parent:probe', *(f'worker:{i}' for i in range(len(children)))}
        checks['each_child_observed_memory_read_and_write'] = bool(children) and all(peer_reads)
        checks['all_shared_records_preserve_exact_observation'] = (
            {e['name'] for e in entities} == expected_names and
            all(e['observations'] == [expected_note] for e in entities))
    result = dict(
        audited_at=datetime.now(timezone.utc).isoformat(), kind='native_mechanism_diagnostic',
        checks=checks, passed=all(checks.values()), parent_thread=sid, children=children,
        counters_by_thread=checked, rollout_counters_by_thread=independent, models=models,
        audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        memory_call_tools_by_thread={s: [i['tool'] for i in items] for s, items in memory_calls.items()},
        total_native_usage={k: sum(checked[s]['total'][k] for s in ids) for k in FIELDS} if reconciled else None,
        parent_turn=json.loads((root / 'completed.json').read_text())['turn'],
        subscription_cash=None, estimated_credits=None,
        limits=['Not a coding-task result or scalability measurement',
                'Configured capacity/observed threads do not prove simultaneous model-request concurrency',
                'Memory checks, when present, are synthetic visibility tests, not coding efficacy',
                'App-server and rollouts reconcile; no independent billing or HTTP-response ledger yet',
                'Copied parent context/tool items in child histories must not be attributed as new child actions'],
    )
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root.resolve())
    with (args.root / 'independent-audit.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: result[k] for k in ['passed', 'checks', 'total_native_usage']}))
