"""Opt-in end-to-end curation with a real HTTP store and an explicit CLI fixture."""
import json
import os
from pathlib import Path
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import test_workspace
from workspace import Handler


@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA')=='1','Opt-in browser QA')
class CurationBrowserTests(unittest.TestCase):
    def test_prompt_name_luna_format_timeline_grouping_and_retrieval(self):
        from playwright.sync_api import sync_playwright,expect
        fixture=test_workspace.WorkspaceTests();fixture.setUp()
        self.addCleanup(fixture.directory.cleanup)
        fixture.rows.append(dict(timestamp='2026-11-05T00:00:03Z',type='event_msg',payload=dict(type='item_completed',thread_id='s',turn_id='t',item=dict(type='CommandExecution',id='test-check',command=['python3','-m','unittest'],aggregated_output='Fixture check output',exit_code=0,duration=dict(secs=3,nanos=0)))))
        fixture.source.write_text(''.join(json.dumps(r)+'\n' for r in fixture.rows))
        fixture.store.scan();fixture.store.mutate('project',dict(name='Fixture project',repo='/repo'))
        bindir=fixture.root/'bin';bindir.mkdir();fake=bindir/'codex'
        fake.write_text('''#!/usr/bin/env python3
import json,pathlib,sys
body=sys.stdin.read()
schema=json.loads(pathlib.Path(sys.argv[sys.argv.index('--output-schema')+1]).read_text())
assert set(schema['properties'])=={'title'}, 'Only a name formatting request is expected'
assert 'Fix the problem' in body
pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(json.dumps({'title':'Repair source behavior'}))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':20,'output_tokens':10,'total_tokens':30}}))
''');fake.chmod(0o700)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.store=fixture.store
        origin=f'http://127.0.0.1:{server.server_port}';server.allowed_hosts={f'127.0.0.1:{server.server_port}'};server.allowed_origins={origin}
        threading.Thread(target=server.serve_forever,daemon=True).start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        with patch.dict(os.environ,{'PATH':str(bindir)+os.pathsep+os.environ['PATH'],'TTGL_TASK_MODEL':'browser-title-fixture','TTGL_TASK_ANALYZER':'codex'}),sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1100});page.emulate_media(reduced_motion='reduce')
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(origin+'/#inbox')
            page.get_by_role('button',name='Actions for s:t',exact=True).click()
            page.get_by_role('menuitem',name='Create task from prompt',exact=True).click()
            expect(page.get_by_role('textbox',name='Intended outcome',exact=True)).to_have_value('Fix the problem')
            page.get_by_role('button',name='Start task',exact=True).click()
            expect(page.locator('dialog')).not_to_be_visible()
            page.locator('nav [data-view="tasks"]').click()
            page.get_by_role('button',name='Explore task',exact=True).click();page.get_by_role('button',name='Task details',exact=True).click()
            expect(page.locator('#modal-title')).to_have_text('Fix the problem')
            chart=page.locator('dialog [data-task-timeline]')
            expect(chart.locator('[data-step-select]')).to_have_count(2)
            expect(chart.locator('.timeline-bar')).to_have_count(2)
            for box in chart.locator('[data-step-select]').all():box.check()
            chart.get_by_role('textbox',name='Subtask name',exact=True).fill('Inspect and verify source')
            chart.get_by_label('Subtask type',exact=True).select_option('test')
            chart.get_by_role('button',name='Collect selected into subtask',exact=True).click()
            group=page.locator('dialog [data-subtask]')
            expect(group).to_have_count(1)
            expect(group).to_contain_text('User-collected · outcome unverified')
            group.locator('summary').click()
            expect(group.locator('[data-history-evidence]')).to_have_count(2)
            group.locator('[data-history-evidence]').first.click()
            expect(group.locator('[data-source-output]')).to_contain_text('aggregated_output')
            page.get_by_role('button',name='Format name with Luna',exact=True).click()
            expect(page.locator('#modal-title')).to_have_text('Repair source behavior',timeout=20000)
            expect(page.locator('dialog')).to_contain_text('30 recorded tokens')
            expect(page.locator('dialog [data-subtask]')).to_have_count(1)
            page.get_by_role('button',name='Name from user prompt',exact=True).click()
            expect(page.locator('#modal-title')).to_have_text('Fix the problem')
            page.get_by_role('button',name='Close',exact=True).click()
            report=page.request.get(origin+'/api/workspace').json()
            self.assertEqual(report['usage']['total_tokens'],110)
            self.assertEqual(report['tasks'][0]['title_source'],'prompt')
            task=report['tasks'][0]['id']
            page.reload()
            expect(page.locator('[data-work-timeline] .timeline-bar')).to_have_count(2)
            expect(page.locator('[data-work-timeline]')).to_contain_text('1 collected subtasks')
            page.screenshot(path='work/security/ui-review-20261112/screenshots/step-timeline-desktop.png',full_page=True,animations='disabled')
            page.set_viewport_size({'width':390,'height':844})
            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),390)
            page.screenshot(path='work/security/ui-review-20261112/screenshots/step-timeline-mobile.png',full_page=True,animations='disabled')
            page.get_by_role('button',name='All tasks',exact=True).click()
            page.locator('[name=query]').fill('verify')
            page.locator('[data-work-search]').get_by_role('button',name='Search',exact=True).click()
            expect(page.locator('.task-card')).to_have_count(1)
            self.assertEqual(errors,[])
            browser.close()


if __name__=='__main__':unittest.main()
