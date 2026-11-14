import json,os,threading,unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from unittest.mock import patch
import test_task_evidence as fixtures
from workspace import Handler
import activity_insights as a
import task_history as h

@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA')=='1','Opt-in existing Playwright/system Chromium QA')
class ActivityBrowserTests(unittest.TestCase):
 def test_suggestions_group_acceptance_and_task_evidence(self):
  from playwright.sync_api import sync_playwright,expect
  fixture=fixtures.EvidenceTests();fixture.setUp();self.addCleanup(fixture.fixture.directory.cleanup)
  fixture.test_native_change_validation_and_image_sources();store=fixture.store
  with store.connection() as c:c.execute('DELETE FROM assignments')
  a.init(store);body=a.collect(store)
  result={'summary':'Browser fixture: proposed task from retained source steps.','tasks':[{'title':'Fixture: repair the page','goal':'Repair the visual page and verify the change.','task_type':'bugfix','tags':['frontend'],'turn_refs':[r['ref'] for r in body['turns']],'confidence':0.8,'subtasks':[{'title':'Repair and verify page','summary':'Fixture interpretation linked to the recorded changes and checks.','activity':'implement','tags':['frontend','validation'],'confidence':0.8,'step_ids':[s['id'] for s in body['steps']]}]}],'suggestions':[{'title':'Keep screenshot references','rationale':'A visual reference exists in retained activity.','action':'Record before/after references with the validation outcome.','validation':'Check screenshot coverage and functional tests before adoption.','risk':'A reference is not visual correctness.','step_ids':[body['steps'][0]['id']]}]}
  server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.store=store;port=server.server_port;url=f'http://127.0.0.1:{port}'
  server.allowed_hosts={f'127.0.0.1:{port}'};server.allowed_origins={url}
  threading.Thread(target=server.serve_forever,daemon=True).start();self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
  with patch.dict(os.environ,{'TTGL_TASK_ANALYZER':'ollama','TTGL_TASK_MODEL':'explicit-browser-fixture'}),patch.object(h,'local_analysis',return_value=(json.dumps(result),{'input_tokens':20,'output_tokens':10},True)),sync_playwright() as p:
   browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
   page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(url+'/#suggestions');page.get_by_role('button',name='Analyze recent activity',exact=True).click()
   expect(page.get_by_role('heading',name='Fixture: repair the page',exact=True)).to_be_visible(timeout=20000)
   page.get_by_role('button',name='Accept task grouping',exact=True).click();page.get_by_role('button',name='Evidence & outcomes',exact=True).click()
   expect(page.get_by_role('heading',name='What changed',exact=True)).to_be_visible()
   expect(page.locator('#modal-content')).to_contain_text('src/page.tsx');expect(page.locator('#modal-content')).to_contain_text('command_passed');expect(page.locator('#modal-content')).to_contain_text('/private/not-read.png')
   page.get_by_text('Add evidence or confirm an intervention',exact=True).click()
   page.get_by_label('Kind',exact=True).select_option('intervention');page.get_by_label('Title',exact=True).fill('I corrected the acceptance test');page.get_by_label('Recorded outcome',exact=True).select_option('confirmed')
   page.get_by_role('button',name='Record evidence',exact=True).click();expect(page.locator('#modal-content')).to_contain_text('I corrected the acceptance test')
   page.get_by_role('button',name='Close',exact=True).click();page.get_by_role('button',name='Suggestions',exact=True).click()
   page.get_by_role('button',name='Decline',exact=True).click();expect(page.locator('#content .detail-grid')).to_contain_text('declined')
   page.set_viewport_size({'width':390,'height':844});page.get_by_role('button',name='Open accepted task',exact=True).click();page.get_by_role('button',name='Evidence & outcomes',exact=True).click()
   expect(page.get_by_role('heading',name='What changed',exact=True)).to_be_visible();self.assertLessEqual(page.locator('dialog').bounding_box()['width'],390)
   dest=Path('work/security/activity-insights-qa/mobile.png');dest.parent.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(dest))
   self.assertEqual(errors,[]);browser.close()
   print('Browser passed: fixture model -> proposals -> accepted task/subtasks -> change, validation and visual references -> explicit intervention -> saved suggestion decision; mobile modal; no page errors. No real model inference.')
if __name__=='__main__':unittest.main()
