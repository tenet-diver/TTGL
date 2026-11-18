"""Execute campaign orchestration with synthetic transport, storage and actors."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import ExitStack
from ttgl.experience_routing import campaign
from ttgl.experience_routing.fixtures import fixture_plan,FixtureBackend
from ttgl.experience_routing.checkpoints import manifest
from ttgl.experience_routing.io import write_new,read,digest
from ttgl.personal import Response

class CampaignTests(unittest.TestCase):
    def exercise(self,root,arms=('LPM','SFM','HRM'),maximum_invocations=20,broken_source=False,broken_actor=False,broken_native=False):
        source=root/'base';source.mkdir();(source/'protected.txt').write_text('original')
        task={'task_id':'fixture-task','repo':'public/fixture','base_commit':'base','prompt':'Arithmetic fixture',
              'public_check_catalog':{n:{'argv':[sys.executable,'-c',f'from {n} import run; assert run(3)=={9 if n=="square" else -3}']} for n in ['square','negate']}}
        config={'study_id':'model-free','project_id':'fixture','private_output_root':str(root),'arms':list(arms),
            'budgets':{'maximum_parent_assignments':10,'maximum_elapsed_seconds':60,'maximum_invocations':maximum_invocations,'maximum_model_tokens':10000},
            'per_parent':{'maximum_elapsed_seconds':60,'maximum_invocations':10,'maximum_model_tokens':1000},
            'snapshots':{a:'snapshot-'+a for a in arms},'models':{'large':'fixture-large','small':'fixture-small'},'mode':'frozen_memory',
            'source_home':'not-used','source_account_hash':'not-used','watermark':0,'policy_version':'fixture','order_seed':1,
            'routing':{'threshold':.9,'minimum_independent_tasks':3},'maximum_large_fallbacks_per_node':1}
        pins={'task_manifest':{'tasks':[task]},'exclusion_registry':{},'model_catalog':{'codex_executable':'unused','codex_sha256':'unused','node_executable':'unused','models':{m:{'reasoning_effort':'low'} for m in ['fixture-small','fixture-large']}},
            'rate_scenario':{'models':{m:{'input':1,'cached':.1,'output':2} for m in ['fixture-small','fixture-large']}},
            'runtime_isolation_manifest':{'host_qualified':True,'workspaces':{'fixture-task':str(source)},'source_hashes':{'fixture-task':'wrong' if broken_source else manifest(source)['state_hash']},'image_id':'fixture','image_review':{},'memory_bytes':100,'cpus':1,'evaluator_revision':'fixture','score_label':'fixture'},
            'execution_fairness_manifest':{'assignment_order':[{'task_id':'fixture-task','arm':a} for a in arms]}}
        freeze=root/'freeze.json';write_new(freeze,{'root':str(root)})
        clients=[];backend_calls=[];closed=[]
        class Client:
            scope={}
            def __init__(self,*args,**kwargs):self.searches=[];clients.append(self)
            def search(self,q):self.searches.append(q);return {'packet':{'experiences':[]}}
            def retain_file(self,p,*,kind,identity):return {'artifactId':digest([kind,identity])}
            def record(self,*args):pass
        class Actor:
            def __init__(self,**kwargs):self.root=kwargs['root'];self.root.mkdir(parents=True)
            def start(self,w):
                if broken_actor:raise OSError('actor startup failure')
                write_new(self.root/'runtime-isolation.json',{'fixture_only':True});return str(w)
            def before_attempt(self,w):pass
            def after_attempt(self,w):pass
            def public_check(self,argv,w,timeout):
                import subprocess
                result=subprocess.run(argv,cwd=w,capture_output=True,timeout=timeout)
                return {'returncode':result.returncode,'output':result.stdout.decode(),'infrastructure_error':False}
            def close(self):closed.append(True)
        class Native(FixtureBackend):
            def __init__(self,**kwargs):super().__init__(Path(kwargs['container']));self.rollout_artifacts=[]
            def complete(self,r):
                backend_calls.append(r.kind)
                if broken_native:raise OSError('lost native response')
                if r.kind=='planning':
                    required=json.loads(r.prompt)['requiredIds'];p=fixture_plan();p.update(required)
                    for n in p['nodes']:n['planRevisionId']=required['planRevisionId']
                    return Response(text=json.dumps(p),thread_id=r.request_id,usage={'input_tokens':10,'cached_input_tokens':0,'output_tokens':2},elapsed_seconds=.01)
                return super().complete(r)
        with ExitStack() as stack:
            stack.enter_context(patch.object(campaign,'verify_freeze',return_value=config))
            stack.enter_context(patch.object(campaign,'pinned',side_effect=lambda c,k,r:pins[k]))
            stack.enter_context(patch.object(campaign,'ExperienceClient',Client))
            stack.enter_context(patch.object(campaign,'DockerWorkspace',Actor))
            stack.enter_context(patch.object(campaign,'RecordedCodexBackend',Native))
            value=campaign.run_campaign(freeze,root/'run')
        return value,backend_calls,clients,closed

    def test_shared_plan_reconciles_actual_and_logical_policy_tokens_and_latency(self):
        with tempfile.TemporaryDirectory() as d:
            result,calls,clients,closed=self.exercise(Path(d))
            self.assertTrue(result['complete']);self.assertEqual(calls.count('planning'),1)
            self.assertEqual(result['observed_actual_invocations'],7);self.assertEqual(result['observed_actual_tokens'],84)
            self.assertEqual([r['deployment_usage']['tokens'] for r in result['results']],[36,36,36])
            self.assertEqual([r['budget']['used_invocations'] for r in result['results']],[3,3,3])
            self.assertEqual(len(closed),3)
            initial=clients[0].searches[0]['repositoryStateHash']
            node_hashes=[q['repositoryStateHash'] for q in clients[0].searches if q['phase']=='plan_node']
            self.assertIn(initial,node_hashes);self.assertGreater(len(set(node_hashes)),1)
    def test_global_actual_call_cap_is_separate_from_logical_shared_plan_reservations(self):
        with tempfile.TemporaryDirectory() as d:
            result,calls,_,_=self.exercise(Path(d),maximum_invocations=6)
            self.assertFalse(result['complete']);self.assertEqual(len(calls),6)
            self.assertEqual(result['observed_actual_invocations'],6);self.assertEqual(result['results'][-1]['public_state'],'budget_exhausted')
    def test_preparation_failure_is_recorded_before_any_model_attempt(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaises(ValueError):self.exercise(root,broken_source=True)
            stop=read(root/'run/stopped.json');self.assertEqual(stop['observed_actual_invocations'],0);self.assertIsNone(stop['current_usage'])
    def test_actor_startup_failure_is_retained_and_cleaned_up(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaises(OSError):self.exercise(root,broken_actor=True)
            self.assertFalse(read(root/'run/stopped.json')['complete'])
    def test_last_assignment_uncertainty_does_not_become_campaign_completion(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            # Planner ambiguity stops before any executor; the root stop receipt
            # retains its unknown measured usage instead of advancing another arm.
            with self.assertRaises(Exception):self.exercise(root,arms=('LPM',),broken_native=True)
            stop=read(root/'run/stopped.json');self.assertEqual(stop['observed_actual_invocations'],1)
            self.assertIsNone(stop['current_usage']['native_tokens']);self.assertFalse(stop['complete'])

if __name__=='__main__':unittest.main()
