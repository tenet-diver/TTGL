"""Overall/task activity workflows and Impact uptake labels with native fixtures."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import test_usage_views_browser
import test_workspace_browser
import optimization


@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA')=='1','Opt-in browser QA')
class DashboardBrowserTests(unittest.TestCase):
    def test_overview_navigation_turn_sources_column_preferences_and_responsive_layout(self):
        from playwright.sync_api import sync_playwright,expect
        host=test_usage_views_browser.UsagePagesBrowserTests();f,origin,task=host.fixture();self.addCleanup(host.doCleanups)
        with f.store.connection() as c:c.execute("INSERT INTO turns VALUES('s','unassigned','/repo','Second request','2026-11-05T00:00:06Z','2026-11-05T00:00:07Z',1)")
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000});page.set_default_timeout(5000)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(origin+'/?range=all')
            expect(page.locator('h1')).to_have_text('Overall activity')
            expect(page.locator('[data-table="dashboard-tools"]')).to_contain_text('Shell · rg')
            expect(page.locator('#content')).to_contain_text('0 confirmed task interventions')
            page.locator('[data-usage-day]').first.focus();page.keyboard.press('Enter')
            expect(page.locator('dialog [data-table="dashboard-day-turns"]')).to_contain_text('Fix the problem')
            page.locator('dialog [data-dash-turn]').click()
            page.get_by_role('button',name='Source 1',exact=True).click()
            expect(page.locator('[data-dash-output]')).to_contain_text('source')
            page.get_by_role('button',name='Open defined task',exact=True).click()
            expect(page.locator('.task-detail')).to_contain_text('Fix')
            page.locator('nav [data-view="overview"]').click()
            page.get_by_role('button',name='search',exact=True).click()
            expect(page.locator('dialog [data-table="dashboard-category-tools"]')).to_contain_text('Shell · rg')
            page.locator('dialog').get_by_role('button',name='Shell · rg',exact=True).click()
            expect(page.locator('[data-table="tool-targets"]')).to_contain_text('rg foo')
            page.locator('nav [data-view="taskactivity"]').click()
            expect(page.locator('h1')).to_have_text('Task activity')
            expect(page.locator('[data-table="activity-turns"] tbody tr')).to_have_count(2)
            expect(page.locator('[data-table="marked-tasks"] tbody tr')).to_have_count(1)
            picker=page.locator('[data-table="activity-turns"] .column-picker')
            picker.locator('summary').click()
            expect(picker.get_by_role('checkbox')).to_have_count(19)
            picker.get_by_role('checkbox',name='Show activity-turns column Workspace',exact=True).check()
            page.reload()
            expect(page.locator('[data-table="activity-turns"] thead')).to_contain_text('Workspace')
            page.get_by_role('textbox',name='Search activity-turns',exact=True).fill('Second request')
            expect(page.locator('[data-table="activity-turns"] tbody tr')).to_have_count(1)
            page.locator('[data-table="activity-turns"] [data-dash-turn]').click()
            expect(page.locator('dialog')).to_contain_text('Unassigned turn')
            page.get_by_role('button',name='Close',exact=True).click()
            page.locator('[data-table="activity-turns"]').get_by_role('button',name='Reset table',exact=True).click()
            page.locator('[data-ops-filters]').get_by_label('Workspace',exact=True).select_option('/repo')
            page.locator('[data-ops-filters]').get_by_role('button',name='Apply filters',exact=True).click()
            page.reload();expect(page.locator('[data-ops-filters]').get_by_label('Workspace',exact=True)).to_have_value('/repo')
            artifacts=Path('work/security/dashboard-pages-qa');artifacts.mkdir(parents=True,exist_ok=True)
            for theme in ('light','dark'):
                page.locator('html').evaluate('(node,theme)=>node.dataset.theme=theme',theme)
                for width in (1440,768,390):
                    page.set_viewport_size({'width':width,'height':1000})
                    for view in ('overview','taskactivity'):
                        page.locator(f'nav [data-view="{view}"]').click()
                        expect(page.locator(f'nav [data-view="{view}"]')).to_have_attribute('aria-current','page')
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
                        if view=='overview' and width==1440:page.screenshot(path=str(artifacts/f'overview-{theme}.png'),full_page=True,animations='disabled')
                    if width==1440:page.screenshot(path=str(artifacts/f'task-activity-{theme}.png'),full_page=True,animations='disabled')
            self.assertEqual(errors,[]);browser.close()

    def test_explicit_analysis_limits_and_impact_uptake_sample_units(self):
        from playwright.sync_api import sync_playwright,expect
        host=test_workspace_browser.WorkspaceBrowserTests();f,origin,task=host.fixture();self.addCleanup(host.doCleanups)
        optimization.change(f.store,dict(title='Large context rule',at='2026-11-05T12:00:00Z',metrics=['cost_per_task','context','context_warnings']))
        with patch('task_history.start',return_value={'id':'fixture','status':'queued'}) as start,sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page();page.set_default_timeout(5000)
            page.goto(origin+'/tasks?range=all')
            start.assert_not_called()
            page.get_by_role('button',name='Review remaining tasks',exact=True).click()
            page.get_by_role('button',name='Analyze selected tasks',exact=True).click()
            expect(page.locator('[data-dash-analysis-result]')).to_contain_text('Select one or two tasks')
            page.locator('dialog input[name="task_id"]').check()
            page.get_by_role('button',name='Analyze selected tasks',exact=True).click()
            expect(page.locator('[data-dash-analysis-result]')).to_contain_text('Fix: queued')
            start.assert_called_once_with(f.store,task,'overview')
            page.get_by_role('button',name='Close',exact=True).click()
            page.locator('nav [data-view="impact"]').click()
            expect(page.locator('.impact-uptake-row')).to_have_text('In use')
            expect(page.locator('.applied-change')).to_contain_text('matched tasks')
            expect(page.locator('.applied-change')).to_contain_text('API responses')
            expect(page.locator('.applied-change')).to_contain_text('observed hours')
            browser.close()


if __name__=='__main__':unittest.main()
