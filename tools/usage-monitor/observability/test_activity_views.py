"""Analysis pages keep interpretations separate from observed source counters."""
import copy
from datetime import datetime, timezone
import json
import unittest
from unittest.mock import patch
import test_workspace
import activity_views as views
import task_curation
import task_evidence
import work_analytics


class ActivityViewTests(unittest.TestCase):
    def setUp(self):
        self.f=test_workspace.WorkspaceTests();self.f.setUp();self.addCleanup(self.f.directory.cleanup)
        self.store=self.f.store
        self.f.rows[0]['payload']['source']='cli'
        self.f.source.write_text(''.join(json.dumps(r)+'\n' for r in self.f.rows))
        self.store.scan();self.project,self.task=self.f.define_task()
        self.store.mutate('assign',dict(session_id='s',turn_id='t',task_id=self.task))
        work_analytics.save_rates(self.store,dict(unit='USD',as_of='2026-11-05',models={'test-model':dict(input=1,cached=.1,output=2)}))
        self.clock=work_analytics.timestamp('2026-11-06T00:00:00Z')

    def report(self,view,**extra):
        return views.report(self.store,view,range='all',clock=self.clock,**extra)

    def add(self,rows):
        self.f.source.write_text(''.join(json.dumps(r)+'\n' for r in self.f.rows+rows))
        self.store.ingest(self.f.source)

    def item(self,ident,typ='CommandExecution',stamp='2026-11-05T00:00:02Z',**item):
        return dict(timestamp=stamp,type='event_msg',payload=dict(type='item_completed',thread_id='s',turn_id='t',item=dict(id=ident,type=typ,**item)))

    def test_process_excludes_raw_turns_and_stale_groups(self):
        data=self.report('process')
        self.assertEqual(data['interpreted_tasks'],0);self.assertEqual(data['coverage']['unclassified'],1)
        task_curation.collect(self.store,self.task,['s:tool:tool'],'Inspect','investigate')
        data=self.report('process')
        self.assertEqual(data['interpreted_tasks'],1)
        self.assertEqual(data['categories'][0]['name'],'investigate')
        self.assertIsNone(data['categories'][0]['cost'])
        self.assertEqual(data['complete_tasks'],0)
        self.assertAlmostEqual(self.report('process',attribution='step_share')['categories'][0]['cost'],.000048)
        with self.store.connection() as c:c.execute("UPDATE events SET output_hash='changed' WHERE id='s:tool:tool'")
        self.assertEqual(self.report('process')['interpreted_tasks'],0)

    def test_paths_transitions_and_rework_count_tasks_once(self):
        self.add([self.item('edit','FileChange',changes={'a.py':{'diff':'+x'}},status='completed'),self.item('search',stamp='2026-11-05T00:00:03Z',command=['rg','next'],exit_code=0)])
        for ident,activity in [('tool','investigate'),('edit','implement'),('search','investigate')]:
            task_curation.collect(self.store,self.task,['s:tool:'+ident],ident,activity)
        data=self.report('process')
        self.assertEqual(data['paths'][0]['path'],['investigate','implement','investigate'])
        self.assertEqual(data['metrics']['rework_tasks'],1);self.assertEqual(data['metrics']['rework_rate'],1)
        cat=next(c for c in data['categories'] if c['name']=='investigate')
        self.assertEqual(cat['subtasks'],2);self.assertEqual(cat['task_ids'],[self.task])
        edge=next(e for e in data['transitions'] if e['from']=='implement' and e['to']=='investigate')
        self.assertEqual((edge['count'],edge['tasks'],edge['rework']),(1,1,1))
        self.assertIsNone(data['metrics']['rework_cost'])
        task_evidence.add(self.store,self.task,'intervention','Corrected',outcome='confirmed')
        rate=next(r for r in self.report('outcomes')['category_rates'] if r['name']=='investigate')
        self.assertEqual((rate['tasks'],rate['needed_fix']),(1,1))

    def test_agents_deduplicate_native_usage_and_keep_unknown_model_time(self):
        data=self.report('agents');agent=data['agents'][0]
        self.assertEqual(agent['name'],'main');self.assertEqual(agent['runs'],1)
        self.assertEqual(agent['metrics']['responses'],1);self.assertEqual(agent['metrics']['tokens'],110)
        self.assertAlmostEqual(agent['metrics']['cost'],.000048)
        self.assertIsNone(agent['metrics']['model_seconds'])
        with self.store.connection() as c:c.execute("UPDATE native_session_facts SET role=NULL WHERE session_id='s'")
        self.assertEqual(self.report('agents')['agents'][0]['name'],'Unknown agent')

    def test_agent_source_preview_is_bounded_without_truncating_metrics(self):
        data,rows,*_=views.scope(self.store,range='all',clock=self.clock)
        response=next(r for r in rows if r['kind']=='generation')
        many=[{**response,'id':'response-'+str(i)} for i in range(301)]
        agent=views.agents(many,data['scenario'])[0]
        self.assertEqual(len(agent['event_ids']),100)
        self.assertEqual(agent['event_count'],301)
        self.assertEqual(agent['metrics']['responses'],301)
        self.assertEqual(agent['metrics']['tokens'],33110)

    def test_timeline_timezone_and_midnight_segments_preserve_one_turn(self):
        # 23:30 -> 01:30 local Amsterdam crosses midnight; counters stay in response buckets.
        with self.store.connection() as c:
            c.execute("UPDATE turns SET start='2026-11-04T22:30:00Z',end='2026-11-05T00:30:00Z'")
        data=self.report('timeline',zone='Europe/Amsterdam')
        self.assertEqual(len(data['heatmap']),168);self.assertEqual(sum(c['responses'] for c in data['heatmap']),1)
        turn=data['turns'][0];self.assertEqual(len(turn['segments']),2)
        self.assertEqual(turn['segments'][0],{'date':'2026-11-04','hour':23.5,'end_hour':24})
        self.assertEqual(turn['segments'][1],{'date':'2026-11-05','hour':0,'end_hour':1.5})
        self.assertEqual(turn['metrics']['tokens'],110)
        self.assertEqual(self.report('timeline',zone='UTC')['heatmap'][3*24]['responses'],1)
        self.assertEqual(data['heatmap'][3*24+1]['responses'],1)
        with self.assertRaises(ValueError):self.report('timeline',zone='Not/A/Timezone')

    def test_dst_fold_combines_both_occurrences_without_duplicating_usage(self):
        with self.store.connection() as c:
            c.execute("UPDATE events SET ts='2026-10-25T00:30:00Z'")
            c.execute("UPDATE turns SET start='2026-10-25T00:30:00Z',end='2026-10-25T02:30:00Z'")
            c.execute("INSERT INTO events(id,session_id,turn_id,kind,name,ts,usage,model) VALUES('fold','s','t','generation','Model response','2026-10-25T01:30:00Z',?,'test-model')",(json.dumps(dict(input_tokens=100,cached_input_tokens=80,output_tokens=10,total_tokens=110)),))
        data=self.report('timeline',zone='Europe/Amsterdam')
        self.assertEqual(data['heatmap'][6*24+2]['responses'],2)
        self.assertEqual(sum(c['metrics']['known_tokens'] for c in data['heatmap']),220)
        self.assertEqual(data['turns'][0]['span'],7200)
        self.assertEqual(data['turns'][0]['segments'][0]['hour'],2.5)
        self.assertEqual(data['turns'][0]['segments'][0]['end_hour'],3.5)

    def test_fix_heuristics_never_turn_into_confirmed_task_failure(self):
        self.add([dict(timestamp='2026-11-05T00:00:03Z',type='event_msg',payload=dict(type='item_completed',turn_id='next',item=dict(type='UserMessage',content=[dict(type='text',text='No, that is still broken')]))),dict(timestamp='2026-11-05T00:00:04Z',type='event_msg',payload=dict(type='turn_aborted',turn_id='t',reason='User interrupted the turn'))])
        data=self.report('outcomes')
        self.assertEqual(data['metrics']['needed_fix'],0);self.assertEqual(data['metrics']['warnings'],1)
        task=data['tasks'][0];self.assertEqual(task['status'],'warning')
        self.assertEqual({s['kind'] for s in task['signals']},{'possible_correction','interrupt'})
        task_evidence.add(self.store,self.task,'intervention','I corrected the acceptance test',outcome='confirmed')
        data=self.report('outcomes')
        self.assertEqual(data['metrics']['needed_fix'],1);self.assertEqual(data['metrics']['fix_rate'],1)
        self.assertEqual(data['workspace_rates'][0]['needed_fix'],1)
        signal=next(s for s in task['signals'] if s['kind']=='interrupt')
        self.assertIn('interrupted',views.signal_detail(self.store,signal['signal_id'])['detail'])

    def test_native_rejection_and_file_overlap_are_reviewable_warnings(self):
        self.add([self.item('edit','FileChange',changes={'a.py':{'diff':'+x'}},status='completed'),self.item('deny',status='denied',command=['deploy'],exit_code=1,stamp='2026-11-05T00:00:03Z')])
        second=self.store.mutate('task',dict(project_id=self.project,title='Next task',goal='Continue work'))['id']
        with self.store.connection() as c:
            c.execute("INSERT INTO turns VALUES('s','next','/repo','Continue work','2026-11-05T00:01:00Z','2026-11-05T00:01:00Z',1)")
            c.execute('INSERT INTO assignments VALUES(?,?,?)',('s','next',second))
            c.execute("INSERT INTO events(id,session_id,turn_id,kind,name,ts) VALUES('next-edit','s','next','tool','FileChange','2026-11-05T00:01:00Z')")
            c.execute("INSERT INTO activity_files VALUES('next-edit','/repo/a.py')")
        data=self.report('outcomes');first=next(t for t in data['tasks'] if t['task_id']==self.task)
        self.assertEqual({s['kind'] for s in first['signals']},{'rejected','same_files'})
        self.assertEqual(first['status'],'warning');self.assertEqual(data['metrics']['needed_fix'],0)

    def test_scope_filters_and_unknowns_are_consistent_for_all_pages(self):
        for view in views.VIEWS:
            with self.subTest(view=view):
                data=self.report(view,project='foreign')
                self.assertEqual(data['source_events'],0)
                data=self.report(view,workspace='/other');self.assertEqual(data['source_events'],0)
        with self.assertRaises(ValueError):views.report(self.store,'process',range='forever')
        with self.assertRaises(ValueError):self.report('process',attribution='invented')

    def test_fix_rates_use_native_working_folder_not_project_root(self):
        with self.store.connection() as c:c.execute("UPDATE projects SET repo='/project-root' WHERE id=?",(self.project,))
        task_evidence.add(self.store,self.task,'intervention','Corrected',outcome='confirmed')
        result=self.report('outcomes')
        self.assertEqual(result['workspace_rates'][0]['name'],'/repo')
        self.assertEqual(result['workspace_rates'][0]['needed_fix'],1)

    def test_step_share_scope_uses_each_selected_turn_not_an_average(self):
        extra=[dict(timestamp='2026-11-07T01:00:00Z',type='turn_context',payload=dict(turn_id='second',model='test-model')),
               dict(timestamp='2026-11-07T01:00:00Z',type='event_msg',payload=dict(type='item_completed',thread_id='s',turn_id='second',item=dict(type='CommandExecution',id='later',command=['rg','later'],exit_code=0))),
               dict(timestamp='2026-11-07T01:00:01Z',type='token_usage_record',payload=dict(thread_id='s',turn_id='second',response_id='later-response',usage=dict(input_tokens=1000,cached_input_tokens=0,output_tokens=10,total_tokens=1010)))]
        self.add(extra);self.store.mutate('assign',dict(session_id='s',turn_id='second',task_id=self.task))
        task_curation.collect(self.store,self.task,['s:tool:tool','s:tool:later'],'Inspect both turns','investigate')
        selected=views.report(self.store,'process',range='1d',clock=work_analytics.timestamp('2026-11-08T00:00:00Z'),attribution='step_share')
        self.assertAlmostEqual(selected['categories'][0]['cost'],.00102)

    def test_projection_backfill_and_repeated_scans_preserve_source_counters(self):
        records=[dict(timestamp='2026-11-05T00:00:04Z',type='event_msg',payload=dict(type='turn_aborted',turn_id='t',reason='Fixture interrupt'))]
        self.add(records)
        with self.store.connection() as c:
            before=[tuple(r) for r in c.execute('SELECT * FROM events ORDER BY id')]
            c.execute('DELETE FROM activity_signals')
            c.execute("DELETE FROM settings WHERE key='activity_views_v1'")
        views.init(self.store);self.store.scan();self.store.scan()
        with self.store.connection() as c:
            self.assertEqual([tuple(r) for r in c.execute('SELECT * FROM events ORDER BY id')],before)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM activity_signals').fetchone()[0],1)

    def test_missing_source_is_reported_and_prevents_bulk_analysis(self):
        self.assertEqual(self.report('process')['sources']['present'],1)
        self.f.source.unlink()
        data=self.report('process');self.assertEqual(data['sources']['unavailable'],1)
        with patch('task_history.start') as start:
            with self.assertRaisesRegex(ValueError,'transcript sources are unavailable'):
                views.analyze_selected(self.store,[self.task])
            start.assert_not_called()

    def test_selected_analysis_is_explicit_bounded_and_reuses_existing_runner(self):
        with patch('task_history.start',return_value={'id':'job','status':'queued'}) as start:
            result=views.analyze_selected(self.store,[self.task])
            start.assert_called_once_with(self.store,self.task,'overview')
            self.assertEqual(result['jobs'][0]['status'],'queued')
        for ids in ([],[self.task]*2,['a','b','c']):
            with self.assertRaises(ValueError):views.analyze_selected(self.store,ids)
        with patch('task_history.start') as start:
            with self.assertRaises(ValueError):views.analyze_selected(self.store,[self.task,'foreign'])
            start.assert_not_called()


if __name__=='__main__':unittest.main()
