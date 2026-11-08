#!/usr/bin/env python3
"""Publish measured Smallville evidence and interpretation to existing TTGL UI."""
import hashlib,json,sys
from pathlib import Path
from smallville_native_mechanism import GLOBAL,HERE
from cost_context_study import REPO
from workspace import Store
from analyst_experiments import plan_experiment,record_evaluation,review_experiment

def main(kind):
 root=GLOBAL/('smallville-native-mechanism-005' if kind=='mechanism' else 'smallville-benchmark-001')
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
 protocol=json.loads((root/'protocol.json').read_text());measurements={**result,'langfuse_reconciled':True,'acceptance_passed':result.get('development_nomination_gate_passed',False)}
 digest=hashlib.sha256(json.dumps(measurements,sort_keys=True).encode()).hexdigest();evaluation=record_evaluation(store,exp,protocol,measurements,digest)
 if kind=='mechanism':
  verdict='inconclusive';notes='Original importance/focal/insight/triple prompts produced useful evidence-linked memory and exact recall. Original parser failed twice;005stored malformed triple fields.006exact-prompt replay corrects all41existing outputs with0newLLMcalls. Forced trigger with natural135remaining.421840tokens/5.1868scenario credits; no task efficacy/savings or production promotion.'
 else:
  verdict='inconclusive' if result['development_nomination_gate_passed'] else 'reject';notes='Registered three-case reused development memory-QA result; '+json.dumps(result['comparisons'])+'. Local indexing and original mechanism research cost remain separate. No official benchmark, fresh transfer, coding-task benefit or cash/quota claim. No deployment promotion without separately frozen evidence.'
 review=review_experiment(store,dict(evaluation_id=evaluation,verdict=verdict,notes=notes))
 store.mutate('task_status',dict(id=task,status='completed',outcome=notes))
 publication=dict(project_id=project,task_id=task,experiment_id=exp,evaluation_id=evaluation,review=review,artifact_sha256=digest)
 with (root/'publication.json').open('x') as f:json.dump(publication,f,indent=2)
 print(json.dumps(publication))
if __name__=='__main__':main(sys.argv[1])
