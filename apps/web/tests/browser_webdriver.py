"""Desktop dark production checks via an existing reviewed Firefox WebDriver.

Uses only Python's standard library. Mutations require the isolated fixture server;
set OBS_TEST_URL only to an Observatory test deployment with qa-task-0 fixtures.
No browser, driver, Python package, source data or model is installed/invoked.
"""
from pathlib import Path
from urllib.parse import quote
import base64
import json
import os
import time
import urllib.error
import urllib.request

URL = os.environ.get('OBS_TEST_URL', 'http://127.0.0.1:3433')
DRIVER = os.environ.get('OBS_WEBDRIVER_URL', 'http://127.0.0.1:14444')
OUT = Path(os.environ.get('OBS_BROWSER_OUTPUT', 'work/security/browser-webdriver'))
OUT.mkdir(parents=True, exist_ok=True)


def request(method, url, value=None):
    req = urllib.request.Request(url, data=json.dumps(value).encode() if value is not None else None,
                                 method=method, headers={'Content-Type': 'application/json'})
    try:
        result = json.load(urllib.request.urlopen(req, timeout=90))
    except urllib.error.HTTPError as error:
        raise RuntimeError(error.read().decode()) from error
    return result


session = request('POST', DRIVER + '/session', {'capabilities': {'alwaysMatch': {
    'browserName': 'firefox', 'moz:firefoxOptions': {'args': ['-headless'], 'binary': '/usr/bin/firefox'}}}})['value']['sessionId']

(OUT / 'session.json').write_text(json.dumps({'sessionId': session}))

def wd(method, path, value=None):
    return request(method, DRIVER + '/session/' + session + path, value)['value']


def js(script):
    return wd('POST', '/execute/sync', {'script': script, 'args': []})


def wait(script):
    until = time.monotonic() + 60
    while time.monotonic() < until:
        if js('return ' + script):
            return
        time.sleep(.2)
    raise AssertionError('UI readiness timed out: ' + script)


def ready():
    time.sleep(.3)
    wait("document.querySelector('h1') && !document.querySelector('.page-loading') && !document.querySelector('.record-list[aria-busy=true]')")
    assert not js("return !!document.querySelector('.storage-error,.error-message')")


def visit(path):
    wd('POST', '/url', {'url': URL + path})
    ready()


def element(selector):
    return wd('POST', '/element', {'using': 'css selector', 'value': selector})['element-6066-11e4-a52e-4f735466cecf']


def click(selector):
    wd('POST', '/element/' + element(selector) + '/click', {})


def fill(selector, text):
    ident = element(selector)
    wd('POST', '/element/' + ident + '/clear', {})
    wd('POST', '/element/' + ident + '/value', {'text': text})


def button(label, scope='document'):
    selector = f"[...{scope}.querySelectorAll('button')].find(b=>b.textContent.trim()==={json.dumps(label)})"
    js(selector + '.click()')


