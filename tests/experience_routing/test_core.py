import copy
import json
from pathlib import Path
import tempfile
import unittest
from ttgl.personal import Request,Response
from ttgl.experience_routing.io import digest,write_new,file_digest
from ttgl.experience_routing.contracts import validate,outcome
from ttgl.experience_routing.fixtures import fixture_plan,run_fixture
from ttgl.experience_routing.plans import PlanState
from ttgl.experience_routing.ledger import UsageLedger,Budget,BudgetExhausted
from ttgl.experience_routing.checkpoints import CheckpointStore,manifest,replay_snapshot
from ttgl.experience_routing.client import ExperienceClient
from ttgl.experience_routing.runtime import Invocations,UncertainInvocation,RetainedInvocation
from ttgl.experience_routing.benchmarks import public_task,assert_exposure,pinned_evaluator
from ttgl.experience_routing.analysis import paired,annotation_audit,learning_curves
from ttgl.experience_routing.inventory import build_splits
from ttgl.experience_routing.config import validate_config,freeze,verify_freeze
from ttgl.experience_routing.replay import replay_manifest

class CoreTests(unittest.TestCase):
 def test_plan_cycles_unknown_paths_and_duplicate_criteria(self):
  for mutation in ('cycle','unknown','path','criterion'):
   p=fixture_plan()
   if mutation=='cycle':p['nodes'][0]['dependsOn']=['negate'];p['nodes'][1]['dependsOn']=['square']
   if mutation=='unknown':p['nodes'][0]['dependsOn']=['absent']
   if mutation=='path':p['nodes'][0]['allowedWritePaths']=['../private']
   if mutation=='criterion':p['nodes'][0]['acceptanceCriteria']*=2
   with self.assertRaises(ValueError):validate('plan',p)
 def test_dependency_blocking(self):
  p=fixture_plan();p['nodes'][1]['dependsOn']=['square'];state=PlanState(p,Budget(3,100,60))
  self.assertEqual([n['nodeId'] for n in state.ready()],['square']);state.finish('square','failed',False)
  self.assertEqual(state.states['negate'],'blocked');self.assertEqual(state.ready(),[])
 def test_replan_keeps_budget_attempts_and_contract_identity(self):
  budget=Budget(3,100,60);budget.reserve();state=PlanState(fixture_plan(),budget);state.finish('square','one',True)
  revised=copy.deepcopy(state.plan);revised['previousRevisionId']=revised['planRevisionId'];revised['planRevisionId']='new'
  for node in revised['nodes']:node['planRevisionId']='new'
  after=PlanState(revised,budget,previous=state);self.assertIs(after.budget,budget);self.assertEqual(after.budget.used_invocations,1);self.assertEqual(after.states['square'],'accepted');self.assertEqual(after.attempts['square'],['one'])
  revised['nodes'][0]['goal']='changed'
  with self.assertRaises(ValueError):PlanState(revised,budget,previous=state)
 def test_outcomes_require_public_scope(self):
  self.assertEqual(outcome([],True),'abstain');self.assertEqual(outcome([{'verdict':'pass'}],False),'abstain')
  self.assertEqual(outcome([{'verdict':'pass'}],True,cancelled=True),'abstain');self.assertEqual(outcome([{'verdict':'pass'}],True),'successful')
  self.assertEqual(outcome([{'verdict':'fail'},{'verdict':'pass'}],True),'unsuccessful')
 def test_checkpoint_reproduces_dependencies_untracked_modes_links_and_deletes(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);w=root/'actor';w.mkdir();(w/'file.py').write_text('old');(w/'run.sh').write_text('exit 0');(w/'run.sh').chmod(0o755);(w/'link').symlink_to('file.py')
   store=CheckpointStore(root/'evidence',w,base_commit='base',environment_digest='image');cp=store.capture('parent','node',{},['earlier-patch'])
   (w/'file.py').unlink();(w/'new').write_text('new');self.assertFalse(store.admissible(cp,['new'],[])['passed']);store.restore(cp)
   self.assertEqual(manifest(w),cp['source_manifest']);self.assertFalse((w/'new').exists());self.assertTrue((w/'link').is_symlink())
   replay_snapshot(cp,root/'replay');self.assertEqual(manifest(root/'replay'),manifest(w));self.assertEqual(cp['dependencyArtifactIds'],['earlier-patch'])
 def test_escape_and_protected_write_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);w=root/'actor';w.mkdir();(w/'protected').write_text('old');s=CheckpointStore(root/'checkpoints',w,base_commit='base',environment_digest='image');cp=s.capture('task','node',{})
   (w/'protected').write_text('bad');self.assertFalse(s.admissible(cp,['**'],['protected'])['passed'])
   (w/'escape').symlink_to('/etc/passwd')
   with self.assertRaises(ValueError):manifest(w)
 def test_cumulative_deltas_dedup_and_unknown_usage(self):
  with tempfile.TemporaryDirectory() as d:
   ledger=UsageLedger(d,{'m':{'input':1,'cached':.1,'output':2}})
   def add(identity,input,output,cache=2):
    req=Request(identity,'m','coding','prompt',Path(d),{},60,thread_id=None if identity=='a' else 'thread')
    response=Response(thread_id='thread',usage={'input_tokens':input,'cached_input_tokens':cache,'output_tokens':output,'cache_write_input_tokens':0,'reasoning_output_tokens':0},usage_scope='thread_cumulative',usage_evidence='reported')
    return ledger.record(req,response,'small_execution','operational',identity,response_ids=[identity])
   first=add('a',10,4);second=add('b',15,6);self.assertEqual(second['delta']['total_tokens'],7)
   add('b',15,6);self.assertEqual(ledger.totals()['actual_invocations'],2);self.assertEqual(ledger.totals()['native_tokens'],21)
   self.assertEqual(UsageLedger(d).totals()['native_tokens'],21);ledger.logical_shared_charge('a','HRM');self.assertEqual(ledger.totals()['actual_invocations'],2)
   req=Request('unknown','m','coding','p',Path(d),{},60);ledger.record(req,Response(),'planning','operational','unknown');self.assertIsNone(ledger.totals()['native_tokens']);self.assertIsNone(ledger.totals()['scenario_cost'])
 def test_budget_and_unknown_transport_never_replay(self):
  with tempfile.TemporaryDirectory() as d:
   class Backend:
    def complete(self,request):return Response(status='timeout')
   budget=Budget(2,100,60);calls=Invocations(Path(d)/'calls',Backend(),UsageLedger(Path(d)/'ledger'),budget)
   req=Request('once','m','coding','prompt',Path(d),{},60)
   with self.assertRaises(UncertainInvocation):calls.call(req,'small_execution')
   with self.assertRaises(RetainedInvocation):calls.call(req,'small_execution')
   with self.assertRaises(BudgetExhausted):budget.reserve()
   self.assertEqual(budget.used_invocations,1)
 def test_runtime_fixture_full_control_flow_and_independent_replay(self):
  with tempfile.TemporaryDirectory() as d:
   report=run_fixture(Path(d)/'fixture');self.assertTrue(report['passed']);self.assertEqual(len(report['cases']),6);self.assertEqual(report['actual_model_calls'],0)
 def test_public_projection_and_exclusions(self):
  record={'task_id':'one','repo':'repository','base_commit':'base','prompt':'public','gold_patch':'secret','test_patch':'secret','grade':True}
  self.assertEqual(set(public_task(record)),{'task_id','repo','base_commit','prompt'})
  with self.assertRaises(ValueError):assert_exposure(public_task(record),{'task_ids':['one']})
 def test_empty_grades_and_fixtures_cannot_claim_target(self):
  self.assertFalse(paired([])['target90_met'])
  rows=[{'task_id':'t','arm':a,'passed':True,'grade_valid':True,'scenario_cost':c,'fixture_only':True} for a,c in [('LPM',100),('HRM',1)]]
  report=paired(rows);self.assertEqual(report['scenario_saving'],.99);self.assertFalse(report['target90_met'])
  rows[1]['scenario_cost']=None;self.assertIsNone(paired(rows)['scenario_saving'])
 def test_annotation_false_success_denominator_and_abstentions(self):
  r=annotation_audit([{'reference':a,'prediction':b} for a,b in [('successful','successful'),('unsuccessful','successful'),('unsuccessful','abstain')]])
  self.assertEqual(r['false_success_rate'],.5);self.assertEqual(r['abstentions'],1)
 def test_parent_disjoint_splits_and_replays(self):
  tasks=[{'task_id':str(i),'repo':'r','base_commit':'b','synthetic_parent':'same','split':s} for i,s in enumerate(['memory_build','final_holdout'])]
  with self.assertRaises(ValueError):build_splits(tasks,{})
  with self.assertRaises(ValueError):replay_manifest([],development_parents=['p'],holdout_parents=['p'])
 def test_arm_lineages_and_chronology(self):
  rows=[{'order':1,'arm':arm,'sequence':n,'memory_lineage':arm,'family':'parsing'} for arm in ['LPM','HRM'] for n in [0,1]]
  curve=learning_curves(rows);self.assertEqual([r['prior_family_exposures'] for r in curve],[0,1,0,1])
 def test_service_loopback_and_draft_execution_gates(self):
  for url in ['https://remote.invalid/api/experience','http://localhost/api/experience','http://127.0.0.1/private']:
   with self.assertRaises(ValueError):ExperienceClient('p','s',url,token='fixture')
  draft={'schema_version':1,'study_id':'s','mode':'frozen_memory','automatic_retries':0,'models':{'annotator':'gpt-6-luna'},'arms':['HRM'],'allow_model_execution':False}
  self.assertFalse(validate_config(draft)['execution_ready'])
  with self.assertRaises(ValueError):validate_config(draft,execution=True)

