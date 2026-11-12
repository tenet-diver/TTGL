"""Evidence integrity and naming lifecycle checks; no live inference."""
import json
import unittest
from unittest.mock import patch

import task_curation as curation
import task_history as history
import test_task_history


class CurationTests(unittest.TestCase):
    def setUp(self):
        self.fixture=test_task_history.HistoryTests();self.fixture.setUp()
        self.addCleanup(self.fixture.tmp.cleanup)
        self.store=self.fixture.store;self.task=self.fixture.task

    def test_prompt_names_and_atomic_creation_from_turn(self):
        created=self.store.mutate('task',{'project_id':self.fixture.project,'goal':'  Add paging\n and test it  '})['id']
        with self.store.connection() as c:
            task=dict(c.execute('SELECT t.*,n.source title_source FROM tasks t JOIN task_names n ON n.task_id=t.id WHERE t.id=?',(created,)).fetchone())
        self.assertEqual(task['title'],'Add paging and test it');self.assertEqual(task['title_source'],'prompt')
        self.assertEqual(curation.rename(self.store,self.task)['title'],'Repair pagination')
        with self.store.connection() as c:
            c.execute("DELETE FROM assignments WHERE session_id='session'")
        created=self.store.mutate('task',{'project_id':self.fixture.project,'session_id':'session','turn_id':'turn'})['id']
        self.assertEqual(history.snapshot(self.store,created)[0]['user_prompt'],'Repair pagination')
        with self.assertRaisesRegex(ValueError,'already assigned'):
            self.store.mutate('task',{'project_id':self.fixture.project,'session_id':'session','turn_id':'turn'})
        with self.store.connection() as c:self.assertEqual(c.execute('SELECT count(*) FROM tasks').fetchone()[0],3)

    def test_collected_groups_search_drilldown_and_immutable_sources(self):
        before,digest=history.snapshot(self.store,self.task)
        group=curation.collect(self.store,self.task,['step1','step0'],'Inspect and verify pagination','test','Recorded by the user',digest)
        self.assertEqual(history.snapshot(self.store,self.task),(before,digest))
        detail=history.detail(self.store,self.task,group['id'])
        self.assertEqual([s['id'] for s in detail['steps']],['step0','step1'])
        self.assertEqual(detail['manual_subtasks'][0]['status'],'unverified')
        self.assertFalse(detail['manual_subtasks'][0]['stale'])
        self.assertEqual(history.search(self.store,'verify',activity='test')['items'][0]['matched_subtasks'],[group['id']])
        self.assertEqual(history.search(self.store,'verify')['items'][0]['manual_subtask_count'],1)
        with self.assertRaisesRegex(ValueError,'already belongs'):
            curation.collect(self.store,self.task,['step0'],'Duplicate')
        with self.store.connection() as c:c.execute("UPDATE events SET output_hash='changed' WHERE id='step0'")
        self.assertTrue(history.detail(self.store,self.task)['manual_subtasks'][0]['stale'])

    def test_selection_bounds_scope_staleness_and_invalid_groups(self):
        for ids in [[],['step0','step0'],['missing'],['step0']*201]:
            with self.assertRaises(ValueError):curation.collect(self.store,self.task,ids,'Invalid')
        with self.assertRaisesRegex(ValueError,'activity'):curation.collect(self.store,self.task,['step0'],'Name','invented')
        with self.assertRaisesRegex(ValueError,'changed'):curation.collect(self.store,self.task,['step0'],'Name',expected_snapshot='obsolete')
        other=self.store.mutate('task',{'project_id':self.fixture.project,'goal':'Other request'})['id']
        with self.assertRaisesRegex(ValueError,'belong'):curation.collect(self.store,other,['step0'],'Foreign')
        group=curation.collect(self.store,self.task,['step0'],'Valid')
        with self.assertRaisesRegex(ValueError,'belong'):history.detail(self.store,other,group['id'])

    def test_timeline_paging_unknown_runtime_and_group_membership(self):
        with self.store.connection() as c:c.execute("UPDATE events SET runtime=NULL WHERE id='step1'")
        first=curation.timeline(self.store,self.task,1)
        self.assertEqual(first['total'],2);self.assertEqual(first['next_offset'],1)
        self.assertIsNone(curation.timeline(self.store,self.task,1,1)['steps'][0]['runtime'])
        curation.collect(self.store,self.task,['step0'],'Search source')
        self.assertIsNotNone(curation.timeline(self.store,self.task)['steps'][0]['group_id'])
        self.assertIn('not separately measured',first['timing_basis'])
        with self.assertRaises(ValueError):curation.timeline(self.store,self.task,101)

    def title_job(self):
        job=self.fixture.job()
        with self.store.connection() as c:c.execute("UPDATE task_history_jobs SET operation='title',engine='ollama' WHERE id=?",(job,))
        return job

    def test_title_job_schema_prompt_and_consumed_failure_usage(self):
        def model(prompt,model,schema):
            self.assertEqual(schema,history.TITLE_SCHEMA)
            self.assertIn('Repair pagination',prompt)
            self.assertNotIn('pytest pagination',prompt)
            return json.dumps({'title':'Repair cursor handling'}),{'total_tokens':45},True
        with patch.object(history,'local_analysis',side_effect=model):history.run_model(self.store,self.title_job())
        detail=history.detail(self.store,self.task)
        self.assertEqual(detail['task']['title'],'Repair cursor handling')
        self.assertEqual(detail['title_provenance']['source'],'model')
        self.assertEqual(detail['user_prompt'],'Repair pagination')
        self.assertEqual(detail['jobs'][0]['usage']['total_tokens'],45)
        self.assertIsNone(detail['analysis'])
        with patch.object(history,'local_analysis',return_value=(json.dumps({'title':''}),{'total_tokens':17},True)):
            history.run_model(self.store,self.title_job())
        detail=history.detail(self.store,self.task)
        self.assertEqual(detail['jobs'][0]['status'],'failed')
        self.assertEqual(detail['jobs'][0]['usage']['total_tokens'],17)
        self.assertEqual(detail['task']['title'],'Repair cursor handling')

    def test_title_race_preserves_new_user_state(self):
        job=self.title_job()
        self.store.mutate('task_status',{'id':self.task,'status':'waiting'})
        with self.assertRaisesRegex(ValueError,'changed'):history.publish(self.store,job,{'title':'Old result'})
        self.assertEqual(history.detail(self.store,self.task)['task']['title'],'Repair pagination')


if __name__=='__main__':unittest.main()
