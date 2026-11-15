import json
from datetime import datetime,timezone
import unittest
import test_workspace
import optimization as o
import work_analytics as a


class OptimizationTests(unittest.TestCase):
    def setUp(self):
        self.f=test_workspace.WorkspaceTests();self.f.setUp();self.addCleanup(self.f.directory.cleanup)
        self.store=self.f.store
        a.save_rates(self.store,{'unit':'USD','as_of':'2026-11-05','models':{'test-model':{'input':1,'cached':.1,'output':2}}})
        self.store.scan();self.project,self.task=self.f.define_task();self.store.mutate('assign',{'session_id':'s','turn_id':'t','task_id':self.task})
        self.now=a.timestamp('2026-11-06T00:00:00Z')

    def add_native(self,items):
        rows=self.f.rows+items
        self.f.source.write_text(''.join(json.dumps(r)+'\n' for r in rows));self.store.ingest(self.f.source)

    def native(self,ident,command,output='ok',failed=False,stamp='2026-11-05T00:00:03Z'):
        return dict(timestamp=stamp,type='event_msg',payload=dict(type='item_completed',thread_id='s',turn_id='t',item=dict(type='CommandExecution',id=ident,command=command,aggregated_output=output,exit_code=1 if failed else 0)))

    def test_measured_metrics_and_unsupported_fields_stay_unknown(self):
        data=o.dashboard(self.store,range='all',clock=self.now)
        metrics={m['id']:m for m in data['metrics']}
        self.assertEqual(metrics['context']['last_7d'],100)
        self.assertEqual(metrics['failed_tools']['last_7d'],0)
        self.assertAlmostEqual(data['spend'],.000048)
        for key in ('cache_rebuild','cache_5m','main_top','sub_top','break_warnings'):
            self.assertIsNone(metrics[key]['last_7d'],key)
        self.assertEqual(data['coverage']['native_details'],1)
        self.assertEqual(o.dashboard(self.store,project='unknown',range='all',clock=self.now)['coverage']['events'],0)

    def test_identical_failures_and_commit_refs_keep_original_steps(self):
        items=[self.native('fail'+str(i),'pytest tests',failed=True,stamp=f'2026-11-05T00:00:0{i+2}Z') for i in range(3)]
        items+=[self.native('commit','git commit -m fix','[work abc1234] Fix validation\n 1 file changed',stamp='2026-11-05T00:00:07Z')]
        self.add_native(items)
        data=o.dashboard(self.store,range='all',clock=self.now)
        loop=next(l for l in data['loops'] if l['kind']=='Same call keeps failing')
        self.assertEqual(loop['event_ids'],['s:tool:fail0','s:tool:fail1','s:tool:fail2'])
        self.assertEqual(data['commits'][0]['ref'],'abc1234');self.assertEqual(data['commits'][0]['event_id'],'s:tool:commit')
        finding=next(f for f in data['findings'] if f['id']=='failed_tools')
        self.assertEqual(finding['count'],3);self.assertIsNone(finding['estimated_saving'])

    def test_edit_check_pattern_requires_three_distinct_pairs(self):
        def edit(i):return dict(timestamp=f'2026-11-05T00:00:{i:02d}Z',type='event_msg',payload=dict(type='item_completed',thread_id='s',turn_id='t',item=dict(type='FileChange',id='edit'+str(i),changes={'file.py':{'diff':'+x'}},status='completed')))
        self.add_native([edit(i) for i in range(2,7)]+[self.native('failed','pytest',failed=True,stamp='2026-11-05T00:00:07Z')])
        self.assertFalse(any(l['kind']=='Repeated edit and failed check' for l in o.dashboard(self.store,range='all',clock=self.now)['loops']))
        self.add_native([edit(2),self.native('check3','pytest',failed=True,stamp='2026-11-05T00:00:03Z'),edit(4),self.native('check5','pytest',failed=True,stamp='2026-11-05T00:00:05Z'),edit(6),self.native('check7','pytest',failed=True,stamp='2026-11-05T00:00:07Z')])
        self.assertTrue(any(l['kind']=='Repeated edit and failed check' for l in o.dashboard(self.store,range='all',clock=self.now)['loops']))

    def test_different_inputs_do_not_form_a_failure_loop(self):
        self.add_native([self.native('fail'+str(i),'pytest test_'+str(i),failed=True) for i in range(3)])
        self.assertFalse(any(l['kind']=='Same call keeps failing' for l in o.dashboard(self.store,range='all',clock=self.now)['loops']))

    def test_large_output_uses_actual_characters_not_bytes_as_tokens(self):
        self.add_native([self.native('large','cat file','é'*16000)])
        data=o.dashboard(self.store,range='all',clock=self.now)
        self.assertIn('s:tool:large',next(f for f in data['findings'] if f['id']=='large_output')['evidence_ids'])
        self.assertIsNone(next(f for f in data['findings'] if f['id']=='large_output')['affected_cost'])
        self.assertAlmostEqual(data['spend'],.000048)

    def test_change_validation_fixed_windows_and_new_session_split(self):
        at=a.timestamp('2026-11-05T12:00:00Z')
        with self.store.connection() as c:
            # One existing session spans the intervention; new-session cohort must exclude it.
            c.execute("INSERT INTO events(id,session_id,turn_id,kind,name,ts,usage,model) VALUES(?,?,?,?,?,?,?,?)",('after','s','t','generation','Model response','2026-11-05T13:00:00Z',json.dumps(dict(input_tokens=10000,cached_input_tokens=0,output_tokens=10,total_tokens=10010)),'test-model'))
        ch=o.change(self.store,dict(title='Reduce context',at='2026-11-05T12:00:00Z',takes_effect='new_sessions',metrics=['context'],workspace='',notes=''))
        data=o.dashboard(self.store,range='1d',clock=at+86400)
        comparison=data['changes'][0]['comparisons'][0]
        self.assertEqual(comparison['before'],100);self.assertIsNone(comparison['after']);self.assertIsNone(comparison['interval'])
        self.assertEqual(comparison['status'],'insufficient_data')
        with self.assertRaises(ValueError):o.change(self.store,dict(title='Bad',at='bad',metrics=['context']))
        with self.assertRaises(ValueError):o.change(self.store,dict(title='Bad',at='2026-11-05',metrics=['invented']))
        o.change(self.store,dict(id=ch['id'],delete=True))
        self.assertEqual(o.dashboard(self.store,clock=self.now)['changes'],[])

    def test_hourly_cluster_interval_and_window_independent_of_chart_range(self):
        at=a.timestamp('2026-11-05T12:00:00Z')
        with self.store.connection() as c:
            c.execute('DELETE FROM assignments');c.execute('DELETE FROM optimization_facts');c.execute('DELETE FROM events')
            for index in range(20):
                stamp=at+(index-10)*3600;ts=datetime.fromtimestamp(stamp,timezone.utc).isoformat();context=200 if index<10 else 100
                c.execute('INSERT INTO events(id,session_id,turn_id,kind,name,ts,usage,model) VALUES(?,?,?,?,?,?,?,?)',(str(index),'s','t','generation','Model response',ts,json.dumps(dict(input_tokens=context,cached_input_tokens=0,output_tokens=10,total_tokens=context+10)),'test-model'))
        o.change(self.store,dict(title='Context limit',at='2026-11-05T12:00:00Z',metrics=['context']))
        one=o.dashboard(self.store,range='1d',clock=at+10*3600)['changes'][0]['comparisons'][0]
        all_time=o.dashboard(self.store,range='all',clock=at+10*3600)['changes'][0]['comparisons'][0]
        self.assertEqual(one,all_time);self.assertEqual(one['interval'],[-100,-100]);self.assertEqual(one['status'],'lower')

    def test_explicit_agent_roles_cache_ttl_and_small_turn_metadata(self):
        rows=json.loads(json.dumps(self.f.rows).replace('"s"','"sub"'))
        rows[0]['payload'].update(cwd='/subrepo',source={'subagent':{'thread_spawn':{'agent_role':'explore'}}})
        for r in rows:
            if r['type']=='token_usage_record' and r['payload'].get('thread_id')=='sub':r['payload']['usage'].update(cache_creation_input_tokens=50,cache_creation_5m_input_tokens=10)
        rows.append(dict(timestamp='2026-11-05T00:10:00Z',type='token_usage_record',payload=dict(thread_id='sub',turn_id='t',response_id='second',usage=dict(input_tokens=100,cached_input_tokens=80,output_tokens=10,total_tokens=110,cache_creation_input_tokens=50,cache_creation_5m_input_tokens=10))))
        rows.append(dict(timestamp='2026-11-05T00:10:01Z',type='event_msg',payload=dict(type='item_completed',thread_id='sub',turn_id='t',item=dict(type='AssistantMessage',id='answer',content=[dict(type='text',text='Done')]))))
        path=self.f.source.with_name('sub.jsonl');path.write_text(''.join(json.dumps(r)+'\n' for r in rows));self.store.ingest(path)
        project=self.store.mutate('project',dict(name='Subagents',repo='/subrepo'))['id']
        task=self.store.mutate('task',dict(project_id=project,title='Explore',goal='Inspect source'))['id']
        self.store.mutate('assign',dict(session_id='sub',turn_id='t',task_id=task))
        o.save_models(self.store,dict(top=['test-model'],small=['cheap'],short_answer=2000))
        data=o.dashboard(self.store,project=project,range='all',clock=self.now)
        metrics={m['id']:m for m in data['metrics']}
        self.assertEqual(metrics['sub_top']['last_7d'],1)
        self.assertEqual(metrics['explore_expensive']['last_7d'],1)
        self.assertEqual(metrics['cache_5m']['last_7d'],.2)
        self.assertEqual(metrics['cache_rebuild']['last_7d'],.5)
        self.assertEqual(metrics['top_small']['last_7d'],1)
        self.assertIsNone(metrics['main_top']['last_7d'])
        self.assertTrue(any(f['id']=='top_small' for f in data['findings']))

    def test_rate_scenario_unknowns_and_idempotent_facts(self):
        self.store.scan();self.store.scan()
        self.assertEqual(o.dashboard(self.store,range='all',clock=self.now)['coverage']['events'],2)
        a.save_rates(self.store,{'unit':'USD','as_of':'2026-11-05','models':{}})
        data=o.dashboard(self.store,range='all',clock=self.now)
        self.assertIsNone(data['spend']);self.assertIsNone(next(m for m in data['metrics'] if m['id']=='cost_per_task')['last_7d'])
        with self.assertRaises(ValueError):o.dashboard(self.store,range='forever')


if __name__=='__main__':unittest.main()