if __name__=='__main__':unittest.main()

class FreezeAndReplayTests(unittest.TestCase):
 def test_freeze_detects_changed_prompt_and_gate_receipts(self):
  from ttgl.experience_routing.config import REQUIRED_PINS,REQUIRED_GATES
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);prompt=root/'prompt.txt';prompt.write_text('frozen public instructions')
   gate=root/'gate.json';write_new(gate,{'qualified_fixture':True})
   ready=root/'readiness.json';write_new(ready,{'gates':{k:{'passed':True,'receipt_path':'gate.json','receipt_sha256':file_digest(gate)} for k in REQUIRED_GATES}})
   sources=root/'sources.json';write_new(sources,{'files':{'prompt.txt':file_digest(prompt)}})
   pins={}
   for key in REQUIRED_PINS:
    if key=='source_commit':pins[key]='fixture-source';continue
    path=ready if key=='readiness_manifest' else sources if key=='source_hashes' else root/(key+'.json')
    if not path.exists():write_new(path,{'fixture':key})
    pins[key]={'path':path.name,'sha256':file_digest(path)}
   cfg={'schema_version':1,'study_id':'fixture','mode':'frozen_memory','automatic_retries':0,'models':{'annotator':'gpt-6-luna'},'arms':['HRM'],'allow_model_execution':True,'pins':pins,
        'budgets':{'maximum_parent_assignments':1,'maximum_invocations':1,'maximum_model_tokens':100,'maximum_elapsed_seconds':60}}
   path=root/'config.json';write_new(path,cfg);receipt=freeze(path,root/'freeze.json');verify_freeze(receipt)
   prompt.write_text('changed public instructions')
   with self.assertRaises(ValueError):verify_freeze(receipt)
 def test_native_response_identity_reingestion_contributes_once(self):
  with tempfile.TemporaryDirectory() as d:
   ledger=UsageLedger(d)
   for name in ['one','reingested']:
    req=Request(name,'m','coding','prompt',Path(d),{},60)
    response=Response(thread_id=name,usage={'input_tokens':10,'cached_input_tokens':2,'output_tokens':3},usage_evidence='reported')
    row=ledger.record(req,response,'small_execution','operational',name,response_ids=['native-response'])
   self.assertEqual(ledger.totals()['native_tokens'],13);self.assertEqual(row['delta']['total_tokens'],0)
 def test_zero_tests_cannot_receive_an_independent_grade(self):
  import sys
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);patch=root/'candidate.patch';patch.write_text('fixture')
   script=root/'grader.py';script.write_text('import json; print(json.dumps('+repr({'tests_collected':0,'passed':True,'artifact_sha256':file_digest(patch),'evaluator_revision':'fixture'})+'))')
   manifest=root/'patch.json';write_new(manifest,{'artifact_path':str(patch),'artifact_sha256':file_digest(patch),'evaluator_revision':'fixture'})
   command=[sys.executable,str(script)]
   with self.assertRaises(ValueError):pinned_evaluator(command,command_hash=digest(command),patch_manifest=manifest,output=root/'grade',timeout=10)
