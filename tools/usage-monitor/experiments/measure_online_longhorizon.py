"""Full matrix accounting after all assignments; no model invocation or regrade."""
import json
from datetime import datetime
from pathlib import Path
from cost_context_study import REPO,PRICING,price
from native_jsonl import records,validate_native_completion
from workspace import Store
from capture_objects import read_capture
from online_longhorizon_trial import POINTER,GLOBAL,sha
KEYS=('input_tokens','cached_input_tokens','output_tokens','total_tokens')
def main():
 root=Path(json.loads(POINTER.read_text())['root'])
 if not (root/'complete.json').exists() or (root/'stopped.json').exists():raise ValueError('Matrix incomplete; preserve failures and audit separately')
 if (root/'results.json').exists():raise ValueError('Immutable result already exists')
 protocol=json.loads((root/'protocol.json').read_text());manifest=json.loads((root/'manifest.json').read_text())
 if sha(root/'protocol.json')!=manifest['copied_protocol_sha256']:raise ValueError('Protocol attachment mismatch')
 store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan();rates=json.loads(PRICING.read_text())['primary_scenario'];captured={}
 capture_roots=[GLOBAL/'online-memory-native-canary-001/captures',Path(json.loads((GLOBAL/'online-capture-storage-002.json').read_text())['destination'])]
 for directory in capture_roots:
  for p in directory.glob('*.json'):
   c=read_capture(p)
   if c.get('operation')=='response' and (c.get('state')!='complete' or c.get('status')!=200 or not c.get('response_ids')):raise ValueError('Uncertain inference transport; unknown usage cannot become zero')
   for ident in c.get('response_ids',[]):
    if ident in captured:raise ValueError('Duplicate captured model response')
    captured[ident]=c
  if any(not (directory/p.name).exists() for p in (directory/'pending').glob('*.json')):raise ValueError('Unresolved captured operation')
  if any(json.loads(p.read_text()).get('upstream_submission')!='not_attempted' for p in (directory/'rejections').glob('*.json')):raise ValueError('Rejected operation has uncertain upstream submission')
 cells=[];assignments=[];all_native=set();allocated=set()
 for spec in protocol['assignments']:
  parent=root/'assignments'/spec['id'];completion=json.loads((parent/'complete.json').read_text())
  if not completion['full_horizon_elapsed'] or completion['wall_seconds']<spec['horizon_seconds']:raise ValueError('Shortened assignment')
  paths=sorted(parent.glob('call-*'));previous={};assignment_ids=[]
  if len(paths)!=spec['horizon_seconds']//900:raise ValueError('Missing checkpoint')
  for index,cell in enumerate(paths):
   sid=validate_native_completion(cell);cli=next(r['usage'] for r in records(cell) if r['type']=='turn.completed');begin=datetime.fromisoformat(json.loads((cell/'started.json').read_text())['at']);end=datetime.fromisoformat(json.loads((paths[index+1]/'started.json').read_text())['at']) if index+1<len(paths) else None
   with store.connection() as db:all_rows=[dict(r) for r in db.execute("SELECT id,usage,ts FROM events WHERE session_id=? AND kind='generation'",(sid,))]
   all_native.update(r['id'] for r in all_rows);rows=[r for r in all_rows if datetime.fromisoformat(r['ts'])>=begin and (end is None or datetime.fromisoformat(r['ts'])<end)]
   if not rows:raise ValueError('Missing native generation; never infer zero usage')
   aux=[]
   for row in rows:
    row['usage']=json.loads(row['usage']);ident=row['id'].split(':response:',1)[1];c=captured[ident]
    if c['status']!=200 or c.get('response_truncated') or c['original_request_sha256']!=c['forwarded_request_sha256']:raise ValueError('Incomplete or transformed transport')
    end_response=next(e['response'] for e in c['response']['sse_events'] if e.get('type')=='response.completed' and e['response']['id']==ident);u=end_response['usage'];transport=dict(input_tokens=u['input_tokens'],cached_input_tokens=u.get('input_tokens_details',{}).get('cached_tokens',0),output_tokens=u['output_tokens'],total_tokens=u['total_tokens'])
    if transport!={k:row['usage'][k] for k in KEYS} or end_response['model']!='gpt-6.1-sol':raise ValueError('Native/transport mismatch')
    if any(i.get('type')=='compaction_trigger' for i in c['request'].get('input',[])):aux.append(row['id'])
   ordinary={k:sum(r['usage'][k] for r in rows if r['id'] not in aux) for k in KEYS};prior=previous.get(sid);counter_mode='per-turn'
   if any(ordinary[k]!=cli[k] for k in KEYS[:3]):
    if not prior or any(ordinary[k]!=cli[k]-prior[k] for k in KEYS[:3]):raise ValueError('CLI counters do not reconcile, including cumulative delta')
    counter_mode='validated-cumulative-delta'
   previous[sid]=cli;ids=[r['id'] for r in rows]
   if allocated.intersection(ids):raise ValueError('A response was allocated twice')
   allocated.update(ids);assignment_ids+=ids;usage={k:sum(r['usage'][k] for r in rows) for k in KEYS};cells.append(dict(assignment=spec['id'],case=spec['task'],condition=spec['condition'],phase=cell.name,session_id=sid,usage=usage,native_response_ids=ids,auxiliary_ids=aux,cli_counter_mode=counter_mode,native_cli_transport_reconciled=True,cost=sum(price(r['usage'],rates) for r in rows)))
  review_path=parent/'artifact-review.json'
  if not review_path.exists():raise ValueError('Separate offline artifact review required for every arm')
  review=json.loads(review_path.read_text())
  if review.get('status') not in ('pass','fail','unknown') or not review.get('rationale') or not review.get('source_hashes'):raise ValueError('Missing artifact review evidence')
  for p,h in review['source_hashes'].items():
   if sha(Path(p))!=h:raise ValueError('Reviewed sealed artifact changed')
  grade=completion['grade'];scored=grade['binary'] if spec['task']=='sqlite' else grade['passed'] if spec['task']=='fuzz' else grade['reward']==1
  assignments.append(dict(**spec,grade=grade,artifact_review=review,artifact_compliant_success=bool(scored and review['status']=='pass'),native_response_ids=assignment_ids,cost=sum(c['cost'] for c in cells if c['assignment']==spec['id']),full_horizon_elapsed=True))
 if allocated!=all_native:raise ValueError('Unallocated native responses')
 # This dedicated proxy serves only these registered diagnostics/matrix. Any
 # captured response absent from native allocations must be explained, not lost.
 known={}
 for name in ('online-memory-native-canary-001','online-memory-native-canary-002','online-memory-native-canary-003','online-memory-native-continuation-001'):
  for cell in json.loads((GLOBAL/name/'results.json').read_text())['cells']:
   for ident in cell['native_response_ids']:known[ident.split(':response:',1)[1]]=name
 expected={i.split(':response:',1)[1] for i in allocated}|set(known)
 if set(captured)!=expected:raise ValueError('Unexpected/orphan captured model response; reconcile before cost claims')
 totals={}
 for condition in protocol['conditions']:
  chosen=[c for c in cells if c['condition']==condition];tasks=[a for a in assignments if a['condition']==condition];totals[condition]=dict(usage={k:sum(c['usage'][k] for c in chosen) for k in KEYS},credit_rate_scenario=sum(c['cost'] for c in chosen),artifact_compliant_successes=sum(a['artifact_compliant_success'] for a in tasks),assignments=len(tasks))
 comparisons={};memory={a['task']:a for a in assignments if a['condition']=='restarted_memory'}
 for control in ('continued_records','restarted_records'):
  base={a['task']:a for a in assignments if a['condition']==control};retained=all(not b['artifact_compliant_success'] or memory[task]['artifact_compliant_success'] for task,b in base.items());saving=1-totals['restarted_memory']['credit_rate_scenario']/totals[control]['credit_rate_scenario'];wins=sum(memory[t]['cost']<base[t]['cost'] for t in base);quality_evidence=any(b['artifact_compliant_success'] for b in base.values());comparisons[control]=dict(retains_all_baseline_successes=retained,credit_rate_scenario_reduction_fraction=saving,paired_cost_wins=wins,nomination_gate=retained and quality_evidence and saving>=.10 and wins>=2)
 result=dict(protocol=protocol['id'],cells=cells,assignments=assignments,totals=totals,comparisons=comparisons,development_nomination_gate_passed=all(c['nomination_gate'] for c in comparisons.values()),unique_responses=len(allocated),native_processes=len(cells),scope='Adapted LHTB-derived full-horizon development, not official leaderboard/noninferiority or cash savings',cash_expense=None,quota_saving=None,research_parent_and_setup_inference=None,local_compute_not_monetized=True)
 with (root/'results.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(dict(comparisons=comparisons,totals=totals)),flush=True)
if __name__=='__main__':main()
