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
    def workspace_fixture(self):
        fixture = test_workspace.WorkspaceTests()
        fixture.setUp()
        self.addCleanup(fixture.directory.cleanup)
        fixture.store.scan()
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.store = fixture.store
        origin = f'http://127.0.0.1:{server.server_port}'
        server.allowed_hosts = {f'127.0.0.1:{server.server_port}'}
        server.allowed_origins = {origin}
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return fixture, origin

    def test_navigation_controls_and_responsive_layout(self):
        from playwright.sync_api import sync_playwright, expect

        fixture, origin = self.workspace_fixture()
        project, task = fixture.define_task()
        fixture.store.mutate('assign', dict(session_id='s', turn_id='t', task_id=task))
        artifacts = Path('work/security/ui-review-20261112/screenshots')
        artifacts.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM', '/usr/bin/chromium'), args=['--no-sandbox'])
            context = browser.new_context(viewport={'width': 1440, 'height': 1100})
            page = context.new_page()
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
            page.locator('tbody').get_by_role('button', name='Clear search and filters', exact=True).click()
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


    def test_column_controls_pagination_and_local_preferences(self):
        from playwright.sync_api import sync_playwright, expect

        fixture, origin = self.workspace_fixture()
        zulu = fixture.store.mutate('project', dict(name='Zulu', repo='/zulu'))['id']
        alpha = fixture.store.mutate('project', dict(name='Alpha', repo='/alpha'))['id']
        for name, project in [('Task 2', zulu), ('Task 10', alpha), ('Task 1', alpha)]:
            task = fixture.store.mutate('task', dict(project_id=project, title=name, goal='Fixture work'))['id']
            if name == 'Task 2':
                fixture.store.mutate('assign', dict(session_id='s', turn_id='t', task_id=task))
            if name == 'Task 1':
                fixture.store.mutate('task_status', dict(id=task, status='completed', outcome='Fixture verification'))
        for i in range(22):
            task = fixture.store.mutate('task', dict(project_id=zulu, title=f'Queued {i:02}', goal='Fixture work'))['id']
            fixture.store.mutate('task_status', dict(id=task, status='waiting'))
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM', '/usr/bin/chromium'), args=['--no-sandbox'])
            context = browser.new_context(viewport={'width': 1440, 'height': 1100})
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            extra_experiments = []
            def workspace_response(route):
                payload = route.fetch().json()
                # Explicit API fixture for missing usage; empty real tasks normally report zero.
                for row in payload['tasks']:
                    if row['title'] in ('Task 1', 'Task 10'):
                        row['usage'] = None
                if extra_experiments:
                    payload['experiments'] = extra_experiments
                route.fulfill(json=payload)
            page.route('**/api/workspace?*', workspace_response)
            page.emulate_media(reduced_motion='reduce')
            page.goto(origin + '/#tasks')
            table = page.locator('[data-table="tasks"]')
            expect(table.locator('tbody tr')).to_have_count(20)
            table.get_by_role('button', name='Next', exact=True).click()
            expect(table.locator('tbody tr')).to_have_count(5)
            page.get_by_role('searchbox', name='Filter tasks by Status', exact=True).fill('ACTIVE')
            expect(table.locator('tbody tr')).to_have_count(2)
            # Filters intersect and use displayed project names, not opaque IDs.
            project_filter = page.get_by_role('searchbox', name='Filter tasks by Project', exact=True)
            project_filter.fill('Zu')
            project_filter.press_sequentially('lu')
            expect(project_filter).to_be_focused()
            expect(table.locator('tbody')).to_contain_text('Task 2')
            expect(table.locator('tbody tr')).to_have_count(1)
            page.reload()
            expect(project_filter).to_have_value('Zulu')
            expect(page.get_by_role('searchbox', name='Filter tasks by Status', exact=True)).to_have_value('ACTIVE')
            expect(table.locator('tbody tr')).to_have_count(1)
            table.get_by_role('button', name='Reset table', exact=True).click()
            page.get_by_role('textbox', name='Search tasks', exact=True).fill('Task')
            title_sort = table.get_by_role('button', name='Sort by Task', exact=True)
            titles = lambda: table.locator('tbody td:first-child').all_text_contents()
            title_sort.click()
            self.assertEqual(titles(), ['Task 1', 'Task 2', 'Task 10'])
            expect(table.locator('th').first).to_have_attribute('aria-sort', 'ascending')
            title_sort.click()
            self.assertEqual(titles(), ['Task 10', 'Task 2', 'Task 1'])
            title_sort.click()
            expect(table.locator('th').first).to_have_attribute('aria-sort', 'none')
            table.get_by_role('button', name='Sort by Project', exact=True).click()
            self.assertEqual(table.locator('tbody td:nth-child(2)').all_text_contents(), ['Alpha', 'Alpha', 'Zulu'])
            tokens_sort = table.get_by_role('button', name='Sort by Measured tokens', exact=True)
            for _ in range(2):
                tokens_sort.click()
                self.assertEqual(titles()[0], 'Task 2')  # Unknown usage remains last in either direction.
            numeric = page.get_by_role('searchbox', name='Filter tasks by Measured tokens', exact=True)
            numeric.fill('>= 100')
            expect(table.locator('tbody tr')).to_have_count(1)
            numeric.fill('>= 0')
            expect(table.locator('tbody tr')).to_have_count(1)  # Missing usage is not zero.
            numeric.fill('= 0')
            expect(table.locator('tbody')).to_contain_text('No matching rows')
            numeric.fill('unknown')
            expect(table.locator('tbody tr')).to_have_count(2)
            page.reload()
            expect(numeric).to_have_value('unknown')
            expect(table.locator('th').nth(3)).to_have_attribute('aria-sort', 'descending')
            table.get_by_role('button', name='Reset table', exact=True).click()
            page.set_viewport_size({'width': 390, 'height': 844})
            expect(page.get_by_role('button', name='Switch to dark theme', exact=True)).to_be_visible()
            page.get_by_role('button', name='Switch to dark theme', exact=True).click()
            expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
            # Saved theme is applied even before the application module executes.
            other = page.context.new_page()
            other.route('**/workspace.js', lambda route: route.abort())
            other.goto(origin)
            expect(other.locator('html')).to_have_attribute('data-theme', 'dark')
            other.unroute('**/workspace.js')
            other.reload()
            expect(other.get_by_role('button', name='Switch to light theme', exact=True)).to_be_visible()
            page.get_by_role('button', name='Switch to light theme', exact=True).click()
            expect(other.locator('html')).to_have_attribute('data-theme', 'light')
            page.get_by_role('button', name='Switch to dark theme', exact=True).click()
            page.reload()
            expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
            expect(table.locator('tbody tr')).to_have_count(20)
            page.screenshot(path='work/security/ui-review-20261112/screenshots/columns-dark-mobile.png', animations='disabled')
            page.set_viewport_size({'width': 1440, 'height': 1100})
            page.screenshot(path='work/security/ui-review-20261112/screenshots/columns-dark-desktop.png', full_page=True, animations='disabled')
            extra_experiments.append(dict(id='column-fixture', proposal={'title': 'Column fixture'},
                baseline={'usage': {'total_tokens': 110}, 'event_count': 2, 'first_at': 'fixture', 'last_at': 'fixture'},
                baseline_sha256='fixture', state='proposed', created='2026-11-12', evaluations=[{
                    'protocol': {'id': 'fixture'}, 'reviews': [], 'measurements': {
                        'scope': 'Browser fixture', 'raw_total_tokens': 12, 'compact_total_tokens': 10,
                        'acceptance_passed': True, 'token_reduction_fraction': .1,
                        'cells': [{'case': 'First', 'condition': 'raw', 'usage': {'total_tokens': 10}, 'wall_seconds': 2, 'quality': {'passed': True}},
                                  {'case': 'Second', 'condition': 'compact', 'usage': {'total_tokens': 2}, 'wall_seconds': 1, 'quality': {'passed': False}}]}}]))
            page.goto(origin + '/?fixture=experiments#experiments')
            page.get_by_role('button', name='Actions for Column fixture', exact=True).click()
            page.get_by_role('menuitem', name='Inspect protocol and baseline', exact=True).click()
            modal_table = page.locator('dialog [data-table]')
            expect(modal_table.locator('tbody tr')).to_have_count(2)
            modal_table.get_by_role('button', name='Sort by Total tokens', exact=True).click()
            expect(modal_table.locator('tbody td:first-child').first).to_have_text('Second')
            modal_table.get_by_role('searchbox', name='Filter evaluation-column-fixture-0 by Quality', exact=True).fill('pass')
            expect(modal_table.locator('tbody tr')).to_have_count(1)
            expect(modal_table.locator('tbody')).to_contain_text('First')
            expect(page.locator('dialog')).to_be_visible()
            blocked = browser.new_page()
            blocked.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Storage blocked','SecurityError')}})")
            blocked.goto(origin)
            blocked.get_by_role('button', name='Switch to dark theme', exact=True).click()
            expect(blocked.locator('html')).to_have_attribute('data-theme', 'dark')
            self.assertEqual(errors, [])
            browser.close()


if __name__ == '__main__':
    unittest.main()
