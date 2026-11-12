"""Opt-in task explorer workflows with retained native fixtures; no model calls."""
import json
import os
from pathlib import Path
import threading
import unittest
from http.server import ThreadingHTTPServer
import test_workspace
from workspace import Handler

@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA')=='1','Opt-in browser QA')
class WorkspaceBrowserTests(unittest.TestCase):
    def fixture(self):
        f=test_workspace.WorkspaceTests();f.setUp();self.addCleanup(f.directory.cleanup);f.store.scan()
        project,task=f.define_task();f.store.mutate('assign',dict(session_id='s',turn_id='t',task_id=task))
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.store=f.store
        origin=f'http://127.0.0.1:{server.server_port}';server.allowed_hosts={f'127.0.0.1:{server.server_port}'};server.allowed_origins={origin}
        threading.Thread(target=server.serve_forever,daemon=True).start();self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        return f,origin,task

    def test_hierarchy_analytics_knowledge_settings_and_responsive_layout(self):
        from playwright.sync_api import sync_playwright,expect
        f,origin,task=self.fixture();artifacts=Path('work/security/ui-review-20261112/screenshots');artifacts.mkdir(parents=True,exist_ok=True)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ['TTGL_CHROMIUM'],args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(origin);expect(page.locator('[data-table="work-tasks"] tbody tr')).to_have_count(1)
            self.assertEqual(page.locator('nav [data-view]').count(),4)
            page.screenshot(path=str(artifacts/'work-explorer-desktop.png'),full_page=True)
            page.locator('[data-table="work-tasks"] [data-work-task]').first.click();expect(page.locator('[data-table="work-subtasks"] [data-subtask]')).to_have_count(1)
            expect(page.locator('[data-work-timeline] .timeline-bar')).to_have_count(1)
            page.locator('[data-table="work-subtasks"] [data-subtask]').click();expect(page.locator('[data-table="work-subtasks"] [data-subtask]')).to_have_attribute('aria-pressed','true')
            expect(page.locator('[data-work-timeline] [data-step-select]')).to_have_count(1)
            page.locator('[data-work-timeline] [data-inspect-step]').click();expect(page.locator('[data-timeline-evidence]')).to_contain_text('aggregated_output')
            page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(artifacts/'work-hierarchy-desktop.png'),full_page=True)
            for width in (1440,768,390):
                page.set_viewport_size({'width':width,'height':1000})
                for view in ['tasks','analytics','knowledge','settings']:
                    page.locator(f'nav [data-view="{view}"]').click();expect(page.locator(f'nav [data-view="{view}"]')).to_have_attribute('aria-current','page')
                    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width,f'{view} at {width}')
            page.locator('nav [data-view="analytics"]').click();expect(page.locator('.bar-chart')).to_have_count(2)
            page.get_by_label('Measure',exact=True).select_option('tokens');expect(page.locator('.bar-chart').last).to_contain_text('110')
            page.get_by_label('Subtask attribution',exact=True).select_option('step_share');expect(page.locator('.bar-chart').last).to_contain_text('110')
            page.screenshot(path=str(artifacts/'work-analytics-mobile.png'),full_page=True)
            page.locator('nav [data-view="knowledge"]').click();page.get_by_label('Graphiti explorer URL').fill('https://example.org/graph')
            page.locator('[data-explorer-link="graphiti"]').get_by_role('button',name='Save link').click()
            expect(page.locator('[data-explorer-link="graphiti"] a')).to_have_attribute('href','https://example.org/graph')
            page.reload();expect(page.get_by_label('Graphiti explorer URL')).to_have_value('https://example.org/graph')
            page.locator('nav [data-view="settings"]').click();expect(page.locator('.rate-editor')).to_contain_text('')
            page.locator('.rate-editor').fill(json.dumps(dict(unit='USD',as_of='2026-11-12',models={})))
            page.get_by_role('button',name='Save rate scenario').click();expect(page.locator('#toast')).to_contain_text('saved')
            page.get_by_role('button',name='Projects',exact=True).click();page.get_by_role('button',name='Add project',exact=True).click()
            page.get_by_role('textbox',name='Project name',exact=True).fill('Browser project');page.get_by_role('textbox',name='Repository / working folder').fill('/browser-fixture')
            page.locator('dialog').get_by_role('button',name='Add project',exact=True).click();expect(page.locator('tbody')).to_contain_text('Browser project')
            self.assertEqual(errors,[]);browser.close()

    def test_saved_theme_column_visibility_sort_and_filters(self):
        from playwright.sync_api import sync_playwright,expect
        f,origin,task=self.fixture()
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ['TTGL_CHROMIUM'],args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000});page.goto(origin)
            page.get_by_role('button',name='Switch to dark theme').click();expect(page.locator('html')).to_have_attribute('data-theme','dark')
            expect(page.locator('[data-table="work-tasks"]')).to_be_visible()
            page.get_by_role('button',name='Sort by Tokens',exact=True).click();expect(page.locator('th[aria-sort="ascending"]')).to_contain_text('Tokens')
            page.get_by_role('searchbox',name='Filter work-tasks by Tokens',exact=True).fill('>= 1000');expect(page.locator('tbody')).to_contain_text('No matching rows')
            page.get_by_role('searchbox',name='Filter work-tasks by Tokens',exact=True).fill('>= 100');expect(page.locator('tbody')).to_contain_text('Fix')
            page.locator('.column-picker summary').click();page.get_by_role('checkbox',name='Show work-tasks column Type',exact=True).uncheck()
            expect(page.locator('thead tr').first).not_to_contain_text('Type')
            page.reload();expect(page.locator('html')).to_have_attribute('data-theme','dark')
            expect(page.locator('[data-table="work-tasks"]')).to_be_visible();expect(page.locator('thead tr').first).not_to_contain_text('Type')
            expect(page.get_by_role('searchbox',name='Filter work-tasks by Tokens',exact=True)).to_have_value('>= 100')
            expect(page.locator('th[aria-sort="ascending"]')).to_contain_text('Tokens')
            page.screenshot(path='work/security/ui-review-20261112/screenshots/work-table-dark.png',full_page=True)
            page.get_by_role('button',name='Reset table',exact=True).click();expect(page.locator('thead tr').first).to_contain_text('Type')
            page.locator('[data-table="work-tasks"] [data-work-task]').first.click();expect(page.locator('[data-table="work-subtasks"]')).to_be_visible()
            page.get_by_role('button',name='Sort by Subtask / recorded turn',exact=True).click()
            page.locator('[data-table="work-subtasks"] [data-subtask]').first.click();expect(page.locator('[data-table="work-subtasks"] [data-subtask]')).to_have_attribute('aria-pressed','true')
            browser.close()

if __name__=='__main__':unittest.main()