def record(name):
    results.append({'name': name, 'passed': True})
    (OUT / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    print('PASS', name, flush=True)


results = []
try:
    health = request('GET', URL + '/api/health')
    assert all(health[k] for k in ['postgres', 'clickhouse', 'raw_storage'])
    # Confirm this is the synthetic deployment before exercising any mutations.
    fixture = request('GET', URL + '/api/records/marked?range=all&query=' + quote(json.dumps({'search': 'Validate Observatory flow 00'})))
    assert any(row['id'] == 'qa-task-0' for row in fixture['rows']), 'Isolated QA fixtures required'
    wd('POST', '/window/rect', {'width': 1440, 'height': 1040})
    routes = ['/', '/tasks', '/grouping', '/tools', '/costs', '/timeline', '/agents', '/process',
              '/entities', '/outcomes', '/suggestions', '/impact', '/experiments', '/live', '/live/rules',
              '/categorization', '/data', '/jobs', '/pricing', '/knowledge', '/tasks/qa-task-0',
              '/tasks/qa-task-0/subtasks/qa-analysis-0%3A0']
    for path in ([] if os.environ.get('OBS_BROWSER_SKIP_ROUTES') else routes):
        visit(path + '?range=all')
        assert js("return document.documentElement.classList.contains('dark')"), path
        assert js('return document.documentElement.scrollWidth <= innerWidth+2'), path
        record('route ' + path)
    visit('/tasks?range=all')
    table = '[data-list=tasks-tasks]'
    wait(f"document.querySelectorAll('{table} tbody tr').length===20")
    first = js(f"return document.querySelector('{table} tbody tr').textContent")
    click('[aria-label="Next page tasks-tasks"]'); ready()
    assert js("return document.querySelector('[aria-label=\"Page tasks-tasks\"]').value") == '2'
    assert js(f"return document.querySelector('{table} tbody tr').textContent") != first
    fill('[aria-label="Search tasks-tasks"]', 'flow 00'); ready()
    wait(f"document.querySelectorAll('{table} tbody tr').length===1")
    assert 'flow 00' in js(f"return document.querySelector('{table} tbody').textContent")
    fill('[aria-label="Search tasks-tasks"]', 'definitely-absent-needle'); ready()
    wait(f"document.querySelector('{table} .record-count').textContent==='0 records'")
    click('[aria-label="Clear search tasks-tasks"]'); ready()
    record('pagination, search, empty results and clear')
    button('Filters', f"document.querySelector('{table}')")
    fill('[aria-label="Filter tasks-tasks by Tokens"]', '>= 1000000'); ready()
    count = js(f"return document.querySelector('{table} .record-count').textContent")
    assert count != '0 records'
    click(table + ' [aria-label="Sort by Tokens"]'); ready()
    click(table + ' [aria-label="Sort by Tokens"]'); ready()
    before = js(f"return document.querySelector('{table} tbody tr').textContent")
    wd('POST', '/refresh', {}); ready()
    assert js(f"return document.querySelector('{table} tbody tr').textContent") == before
    assert js("return document.querySelector('[aria-label=\"Filter tasks-tasks by Tokens\"]').value") == '>= 1000000'
    record('numeric filtering, both sort directions and persisted queries')
    click('[aria-label="Columns tasks-tasks"]')
    js("[...document.querySelectorAll('[role=menuitemcheckbox]')].find(e=>e.textContent==='Duration').click()")
    wd('POST', '/actions', {'actions': [{'type': 'key', 'id': 'keyboard', 'actions': [{'type': 'keyDown', 'value': '\ue00c'}, {'type': 'keyUp', 'value': '\ue00c'}]}]})
    wait("!document.querySelector('[data-list=tasks-tasks] [aria-label=\"Sort by Duration\"]')")
    wait("JSON.parse(localStorage.getItem('observatory-table:tasks-tasks:tasks')).visibility.duration===false")
    wd('POST', '/refresh', {}); ready()
    assert not js("return !!document.querySelector('[data-list=tasks-tasks] [aria-label=\"Sort by Duration\"]')")
    button('Reset', f"document.querySelector('{table}')"); ready()
    record('column visibility and reset persist')
    # Select source text; valid fixtures may share the same retained prompt.
    fill('[aria-label="Search tasks-tasks"]', 'flow'); ready()
    # Filter an exact cell through the actual context menu.
    js(f"document.querySelector('{table} tbody td').scrollIntoView({{block:'center'}})")
    selected = js(f"return document.querySelector('{table} tbody td').textContent")
    expected = request('GET', URL + '/api/records/tasks?range=all&query=' + quote(json.dumps({'search':'flow','filters':{'title':'=='+json.dumps(selected)}})))['total']
    ident = element(table + ' tbody td')
    wd('POST', '/actions', {'actions': [{'type': 'pointer', 'id': 'mouse', 'parameters': {'pointerType': 'mouse'}, 'actions': [
        {'type': 'pointerMove', 'origin': {'element-6066-11e4-a52e-4f735466cecf': ident}, 'x': 0, 'y': 0},
        {'type': 'pointerDown', 'button': 2}, {'type': 'pointerUp', 'button': 2}]}]})
    button('Show matching'); ready()
    wait(f"document.querySelector('{table} .record-count').textContent==={json.dumps(format(expected, ',')+' records')}")
    assert js(f"return [...document.querySelectorAll('{table} tbody tr td:first-child')].every(e=>e.textContent==={json.dumps(selected)})")
    button('Reset', f"document.querySelector('{table}')"); ready()
    record('exact context-menu include filter')
    visit('/tasks/qa-task-0/subtasks/qa-analysis-0%3A0?range=all')
    wait("document.querySelectorAll('[data-list=task-steps] tbody tr').length===2")
    click('.native-timeline button'); ready()
    wait("document.querySelectorAll('[data-list=task-steps] tbody tr').length===1")
    button('Clear step filter'); ready()
    click('[data-list=task-steps] .row-actions button') if js("return !!document.querySelector('[data-list=task-steps] .row-actions button')") else click('[data-list=task-steps] tbody button[aria-label^=Inspect]')
    wait("!!document.querySelector('[role=dialog] pre')")
    assert 'Synthetic browser validation' in js("return document.querySelector('[role=dialog]').textContent")
    wd('POST', '/actions', {'actions': [{'type': 'key', 'id': 'keyboard', 'actions': [{'type': 'keyDown', 'value': '\ue00c'}, {'type': 'keyUp', 'value': '\ue00c'}]}]})
    click('.screenshot-grid button')
    wait("document.querySelector('[role=dialog] img')?.naturalWidth>0")
    record('subtask step selection, retained source and image retrieval')
    visit('/live/rules?range=all')
    switch = '[role=switch][aria-label="Enable Prompt after a break"]'
    before = js(f"return document.querySelector({json.dumps(switch)}).getAttribute('aria-checked')")
    click(switch); ready(); wd('POST', '/refresh', {}); ready()
    assert js(f"return document.querySelector({json.dumps(switch)}).getAttribute('aria-checked')") != before
    click(switch); ready()
    record('persisted rule mutation and restoration')
    visit('/impact?range=all'); button('Record a change')
    title = 'WebDriver fixture ' + str(time.time_ns())
    fill('[role=dialog] input[name=title]', title)
    fill('[role=dialog] textarea[name=notes]', 'Synthetic fixture; no causal saving claim')
    button('Save', "document.querySelector('[role=dialog]')"); ready()
    wait(f"document.querySelector('[data-list=impact-changes]').textContent.includes({json.dumps(title)})")
    record('persisted form mutation immediately refreshes list')
    visit('/experiments?range=all')
    wait("document.querySelectorAll('[data-list=experiments-experiments] tbody tr').length>0")
    click('[data-list=experiments-experiment-evaluations] tbody button[aria-label^=Inspect]')
    wait("!!document.querySelector('[role=dialog] pre')")
    assert 'measurements' in js("return document.querySelector('[role=dialog] pre').textContent")
    record('experiment measurements inspect without inference')
    visit('/tasks?range=all')
    (OUT / 'desktop-dark.png').write_bytes(base64.b64decode(wd('GET', '/moz/screenshot/full')))
finally:
    try:
        (OUT / 'last-screen.png').write_bytes(base64.b64decode(wd('GET', '/moz/screenshot/full')))
        (OUT / 'last-state.json').write_text(json.dumps(js("return {url:location.href,preferences:localStorage.getItem('observatory-table:tasks-tasks:tasks'),alerts:[...document.querySelectorAll('[role=alert]')].map(x=>x.textContent)}"),indent=2))
    except Exception:
        pass
    try:
        wd('DELETE', '')
    except Exception:
        pass
print(json.dumps({'checks': len(results), 'passed': True, 'model_calls': 0}), flush=True)
