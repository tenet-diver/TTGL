#!/usr/bin/env python3
"""Publish measured Smallville evidence and interpretation to existing TTGL UI."""
import hashlib,json,sys
from pathlib import Path
from smallville_native_mechanism import GLOBAL,HERE
from cost_context_study import REPO
from workspace import Store
from analyst_experiments import plan_experiment,record_evaluation,review_experiment,record_accounting

def main(kind):
 root=GLOBAL/({'mechanism':'smallville-native-mechanism-005','benchmark':'smallville-benchmark-001','validation':'smallville-validation-001','original':'smallville-original-benchmark-001'}[kind])
 if (root/'publication.json').exists():raise ValueError('Already published')
 result=json.loads((root/'results.json').read_text());audit=json.loads((root/'langfuse-audit-001.json').read_text())
 if not audit['all_reconciled']:raise ValueError('Langfuse accounting not reconciled')
 store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan()
 project=store.mutate('project',dict(name='Smallville memory research '+kind,repo=str(REPO),scope='Original implementation first, preserved compatibility failures, measured inference and exact source evidence; no hosted memory.'))['id']
 task=store.mutate('task',dict(project_id=project,title='Smallville '+kind+' measured trial',goal='Measure memory correctness, complete inference and deployment limitations.',acceptance='Original mechanism fidelity or registered benchmark quality/cost gate; all unique native/transport/Langfuse responses reconcile.'))['id']
 sessions={c['session_id'] for c in result['cells']}
 with store.connection() as db:turns=[dict(r) for r in db.execute('SELECT session_id,turn_id FROM turns')]
 for turn in turns:
  if turn['session_id'] in sessions:store.mutate('assign',dict(task_id=task,**turn))
 exp=plan_experiment(store,dict(task_id=task,title='Original-style Smallville '+kind,
  change='Original storage/ranking/prompts tested before modern-output parsing and an independently labeled evidence-first candidate.',
  metrics='Native unique response tokens and frozen Codex credit-rate scenario; all model roles plus independently recorded local work.',
  quality_gate='Full frozen protocol; do not promote from mechanism-only or reused development evidence.',
  overhead='Original41calls, compatibility/replay and analyst/setup are research expense; judge inference separate; cash/quota unknown.',
  rollback='No global routing/memory change. Optional modules remain opt-in. Preserve all logs and immutable failures.'))['id']
 neutral=None
 if kind=='validation':
  neutral_root=GLOBAL/'smallville-neutral-validation-audit-002'
  if not json.loads((neutral_root/'langfuse-audit-001.json').read_text())['all_reconciled']:raise ValueError('Neutral audit not reconciled')
  neutral=json.loads((neutral_root/'results.json').read_text())
 protocol=json.loads((root/'protocol.json').read_text());measurements={**result,'langfuse_reconciled':True,'acceptance_passed':result.get('development_nomination_gate_passed',False)}
 if neutral:
  measurements['neutral_audit']={k:v for k,v in neutral.items() if k!='cells'}
  measurements['acceptance_passed']=measurements['acceptance_passed'] and neutral['neutral_quality_gate_passed']
 digest=hashlib.sha256(json.dumps(measurements,sort_keys=True).encode()).hexdigest();evaluation=record_evaluation(store,exp,protocol,measurements,digest)
 if kind=='mechanism':
  verdict='inconclusive';notes='Original importance/focal/insight/triple prompts produced useful evidence-linked memory and exact recall. Original parser failed twice;005stored malformed triple fields.006exact-prompt replay corrects all41existing outputs with0newLLMcalls. Forced trigger with natural135remaining.421840tokens/5.1868scenario credits; no task efficacy/savings or production promotion.'
 else:
  verdict='inconclusive' if measurements['acceptance_passed'] else 'reject';notes=('Registered six-case fresh validation result; ' if kind=='validation' else 'Registered direct original-style three-case development arm; ' if kind=='original' else 'Registered three-case reused development memory-QA result; ')+json.dumps(result['comparisons'])+'. Local indexing and original mechanism research cost remain separate. No official benchmark, fresh transfer, coding-task benefit or cash/quota claim. No deployment promotion without separately frozen evidence.'
 if neutral:notes+=' Neutral-cwd audit: '+json.dumps(neutral['scores'])+'; disagreements='+str(len(neutral['disagreements']))+'; both label sets preserved; post-generation sensitivity audit.'
 review=review_experiment(store,dict(evaluation_id=evaluation,verdict=verdict,notes=notes))
 if neutral:
  record_accounting(store,exp,dict(kind='additional neutral-grading research overhead',credit_rate_scenario=neutral['research_credit_rate_scenario'],model_processes=len(neutral['cells']),cash_cost=None,source='smallville-neutral-validation-audit-002/results.json',note='Separate from deployment reader costs; primary grades preserved.'))
 store.mutate('task_status',dict(id=task,status='completed',outcome=notes))
 publication=dict(project_id=project,task_id=task,experiment_id=exp,evaluation_id=evaluation,review=review,artifact_sha256=digest)
 with (root/'publication.json').open('x') as f:json.dump(publication,f,indent=2)
 print(json.dumps(publication))
if __name__=='__main__':main(sys.argv[1])
