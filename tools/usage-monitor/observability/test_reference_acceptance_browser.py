"""Screenshot acceptance on populated native fixtures, never real inference.

References: the user's Overall activity, Task activity/detail, Tools/drilldown,
Costs, Timeline, Agents, Process, Outcomes, Suggestions, Impact and Steering photos.
Photo data is not a measurement fixture: structure/interaction is compared, not
its exact counts, agent taxonomy, inferred savings or subscription charges.
"""
from datetime import datetime,timedelta,timezone
import html
import json
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch

import test_workspace_browser
import optimization
import steering
import task_evidence
import task_history
import work_analytics

DEST=Path('work/security/reference-acceptance-20261115')


def populated_fixture(test):
    host=test_workspace_browser.WorkspaceBrowserTests();f,origin,original=host.fixture();test.addCleanup(host.doCleanups)
    project=f.store.mutate('project',dict(name='Acceptance workspace',repo='/reference'))['id']
    work_analytics.save_rates(f.store,dict(unit='USD',as_of='2026-11-15',models={
        'opus-reference':dict(input=5,cached=.5,output=25),
        'sonnet-reference':dict(input=3,cached=.3,output=15),
        'haiku-reference':dict(input=1,cached=.1,output=5),
        'test-model':dict(input=1,cached=.1,output=2)}))
    base=datetime.now(timezone.utc).replace(hour=10,minute=0,second=0,microsecond=0)-timedelta(days=28)
    task_history.init(f.store)
    tasks=[]
    for day in range(28):
        sid=f'reference-{day:02}';stamp=base+timedelta(days=day,hours=day%5);rows=[]
        def record(typ,payload,second=0):rows.append(dict(type=typ,timestamp=(stamp+timedelta(seconds=second)).isoformat(),payload=payload))
        record('session_meta',dict(id=sid,cwd='/reference',source='cli',timestamp=stamp.isoformat()))
        record('turn_context',dict(turn_id='t',model=['opus-reference','sonnet-reference','haiku-reference'][day%3]))
        record('event_msg',dict(type='task_started',turn_id='t'))
        record('event_msg',dict(type='item_completed',thread_id=sid,turn_id='t',item=dict(type='UserMessage',content=[dict(type='text',text=f'Implement dashboard-case-{day:02} and verify the result')])) ,1)
        for phase,(command,kind) in enumerate([(['cat','src/app.ts'],'CommandExecution'),(['edit'],'FileChange'),(['pytest','tests'],'CommandExecution'),(['git','commit','-m',f'Dashboard {day:02}'],'CommandExecution')]):
            tokens=150000+day*10000+phase*25000
            record('token_usage_record',dict(thread_id=sid,turn_id='t',response_id=f'r{phase}',usage=dict(input_tokens=tokens,cached_input_tokens=int(tokens*.9),output_tokens=800,total_tokens=tokens+800,cache_creation_input_tokens=1000,cache_creation_5m_input_tokens=400)),phase*30+2)
            item=dict(type=kind,id=f'phase{phase}',status='completed')
            if kind=='FileChange':item['changes']={f'src/dashboard-{day:02}.tsx':dict(diff='+verified fixture')}
            else:item.update(command=command,exit_code=1 if phase==2 and day%5==0 else 0,aggregated_output=(f'[work {day+1:07x}] Dashboard {day:02}' if phase==3 else '3 passed' if phase==2 else 'export default fixture'),duration=dict(secs=phase+1,nanos=0))
            record('event_msg',dict(type='item_completed',thread_id=sid,turn_id='t',item=item),phase*30+15)
        if day%4==0:
            for repeat in range(3):record('event_msg',dict(type='item_completed',thread_id=sid,turn_id='t',item=dict(type='CommandExecution',id=f'repeat-{repeat}',command=['pytest','tests/retry'],exit_code=1,aggregated_output='1 failed',duration=dict(secs=1,nanos=0))),121+repeat)
        if day==27:
            image_source=dict(type='base64',media_type='image/png',data='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9ZlWQAAAAASUVORK5CYII=')
            image_item=dict(type='ImageView',id='screen',path='/private/not-read.png',status='completed',content=[dict(type='image',source=image_source)])
            record('event_msg',dict(type='item_completed',thread_id=sid,turn_id='t',item=image_item),124)
        record('event_msg',dict(type='item_completed',thread_id=sid,turn_id='t',item=dict(type='AssistantMessage',content=[dict(type='text',text='Changed the dashboard. Check the recorded validation before accepting.')])) ,125)
        record('event_msg',dict(type='task_complete',turn_id='t'),130)
        source=f.source.with_name(sid+'.jsonl');source.write_text(''.join(json.dumps(row)+'\n' for row in rows));f.store.scan()
        task=f.store.mutate('task',dict(project_id=project,title=f'Acceptance task case-{day:02}',goal=f'Implement dashboard-case-{day:02} and verify the result',acceptance='Relevant checks pass'))['id']
        f.store.mutate('assign',dict(session_id=sid,turn_id='t',task_id=task));tasks.append(task)
        with f.store.connection() as c:
            c.execute("UPDATE events SET runtime=.8 WHERE session_id=? AND kind='generation'",(sid,))
            c.execute("UPDATE native_session_facts SET role=?,agent_type=? WHERE session_id=?",('main' if day%3==0 else 'sub',None if day%3==0 else 'Explore' if day%3==1 else 'general-purpose',sid))
            for phase in range(4):c.execute('UPDATE optimization_facts SET cache_write=1000,cache_5m=400 WHERE event_id=?',(sid+':response:r'+str(phase),))
        body,digest=task_history.snapshot(f.store,task,'all');job='reference-job-'+str(day)
        with f.store.connection() as c:c.execute('INSERT INTO task_history_jobs(id,task_id,snapshot_hash,snapshot,status,created,model,operation) VALUES(?,?,?,?,?,?,?,?)',(job,task,digest,json.dumps(body),'queued',time.time(),'acceptance-fixture','overview'))
        groups=[]
        for i,activity in enumerate(['investigate','implement','test','operate']):
            members=[row['id'] for row in body['steps'][i*2:(i+1)*2]] if i<3 else [row['id'] for row in body['steps'][6:]]
            groups.append(dict(title=activity.title()+' the dashboard',summary='Deterministic acceptance fixture, not an actual model analysis.',activity=activity,tags=['reference-fixture'],step_ids=members,confidence=1))
        task_history.publish(f.store,job,dict(summary='Acceptance fixture for the supplied page screenshots.',task_type='feature',knowledge=[],subtasks=groups),{'total_tokens':0})
        if day%5==0:task_evidence.add(f.store,task,'intervention','Corrected the acceptance requirement',outcome='confirmed')
    optimization.change(f.store,dict(title='Limit large contexts',at=(base+timedelta(days=14)).isoformat(),metrics=['cost_per_task','context','large_context','context_warnings'],notes='Synthetic acceptance fixture. No causal improvement is asserted.'))
    optimization.change(f.store,dict(title='Prefer targeted file reads',at=(base+timedelta(days=17)).isoformat(),metrics=['cost_per_task','shell','shell_again'],takes_effect='new_sessions',notes='Synthetic acceptance fixture.'))
    steering.save_rule(f.store,dict(name='Shell file exploration',kind='command',mode='warn',message='Use targeted reads and search.',config=dict(tool='Bash',pattern='cat ')))
    for i in range(3):
        steering.receive(f.store,dict(session_id=f'live-reference-{i}',event_id='start',event='start',workspace='/reference',cost_usd=0))
        steering.receive(f.store,dict(session_id=f'live-reference-{i}',event_id='tool',event='pre_tool',workspace='/reference',tool='Bash',command='cat src/app.ts',cost_usd=7,context_tokens=250000))
    return f,origin,tasks,project


