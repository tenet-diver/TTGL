"""Publish actual online integration outcomes/usage without efficacy claims."""
import argparse,hashlib,json
from pathlib import Path
from cost_context_study import REPO
from workspace import Store
from analyst_experiments import plan_experiment,record_evaluation,review_experiment,record_accounting
def main(root):
 if (root/'publication.json').exists():raise ValueError('Already published')
 result=json.loads((root/'results.json').read_text());audit=json.loads((root/'langfuse-audit-001.json').read_text())
 if not audit['all_reconciled']:raise ValueError('Accounting must reconcile first')
 store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan()
 project=store.mutate('project',dict(name='Online task memory integration '+root.name,repo=str(REPO),scope='Synthetic forced code/check/note/recall integration, including failed attempts; no benchmark efficacy or adoption.'))['id']
 task=store.mutate('task',dict(project_id=project,title=root.name,goal='Exercise actual task tools, source-linked fallible notes and recall/continuation.',acceptance='Registered mechanism checks and independent fixture, complete native/CLI/proxy/Langfuse accounting.'))['id']
 sessions={c['session_id'] for c in result['cells']}
 with store.connection() as db:turns=[dict(r) for r in db.execute('SELECT session_id,turn_id FROM turns')]
 for turn in turns:
  if turn['session_id'] in sessions:store.mutate('assign',dict(task_id=task,**turn))
 exp=plan_experiment(store,dict(task_id=task,title=root.name,change='Incremental SQLite/FTS with optional reviewed local note embeddings and restricted writable-task MCP bridge.',metrics='Complete measured native model tokens, frozenNov7credit-rate scenario; local operations separate.',quality_gate='Actual recorded tool execution and independent saved-code checks; forced mechanism only.',overhead='All calls here are research integration overhead, not task-model savings. Failed attempts included.',rollback='No global memory/routing adoption. All raw source captures and failed states retained.'))['id']
 measurements=dict(result,langfuse_reconciled=True,acceptance_passed=result['diagnostic_passed']);digest=hashlib.sha256(json.dumps(measurements,sort_keys=True).encode()).hexdigest();evaluation=record_evaluation(store,exp,json.loads((root/'protocol.json').read_text()),measurements,digest)
 notes='Mechanism '+('passed' if result['diagnostic_passed'] else 'failed')+'; '+result['scope']+'. No autonomous memory-use, long-horizon quality/cost, cash saving or global adoption claim.'
 review=review_experiment(store,dict(evaluation_id=evaluation,verdict='inconclusive' if result['diagnostic_passed'] else 'reject',notes=notes));record_accounting(store,exp,dict(kind='native integration research overhead',credit_rate_scenario=result['credit_rate_scenario'],model_processes=result['completed_calls'],cash_cost=None,source=str(root/'results.json'),note='All response IDs reconcile; no efficacy comparison.'))
 store.mutate('task_status',dict(id=task,status='completed',outcome=notes))
 with (root/'publication.json').open('x') as f:json.dump(dict(project_id=project,task_id=task,experiment_id=exp,evaluation_id=evaluation,review=review,artifact_sha256=digest),f,indent=2)
 print(root.name,'published',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);main(p.parse_args().root)
