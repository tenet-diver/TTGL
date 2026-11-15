"""Interpretations retain citations, provenance, uncertainty and native measurements."""
import copy
import json
import unittest
from unittest.mock import patch

import activity_views
import optimization
import process_analysis as process
import task_history as history
import test_task_history
import usage_views
import work_analytics


class ProcessAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.f=test_task_history.HistoryTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.store=self.f.store;self.task=self.f.task

    def result(self,body):
        groups=copy.deepcopy(self.f.result['subtasks'])
        for group in groups:group.update(outcome='unknown',outcome_reason='Visible operations do not independently establish this subtask outcome.',runtime_role='finite_operation')
        return dict(summary=self.f.result['summary'],subtasks=groups,task_type='bugfix',knowledge=[],
                    outcome='unknown',outcome_reason='Task acceptance is not independently recorded.',outcome_confidence=.7,outcome_step_ids=['step1'],
                    intervention='none_observed',intervention_reason='No correction is visible in the supplied request.',intervention_turn_ids=[])

    def publish(self):
        job=history.start(self.store,self.task,'process',_launch=False)
        body,_=history.snapshot(self.store,self.task,'all');body=process.snapshot(self.store,body)
        result=self.result(body)
        aid=history.publish(self.store,job['id'],result,{'input_tokens':100,'output_tokens':50,'total_tokens':150})
        return aid,job['id']

    def test_publish_exposes_hierarchy_outcomes_without_changing_native_status(self):
        before=optimization.dataset(self.store)['rows']
        aid,job_id=self.publish()
        task=work_analytics.task_data(self.store,self.task)
        self.assertEqual(task['status'],'active')
        self.assertEqual(task['process_result']['outcome'],'unknown')
        self.assertEqual(task['process_result']['source_steps'],['step1'])
        self.assertEqual(task['process_result']['protocol'],'task-process-v1')
        self.assertTrue(all(g['process_result']['outcome']=='unknown' for g in task['subtasks']))
        self.assertEqual(task['metrics']['unreviewed_steps'],0)
        self.assertEqual(task['mining_overhead_tokens'],150)
        overview=work_analytics.overview(self.store,result='unknown',limit=1)
        self.assertEqual(overview['total'],1)
        self.assertEqual(overview['process_outcomes']['tasks'],{'unknown':1})
        self.assertEqual(work_analytics.overview(self.store,result='failed')['total'],0)
        after=optimization.dataset(self.store)['rows']
        self.assertEqual([(r['id'],r['usage'],r['failed']) for r in before],[(r['id'],r['usage'],r['failed']) for r in after])

    def test_tool_categories_use_process_version_and_reject_changed_evidence(self):
        self.publish()
        rows=optimization.dataset(self.store)['rows']
        labeled=usage_views.label_tools(self.store,rows)
        self.assertEqual({r['category'] for r in labeled},{'investigate','test'})
        self.assertTrue(all(r['category_basis']=='Task-process interpretation' for r in labeled))
        with self.store.connection() as c:c.execute("UPDATE events SET output_hash='changed' WHERE id='step0'")
        labeled=usage_views.label_tools(self.store,optimization.dataset(self.store)['rows'])
        self.assertEqual(next(r for r in labeled if r['id']=='step0')['category_basis'],'Fallback name rule')
        self.assertTrue(work_analytics.task_data(self.store,self.task)['process_result']['stale'])

    def test_invalid_outcome_and_intervention_citations_are_rejected(self):
        body,_=history.snapshot(self.store,self.task,'all');body=process.snapshot(self.store,body)
        valid=self.result(body)
        for patch in (dict(outcome='success'),dict(outcome_step_ids=['foreign']),dict(outcome='done',outcome_step_ids=[]),
                      dict(intervention='observed',intervention_turn_ids=[]),dict(intervention='possible',intervention_turn_ids=['foreign']),dict(outcome_confidence=1.1)):
            with self.assertRaises(ValueError):process.validate({**valid,**patch},body)

    def test_assignment_decoder_expands_outcome_aliases_and_preserves_result_fields(self):
        body,_=history.snapshot(self.store,self.task,'all');body=process.snapshot(self.store,body)
        document,aliases,schema=history.work_contract(body,process.schema(history.WORK_SCHEMA))
        result=self.result(body)
        for group in result['subtasks']:group.pop('step_ids')
        result['assignments']={alias:i for i,alias in enumerate(aliases)}
        result['outcome_step_ids']=[list(aliases)[1]]
        decoded=process.decode(result,aliases,history.decode_work_result)
        self.assertEqual(decoded['outcome_step_ids'],['step1'])
        self.assertEqual(decoded['subtasks'][0]['step_ids'],['step0'])
        self.assertEqual(schema['properties']['outcome_step_ids']['items']['enum'],list(aliases))
        process.validate(decoded,body)

    def test_native_runner_publishes_new_schema_and_preserves_positive_metering(self):
        job=history.start(self.store,self.task,'process',_launch=False)
        directory=self.store.data/'task-history-attempts'/job['id']
        host=self
        class NativeFixture:
            returncode=0
            def __init__(self,argv,**options):self.stdout=options['stdout']
            def communicate(self,prompt,timeout):
                host.assertIn(b'PROCESS INTERPRETATION',prompt)
                aliases=json.loads((directory/'source-aliases.json').read_text())
                with host.store.connection() as c:body=json.loads(c.execute('SELECT snapshot FROM task_history_jobs WHERE id=?',(job['id'],)).fetchone()[0])
                result=host.result(body)
                for group in result['subtasks']:group.pop('step_ids')
                result['assignments']={alias:i for i,alias in enumerate(aliases)}
                result['outcome_step_ids']=[list(aliases)[1]]
                (directory/'answer.json').write_text(json.dumps(result))
                self.stdout.write((json.dumps({'type':'turn.completed','usage':{'input_tokens':100,'output_tokens':50}})+'\n').encode());self.stdout.flush()
        with patch.object(history.subprocess,'Popen',NativeFixture):history.run_model(self.store,job['id'])
        task=work_analytics.task_data(self.store,self.task)
        self.assertEqual(task['jobs'][0]['status'],'completed')
        self.assertEqual(task['process_result']['source_steps'],['step1'])
        self.assertEqual(task['mining_overhead_tokens'],150)


if __name__=='__main__':unittest.main()
