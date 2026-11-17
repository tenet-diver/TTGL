"""Production Next.js checks using isolated synthetic PostgreSQL/ClickHouse/S3 data.

The S3 endpoint is a labeled protocol fixture, not Garage compatibility evidence.
Photographs specify hierarchy, density and interactions, not fixture counts.
"""
import json
import os
from pathlib import Path
import re
import time
import urllib.request
from urllib.parse import quote
from playwright.sync_api import sync_playwright, expect

BASE = os.environ.get('OBS_TEST_URL', 'http://127.0.0.1:3433')
OUT = Path('work/security/next-migration-20261115/browser')
OUT.mkdir(parents=True, exist_ok=True)
PAGES = {
    '/': 'Overall activity', '/tasks': 'Task activity', '/grouping': 'Task grouping',
    '/tools': 'Tool usage', '/tools?family=Shell&action=cat': 'Shell',
    '/costs': 'Cost & tokens', '/timeline': 'Activity timeline', '/agents': 'Agents',
    '/process': 'Process map', '/entities': 'Entities', '/outcomes': 'Outcomes',
    '/suggestions': 'Suggestions', '/impact': 'Impact', '/live': 'Live sessions',
    '/live/rules': 'Steering rules', '/categorization': 'Categorization',
    '/data': 'Data list', '/jobs': 'Mining jobs', '/pricing': 'Pricing',
    '/knowledge': 'Knowledge', '/tasks/qa-task-0': 'Validate Observatory flow 00', '/tasks/qa-task-0/subtasks/qa-analysis-0%3A0':'Explore',
}
native = json.load(urllib.request.urlopen(BASE+'/api/records/tasks?range=all&search=Retained%20native%20prompt'))
assert native['rows'], 'Collector-created native task fixture is required for encoded-ID routing checks'
row=native['rows'][0]
PAGES[quote(row['href'],safe='/')]=row['title']
results, errors, captures = [], [], []

def visit(page, route):
    page.goto(BASE + route + ('&' if '?' in route else '?') + 'range=all', wait_until='networkidle')
    expect(page.locator('.record-list[aria-busy=true]')).to_have_count(0)
    expect(page.locator('.storage-error')).to_have_count(0)
    expect(page.get_by_role('alert').filter(has_text=re.compile(r'\S'))).to_have_count(0)

