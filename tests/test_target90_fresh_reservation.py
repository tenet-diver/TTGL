import importlib.util,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts'))
spec=importlib.util.spec_from_file_location('fresh',Path(__file__).parents[1]/'scripts/reserve_target90_v9_development.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def task(repo,commit,variant=''):
 return f'v2/tasks/instance_{repo}-'+commit*40+variant+'/instruction.md'
def test_family_exclusion_covers_all_variants_and_selection_is_reproducible():
 paths=[task('a__a','a','-v1'),task('a__a','a','-v2'),task('a__a','b'),task('b__b','c'),task('c__c','d')]
 excluded=['instance_a__a-'+'a'*40+'-v1'];a,n=m.select(paths,excluded,'fixed',3);b,_=m.select(paths,excluded,'fixed',3)
 assert a==b and n==3
 assert all(m.family(x['instance_id'])!=m.family(excluded[0]) for x in a)
 assert len({x['repository'] for x in a})==3
 assert m.upstream.SEED=='ttgl-pro-prompt-001'
def test_one_variant_per_family_before_ranking():
 paths=[task('a__a','a','-v1'),task('a__a','a','-v2'),task('b__b','b')]
 rows,n=m.select(paths,[],'fixed',2)
 assert n==2 and len({m.family(r['instance_id']) for r in rows})==2


def test_rerun_reuses_selection_after_its_own_new_claims(tmp_path,monkeypatch):
 import json,hashlib
 monkeypatch.setattr(m,'ROOT',tmp_path)
 for name in m.POLICY_FILES:
  p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('frozen')
 body=b'public fixture';blob=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
 ids=[f'instance_repo{i%11}__repo{i%11}-'+f'{i:040x}' for i in range(642)]
 entries=[{'path':f'v2/tasks/{task}/{name}','type':'blob','sha':blob} for task in ids for name in ['instruction.md','task.toml','environment/Dockerfile']]
 parent=tmp_path/'experiments/swe-pro-prompt-001';parent.mkdir(parents=True);raw=json.dumps({'tree':entries,'truncated':False}).encode();(parent/'upstream-tree.json').write_bytes(raw)
 (parent/'reservation.json').write_text(json.dumps({'revision':m.upstream.REVISION,'inventory_sha256':m.sha(raw),'development':[{'instance_id':ids[0]}],'held_out':[{'instance_id':ids[1]}]}))
 claims=tmp_path/'artifacts/assignment-claims';claims.mkdir(parents=True);(claims/'old.json').write_text(json.dumps({'task_id':ids[2]}))
 fetched=[]
 monkeypatch.setattr(m.upstream,'fetch',lambda url:fetched.append(url) or body)
 output=tmp_path/'new';monkeypatch.setattr(sys,'argv',['reserve','--output',str(output),'--seed','fixed'])
 m.main();first=(output/'selection.json').read_bytes();reservation=json.loads((output/'reservation.json').read_text());assert len(fetched)==18
 selected=reservation['development'][0]['instance_id'];(claims/'new.json').write_text(json.dumps({'task_id':selected}))
 m.main();assert (output/'selection.json').read_bytes()==first;assert len(fetched)==18
 assert all(ids[1] not in url for url in fetched)
