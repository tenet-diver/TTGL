"""Register the frozen matrix in existing TTGL and attach actual native turns."""
import argparse,json
from pathlib import Path
from cost_context_study import REPO
from workspace import Store
from analyst_experiments import plan_experiment
def store():return Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000')
def prepare(root):
 from online_longhorizon_trial import sha
 if (root/'ttgl-plan.json').exists() or (root/'ttgl-planning-started.json').exists():raise ValueError('Existing/started TTGL plan; reconcile instead of duplicate')
 with (root/'ttgl-planning-started.json').open('x') as f:json.dump(dict(model_calls=0,no_automatic_metadata_retry=True),f)
 protocol=json.loads((root/'protocol.json').read_text());database=store();project=database.mutate('project',dict(name='Online memory full-horizon development001',repo=str(REPO),scope='Nine adapted LHTB-derived assignments; continued/lexical restart/semantic restart. Full horizons, private grades offline only.'))['id'];tasks={}
 for spec in protocol['assignments']:
  tasks[spec['id']]=database.mutate('task',dict(project_id=project,title=spec['task']+' / '+spec['condition'],goal='Complete the original public task artifacts and verification within the registered full horizon.',acceptance='Independent adapted task verifier plus separate offline artifact review, all native response counters reconciled.'))['id']
 with (root/'ttgl-plan.json').open('x') as f:json.dump(dict(project_id=project,task_ids=tasks,baseline_assignment=protocol['assignments'][0]['id'],experiment_id=None,experiment_deferred_reason='Existing experiment framework requires a measured baseline. Activate only after first full matched control; never invent or substitute historical baseline evidence.',protocol_sha256=sha(root/'protocol.json'),state='protocol_and_tasks_registered_before_model_inference'),f,indent=2)
 print('TTGL matrix plan registered; zero benchmark model calls.',flush=True)
def attach(root,spec,cell,sid):
 plan=root/'ttgl-plan.json'
 if not plan.exists():return # Direct software-test fixture, not CLI study runner.
 path=cell/'ttgl-turn-assignment.json'
 if path.exists():raise ValueError('Phase assignment already recorded')
 data=json.loads(plan.read_text());database=store();database.scan()
 with database.connection() as db:turns=[dict(r) for r in db.execute('SELECT session_id,turn_id FROM turns WHERE session_id=?',(sid,))]
 if not turns:raise ValueError('Native completed turn not yet collected')
 for turn in turns:database.mutate('assign',dict(task_id=data['task_ids'][spec['id']],**turn))
 with path.open('x') as f:json.dump(dict(session=sid,task_id=data['task_ids'][spec['id']],turns=turns,measured_usage_from_native=True),f,indent=2)
def activate(root,spec):
 path=root/'ttgl-plan.json'
 if not path.exists():return
 plan=json.loads(path.read_text())
 if spec['id']!=plan['baseline_assignment']:return
 if (root/'ttgl-experiment-activation.json').exists() or (root/'ttgl-experiment-activation-intent.json').exists():raise ValueError('Existing/uncertain experiment activation; no duplicate')
 completion=root/'assignments'/spec['id']/'complete.json'
 if not completion.exists() or not json.loads(completion.read_text())['full_horizon_elapsed']:raise ValueError('Actual full control required')
 with (root/'ttgl-experiment-activation-intent.json').open('x') as f:json.dump(dict(baseline_assignment=spec['id'],no_automatic_retry=True),f)
 protocol=json.loads((root/'protocol.json').read_text());database=store()
 experiment=plan_experiment(database,dict(task_id=plan['task_ids'][spec['id']],title=protocol['id'],change='Compare full continued native context and lexical records with restarted lexical records and incremental semantic task memory.',metrics='All actual model responses/cache counters, frozenNov7credit scenario, quality/artifact policy, full horizon and local compute separate. Frozen UI baseline is first full control; final comparisons use all matched controls.',quality_gate=protocol['selection'],overhead='Controls/integration/analyst costs separate from deployment conditions. No saving claim before all9assignments and accounting.',rollback='No global adoption, uncertain calls never retried, all evidence preserved and schedules paused.'))['id']
 with (root/'ttgl-experiment-activation.json').open('x') as f:json.dump(dict(experiment_id=experiment,actual_baseline_assignment=spec['id'],completion_evidence=str(completion),registered_protocol_unchanged=True),f,indent=2)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);prepare(p.parse_args().root)
