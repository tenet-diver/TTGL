"""Matched checkpoint replay, with one sealed attempt per registered condition."""
from pathlib import Path
from .io import read,write_new,digest

CONDITIONS=('small_empty','small_raw','small_structured','large_structured')


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
        value=execute(a)
        if value.get('uncertain'):
            write_new(root/'uncertain.json',value);break
        write_new(root/'completion.json',value);results.append(value)
    complete=len(results)==len(manifest['assignments'])
    result={'complete':complete,'assigned':len(manifest['assignments']),'completed':len(results),'results':results}
    write_new(output/('completion.json' if complete else 'stopped.json'),result);return result
