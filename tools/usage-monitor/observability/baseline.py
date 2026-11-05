#!/usr/bin/env python3
"""Read-only, metadata-only baseline from one native Codex rollout. No inference."""
import argparse
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('ttgl_bridge', Path(__file__).resolve().parents[1] / 'langfuse/bridge.py')
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)
FIELDS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'reasoning_output_tokens', 'total_tokens')


def summarize(path):
    meta, tools, bad = bridge.tool_records(path)
    responses = {}
    conflicts = set()
    cumulative = None
    native_cumulative = None
    last = None
    for _, record in bridge.monitor.lines(path):
        if not record:
            continue
        payload = record.get('payload') or {}
        timestamp = record.get('timestamp')
        if timestamp and timestamp < meta.get('timestamp', ''):
            continue
        if payload.get('thread_id') and payload['thread_id'] != meta['id']:
            continue
        last = timestamp or last
        if record.get('type') == 'event_msg' and payload.get('type') == 'token_count':
            cumulative = (payload.get('info') or {}).get('total_token_usage')
        if record.get('type') != 'token_usage_record':
            continue
        ident = payload.get('response_id')
        usage = payload.get('usage')
        if not ident or not isinstance(usage, dict):
            continue
        if isinstance(payload.get('thread_token_usage'), dict):
            native_cumulative = payload['thread_token_usage']
        counts = {k: usage.get(k) for k in FIELDS}
        if any(not isinstance(v, int) or isinstance(v, bool) or v < 0 for v in counts.values()):
            conflicts.add(ident)
            continue
        if ident in responses and responses[ident]['usage'] != counts:
            conflicts.add(ident)
        responses[ident] = {'response_id': ident, 'turn_id': payload.get('turn_id'), 'timestamp': timestamp, 'usage': counts}
    for ident in conflicts:
        responses.pop(ident, None)
    totals = {k: sum(r['usage'][k] for r in responses.values()) for k in FIELDS}
    def residual_against(counter):
        return {k: totals[k] - counter[k] for k in FIELDS} if counter and all(isinstance(counter.get(k), int) for k in FIELDS) else None
    residual = residual_against(native_cumulative or cumulative)
    groups = collections.defaultdict(list)
    for tool in tools:
        if tool['native_runtime_ns'] is not None:
            groups[tool['operation']].append(tool['native_runtime_ns'] / 1e9)
    def quantile(values, fraction):
        values = sorted(values)
        at = (len(values) - 1) * fraction
        lo = int(at)
        return values[lo] + (values[min(lo + 1, len(values) - 1)] - values[lo]) * (at - lo)
    runtime = [{'operation': name, 'count': len(values), 'runtime_seconds_sum': sum(values),
                'p50_seconds': quantile(values, .5), 'p95_seconds': quantile(values, .95),
                'max_seconds': max(values)} for name, values in groups.items()]
    runtime.sort(key=lambda row: -row['runtime_seconds_sum'])
    return {'schema': 'ttgl-native-baseline-v1', 'session_id': meta['id'], 'cli_version': meta.get('cli_version'),
            'started_at': meta.get('timestamp'), 'observed_through': last,
            'source_kind': 'native_transcript', 'source_snapshot_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'responses': list(responses.values()), 'unique_responses': len(responses), 'usage': totals,
            'cache_fraction': totals['cached_input_tokens'] / totals['input_tokens'] if totals['input_tokens'] else None,
            'fresh_input_tokens': totals['input_tokens'] - totals['cached_input_tokens'],
            'cumulative_residual': residual, 'conflicting_response_ids': sorted(conflicts), 'invalid_lines': bad,
            'reconciliation_basis': 'token_usage_record.thread_token_usage' if native_cumulative else 'event_msg.token_count',
            'legacy_counter_residual': residual_against(cumulative),
            'tool_count': len(tools), 'tools_with_native_runtime': sum(t['native_runtime_ns'] is not None for t in tools),
            'tool_runtime': runtime, 'actual_cost': None, 'task_outcome': None,
            'limitations': ['Active-session snapshot; not whole-task completion.',
                            'Cached input and reasoning output are subsets; never add them to totals.',
                            'Tool runtimes can overlap; their sum is not task latency or agent-blocking time.',
                            'Model latency, time to first token, raw wire pairs and retry attempts need additional capture.',
                            'No raw prompts, tool arguments/results, reasoning, credentials or account balances exported.',
                            'No savings or quality improvement established.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rollout', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # Freeze the active file before parsing/hashing; originals remain unchanged.
    import tempfile
    raw = args.rollout.read_bytes()
    raw = raw[:raw.rfind(b'\n') + 1]
    with tempfile.TemporaryDirectory(prefix='ttgl-baseline-') as directory:
        snapshot = Path(directory) / 'snapshot.jsonl'
        snapshot.write_bytes(raw)
        report = summarize(snapshot)
    args.output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as output:
        json.dump(report, output, indent=2)
        output.write('\n')
    print(json.dumps({k: report[k] for k in ('unique_responses', 'usage', 'cache_fraction', 'cumulative_residual', 'tool_count', 'tools_with_native_runtime')}))


if __name__ == '__main__':
    main()
