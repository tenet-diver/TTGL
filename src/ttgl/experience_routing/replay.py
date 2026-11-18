"""Matched checkpoint replay, with one sealed attempt per registered condition."""
from pathlib import Path
from .io import read,write_new,digest,file_digest
from .checkpoints import replay_snapshot,manifest
from .contracts import validate

CONDITIONS=('small_empty','small_raw','small_structured','large_structured')


def execute_checkpoint(assignment, checkpoint, contract, destination, execute, *, packet=None):
    """Restore the exact pre-node state and execute a supplied qualified adapter.

    This has no planner and no publication path. The caller supplies a bounded,
    retained executor after native qualification; tests use a synthetic adapter.
    """
    if assignment['condition'] not in CONDITIONS:raise ValueError('Unknown replay condition')
    if assignment['checkpoint_id']!=checkpoint['checkpointId'] or assignment['parent_id']!=checkpoint['taskInstanceId']:
        raise ValueError('Replay parent/checkpoint identity differs')
    if assignment['source_state_hash']!=checkpoint['repositoryStateHash'] or assignment['contract_hash']!=digest(contract) or checkpoint['contractHash']!=digest(contract):
        raise ValueError('Replay requires the exact frozen source and node contract')
    if contract['nodeId']!=checkpoint['planNodeId']:raise ValueError('Replay node identity differs')
    replay_snapshot(checkpoint,destination)
    before=manifest(destination)
    if before['state_hash']!=assignment['source_state_hash']:raise ValueError('Replay pre-node state differs')
    experiences=packet or {'experiences':[]}
    if assignment['condition']=='small_empty':experiences={'experiences':[]}
    elif assignment['condition']=='small_raw':
        if not experiences.get('rawEvidence'):raise ValueError('Raw replay condition requires retained source evidence')
    elif not experiences.get('experiences'):raise ValueError('Structured replay condition requires a frozen experience packet')
    import copy
    immutable_hash=digest(contract)
    execution_contract=copy.deepcopy(contract)
    value=execute(execution_contract,Path(destination),copy.deepcopy(experiences),'large' if assignment['condition']=='large_structured' else 'small')
    if digest(execution_contract)!=immutable_hash:raise ValueError('Replay executor changed the frozen contract')
    return {**value,'checkpoint_id':checkpoint['checkpointId'],'contract_hash':digest(contract),
            'source_state_hash':before['state_hash'],'shadow_memory_publication':False,'scope':'subtask_replay'}


def replay_manifest(checkpoints,*,development_parents,holdout_parents,seed=0):
    import random
    if set(development_parents)&set(holdout_parents):raise ValueError('Replay parents cross development/holdout')
    rows=[];seen=set();rng=random.Random(seed)
    for cp in checkpoints:
        if cp['checkpointId'] in seen:raise ValueError('Duplicate checkpoint')
        seen.add(cp['checkpointId']);parent=cp['taskInstanceId']
        if parent not in set(development_parents)|set(holdout_parents):raise ValueError('Unregistered replay parent')
        conditions=list(CONDITIONS);rng.shuffle(conditions)
        for condition in conditions:
            rows.append({'assignment_id':digest([cp['checkpointId'],condition]),'checkpoint_id':cp['checkpointId'],
              'parent_id':parent,'condition':condition,'split':'router_development' if parent in development_parents else 'mechanism_holdout',
              'contract_hash':cp['contractHash'],'source_state_hash':cp['repositoryStateHash']})
    return {'schema_version':1,'seed':seed,'assignments':rows,'automatic_retries':0,'shadow_memory_publication':False}


def replay_registered(manifest,execute,output):
    output=Path(output)
    if (output/'started.json').exists():raise ValueError('Replay already owned; no automatic attempt replacement')
    write_new(output/'started.json',{'manifest_hash':digest(manifest),'assignments':len(manifest['assignments'])})
    results=[]
    for a in manifest['assignments']:
        root=output/a['assignment_id'];write_new(root/'started.json',a)
        try:value=execute(a)
        except BaseException as error:
            failure={'uncertain':True,'error':type(error).__name__,'reason':str(error)[:1000],'automatic_retry':False}
            write_new(root/'uncertain.json',failure)
            write_new(output/'stopped.json',{'complete':False,'assigned':len(manifest['assignments']),'completed':len(results),'results':results,'failure':failure})
            raise
        if value.get('uncertain'):
            write_new(root/'uncertain.json',value);break
        write_new(root/'completion.json',value);results.append(value)
    complete=len(results)==len(manifest['assignments'])
    result={'complete':complete,'assigned':len(manifest['assignments']),'completed':len(results),'results':results}
    write_new(output/('completion.json' if complete else 'stopped.json'),result);return result
