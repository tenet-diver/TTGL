"""Reusable list behavior without the workspace shell or page-specific handlers."""
import os
import unittest
import test_workspace_browser


@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA')=='1','Opt-in browser QA')
class DataListBrowserTests(unittest.TestCase):
    def fixture(self):
        host=test_workspace_browser.WorkspaceBrowserTests();_,origin,_=host.fixture();self.addCleanup(host.doCleanups)
        return origin

    def test_standalone_paging_search_filters_sort_nulls_preferences_and_row_actions(self):
        from playwright.sync_api import sync_playwright,expect
        origin=self.fixture()
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1280,'height':900});page.set_default_timeout(5000)
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.route('**/list-fixture',lambda route:route.fulfill(content_type='text/html',body='<!doctype html><link rel="stylesheet" href="/ui.css"><link rel="stylesheet" href="/workspace.css"><main style="margin:16px"><form id="fixture-form"><div id="records"></div></form><div id="second"></div></main>'))
            page.goto(origin+'/list-fixture')
            mount='''async () => {
              const {renderList}=await import('/data-list.js');window.submits=0;document.querySelector('form').onsubmit=e=>{e.preventDefault();window.submits++;};
              const rows=Array.from({length:55},(_,i)=>({id:i,title:'Row '+String(i).padStart(2,'0'),value:i===14?null:i,notes:i===42?'Hidden résumé marker':'Ordinary'}));
              const cols=[{key:'title',label:'Name'},{key:'value',label:'Amount',numeric:true},{key:'notes',label:'Notes',hiddenByDefault:true}];
              document.querySelector('#records').innerHTML=renderList('fixture-list',cols,rows,r=>[{id:'open',label:'Open row',onSelect:()=>window.opened=r.id}]);
              document.querySelector('#second').innerHTML=renderList('second-list',cols,rows.slice(0,3),null);
            }'''
            page.evaluate(mount)
            table=page.locator('[data-table="fixture-list"]')
            expect(table.locator('tbody tr')).to_have_count(20)
            table.get_by_role('button',name='Next',exact=True).click()
            expect(table.locator('tbody tr').first).to_contain_text('Row 20')
            table.get_by_role('button',name='Actions for Row 20',exact=True).click()
            page.get_by_role('menuitem',name='Open row',exact=True).click()
            self.assertEqual(page.evaluate('window.opened'),20)
            table.get_by_label('Rows per page fixture-list',exact=True).select_option('50')
            expect(table.locator('tbody tr')).to_have_count(50)
            table.get_by_label('Page fixture-list',exact=True).fill('2');page.keyboard.press('Enter')
            expect(table.locator('tbody tr')).to_have_count(5)
            table.get_by_label('Filter fixture-list by Amount',exact=True).fill('>= 50')
            expect(table.locator('tbody tr')).to_have_count(5)
            expect(table.get_by_label('Page fixture-list',exact=True)).to_have_value('1')
            table.get_by_role('button',name='Reset table',exact=True).click()
            table.get_by_label('Rows per page fixture-list',exact=True).select_option('100')
            table.get_by_role('button',name='Sort by Amount',exact=True).click()
            expect(table.locator('tbody tr').last).to_contain_text('Row 14')
            table.get_by_role('button',name='Sort by Amount',exact=True).click()
            expect(table.locator('tbody tr').first).to_contain_text('Row 54')
            expect(table.locator('tbody tr').last).to_contain_text('Row 14')
            table.get_by_role('textbox',name='Search fixture-list',exact=True).fill('resume marker')
            expect(table.locator('tbody tr')).to_have_count(1);expect(table.locator('tbody tr')).to_contain_text('Row 42')
            page.keyboard.press('Enter');self.assertEqual(page.evaluate('window.submits'),0)
            expect(page.locator('[data-table="second-list"] tbody tr')).to_have_count(3)
            page.reload();page.evaluate(mount)
            expect(page.get_by_label('Rows per page fixture-list',exact=True)).to_have_value('100')
            expect(page.get_by_role('textbox',name='Search fixture-list',exact=True)).to_have_value('resume marker')
            page.get_by_role('textbox',name='Search fixture-list',exact=True).fill('unmatched query')
            expect(page.locator('[data-table="fixture-list"]')).to_contain_text('No matching rows')
            page.locator('[data-table="fixture-list"]').get_by_role('button',name='Clear search and filters',exact=True).click()
            expect(page.locator('[data-table="fixture-list"] tbody tr')).to_have_count(20)
            self.assertEqual(errors,[]);browser.close()

    def test_column_picker_escapes_nested_scroll_and_saves_visibility(self):
        from playwright.sync_api import sync_playwright,expect
        origin=self.fixture()
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':390,'height':844})
            page.route('**/nested-fixture',lambda route:route.fulfill(content_type='text/html',body='<link rel="stylesheet" href="/ui.css"><link rel="stylesheet" href="/workspace.css"><div style="max-height:180px;overflow:auto"><div id="nested"></div></div><section style="height:500px">Later content</section>'))
            page.goto(origin+'/nested-fixture')
            page.evaluate("""async()=>{const {renderList}=await import('/data-list.js');const columns=Array.from({length:19},(_,i)=>({key:'field'+i,label:'Field '+i,hiddenByDefault:i>2}));document.querySelector('#nested').innerHTML=renderList('nested-list',columns,[{field0:'<img src=x onerror=alert(1)>',field18:'Visible after toggle'}],null);}""")
            picker=page.locator('.column-picker');picker.locator('summary').click()
            expect(picker.locator('.column-options')).to_be_visible()
            picker.get_by_role('checkbox',name='Show nested-list column Field 18',exact=True).check()
            expect(page.locator('[data-table="nested-list"] thead')).to_contain_text('Field 18')
            page.keyboard.press('Escape')
            expect(picker.locator('.column-options')).not_to_be_visible()
            expect(page.locator('img')).to_have_count(0)
            stored=page.evaluate("JSON.parse(localStorage.getItem('ttgl-table-settings-v1'))['nested-list']")
            self.assertNotIn('field18',stored['hiddenColumns'])
            browser.close()

    def test_selection_survives_page_search_and_sort_without_submitting_parent_form(self):
        from playwright.sync_api import sync_playwright,expect
        origin=self.fixture()
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page();page.route('**/selection-fixture',lambda route:route.fulfill(content_type='text/html',body='<link rel="stylesheet" href="/ui.css"><link rel="stylesheet" href="/workspace.css"><form id="choices"><div id="records"></div></form>'))
            page.goto(origin+'/selection-fixture')
            page.evaluate('''async()=>{const {renderList,selectionColumn,selectedIds}=await import('/data-list.js');window.selectedIds=selectedIds;window.submits=0;document.querySelector('form').onsubmit=e=>{e.preventDefault();window.submits++;};const rows=Array.from({length:45},(_,i)=>({id:String(i),title:'Choice '+i}));document.querySelector('#records').innerHTML=renderList('selection-list',[selectionColumn('selection-list',{limit:2}),{key:'title',label:'Title'}],rows,null);}''')
            table=page.locator('[data-table="selection-list"]')
            table.get_by_role('checkbox',name='Choice 0',exact=True).check()
            table.get_by_role('button',name='Next',exact=True).click()
            table.get_by_role('checkbox',name='Choice 20',exact=True).check()
            self.assertEqual(page.evaluate("window.selectedIds('selection-list')"),['0','20'])
            table.get_by_role('textbox',name='Search selection-list',exact=True).fill('Choice 0')
            expect(table.get_by_role('checkbox',name='Choice 0',exact=True)).to_be_checked()
            expect(table.locator('[data-list-selection-count]')).to_have_text('2 selected')
            self.assertEqual(page.evaluate('window.submits'),0)
            browser.close()


if __name__=='__main__':unittest.main()
