#!/usr/bin/env python3
"""Check actual article layout without JavaScript and with a failed photograph."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from visual_regression import serve


def main():
    site = Path(__file__).resolve().parents[1] / '_site'
    with serve(site) as url, sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_EXECUTABLE'), args=['--no-sandbox'])
        for width, columns in [(390, 1), (768, 2), (1440, 3)]:
            context = browser.new_context(java_script_enabled=False, viewport={'width': width, 'height': 900})
            page = context.new_page()
            page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(url) else route.abort())
            for route in ['/2026/11/01/rafjam/', '/2017/01/04/hermina/', '/2022/08/01/bk/']:
                page.goto(url + route)
                grid = page.locator('.entry-content')
                measured = grid.evaluate('el=>({display:getComputedStyle(el).display,cols:getComputedStyle(el).gridTemplateColumns.split(" ").length,height:el.getBoundingClientRect().height})')
                assert measured['display'] == 'grid' and measured['cols'] == columns and measured['height'] > 100, (route, width, measured)
                assert page.locator('.entry-content img').count() > 0
            context.close()
        page = browser.new_page(viewport={'width': 390, 'height': 844})
        page.route('**/*', lambda route: route.abort() if '/assets/uploads/2026/11/IMG_0676.webp' in route.request.url or not route.request.url.startswith(url) else route.continue_())
        page.goto(url + '/2026/11/01/rafjam/')
        page.wait_for_function("document.querySelector('.masonry-initialized')")
        # A broken photo must not collapse or stop positioning later gallery items.
        failed = page.locator('.entry-content img[src*="IMG_0676.webp"]')
        assert failed.evaluate('img=>img.complete && img.naturalWidth===0'), 'Fixture must actually fail the photo request'
        heights = page.locator('.entry-content > figure').evaluate_all('els=>els.map(e=>e.getBoundingClientRect().height)')
        assert all(h > 0 for h in heights), heights
        browser.close()
    print('PASS: 1/2/3-column no-JS fallback and masonry after an image error')


if __name__ == '__main__':
    main()
