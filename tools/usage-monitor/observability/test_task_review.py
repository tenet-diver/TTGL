"""Review contracts for model-only work and bounded native evidence ownership."""
import copy
import json
import unittest
from unittest.mock import patch
import task_history as h
import task_review
import test_work_analytics
import work_analytics as w

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture=test_work_analytics.WorkAnalyticsTests();self.fixture.setUp();self.addCleanup(self.fixture.fixture.tmp.cleanup)
        self.store=self.fixture.store;self.task=self.fixture.task

    def test_response_only_work_can_be_classified_with_measured_counters(self):
        with self.store.connection() as c:c.execute("DELETE FROM events WHERE kind='tool'")
        with patch('task_history.threading.Thread'):
            job=h.start(self.store,self.task,'overview')
        body,_=h.snapshot(self.store,self.task,'all');self.assertEqual(len(body['steps']),1)
        _,aliases,schema=h.work_contract(body)
        raw={'summary':'One observed memory operation; no tool execution was recorded.','task_type':'operations','knowledge':[],
             'subtasks':[dict(title='Transform recorded memory',summary='A single recorded response.',activity='operate',tags=['memory'],confidence=.6)],'assignments':{key:0 for key in aliases}}
        h.publish(self.store,job['id'],h.decode_work_result(raw,aliases),{'total_tokens':20})
        task=w.task_data(self.store,self.task)
        self.assertEqual(task['classification_status'],'processed');self.assertEqual(task['metrics']['total_steps'],1)
        self.assertEqual(task['metrics']['tool_calls'],0);self.assertEqual(task['subtasks'][0]['metrics']['tokens'],120)
        self.assertEqual(task['subtasks'][0]['usage_basis'],'native_responses')
        self.assertAlmostEqual(task['subtasks'][0]['metrics']['cost'],task['metrics']['cost'])
        self.assertEqual(w.source_steps(self.store,self.task,task['subtasks'][0]['id'])['items'][0]['id'],'response')

    def test_large_conversation_contract_expands_every_record_once(self):
        body,_=h.snapshot(self.store,self.task,'all');row=body['steps'][0]
        body['steps']=[{**row,'id':f'native-{i}','kind':'generation' if i%2 else 'tool'} for i in range(600)]
        document,aliases,schema=h.work_contract(body)
        self.assertLessEqual(len(document['steps']),64)
        raw={'summary':'Grouped observed activity.','task_type':'investigation','knowledge':[],
             'subtasks':[dict(title='Review evidence',summary='All supplied chronological blocks.',activity='review',tags=[],confidence=.5)],'assignments':{key:0 for key in aliases}}
        result=h.decode_work_result(raw,aliases)
        self.assertEqual(result['subtasks'][0]['step_ids'],[row['id'] for row in body['steps']])
        h.validate({'summary':result['summary'],'subtasks':result['subtasks']},body)

    def test_unprocessed_work_and_frozen_review_scope_remain_explorable(self):
        task=w.task_data(self.store,self.task)
        self.assertEqual(task['classification_status'],'unprocessed')
        self.assertEqual(task['metrics']['total_steps'],3);self.assertEqual(task['metrics']['tool_calls'],2)
        self.assertEqual(sum(g['metrics']['total_steps'] for g in task['subtasks']),3)
        self.assertEqual(task['tool_breakdown'][0]['metrics']['tool_calls'],1)
        manifest=task_review.prepare(self.store)
        self.assertEqual(manifest['task_ids'],[self.task])
        self.assertEqual(w.overview(self.store,review=manifest['id'])['total'],1)
        with self.assertRaises(ValueError):w.overview(self.store,review='unknown')

    def test_unchanged_review_reuses_analysis_without_new_inference_or_counting_old_usage(self):
        with patch('task_history.threading.Thread'):job=h.start(self.store,self.task,'overview')
        body,_=h.snapshot(self.store,self.task,'all');_,aliases,_=h.work_contract(body)
        raw={'summary':'Observed recorded activity.','task_type':'investigation','knowledge':[],
             'subtasks':[dict(title='Inspect recorded source',summary='Supplied records only.',activity='investigate',tags=[],confidence=.5)],'assignments':{key:0 for key in aliases}}
        aid=h.publish(self.store,job['id'],h.decode_work_result(raw,aliases),{'total_tokens':20})
        manifest=task_review.prepare(self.store)
        with patch('task_history.run_model') as model:result=task_review.run(self.store,manifest)
        model.assert_not_called();self.assertEqual(result['completed'],1)
        self.assertTrue(result['members'][0]['reused']);self.assertEqual(result['members'][0]['job_id'],job['id'])
        self.assertEqual(result['members'][0]['analysis_id'],aid);self.assertNotIn('usage',result['members'][0])
        self.assertEqual(w.task_data(self.store,self.task)['mining_overhead_tokens'],20)

if __name__=='__main__':unittest.main()