def capture(page, route, theme):
    name = re.sub(r'[^a-zA-Z0-9_-]', '-', route.strip('/')) or 'overview'
    artifact=OUT/f'{name}-{theme}.png'
    page.screenshot(path=str(artifact), full_page=True)
    captures.append(str(artifact))

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
    page.on('pageerror', lambda error: errors.append({'route':page.url,'error':str(error)}))
    for route, title in PAGES.items():
        started = time.monotonic()
        visit(page, route)
        expect(page.get_by_role('heading', name=title, exact=True, level=1)).to_be_visible()
        capture(page, route, 'dark')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2'), route
        results.append({'route': route, 'seconds': round(time.monotonic() - started, 3),
                        'tables': page.locator('[data-list]').count()})
    print('Desktop routes passed', len(results), flush=True)

    visit(page, '/tasks')
    table = page.locator('[data-list="tasks-tasks"]')
    expect(table.locator('tbody tr')).to_have_count(20)
    first_before = table.locator('tbody tr').first.inner_text()
    total_before = table.locator('.record-count').inner_text()
    table.get_by_role('button', name='Next page tasks-tasks', exact=True).click()
    expect(table.locator('.page-jump input')).to_have_value('2')
    expect(table.locator('tbody tr').first).not_to_have_text(first_before)
    table.get_by_role('textbox', name='Search tasks-tasks', exact=True).fill('flow 00')
    expect(table.locator('tbody tr')).to_have_count(1)
    expect(table.locator('tbody')).to_contain_text('flow 00')
    table.get_by_role('button', name='Clear search tasks-tasks', exact=True).click()
    expect(table.locator('tbody tr')).to_have_count(20)
    table.get_by_role('button', name='Filters', exact=True).click()
    table.get_by_role('textbox', name='Filter tasks-tasks by Tokens', exact=True).fill('>= 1000000')
    expect(table.locator('.record-count')).not_to_have_text(total_before)
    table.get_by_role('button', name='Reset', exact=True).click()
    table.get_by_role('button', name='Sort by Started', exact=True).click()
    expect(table.get_by_role('button', name='Sort by Started', exact=True)).to_have_attribute('aria-pressed', 'true')
    table.get_by_role('button', name='Columns tasks-tasks', exact=True).click()
    page.get_by_role('menuitemcheckbox', name='Tokens', exact=True).click()
    page.keyboard.press('Escape')
    expect(table.get_by_role('button', name='Sort by Tokens', exact=True)).to_have_count(0)
    page.reload(wait_until='networkidle')
    expect(table.get_by_role('button', name='Sort by Tokens', exact=True)).to_have_count(0)
    table.locator('tbody tr').first.locator('td').first.click(button='right')
    page.get_by_role('button', name='Show matching', exact=True).click()
    expect(table.locator('.record-count')).to_have_text('1 records')
    table.get_by_role('button', name='Reset', exact=True).click()
    print('Shared table controls passed', flush=True)

    visit(page, '/live/rules')
    switch = page.get_by_role('switch', name='Enable Prompt after a break', exact=True)
    before = switch.get_attribute('aria-checked')
    switch.click()
    expect(switch).to_have_attribute('aria-checked', 'false' if before == 'true' else 'true')
    page.reload(wait_until='networkidle')
    expect(switch).to_have_attribute('aria-checked', 'false' if before == 'true' else 'true')
    switch.click()
    expect(switch).to_have_attribute('aria-checked', before)

    visit(page, '/impact')
    page.get_by_role('button', name='Record a change', exact=True).click()
    dialog = page.get_by_role('dialog')
    title = 'Browser validation change ' + str(time.time_ns())
    dialog.get_by_label('What did you change?', exact=True).fill(title)
    dialog.get_by_label('Notes and evidence', exact=True).fill('Synthetic fixture; no causal performance claim')
    dialog.get_by_role('button', name='Save', exact=True).click()
    expect(dialog).not_to_be_visible()
    expect(page.locator('[data-list="impact-changes"]')).to_contain_text(title)
    print('Persisted mutations and immediate table refresh passed', flush=True)

    visit(page, '/tasks/qa-task-0')
    page.get_by_role('button',name='Record outcome',exact=True).click()
    outcome=page.get_by_role('dialog')
    outcome.get_by_label('Task status',exact=True).click()
    page.get_by_role('option',name='completed',exact=True).click()
    outcome.get_by_label('Acceptance evidence',exact=True).fill('')
    outcome.get_by_role('button',name='Save',exact=True).click()
    expect(outcome.get_by_role('alert')).to_contain_text('acceptance evidence')
    outcome.get_by_label('Acceptance evidence',exact=True).fill('Synthetic explicit acceptance record for browser validation')
    outcome.get_by_role('button',name='Save',exact=True).click()
    expect(outcome).not_to_be_visible()
    expect(page.locator('.page-header')).to_contain_text('completed')
    steps = page.locator('[data-list="task-steps"]')
    expect(steps).to_have_count(0)
    page.locator('[data-list="task-subtasks"]').get_by_role('link',name='Explore',exact=True).click()
    expect(page).to_have_url(re.compile(r'/tasks/qa-task-0/subtasks/qa-analysis-0(?:%3A|:)0'))
    expect(steps.locator('tbody tr')).to_have_count(2)
    expect(page.locator('.page-header')).to_contain_text('blocked')
    expect(page.locator('main')).to_contain_text('Synthetic missing fixture permission')
    page.locator('.native-timeline button').first.click()
    expect(steps.locator('tbody tr')).to_have_count(1)
    page.get_by_role('button', name='Clear step filter', exact=True).click()
    expect(steps.locator('tbody tr')).to_have_count(2)
    steps.get_by_role('button', name='Inspect', exact=False).first.click()
    expect(page.get_by_role('dialog')).to_contain_text('Synthetic browser validation')
    page.keyboard.press('Escape')
    page.locator('.screenshot-grid button').first.click()
    expect(page.get_by_role('dialog').locator('img')).to_be_visible()
    assert page.get_by_role('dialog').locator('img').evaluate('(img)=>img.complete&&img.naturalWidth>0')
    page.keyboard.press('Escape')
    visit(page,'/tasks/qa-task-0/subtasks/qa-analysis-0%3A1')
    expect(steps.locator('tbody tr')).to_have_count(2)
    expect(page.locator('.screenshot-grid button')).to_have_count(0)
    expect(steps.locator('tbody')).not_to_contain_text('qa-task-1')
    forged=page.request.get(BASE+'/api/records/steps?range=all&task=qa-task-0&subtask=qa-analysis-0%3A0&ids=qa-task-0%3A7')
    assert forged.ok and forged.json()['total']==0
    rejected=page.request.get(BASE+'/api/records/steps?range=all&task=qa-task-1&subtask=qa-analysis-0%3A0')
    assert rejected.status==400
    visit(page,'/tasks/qa-task-0')
    page.get_by_role('button',name='Open subtask Explore',exact=True).click()
    expect(steps.locator('tbody tr')).to_have_count(2)
    print('Task → subtask navigation, scoped source/image/tool flows and server isolation passed', flush=True)

    browser.close()
assert not errors, errors
report = {'scope':'Desktop dark theme only', 'pages': results, 'page_errors': errors,
          'checks': ['23 desktop routes, including encoded native task and subtask IDs', 'shared search/filter/exact filter/sort/pagination/visibility persistence',
                     'rule mutation persistence', 'impact creation with immediate refresh',
                     'task acceptance validation, nested subtask navigation, typed outcomes, scoped phase/source/image interactions and server isolation', 'desktop dark theme only, as requested'],
          'captures':captures,
          'backend': 'real PostgreSQL and ClickHouse; S3 protocol fixture, not Garage'}
(OUT / 'results.json').write_text(json.dumps(report, indent=2))
print(json.dumps({'passed': len(results), 'page_errors': errors, 'captures': len(captures)}))
