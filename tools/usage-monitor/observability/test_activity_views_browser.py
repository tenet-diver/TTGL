"""Native analysis pages against retained fixtures; no live model invocation."""
import json
import os
import time
from pathlib import Path
import unittest
from unittest.mock import patch
import test_workspace_browser as fixtures
import task_curation
import task_evidence


@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA')=='1','Opt-in browser QA')
class ActivityPagesBrowserTests(unittest.TestCase):
    def fixture(self):
        host=fixtures.WorkspaceBrowserTests();fixture,origin,task=host.fixture();self.addCleanup(host.doCleanups)
        fixture.rows[0]['payload']['source']='cli'
        records=[dict(timestamp='2026-11-05T00:00:02Z',type='event_msg',payload=dict(type='item_completed',thread_id='s',turn_id='t',item=dict(type='FileChange',id='edit',changes={'src/a.py':{'diff':'+x'}},status='completed'))),dict(timestamp='2026-11-05T00:00:03Z',type='event_msg',payload=dict(type='item_completed',thread_id='s',turn_id='t',item=dict(type='CommandExecution',id='again',command=['rg','again'],aggregated_output='Related source',exit_code=0)))]
        fixture.source.write_text(''.join(json.dumps(r)+'\n' for r in fixture.rows+records));fixture.store.ingest(fixture.source)
        return fixture,origin,task

    def test_process_agent_timeline_and_fix_rate_drilldowns(self):
        from playwright.sync_api import sync_playwright,expect
        fixture,origin,task=self.fixture()
        for ident,kind in [('tool','investigate'),('edit','implement'),('again','investigate')]:
            task_curation.collect(fixture.store,task,['s:tool:'+ident],ident,kind)
        task_evidence.add(fixture.store,task,'intervention','Acceptance test corrected','Explicit browser fixture',outcome='confirmed')
        import task_history
        body,digest=task_history.snapshot(fixture.store,task,'all')
        with fixture.store.connection() as c:c.execute('INSERT INTO task_history_jobs(id,task_id,snapshot_hash,snapshot,status,created,model,operation) VALUES(?,?,?,?,?,?,?,?)',('pending-refresh',task,digest,json.dumps(body),'queued',time.time(),'explicit-fixture','overview'))
        artifacts=Path(__file__).resolve().parents[3]/'work/security/activity-pages-qa';artifacts.mkdir(parents=True,exist_ok=True)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1100},timezone_id='Europe/Amsterdam');page.set_default_timeout(5000)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(origin+'/process?range=all')
            expect(page.locator('[data-table="process-paths"]')).to_contain_text('Investigate')
            expect(page.locator('.process-flow [data-flow-node]')).to_have_count(4)
            expect(page.locator('[data-table="process-categories"] tbody tr').first.locator('td').nth(2)).to_have_text('1')
            page.locator('[data-flow-node="Start"]').click()
            expect(page.locator('dialog [data-table="analysis-drill-tasks"]')).to_contain_text('Fix')
            page.get_by_role('button',name='Close',exact=True).click()
            page.locator('[data-flow-node="investigate"]').click()
            expect(page.locator('dialog [data-table="analysis-drill-tasks"]')).to_contain_text('Fix')
            page.get_by_role('button',name='Close',exact=True).click()
            page.locator('[data-flow-node="implement"]').focus();page.keyboard.press('Enter')
            expect(page.locator('dialog')).to_contain_text('Fix');page.get_by_role('button',name='Close',exact=True).click()
            page.get_by_label('Connections',exact=True).focus();page.keyboard.press('Home')
            expect(page.locator('[data-flow-edges] path')).to_have_count(1)
            page.reload();expect(page.get_by_label('Connections',exact=True)).to_have_value('1')
            filters=page.locator('[data-ops-filters]')
            filters.get_by_label('Subtask usage attribution',exact=True).select_option('step_share')
            filters.get_by_role('button',name='Apply filters',exact=True).click()
            expect(filters.get_by_label('Subtask usage attribution',exact=True)).to_have_value('step_share')
            page.screenshot(path=str(artifacts/'process-light-desktop.png'),full_page=True,animations='disabled')
            page.locator('[data-table="process-paths"] [data-path-tasks]').click()
            page.locator('dialog [data-analysis-task]').click()
            expect(page.locator('.task-detail')).to_contain_text('Fix')
            page.locator('nav [data-view="agents"]').click()
            expect(page.locator('[data-table="agent-comparison"]')).to_contain_text('main')
            expect(page.locator('[data-table="agent-comparison"]')).to_contain_text('110')
            expect(page.locator('[data-table="agent-comparison"] tbody tr').first.locator('td').nth(3)).to_have_text('1')
            expect(page.locator('[data-table="agent-comparison"] tbody tr').first.locator('td').nth(4)).to_have_text('3')
            page.locator('[data-agent-detail="main"]').click()
            page.locator('dialog').get_by_role('button',name='Source 1',exact=True).click()
            expect(page.locator('[data-analysis-output]')).to_contain_text('source')
            page.get_by_role('button',name='Close',exact=True).click()
            page.locator('nav [data-view="timeline"]').click()
            expect(page.locator('.heat-cell')).to_have_count(168)
            expect(page.locator('[data-turn-detail]')).to_have_count(2)
            page.get_by_label('Heatmap measure',exact=True).select_option('tokens')
            page.locator('.heat-cell:not(:disabled)').click()
            expect(page.locator('dialog')).to_contain_text('Europe/Amsterdam')
            page.get_by_role('button',name='Close',exact=True).click()
            page.reload();expect(page.get_by_label('Heatmap measure',exact=True)).to_have_value('tokens')
            filters=page.locator('[data-ops-filters]');filters.get_by_label('Display timezone',exact=True).select_option('UTC')
            filters.get_by_role('button',name='Apply filters',exact=True).click()
            expect(filters.get_by_label('Display timezone',exact=True)).to_have_value('UTC')
            page.locator('.turn-block').first.click();expect(page.locator('dialog')).to_contain_text('Open task')
            page.get_by_role('button',name='Close',exact=True).click()
            page.locator('nav [data-view="outcomes"]').click()
            expect(page.locator('[data-table="fix-workspaces"]')).to_contain_text('100%')
            expect(page.locator('[data-table="fix-categories"]')).to_contain_text('Investigate')
            page.get_by_role('button',name='Inspect signals',exact=True).click()
            expect(page.locator('dialog')).to_contain_text('Acceptance test corrected')
            page.get_by_role('button',name='Close',exact=True).click()
            page.get_by_role('button',name='Switch to dark theme',exact=True).click()
            for width in (1440,768,390):
                page.set_viewport_size({'width':width,'height':1000})
                for view in ('process','agents','timeline','outcomes'):
                    page.locator(f'nav [data-view="{view}"]').click()
                    expect(page.locator(f'nav [data-view="{view}"]')).to_have_attribute('aria-current','page')
                    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width,view)
            page.screenshot(path=str(artifacts/'outcomes-dark-mobile.png'),full_page=True,animations='disabled')
            self.assertEqual(errors,[]);browser.close()

    def test_explicit_selected_analysis_reuses_existing_job_api(self):
        from playwright.sync_api import sync_playwright,expect
        fixture,origin,task=self.fixture()
        with patch('task_history.start',return_value={'id':'fixture-job','status':'queued'}) as start,sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page();page.goto(origin+'/process?range=all')
            page.get_by_role('button',name='Review remaining tasks',exact=True).click()
            page.locator('dialog').get_by_role('checkbox',name='Fix',exact=True).check()
            page.get_by_role('button',name='Analyze selected tasks',exact=True).click()
            expect(page.locator('[data-analysis-result]')).to_contain_text('queued')
            start.assert_called_once_with(fixture.store,task,'overview')
            browser.close()


if __name__=='__main__':unittest.main()
