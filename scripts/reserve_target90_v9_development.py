#!/usr/bin/env python3
"""Reserve fresh fixed-v9 development by IDs only, before reading public inputs."""
import argparse, datetime, hashlib, json, re, shutil
from pathlib import Path
import prepare_swe_pro_subset as upstream
ROOT=Path(__file__).resolve().parents[1]
POLICY_FILES=['src/ttgl/evidence_decision_router.py','prompts/controller-v9-common.txt',
              'prompts/controller-v9-routing.txt','src/ttgl/harbor_bridge.py']

def sha(data):return hashlib.sha256(data).hexdigest()
def family(task):
    match=re.fullmatch(r'(instance_.+-[0-9a-f]{40})(?:-v.*)?',task)
    if not match:raise ValueError('Unrecognized task family')
    return match.group(1)

def select(paths,excluded,seed,count):
    blocked={family(x) for x in excluded};groups={}
    for path in paths:
        task=path.split('/')[2];key=family(task)
        if key not in blocked:groups.setdefault(key,[]).append(path)
    # One variant per bug family before repository-stratified ranking.
    eligible=[min(rows,key=lambda p:sha((seed+':variant:'+p).encode())) for rows in groups.values()]
    old=upstream.SEED
    try:
        upstream.SEED=seed;chosen,_=upstream.reserve(eligible,dev_count=count,held_count=0)
    finally:upstream.SEED=old
    if len({family(x['instance_id']) for x in chosen})!=count:raise ValueError('Duplicate family')
    return chosen,len(eligible)

def write_new(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seed',required=True);p.add_argument('--count',type=int,default=6)
    args=p.parse_args()
    if args.count!=6:raise ValueError('This registered extension is bounded to six tasks')
    parent=ROOT/'experiments/swe-pro-prompt-001';reservation=json.loads((parent/'reservation.json').read_text())
    raw=(parent/'upstream-tree.json').read_bytes()
    if sha(raw)!=reservation['inventory_sha256'] or reservation['revision']!=upstream.REVISION:raise ValueError('Pinned inventory differs')
    tree=json.loads(raw)
    if tree.get('truncated'):raise ValueError('Incomplete inventory')
    paths=[r['path'] for r in tree['tree'] if r['path'].startswith('v2/tasks/') and r['path'].endswith('/instruction.md')]
    if len(paths)!=642:raise ValueError('Unexpected population')
    # Administrative ID exclusion only; no held-out task content or grades read.
    excluded={x['instance_id'] for x in reservation['development']+reservation['held_out']}
    selection=args.output/'selection.json'
    prior=json.loads(selection.read_text()) if selection.exists() else None
    claims={}
    claim_paths=([Path(x) for x in prior['prior_claims_sha256']] if prior else
                 list((ROOT/'artifacts/assignment-claims').glob('*.json')))
    for path in claim_paths:
        row=json.loads(path.read_text());task=row.get('task_id','')
        if task.startswith('instance_'):
            excluded.add(task);claims[str(path)]=sha(path.read_bytes())
    chosen,eligible=select(paths,excluded,args.seed,args.count)
    policy={name:sha((ROOT/name).read_bytes()) for name in POLICY_FILES}
    fixed={'status':'registered_ID_only_selection_before_public_task_download_or_inference',
           'seed':args.seed,'revision':upstream.REVISION,'inventory_sha256':sha(raw),
           'policy':'v9','policy_sha256':policy,'development':chosen,'held_out':[],
           'eligible_unique_families':eligible,'excluded_family_count':len({family(x) for x in excluded}),
           'excluded_families_sha256':sha(json.dumps(sorted({family(x) for x in excluded})).encode()),
           'original_reservation_sha256':sha((parent/'reservation.json').read_bytes()),
           'prior_claims_sha256':claims,'selection_source_sha256':sha(Path(__file__).read_bytes()),
           'scored_assignment_cap':12,'per_task_cap':2,'automatic_retries':0,
           'no_policy_revision_within_six_task_block':True,'no_favorable_stopping_or_replacement':True,
           'reserved_validation_content_read':False,'reserved_validation_inference':0,
           'no_642_task_run':True,'monitoring':'PAUSED'}
    args.output.mkdir(parents=True,exist_ok=True);selection=args.output/'selection.json'
    if selection.exists():
        original=json.loads(selection.read_text());original.pop('registered_at',None)
        if original!=fixed:raise ValueError('Existing selection changed; no silent reselection')
    else:write_new(selection,{**fixed,'registered_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    inventory=args.output/'upstream-tree.json'
    if inventory.exists() and sha(inventory.read_bytes())!=sha(raw):raise ValueError('Copied inventory changed')
    if not inventory.exists():inventory.write_bytes(raw)
    manifest=args.output/'reservation.json'
    if manifest.exists():
        previous=json.loads(manifest.read_text())
        if previous['selection_sha256']!=sha(selection.read_bytes()):raise ValueError('Reservation selection changed')
        for row in previous['development']:
            for item in row['files'].values():
                if sha(Path(item['path']).read_bytes())!=item['sha256']:raise ValueError('Reserved public input changed')
        print(json.dumps({'status':'same_reservation_reused','tasks':6,'model_calls':0}));return
    entries={r['path']:r for r in tree['tree'] if r['type']=='blob'};rows=[]
    for selected in chosen:
        row={**selected,'files':{}}
        for name in ['instruction.md','task.toml','environment/Dockerfile']:
            path='v2/tasks/'+row['instance_id']+'/'+name;target=args.output/'public'/row['instance_id']/name
            data=target.read_bytes() if target.exists() else upstream.fetch(f'https://raw.githubusercontent.com/{upstream.REPOSITORY}/{upstream.REVISION}/{path}')
            blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            if blob!=entries[path]['sha']:raise ValueError('Public input differs from pinned upstream blob')
            if not target.exists():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
            row['files'][name]={'path':str(target.resolve()),'sha256':sha(data)}
        rows.append(row)
    write_new(manifest,{'status':'reserved_public_inputs_only_not_executed','dataset':'SWE-bench Pro V2',
        'upstream_repository':upstream.REPOSITORY,'revision':upstream.REVISION,'population_tasks':642,
        'inventory_sha256':sha(raw),'seed':args.seed,'development':rows,'held_out':[],
        'selection_sha256':sha(selection.read_bytes()),'policy_sha256':policy,
        'private_tests_or_reference_solutions_downloaded':False,'inference_calls':0,
        'full_population_run_authorized_by_this_manifest':False})
    print(json.dumps({'status':'six_fresh_fixed_v9_development_tasks_reserved','tasks':[r['repository'] for r in rows],'model_calls':0,'validation_content_read':False}))

if __name__=='__main__':main()
