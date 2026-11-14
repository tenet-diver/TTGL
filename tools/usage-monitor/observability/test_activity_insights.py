import copy,json,time,unittest
from unittest.mock import patch
import test_task_history as fixtures
import activity_insights as a
import task_history as h
import analyst_mcp

class ActivityTests(unittest.TestCase):
 def setUp(self):
  self.fixture=fixtures.HistoryTests();self.fixture.setUp();self.addCleanup(self.fixture.tmp.cleanup)
  self.store=self.fixture.store;a.init(self.store)
  with self.store.connection() as c:c.execute('DELETE FROM assignments')
  self.body=a.collect(self.store);self.proposal={'title':'Repair pagination','goal':'Investigate cursor behavior and verify regression','task_type':'bugfix','tags':['pagination'],'turn_refs':[self.body['turns'][0]['ref']],'confidence':0.8,'subtasks':copy.deepcopy(self.fixture.result['subtasks'])}
  self.result={'summary':'One candidate task from recorded activity; outcome unverified.','tasks':[self.proposal],'suggestions':[{'title':'Use focused verification','rationale':'The evidence includes a targeted verification operation.','action':'Preserve a focused regression command in the workflow.','validation':'Compare full task quality and source outcomes before adopting.','risk':'Evidence is small; no measured improvement established.','step_ids':['step1']}]}
 def job(self,status='completed'):
  ident=str(time.time_ns());raw=json.dumps(self.body,sort_keys=True)
  with self.store.connection() as c:c.execute('INSERT INTO activity_insight_jobs(id,scope,snapshot,snapshot_hash,model,engine,status,created,result) VALUES(?,?,?,?,?,?,?,?,?)',(ident,'all',raw,'hash','test-model','ollama',status,time.time(),json.dumps(self.result) if status=='completed' else None))
  return ident
 def test_acceptance_creates_task_subtasks_tags_and_exact_source(self):
  result=a.apply_task(self.store,self.job(),0);task=result['task_id']
  detail=h.detail(self.store,task)
  self.assertEqual(len(detail['subtasks']),2);self.assertFalse(detail['stale']);self.assertEqual(detail['task']['status'],'unresolved')
  self.assertEqual(h.search(self.store,'regression')['items'][0]['task_id'],task)
  self.assertEqual(detail['jobs'][0]['engine'],'activity-derived');self.assertIsNone(detail['jobs'][0]['usage'])
 def test_acceptance_is_idempotent(self):
  job=self.job();first=a.apply_task(self.store,job,0)
  self.assertEqual(a.apply_task(self.store,job,0)['task_id'],first['task_id'])
 def test_explicit_assignment_protected(self):
  with self.store.connection() as c:c.execute('INSERT INTO assignments VALUES(?,?,?)',('session','turn',self.fixture.task))
  self.body=a.collect(self.store);job=self.job()
  with self.assertRaisesRegex(ValueError,'explicit task'):a.apply_task(self.store,job,0)
 def test_confirmed_native_task_cannot_be_regrouped(self):
  with self.store.connection() as c:
   c.execute('INSERT INTO task_discovery_tasks VALUES(?,?,?)',(self.fixture.task,'session','provisional source'))
   c.execute('INSERT INTO assignments VALUES(?,?,?)',('session','turn',self.fixture.task))
  self.store.mutate('task_status',{'id':self.fixture.task,'status':'completed','outcome':'User verified the task'})
  self.body=a.collect(self.store);self.assertFalse(self.body['turns'][0]['provisional'])
  with self.assertRaisesRegex(ValueError,'explicit task'):a.apply_task(self.store,self.job(),0)
 def test_source_changes_refuse_without_partial_tasks(self):
  job=self.job()
  with self.store.connection() as c:c.execute("UPDATE events SET name='changed' WHERE id='step0'");before=c.execute('SELECT count(*) FROM tasks').fetchone()[0]
  with self.assertRaisesRegex(ValueError,'Source steps changed'):a.apply_task(self.store,job,0)
  with self.store.connection() as c:self.assertEqual(c.execute('SELECT count(*) FROM tasks').fetchone()[0],before)
 def test_no_invented_suggestions_steps_or_duplicate_turns(self):
  for kind in ('step','duplicate','wrong-subtask'):
   r=copy.deepcopy(self.result)
   if kind=='step':r['suggestions'][0]['step_ids']=['foreign']
   if kind=='duplicate':r['tasks'].append(copy.deepcopy(r['tasks'][0]))
   if kind=='wrong-subtask':r['tasks'][0]['subtasks'][0]['step_ids']=['foreign']
   with self.subTest(kind=kind),self.assertRaises(ValueError):a.validate(r,self.body)
 def test_decisions_never_apply_code(self):
  job=self.job();result=a.decide(self.store,job,0,'accepted_for_trial','Check before changing code')
  self.assertFalse(result['applied_changes']);self.assertEqual(a.state(self.store)['latest']['decisions']['0']['decision'],'accepted_for_trial')
 def test_completed_model_and_rejected_model_retain_usage(self):
  job=self.job('queued')
  with patch.object(h,'local_analysis',return_value=(json.dumps(self.result),{'input_tokens':20,'output_tokens':10},True)):a.run(self.store,job)
  state=a.state(self.store);self.assertEqual(state['jobs'][0]['status'],'completed');self.assertEqual(state['jobs'][0]['usage']['total_tokens'],30)
  bad=copy.deepcopy(self.result);bad['suggestions'][0]['step_ids']=['foreign'];job=self.job('queued')
  with patch.object(h,'local_analysis',return_value=(json.dumps(bad),{'input_tokens':20,'output_tokens':10},True)):a.run(self.store,job)
  state=a.state(self.store);self.assertEqual(state['jobs'][0]['status'],'failed');self.assertEqual(state['jobs'][0]['usage']['total_tokens'],30)
  self.assertIsNotNone(state['latest'])
 def test_older_windows_are_explicit_and_bounded(self):
  job=self.job();self.assertIsNotNone(a.state(self.store)['latest'])
  older=a.state(self.store,offset=20);self.assertIsNone(older['latest']);self.assertFalse(older['has_older'])
  with self.assertRaisesRegex(ValueError,'offset'):a.collect(self.store,offset=-1)
  with self.assertRaisesRegex(ValueError,'No collected'):a.collect(self.store,offset=20)
  with self.assertRaisesRegex(ValueError,'scope'):a.collect(self.store,project={})
 def test_completed_attempt_is_not_rerun_or_usage_erased(self):
  job=self.job('queued')
  with patch.object(h,'local_analysis',return_value=(json.dumps(self.result),{'input_tokens':20,'output_tokens':10},True)) as model:
   a.run(self.store,job);a.run(self.store,job);self.assertEqual(model.call_count,1)
  self.assertEqual(a.state(self.store)['jobs'][0]['usage']['total_tokens'],30)
 def test_mcp_read_tools(self):
  self.job();r=analyst_mcp.handle(self.store,{'method':'tools/call','params':{'name':'query_activity_suggestions','arguments':{}}})
  self.assertFalse(r.get('isError',False))
if __name__=='__main__':unittest.main()
