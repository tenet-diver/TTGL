"""The native adapter is composed end-to-end with synthetic transport and actor only."""
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from contextlib import ExitStack
import subprocess,sys
from ttgl.experience_routing.native_replay import run_native_replay
from ttgl.experience_routing.checkpoints import CheckpointStore
from ttgl.experience_routing.fixtures import fixture_plan,FixtureBackend
from ttgl.experience_routing.replay import replay_manifest
from ttgl.experience_routing.io import digest,write_new

class NativeReplayTests(TestCase):
    def exercise(self,condition):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);w=root/'original';w.mkdir();(w/'accepted-dependency').write_text('retained prior source')
            plan=fixture_plan();node=plan['nodes'][0]
            cp=CheckpointStore(root/'checkpoint',w,base_commit='base',environment_digest='image').capture('fixture-task','square',node,['accepted-artifact'])
            assignment=next(a for a in replay_manifest([cp],development_parents=['fixture-task'],holdout_parents=[])['assignments'] if a['condition']==condition)
            spec={'condition':condition,'checkpoint_id':cp['checkpointId'],'contract_hash':digest(node),'shadow_memory_publication':False,'arm':'S0'}
            config={'replay':spec,'private_output_root':str(root),'arms':['S0'],'project_id':'fixture','study_id':'model-free-replay','snapshots':{'S0':'snapshot'},'source_home':'unused','source_account_hash':'unused','models':{'small':'fixture-small','large':'fixture-large'},'budgets':{'maximum_invocations':1,'maximum_model_tokens':100,'maximum_elapsed_seconds':60},'per_parent':{'maximum_invocations':1,'maximum_model_tokens':100,'maximum_elapsed_seconds':60}}
            freeze=root/'freeze.json';write_new(freeze,{'root':str(root)})
            task={'task_id':'fixture-task','repo':'fixture','base_commit':'base','prompt':'Square','public_check_catalog':{'square':{'argv':[sys.executable,'-c','from square import run; assert run(3)==9']}}}
            qualified={'image_id':'image','image_review':{},'host_qualified':True,'replay_checkpoint_hashes':{cp['checkpointId']:cp['repositoryStateHash']},'memory_bytes':100,'cpus':1}
            values={'task_manifest':{'tasks':[task]},'exclusion_registry':{},'runtime_isolation_manifest':qualified,'model_catalog':{'codex_executable':'unused','codex_sha256':'unused','node_executable':'unused','models':{m:{'reasoning_effort':'low'} for m in ['fixture-small','fixture-large']}},'rate_scenario':{'models':{}}}
            replay_values={'checkpoint_manifest':cp,'node_contract':node,'original_plan':plan,
                'experience_packet':{'rawEvidence':['audited public source'],'sourceExperienceVersionIds':['prior-version']} if condition=='small_raw' else {'experiences':[{'versionId':'prior-version'}]},
                'retrieval_query':{'taskInstanceId':'fixture-task','workItemId':'square','repositoryStateHash':cp['repositoryStateHash'],'arm':'S0','memorySnapshotId':'snapshot'},
                'raw_packet_provenance':{'visibility':'runtime_public','reviewed':True,'rawEvidenceHash':digest(['audited public source']),'sourceVersionIds':['prior-version']}}
            kinds=[];operations=[];closed=[]
            class Client:
                def __init__(self,*a,**kw):pass
                def record(self,kind,value):operations.append(kind)
                def read(self,query,versions):return {'experiences':[{'versionId':'prior-version'}]}
                def retain_file(self,p,**kw):return {'artifactId':digest(kw)}
            class Actor:
                def __init__(self,**kw):pass
                def start(self,w):return str(w)
                def after_attempt(self,w):pass
                def public_check(self,argv,w,timeout):
                    r=subprocess.run(argv,cwd=w,capture_output=True,timeout=timeout)
                    return {'returncode':r.returncode,'output':r.stdout.decode(),'infrastructure_error':False}
                def close(self):closed.append(True)
            class Native(FixtureBackend):
                def __init__(self,**kw):super().__init__(kw['container'])
                def complete(self,r):kinds.append((r.kind,r.model));return super().complete(r)
            prefix='ttgl.experience_routing.native_replay.'
            with ExitStack() as stack:
                for key,value in [('verify_freeze',lambda f:config),('pinned',lambda c,k,r:values[k]),('replay_pin',lambda c,k,r:replay_values[k]),('ExperienceClient',Client),('DockerWorkspace',Actor),('RecordedCodexBackend',Native)]:stack.enter_context(patch(prefix+key,value))
                result=run_native_replay(freeze,assignment,root/'run')
            self.assertTrue(result['complete']);self.assertEqual(result['scope'],'subtask_replay')
            self.assertEqual(kinds,[('coding','fixture-large' if condition=='large_structured' else 'fixture-small')]);self.assertNotIn('reuse',operations);self.assertNotIn('ingest-native',operations)
            self.assertFalse(result['shadow_memory_publication']);self.assertEqual(result['usage']['native_tokens'],12)
            self.assertEqual((root/'run/source/accepted-dependency').read_text(),'retained prior source');self.assertEqual(len(closed),1)

    def test_exact_node_executes_each_condition_without_parent_planning_or_shadow_annotation(self):
        for condition in ['small_empty','small_raw','small_structured','large_structured']:
            with self.subTest(condition=condition):self.exercise(condition)
