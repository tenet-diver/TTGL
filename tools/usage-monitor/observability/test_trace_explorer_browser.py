"""Opt-in browser investigation using retained fixtures; no inference or installs."""
import os
import unittest

import test_workspace_browser as fixtures


@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA') == '1', 'Opt-in browser QA')
class TraceExplorerBrowserTests(unittest.TestCase):
    def test_filter_turn_steps_raw_navigation_and_url_reload(self):
        from playwright.sync_api import sync_playwright, expect
        host = fixtures.WorkspaceBrowserTests()
        fixture, origin, task = host.fixture()
        self.addCleanup(host.doCleanups)
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ['TTGL_CHROMIUM'], args=['--no-sandbox'])
            try:
                page = browser.new_page(viewport={'width':1440, 'height':1000})
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(origin+'/investigate')
                expect(page.locator('.trace-results')).to_contain_text('Fix')
                expect(page.locator('.trace-results')).to_contain_text('110')
                page.get_by_label('Search prompts, tasks or operation labels',exact=True).fill('Resolve failure')
                page.get_by_role('button',name='Apply',exact=True).click()
                expect(page.locator('.trace-results')).to_contain_text('Fix')
                page.get_by_role('button',name='Inspect steps',exact=True).click()
                expect(page.locator('.trace-results .trace-result')).to_have_count(2)
                page.reload()
                expect(page.locator('.trace-results .trace-result')).to_have_count(2)
                page.locator('.trace-result').filter(has_text='shell').get_by_role('button',name='Read original evidence').click()
                expect(page.locator('dialog')).to_contain_text('CommandExecution')
                expect(page.locator('dialog')).to_contain_text('aggregated_output')
                page.get_by_role('button',name='Close',exact=True).click()
                page.get_by_role('button',name='Tools',exact=True).click()
                page.get_by_role('button',name='Find turns',exact=True).click()
                expect(page.locator('.trace-results')).to_contain_text('Fix')
                for width in (1440,768,390):
                    page.set_viewport_size({'width':width,'height':1000})
                    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
                self.assertEqual(errors,[])
            finally:
                browser.close()


if __name__ == '__main__':
    unittest.main()