@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA')=='1','Opt-in browser QA')
class ReferenceAcceptanceBrowserTests(unittest.TestCase):
    def test_all_reference_pages_with_populated_data_and_shared_controls(self):
        from playwright.sync_api import sync_playwright,expect
        f,origin,tasks,project=populated_fixture(self)
        DEST.mkdir(parents=True,exist_ok=True);screens=[];errors=[];bad_responses=[]
        routes=[('overall','/?range=all','Overall activity','dashboard-tools'),('tasks','/tasks?range=all','Task activity','activity-turns'),
          ('task-detail','/tasks/'+tasks[-1]+'?range=all',None,'task-report-steps'),('tools','/tools?range=all','Tool usage','usage-tools'),
          ('costs','/costs?range=all','Cost & tokens','cost-models'),('timeline','/timeline?range=all','Activity timeline','timeline-turns'),
          ('agents','/agents?range=all','Agents','agent-comparison'),('process','/process?range=all','Process map','process-transitions'),
          ('outcomes','/outcomes?range=all','Outcomes','tasks-needing-fix'),('suggestions','/suggestions?range=all','Suggestions','built-in-findings'),
          ('impact','/impact?range=all','Impact','impact-changes'),('rules','/live/rules?range=all','Steering rules','steering-rules'),
          ('live','/live?range=all','Live sessions','steering-log')]
        with patch('task_history.start',side_effect=AssertionError('Acceptance browsing must not start inference')),sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            try:
                page=browser.new_page(viewport={'width':1440,'height':1000},timezone_id='Europe/Amsterdam');page.set_default_timeout(7000)
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('response',lambda response:bad_responses.append(response.url) if '/api/' in response.url and response.status>=400 else None)
                for theme,width in [('dark',1440),('light',1440),('dark',390)]:
                    page.set_viewport_size({'width':width,'height':1000})
                    for name,path,title,list_id in routes:
                        page.goto(origin+path);page.locator('html').evaluate("(node,value)=>{node.dataset.theme=value;localStorage.setItem('ttgl-theme',value)}",theme)
                        if title:expect(page.locator('h1')).to_have_text(title)
                        records=page.locator(f'[data-table="{list_id}"]');expect(records).to_be_visible()
                        expect(records.locator('.column-picker').first).to_be_visible()
                        expect(records.locator('[data-search]').first).to_be_visible()
                        expect(records.locator('[data-toggle-filters]').first).to_be_visible()
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width,name)
                        # The photographed card chevrons must actually collapse the body.
                        card=page.locator('details.analysis-card,details.report-card').first
                        if card.count():
                            summary=card.locator(':scope>summary');summary.click(position={'x':8,'y':12});expect(card).not_to_have_attribute('open','')
                            summary.press('Enter');expect(card).to_have_attribute('open','')
                        if name=='impact':
                            inner=page.locator('.applied-change').first.locator('.table-container').last
                            self.assertLessEqual(inner.evaluate('(node)=>node.scrollWidth'),inner.evaluate('(node)=>node.clientWidth')+1)
                        if width==1440 and name in ('overall','costs','tools','outcomes'):
                            pair=page.locator('.analysis-pair,.chart-grid,.usage-pair,.dashboard-pair').first
                            if pair.count():self.assertGreater(len(pair.evaluate("node=>getComputedStyle(node).gridTemplateColumns.split(' ')")),1)
                        page.evaluate('document.activeElement?.blur();window.scrollTo(0,0)');page.mouse.move(0,0);page.screenshot(path=str(DEST/f'{name}-{theme}-{width}.png'),full_page=True,animations='disabled')
                        screens.append(dict(page=name,theme=theme,width=width,file=f'{name}-{theme}-{width}.png',list=list_id))
                # Scope/range segments from the photos submit and survive reload.
                page.set_viewport_size({'width':1440,'height':1000});page.goto(origin+'/costs?range=all')
                page.get_by_role('group',name='Date range',exact=True).get_by_role('button',name='7d',exact=True).click()
                expect(page.locator('[data-range="7d"]')).to_have_attribute('aria-pressed','true');self.assertIn('range=7d',page.url)
                page.reload();expect(page.locator('[data-range="7d"]')).to_have_attribute('aria-pressed','true')
                # Populated native turn list: real paging, search, filters and sorting.
                page.goto(origin+'/tasks?range=all');records=page.locator('[data-table="activity-turns"]')
                records.get_by_label('Rows per page activity-turns',exact=True).select_option('10');expect(records.locator('tbody tr')).to_have_count(10)
                records.get_by_role('button',name='Next',exact=True).click();expect(records.get_by_label('Page activity-turns',exact=True)).to_have_value('2')
                records.get_by_label('Search activity-turns',exact=True).fill('dashboard-case-00');expect(records.locator('tbody tr')).to_have_count(1)
                records.get_by_role('button',name='Reset table',exact=True).click()
                records.get_by_role('button',name='Sort by API estimate',exact=True).click();expect(records.locator('th[aria-sort="ascending"]')).to_contain_text('API estimate')
                records.get_by_role('button',name='Filters',exact=True).click()
                records.get_by_label('Filter activity-turns by API estimate',exact=True).fill('> 1')
                # Eight Opus turns and one Sonnet turn exceed this fixture rate threshold.
                expect(records.locator('tbody tr')).to_have_count(9)
                expect(records.get_by_label('Page activity-turns',exact=True)).to_have_value('1')
                for cell in records.locator('tbody tr td:nth-child(3)').all():self.assertGreater(float(cell.inner_text().split()[0]),1)
                page.reload();expect(records.get_by_label('Filter activity-turns by API estimate',exact=True)).to_have_value('> 1');expect(records.locator('tbody tr')).to_have_count(9)
                records.get_by_role('button',name='Reset table',exact=True).click()
                # Tool-family view and the photographed inline area-measure tabs.
                page.goto(origin+'/tools?range=all')
                page.locator('.tool-treemap button[aria-label="Shell · cat"]').click()
                expect(page.locator('[data-table="tool-targets"]')).to_contain_text('cat src/app.ts')
                page.get_by_role('group',name='Tool treemap measure',exact=True).get_by_role('button',name='Time',exact=True).click()
                expect(page.locator('[data-tool-measure="runtime"]')).to_have_attribute('aria-pressed','true')
                page.reload();expect(page.locator('[data-tool-measure="runtime"]')).to_have_attribute('aria-pressed','true')
                for width in (1440,390):
                    page.set_viewport_size({'width':width,'height':1000});page.evaluate('document.activeElement?.blur();window.scrollTo(0,0)')
                    expect(page.locator('html')).to_have_attribute('data-theme','dark')
                    page.screenshot(path=str(DEST/f'tool-detail-dark-{width}.png'),full_page=True,animations='disabled')
                    screens.append(dict(page='tool-detail',theme='dark',width=width,file=f'tool-detail-dark-{width}.png',list='tool-targets'))
                page.set_viewport_size({'width':1440,'height':1000});page.goto(origin+'/tasks/'+tasks[-1]+'?range=all')
                steps=page.locator('[data-table="task-report-steps"]');expect(steps).to_be_visible()
                image=page.locator('.report-screenshots img').first
                expect(image).to_be_visible();page.wait_for_function("() => document.querySelector('.report-screenshots img').naturalWidth===1")
                source=page.request.get(origin+image.get_attribute('src'));self.assertEqual(source.status,200)
                self.assertEqual(source.headers['content-type'],'image/png');self.assertEqual(source.headers['cross-origin-resource-policy'],'same-origin')
                page.get_by_role('button',name='Open retained screenshot 1',exact=True).click();expect(page.locator('dialog .report-image-full')).to_be_visible()
                page.get_by_role('button',name='Close',exact=True).click()
                page.locator('[data-report-phase]').first.click();expect(steps.locator('tbody tr')).to_have_count(2)
                page.get_by_role('button',name='All report steps',exact=True).click()
                expect(page.locator('html')).to_have_attribute('data-theme','dark')
                steps.scroll_into_view_if_needed();page.evaluate('document.activeElement?.blur()');page.screenshot(path=str(DEST/'steps-dark-1440.png'),animations='disabled')
                screens.append(dict(page='steps',theme='dark',width=1440,file='steps-dark-1440.png',list='task-report-steps'))
                # Other paginated lists use the same full-cohort query contract.
                page.goto(origin+'/?range=all#tasks');work=page.locator('[data-table="work-tasks"]')
                expect(work).to_be_visible()
                work.get_by_label('Search work-tasks',exact=True).fill('case-00');expect(work.locator('tbody tr')).to_have_count(1)
                expect(work.locator('tbody')).to_contain_text('Acceptance task case-00')
                work.get_by_role('button',name='Reset table',exact=True).click()
                page.goto(origin+'/tasks/'+tasks[-1]+'?range=all')
                page.locator('.step-panel>summary').click();sources=page.locator('[data-table="work-steps"]')
                expect(sources).to_be_visible();sources.get_by_label('Search work-steps',exact=True).fill('ImageView')
                expect(sources.locator('tbody tr')).to_have_count(1);expect(sources.locator('tbody')).to_contain_text('ImageView')
                import bulk_analysis
                bulk_analysis.start(f.store,launch=False)
                page.locator('#bulk-analysis').click();queue=page.locator('[data-table="bulk-analysis-items"]')
                expect(queue).to_be_visible();queue.get_by_label('Search bulk-analysis-items',exact=True).fill('case-00')
                expect(queue.locator('tbody tr')).to_have_count(1);expect(queue.locator('tbody')).to_contain_text('Acceptance task case-00')
                page.get_by_role('button',name='Close',exact=True).click()
                page.goto(origin+'/live?range=all')
                with f.store.connection() as c:c.execute('UPDATE live_sessions SET last_seen=?',(time.time()-90000,))
                page.reload();expect(page.locator('#content')).to_contain_text('No session reported in the last 24 hours')
                expect(page.locator('[data-table="steering-log"] tbody tr')).not_to_have_count(0)
                page.screenshot(path=str(DEST/'live-empty-dark-1440.png'),full_page=True,animations='disabled')
                screens.append(dict(page='live-empty',theme='dark',width=1440,file='live-empty-dark-1440.png',list='steering-log'))
                self.assertEqual(errors,[]);self.assertEqual(bad_responses,[])
            finally:browser.close()
        (DEST/'manifest.json').write_text(json.dumps(dict(source='User-supplied page photographs',fixture='Generated native records and deterministic interpreted groups; no inference',screens=screens,errors=errors,bad_responses=bad_responses),indent=2))
        (DEST/'index.html').write_text('<!doctype html><title>Reference acceptance evidence</title><h1>Observatory screenshot acceptance</h1><p>Populated fixtures, not user measurements. Inspect each capture against the supplied reference photos.</p>'+''.join(f'<p><a href="{html.escape(s["file"])}">{html.escape(s["page"])} · {s["theme"]} · {s["width"]}px</a></p>' for s in screens))


if __name__=='__main__':unittest.main()
