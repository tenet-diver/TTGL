"""Task hierarchy accounting and mining contracts; explicit fixtures, no live inference."""
import copy
import json
import unittest
from unittest.mock import patch
import test_task_history
import task_history as h
import task_curation as c
import work_analytics as w

class WorkAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.fixture=test_task_history.HistoryTests();self.fixture.setUp();self.addCleanup(self.fixture.tmp.cleanup)
        self.store=self.fixture.store;self.task=self.fixture.task
        with self.store.connection() as db:
            db.execute('INSERT INTO events(id,session_id,turn_id,kind,name,ts,usage,model) VALUES(?,?,?,?,?,?,?,?)',('response','session','turn','generation','model','2026-11-12T01:00:03Z',json.dumps(dict(input_tokens=100,cached_input_tokens=25,output_tokens=20,total_tokens=120)),'model'))
        self.scenario=dict(unit='USD',as_of='2026-11-12',models={'model':dict(input=2,cached=.5,output=4)})
        w.save_rates(self.store,self.scenario)

    def publish(self):
        result=copy.deepcopy(self.fixture.result);result.update(task_type='bugfix',knowledge=[dict(title='Cursor lesson',statement='Fixture candidate from a source operation; unverified.',step_ids=['step0'],confidence=.6)])
        job=self.fixture.job()
        with self.store.connection() as db:db.execute("UPDATE task_history_jobs SET operation='overview' WHERE id=?",(job,))
        h.publish(self.store,job,result,dict(input_tokens=10,cached_input_tokens=0,output_tokens=4,total_tokens=14))
        return result

    def test_native_totals_and_no_fabricated_subtask_usage(self):
        self.publish();task=w.task_data(self.store,self.task)
        self.assertEqual(task['metrics']['tokens'],120)
        self.assertAlmostEqual(task['metrics']['cost'],.0002425)
        self.assertEqual(task['mining_overhead_tokens'],14)
        self.assertEqual(task['type'],'bugfix');self.assertEqual(len(task['knowledge']),1)
        self.assertTrue(all(s['metrics']['tokens'] is None and s['metrics']['cost'] is None for s in task['subtasks']))
        self.assertFalse(task['analysis_stale'])

    def test_manual_override_partition_and_estimate_conservation(self):
        self.publish();c.collect(self.store,self.task,['step0'],'Human interpretation','review')
        task=w.task_data(self.store,self.task,'step_share')
        self.assertEqual(len(task['subtasks']),2)
        self.assertEqual([s['source'] for s in task['subtasks']],['user','model'])
        self.assertEqual(sum(s['metrics']['steps'] for s in task['subtasks']),2)
        self.assertEqual(sum(s['metrics']['tokens'] for s in task['subtasks']),120)
        self.assertAlmostEqual(sum(s['metrics']['cost'] for s in task['subtasks']),task['metrics']['cost'])
        self.assertEqual(task['unattributed_tokens'],0)
        with self.store.connection() as db:db.execute("UPDATE events SET output_hash='changed' WHERE id='step0'")
        task=w.task_data(self.store,self.task)
        self.assertTrue(task['analysis_stale']);self.assertTrue(task['subtasks'][0]['stale']);self.assertTrue(task['knowledge'][0]['stale'])

    def test_missing_counters_prices_and_runtime_stay_unknown(self):
        with self.store.connection() as db:
            db.execute("UPDATE events SET usage=NULL WHERE id='response'")
            db.execute("UPDATE events SET runtime=NULL WHERE kind='tool'")
        task=w.task_data(self.store,self.task,'step_share')
        self.assertIsNone(task['metrics']['tokens']);self.assertIsNone(task['metrics']['cost']);self.assertIsNone(task['metrics']['runtime_seconds'])
        self.assertIsNone(task['subtasks'][0]['metrics']['tokens'])
        self.assertIsNone(w.overview(self.store)['task_types'][0]['runtime_seconds'])
        self.assertIsNone(w.cost({'input_tokens':100,'output_tokens':20},'model',self.scenario))
        self.assertIsNone(w.cost({'input_tokens':100,'cached_input_tokens':0,'output_tokens':20},'unknown',self.scenario))

    def test_scope_search_and_model_only_turns(self):
        self.publish()
        with self.store.connection() as db:
            db.execute("INSERT INTO turns VALUES('session','model-only','/repo','Follow-up','2026-11-12','2026-11-12',1)")
            db.execute('INSERT INTO assignments VALUES(?,?,?)',('session','model-only',self.task))
            db.execute("INSERT INTO events(id,session_id,turn_id,kind,name,usage,model) VALUES('r2','session','model-only','generation','model',?,?)",(json.dumps(dict(input_tokens=10,cached_input_tokens=0,output_tokens=0,total_tokens=10)),'model'))
        task=w.task_data(self.store,self.task,'step_share')
        self.assertEqual(task['unattributed_tokens'],0)
        self.assertEqual(task['subtasks'][-1]['usage_basis'],'native_turn')
        self.assertEqual(sum(s['metrics']['tokens'] for s in task['subtasks']),task['metrics']['tokens'])
        report=w.overview(self.store,query='regression',attribution='step_share')
        self.assertEqual(report['total'],1);self.assertEqual(sum(s['steps'] for s in report['subtask_types']),2)
        self.assertEqual(w.overview(self.store,query='Cursor lesson')['total'],1)
        self.assertEqual(w.overview(self.store,query='pytest')['total'],1)
        self.assertEqual(w.overview(self.store,task_type='feature')['total'],0)
        self.assertEqual(w.overview(self.store,project='unknown')['total'],0)

    def test_knowledge_must_cite_real_source_and_rates_are_validated(self):
        result=self.publish();result['knowledge'][0]['step_ids']=['foreign']
        job=self.fixture.job()
        with self.store.connection() as db:db.execute("UPDATE task_history_jobs SET operation='overview' WHERE id=?",(job,))
        with self.assertRaisesRegex(ValueError,'cite source'):h.publish(self.store,job,result)
        for row in [dict(input=-1,cached=0,output=1),dict(input=float('nan'),cached=0,output=1),dict(input=1,output=1)]:
            scenario=copy.deepcopy(self.scenario);scenario['models']['model']=row
            with self.assertRaises(ValueError):w.save_rates(self.store,scenario)

    def test_subtask_timeline_and_bounded_source_excerpts(self):
        self.publish();task=w.task_data(self.store,self.task)
        timeline=c.timeline(self.store,self.task,subtask_id=task['subtasks'][0]['id'])
        self.assertEqual(timeline['total'],1);self.assertEqual(timeline['steps'][0]['id'],'step0')
        with self.assertRaises(ValueError):c.timeline(self.store,self.task,subtask_id='foreign')
        body,_=h.snapshot(self.store,self.task)
        self.assertEqual(h.overview_evidence(self.store,body)['steps'],{})

    def test_work_contract_has_one_required_owner_for_each_source_step(self):
        body,_=h.snapshot(self.store,self.task);model_body,aliases,schema=h.work_contract(body)
        self.assertEqual(schema['properties']['assignments']['required'],list(aliases))
        self.assertFalse(schema['properties']['assignments']['additionalProperties'])
        result=copy.deepcopy(self.fixture.result);result.update(task_type='bugfix',knowledge=[],assignments={'S0001':0,'S0002':1})
        for group in result['subtasks']:group.pop('step_ids')
        decoded=h.decode_work_result(result,aliases)
        h.validate({'summary':decoded['summary'],'subtasks':decoded['subtasks']},body)
        self.assertEqual(decoded['subtasks'][0]['step_ids'],['step0'])
        result['assignments']['S0002']=4
        with self.assertRaisesRegex(ValueError,'index'):h.decode_work_result(result,aliases)

    def test_live_overview_accepts_only_appended_evidence_and_keeps_frozen_coverage(self):
        result=copy.deepcopy(self.fixture.result);result.update(task_type='bugfix',knowledge=[])
        job=self.fixture.job()
        with self.store.connection() as db:
            db.execute("UPDATE task_history_jobs SET operation='overview' WHERE id=?",(job,))
            db.execute("INSERT INTO events(id,session_id,turn_id,kind,name,ts) VALUES('added','session','turn','tool','Later check','2026-11-12T01:00:04Z')")
        h.publish(self.store,job,result)
        task=w.task_data(self.store,self.task)
        self.assertTrue(task['analysis_stale']);self.assertEqual(sum(g['metrics']['steps'] for g in task['subtasks']),3)
        self.assertEqual(task['subtasks'][-1]['step_ids'],['added'])
        before,_=h.snapshot(self.store,self.task)
        changed=copy.deepcopy(before);changed['steps'][0]['name']='Different operation'
        self.assertFalse(h.append_only_overview(before,changed))

    def test_empty_proposal_derivation_preserves_failed_attempt_usage_and_raw_output(self):
        body,_=h.snapshot(self.store,self.task);_,aliases,_=h.work_contract(body)
        raw=copy.deepcopy(self.fixture.result);raw.update(task_type='bugfix',knowledge=[],assignments={'S0001':0,'S0002':1})
        for group in raw['subtasks']:group.pop('step_ids')
        raw['subtasks'].append(dict(title='Unsupported proposal',summary='No evidence assigned.',activity='other',tags=[],confidence=.1))
        job=self.fixture.job();directory=self.store.data/'task-history-attempts'/job;directory.mkdir(parents=True)
        source=json.dumps(raw);(directory/'answer.json').write_text(source);(directory/'source-aliases.json').write_text(json.dumps(aliases))
        with self.store.connection() as db:
            db.execute("UPDATE task_history_jobs SET operation='overview',status='failed',error='Unknown or missing source step',usage=? WHERE id=?",(json.dumps({'total_tokens':123}),job))
            before=dict(db.execute('SELECT status,error,usage FROM task_history_jobs WHERE id=?',(job,)).fetchone())
        h.recover_empty_proposals(self.store,job)
        with self.store.connection() as db:self.assertEqual(dict(db.execute('SELECT status,error,usage FROM task_history_jobs WHERE id=?',(job,)).fetchone()),before)
        self.assertEqual((directory/'answer.json').read_text(),source)
        task=w.task_data(self.store,self.task)
        self.assertEqual(task['mining_overhead_tokens'],123);self.assertEqual(len(task['subtasks']),2)
        self.assertEqual(json.loads(task['analysis_derivation']['omitted']),['Unsupported proposal'])
        self.assertEqual(h.snapshot(self.store,self.task)[0],body)

if __name__=='__main__':unittest.main()
