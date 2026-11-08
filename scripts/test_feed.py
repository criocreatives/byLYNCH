"""Exercise the complete paginated feed, archive filters and card hover."""
import os
from visual_regression import serve
from playwright.sync_api import sync_playwright
from pathlib import Path
with serve(Path(__file__).resolve().parents[1] / '_site') as url, sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_EXECUTABLE'),args=['--no-sandbox'])
 for width in [390,1440]:
  ctx=browser.new_context(viewport={'width':width,'height':900})
  page=ctx.new_page();page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(url) else r.abort())
  page.goto(url);page.wait_for_load_state('load')
  for step in range(8):
   previous=page.locator('[data-post-feed]>.hentry').count()
   if not page.locator('.older-posts-wrap').count():break
   page.evaluate('scrollTo(0,document.body.scrollHeight)')
   page.wait_for_function('(n)=>document.querySelectorAll("[data-post-feed]>.hentry").length>n || !document.querySelector(".older-posts-wrap")',arg=previous,timeout=15000)
  cards=page.locator('[data-post-feed]>.hentry');assert cards.count()==58,(width,cards.count())
  links=cards.locator('.entry-title a').evaluate_all('els=>els.map(e=>e.pathname)');assert len(set(links))==58
  assert page.locator('[data-post-feed]>.bylynch-home-grid-ad').count()==9
  assert cards.locator('.content-rating-badge').count()==10
  cadence=page.locator('[data-post-feed]').evaluate('feed=>{let n=0;return [...feed.children].filter(e=>{if(e.classList.contains("hentry")){n++;return false}return e.matches("[data-home-grid-ad]")&&n%6!==0}).length}')
  assert cadence==0
  page.goto(url+'/archive/?cat=FILM');page.wait_for_load_state('load')
  visible=page.locator('.site-main>.hentry:visible');assert visible.count()>0
  assert visible.evaluate_all('els=>els.every(e=>e.dataset.categories.toLowerCase().split("||").includes("film"))')
  page.goto(url);page.wait_for_load_state('load')
  clipped=page.locator('.has-clipped-excerpt').first;clipped.hover();page.wait_for_timeout(650)
  assert clipped.locator('.entry-summary p').evaluate('e=>getComputedStyle(e).webkitLineClamp')=='none'
  ctx.close();print('PASS extra interactions:',width,'58 unique cards, 9 ads at exact cadence, 10 E badges, filter and hover')
 browser.close()
