"""Real native-page workflows against temporary local evidence, no model calls."""
import os
from pathlib import Path
import unittest
import test_workspace_browser as fixtures
import steering


@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA')=='1','Opt-in browser QA')
class OptimizationBrowserTests(unittest.TestCase):
    def test_rules_live_notes_impact_outcomes_and_suggestions(self):
        from playwright.sync_api import sync_playwright,expect
        host=fixtures.WorkspaceBrowserTests();fixture,origin,task=host.fixture();self.addCleanup(host.doCleanups)
        steering.receive(fixture.store,dict(session_id='browser-live',event_id='start',event='start',workspace='/repo',cost_usd=0))
        dest=Path('/workspace/TTGL/work/security/optimization-qa');dest.mkdir(parents=True,exist_ok=True)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1100});page.set_default_timeout(5000);errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(origin+'/live/rules?range=all')
            expect(page.get_by_role('heading',name='Steering rules',exact=True).first).to_be_visible()
            expect(page.locator('[data-table="steering-rules"] tbody tr')).to_have_count(11)
            page.get_by_role('button',name='Add rule',exact=True).click()
            page.get_by_label('Rule name',exact=True).fill('Browser safety rule')
            page.get_by_label('Mode',exact=True).select_option('block')
            page.get_by_label('Message',exact=True).fill('Inspect this operation before continuing.')
            page.get_by_label('Command pattern',exact=True).fill('deploy production')
            page.get_by_role('button',name='Save rule',exact=True).click()
            expect(page.locator('dialog')).not_to_be_visible()
            page.get_by_role('textbox',name='Search steering-rules',exact=True).fill('Browser safety rule')
            expect(page.locator('[data-table="steering-rules"] tbody tr')).to_have_count(1)
            page.get_by_role('combobox',name='Mode for Browser safety rule',exact=True).select_option('ask')
            expect(page.get_by_role('combobox',name='Mode for Browser safety rule',exact=True)).to_have_value('ask')
            result=steering.receive(fixture.store,dict(session_id='browser-live',event_id='deploy',event='pre_tool',workspace='/repo',tool='Bash',command='deploy production'))
            self.assertEqual(result['decision'],'ask')
            page.locator('nav [data-view="live"]').click()
            expect(page.locator('[data-table="live-sessions"]')).to_contain_text('browser-live')
            page.get_by_role('button',name='Send note',exact=True).click()
            page.get_by_label('Note',exact=True).fill('Check the responsive layout')
            page.get_by_role('button',name='Queue note',exact=True).click();expect(page.locator('dialog')).not_to_be_visible()
            note=steering.receive(fixture.store,dict(session_id='browser-live',event_id='prompt',event='prompt',workspace='/repo'))
            self.assertIn('Check the responsive layout',note['messages'])
            page.get_by_role('button',name='Pause',exact=True).click();expect(page.get_by_role('button',name='Resume',exact=True)).to_be_visible()
            page.get_by_role('button',name='Resume',exact=True).click();expect(page.get_by_role('button',name='Pause',exact=True)).to_be_visible()
            page.locator('nav [data-view="impact"]').click()
            page.get_by_role('button',name='Record a change',exact=True).click()
            page.get_by_label('Change title',exact=True).fill('Browser context limit')
            page.get_by_label('Applied at',exact=True).fill('2026-11-05T12:00')
            page.get_by_label('Takes effect',exact=True).select_option('new_sessions')
            page.get_by_label('Average context',exact=True).check()
            page.locator('dialog').get_by_role('button',name='Record change',exact=True).click()
            expect(page.locator('.applied-change')).to_contain_text('Browser context limit')
            expect(page.locator('.applied-change')).to_contain_text('New sessions only')
            expect(page.locator('.impact-grid .ops-chart')).to_have_count(17)
            page.get_by_role('button',name='Switch to dark theme',exact=True).click()
            page.screenshot(path=str(dest/'impact-dark-desktop.png'),full_page=True,animations='disabled')
            for width in (1440,768,390):
                page.set_viewport_size({'width':width,'height':1000})
                for view in ('steering','live','impact','outcomes','suggestions'):
                    page.locator(f'nav [data-view="{view}"]').click()
                    expect(page.locator(f'nav [data-view="{view}"]')).to_have_attribute('aria-current','page')
                    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width,view)
            expect(page.locator('[data-table="built-in-findings"]')).to_contain_text('Large tool results')
            page.get_by_role('button',name='Show evidence',exact=True).first.click()
            page.locator('dialog').get_by_role('button',name='Source 1',exact=True).click()
            expect(page.locator('[data-ops-output]')).to_contain_text('source')
            page.screenshot(path=str(dest/'suggestions-evidence-mobile.png'),full_page=True,animations='disabled')
            page.get_by_role('button',name='Close',exact=True).click()
            page.locator('nav [data-view="impact"]').click();page.screenshot(path=str(dest/'impact-dark-mobile.png'),full_page=True,animations='disabled')
            page.locator('.applied-change').get_by_role('button',name='Delete',exact=True).click()
            page.get_by_role('button',name='Delete change',exact=True).click();expect(page.locator('.applied-change')).to_have_count(0)
            page.reload();expect(page.locator('.applied-change')).to_have_count(0)
            self.assertEqual(errors,[])
            browser.close()


if __name__=='__main__':unittest.main()
