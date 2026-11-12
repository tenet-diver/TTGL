"""Opt-in workflow/layout QA, using a temporary store and no model calls."""
import os
from pathlib import Path
import threading
import unittest
from http.server import ThreadingHTTPServer

import test_workspace
from workspace import Handler


@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA') == '1', 'Opt-in browser QA')
class WorkspaceBrowserTests(unittest.TestCase):
    def test_navigation_controls_and_responsive_layout(self):
        from playwright.sync_api import sync_playwright, expect

        fixture = test_workspace.WorkspaceTests()
        fixture.setUp()
        self.addCleanup(fixture.directory.cleanup)
        fixture.store.scan()
        project, task = fixture.define_task()
        fixture.store.mutate('assign', dict(session_id='s', turn_id='t', task_id=task))
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.store = fixture.store
        origin = f'http://127.0.0.1:{server.server_port}'
        server.allowed_hosts = {f'127.0.0.1:{server.server_port}'}
        server.allowed_origins = {origin}
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        artifacts = Path('work/security/ui-review-20261112/screenshots')
        artifacts.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM', '/usr/bin/chromium'), args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1440, 'height': 1100})
            errors, bad_responses = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('response', lambda response: bad_responses.append(response.url) if response.status >= 400 else None)
            page.goto(origin)
            expect(page.locator('#content')).to_have_attribute('aria-busy', 'false')
            page.evaluate('document.fonts.ready')
            self.assertTrue(page.evaluate('document.fonts.check("400 14px Geist")'))
            self.assertTrue(page.evaluate("document.fonts.check('400 12px \"JetBrains Mono\"')"))
            page.screenshot(path=str(artifacts / 'overview-desktop.png'), full_page=True, animations='disabled')

            views = page.locator('nav [data-view]').evaluate_all('(nodes) => nodes.map(n => n.dataset.view)')
            for width in (1440, 768, 390):
                page.set_viewport_size({'width': width, 'height': 1000})
                for view in views:
                    page.locator(f'nav [data-view="{view}"]').click()
                    expect(page.locator(f'nav [data-view="{view}"]')).to_have_attribute('aria-current', 'page')
                    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width, f'{view} overflows at {width}')

            page.set_viewport_size({'width': 1440, 'height': 1100})
            page.locator('nav [data-view="projects"]').click()
            page.get_by_role('button', name='Add project', exact=True).click()
            page.get_by_role('textbox', name='Project name', exact=True).fill('Browser project')
            page.get_by_role('textbox', name='Repository / working folder').fill('/browser-fixture')
            page.locator('dialog').get_by_role('button', name='Add project', exact=True).click()
            expect(page.locator('dialog')).not_to_be_visible()
            expect(page.locator('tbody')).to_contain_text('Browser project')
            page.get_by_role('textbox', name='Search projects').fill('no-results')
            expect(page.locator('tbody')).to_contain_text('No matching rows')
            page.locator('tbody').get_by_role('button', name='Clear search', exact=True).click()
            expect(page.locator('tbody')).to_contain_text('Browser project')

            page.locator('nav [data-view="tasks"]').click()
            page.get_by_role('button', name='Actions for Fix', exact=True).press('ArrowDown')
            menu = page.get_by_role('menu')
            expect(menu).to_be_visible()
            page.keyboard.press('End')
            page.keyboard.press('ArrowUp')
            page.keyboard.press('Escape')
            expect(menu).not_to_be_visible()
            expect(page.get_by_role('button', name='Actions for Fix', exact=True)).to_be_focused()
            page.get_by_role('button', name='Actions for Fix', exact=True).click()
            page.get_by_role('menuitem', name='Goal and verification', exact=True).click()
            expect(page.locator('dialog')).to_be_visible()
            page.set_viewport_size({'width': 390, 'height': 844})
            self.assertLessEqual(page.locator('dialog').bounding_box()['width'], 390)
            page.screenshot(path=str(artifacts / 'task-mobile.png'), animations='disabled')
            page.keyboard.press('Escape')

            page.set_viewport_size({'width': 1440, 'height': 1100})
            page.get_by_role('button', name='Switch to dark theme', exact=True).click()
            page.reload()
            expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
            page.get_by_role('button', name='Switch to light theme', exact=True).click()
            page.locator('nav [data-view="history"]').click()
            page.wait_for_selector('#history-results article')
            page.screenshot(path=str(artifacts / 'history-desktop.png'), full_page=True, animations='disabled')

            # Failure/recovery is an HTTP fixture; it never invokes a model.
            page.route('**/api/workspace?*', lambda route: route.fulfill(status=503, body='{}'))
            page.reload()
            expect(page.get_by_text('Evidence is unavailable', exact=True)).to_be_visible()
            page.unroute('**/api/workspace?*')
            page.get_by_role('button', name='Try again', exact=True).click()
            page.wait_for_selector('#history-results article')
            self.assertEqual(errors, [])
            self.assertEqual(len(bad_responses), 1, bad_responses)  # Intentional 503 above.
            browser.close()


if __name__ == '__main__':
    unittest.main()
