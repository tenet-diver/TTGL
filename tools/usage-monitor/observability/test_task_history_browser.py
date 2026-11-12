import json,os,sys,tempfile,threading,time,unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
sys.path.insert(0,str(Path('tools/usage-monitor/observability').resolve()))
import test_workspace
from workspace import Handler


@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA')=='1','Opt-in browser QA using existing Playwright and system Chromium')
class HistoryBrowserTests(unittest.TestCase):
    def test_analysis_search_drilldown_and_mobile(self):
        from playwright.sync_api import sync_playwright,expect
        fixture=test_workspace.WorkspaceTests();fixture.setUp()
        previous_path=os.environ.get('PATH','');previous_model=os.environ.get('TTGL_TASK_MODEL')
        try:
            fixture.store.scan();project,task=fixture.define_task()
            fixture.store.mutate('assign',dict(session_id='s',turn_id='t',task_id=task))
            # Explicit test-only native CLI fixture. No actual model inference or downloaded executable.
            bindir=fixture.root/'bin';bindir.mkdir();fake=bindir/'codex'
            fake.write_text('''#!/usr/bin/env python3
        import sys,json,pathlib
        text=sys.stdin.read();body=json.loads(text[text.index('\\n')+1:].split('\\nVISIBLE EVIDENCE EXCERPTS:')[0])
        result={'summary':'Test fixture: searched source to locate the failing behavior; task success unverified.','subtasks':[{'title':'Investigate source behavior','summary':'A search operation inspected the source. This is a fixture interpretation.','activity':'investigate','tags':['regression','source-search'],'confidence':0.8,'step_ids':[s['id'] for s in body['steps']]}]}
        schema=json.loads(pathlib.Path(sys.argv[sys.argv.index('--output-schema')+1]).read_text())
        if 'knowledge' in schema['properties']:result.update(task_type='investigation',knowledge=[{'title':'Fixture search lesson','statement':'Search evidence was collected in this fixture; outcome unverified.','step_ids':[body['steps'][0]['id']],'confidence':0.6}])
        if 'assignments' in schema['properties']:
            result['assignments']={s['id']:0 for s in body['steps']}
            for group in result['subtasks']:group.pop('step_ids')
        pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(json.dumps(result))
        print(json.dumps({'type':'turn.completed','usage':{'input_tokens':20,'output_tokens':10,'total_tokens':30}}))
        '''.replace('\n        ','\n'));fake.chmod(0o700)
            os.environ['PATH']=str(bindir)+os.pathsep+os.environ['PATH'];os.environ['TTGL_TASK_MODEL']='browser-fixture-model'
            server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.store=fixture.store
            port=server.server_port;server.allowed_hosts={f'127.0.0.1:{port}',f'localhost:{port}'};server.allowed_origins={f'http://127.0.0.1:{port}',f'http://localhost:{port}'}
            threading.Thread(target=server.serve_forever,daemon=True).start()
            self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
                page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(f'http://127.0.0.1:{port}/#tasks');page.wait_for_selector('[data-table="work-tasks"] [data-work-task]')
                page.locator('[data-table="work-tasks"] [data-work-task]').first.click()
                page.get_by_role('button',name='Mine with Luna',exact=True).click()
                page.wait_for_selector('.task-detail [data-mining-active="true"]')
                page.wait_for_function('''async () => {const r=await fetch('/api/work-task?task_id='+new URLSearchParams(location.search).get('task'));const d=await r.json();return d.jobs[0]?.status==='completed';}''')
                page.get_by_role('button',name='Refresh',exact=True).click()
                page.wait_for_selector('[data-table="task-knowledge"]',timeout=20000)
                page.get_by_role('button',name='Task details',exact=True).click()
                page.wait_for_selector('dialog [data-subtask]',timeout=20000)
                assert 'fixture' in page.locator('#modal-content').inner_text().lower()
                page.locator('dialog [data-subtask] summary').click();page.wait_for_selector('[data-history-evidence]')
                page.locator('[data-history-evidence]').click();page.wait_for_selector('[data-source-output] pre')
                assert 'aggregated_output' in page.locator('[data-source-output]').inner_text()
                page.get_by_role('button',name='Close',exact=True).click();page.get_by_role('button',name='All tasks',exact=True).click()
                page.locator('[name=query]').fill('regression');page.locator('[data-work-search]').get_by_role('button',name='Search',exact=True).click()
                expect(page.locator('[data-table="work-tasks"] tbody tr')).to_have_count(1)
                assert page.locator('[data-table="work-tasks"] tbody tr').count()==1
                page.locator('[name=query]').fill('nothingmatches');page.locator('[data-work-search]').get_by_role('button',name='Search',exact=True).click();page.wait_for_selector('.ui-empty')
                page.locator('[name=query]').fill('regression');page.locator('[data-work-search]').get_by_role('button',name='Search',exact=True).click();page.wait_for_selector('[data-table="work-tasks"] [data-work-task]')
                page.set_viewport_size({'width':390,'height':844});page.locator('[data-table="work-tasks"] [data-work-task]').first.click();page.get_by_role('button',name='Task details',exact=True).click();page.wait_for_selector('dialog [data-subtask]')
                assert page.locator('dialog').bounding_box()['width']<=390
                screenshot=Path('work/security/task-history-qa/mobile.png');screenshot.parent.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(screenshot))
                assert not errors,errors
                print(json.dumps({'browser':'system Chromium via existing Playwright','analysis':'explicit CLI test fixture, not real model','checks':['task discovery','analysis button and background process','subtask interpretation','lazy source steps','retained source retrieval','tag search','empty state','mobile modal'],'page_errors':errors,'screenshot':str(screenshot)}))
                browser.close()
        finally:
            fixture.tearDown();fixture.directory.cleanup()
            os.environ['PATH']=previous_path
            if previous_model is None:os.environ.pop('TTGL_TASK_MODEL',None)
            else:os.environ['TTGL_TASK_MODEL']=previous_model

if __name__=='__main__':unittest.main()
