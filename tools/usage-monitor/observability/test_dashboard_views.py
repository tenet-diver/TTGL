"""Dashboard counting units, coverage and native source invariants."""
import copy
import json
import time
import unittest
from unittest.mock import patch
import test_activity_views
import dashboard_views as d
import task_curation
import task_discovery
import task_evidence
import task_history
import work_analytics


class DashboardViewTests(unittest.TestCase):
    def setUp(self):
        self.f=test_activity_views.ActivityViewTests();self.f.setUp();self.addCleanup(self.f.f.directory.cleanup)
        self.store=self.f.store;self.task=self.f.task

    def report(self,view='taskactivity',**extra):
        return d.report(self.store,view,range='all',clock=self.f.clock,**extra)

    def test_native_turns_and_marked_tasks_are_distinct_without_recounting_usage(self):
        result=self.report()
        self.assertEqual(result['counts'],dict(turns=1,prompts=1,sessions=1,defined_tasks=1))
        self.assertEqual(result['turns'][0]['metrics']['tokens'],110)
        self.assertEqual(result['marked_tasks'][0]['turns'],1)
        self.assertEqual(result['metrics']['responses'],1)
        self.assertAlmostEqual(result['statistics']['cost']['mean'],.000048)
        with self.store.connection() as c:c.execute('DELETE FROM assignments')
        unassigned=self.report()
        self.assertEqual(len(unassigned['turns']),1);self.assertIsNone(unassigned['turns'][0]['task_id'])
        self.assertEqual(unassigned['marked_tasks'],[]);self.assertEqual(unassigned['metrics']['tokens'],110)

    def test_percentiles_and_known_sample_denominators(self):
        stats=d.distribution([1,2,3,4,None])
        self.assertEqual(stats['mean'],2.5);self.assertEqual(stats['median'],2.5)
        self.assertAlmostEqual(stats['p90'],3.7);self.assertEqual((stats['known'],stats['total']),(4,5))
        self.assertIsNone(d.distribution([None])['mean'])
        with self.store.connection() as c:c.execute("UPDATE events SET model='unpriced' WHERE kind='generation'")
        result=self.report();self.assertIsNone(result['statistics']['cost']['mean'])
        self.assertEqual(result['statistics']['cost']['known'],0);self.assertEqual(result['statistics']['cost']['total'],1)

    def test_coverage_keeps_partial_interpretation_pending_and_missing_sources_distinct(self):
        self.assertEqual(self.report()['coverage'],{'unclassified':1})
        self.assertEqual(self.report()['interpreted_spend_share'],0)
        task_curation.collect(self.store,self.task,['s:tool:tool'],'Read source','investigate')
        interpreted=self.report();self.assertEqual(interpreted['interpreted_turns'],1);self.assertEqual(interpreted['complete_turns'],0)
        body,digest=task_history.snapshot(self.store,self.task,'all')
        with self.store.connection() as c:c.execute('INSERT INTO task_history_jobs(id,task_id,snapshot_hash,snapshot,status,created,model,operation) VALUES(?,?,?,?,?,?,?,?)',('pending',self.task,digest,json.dumps(body),'queued',time.time(),'fixture','overview'))
        pending=self.report();self.assertEqual(pending['coverage'],{'pending':1});self.assertEqual(pending['interpreted_turns'],1)
        self.f.f.source.unlink()
        unavailable=self.report();self.assertEqual(unavailable['source_coverage'],{'unavailable':1});self.assertEqual(unavailable['eligible'],[])

    def test_title_formatting_job_is_not_pending_subtask_analysis(self):
        task_history.init(self.store)
        body,digest=task_history.snapshot(self.store,self.task,'all')
        with self.store.connection() as c:c.execute('INSERT INTO task_history_jobs(id,task_id,snapshot_hash,snapshot,status,created,model,operation) VALUES(?,?,?,?,?,?,?,?)',('title-only',self.task,digest,json.dumps(body),'queued',time.time(),'fixture','title'))
        self.assertEqual(self.report()['coverage'],{'unclassified':1})

    def test_explicit_tasks_exclude_provisional_discovery(self):
        rows=copy.deepcopy(self.f.f.rows)
        for row in rows:
            row['payload']=json.loads(json.dumps(row['payload']).replace('"s"','"second"'))
        path=self.f.f.source.with_name('second.jsonl');path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        self.store.ingest(path);task_discovery.configure(self.store,True)
        result=self.report()
        self.assertEqual(result['counts']['defined_tasks'],2)
        self.assertEqual([t['id'] for t in result['marked_tasks']],[self.task])
        self.assertEqual(result['counts']['turns'],2);self.assertEqual(result['metrics']['tokens'],220)

    def test_confirmed_fix_denominator_is_tasks_not_turns(self):
        with self.store.connection() as c:
            c.execute("INSERT INTO turns VALUES('s','second','/repo','Follow-up','2026-11-05T00:00:02Z','2026-11-05T00:00:03Z',1)")
            c.execute('INSERT INTO assignments VALUES(?,?,?)',('s','second',self.task))
        task_evidence.add(self.store,self.task,'intervention','Corrected the requirement',outcome='confirmed')
        result=self.report('overview')
        self.assertEqual(result['counts']['turns'],2)
        self.assertEqual(result['outcomes']['tasks'],1);self.assertEqual(result['outcomes']['needed_fix'],1)
        self.assertEqual(result['outcomes']['fix_rate'],1)
        self.assertTrue(all('assigned' in t['outcome_basis'] for t in result['turns']))

    def test_role_time_excludes_background_and_category_drilldown_does_not_mix_categories(self):
        self.f.add([self.f.item('again',command=['rg','again'],exit_code=0,duration={'secs':3,'nanos':0})])
        with self.store.connection() as c:
            c.execute("INSERT INTO analyses VALUES('review','2026-11-05','fixture','hash','{}','{}')")
            c.execute("INSERT INTO agent_annotations VALUES('review','s:tool:again','custom category','background_service_lifetime','fixture','high')")
        result=self.report('overview')
        category=next(c for c in result['top_categories'] if c['name']=='search')
        self.assertEqual(category['tools'][0]['calls'],1)
        self.assertEqual(sum(r['known_runtime'] for r in result['time_by_role']),2)
        self.assertIsNone(next(r for r in result['time_by_role'] if r['name']=='model')['runtime'])
        self.assertEqual(result['cache_hit_rate'],.8)
        self.assertEqual(result['days'][0]['turn_keys'],[('s','t')])

    def test_range_clips_spans_and_workspace_project_filters(self):
        with self.store.connection() as c:c.execute("UPDATE turns SET start='2026-11-04T12:00:00Z',end='2026-11-05T12:00:00Z'")
        result=d.report(self.store,'taskactivity',range='1d',clock=work_analytics.timestamp('2026-11-05T18:00:00Z'))
        self.assertTrue(result['turns'][0]['clipped']);self.assertEqual(result['turns'][0]['span'],18*3600)
        self.assertEqual(result['marked_tasks'][0]['span_sum'],18*3600)
        self.assertEqual(self.report(workspace='/elsewhere')['turns'],[])
        self.assertEqual(self.report(project='unknown')['turns'],[])
        with self.assertRaises(ValueError):d.report(self.store,'unknown')
        with self.assertRaises(ValueError):d.report(self.store,'overview',range='bad')

    def test_reads_never_launch_inference_and_invalid_cache_is_unknown(self):
        with patch('task_history.start',side_effect=AssertionError('No implicit inference')):
            self.report();self.report('overview')
        with self.store.connection() as c:
            usage=dict(input_tokens=100,cached_input_tokens=200,output_tokens=10,total_tokens=110)
            c.execute("UPDATE events SET usage=? WHERE kind='generation'",(json.dumps(usage),))
        self.assertIsNone(self.report('overview')['cache_hit_rate'])


if __name__=='__main__':unittest.main()
