"""Reconcile each completed online memory diagnostic, including failed ones."""
import argparse,json
from pathlib import Path
from cost_context_study import REPO,PRICING,price
from native_jsonl import records,validate_native_completion
from workspace import Store
from capture_objects import read_capture
GLOBAL=REPO/'work/security/context-memory-20261107'
KEYS=('input_tokens','cached_input_tokens','output_tokens','total_tokens')
def measure(version):
 root=GLOBAL/('online-memory-native-canary-'+version)
 if not any((root/p).exists() for p in ('complete.json','stopped.json')):raise ValueError('Active diagnostic; do not finalize')
 output=root/'results.json'
 if output.exists():raise ValueError('Immutable receipt already exists')
 store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan();rates=json.loads(PRICING.read_text())['primary_scenario'];captured={}
 roots=[GLOBAL/'online-memory-native-canary-001/captures']
 if (GLOBAL/'online-capture-storage-002.json').exists():roots.append(Path(json.loads((GLOBAL/'online-capture-storage-002.json').read_text())['destination']))
 rejected=[]
 for directory in roots:
  for p in directory.glob('*.json'):
   c=read_capture(p)
   for ident in c.get('response_ids',[]):
    if ident in captured:raise ValueError('Duplicate response capture')
    captured[ident]=c
  for p in (directory/'rejections').glob('*.json'):
   c=json.loads(p.read_text());rejected.append(dict(id=c['id'],status=c.get('status'),upstream_submission=c.get('upstream_submission'),ended_ns=c.get('ended_ns')))
 cells=[]
 for cell in sorted(root.glob('call-*')):
  if not (cell/'agent.jsonl').exists():raise ValueError('Missing call evidence')
  sid=validate_native_completion(cell);cli=next(r['usage'] for r in records(cell) if r['type']=='turn.completed')
  with store.connection() as db:rows=[dict(r) for r in db.execute("SELECT id,usage FROM events WHERE session_id=? AND kind='generation'",(sid,))]
  if not rows:raise ValueError('Missing measured responses')
  aux=[]
  for row in rows:
   row['usage']=json.loads(row['usage']);ident=row['id'].split(':response:',1)[1];c=captured[ident]
   if c['status']!=200 or c.get('response_truncated') or c['original_request_sha256']!=c['forwarded_request_sha256']:raise ValueError('Incomplete/modified transport')
   ends=[e['response'] for e in c['response']['sse_events'] if e.get('type')=='response.completed'];end=next(e for e in ends if e['id']==ident);u=end['usage']
   measured=dict(input_tokens=u['input_tokens'],cached_input_tokens=u.get('input_tokens_details',{}).get('cached_tokens',0),output_tokens=u['output_tokens'],total_tokens=u['total_tokens'])
   if measured!={k:row['usage'][k] for k in KEYS}:raise ValueError('Native/proxy discrepancy')
   if end['model']!='gpt-6.1-sol':raise ValueError('Unexpected model')
   if any(x.get('type')=='compaction_trigger' for x in c['request'].get('input',[])):aux.append(row['id'])
  ordinary={k:sum(r['usage'][k] for r in rows if r['id'] not in aux) for k in KEYS}
  if any(ordinary[k]!=cli[k] for k in KEYS[:3]):raise ValueError('CLI/native discrepancy')
  calls=[r['item'] for r in records(cell) if r['type']=='item.completed' and r.get('item',{}).get('type')=='mcp_tool_call']
  usage={k:sum(r['usage'][k] for r in rows) for k in KEYS};cells.append(dict(case='synthetic_restart',condition='online_memory',phase=cell.name,session_id=sid,usage=usage,native_response_ids=[r['id'] for r in rows],auxiliary_ids=aux,native_cli_transport_reconciled=True,cost=sum(price(r['usage'],rates) for r in rows),tool_calls=len(calls),tool_errors=sum(bool(i.get('error')) or i.get('status')=='failed' for i in calls)))
 ids=[i for c in cells for i in c['native_response_ids']]
 if len(ids)!=len(set(ids)):raise ValueError('Duplicate native response')
 status=json.loads((root/('complete.json' if (root/'complete.json').exists() else 'stopped.json')).read_text());result=dict(protocol=root.name,diagnostic_passed=status.get('passed',False),cells=cells,completed_calls=len(cells),unique_responses=len(ids),usage={k:sum(c['usage'][k] for c in cells) for k in KEYS},credit_rate_scenario=sum(c['cost'] for c in cells),pricing=rates,capture_roots=[str(p) for p in roots],cash_expense=None,quota_saving=None,scope='Forced synthetic development integration; all failed/successful model responses included, no efficacy or savings comparison',shared_proxy_rejections=rejected)
 with output.open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps({k:result[k] for k in ('protocol','diagnostic_passed','completed_calls','unique_responses','usage','credit_rate_scenario')}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('version');measure(p.parse_args().version)
