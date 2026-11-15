"""Usage-view accounting, attribution and task story regression contracts."""
import copy
import json
import unittest
from unittest.mock import patch
import test_activity_views
import usage_views as usage
import work_analytics
import task_curation


class UsageViewTests(unittest.TestCase):
    def setUp(self):
        self.f=test_activity_views.ActivityViewTests();self.f.setUp();self.addCleanup(self.f.f.directory.cleanup)
        self.store=self.f.store;self.task=self.f.task;self.project=self.f.project

    def report(self,view='costs',**kwargs):
        return usage.report(self.store,view,range='all',clock=self.f.clock,**kwargs)

    def test_cost_reconciliation_token_partition_and_deduplication(self):
        d=self.report();m=d['metrics']
        self.assertEqual((m['responses'],m['input'],m['cache_read'],m['uncached_input'],m['output']),(1,100,80,20,10))
        self.assertEqual(m['tokens'],110);self.assertIsNone(m['cache_write']);self.assertIsNone(m['context_cost'])
        self.assertIsNone(m['average_latency']);self.assertAlmostEqual(m['cost'],.000048)
        self.assertEqual(sum(b['count'] for b in d['bands']),1)
        self.assertAlmostEqual(sum(b['cost'] or 0 for b in d['bands']),m['cost'])
        self.assertEqual(d['models'][0]['share'],1)
        self.assertEqual(d['days'][0]['date'],'2026-11-05')

    def test_explicit_cache_writes_are_separate_from_input_partition(self):
        with self.store.connection() as c:
            ident=c.execute("SELECT id FROM events WHERE kind='generation'").fetchone()[0]
            c.execute('INSERT INTO optimization_facts(event_id,cache_write,cache_5m) VALUES(?,?,?)',(ident,30,10))
        m=self.report()['metrics']
        self.assertEqual(m['cache_write'],30)
        self.assertEqual(m['uncached_input']+m['cache_read']+m['output'],m['tokens'])
        self.assertEqual(m['tokens'],110)

    def test_unknown_rate_usage_and_unassigned_are_not_zero_cost(self):
        with self.store.connection() as c:
            c.execute("UPDATE events SET model='unpriced' WHERE kind='generation'")
        d=self.report();self.assertIsNone(d['metrics']['cost']);self.assertIsNone(d['models'][0]['share'])
        self.assertEqual(d['bands'][-1]['count'],1);self.assertEqual(d['metrics']['priced_responses'],0)
        with self.store.connection() as c:c.execute('DELETE FROM assignments')
        d=self.report();self.assertEqual(d['unassigned']['responses'],1);self.assertEqual(sum(b['count'] for b in d['bands']),0)
        self.assertIsNone(d['unassigned']['cost'])

    def test_cost_bands_are_half_open_and_include_unknown_tool_only_tasks(self):
        data,rows,*_=__import__('activity_views').scope(self.store,range='all',clock=self.f.clock)
        response=next(r for r in rows if r['kind']=='generation')
        rows=[]
        for i,amount in enumerate((0,.05,.25,1,5,20)):
            rows.append({**response,'id':str(i),'task_id':str(i),'cost':amount,'usage':dict(input_tokens=int(amount*1e6),cached_input_tokens=0,output_tokens=0,total_tokens=int(amount*1e6))})
        # Cost is recalculated from the frozen native counters, not a supplied cost field.
        scenario=dict(unit='USD',models={'test-model':dict(input=1,cached=0,output=0)})
        tool={**rows[0],'id':'tool','task_id':'tool-only','kind':'tool','usage':None,'failed':None,'runtime':None}
        d=usage.costs(rows+[tool],scenario,'UTC')
        self.assertEqual([b['count'] for b in d['bands']],[1]*7)

    def test_scope_and_timezone_for_daily_aggregates(self):
        with self.store.connection() as c:c.execute("UPDATE events SET ts='2026-11-04T23:30:00Z'")
        self.assertEqual(self.report(zone='UTC')['days'][0]['date'],'2026-11-04')
        self.assertEqual(self.report(zone='Europe/Amsterdam')['days'][0]['date'],'2026-11-05')
        self.assertEqual(self.report(workspace='/other')['metrics']['responses'],0)
        self.assertEqual(self.report(project='other')['metrics']['responses'],0)
        with self.assertRaises(ValueError):usage.report(self.store,'costs',range='invalid')
        with self.assertRaises(KeyError):self.report(zone='Unknown/Zone')

    def test_tool_actions_targets_unknowns_and_safe_compound_labels(self):
        self.f.add([self.f.item('second',command='cat a.py | head -n 5',exit_code=1,duration={'secs':3,'nanos':0})])
        d=self.report('tools');self.assertEqual(d['metrics']['calls'],2)
        self.assertEqual({r['action'] for r in d['tools']},{'rg','Compound shell'})
        self.assertTrue(all(r['call_cost'] is None and r['context_cost'] is None for r in d['tools']))
        filtered=self.report('tools',family='Shell',action='rg')
        self.assertEqual(filtered['metrics']['calls'],1);self.assertEqual(filtered['targets'][0]['target'],'rg foo')
        self.assertEqual(usage.shell_action('MODE=quiet /usr/bin/python3 a.py'),'python3')
        self.assertEqual(usage.shell_action('cat "unterminated'),'Unparsed shell')
        with patch('subprocess.run',side_effect=AssertionError('Must never execute recorded commands')):
            self.report('tools')

    def test_optional_full_turn_allocations_conserve_cost_with_clipped_scope(self):
        self.f.add([self.f.item('second',stamp='2026-11-05T00:00:03Z',command=['python3','a.py'],exit_code=0)])
        d=self.report('tools',attribution='step_share')
        self.assertAlmostEqual(sum(r['call_cost'] for r in d['tools']),.000048)
        data,rows,*_=__import__('activity_views').scope(self.store,range='all',clock=self.f.clock)
        selected=[r for r in rows if r['id']=='s:tool:tool']
        subset=usage.tools(self.store,selected,data['scenario'],'step_share',data['rows'],'UTC')
        self.assertAlmostEqual(subset['metrics']['call_cost'],.000024)
        with self.store.connection() as c:
            c.execute("INSERT INTO analyses VALUES('runtime-review','2026-11-05','fixture','hash','{}','{}')")
            c.execute("INSERT INTO agent_annotations VALUES('runtime-review','s:tool:tool','waiting','background_service_lifetime','fixture','high')")
        d=self.report('tools');self.assertEqual(d['metrics']['background_calls'],1)
        self.assertEqual(d['metrics']['runtime'],None) # remaining tool lacks runtime

    def test_inline_task_story_links_current_phases_checks_final_message_and_sources(self):
        self.f.add([self.f.item('edit','FileChange',changes={'a.py':{'diff':'+fixed'}},status='completed'),
                    self.f.item('check',command=['pytest','tests'],exit_code=1,aggregated_output='1 failed'),
                    self.f.item('answer','AssistantMessage',stamp='2026-11-05T00:00:06Z',content=[dict(type='text',text='Tests failed; work remains.')])])
        task_curation.collect(self.store,self.task,['s:tool:edit'],'Implement','implement')
        d=usage.task_report(self.store,self.task)
        self.assertEqual(d['phases'][0]['title'],'Implement')
        self.assertIn('Last recorded validation command failed.',d['packet']['story']['open_items'])
        self.assertEqual(d['packet']['last_message']['text'],'Tests failed; work remains.')
        self.assertIn('not independently verified',d['packet']['last_message']['basis'])
        self.assertEqual(d['timeline_range']['start'],work_analytics.timestamp('2026-11-04T23:59:59Z'))
        self.assertEqual(d['timeline_range']['end'],work_analytics.timestamp('2026-11-05T00:00:02Z'))
        self.assertEqual(len(d['events']),4);self.assertEqual(d['metrics']['responses'],1)
        self.assertIsNone(next(e for e in d['events'] if e['kind']=='tool')['input'])
        with self.assertRaises(ValueError):usage.task_report(self.store,'unknown')


if __name__=='__main__':unittest.main()
