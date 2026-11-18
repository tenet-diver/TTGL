"""Model-free regression coverage for retained execution and failure boundaries."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from ttgl.personal import Request, Response
from ttgl.experience_routing.io import digest,read,write_new,file_digest
from ttgl.experience_routing.runtime import Invocations,PreparationFailure,UncertainInvocation,ParentRunner
from ttgl.experience_routing.ledger import UsageLedger,Budget,BudgetExhausted
from ttgl.experience_routing.backend import NativeCallFailure,RecordedCodexBackend
from ttgl.experience_routing.fixtures import fixture_plan,FixtureBackend
from ttgl.experience_routing.plans import PlanState
from ttgl.experience_routing.checkpoints import CheckpointStore,manifest
from ttgl.experience_routing.verification import PublicVerifier
from ttgl.experience_routing.policy import RoutingPolicy
from ttgl.experience_routing.replay import replay_manifest,replay_registered,execute_checkpoint


def measured(text='{}',seconds=.001):
    return Response(text=text,thread_id='synthetic',usage={'input_tokens':10,'cached_input_tokens':0,'output_tokens':2},elapsed_seconds=seconds)

class AccountingTests(unittest.TestCase):
    def test_preflight_failure_does_not_reserve_or_invoke(self):
        with tempfile.TemporaryDirectory() as d:
            class Backend:
                def preflight(self,r):raise ValueError('missing reviewed runtime')
                def complete(self,r):raise AssertionError('must not invoke')
            budget=Budget(2,100,60);ledger=UsageLedger(Path(d)/'ledger');calls=Invocations(Path(d)/'calls',Backend(),ledger,budget)
            with self.assertRaises(PreparationFailure):calls.call(Request('one','m','coding','p',Path(d),{},60),'small_execution')
            self.assertEqual(budget.used_invocations,0);self.assertEqual(ledger.totals()['actual_invocations'],0)
    def test_partial_usage_survives_raw_archive_failure(self):
        with tempfile.TemporaryDirectory() as d:
            class Backend:
                def complete(self,r):raise NativeCallFailure(OSError('archive unavailable'),measured())
            budget=Budget(2,100,60);ledger=UsageLedger(Path(d)/'ledger');calls=Invocations(Path(d)/'calls',Backend(),ledger,budget)
            with self.assertRaises(UncertainInvocation):calls.call(Request('one','m','coding','p',Path(d),{},60),'small_execution')
            self.assertEqual(ledger.totals()['native_tokens'],12);self.assertEqual(budget.used_tokens,12)
            self.assertTrue((Path(d)/'calls/one/uncertain.json').exists())
    def test_unknown_backend_exception_is_not_free_inference(self):
        with tempfile.TemporaryDirectory() as d:
            class Backend:
                def complete(self,r):raise OSError('lost response')
            budget=Budget(2,100,60);ledger=UsageLedger(Path(d)/'ledger');calls=Invocations(Path(d)/'calls',Backend(),ledger,budget)
            with self.assertRaises(UncertainInvocation):calls.call(Request('one','m','coding','p',Path(d),{},60),'small_execution')
            self.assertTrue(budget.unknown_usage);self.assertIsNone(ledger.totals()['native_tokens'])
            with self.assertRaises(BudgetExhausted):budget.reserve()
    def test_call_deadline_is_capped_to_parent_budget(self):
        with tempfile.TemporaryDirectory() as d:
            seen=[]
            class Backend:
                def complete(self,r):seen.append(r.timeout_seconds);return measured()
            calls=Invocations(Path(d)/'calls',Backend(),UsageLedger(Path(d)/'ledger'),Budget(2,100,.5))
            calls.call(Request('one','m','coding','p',Path(d),{},600),'planning')
            self.assertLessEqual(seen[0],.5)
    def test_shared_planner_charges_tokens_latency_and_price_without_double_actual_spend(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);rates={'m':{'input':1,'cached':.1,'output':2}}
            source=UsageLedger(root/'source',rates);r=source.record(Request('plan','m','planning','p',root,{},60),measured(seconds=4),'planning','operational','hash')
            replay=UsageLedger(root/'replay',rates);charge=replay.logical_shared_charge('plan','HRM',receipt=r)
            replay.logical_shared_charge('plan','HRM',receipt=r)
            self.assertEqual(replay.totals()['actual_invocations'],0)
            total=replay.deployment_totals();self.assertEqual(total['tokens'],12);self.assertEqual(total['model_seconds'],4);self.assertEqual(total['logical_invocations'],1)
            self.assertEqual(total['scenario_cost'],r['scenario_cost'])
            budget=Budget(3,100,10);budget.charge_shared(charge)
            self.assertEqual(budget.used_tokens,12);self.assertLessEqual(budget.remaining_seconds,6)
            self.assertEqual(budget.receipt()['logical_shared_invocations'],1)
            source.logical_shared_charge('plan','LPM');self.assertEqual(source.deployment_totals()['tokens'],12)
            with self.assertRaises(ValueError):replay.logical_shared_charge('plan','HRM',receipt={**r,'elapsed_seconds':8})
    def test_scenario_cap_stops_unpriced_or_exhausted_policy(self):
        for cost in (None,2):
            b=Budget(5,100,60,maximum_scenario_cost=1);b.charge({'delta':{'total_tokens':10},'scenario_cost':cost})
            with self.assertRaises(BudgetExhausted):b.reserve()

class RuntimeTests(unittest.TestCase):
    def run_case(self,root,behavior='success',backend_factory=None,verifier_factory=None,memory=None):
        w=root/'actor';w.mkdir();(w/'protected.txt').write_text('original')
        backend=backend_factory(w) if backend_factory else FixtureBackend(w,behavior)
        budget=Budget(6,1000,60);ledger=UsageLedger(root/'ledger');calls=Invocations(root/'calls',backend,ledger,budget,origin='fixture')
        checks={n:{'argv':[sys.executable,'-c',f'from {n} import run; assert run(3)=={9 if n=="square" else -3}']} for n in ['square','negate']}
        verifier=verifier_factory(checks,root) if verifier_factory else PublicVerifier(checks,['protected.txt'],root/'checks')
        store=CheckpointStore(root/'checkpoints',w,base_commit='fixture',environment_digest='fixture')
        cfg={'models':{'fixture-large':{'reasoning_effort':'low'},'fixture-small':{'reasoning_effort':'low'}},'watermark':0,'memory_snapshot_id':'fixture','policy_version':'fixture','mode':'frozen_memory'}
        runner=ParentRunner(task={'task_id':'fixture-task','prompt':'Public arithmetic'},arm='LPM',workspace=w,checkpoints=store,verifier=verifier,invocations=calls,policy=RoutingPolicy(small='fixture-small',large='fixture-large',mode='all_large'),memory=memory or (lambda *a:{'experiences':[]}),output=root/'parent',config=cfg)
        return runner,backend,budget
    def test_last_node_uncertainty_has_durable_terminal_state(self):
        with tempfile.TemporaryDirectory() as d:
            class Broken(FixtureBackend):
                def complete(self,r):raise OSError('unavailable after start')
            root=Path(d);runner,backend,budget=self.run_case(root,backend_factory=Broken)
            result=runner.run(fixture_plan());self.assertEqual(result['public_state'],'uncertain')
            terminals=list((root/'parent/attempts').glob('*.json'));self.assertEqual(len(terminals),1)
            self.assertEqual(read(terminals[0])['status'],'uncertain');self.assertEqual(result['node_states']['square'],'uncertain')
    def test_cancellation_is_sealed_and_never_falls_back(self):
        with tempfile.TemporaryDirectory() as d:
            class Cancel(FixtureBackend):
                def complete(self,r):raise KeyboardInterrupt()
            root=Path(d);runner,backend,budget=self.run_case(root,backend_factory=Cancel)
            result=runner.run(fixture_plan());self.assertEqual(result['public_state'],'uncertain')
            self.assertEqual(result['uncertainty']['type'],'KeyboardInterrupt');self.assertEqual(budget.used_invocations,1)
    def test_final_whole_task_failure_is_not_overridden_by_node_success(self):
        with tempfile.TemporaryDirectory() as d:
            class WholeFailure(PublicVerifier):
                def verify(self,*args,**kwargs):
                    v,t=super().verify(*args,**kwargs)
                    if kwargs.get('scope')=='whole_task':v['verdict']='fail'
                    return v,t
            root=Path(d);runner,_,_=self.run_case(root,verifier_factory=lambda c,r:WholeFailure(c,[],r/'checks'))
            result=runner.run(fixture_plan());self.assertEqual(result['public_state'],'unsuccessful');self.assertTrue(all(s=='accepted' for s in result['node_states'].values()))
    def test_verifier_exception_keeps_completed_model_usage_and_terminal_attempt(self):
        with tempfile.TemporaryDirectory() as d:
            class BrokenVerifier(PublicVerifier):
                def verify(self,*args,**kwargs):raise ValueError('changed public contract')
            root=Path(d);runner,_,budget=self.run_case(root,verifier_factory=lambda c,r:BrokenVerifier(c,[],r/'checks'))
            result=runner.run(fixture_plan());self.assertEqual(result['public_state'],'infrastructure_error');self.assertEqual(budget.used_tokens,12)
            self.assertEqual(len(list((root/'parent/attempts').glob('*.json'))),1)
    def test_unknown_public_environment_does_not_trigger_model_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);runner,backend,budget=self.run_case(root,verifier_factory=lambda c,r:PublicVerifier(c,[],r/'checks',executor=lambda *a:{'returncode':None,'output':'unavailable','infrastructure_error':True}))
            result=runner.run(fixture_plan());self.assertEqual(result['public_state'],'infrastructure_error');self.assertEqual(len(backend.calls),1)
    def test_aggregate_public_check_timeout_is_not_reset_for_each_criterion(self):
        with tempfile.TemporaryDirectory() as d:
            observed=[]
            def execute(argv,w,timeout):observed.append(timeout);time.sleep(.025);return {'returncode':0,'output':'fixture','infrastructure_error':False}
            root=Path(d);verifier=PublicVerifier({x:{'argv':['fixture']} for x in ['a','b']},[],root/'checks',executor=execute)
            result,_=verifier.verify({'nodeId':'node','acceptanceCriteria':[{'id':'a'},{'id':'b'}]},'once',root,timeout=.01)
            self.assertEqual(len(observed),1);self.assertEqual(result['criterionResults'][1]['verdict'],'unknown')
    def test_replanning_cannot_reset_failed_nodes_budget_or_drop_accepted_contracts(self):
        budget=Budget(5,100,60);old=PlanState(fixture_plan(),budget);old.finish('square','prior',False)
        p=copy.deepcopy(old.plan);p.update(previousRevisionId=p['planRevisionId'],planRevisionId='revision-2')
        for n in p['nodes']:n['planRevisionId']='revision-2'
        revised=PlanState(p,budget,old);self.assertEqual(revised.states['square'],'failed')
        with self.assertRaises(ValueError):PlanState(p,Budget(5,100,60),old)
        p['nodes']=p['nodes'][:1]
        with self.assertRaises(ValueError):PlanState(p,budget,old)

class ReplayTests(unittest.TestCase):
    def test_exact_checkpoint_replay_restores_cumulative_source_and_unchanged_contract(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);w=root/'source';w.mkdir();(w/'accepted-dependency').write_text('retained')
            node=fixture_plan()['nodes'][0];store=CheckpointStore(root/'cp',w,base_commit='base',environment_digest='env');cp=store.capture('parent',node['nodeId'],node,['accepted'])
            assignments=replay_manifest([cp],development_parents=['parent'],holdout_parents=[])['assignments']
            seen=[]
            def execute(contract,workspace,packet,executor):
                self.assertEqual(contract,node);self.assertEqual((workspace/'accepted-dependency').read_text(),'retained');seen.append(executor);return {'uncertain':False}
            for i,a in enumerate(assignments):execute_checkpoint(a,cp,node,root/str(i),execute,packet={'rawEvidence':['source'],'experiences':[{'versionId':'frozen'}]})
            self.assertEqual(seen.count('large'),1)
            bad={**assignments[0],'contract_hash':'changed'}
            with self.assertRaises(ValueError):execute_checkpoint(bad,cp,node,root/'bad',execute)
            self.assertFalse((root/'bad').exists())
    def test_replay_exception_is_retained_without_retry(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'replay';m={'assignments':[{'assignment_id':'once'}]}
            def execute(a):raise OSError('lost transport')
            with self.assertRaises(OSError):replay_registered(m,execute,root)
            self.assertTrue((root/'once/uncertain.json').exists());self.assertFalse(read(root/'stopped.json')['complete'])
            with self.assertRaises(ValueError):replay_registered(m,execute,root)

if __name__=='__main__':unittest.main()

class ReportingTests(unittest.TestCase):
    def test_missing_failed_assignment_cannot_disappear_from_primary_cost_or_target(self):
        from ttgl.experience_routing.analysis import paired
        rows=[{'task_id':'matched','arm':a,'passed':True,'grade_valid':True,'scenario_cost':c} for a,c in [('LPM',100),('HRM',1)]]
        rows.append({'task_id':'missing-candidate','arm':'LPM','passed':True,'grade_valid':True,'scenario_cost':100})
        result=paired(rows);self.assertEqual(result['assigned_comparison_tasks'],2);self.assertFalse(result['target90_met']);self.assertIsNone(result['scenario_saving']);self.assertEqual(result['unpaired_task_ids'],['missing-candidate'])
    def test_invalid_grade_boolean_and_nonfinite_cost_are_rejected(self):
        from ttgl.experience_routing.analysis import paired
        for bad in [{'passed':'false','scenario_cost':1},{'passed':True,'scenario_cost':float('nan')},{'passed':True,'scenario_cost':-1}]:
            with self.assertRaises(ValueError):paired([{'task_id':'t','arm':'HRM','grade_valid':True,**bad}])

class NativeSpoolTests(unittest.TestCase):
    def test_each_attempt_retains_its_own_streams_and_partial_usage_on_archive_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);home=root/'canonical';home.mkdir()
            write_new(home/'auth.json',{'auth_mode':'chatgpt','tokens':{'account_id':'synthetic','access_token':'synthetic','refresh_token':'synthetic'}})
            from ttgl.experience_routing.backend import source_binding
            seen=[]
            class Client:
                def retain_file(self,p,*,kind,identity):
                    seen.append(identity)
                    if identity=='second:events.jsonl':raise OSError('storage unavailable')
                    return {'artifactId':digest(identity)}
            class Process:
                returncode=0;pid=100
                def __init__(self,command,**kwargs):
                    self.out=kwargs['stdout'];self.env=kwargs['env']
                def communicate(self,prompt,timeout):
                    self.out.write((json.dumps({'type':'thread.started','thread_id':'synthetic'})+'\n'+json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'{}'}})+'\n'+json.dumps({'type':'turn.completed','usage':{'input_tokens':10,'cached_input_tokens':0,'output_tokens':2}})+'\n').encode());self.out.flush()
                def wait(self):return 0
            backend=RecordedCodexBackend(executable=sys.executable,executable_sha256=file_digest(Path(sys.executable).resolve()),source_home=home,source_account_hash=source_binding(home)['account_hash'],output=root/'native',client=Client())
            with patch('ttgl.experience_routing.backend.subprocess.Popen',Process):
                first=backend.complete(Request('first','gpt-6-luna','planning','Fixture input',root,{},60,read_only=True))
                self.assertEqual(first.usage['input_tokens'],10)
                with self.assertRaises(NativeCallFailure) as caught:backend.complete(Request('second','gpt-6-luna','planning','Fixture input',root,{},60,read_only=True))
            self.assertEqual(caught.exception.response.usage['output_tokens'],2)
            self.assertIn('second:stderr.log',seen)
            self.assertTrue((root/'native/second/events.jsonl').exists());self.assertFalse((root/'native/second/client-home/auth.json').exists())
            self.assertEqual(backend.last_native_artifact_hash,file_digest(root/'native/second/events.jsonl'))

class OwnershipTests(unittest.TestCase):
    def test_cancelled_replan_nodes_block_dependents_without_resetting_attempts(self):
        p=fixture_plan();p['nodes'][1]['dependsOn']=['square'];b=Budget(4,100,60);old=PlanState(p,b)
        updated=copy.deepcopy(p);updated.update(previousRevisionId=p['planRevisionId'],planRevisionId='next',cancelledNodeIds=['square'])
        for n in updated['nodes']:n['planRevisionId']='next'
        state=PlanState(updated,b,old);self.assertEqual(state.states,{'square':'cancelled','negate':'blocked'});self.assertFalse(state.ready())
    def test_checkpoint_raw_source_artifact_is_private(self):
        import stat
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);w=root/'actor';w.mkdir();(w/'private').write_text('fixture')
            cp=CheckpointStore(root/'cp',w,base_commit='base',environment_digest='image').capture('t','n',{})
            self.assertEqual(stat.S_IMODE(Path(cp['archive_path']).stat().st_mode),0o600)
            self.assertEqual(stat.S_IMODE(Path(cp['archive_path']).parent.stat().st_mode),0o700)
    def test_failed_actor_start_removes_only_its_new_owned_container(self):
        from ttgl.experience_routing.execution import DockerWorkspace
        actor=object.__new__(DockerWorkspace);actor.memory=1024;actor.cpus=1;actor.image='fixture';seen=[]
        def docker(*args,**kwargs):
            seen.append(args)
            if args[0]=='start':raise RuntimeError('fixture start failure')
            return b''
        with patch('ttgl.experience_routing.execution.docker',docker):
            with self.assertRaises(RuntimeError):actor._create('owned-fixture')
        self.assertEqual(seen[-1],('rm','-f','owned-fixture'))

class ReplanExecutionTests(unittest.TestCase):
    def execute_case(self,root,always_fail=False):
        helper=RuntimeTests();runner,backend,budget=helper.run_case(root)
        original=backend.complete
        def complete(request):
            payload=json.loads(request.prompt);name=payload['node']['nodeId']
            if name=='square' or name=='repair-square' and always_fail:
                result=original(request);(backend.workspace/'square.py').write_text('def run(x): return x+1\n');return result
            if name=='repair-square':
                payload['node']['nodeId']='square'
                from dataclasses import replace
                return original(replace(request,prompt=json.dumps(payload)))
            return original(request)
        backend.complete=complete
        def revise(state,history,parent_budget):
            self.assertIs(parent_budget,budget)
            self.assertEqual(parent_budget.used_invocations,1)
            p=copy.deepcopy(state.plan);p.update(previousRevisionId=p['planRevisionId'],planRevisionId='repair-plan',continuedNodeIds=['negate'])
            for n in p['nodes']:n['planRevisionId']='repair-plan'
            p['nodes'][0].update(nodeId='repair-square',supersedesNodeIds=['square'])
            return p
        runner.replan=revise
        return runner.run(fixture_plan()),budget
    def test_material_replan_preserves_consumed_budget_and_failed_source(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);result,budget=self.execute_case(root)
            self.assertEqual(result['public_state'],'completed');self.assertEqual(result['replans'],1)
            self.assertEqual(budget.used_invocations,3)
            self.assertEqual(len(list((root/'parent/patches').glob('*.json'))),3)
    def test_a_second_failed_revision_cannot_create_an_unbounded_replan(self):
        with tempfile.TemporaryDirectory() as d:
            result,budget=self.execute_case(Path(d),always_fail=True)
            self.assertEqual(result['public_state'],'unsuccessful');self.assertEqual(result['replans'],1)
            self.assertEqual(budget.used_invocations,2)

class DenominatorTests(unittest.TestCase):
    def test_entirely_missing_parent_is_retained_and_a_registered_denominator_is_required(self):
        from ttgl.experience_routing.analysis import paired
        rows=[{'task_id':'observed','arm':a,'passed':True,'grade_valid':True,'scenario_cost':c} for a,c in [('LPM',100),('HRM',1)]]
        self.assertFalse(paired(rows)['target90_met'])
        complete=paired(rows,expected_task_ids=['observed']);self.assertTrue(complete['target90_met'])
        missing=paired(rows,expected_task_ids=['observed','missing-both-arms']);self.assertFalse(missing['target90_met']);self.assertEqual(missing['invalid_or_unresolved_pairs'],1);self.assertIsNone(missing['scenario_saving'])
