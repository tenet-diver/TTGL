#!/usr/bin/env python3
"""Publish actual native mechanism receipts without inventing benchmark outcomes."""
import hashlib,json,sys
from pathlib import Path
from longmemeval_codex_trial import Store,REPO
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'observability'))
from analyst_experiments import plan_experiment,record_evaluation


def publish(directory):
    if (directory/'publication.json').exists():raise ValueError('Publication already exists')
    raw=(directory/'results.json').read_bytes();result=json.loads(raw);protocol=json.loads((directory/'protocol.json').read_text())
    if not json.loads((directory/'langfuse-audit-001.json').read_text())['all_reconciled']:raise ValueError('Langfuse audit required')
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');report=store.report(event_limit=None)
    project=next(p['id'] for p in report['projects'] if p['name']=='Context and memory optimization')
    cell=result['cells'][0]
    if not cell['native_reconciled']:raise ValueError('Native reconciliation required')
    task=store.mutate('task',dict(project_id=project,title=protocol['id'],goal='Native capture and automatic-compaction mechanism diagnostic',acceptance='Frozen synthetic gate, not a coding benchmark or savings comparison.'))['id']
    for turn in report['turns']:
        if turn['session_id']==cell['session_id']:store.mutate('assign',dict(session_id=turn['session_id'],turn_id=turn['turn_id'],task_id=task))
    store.mutate('task_status',dict(id=task,status='completed' if result['gate_passed'] else 'unresolved',outcome='Actual measured mechanism gate:'+str(result['gate_passed'])+'; native/transport/Langfuse reconciled.'))
    gate=protocol['acceptance'];gate='; '.join(gate) if isinstance(gate,list) else gate
    exp=plan_experiment(store,dict(task_id=task,title=protocol['id'],change=protocol.get('transport','Capture-only mechanism gate'),metrics='Unique native responses including compaction, transport equality, exact synthetic recall, full-string retention and CLI snapshot semantics.',quality_gate=gate,overhead='All inference is research overhead; no cash/quota/savings claim.',rollback=protocol['rollback']))['id']
    evaluation=record_evaluation(store,exp,protocol,result,hashlib.sha256(raw).hexdigest())
    receipt=dict(project_id=project,experiment_id=exp,evaluation_id=evaluation,task_id=task,result_sha256=hashlib.sha256(raw).hexdigest(),note='Metadata linkage only; no new usage or inference observations inserted.')
    with (directory/'publication.json').open('x') as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    print(json.dumps(receipt))


if __name__=='__main__':publish(Path(sys.argv[1]).resolve())
