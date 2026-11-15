"""Browser workflows without an installed automation SDK or real model calls.

Start a separately reviewed Firefox/geckodriver runtime, then set
TTGL_WEBDRIVER_URL and TTGL_FIREFOX_BINARY (path inside that runtime).
"""
import json
import os
from pathlib import Path
import time
import threading
import unittest
from unittest.mock import patch
import urllib.request

from webdriver_qa import Browser
import test_usage_views_browser
import task_history
import task_evidence
import bulk_analysis
import steering


@unittest.skipUnless(os.environ.get('TTGL_WEBDRIVER_URL'),'Opt-in WebDriver QA')
class WorkspaceWebDriverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.browser=Browser(os.environ['TTGL_WEBDRIVER_URL'],os.environ['TTGL_FIREFOX_BINARY'])
    @classmethod
    def tearDownClass(cls):cls.browser.close()

    def setUp(self):
        host=test_usage_views_browser.UsagePagesBrowserTests();self.f,self.origin,self.task=host.fixture();self.addCleanup(host.doCleanups)
        self.b=self.browser;self.b.size(1440)
        # Even an unexpected analysis click can never invoke a model in this suite.
        guard=patch.object(task_history,'run_model',side_effect=AssertionError('Unexpected inference'));guard.start();self.addCleanup(guard.stop)
        launch=patch.object(bulk_analysis.subprocess,'Popen');self.launch=launch.start();self.launch.return_value.pid=123456;self.addCleanup(launch.stop)
        self.b.goto(self.origin+'/?range=all');self.b.ready()
        self.b.js('window.qaErrors=[];addEventListener("error",e=>qaErrors.push(e.message));addEventListener("unhandledrejection",e=>qaErrors.push(String(e.reason)));')
        def evidence():
            dest=Path(os.environ.get('TTGL_QA_ARTIFACTS','/tmp/observatory-webdriver-qa'));dest.mkdir(parents=True,exist_ok=True)
            self.b.shot(str(dest/(self._testMethodName+'.png')))
            (dest/(self._testMethodName+'.json')).write_text(json.dumps({'url':self.b.request('/url'),'errors':self.b.js('return window.qaErrors||[]'),'text':self.b.text('body')},indent=2))
        self.addCleanup(evidence)

    def goto(self,path):self.b.goto(self.origin+path);self.b.ready()
    def contains(self,css,text):self.b.wait('document.querySelector('+json.dumps(css)+')?.innerText.includes('+json.dumps(text)+')')
    def close(self):self.b.button('Close','#modal');self.b.closed()
    def assert_clean(self):self.assertEqual(self.b.js('return window.qaErrors||[]'),[])
    def many_tasks(self,count=43):
        with self.f.store.connection() as c:project=c.execute('SELECT project_id FROM tasks WHERE id=?',(self.task,)).fetchone()[0]
        ids=[]
        for i in range(count):
            task=self.f.store.mutate('task',dict(project_id=project,title=f'Pagination record {i:02}'+(' unique-marker' if i==0 else ''),goal=f'Goal {i}'))['id'];ids.append(task)
            with self.f.store.connection() as c:
                turn='page'+str(i);c.execute('INSERT INTO turns VALUES(?,?,?,?,?,?,?)',('s',turn,'/repo',f'Paging prompt {i:02}','2026-11-05T00:01:00Z','2026-11-05T00:01:02Z',1));c.execute('INSERT INTO assignments VALUES(?,?,?)',('s',turn,task))
                c.execute('INSERT INTO events(id,session_id,turn_id,kind,name,ts,usage,model) VALUES(?,?,?,?,?,?,?,?)',(turn,'s',turn,'generation','Response','2026-11-05T00:01:01Z',json.dumps(dict(input_tokens=i*100,cached_input_tokens=0,output_tokens=10,total_tokens=i*100+10)),'test-model'))
        return ids

    def test_navigation_responsive_theme_and_settings(self):
        views=['overview','taskactivity','tasks','analytics','costs','tools','timeline','agents','process','outcomes','investigate','impact','suggestions','knowledge','live','steering','settings']
        for width,theme in [(1440,'light'),(768,'light'),(390,'dark')]:
            self.b.size(width);self.b.js('document.documentElement.dataset.theme=arguments[0]',theme)
            for view in views:
                with self.subTest(width=width,view=view):
                    self.b.nav(view);self.assertLessEqual(self.b.js('return document.documentElement.scrollWidth'),width)
                    geometry=self.b.js('const form=document.querySelector("#page-scope>form");if(!form)return null;const r=form.getBoundingClientRect();return {height:r.height,bottom:r.bottom,title:document.querySelector(".page-header").getBoundingClientRect().top};');
                    if geometry:self.assertLessEqual(geometry['height'],48);self.assertLessEqual(geometry['bottom'],geometry['title'])
        self.b.size(1440);self.b.js('document.documentElement.dataset.theme="light"');self.b.click('#theme')
        self.goto('/?range=all#settings');self.assertEqual(self.b.js('return document.documentElement.dataset.theme'),'dark')
        self.b.fill('.rate-editor',json.dumps(dict(unit='USD',as_of='2026-11-15',models={})));self.b.button('Save rate scenario');self.contains('#toast','saved')
        self.assertEqual(json.load(urllib.request.urlopen(self.origin+'/api/work-cost-rates'))['models'],{})
        self.assert_clean()

    def test_top_scope_controls_apply_persist_and_keep_search_drafts(self):
        import work_analytics
        with self.f.store.connection() as c:project=c.execute('SELECT project_id FROM tasks WHERE id=?',(self.task,)).fetchone()[0]
        self.b.click('#page-scope [data-range="1d"]');self.b.ready();self.assertIn('range=1d',self.b.request('/url'))
        self.b.click('#page-scope [data-range="all"]');self.b.ready();self.b.select('#page-scope [name=project]',project);self.b.select('#page-scope [name=workspace]','/repo');self.b.button('Apply filters','#page-scope');self.b.ready();self.assertIn('workspace=%2Frepo',self.b.request('/url'))
        self.goto(self.b.request('/url').removeprefix(self.origin));self.assertEqual(self.b.js('return document.querySelector("#page-scope [name=project]").value'),project)
        self.b.size(390);self.assertTrue(self.b.js('const f=document.querySelector("#page-scope>form");return f.querySelector("button[type=submit]").getBoundingClientRect().right<=f.getBoundingClientRect().right'));self.b.select('#page-scope [name=range]','7d');self.b.button('Apply filters','#page-scope');self.b.ready();self.assertIn('range=7d',self.b.request('/url'));self.assertLessEqual(self.b.js('return document.querySelector("#page-scope>form").getBoundingClientRect().height'),48)
        self.b.size(1440);self.b.nav('tasks');self.b.fill('[data-work-search] [name=query]','Fix')
        original=work_analytics.overview;started=threading.Event();release=threading.Event();self.addCleanup(release.set)
        def delayed(*args,**kwargs):
            started.set();release.wait(10);return original(*args,**kwargs)
        with patch.object(work_analytics,'overview',side_effect=delayed):
            self.b.button('Search','[data-work-search]');self.assertTrue(started.wait(3));self.b.fill('[data-work-search] [name=query]','Pending draft');self.b.js('document.activeElement.setSelectionRange(3,3)');release.set();self.b.ready()
        self.assertEqual(self.b.js('return document.querySelector("[data-work-search] [name=query]").value'),'Pending draft');self.assertEqual(self.b.js('return document.activeElement.selectionStart'),3);self.assert_clean()

    def test_global_task_pagination_sort_filter_and_preferences(self):
        self.many_tasks();self.b.nav('tasks');self.assertEqual(self.b.count('[data-table=work-tasks] tbody tr'),20)
        self.b.click('[data-page=work-tasks][data-delta="1"]');self.b.wait('document.querySelector("[data-list-jump=work-tasks]")?.value==="2"')
        self.b.select('[data-list-size=work-tasks]','10');self.b.wait('document.querySelectorAll("[data-table=work-tasks] tbody tr").length===10')
        self.b.fill('[data-list-jump=work-tasks]','5');self.b.request('/element/'+self.b.element('[data-list-jump=work-tasks]')+'/value',{'text':'\ue007'});self.b.wait('document.querySelector("[data-list-jump=work-tasks]")?.value==="5" && document.querySelectorAll("[data-table=work-tasks] tbody tr").length===4')
        self.b.click('[data-sort=work-tasks][data-key=tokens]');self.b.wait('document.querySelector("[data-table=work-tasks] th[aria-sort=ascending]")?.innerText.includes("Tokens")')
        self.b.click('[data-sort=work-tasks][data-key=tokens]');self.contains('[data-table=work-tasks] tbody tr','Pagination record 42')
        self.b.click('[data-toggle-filters=work-tasks]');self.b.fill('[data-column-filter=work-tasks][data-key=tokens]','>= 4000');self.b.wait('document.querySelectorAll("[data-table=work-tasks] tbody tr").length===3')
        self.b.click('[data-table=work-tasks] .column-picker summary');self.b.click('[data-column-toggle=work-tasks][data-key=type]')
        self.goto('/?range=all#tasks');self.assertEqual(self.b.js('return document.querySelector("[data-column-filter=work-tasks][data-key=tokens]").value'),'>= 4000');self.assertEqual(self.b.count('[data-table=work-tasks] tbody tr'),3)
        self.assertEqual(self.b.count('[data-table=work-tasks] th button[data-key=type]'),0)
        self.b.click('[data-reset-table=work-tasks]');self.b.wait('document.querySelectorAll("[data-table=work-tasks] tbody tr").length===10')
        self.b.fill('[data-search=work-tasks]','unique-marker');self.b.wait('document.querySelectorAll("[data-table=work-tasks] tbody tr").length===1');self.contains('[data-table=work-tasks] tbody','record 00')
        self.assert_clean()

    def test_native_turn_pagination_search_sources_and_day_drilldown(self):
        self.many_tasks();self.b.nav('taskactivity');self.assertEqual(self.b.count('[data-table=activity-turns] tbody tr'),20)
        self.b.click('[data-page=activity-turns][data-delta="1"]');self.b.wait('document.querySelector("[data-list-jump=activity-turns]")?.value==="2"')
        self.b.fill('[data-search=activity-turns]','Fix the problem');self.b.wait('document.querySelectorAll("[data-table=activity-turns] tbody tr").length===1');self.contains('[data-table=activity-turns] tbody','Fix the problem')
        self.b.click('[data-table=activity-turns] [data-dash-turn]');self.contains('#modal','Fix the problem');self.b.click('[data-dash-source]');self.contains('[data-dash-output]','source')
        self.b.click('#modal [data-dash-task]');self.b.wait('document.querySelector(".task-detail")');self.b.nav('overview');self.b.click('[data-usage-day]');self.contains('#modal','turns');self.b.wait('document.querySelectorAll("#modal [data-dash-turn]").length===20');self.assertEqual(self.b.count('#modal [data-dash-turn]'),20);self.close()
        self.assert_clean()

    def test_hierarchy_step_pagination_citations_and_process_results(self):
        with self.f.store.connection() as c:
            for i in range(25):c.execute('INSERT INTO events(id,session_id,turn_id,kind,name,ts,runtime,failed) VALUES(?,?,?,?,?,?,?,?)',(f'qa-step{i}','s','t','tool',f'Check {i}','2026-11-05T00:00:04Z',.1,0))
        job=task_history.start(self.f.store,self.task,'process',_launch=False)
        with self.f.store.connection() as c:body=json.loads(c.execute('SELECT snapshot FROM task_history_jobs WHERE id=?',(job['id'],)).fetchone()[0])
        groups=[dict(title='Review recorded work',summary='Fixture source interpretation',activity='investigate',tags=['fixture'],confidence=.7,step_ids=[r['id'] for r in body['steps']],outcome='failed',outcome_reason='Retained failed test',runtime_role='finite_operation')]
        result=dict(summary='Fixture interpretation, not an independent grade',subtasks=groups,task_type='bugfix',knowledge=[],outcome='failed',outcome_reason='Retained failed test',outcome_confidence=.7,outcome_step_ids=['s:tool:check'],intervention='none_observed',intervention_reason='No correction observed',intervention_turn_ids=[])
        task_history.publish(self.f.store,job['id'],result,{'total_tokens':123})
        self.goto('/tasks/'+self.task+'?range=all');self.contains('[data-table=task-report-steps]','pytest');
        initial=self.b.js('return performance.getEntriesByType("resource").map(r=>r.name)');self.assertFalse(any('/api/work-explorer?' in u or '/api/work-steps?' in u or '/api/task-timeline?' in u for u in initial));
        self.contains('.task-detail','failed');self.contains('[data-table=work-subtasks]','Review recorded work')
        self.b.click('[data-table=work-subtasks] tbody tr:nth-child(2) [data-subtask]');self.b.wait('document.querySelectorAll("[data-table=work-steps] tbody tr").length===20');self.b.click('[data-page=work-steps][data-delta="1"]');self.b.wait('document.querySelectorAll("[data-table=work-steps] tbody tr").length===8')
        self.b.button('All steps');self.b.click('.step-panel>summary');self.b.wait('document.querySelector("[data-work-timeline] [data-inspect-step]")');self.b.click('[data-inspect-step="s:tool:check"]');self.contains('[data-timeline-evidence]','1 failed')
        self.b.button('All tasks');self.b.ready();self.b.select('[data-work-filter=result]','failed');self.contains('[data-table=work-tasks]','Fix');self.b.select('[data-work-filter=result]','done');self.contains('[data-table=work-tasks]','Nothing here yet')
        self.b.nav('tools');self.contains('#content','INTERPRETED CATEGORIES');self.assertEqual(sum('/api/task-report?' in u for u in self.b.js('return performance.getEntriesByType("resource").map(r=>r.name)')),1);self.assert_clean()

    def test_cost_tools_process_agents_timeline_outcomes_and_evidence(self):
        task_evidence.add(self.f.store,self.task,'intervention','QA acceptance corrected','Explicit fixture correction',outcome='confirmed')
        self.b.nav('costs');self.contains('[data-table=cost-models]','test-model');self.b.click('[data-usage-day]');self.contains('#modal','Fix');self.b.click('[data-usage-source]');self.contains('[data-usage-output]','source');self.close()
        self.b.nav('tools');self.b.click('.tool-treemap button[aria-label="Shell · rg"]');self.contains('[data-table=tool-targets]','rg foo');self.b.button('rg foo');self.b.click('[data-usage-source]');self.contains('[data-usage-output]','CommandExecution');self.close()
        self.b.select('[aria-label="Treemap measure"]','runtime');self.b.select('[aria-label="Tool cost attribution"]','step_share');self.b.button('Apply filters');self.contains('[data-table=usage-tools]','Estimated tool share')
        self.b.nav('agents');self.b.click('[data-agent-detail]');self.contains('#modal','native sessions');self.b.click('[data-analysis-source]');self.contains('[data-analysis-output]','source');self.close()
        self.b.nav('timeline');self.assertEqual(self.b.count('.heat-cell'),168);self.b.select('[aria-label="Heatmap measure"]','tokens');self.b.click('.heat-cell:not(:disabled)');self.contains('#modal','UTC');self.close()
        self.b.nav('outcomes');self.contains('#content','warning');self.b.button('Inspect signals');self.contains('#modal','QA acceptance corrected');self.close();self.assert_clean()

    def test_evidence_explorer_query_tabs_raw_and_reload(self):
        self.b.nav('investigate');self.contains('.trace-results','Fix');self.b.fill('[data-trace-filters] [name=query]','Resolve failure');self.b.button('Apply');self.contains('.trace-results','Fix')
        self.b.button('Inspect steps');self.b.wait('document.querySelectorAll(".trace-result").length===4');self.goto(self.b.request('/url').removeprefix(self.origin));self.assertEqual(self.b.count('.trace-result'),4)
        self.b.button('Read original evidence');self.contains('#modal','source');self.close();self.b.button('Tools','.trace-modes');self.b.button('Find turns');self.contains('.trace-results','Fix');self.assert_clean()

    def test_bulk_start_stop_pagination_and_resumed_polling(self):
        self.many_tasks();self.b.click('#bulk-analysis');self.contains('#modal','No bulk analysis');self.b.click('[data-bulk-start]');self.contains('#modal','44');self.assertEqual(self.launch.call_count,1)
        self.assertEqual(self.b.count('[data-table=bulk-analysis-items] tbody tr'),20)
        self.b.click('[data-page=bulk-analysis-items][data-delta="1"]');self.b.wait('document.querySelector("[data-list-jump=bulk-analysis-items]")?.value==="2"')
        # Focus spans a poll; moving focus away must allow later refreshes.
        self.b.js('document.querySelector("[data-list-jump=bulk-analysis-items]").focus()');time.sleep(4.3)
        with self.f.store.connection() as c:c.execute("UPDATE bulk_analysis_items SET status='failed',error='QA refresh witness' WHERE task_id=?",(self.task,))
        self.b.click('#modal-title');self.contains('#modal','failed: 1')
        self.b.click('[data-bulk-stop]');self.contains('#modal','stopping');self.assertEqual(self.launch.call_count,1)
        with self.f.store.connection() as c:self.assertEqual(c.execute('SELECT status FROM bulk_analysis_batches').fetchone()[0],'stopping')
        self.assert_clean()

    def test_local_collection_controls_selection_and_row_actions(self):
        self.b.js('''return import('/data-list.js').then(({renderList,selectionColumn,selectedIds})=>{
          window.selectedIds=selectedIds;document.querySelector('#content').innerHTML='<form id="qa-form"><div id="qa-list"></div></form>';window.submits=0;document.querySelector('#qa-form').onsubmit=e=>{e.preventDefault();window.submits++};
          const rows=Array.from({length:55},(_,i)=>({id:String(i),title:'Row '+String(i).padStart(2,'0'),amount:i===14?null:i,note:i===42?'résumé marker':'ordinary'}));
          document.querySelector('#qa-list').innerHTML=renderList('qa-list',[selectionColumn('qa-list',{limit:2}),{key:'title',label:'Name'},{key:'amount',label:'Amount',numeric:true},{key:'note',label:'Notes',hiddenByDefault:true}],rows,r=>[{id:'open',label:'Open row',onSelect:()=>window.opened=r.id}]);
        })''')
        self.b.wait('document.querySelector("[data-list-select=qa-list]")');self.b.click('[data-list-select=qa-list][data-choice="0"]');self.b.click('[data-page=qa-list][data-delta="1"]');self.b.click('[data-list-select=qa-list][data-choice="20"]');self.assertEqual(self.b.js('return selectedIds("qa-list")'),['0','20'])
        self.b.button('Actions for Row 20');self.b.button('Open row');self.assertEqual(self.b.js('return window.opened'),'20')
        self.b.select('[data-list-size=qa-list]','100');self.b.click('[data-sort=qa-list][data-key=amount]');self.contains('[data-table=qa-list] tbody tr:last-child','Row 14');self.b.click('[data-sort=qa-list][data-key=amount]');self.contains('[data-table=qa-list] tbody tr:first-child','Row 54')
        self.b.fill('[data-search=qa-list]','resume marker');self.assertEqual(self.b.count('[data-table=qa-list] tbody tr'),1);self.contains('[data-table=qa-list] tbody','Row 42');self.assertEqual(self.b.js('return window.submits'),0);self.assert_clean()

    def test_populated_reference_routes_and_retained_image(self):
        from test_reference_acceptance_browser import populated_fixture
        fixture,origin,tasks,project=populated_fixture(self)
        routes=[('/?range=all','dashboard-tools'),('/tasks?range=all','activity-turns'),('/tasks/'+tasks[-1]+'?range=all','task-report-steps'),('/tools?range=all','usage-tools'),('/costs?range=all','cost-models'),('/timeline?range=all','timeline-turns'),('/agents?range=all','agent-comparison'),('/process?range=all','process-transitions'),('/outcomes?range=all','tasks-needing-fix'),('/suggestions?range=all','built-in-findings'),('/impact?range=all','impact-changes'),('/live/rules?range=all','steering-rules'),('/live?range=all','steering-log')]
        for width in (1440,390):
            self.b.size(width)
            for path,table in routes:
                with self.subTest(width=width,path=path):
                    self.b.goto(origin+path);self.b.ready();self.b.wait('document.querySelector('+json.dumps('[data-table="'+table+'"]')+')');self.assertLessEqual(self.b.js('return document.documentElement.scrollWidth'),width)
        self.b.goto(origin+'/tasks/'+tasks[-1]+'?range=all');self.b.ready();self.b.wait('document.querySelector("[data-report-image] img")?.complete && document.querySelector("[data-report-image] img")?.naturalWidth===1');self.b.click('[data-report-image]');self.b.wait('document.querySelector(".report-image-full")?.complete && document.querySelector(".report-image-full")?.naturalWidth===1');self.close()

    def test_process_map_drilldown_opens_its_task(self):
        self.b.nav('process');self.b.click('[data-flow-node="implement"]');self.contains('#modal','Fix');self.b.click('[data-analysis-task]');self.contains('.task-detail','Fix');self.assert_clean()

    def test_context_value_filters_local_exact_unknown_and_keyboard(self):
        self.b.js('''return import('/data-list.js').then(({renderList})=>{document.querySelector('#content').innerHTML=renderList('context-fixture',[{key:'name',label:'Name'},{key:'value',label:'Value'},{key:'amount',label:'Amount',numeric:true}],[{name:'One',value:'alpha',amount:0},{name:'Two',value:'alphabet',amount:1},{name:'Three',value:'alpha',amount:0},{name:'Unknown row',value:null,amount:null}],null);})''')
        cell='[data-table=context-fixture] tbody tr:first-child [data-list-cell=value]'
        self.b.context_click(cell);self.b.button('Show matching','[data-cell-filter-menu]');self.assertEqual(self.b.count('[data-table=context-fixture] tbody tr'),2);self.assertNotIn('alphabet',self.b.text('[data-table=context-fixture] tbody'))
        self.b.click('[data-reset-table=context-fixture]');self.b.context_click(cell);self.b.button('Filter out','[data-cell-filter-menu]');self.assertEqual(self.b.count('[data-table=context-fixture] tbody tr'),2);self.contains('[data-table=context-fixture] tbody','alphabet');self.contains('[data-table=context-fixture] tbody','Unknown row')
        self.b.click('[data-reset-table=context-fixture]');self.b.context_click('[data-table=context-fixture] tbody tr:last-child [data-list-cell=amount]');self.b.button('Show matching','[data-cell-filter-menu]');self.assertEqual(self.b.count('[data-table=context-fixture] tbody tr'),1);self.contains('[data-table=context-fixture] tbody','Unknown row')
        self.b.click('[data-reset-table=context-fixture]');self.b.context_click('[data-table=context-fixture] tbody tr:first-child [data-list-cell=amount]');self.b.button('Filter out','[data-cell-filter-menu]');self.assertEqual(self.b.count('[data-table=context-fixture] tbody tr'),2);self.contains('[data-table=context-fixture] tbody','Unknown row')
        self.b.click('[data-reset-table=context-fixture]');self.b.context_click(cell);self.b.request('/element/'+self.b.element('[data-cell-filter-menu] [role=menuitem]')+'/value',{'text':'\ue00c'});self.b.wait('!document.querySelector("[data-cell-filter-menu]")');self.assertEqual(self.b.count('[data-table=context-fixture] tbody tr'),4)
        self.b.request('/actions',{'actions':[{'type':'key','id':'context-keys','actions':[{'type':'keyDown','value':'\ue008'},{'type':'keyDown','value':'\ue03a'},{'type':'keyUp','value':'\ue03a'},{'type':'keyUp','value':'\ue008'}]}]});self.b.wait('document.querySelector("[data-cell-filter-menu] [role=menu]")?.matches(":popover-open")');self.b.click('h1');self.b.wait('!document.querySelector("[data-cell-filter-menu]")');self.assert_clean()

    def test_context_value_filters_remote_full_scope_and_reload(self):
        self.many_tasks();self.b.nav('tasks');table='[data-table=work-tasks]'
        self.b.click('[data-page=work-tasks][data-delta="1"]');self.b.wait('document.querySelector("[data-list-jump=work-tasks]")?.value==="2"')
        self.b.context_click(table+' tbody tr:first-child [data-list-cell=status]');self.b.button('Show matching','[data-cell-filter-menu]');self.b.wait('document.querySelector("[data-list-jump=work-tasks]")?.value==="1"');self.contains(table+' .list-pagination','of 44');self.assertEqual(self.b.count(table+' tbody tr'),20)
        self.b.context_click(table+' tbody tr:first-child [data-list-cell=status]');self.b.button('Filter out','[data-cell-filter-menu]');self.contains(table,'No matching rows');self.contains(table+' .list-pagination','of 0');self.goto('/?range=all#tasks');self.contains(table,'No matching rows');self.assertEqual(self.b.js('return document.querySelector("[data-column-filter=work-tasks][data-key=status]").value'),'is not "active"')
        self.b.click('[data-reset-table=work-tasks]');self.b.wait('document.querySelectorAll("[data-table=work-tasks] tbody tr").length===20');self.assert_clean()

    def test_context_value_filters_inside_modal(self):
        self.b.click('[data-usage-day]');self.b.wait('document.querySelector("#modal [data-list-cell=models]")');self.b.context_click('#modal [data-list-cell=models]');self.b.button('Show matching','[data-cell-filter-menu]');self.b.wait('document.querySelector("#modal [data-column-filter][data-key=models]")?.value==='+json.dumps('is "test-model"'));self.contains('#modal','Fix the problem');self.close();self.assert_clean()

    def test_live_notes_pause_resume_and_delivery(self):
        steering.receive(self.f.store,dict(session_id='qa-live',event_id='start',event='start',workspace='/repo',cost_usd=0))
        self.b.nav('live');self.b.button('Send note');self.b.fill('#modal [name=note]','Review the checks');self.b.button('Queue note');self.b.closed()
        result=steering.receive(self.f.store,dict(session_id='qa-live',event_id='prompt',event='prompt',workspace='/repo'))
        self.assertIn('Review the checks',result['messages']);self.b.button('Pause');self.b.wait('document.querySelector("[data-session-pause]")?.innerText==="Resume"');self.b.button('Resume');self.b.wait('document.querySelector("[data-session-pause]")?.innerText==="Pause"');self.assert_clean()

    def test_projects_knowledge_steering_and_impact_mutations(self):
        self.b.nav('knowledge');self.b.fill('[aria-label="Graphiti explorer URL"]','https://example.org/graph');self.b.button('Save link','[data-explorer-link=graphiti]');self.b.wait('document.querySelector("[data-explorer-link=graphiti] a")?.href==="https://example.org/graph"');self.goto('/?range=all#knowledge');self.assertEqual(self.b.js('return document.querySelector(arguments[0]).value','[aria-label="Graphiti explorer URL"]'),'https://example.org/graph')
        self.b.nav('settings');self.b.button('Projects');self.b.button('Add project');self.b.fill('#modal [name=name]','QA project');self.b.fill('#modal [name=repo]','/qa');self.b.button('Add project','#modal');self.b.closed();self.contains('tbody','QA project')
        self.b.nav('steering');self.b.button('Add rule');self.b.fill('#modal [name=name]','QA rule');self.b.fill('#modal [name=message]','Review operation');self.b.fill('#modal [name=pattern]','deploy production');self.b.button('Save rule');self.b.closed();self.contains('[data-table=steering-rules]','QA rule')
        self.b.nav('impact');self.b.button('Record a change');self.b.fill('#modal [name=title]','QA change');self.b.button('Record change','#modal');self.b.closed();self.contains('.applied-change','QA change');self.b.button('Delete','.applied-change');self.b.button('Delete change','#modal');self.b.closed();self.b.wait('!document.querySelector(".applied-change")');self.assert_clean()

if __name__=='__main__':unittest.main()
