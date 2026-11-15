"""Cost/tool/task browser workflows use native fixtures and never model inference."""
import json
import os
from pathlib import Path
import unittest
import test_workspace_browser
import task_curation
import work_analytics


@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA')=='1','Opt-in browser QA')
class UsagePagesBrowserTests(unittest.TestCase):
    def fixture(self):
        host=test_workspace_browser.WorkspaceBrowserTests();f,origin,task=host.fixture();self.addCleanup(host.doCleanups)
        rows=[dict(timestamp='2026-11-05T00:00:02Z',type='event_msg',payload=dict(type='item_completed',thread_id='s',turn_id='t',item=dict(type='FileChange',id='edit',changes={'src/a.py':{'diff':'+fixed'}},status='completed'))),
              dict(timestamp='2026-11-05T00:00:03Z',type='event_msg',payload=dict(type='item_completed',thread_id='s',turn_id='t',item=dict(type='CommandExecution',id='check',command=['pytest','tests'],exit_code=1,aggregated_output='1 failed',duration={'secs':1,'nanos':0}))),
              dict(timestamp='2026-11-05T00:00:05Z',type='event_msg',payload=dict(type='item_completed',thread_id='s',turn_id='t',item=dict(type='AssistantMessage',id='answer',content=[dict(type='text',text='One test still fails; this is not complete.')])))]
        f.source.write_text(''.join(json.dumps(r)+'\n' for r in f.rows+rows));f.store.ingest(f.source)
        work_analytics.save_rates(f.store,dict(unit='USD',as_of='2026-11-05',models={'test-model':dict(input=1,cached=.1,output=2)}))
        task_curation.collect(f.store,task,['s:tool:edit'],'Implement the fix','implement')
        return f,origin,task

    def test_cost_and_tool_charts_filters_and_source_drilldown(self):
        from playwright.sync_api import sync_playwright,expect
        f,origin,task=self.fixture()
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000},timezone_id='Europe/Amsterdam');page.set_default_timeout(5000)
            errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(origin+'/costs?range=all')
            expect(page.locator('h1')).to_have_text('Cost & tokens')
            expect(page.locator('[data-table="cost-models"]')).to_contain_text('test-model')
            expect(page.locator('[data-table="cost-models"] tbody tr').first.locator('td').nth(1)).to_have_text('1')
            artifacts=Path('work/security/usage-pages-qa');artifacts.mkdir(parents=True,exist_ok=True)
            page.screenshot(path=str(artifacts/'costs-desktop-light.png'),full_page=True,animations='disabled')
            page.locator('[data-usage-day]').first.focus();page.keyboard.press('Enter')
            expect(page.locator('dialog')).to_contain_text('Fix')
            page.get_by_role('button',name='Source 1',exact=True).click();expect(page.locator('[data-usage-output]')).to_contain_text('source')
            page.get_by_role('button',name='Close',exact=True).click()
            page.locator('[data-cost-band="0"]').first.click();page.locator('dialog [data-usage-task]').click()
            expect(page.locator('.task-detail')).to_contain_text('Fix')
            page.locator('nav [data-view="tools"]').click()
            expect(page.locator('[data-table="usage-tools"]')).to_contain_text('Shell · rg')
            page.locator('.tool-treemap button[aria-label="Shell · rg"]').click()
            expect(page.locator('[data-table="tool-targets"]')).to_contain_text('rg foo')
            expect(page).to_have_url(__import__('re').compile('family=Shell'))
            page.reload();expect(page.locator('[data-table="tool-targets"]')).to_contain_text('rg foo')
            page.get_by_role('button',name='rg foo',exact=True).click()
            page.get_by_role('button',name='Source 1',exact=True).click();expect(page.locator('[data-usage-output]')).to_contain_text('CommandExecution')
            page.get_by_role('button',name='Close',exact=True).click()
            page.get_by_label('Treemap measure',exact=True).select_option('runtime')
            expect(page.get_by_label('Treemap measure',exact=True)).to_have_value('runtime')
            page.get_by_label('Tool cost attribution',exact=True).select_option('step_share')
            page.locator('[data-ops-filters]').get_by_role('button',name='Apply filters',exact=True).click()
            expect(page.locator('[data-table="usage-tools"]')).to_contain_text('Estimated tool share')
            page.get_by_label('Treemap measure',exact=True).select_option('context_cost')
            expect(page.locator('.tool-treemap')).to_have_count(0)
            expect(page.locator('#content')).to_contain_text('No values for this measure')
            page.get_by_role('button',name='All tools',exact=True).click()
            page.get_by_label('Treemap measure',exact=True).select_option('calls')
            for theme in ('light','dark'):
                page.locator('html').evaluate('(node,theme)=>node.dataset.theme=theme',theme)
                for width in (1440,768,390):
                    page.set_viewport_size({'width':width,'height':1000})
                    for view in ('costs','tools'):
                        page.locator(f'nav [data-view="{view}"]').click()
                        expect(page.locator(f'nav [data-view="{view}"]')).to_have_attribute('aria-current','page')
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
            artifacts=Path('work/security/usage-pages-qa');artifacts.mkdir(parents=True,exist_ok=True)
            page.screenshot(path=str(artifacts/'tools-mobile-dark.png'),full_page=True,animations='disabled')
            self.assertEqual(errors,[]);browser.close()

    def test_inline_task_story_phase_selection_and_full_source(self):
        from playwright.sync_api import sync_playwright,expect
        f,origin,task=self.fixture()
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000});page.set_default_timeout(5000)
            errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(origin+'/tasks/'+task+'?range=all')
            report=page.locator('[data-task-report]')
            expect(report.get_by_role('heading',name='Story',exact=True)).to_be_visible()
            expect(report).to_contain_text('Last recorded validation command failed')
            expect(report).to_contain_text('One test still fails; this is not complete.')
            expect(report).to_contain_text('task success remains unverified')
            expect(report.locator('[data-table="task-report-steps"] tbody tr')).to_have_count(4)
            self.assertEqual(report.locator('.report-step-row').nth(1).locator('.report-step-track i').evaluate('(node)=>node.style.left'),'0%')
            self.assertIn('50%',report.locator('.report-step-row').nth(1).locator('.report-step-track i').evaluate('(node)=>node.style.width'))
            page.get_by_role('button',name='Phase: Implement the fix',exact=True).click()
            expect(report.locator('[data-table="task-report-steps"] tbody tr')).to_have_count(1)
            expect(report.locator('[data-table="task-report-steps"]')).to_contain_text('FileChange')
            page.get_by_role('button',name='All report steps',exact=True).click()
            expect(report.locator('[data-table="task-report-steps"] tbody tr')).to_have_count(4)
            report.locator('[data-report-source="s:tool:check"]').first.click()
            expect(page.locator('dialog')).to_contain_text('1 failed')
            page.get_by_role('button',name='Close',exact=True).click()
            artifacts=Path('work/security/usage-pages-qa');artifacts.mkdir(parents=True,exist_ok=True)
            page.screenshot(path=str(artifacts/'task-report-desktop.png'),full_page=True,animations='disabled')
            for width in (1440,768,390):
                page.set_viewport_size({'width':width,'height':1000})
                self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
            self.assertEqual(errors,[]);browser.close()


if __name__=='__main__':unittest.main()
