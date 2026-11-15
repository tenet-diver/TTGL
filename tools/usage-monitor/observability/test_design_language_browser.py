"""Computed Vercel-reference styles, contrast and native interaction regression checks."""
import os
from pathlib import Path
import unittest
import test_usage_views_browser


def luminance(rgb):
    parts=[v/255 for v in rgb]
    parts=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in parts]
    return sum(a*b for a,b in zip(parts,(.2126,.7152,.0722)))


def contrast(first,second):
    light,dark=sorted((luminance(first),luminance(second)),reverse=True)
    return (light+.05)/(dark+.05)


@unittest.skipUnless(os.environ.get('TTGL_BROWSER_QA')=='1','Opt-in browser QA')
class DesignLanguageBrowserTests(unittest.TestCase):
    def fixture(self):
        host=test_usage_views_browser.UsagePagesBrowserTests();f,origin,task=host.fixture();self.addCleanup(host.doCleanups)
        return f,origin,task

    def test_surfaces_typography_status_dots_and_keyboard_focus(self):
        from playwright.sync_api import sync_playwright,expect
        _,origin,_=self.fixture()
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1000});page.goto(origin+'/?range=all')
            expect(page.locator('h1')).to_have_text('Overall activity')
            page.evaluate('''async()=>{const {button,badge}=await import('/ui.js');const host=document.createElement('section');host.id='style-fixture';host.innerHTML=button('Primary fixture','id="primary-fixture"',true)+button('Ghost fixture','id="ghost-fixture"')+'<input id="style-input" class="ui-input" aria-label="Style input">'+badge('completed')+badge('failed')+badge('waiting');document.querySelector('#content').prepend(host);}''')
            for theme in ('light','dark'):
                page.locator('html').evaluate('(node,theme)=>node.dataset.theme=theme',theme)
                body=page.locator('body').evaluate('(node)=>{const s=getComputedStyle(node);return {background:s.backgroundColor,color:s.color,font:s.fontFamily,weight:s.fontWeight}}')
                self.assertEqual(body['background'],'rgb(250, 250, 250)' if theme=='light' else 'rgb(10, 10, 10)')
                self.assertIn('Geist',body['font']);self.assertEqual(body['weight'],'400')
                card=page.locator('.ops-card').first.evaluate('(node)=>{const s=getComputedStyle(node);return {border:s.borderTopWidth,shadow:s.boxShadow,radius:s.borderRadius}}')
                self.assertEqual(card['border'],'0px');self.assertIn('1px',card['shadow']);self.assertEqual(card['radius'],'12px')
                heading=page.locator('h1').evaluate('(node)=>{const s=getComputedStyle(node);return [s.fontSize,s.fontWeight,s.letterSpacing]}')
                self.assertEqual(heading,['32px','600','-1.28px'])
                self.assertEqual(page.locator('.page-header').evaluate("node=>getComputedStyle(node,'::before').content"),'none')
                for badge in page.locator('#style-fixture .ui-badge').all():
                    style=badge.evaluate("node=>{const s=getComputedStyle(node),dot=getComputedStyle(node,'::before');return {background:s.backgroundColor,color:s.color,dot:[dot.width,dot.height,dot.borderRadius]}}")
                    self.assertEqual(style['background'],'rgba(0, 0, 0, 0)')
                    self.assertEqual(style['dot'],['8px','8px','50%'])
                    self.assertEqual(style['color'],body['color'])
                button=page.locator('#ghost-fixture');before=button.bounding_box();button.hover()
                self.assertEqual(button.bounding_box(),before)
                button.focus();page.keyboard.press('Tab');page.keyboard.press('Shift+Tab')
                focus=button.evaluate('node=>({shadow:getComputedStyle(node).boxShadow,transform:getComputedStyle(node).transform})')
                self.assertIn('2px',focus['shadow']);self.assertIn('4px',focus['shadow']);self.assertEqual(focus['transform'],'none')
                page.locator('#style-input').focus()
                self.assertEqual(page.locator('#style-input').evaluate('node=>getComputedStyle(node).outlineWidth'),'1px')
                primary=page.locator('#primary-fixture');primary.hover();page.mouse.down()
                pressed=primary.evaluate('node=>({background:getComputedStyle(node).backgroundColor,color:getComputedStyle(node).color,transform:getComputedStyle(node).transform})');page.mouse.up()
                self.assertNotEqual(pressed['background'],pressed['color']);self.assertEqual(pressed['transform'],'none')
                gradients=page.evaluate("[...document.querySelectorAll('*')].filter(node=>getComputedStyle(node).backgroundImage.includes('gradient(')).length")
                self.assertEqual(gradients,0)
                self.assertEqual(page.evaluate("[...document.querySelectorAll('*')].some(node=>Number(getComputedStyle(node).fontWeight)>600)"),False)
            browser.close()

    def test_data_fills_have_readable_labels_and_category_color_is_dot_sized(self):
        from playwright.sync_api import sync_playwright,expect
        _,origin,_=self.fixture()
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page();page.goto(origin+'/tools?range=all')
            expect(page.locator('.tool-treemap button')).to_have_count(3)
            for theme in ('light','dark'):
                page.locator('html').evaluate('(node,theme)=>node.dataset.theme=theme',theme)
                tiles=page.locator('.tool-treemap button').evaluate_all("nodes=>nodes.map(node=>{const s=getComputedStyle(node),rgb=v=>(v.match(/[\\d.]+/g)||[]).slice(0,3).map(Number);return {background:rgb(s.backgroundColor),color:rgb(s.color)}})")
                for tile in tiles:
                    self.assertGreater(len(set(tile['background'])),1)
                    self.assertGreaterEqual(contrast(tile['background'],tile['color']),4.5)
            page.locator('nav [data-view="process"]').click()
            expect(page.locator('.category-chip')).not_to_have_count(0)
            for dot in page.locator('.category-chip>span').all():
                self.assertLessEqual(dot.bounding_box()['width'],10)
                self.assertLessEqual(dot.bounding_box()['height'],10)
            browser.close()

    def test_reference_layout_stays_responsive_across_critical_widths(self):
        from playwright.sync_api import sync_playwright,expect
        _,origin,_=self.fixture()
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('TTGL_CHROMIUM','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page();page.goto(origin+'/?range=all');errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            artifacts=Path('work/security/design-language-qa');artifacts.mkdir(parents=True,exist_ok=True)
            for theme in ('light','dark'):
                page.locator('html').evaluate('(node,theme)=>node.dataset.theme=theme',theme)
                for width in (370,600,768,960,1200,1600):
                    page.set_viewport_size({'width':width,'height':1000})
                    for view in ('overview','taskactivity','tools','costs'):
                        page.locator(f'nav [data-view="{view}"]').click()
                        expect(page.locator(f'nav [data-view="{view}"]')).to_have_attribute('aria-current','page')
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
                    if width in (370,1600):page.screenshot(path=str(artifacts/f'costs-{theme}-{width}.png'),full_page=True,animations='disabled')
            self.assertEqual(errors,[]);browser.close()


if __name__=='__main__':unittest.main()
