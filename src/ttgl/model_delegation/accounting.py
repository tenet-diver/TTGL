"""Reconcile native receipts, never parent aggregate + child counters together."""
import json
from pathlib import Path
from ..personal import USAGE_FIELDS
from ..experience_routing.io import digest
FIELDS = tuple(dict.fromkeys((*USAGE_FIELDS, 'total_tokens')))


def reconcile(paths):
    records=[];seen={};response_owner={};thread_owner={};issues=[];duplicates=[]
    for path in sorted(map(Path,paths)):
        for line in path.read_text().splitlines():
            row=json.loads(line)
            if row.get('kind')!='native':continue
            key=digest([row['model'],row['thread_id'],row['raw_artifact_hash'],row['signature']])
            if key in seen:
                duplicates.append({'path':str(path),'receipt':key});continue
            seen[key]=str(path)
            ids=set(row.get('response_ids',[]))
            if any(i in response_owner for i in ids):issues.append('overlapping_native_response_ids')
            thread=(row['model'],row['thread_id'])
            if thread in thread_owner and thread_owner[thread]!=str(path):
                issues.append('same_thread_cumulative_counters_across_separate_ledgers')
            thread_owner[thread]=str(path)
            for identity in ids:response_owner[identity]=key
            if not row['delta'].get('total_tokens'):issues.append('unknown_or_nonpositive_native_usage')
            records.append({'path':str(path),'receipt':key,**{k:row[k] for k in ('model','thread_id','delta','role','purpose')}})
    def total(rows):
        return {k:None if issues or any(r['delta'].get(k) is None for r in rows) else sum(r['delta'][k] for r in rows) for k in FIELDS}
    known=[r for r in records if (r['delta'].get('total_tokens') or 0)>0]
    ambiguous=any(i!='unknown_or_nonpositive_native_usage' for i in issues)
    subtotal={k:None if ambiguous or any(r['delta'].get(k) is None for r in known)
              else sum(r['delta'][k] for r in known) for k in FIELDS}
    return {'native_receipts':len(records),'duplicates_excluded':duplicates,'issues':sorted(set(issues)),
            'native_usage':total(records),'positive_metered_receipts':len(known),'measured_subtotal':subtotal,
            'models':{m:total([r for r in records if r['model']==m]) for m in sorted({r['model'] for r in records})},
            'records':records,'wall_time_total':None,'wall_time_reason':'Parent/worker CLI envelopes can overlap; use separately observed full-task envelopes',
            'actual_cash':None,'scope':'Measured native receipt subtotal only; excludes missing/unknown attempts and managed analyst overhead'}
