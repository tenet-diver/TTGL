"""Evidence-dialog browser QA against the native UI and temporary evidence."""
import os
from pathlib import Path
import threading
import unittest
from http.server import ThreadingHTTPServer
import test_task_evidence as fixtures
from workspace import Handler


@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA') == '1', 'Opt-in browser QA')
class TaskStoryBrowserTests(unittest.TestCase):
    def test_story_source_drilldown_and_mobile_dark_layout(self):
        from playwright.sync_api import sync_playwright, expect
        fixture = fixtures.EvidenceTests()
        fixture.setUp()
        self.addCleanup(fixture.fixture.directory.cleanup)
        fixture.test_native_change_validation_and_image_sources()
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.store = fixture.store
        origin = f'http://127.0.0.1:{server.server_port}'
        server.allowed_hosts = {f'127.0.0.1:{server.server_port}'}
        server.allowed_origins = {origin}
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM', '/usr/bin/chromium'), args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.route('**/story-fixture', lambda route: route.fulfill(content_type='text/html', body='''<!doctype html><html data-theme="light"><head><link rel="stylesheet" href="/ui.css"><link rel="stylesheet" href="/workspace.css"><link rel="stylesheet" href="/work-explorer.css"></head><body><dialog id="modal" open><div class="modal-body" id="modal-content"></div></dialog></body></html>'''))
            page.goto(origin + '/story-fixture')
            page.evaluate('''async task => {
                const {openTaskEvidence} = await import('/activity-insights.js');
                await openTaskEvidence(task, (title, body) => {
                    document.querySelector('#modal-content').innerHTML = body;
                }, () => { throw Error('Mutation outside isolated QA'); }, message => { throw Error(message); });
            }''', fixture.task)
            expect(page.get_by_role('heading', name='Task story', exact=True)).to_be_visible()
            expect(page.get_by_role('heading', name='What remains open', exact=True)).to_be_visible()
            expect(page.locator('.evidence-summary')).to_contain_text('src/page.tsx')
            expect(page.locator('.evidence-summary')).to_contain_text('command_passed')
            expect(page.locator('.evidence-summary')).to_contain_text('Task acceptance has not been recorded')
            page.get_by_role('button', name='Inspect original step').first.click()
            expect(page.locator('[data-proof-output]')).to_contain_text('+button')
            for theme in ('light', 'dark'):
                page.locator('html').evaluate('(node, theme) => node.dataset.theme = theme', theme)
                for width in (1440, 768, 390):
                    page.set_viewport_size({'width': width, 'height': 1000})
                    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)
                    self.assertLessEqual(page.locator('dialog').bounding_box()['width'], width)
            self.assertEqual(errors, [])
            browser.close()


if __name__ == '__main__':
    unittest.main()
