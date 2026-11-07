#!/usr/bin/env python3
"""Reconcile native compaction from response IDs, not reset context counters."""
import argparse
import collections
import json
from pathlib import Path
from cost_context_study import PRICING, price

KEYS = ('input_tokens','cached_input_tokens','output_tokens','total_tokens')


def response_usage(value):
    return dict(input_tokens=value['input_tokens'],
                cached_input_tokens=value.get('input_tokens_details',{}).get('cached_tokens',0),
                output_tokens=value['output_tokens'], total_tokens=value['total_tokens'])


def measure(root):
    if (root/'results.json').exists():
        raise ValueError('Preserve prior measurement')
    complete = json.loads((root/'complete.json').read_text())
    native = json.loads((root/'native-events.json').read_text())
    captures = []
    for path in (root/'captures').glob('*.json'):
        record = json.loads(path.read_text())
        if record.get('path','').endswith('/models'):
            continue
        if record.get('state') != 'complete' or record.get('status') != 200 or record.get('response_truncated'):
            raise ValueError('Incomplete, failed or truncated native transport evidence')
        response = record['response']
        if 'sse_events' in response:
            completions = [e['response'] for e in response['sse_events'] if e.get('type')=='response.completed']
            if len(completions)!=1:
                raise ValueError('Expected one completed response per request')
            response = completions[0]
        captures.append(dict(id=response['id'],usage=response_usage(response['usage']),
                             path=record['path'],started_ns=record['started_ns']))
    captures.sort(key=lambda x:x['started_ns'])
    if len(captures)!=3 or len({c['id'] for c in captures})!=3:
        raise ValueError('Registered three operations not uniquely accounted')
    native_ids = {r['id'].split(':response:',1)[1]:r for r in native}
    if len(native_ids)!=len(native) or set(native_ids)!={c['id'] for c in captures}:
        raise ValueError('Native/transport response ID mismatch')
    for phase, captured in zip(('seed','compact','followup'),captures):
        captured['phase'] = phase
        actual = json.loads(native_ids[captured['id']]['usage'])
        if {k:actual[k] for k in KEYS} != captured['usage']:
            raise ValueError('Native/transport usage mismatch')
    notifications = []
    for line in (root/'rpc.jsonl').read_bytes().split(b'\n'):
        if line.strip():
            notifications.append(json.loads(line))
    messages = [(r.get('phase'),r.get('message',{}).get('params',{}).get('item',{}))
                for r in notifications if r.get('message',{}).get('method')=='item/completed']
    answers = {phase:item['text'] for phase,item in messages if item.get('type')=='agentMessage'}
    no_tools = all(item.get('type') in ('agentMessage','reasoning','contextCompaction') for _,item in messages)
    quality = answers.get('seed')=='READY' and answers.get('followup')=='R7Q2' and no_tools
    usage = {k:sum(c['usage'][k] for c in captures) for k in KEYS}
    updates = [r['message']['params']['tokenUsage'] for r in notifications
               if r.get('message',{}).get('method')=='thread/tokenUsage/updated']
    final = updates[-1]['total']
    counter_names = dict(input_tokens='inputTokens',cached_input_tokens='cachedInputTokens',
                         output_tokens='outputTokens',total_tokens='totalTokens')
    if any(usage[k]!=final[v] for k,v in counter_names.items()):
        raise ValueError('Final cumulative thread counter mismatch')
    rates = json.loads(PRICING.read_text())['primary_scenario']
    cost = sum(price(c['usage'],rates) for c in captures)
    reset = any(u['last'].get('inputTokens')==0 and u['last'].get('outputTokens')==0
                and u['last'].get('totalTokens',0)>0 for u in updates)
    remote = any(c['path'].endswith('/compact') for c in captures)
    cell = dict(case='durable-fact-compaction',condition='native_compaction',session_id=complete['session_id'],
                native_response_ids=[r['id'] for r in native],native_reconciled=True,usage=usage,cost=cost,
                quality=dict(passed=quality,kind='Synthetic retained-fact and no-tools mechanism checks'))
    public = dict(id=root.name,native_compaction_passed=quality,remote_compact_endpoint_exercised=remote,
                  registered_remote_endpoint_gate_passed=quality and remote,
                  actual_branch='remote_compact_endpoint' if remote else 'local_compaction_via_responses',
                  unique_responses=3,native_transport_cumulative_reconciled=True,
                  reset_context_size_notification_present=reset,usage=usage,credit_rate_scenario=cost,
                  phases=[{k:v for k,v in c.items() if k not in ('id','started_ns')} for c in captures],
                  cash_cost=None,note='Explicit compaction inference is included. Context-size reset notifications are not zero-cost responses. A three-operation canary is not a task-quality or savings comparison.')
    result = dict(**public,cells=[cell],protocol=json.loads((root/'protocol.json').read_text()))
    (root/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    target=Path(__file__).resolve().parents[1]/'studies'/(root.name.replace('canary-','results-')+'.json')
    with target.open('x') as stream:
        json.dump(public,stream,indent=2)
        stream.write('\n')
    print(json.dumps(public))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    measure(parser.parse_args().directory)
