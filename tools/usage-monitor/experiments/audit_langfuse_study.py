#!/usr/bin/env python3
"""Reconcile finalized trial counters against Langfuse v2 without re-ingestion."""
import argparse
import base64
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request


def audit(directory,credentials,start,end):
    result=json.loads((directory/'results.json').read_text())
    config=json.loads(credentials.read_text())
    if config['base_url'] not in ('http://localhost:3000','http://127.0.0.1:3000'):
        raise ValueError('Only existing loopback Langfuse deployment')
    auth=base64.b64encode((config['public_key']+':'+config['secret_key']).encode()).decode()
    receipts=[]
    for cell in result['cells']:
        rows=[];cursor=None;seen_cursors=set()
        while True:
            q=dict(limit=100,fields='core,basic,usage',fromStartTime=start,toStartTime=end,
                filter=json.dumps([dict(column='sessionId',type='stringOptions',operator='any of',value=[cell['session_id']])]))
            if cursor:q['cursor']=cursor
            req=urllib.request.Request(config['base_url']+'/api/public/v2/observations?'+urllib.parse.urlencode(q),headers={'Authorization':'Basic '+auth})
            with urllib.request.urlopen(req,timeout=30) as r:data=json.load(r)
            rows+=data['data'];cursor=data.get('meta',{}).get('cursor')
            if not cursor:break
            if cursor in seen_cursors:raise ValueError('Repeated pagination cursor')
            seen_cursors.add(cursor)
        gens=[r for r in rows if r['type']=='GENERATION']
        actual_ids=[r['id'] for r in gens]
        expected_ids=[hashlib.sha256(i.encode()).hexdigest()[:16] for i in cell['native_response_ids']]
        usage={k:sum(g.get('usageDetails',{}).get(k,0) for g in gens) for k in ('input','input_cached_tokens','output','total')}
        native=cell['usage'];expected=dict(input=native['input_tokens']-native['cached_input_tokens'],
            input_cached_tokens=native['cached_input_tokens'],output=native['output_tokens'],total=native['total_tokens'])
        reconciled=(sorted(actual_ids)==sorted(expected_ids) and len(set(actual_ids))==len(actual_ids) and usage==expected)
        receipts.append(dict(session=cell['session_id'],generation_ids=actual_ids,expected_generation_ids=expected_ids,
            usage=usage,expected=expected,reconciled=reconciled,
            all_session_ids_match=all(r.get('sessionId')==cell['session_id'] for r in rows)))
    return dict(at=datetime.now(timezone.utc).isoformat(),api='Langfuse v2 observations, explicit usage fields and bounded dates',
        all_reconciled=all(r['reconciled'] and r['all_session_ids_match'] for r in receipts),sessions=receipts,
        note='Read-only accounting audit. Transcript and proxy sources are not added together. No observations re-ingested.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('--credentials',type=Path,required=True)
    p.add_argument('--start',required=True);p.add_argument('--end',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise ValueError('Preserve old audit; use a fresh receipt filename')
    result=audit(args.directory,args.credentials,args.start,args.end);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(sessions=len(result['sessions']),all_reconciled=result['all_reconciled'])))
