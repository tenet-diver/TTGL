"""Read-only desktop dark validation after the isolated synthetic load seed."""
import json
import os
from pathlib import Path
import time
from playwright.sync_api import sync_playwright, expect
base=os.environ.get('OBS_TEST_URL','http://127.0.0.1:3433')
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    started=time.monotonic()
    page.goto(base+'/tasks?range=all&project=qa-load',wait_until='networkidle')
    table=page.locator('[data-list="tasks-tasks"]')
    expect(table.locator('.record-count')).to_have_text('1,000 records')
    expect(table.locator('tbody tr')).to_have_count(20)
    table.get_by_role('textbox',name='Search tasks-tasks',exact=True).fill('task 999')
    expect(table.locator('.record-count')).to_have_text('1 records')
    expect(table.locator('tbody')).to_contain_text('task 999')
    page.goto(base+'/tasks/qa-load-task-0',wait_until='networkidle')
    expect(page.locator('[data-list="task-steps"]')).to_have_count(0)
    expect(page.get_by_role('button',name='Analyze with Luna',exact=True)).to_be_visible()
    response=page.request.get(base+'/api/records/steps?range=all&project=qa-load&task=qa-load-task-0')
    assert response.ok and response.json()['total']==12
    page.screenshot(path='work/security/next-migration-20261115/browser/load-task-desktop-dark.png',full_page=True)
    assert not errors,errors
    print(json.dumps({'scope':'desktop dark','turns':1000,'events':12000,'pagination_rows':20,'global_phrase_search':'pass','raw_step_records':12,'unclassified_task_has_no_unscoped_step_table':True,'page_errors':errors,'seconds':round(time.monotonic()-started,3)}))
    browser.close()
