#!/usr/bin/env python3
"""Audit actual grade/patch joins and recompute native event-counter totals."""
import argparse
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ttgl import benchmark, personal

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--study-dir', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--allow-partial', action='store_true')
args = parser.parse_args()
study = args.study_dir.resolve()
design, _ = benchmark.load_design(study)
grades = json.loads((study/'grades.json').read_text())
rates = json.loads((study/'rate-scenario.json').read_text())
records, missing, tool_types = [], [], Counter()
for assignment in design['assignment_order']:
    arm, key = assignment['arm'], assignment['instance_id']
    run = study/'runs'/arm/key
    if not (run/'manifest.json').exists() or not grades.get(arm,{}).get(key):
        missing.append(assignment)
        continue
    manifest = json.loads((run/'manifest.json').read_text())
    patch = json.loads((study/'patches'/arm/(key+'.json')).read_text())
    if patch['manifest_sha256'] != benchmark.digest(run/'manifest.json'):
        raise ValueError('Patch manifest binding changed')
    report = Path(grades[arm][key])
    if not report.is_absolute():
        report = study/report
    resolved, report_hash, evidence = benchmark.read_grade(report,key,patch['patch_sha256'])
    requests, responses = {}, {}
    sums = {field:0 for field in personal.USAGE_FIELDS}
    per_model = {}
    context_violations = []
    for line in (run/'events.jsonl').read_text().splitlines():
        event = json.loads(line)
        if event['event'] not in ('request','response'):
            continue
        bucket = requests if event['event']=='request' else responses
        if event['request_id'] in bucket:
            raise ValueError('Repeated invocation identity')
        bucket[event['request_id']] = event
        if event['event'] != 'response':
            continue
        model = per_model.setdefault(event['model'],{field:0 for field in personal.USAGE_FIELDS})
        for field in personal.USAGE_FIELDS:
            value = event['usage_delta'].get(field)
            for target in (sums,model):
                target[field] = None if value is None or target[field] is None else target[field]+value
        for tool in event.get('tool_events',[]):
            tool_types[tool['type']] += 1
            if event['kind'] in ('expert','router'):
                context_violations.append({'request_id':event['request_id'],'type':tool['type']})
    if set(requests) != set(responses):
        raise ValueError('Unreconciled request/response identities')
    if sums != manifest['usage']:
        raise ValueError('Native event deltas do not reconcile to finalized totals')
    if set(per_model) != set(manifest['usage_by_model']):
        raise ValueError('An invoked model is missing from finalized accounting')
    for model,usage in per_model.items():
        if manifest['usage_by_model'][model]['usage'] != usage:
            raise ValueError('Per-model native totals do not reconcile')
    known = all(type(usage[k]) is int for usage in per_model.values()
                for k in ('input_tokens','cached_input_tokens','output_tokens'))
    cost = Decimal(0) if known else None
    if known:
        for model,usage in per_model.items():
            rate = rates['models'][model]
            uncached = usage['input_tokens']-usage['cached_input_tokens']
            if uncached < 0:
                raise ValueError('Cache subset exceeds input')
            cost += (Decimal(uncached)*Decimal(str(rate['input_per_million']))
                     +Decimal(usage['cached_input_tokens'])*Decimal(str(rate['cached_input_per_million']))
                     +Decimal(usage['output_tokens'])*Decimal(str(rate['output_per_million'])))/Decimal(1000000)
    records.append({'arm':arm,'task_id':key,'resolved':resolved,
        'native_usage_complete':known,'published_rate_scenario_usd_decimal':str(cost) if cost is not None else None,
        'context_only_role_tool_violations':context_violations,
        'manifest_sha256':benchmark.digest(run/'manifest.json'),
        'events_sha256':benchmark.digest(run/'events.jsonl'),
        'report_sha256':report_hash,'evidence':evidence})
if missing and not args.allow_partial:
    raise ValueError('Incomplete assigned study; use --allow-partial only for explicit checkpoints')
benchmark.write_new(args.output,{'status':'partial_checkpoint_audit' if missing else 'complete_study_audit',
    'assigned':len(design['assignment_order']),'audited':len(records),'missing':missing,
    'tool_event_types':dict(tool_types),'records':records,
    'context_only_role_tool_violations':sum(len(r['context_only_role_tool_violations']) for r in records),
    'design_sha256':benchmark.digest(study/'design.json'),
    'rates_sha256':benchmark.digest(study/'rate-scenario.json'),
    'script_sha256':benchmark.digest(Path(__file__)),
    'scope':'Independent event-delta sums, Decimal scenario arithmetic and exact official grade joins; not an invoice or a formal isolation proof'})
print(json.dumps({'assigned':len(design['assignment_order']),'audited':len(records),'missing':len(missing),'tool_event_types':dict(tool_types)}))
