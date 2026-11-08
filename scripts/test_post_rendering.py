#!/usr/bin/env python3
"""Browser fixtures for legacy compatibility, separate from masonry geometry."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from visual_regression import serve

FIXTURE = '''<div class="bk-redesign"><div class="entry-content">
Loose <em>editorial</em> text.<hr><p>…</p>
<div class="wp-block-gallery" id="legacy-gallery">
  <figure style="color: red"><a href="#credit"><picture><source type="image/webp" srcset="/photo.webp"><img src="/photo.jpg" alt=""></picture></a><figcaption>Original credit</figcaption></figure>
  <figure><img src="/second.jpg" alt=""><figcaption>Second caption</figcaption></figure>
</div>
<p>Text between photographs <a href="#credit">linked credit</a></p>
<p><picture><source srcset="/modern.webp"><img src="/modern.jpg" alt=""></picture></p>
<ul><li>Authored list</li></ul>
<div class="soundcloud-embed"><iframe src="https://w.soundcloud.com/player/" height="166"></iframe><p>Audio credit</p></div>
<div><iframe src="https://www.youtube.com/embed/example"></iframe></div>
<video controls></video>
<div class="wp-block-gallery"><p>Do not lose this gallery introduction</p><figure><img src="/mixed1.jpg"></figure><figure><img src="/mixed2.jpg"></figure></div>
</div></div>'''


def main():
    root = Path(__file__).resolve().parents[1]
    with serve(root) as url, sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_EXECUTABLE'), args=['--no-sandbox'])
        page = browser.new_page()
        page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(url) else route.abort())
        page.goto(url)
        page.set_content(FIXTURE)
        result = page.evaluate('''async () => {
          const {prepareGallery} = await import('/assets/js/post.js');
          const grid = document.querySelector('.entry-content');
          const original = [...grid.querySelectorAll('img,picture,source,a,figcaption,iframe,video,ul,hr,em')];
          const attributes = original.map(node=>[...node.attributes].map(a=>[a.name,a.value]));
          const text = grid.textContent.replace(/\\s+/g,' ').trim();
          prepareGallery(grid);
          const once = grid.innerHTML;
          prepareGallery(grid);
          return {
            nodesPreserved:original.every(node=>grid.contains(node)),
            attributesPreserved:original.every((node,i)=>attributes[i].every(([k,v])=>node.getAttribute(k)===v)),
            textPreserved:grid.textContent.replace(/\\s+/g,' ').trim()===text,
            idempotent:once===grid.innerHTML,
            embeds:grid.querySelectorAll('.full-width-embed').length,
            mixedCopy:grid.querySelector('.wp-block-gallery p')?.textContent
          };
        }''')
        browser.close()
    assert all(result[k] for k in ['nodesPreserved', 'attributesPreserved', 'textPreserved', 'idempotent']), result
    assert result['embeds'] == 2, result
    assert result['mixedCopy'] == 'Do not lose this gallery introduction', result
    print('PASS: legacy galleries, picture/srcset, captions, lists, embeds, text and node identity; idempotent preparation')


if __name__ == '__main__':
    main()
