"""Production Next.js browser checks against synthetic, isolated DB/S3 fixtures."""
import json,os,pathlib,time,re
from playwright.sync_api import sync_playwright,expect
BASE=os.environ.get('OBS_TEST_URL','http://127.0.0.1:3433')
OUT=pathlib.Path('work/security/next-migration-20261115/browser');OUT.mkdir(parents=True,exist_ok=True)
PAGES={'/':'Overall activity','/tasks':'Task activity','/grouping':'Task grouping','/tools':'Tool usage','/costs':'Cost & tokens','/timeline':'Activity timeline','/agents':'Agents','/process':'Process map','/entities':'Entities','/outcomes':'Outcomes','/suggestions':'Suggestions','/impact':'Impact','/live':'Live sessions','/live/rules':'Steering rules','/categorization':'Categorization','/data':'Data list','/jobs':'Mining jobs','/pricing':'Pricing','/knowledge':'Knowledge','/tasks/qa-task-0':'Validate Observatory flow 00'}
results=[];errors=[]
with sync_playwright()as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
 page.on('pageerror',lambda e:errors.append(str(e)))
 for route,title in PAGES.items():
  started=time.monotonic();page.goto(BASE+route+'?range=all',wait_until='networkidle');expect(page.get_by_role('heading',name=title,exact=True,level=1)).to_be_visible();expect(page.locator('.storage-error')).to_have_count(0);expect(page.locator('.record-list[aria-busy=true]')).to_have_count(0);expect(page.get_by_role('alert').filter(has_text=re.compile(r'\S'))).to_have_count(0)
  page.screenshot(path=str(OUT/((route.strip('/').replace('/','-')or'overview')+'-dark.png')),full_page=True)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2'),route+' desktop overflow'
  results.append({'route':route,'seconds':round(time.monotonic()-started,3),'tables':page.locator('[data-list]').count()})
 # Full-cohort search, column filters, natural sort and built-in pagination.
 page.goto(BASE+'/tasks?range=all',wait_until='networkidle');table=page.locator('[data-list="tasks-tasks"]');expect(table.locator('tbody tr')).to_have_count(20);first_before=table.locator('tbody tr').first.inner_text();total_before=table.locator('.record-count').inner_text()
 table.get_by_role('button',name='Next page tasks-tasks',exact=True).click();expect(table.locator('.page-jump input')).to_have_value('2');expect(table.locator('tbody tr').first).not_to_have_text(first_before)
 table.get_by_role('textbox',name='Search tasks-tasks',exact=True).fill('flow 00');expect(table.locator('tbody tr')).to_have_count(1);expect(table.locator('tbody')).to_contain_text('flow 00')
 table.get_by_role('button',name='Clear search tasks-tasks',exact=True).click();expect(table.locator('tbody tr')).to_have_count(20)
 table.get_by_role('button',name='Filters',exact=True).click();table.get_by_role('textbox',name='Filter tasks-tasks by Tokens',exact=True).fill('>= 1000000');expect(table.locator('.record-count')).not_to_have_text(total_before);table.get_by_role('button',name='Reset',exact=True).click()
 table.get_by_role('button',name='Sort by Started',exact=True).click();expect(table.get_by_role('button',name='Sort by Started',exact=True)).to_have_attribute('aria-pressed','true')
 table.get_by_role('button',name='Columns tasks-tasks',exact=True).click();page.get_by_role('menuitemcheckbox',name='Tokens',exact=True).click();page.keyboard.press('Escape');expect(table.get_by_role('button',name='Sort by Tokens',exact=True)).to_have_count(0)
 page.reload(wait_until='networkidle');expect(table.get_by_role('button',name='Sort by Tokens',exact=True)).to_have_count(0)
 # Rule settings persist through the actual mutation API.
 page.goto(BASE+'/live/rules?range=all',wait_until='networkidle');switch=page.get_by_role('switch',name='Enable Prompt after a break',exact=True);before=switch.get_attribute('aria-checked');switch.click();expect(switch).to_have_attribute('aria-checked','false' if before=='true' else 'true');page.reload(wait_until='networkidle');expect(switch).to_have_attribute('aria-checked','false' if before=='true' else 'true');switch.click();expect(switch).to_have_attribute('aria-checked',before)
 # Explicit change form and comparison card.
 page.goto(BASE+'/impact?range=all',wait_until='networkidle');page.get_by_role('button',name='Record a change',exact=True).click();dialog=page.get_by_role('dialog');dialog.get_by_label('What did you change?',exact=True).fill('Browser validation change');dialog.get_by_label('Notes and evidence',exact=True).fill('Synthetic fixture; no causal performance claim');dialog.get_by_role('button',name='Save',exact=True).click();expect(dialog).not_to_be_visible();expect(page.locator('[data-list="impact-changes"]')).to_contain_text('Browser validation change')
 # Task source inspector and phase filter.
 page.goto(BASE+'/tasks/qa-task-0?range=all',wait_until='networkidle');steps=page.locator('[data-list="task-steps"]');expect(steps.locator('tbody tr')).to_have_count(8);page.locator('.phase-track button').first.click();expect(steps.locator('tbody tr')).to_have_count(2);page.get_by_role('button',name='Clear phase / step filter',exact=True).click();expect(steps.locator('tbody tr')).to_have_count(8);steps.get_by_role('button',name='Inspect',exact=False).first.click();expect(page.get_by_role('dialog')).to_contain_text('Synthetic browser validation');page.keyboard.press('Escape')
 page.locator('.screenshot-grid button').first.click();expect(page.get_by_role('dialog').locator('img')).to_be_visible();assert page.get_by_role('dialog').locator('img').evaluate('(img)=>img.complete&&img.naturalWidth>0');page.keyboard.press('Escape')
 # Theme and phone layout are checked for every reference view.
 for route,title in list(PAGES.items())[:14]:
  page.goto(BASE+route+'?range=all',wait_until='networkidle');
  if page.locator('html').get_attribute('class')=='dark':page.get_by_role('button',name='Switch to light theme',exact=True).first.click();expect(page.locator('html')).not_to_have_class('dark');page.screenshot(path=str(OUT/((route.strip('/').replace('/','-')or'overview')+'-light.png')),full_page=True)
  page.set_viewport_size({'width':390,'height':844});page.reload(wait_until='networkidle');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2'),route+' mobile overflow';expect(page.get_by_role('heading',name=title,exact=True,level=1)).to_be_visible();page.screenshot(path=str(OUT/((route.strip('/').replace('/','-')or'overview')+'-mobile.png')),full_page=True);page.set_viewport_size({'width':1440,'height':1000})
 browser.close()
assert not errors,errors
(OUT/'results.json').write_text(json.dumps({'pages':results,'page_errors':errors,'checks':['20 routes desktop','shared search/filter/sort/pagination/visibility persistence','rule mutation persistence','impact creation','task phase/source/image interactions','14 light and mobile routes'],'backend':'real PostgreSQL and ClickHouse; S3 protocol fixture, not Garage'},indent=2))
print(json.dumps({'passed':len(results),'page_errors':errors,'captures':len(list(OUT.glob('*.png')))}))
