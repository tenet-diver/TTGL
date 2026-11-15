"""Task detail must stay independent of unrelated workspace history."""
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
import test_usage_views_browser
import optimization
import usage_views
import work_analytics


class TaskPageQueryTests(unittest.TestCase):
    def fixture(self):
        host=test_usage_views_browser.UsagePagesBrowserTests();f,origin,task=host.fixture();self.addCleanup(host.doCleanups)
        return f,origin,task

    def test_task_dataset_excludes_other_sessions_but_retains_followups(self):
        f,_,task=self.fixture()
        with f.store.connection() as c:
            c.execute("INSERT INTO turns VALUES('s','next','/repo','Wait, fix this','2026-11-05T00:01:00Z','2026-11-05T00:02:00Z',1)")
            c.execute("INSERT INTO events(id,session_id,turn_id,kind,name,ts) VALUES('next-event','s','next','tool','Read','2026-11-05T00:01:00Z')")
            c.executemany('INSERT INTO events(id,session_id,turn_id,kind,name,ts) VALUES(?,?,?,?,?,?)',[(f'unrelated-{i}','other','turn','tool','Read','2026-11-05T00:00:00Z') for i in range(3000)])
        data=optimization.dataset(f.store,task_id=task)
        self.assertIn('next-event',{r['id'] for r in data['rows']})
        self.assertFalse(any(r['session_id']=='other' for r in data['rows']))
        with patch.object(work_analytics,'task_data',wraps=work_analytics.task_data) as build:
            report=usage_views.task_report(f.store,task)
        self.assertEqual(build.call_count,1)
        self.assertEqual(report['event_count'],4)
        self.assertEqual(report['outcome']['tasks'][0]['followup'],'Wait, fix this')

    def test_all_source_steps_do_not_rebuild_subtask_analytics(self):
        f,_,task=self.fixture()
        with patch.object(work_analytics,'task_data',side_effect=AssertionError('Unnecessary full task analytics')):
            rows=work_analytics.source_steps(f.store,task,limit='all')
            self.assertEqual(rows['total'],4)
            with self.assertRaises(ValueError):work_analytics.source_steps(f.store,'missing')


@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA')=='1','Opt-in browser QA')
class TaskPageBrowserTests(unittest.TestCase):
    fixture=TaskPageQueryTests.fixture

    def test_direct_task_requests_compact_steps_and_lazy_source_collection(self):
        from playwright.sync_api import sync_playwright,expect
        f,origin,task=self.fixture()
        with f.store.connection() as c:
            usage=json.dumps(dict(input_tokens=100000,cached_input_tokens=80000,output_tokens=500,total_tokens=100500))
            for i in range(120):
                c.execute('INSERT INTO events(id,session_id,turn_id,kind,name,ts,runtime,usage,model) VALUES(?,?,?,?,?,?,?,?,?)',(f'load-{i}','s','t','generation' if i%2==0 else 'tool','Model response' if i%2==0 else 'Bash',f'2026-11-05T00:{i//60:02}:{i%60:02}Z',.4,usage if i%2==0 else None,'test-model' if i%2==0 else None))
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];requests=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('request',lambda r:requests.append(r.url))
            # A detail page must not depend on the slow whole-workspace aggregation.
            page.route('**/api/work-explorer?*',lambda route:route.abort())
            page.goto(origin+'/tasks/'+task+'?range=all')
            steps=page.locator('[data-table="task-report-steps"]')
            expect(steps.locator('tbody tr')).to_have_count(20)
            self.assertFalse(any('/api/work-explorer?' in r for r in requests))
            self.assertFalse(any('/api/work-steps?' in r or '/api/task-timeline?' in r for r in requests))
            self.assertEqual(sum('/api/work-task?' in r for r in requests),1)
            self.assertEqual(sum('/api/task-report?' in r for r in requests),1)
            self.assertLessEqual(steps.locator('tbody tr').first.bounding_box()['height'],36)
            expect(steps.locator('.column-filters')).not_to_be_visible()
            steps.get_by_role('button',name='Filters',exact=True).click()
            steps.get_by_label('Filter task-report-steps by Tokens in',exact=True).fill('>= 100000')
            expect(steps.locator('tbody tr')).to_have_count(20)
            steps.get_by_role('button',name='Sort by Tokens in',exact=True).click()
            steps.get_by_role('button',name='Next',exact=True).click()
            expect(steps.get_by_label('Page task-report-steps',exact=True)).to_have_value('2')
            steps.get_by_role('button',name='Reset table',exact=True).click()
            page.locator('[data-subtask]').first.click()
            expect(page.locator('[data-subtask]').first).to_have_attribute('aria-pressed','true')
            # Subtask changes keep the existing story instead of rereading transcripts.
            self.assertEqual(sum('/api/task-report?' in r for r in requests),1)
            expect(page.locator('[data-work-steps] tbody tr')).not_to_have_count(0)
            page.locator('[data-all-steps]').click()
            expect(page.locator('[data-subtask]').first).to_have_attribute('aria-pressed','false')
            self.assertEqual(sum('/api/task-report?' in r for r in requests),1)
            artifacts=Path('work/security/task-layout-qa');artifacts.mkdir(parents=True,exist_ok=True)
            for theme in ('light','dark'):
                page.locator('html').evaluate('(node,theme)=>node.dataset.theme=theme',theme)
                for width in (1440,768,390):
                    page.set_viewport_size({'width':width,'height':1000})
                    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
                    page.evaluate('window.scrollTo(0,0)')
                    page.screenshot(path=str(artifacts/f'task-{theme}-{width}.png'),full_page=True,animations='disabled')
                    steps.scroll_into_view_if_needed()
                    page.screenshot(path=str(artifacts/f'steps-{theme}-{width}.png'),animations='disabled')
            # Advance the browser clock to prove an idle analysis page does not poll.
            page.clock.install();before=len(requests);page.clock.fast_forward(11000)
            self.assertEqual(len(requests),before)
            self.assertEqual(errors,[]);browser.close()


if __name__=='__main__':unittest.main()
