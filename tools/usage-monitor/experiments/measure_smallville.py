#!/usr/bin/env python3
"""Response-level accounting for original mechanism and matched benchmark."""
import json,sys
from pathlib import Path
from smallville_native_mechanism import GLOBAL,HERE
from native_jsonl import records,validate_native_completion
from cost_context_study import REPO,PRICING,price
from workspace import Store
from capture_objects import read_capture
KEYS=('input_tokens','cached_input_tokens','output_tokens','total_tokens')
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def measure(kind):
 root=GLOBAL/({'mechanism':'smallville-native-mechanism-005','benchmark':'smallville-benchmark-001','original':'smallville-original-benchmark-001','validation':'smallville-validation-001','neutral':'smallville-neutral-validation-audit-002'}[kind])
 if not (root/'complete.json').exists():raise ValueError('Incomplete block')
 if (root/'results.json').exists():raise ValueError('Preserve immutable results')
 store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan();rates=json.loads(PRICING.read_text())['primary_scenario']
 captured={}
 for p in (GLOBAL/'smallville-native-mechanism-003/captures').glob('*.json'):
  c=read_capture(p)
  for ident in c.get('response_ids',[]):
   if ident in captured:raise ValueError('Duplicate capture response')
   captured[ident]=c
 def meter(cell,**meta):
  sid=validate_native_completion(cell)
  with store.connection() as db:rows=[dict(r) for r in db.execute("SELECT id,usage FROM events WHERE session_id=? AND kind='generation'",(sid,))]
  if not rows:raise ValueError('Missing native responses')
  aux=[]
  for r in rows:
   r['usage']=json.loads(r['usage']);ident=r['id'].split(':response:',1)[1];c=captured[ident]
   if c['status']!=200 or c.get('response_truncated') or c['original_request_sha256']!=c['forwarded_request_sha256']:raise ValueError('Incomplete/changed wire evidence')
   ends=[e['response'] for e in c['response']['sse_events'] if e.get('type')=='response.completed'];end=next(x for x in ends if x['id']==ident);u=end['usage']
   transport=dict(input_tokens=u['input_tokens'],cached_input_tokens=u.get('input_tokens_details',{}).get('cached_tokens',0),output_tokens=u['output_tokens'],total_tokens=u['total_tokens'])
   if transport!={k:r['usage'][k] for k in KEYS}:raise ValueError('Transport/native usage mismatch')
   if end['model']!='gpt-6.1-sol':raise ValueError('Response model changed')
   if any(x.get('type')=='compaction_trigger' for x in c['request'].get('input',[])):aux.append(r['id'])
  usage={k:sum(r['usage'][k] for r in rows) for k in KEYS};cli=next(r['usage'] for r in records(cell) if r.get('type')=='turn.completed')
  ordinary={k:sum(r['usage'][k] for r in rows if r['id'] not in aux) for k in KEYS}
  if any(cli[k]!=ordinary[k] for k in KEYS[:3]):raise ValueError('CLI ordinary usage mismatch')
  return dict(meta,session_id=sid,usage=usage,native_response_ids=[r['id'] for r in rows],auxiliary_ids=aux,native_cli_transport_reconciled=True,cost=sum(price(r['usage'],rates) for r in rows),wall_seconds=json.loads((cell/'completion.json').read_text())['elapsed_seconds'])
 cells=[]
 if kind=='mechanism':
  for version in ('003','004','005'):
   parent=GLOBAL/('smallville-native-mechanism-'+version)
   for p in sorted(parent.glob('call-*')):
    role=json.loads((p/'complete.json').read_text())['role'];cells.append(meter(p,case='synthetic',condition='original_compatibility',role=role,version=version))
  evidence=[]
  for line in (GLOBAL/'smallville-native-mechanism-003/memory/audit.jsonl').read_text().splitlines():
   r=json.loads(line)
   if r['kind']=='diagnostic_forced_reflection':evidence.append(r)
  pointer=json.loads((root/'memory/current.json').read_text())['checkpoint'];nodes=json.loads((root/'memory'/pointer/'nodes.json').read_text())
  malformed=[k for k,n in nodes.items() if n.get('predicate','').startswith('(TTGL')]
  result=dict(id='smallville-mechanism-results-001',cells=cells,completed_calls=len(cells),usage={k:sum(c['usage'][k] for c in cells) for k in KEYS},credit_rate_scenario=sum(c['cost'] for c in cells),observations=6,thoughts=15,reader_exact=True,reflection_forced=True,original_trigger_evidence=evidence,completion_remaining_field_correction='005natural_remaining0is copied forced state from003failure snapshot; use original003audit original_remaining for natural trigger. Frozen completion preserved.',malformed_triple_nodes=malformed,gate='recall/storage/evidence mechanism observed; semantic triple fidelity not approved',limitations='Synthetic forced reflection; not benchmark/savings. All original9+continuation32calls retained; parsing failures preserved.',cash_cost=None,quota_saving=None)
 elif kind=='neutral':
  plan=json.loads((root/'plan.json').read_text());source=GLOBAL/'smallville-validation-001';scores={a:0 for a in ('full_history','file_search','evidence_memory')};disagreements=[]
  for item in plan:
   p=root/item['assessment'];grade=json.loads((p/'grade.json').read_text());prior=json.loads((source/f'case-{item["case"]:02d}'/item['condition']/'grade.json').read_text());scores[item['condition']]+=grade['passed']
   cells.append(meter(p/'call-001',case=item['question_id'],condition=item['condition'],role='neutral_judge_overhead',grade=grade,primary_grade=prior))
   if grade['passed']!=prior['passed']:disagreements.append(dict(case=item['question_id'],condition=item['condition'],primary=prior['passed'],neutral=grade['passed']))
  retained={}
  for arm in ('full_history','file_search'):
   retained[arm]=all(not next(c for c in cells if c['case']==key and c['condition']==arm)['grade']['passed'] or next(c for c in cells if c['case']==key and c['condition']=='evidence_memory')['grade']['passed'] for key in {x['question_id'] for x in plan})
  result=dict(id='smallville-neutral-audit-results-002',cells=cells,scores=scores,disagreements=disagreements,baseline_successes_retained=retained,neutral_quality_gate_passed=all(retained.values()),research_credit_rate_scenario=sum(c['cost'] for c in cells),registration_timing=json.loads((root/'manifest.json').read_text())['registration_timing'],cash_cost=None,limitations='Same-model unchanged-rubric condition-neutral cwd audit; post-generation after primary grading began but before label inspection/audit inference. Primary grades preserved. Not independent human/programmatic truth or new solver trials.')
 elif kind=='original':
  registry=json.loads((root/'readers-complete.json').read_text())
  for item in registry:
   case=root/f'case-{item["case"]:02d}';grade=json.loads((case/'grade.json').read_text())
   for p in sorted((case/'build').glob('call-*')):
    role=json.loads((p/'complete.json').read_text())['role'];cells.append(meter(p,case=item['question_id'],condition='original_memory',role=role))
   if not item['memory_failed']:
    cells.append(meter(case/'reader/call-001',case=item['question_id'],condition='original_memory',role='reader',grade=grade))
    cells.append(meter(case/'judge/call-001',case=item['question_id'],condition='original_memory',role='judge_overhead'))
  task=[c for c in cells if c['role']!='judge_overhead'];baseline=json.loads((GLOBAL/'smallville-benchmark-001/results.json').read_text());cost=sum(c['cost'] for c in task);comparisons={}
  for arm in ('full_history','file_search','evidence_memory'):
   controls=[c for c in baseline['cells'] if c['role']=='reader' and c['condition']==arm];wins=0;retained=True
   for item in registry:
    control=next(c for c in controls if c['case']==item['question_id']);case_cost=sum(c['cost'] for c in task if c['case']==item['question_id']);passed=json.loads((root/f'case-{item["case"]:02d}'/'grade.json').read_text())['passed'];wins+=case_cost<control['cost'];retained=retained and (not control['grade']['passed'] or passed)
   comparisons[arm]=dict(scenario_saving_fraction=1-cost/sum(c['cost'] for c in controls),baseline_successes_retained=retained,paired_cost_wins=wins)
  original_eligible=all(comparisons[a]['baseline_successes_retained'] and comparisons[a]['scenario_saving_fraction']>=.1 and comparisons[a]['paired_cost_wins']>=2 for a in ('full_history','file_search'))
  builds=[json.loads(p.read_text()) for p in root.glob('case-*/memory-build.json')]
  result=dict(id='smallville-original-benchmark-results-001',development_nomination_gate_passed=original_eligible,cells=cells,cases=len(registry),successes=sum(json.loads((root/f'case-{i["case"]:02d}'/'grade.json').read_text())['passed'] for i in registry),memory_contract_failures=sum(i['memory_failed'] for i in registry),task_credit_rate_scenario=cost,task_usage={k:sum(c['usage'][k] for c in task) for k in KEYS},task_model_processes=len(task),judge_overhead_credits=sum(c['cost'] for c in cells if c['role']=='judge_overhead'),comparisons=comparisons,natural_reflection_events=sum(len(b['natural_reflections']) for b in builds),observations=sum(b['observations'] for b in builds),thoughts=sum(b['thoughts'] for b in builds),cash_cost=None,quota_saving=None,limitations='Original-style session adapter on3reused development memory-QA cases, model-judged. Original prompts/ranking/threshold with compatibleV3parsers and local BGE; no forced benchmark reflection. Full source fallback. Published scenario notcash/quota. Setup/mechanism/analyst/judges separate; no long-horizon coding or held-out claim.')
 else:
  registry=json.loads((root/'readers-complete.json').read_text())
  for item in registry:
   parent=root/item['cell'];grade=json.loads((parent/'grade.json').read_text());cells.append(meter(parent/'call-001',case=item['question_id'],condition=item['condition'],role='reader',grade=grade));cells.append(meter(parent/'judge/call-001',case=item['question_id'],condition=item['condition'],role='judge_overhead'))
  totals={}
  for arm in ('full_history','file_search','evidence_memory'):
   selected=[c for c in cells if c['condition']==arm and c['role']=='reader'];totals[arm]=dict(credit_rate_scenario=sum(c['cost'] for c in selected),usage={k:sum(c['usage'][k] for c in selected) for k in KEYS},successes=sum(c['grade']['passed'] for c in selected),tasks=len(selected),reader_wall_seconds=sum(c['wall_seconds'] for c in selected))
  build_seconds=sum(json.loads(p.read_text())['seconds'] for p in root.glob('case-*/memory-build.json'))
  retrieval_seconds=sum(json.loads(p.read_text())['seconds'] for p in root.glob('case-*/retrieval.json'))
  totals['evidence_memory']['local_build_seconds']=build_seconds
  totals['evidence_memory']['local_retrieval_seconds']=retrieval_seconds
  totals['evidence_memory']['summed_finite_operation_seconds']=totals['evidence_memory']['reader_wall_seconds']+build_seconds+retrieval_seconds
  candidate=totals['evidence_memory'];comparisons={} 
  for base in ('full_history','file_search'):
   pairs=[(next(c for c in cells if c['case']==key and c['condition']==base and c['role']=='reader'),next(c for c in cells if c['case']==key and c['condition']=='evidence_memory' and c['role']=='reader')) for key in json.loads((root/'protocol.json').read_text())['cases']]
   comparisons[base]=dict(scenario_saving_fraction=1-candidate['credit_rate_scenario']/totals[base]['credit_rate_scenario'],baseline_successes_retained=all(not a['grade']['passed'] or b['grade']['passed'] for a,b in pairs),paired_cost_wins=sum(b['cost']<a['cost'] for a,b in pairs))
  eligible=all(x['baseline_successes_retained'] and x['scenario_saving_fraction']>=.1 and x['paired_cost_wins']>len(json.loads((root/'protocol.json').read_text())['cases'])/2 for x in comparisons.values())
  embed=[json.loads(x) for x in (root/'embedding-inferences.jsonl').read_text().splitlines()]
  result=dict(id=('smallville-validation-results-001' if kind=='validation' else 'smallville-benchmark-results-001'),cells=cells,totals=totals,comparisons=comparisons,development_nomination_gate_passed=eligible,local_embedding_calls=len(embed),local_embedding_seconds=sum(x['seconds'] for x in embed),memory_index_bytes=sum(p.stat().st_size for p in root.glob('case-*/memory.sqlite')),judge_overhead_credits=sum(c['cost'] for c in cells if c['role']=='judge_overhead'),cash_cost=None,quota_saving=None,limitations=('Six fresh stratified public memory-QA cases, model-judged; fixed policy, no official score, statistical noninferiority or long-horizon coding benefit.' if kind=='validation' else 'Three reused development memory-QA cases, model-judged; no official score, held-out transfer or long-horizon coding benefit.')+' Candidate remote memory-creation inference0; all reader/auxiliary inference included. Local embedding inference/index/runtime, original mechanism and analyst research separate; startup not fully attributed.')
 ids=[i for c in cells for i in c['native_response_ids']]
 if len(ids)!=len(set(ids)):raise ValueError('Response counted twice')
 write(root/'results.json',result);public={k:v for k,v in result.items() if k!='cells'};write(HERE.parent/'studies'/('smallville-neutral-audit-results-002.json' if kind=='neutral' else 'smallville-'+kind+'-results-001.json'),public);print(json.dumps(public,indent=2))
if __name__=='__main__':measure(sys.argv[1])
