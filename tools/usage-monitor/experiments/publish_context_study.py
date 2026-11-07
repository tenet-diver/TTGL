#!/usr/bin/env python3
"""Attach reconciled existing trial evidence to TTGL; never duplicate usage rows."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'observability'))
from workspace import Store
from analyst_experiments import plan_experiment,record_evaluation


def publish(directory):
    if (directory/'publication.json').exists():raise ValueError('Publication already exists; preserve receipt')
    raw=(directory/'results.json').read_bytes();result=json.loads(raw)
    if not (directory/'complete.json').exists() or not result.get('cells'):
        raise ValueError('Incomplete trial')
    if not all(c.get('native_reconciled') for c in result['cells']):
        raise ValueError('Native reconciliation required')
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000',REPO/'work/security/langfuse-stack/captures')
    store.scan();report=store.report(event_limit=None)
    project=next((p['id'] for p in report['projects'] if p['name']=='Context and memory optimization'),None)
    if project is None:project=store.mutate('project',dict(name='Context and memory optimization',repo=str(REPO),scope='Registered context/memory trials with independent checks, native usage and research overhead; not cash or quota measurement.'))['id']
    protocol=json.loads((directory/'protocol.json').read_text())
    baseline='baseline' if any(c['condition']=='baseline' for c in result['cells']) else 'none'
    task_ids={}
    for cell in result['cells']:
        label=str(cell.get('case') or cell.get('sequence'))+' '+cell['condition']+' '+str(cell.get('stage',''))
        task=store.mutate('task',dict(project_id=project,title=protocol['id']+' '+label,
            goal='Execute the frozen comparison cell and account for every native response.',
            acceptance='Registered independent quality checks and exact native/CLI reconciliation.'))['id']
        for turn in report['turns']:
            if turn['session_id']==cell['session_id']:
                store.mutate('assign',dict(session_id=turn['session_id'],turn_id=turn['turn_id'],task_id=task))
        quality=cell.get('quality',cell.get('grade',{}));passed=quality.get('passed',False)
        store.mutate('task_status',dict(id=task,status='completed' if passed else 'unresolved',outcome='Independent checks: '+json.dumps(quality)+'; native/CLI reconciled.'))
        task_ids[label]=task
    anchor=next(task for label,task in task_ids.items() if (' '+baseline+' ') in label)
    experiment=plan_experiment(store,dict(task_id=anchor,title=protocol['id'],change='Registered context/memory representation or independent-read guidance; see frozen protocol for treatment/comparator.',
        metrics='Complete-run native tokens, cached/fresh/output, independent quality and process wall time. All actual cells retained.',
        quality_gate=protocol.get('development_gate',protocol.get('acceptance','All independent checks pass.')),
        overhead=protocol['overhead'],rollback=protocol['rollback']))['id']
    evaluation=record_evaluation(store,experiment,protocol,result,hashlib.sha256(raw).hexdigest())
    receipt=dict(project_id=project,experiment_id=experiment,evaluation_id=evaluation,task_ids=task_ids,result_sha256=hashlib.sha256(raw).hexdigest(),
        note='Metadata publication links existing unique native response evidence; no new generation observations or usage inserted.')
    (directory/'publication.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='task_ids'}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);args=p.parse_args();publish(args.directory.resolve())
