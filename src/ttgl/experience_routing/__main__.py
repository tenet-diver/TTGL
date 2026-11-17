"""Explicit finite stages. Inspection and preparation never call a model."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from .io import read,write_new,digest,file_digest
from .config import load,validate_config,freeze,verify_freeze


def parser():
    p=argparse.ArgumentParser(prog='python -m ttgl.experience_routing')
    commands=p.add_subparsers(dest='command',required=True)
    for name in ('inspect','validate-config','prepare','freeze','run'):
        q=commands.add_parser(name);q.add_argument('--config',required=True)
        if name in ('freeze','run'):q.add_argument('--output',required=True)
    q=commands.add_parser('inventory');q.add_argument('--root',default='.');q.add_argument('--output',required=True)
    q=commands.add_parser('build-splits');q.add_argument('--manifest',required=True);q.add_argument('--exclusions',required=True);q.add_argument('--output',required=True);q.add_argument('--seed',type=int,default=17012026)
    for name in ('annotate','audit-annotations','replay-subtasks','calibrate','grade'):
        q=commands.add_parser(name);q.add_argument('--manifest',required=True);q.add_argument('--output',required=True)
    q=commands.add_parser('report');q.add_argument('--study',required=True);q.add_argument('--output',required=True);q.add_argument('--control',default='LPM');q.add_argument('--candidate',default='HRM')
    q=commands.add_parser('fixture');q.add_argument('--output',required=True)
    return p


def prepare(path):
    config=load(path);result=validate_config(config,root=Path(path).resolve().parent)
    result.update(stage='model-free preparation',model_calls=0,
      next_model_dependent_gates=[x for x in result['missing'] if x.startswith('gate:')],
      automatic_retries=0,execution_enabled=config.get('allow_model_execution',False))
    return result


def annotate(manifest,output):
    from .client import ExperienceClient
    rows=manifest['assignments']
    if len(rows)>manifest['maximum_assignments'] or not rows:raise ValueError('Finite annotation assignments required')
    if len({r['analysis_id'] for r in rows})!=len(rows):raise ValueError('Duplicate annotation source')
    client=ExperienceClient(manifest['project_id'],manifest['study_id'],manifest['endpoint'])
    root=Path(output);write_new(root/'started.json',{'manifest_hash':digest(manifest),'model_calls':0})
    receipts=[]
    for row in rows:
        value=client.call('queue-extraction',{'analysisId':row['analysis_id'],'promptVersion':manifest['prompt_version'],'metadata':row['metadata']})
        write_new(root/(row['assignment_id']+'.json'),value);receipts.append(value)
    # Queuing is distinct from invoking. Worker requires explicit exact job IDs,
    # source binding, a finite registered budget and OBS_ALLOW_EXPERIENCE_MODELS.
    result={'queued':receipts,'model_calls':0,'execution':'explicit source-local experience-worker job IDs'}
    write_new(root/'completion.json',result);return result


def replay(manifest,output):
    from .replay import replay_registered,CONDITIONS
    from .campaign import run_campaign
    groups={}
    for a in manifest['assignments']:groups.setdefault(a['checkpoint_id'],[]).append(a)
    for checkpoint,rows in groups.items():
        if {r['condition'] for r in rows}!=set(CONDITIONS) or len(rows)!=4:raise ValueError('Replay requires four distinct matched conditions')
        if len({(r['contract_hash'],r['source_state_hash'],r['parent_id']) for r in rows})!=1:raise ValueError('Replay checkpoint and contract differ')
    def execute(a):
        frozen=read(a['freeze_path']);config=verify_freeze(frozen)
        if config.get('replay',{}).get('checkpoint_id')!=a['checkpoint_id'] or config['replay'].get('condition')!=a['condition'] or config['replay'].get('contract_hash')!=a['contract_hash']:raise ValueError('Replay freeze does not pin its condition and checkpoint contract')
        result=run_campaign(a['freeze_path'],Path(output)/a['assignment_id']/'campaign')
        return {**result,'uncertain':not result['complete'],'assignment':a}
    return replay_registered(manifest,execute,output)


def grade(manifest,output):
    from .benchmarks import pinned_evaluator
    if not manifest.get('assignments') or len(manifest['assignments'])>manifest['maximum_assignments']:raise ValueError('Finite evaluator assignment list required')
    root=Path(output);write_new(root/'started.json',{'manifest_hash':digest(manifest),'model_calls':0})
    rows=[]
    for a in manifest['assignments']:
        receipt=pinned_evaluator(a['command'],command_hash=a['command_hash'],patch_manifest=a['patch_manifest'],output=root/a['assignment_id'],timeout=manifest['timeout_seconds'])
        rows.append({**receipt,'task_id':a['task_id'],'arm':a['arm'],'repository':a['repository'],'grade_valid':True,
                     'scenario_cost':a.get('scenario_cost'),'fixture_only':a.get('fixture_only',False)})
    write_new(root/'completion.json',{'grades':rows,'visibility':'evaluation_sealed','model_calls':0});return {'graded':len(rows),'model_calls':0}


def main(argv=None):
    a=parser().parse_args(argv);name=a.command
    if name in ('inspect','prepare','validate-config'):result=prepare(a.config)
    elif name=='freeze':result=freeze(a.config,a.output)
    elif name=='run':
        from .campaign import run_campaign
        result=run_campaign(a.config,a.output)
    elif name=='fixture':
        from .fixtures import run_fixture
        result=run_fixture(a.output)
    elif name=='inventory':
        from .inventory import inventory,exclusion_registry
        result=inventory(a.root);write_new(a.output,result)
        write_new(Path(a.output).with_name('exclusion-registry.json'),exclusion_registry(result))
    elif name=='build-splits':
        from .inventory import build_splits
        result=build_splits(read(a.manifest)['tasks'],read(a.exclusions),a.seed);write_new(a.output,result)
    elif name=='annotate':result=annotate(read(a.manifest),a.output)
    elif name=='audit-annotations':
        from .analysis import annotation_audit
        result=annotation_audit(read(a.manifest)['adjudications']);write_new(a.output,result)
    elif name=='calibrate':
        from .policy import calibrate
        m=read(a.manifest);result=calibrate(m['rows'],thresholds=m['thresholds']);write_new(a.output,result)
    elif name=='replay-subtasks':result=replay(read(a.manifest),a.output)
    elif name=='grade':result=grade(read(a.manifest),a.output)
    elif name=='report':
        from .analysis import paired
        study=read(a.study);result=paired(study.get('grades',study.get('records',[])),a.control,a.candidate);write_new(a.output,result)
    print(json.dumps(result,indent=2,default=str));return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,RuntimeError,OSError,KeyError) as error:
        print(json.dumps({'error':type(error).__name__,'reason':str(error),'automatic_retry':False}),file=sys.stderr)
        raise SystemExit(2)
