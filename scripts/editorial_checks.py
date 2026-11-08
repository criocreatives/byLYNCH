"""Named editorial regression fixtures; general invariants live in check_site.py."""
import json
import re

def check_editorial(*, ROOT, SITE, check, rendered, inspect, post_urls, archive_html, flagged, people_data):
    # Hermina: public original gallery, original card/hero photograph, E classification,
    # restored historical metadata, indexed normally and no AdSense anywhere on article.
    hermina_url = "/2017/01/04/hermina/"
    hermina_html = rendered(hermina_url).read_text(encoding="utf-8")
    hermina_source = (ROOT / "_posts" / "2017-01-04-hermina.md").read_text(encoding="utf-8")
    check('layout: post' in hermina_source and
          'date: 2017-01-04 03:00:51 -0500' in hermina_source,
          "Hermina original publication date/layout missing")
    check('protected:' not in hermina_source and 'hermina-password-form' not in hermina_html,
          "Old Hermina password protection remains")
    check('<meta name="robots" content="noindex' not in hermina_html,
          "Public Hermina must not contain noindex")
    check('<h1 class="entry-title">Hermina</h1>' in hermina_html,
          "Hermina heading missing")
    check('class="content-rating-badge"' in hermina_html,
          "Hermina E badge missing")
    check("pagead2.googlesyndication.com" not in hermina_html
          and "google-adsense-account" not in hermina_html
          and '<ins class="adsbygoogle"' not in hermina_html,
          "Hermina must not load AdSense on its article")
    check(hermina_html.count('/assets/uploads/2016/12/img_4444.webp') >= 1,
          "Original Hermina featured photo missing")
    check("Have you ever danced with the devil" in hermina_html and
          "Fin." in hermina_html,
          "Original Hermina text missing")
    check(len(re.findall(r'<img[^>]+src="/assets/uploads/2016/12/[^"]+\.webp"', hermina_html)) >= 12,
          "Hermina should contain its twelve original article photos")
    check("2017/01/04/hermina/" in (SITE / "sitemap.xml").read_text(encoding="utf-8"),
          "Public Hermina missing from sitemap")
    check('"slug": "hermina"' in (SITE / "search.json").read_text(encoding="utf-8"),
          "Public Hermina missing from search index")
    check(not (SITE / "assets" / "protected" / "hermina").exists(),
          "Encrypted Hermina files must not ship")
    check(not (SITE / "assets" / "js" / "hermina-protected.js").exists(),
          "Old Hermina password script must not ship")
    check(not (SITE / "assets" / "uploads" / "2016" / "12" / "hermina-locked.jpg").exists(),
          "Old locked placeholder image must not ship")
    for name in (
        "img_9525d.webp", "img_443921.webp", "img_4443.webp", "img_9756-g.webp",
        "img_4445.webp", "img_4446.webp", "img_4449-2.webp", "img_4448-2.webp",
        "img_7662.webp", "img_7661.webp", "img_44g79.webp", "img_4447.webp",
        "img_4444.webp",
    ):
        check((SITE / "assets" / "uploads" / "2016" / "12" / name).is_file(),
              "Original Hermina photograph missing: " + name)


    # Kosher's Everything: preserve all 18 originals and the two designated images.
    kosher_source = ROOT / "_posts" / "2020-11-29-koshers-everything.md"
    check(kosher_source.is_file(), "Kosher source article missing")
    if kosher_source.is_file():
        source = kosher_source.read_text(encoding="utf-8")
        chunks = source.split("\n---\n", 1)
        front, gallery = chunks if len(chunks) == 2 else (source, "")
        images = re.findall(r'<img src="(/assets/uploads/2020/11/[^"]+)"', gallery)
        webps = re.findall(r'<source type="image/webp" srcset="([^"]+)"', gallery)
        check(len(images) == 18 and len(set(images)) == 18,
              "Kosher gallery must contain 18 distinct original photographs")
        check(len(webps) == 18 and len(set(webps)) == 18,
              "Kosher gallery must contain 18 distinct WebP sources")
        for img in images:
            check((ROOT / img.lstrip("/")).is_file(),
                  "Missing original Kosher image: " + img)
            check((SITE / img.lstrip("/")).is_file(),
                  "Original Kosher image absent from site: " + img)
        for webp in webps:
            check((ROOT / webp.lstrip("/")).is_file(),
                  "Missing optimized Kosher image: " + webp)
            check((SITE / webp.lstrip("/")).is_file(),
                  "Optimized Kosher image absent from site: " + webp)
        card = "/assets/uploads/2020/11/mg_5112.jpg"
        header = "/assets/uploads/2020/11/IMG_9050.jpg"
        check(card in images and header in images,
              "Kosher gallery must include both card and header photographs")
        check('header_image: "2020/11/IMG_9050.jpg"' in front,
              "Wrong custom Kosher header image")
        check('featured_people:\n  - kosher' in front,
              "Kosher featured_people metadata missing")
        check('exclude_ads: true' not in front and 'exclude_ads: false' not in front,
              "Kosher should inherit standard ad eligibility from the shared post template")
        url = post_urls.get("koshers-everything")
        check(bool(url), "Kosher's Everything permalink missing")
        if url:
            html, parsed = inspect(url)
            check('src="' + header + '"' in html,
                  "Kosher header image missing on post page")
            check('src="' + card + '"' in archive_html,
                  "Kosher archive card image missing")
            check('class="lynch-credits"' in html and "Kosher" in html,
                  "Kosher People & Credits section missing")
            check(html.count("pagead2.googlesyndication.com/pagead/js/adsbygoogle.js") == 1,
                  "Kosher post must load the AdSense publisher script exactly once")
            check(html.count('<ins class="adsbygoogle"') == 2,
                  "Kosher post must render its two standard manual ad units")
            check('data-ad-slot="9856514493"' in html,
                  "Kosher metadata ad placement missing")
            check('data-ad-slot="7038779463"' in html,
                  "Kosher after-gallery ad placement missing")
            check('class="content-rating-badge"' not in html,
                  "Kosher post must not get the nudity E badge")
            blog = [json.loads(j) for j in parsed.ld_json]
            check(any(b.get("@type") == "BlogPosting" and
                      any(m.get("name") == "Kosher" for m in b.get("mentions", []))
                      for b in blog), "Kosher schema Person mention missing")

    # Setsuna: new replacement photo archive, independent card/hero and standard ads.
    setsuna_source = ROOT / "_posts" / "2024-10-26-setsuna.md"
    check(setsuna_source.is_file(), "Setsuna source post missing")
    if setsuna_source.is_file():
        source = setsuna_source.read_text(encoding="utf-8")
        sections = source.split("\n---\n", 1)
        front, gallery = sections if len(sections) == 2 else (source, "")
        originals = re.findall(r'<img src="(/assets/uploads/2024/10/[^"]+)"', gallery)
        webps = re.findall(r'<source type="image/webp" srcset="([^"]+)"', gallery)
        check(len(originals) == 13 and len(set(originals)) == 13,
              "Setsuna must contain 13 distinct originals")
        check(len(webps) == 13 and len(set(webps)) == 13,
              "Setsuna must contain 13 distinct gallery WebP images")
        for original_path in originals:
            check((ROOT / original_path.lstrip("/")).is_file(),
                  "Setsuna photo absent from Git: " + original_path)
            check((SITE / original_path.lstrip("/")).is_file(),
                  "Setsuna original absent from build: " + original_path)
        for webp_path in webps:
            check((ROOT / webp_path.lstrip("/")).is_file(),
                  "Setsuna WebP absent from Git: " + webp_path)
            check((SITE / webp_path.lstrip("/")).is_file(),
                  "Setsuna WebP absent from build: " + webp_path)
        card = "/assets/uploads/2024/10/IMG_8836.jpg"
        header = "/assets/uploads/2024/10/IMG_8840.jpg"
        check(card in originals and header in originals,
              "Setsuna card and hero originals must also appear in the gallery")
        check('header_image: "2024/10/IMG_8840.jpg"' in front,
              "Setsuna header must be IMG_8840.jpg")
        check('exclude_ads:' not in front,
              "Setsuna must use standard AdSense placement, not a special opt-out")
        check("setsuna" not in flagged, "Setsuna must not carry the nudity E rating")
        url = post_urls.get("setsuna")
        check(url == "/2024/10/26/setsuna/", "Setsuna URL/date incorrect")
        if url:
            html, parsed = inspect(url)
            check('src="' + header + '"' in html,
                  "Setsuna hero image not found")
            check('src="' + card + '"' in archive_html,
                  "Setsuna archive image not found")
            check(html.count("pagead2.googlesyndication.com/pagead/js/adsbygoogle.js") == 1,
                  "Setsuna must load standard AdSense script once")
            check(html.count('<ins class="adsbygoogle"') == 2,
                  "Setsuna must render two standard manual ad placements")
            check('data-ad-slot="9856514493"' in html and
                  'data-ad-slot="7038779463"' in html,
                  "Setsuna standard ad slots missing")
            check('class="content-rating-badge"' not in html,
                  "Setsuna must not receive the E rating badge")

    # Roux as Wednesday Addams: six photographs with distinct card and hero.
    roux_slug = "roux-as-wednesday-addams"
    roux_path = ROOT / "_posts" / "2025-10-16-roux-as-wednesday-addams.md"
    check(roux_path.is_file(), "Roux Wednesday source post missing")
    if roux_path.is_file():
        raw = roux_path.read_text(encoding="utf-8")
        parts = raw.split("\n---\n", 1)
        front, gallery = parts if len(parts) == 2 else (raw, "")
        jpgs = re.findall(r'<img src="(/assets/uploads/2025/10/[^"]+)"', gallery)
        webps = re.findall(r'<source type="image/webp" srcset="([^"]+)"', gallery)
        check(len(jpgs) == 6 and len(set(jpgs)) == 6,
              "Roux Wednesday must include six unique original photographs")
        check(len(webps) == 6 and len(set(webps)) == 6,
              "Roux Wednesday must include six unique WebP gallery sources")
        for rel in jpgs + webps:
            check((ROOT / rel.lstrip("/")).is_file(),
                  "Roux Wednesday asset missing from repository: " + rel)
            check((SITE / rel.lstrip("/")).is_file(),
                  "Roux Wednesday asset absent from Jekyll build: " + rel)
        card = "/assets/uploads/2025/10/IMG_7607.jpg"
        hero = "/assets/uploads/2025/10/IMG_7612.jpg"
        check(card in jpgs and hero in jpgs,
              "Roux card and hero photographs must remain in the gallery")
        check("header_image: \"2025/10/IMG_7612.jpg\"" in front,
              "Wrong Roux Wednesday header image")
        check("featured_people:\n  - roux" in front,
              "Roux Wednesday missing featured subject")
        check("exclude_ads:" not in front,
              "Roux Wednesday must inherit standard manual ads")
        check(roux_slug not in flagged,
              "Roux Wednesday must not be given an E-rating badge")
        check("https://www.instagram.com/rouxrx/" in people_data,
              "Roux current Instagram profile missing")
        url = post_urls.get(roux_slug)
        check(url == "/2025/10/16/roux-as-wednesday-addams/",
              "Roux Wednesday date/permalink incorrect")
        if url:
            html, parsed = inspect(url)
            check('src="' + hero + '"' in html,
                  "Roux Wednesday hero image missing on post")
            check('src="' + card + '"' in archive_html,
                  "Roux Wednesday card image missing from archive")
            check('class="lynch-credits"' in html and "Roux" in html,
                  "Roux Wednesday visible People & Credits missing")
            check("https://www.instagram.com/rouxrx/" in html,
                  "Roux Wednesday linked credit missing updated Instagram")
            check(html.count("pagead2.googlesyndication.com/pagead/js/adsbygoogle.js") == 1,
                  "Roux Wednesday must load standard AdSense publisher script once")
            check(html.count('<ins class="adsbygoogle"') == 2,
                  "Roux Wednesday must render two manual ad placements")
            check('data-ad-slot="9856514493"' in html and
                  'data-ad-slot="7038779463"' in html,
                  "Roux Wednesday manual ad slots missing")
            check('class="content-rating-badge"' not in html,
                  "Roux Wednesday incorrectly shows nudity rating")
            blogs = [json.loads(x) for x in parsed.ld_json]
            check(any(b.get("@type") == "BlogPosting" and
                      any(p.get("name") == "Roux" and
                          p.get("sameAs") == "https://www.instagram.com/rouxrx/"
                          for p in b.get("mentions", []))
                      for b in blogs),
                  "Roux Wednesday Person structured data missing current profile")

    # WRC Candids: every delivered photo, separate cover/hero and club link.
    wrc_candids_source = ROOT / "_posts" / "2026-08-29-wrc-candids.md"
    check(wrc_candids_source.is_file(), "WRC Candids source post missing")
    if wrc_candids_source.is_file():
        source = wrc_candids_source.read_text(encoding="utf-8")
        parts = source.split("\n---\n", 1)
        front, gallery = parts if len(parts) == 2 else (source, "")
        photos = re.findall(r'<img src="(/assets/uploads/2026/08/[^"]+)"', gallery)
        webps = re.findall(r'<source type="image/webp" srcset="([^"]+)"', gallery)
        expected_names = {"IMG_8571.jpg", "IMG_8572.jpg", "IMG_8573.jpg",
                          "IMG_8586.jpg", "IMG_8591.jpg", "IMG_8616.jpg", "IMG_8618.jpg"}
        check(len(photos) == 7 and {p.rsplit("/", 1)[-1] for p in photos} == expected_names,
              "WRC Candids must contain all seven unique original photographs")
        check(len(webps) == 7 and len(set(webps)) == 7,
              "WRC Candids must contain seven distinct WebP gallery sources")
        for rel in photos + webps:
            check((ROOT / rel.lstrip("/")).is_file(), "WRC asset missing in Git: " + rel)
            check((SITE / rel.lstrip("/")).is_file(), "WRC asset missing in built site: " + rel)
        card = "/assets/uploads/2026/08/IMG_8618.jpg"
        header = "/assets/uploads/2026/08/IMG_8591.jpg"
        check(card in photos and header in photos,
              "WRC card/header images must remain inside the gallery")
        check('header_image: "2026/08/IMG_8591.jpg"' in front,
              "WRC post header must use IMG_8591.jpg")
        check("exclude_ads:" not in front and "wrc-candids" not in flagged,
              "WRC post must use standard AdSense, without an E rating")
        url = post_urls.get("wrc-candids")
        check(url == "/2026/08/29/wrc-candids/", "WRC Candids permalink or date incorrect")
        if url:
            html, parsed = inspect(url)
            check('src="' + header + '"' in html, "WRC header photo not rendered")
            check('src="' + card + '"' in archive_html, "WRC card photo not in archive")
            check(html.count("pagead2.googlesyndication.com/pagead/js/adsbygoogle.js") == 1,
                  "WRC article should load AdSense exactly once")
            check(html.count('<ins class="adsbygoogle"') == 2,
                  "WRC article should have both manual ad placements")
            check('data-ad-slot="9856514493"' in html and
                  'data-ad-slot="7038779463"' in html,
                  "WRC manual AdSense slot IDs are missing")
            check('class="content-rating-badge"' not in html,
                  "WRC article should not show an E badge")
            check('href="https://updates.wadadarunclub.com/"' in html,
                  "WRC article must link to the official Wadada Run Club website")


    # Falling Edge editorial hero and listing cover are intentionally different
    # photographs already present in the 12-image source gallery.
    falling_post = (ROOT / "_posts" / "2021-02-18-falling-edge.md").read_text(encoding="utf-8")
    falling_card = "/assets/uploads/2021/02/img_1077.jpg"
    falling_header = "/assets/uploads/2021/02/share-eeb5f485-8ba8-4b99-96b4-f8eee5f30199.jpg"
    featured_content = (ROOT / "_data" / "featured.yml").read_text(encoding="utf-8")
    check("falling-edge: 2021/02/img_1077.jpg" in featured_content,
          "Falling Edge archive card selection changed")
    check('header_image: "2021/02/share-eeb5f485-8ba8-4b99-96b4-f8eee5f30199.jpg"' in falling_post,
          "Falling Edge header selection changed")
    check(falling_card in falling_post and falling_header in falling_post,
          "Falling Edge selected images must remain present in original gallery")
    falling_html, _ = inspect("/2021/02/18/falling-edge/")
    check('src="' + falling_header + '"' in falling_html,
          "Falling Edge custom hero does not render")
    check('src="' + falling_card + '"' in archive_html,
          "Falling Edge archive card does not render")
    for suffix in ("480", "960"):
        cover_variant = ROOT / "assets" / "optimized" / "covers" / "2021" / "02" / ("img_1077-" + suffix + ".webp")
        check(cover_variant.is_file() and (SITE / cover_variant.relative_to(ROOT)).is_file(),
              "Falling Edge responsive cover missing: " + suffix)


    # Current owner-authored RafJam choices are intentionally separate from the
    # generic media rules. Changes here require review of the editorial request.
    rafjam = (ROOT / '_posts/2026-11-01-rafjam.md').read_text()
    front, body = rafjam.split('\n---\n', 1)
    photos = re.findall(r'<img[^>]+src="/assets/uploads/2026/11/(IMG_\d+\.webp)"', body)
    check(len(photos) == 40 and len(set(photos)) == 40, 'RafJam requires 40 distinct gallery photographs')
    check(photos == sorted(photos), 'RafJam numeric image order changed')
    check('IMG_0884.webp' in photos and photos.index('IMG_0876.webp') < photos.index('IMG_0884.webp') < photos.index('IMG_0902.webp'), 'RafJam waterfall photo order changed')
    for number in ('0715', '0725', '0757', '0778', '0790', '0825', '0834', '0870', '0875', '0958'):
        name = 'IMG_' + number + '.webp'
        check(name not in photos, 'Removed RafJam selection restored: ' + name)
        check((ROOT / 'assets/uploads/2026/11' / name).is_file(), 'Preserved RafJam source deleted: ' + name)
    check('header_image: "2026/11/IMG_0755.webp"' in front, 'RafJam hero changed')
    check('rafjam: 2026/11/IMG_0771.webp' in (ROOT / '_data/featured.yml').read_text(), 'RafJam card changed')
    for text in ('The hike made it out the group chat.', '5KM there and 5KM back. (Zone 1, light work)', 'Stir well &amp; enjoy.', 'dem peppa spray desmond eye'):
        # Markdown may contain a literal ampersand; preserve either source spelling.
        check(text in body or text.replace('&amp;', '&') in body, 'RafJam owner copy missing: ' + text)
    check(bool(re.search(r'IMG_0722.webp[^>]*>.*?</figure>\s*<p>dem peppa spray desmond eye</p>', body, re.S)), 'RafJam caption must immediately follow 0722')
    check('<p><a href="https://updates.wadadarunclub.com/"' in body and 'Brought to you by Wadada Run Club' in body, 'RafJam ordinary linked closing paragraph changed')
    check(post_urls.get('rafjam') == '/2026/11/01/rafjam/', 'RafJam historical permalink changed')
