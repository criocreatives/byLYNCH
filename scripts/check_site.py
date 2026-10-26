#!/usr/bin/env python3
"""Sanity-check a built byLYNCH Jekyll site. Standard library only.

Run from repository root after: jekyll build
This is deliberately a regression guard, not a substitute for browser testing.
"""
from __future__ import annotations

import json
import re
import sys
import zlib
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
BASE = "https://bylynch.com"
errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


class Extract(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.links: dict[str, str] = {}
        self.images: list[dict[str, str]] = []
        self.sources: list[dict[str, str]] = []
        self.headings: list[str] = []
        self.ld_json: list[str] = []
        self._in_ld = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {key: (value or "") for key, value in attrs}
        if tag == "meta":
            key = a.get("property") or a.get("name")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            if a.get("rel"):
                self.links[a["rel"]] = a.get("href", "")
        elif tag == "img":
            self.images.append(a)
        elif tag == "source":
            self.sources.append(a)
        elif tag in ("h1", "h2"):
            self.headings.append(tag)
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld = True

    def handle_data(self, data: str) -> None:
        if self._in_ld:
            self.ld_json.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._in_ld = False


def rendered(url: str) -> Path:
    return SITE / url.strip("/") / "index.html"


def inspect(url: str) -> tuple[str, Extract]:
    path = rendered(url)
    check(path.is_file(), "Missing generated page: " + url)
    if not path.is_file():
        return "", Extract()
    html = path.read_text(encoding="utf-8")
    parsed = Extract()
    parsed.feed(html)
    for label in ("description", "og:title", "og:description", "og:image", "og:url", "twitter:card"):
        check(bool(parsed.meta.get(label)), url + ": missing SEO meta " + label)
    check(parsed.links.get("canonical") == BASE + url, url + ": canonical URL mismatch")
    for item in parsed.ld_json:
        try:
            value = json.loads(item)
            check(value.get("@context") == "https://schema.org", url + ": wrong JSON-LD context")
        except (ValueError, AttributeError):
            errors.append(url + ": invalid JSON-LD")
    return html, parsed


check((SITE / "robots.txt").is_file(), "robots.txt was not generated")
if (SITE / "robots.txt").is_file():
    text = (SITE / "robots.txt").read_text(encoding="utf-8")
    check("Sitemap: https://bylynch.com/sitemap.xml" in text, "robots.txt sitemap hint missing")

sitemap = SITE / "sitemap.xml"
check(sitemap.is_file(), "sitemap.xml missing")
if sitemap.is_file():
    try:
        tree = ET.parse(sitemap)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [x.text for x in tree.findall(".//s:loc", ns)]
        check(BASE + "/" in locs, "Homepage missing from sitemap")
        check(BASE + "/archive/" in locs, "Archive missing from sitemap")
        check(len(locs) >= 55, f"Sitemap has only {len(locs)} URLs (expected public articles + pages)")
        check(len(set(locs)) == len(locs), "Duplicate sitemap URLs found")
    except ET.ParseError as ex:
        errors.append("sitemap.xml is not valid XML: " + str(ex))

home_html, home = inspect("/")

# Social-sharing preview must use the original solid-brick LYNCH logo, not
# the old white-on-white transparent logo asset.
social_path = ROOT / "assets/brand/lynch-social-preview.png"
check(social_path.is_file(), "Social-sharing brand image missing")
if social_path.is_file():
    png = social_path.read_bytes()
    check(png[:8] == b"\x89PNG\r\n\x1a\n", "Social preview must be PNG")
    if len(png) >= 24:
        size = (int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big"))
        check(size == (1200, 630), "Social preview must be 1200x630")
    # Validate chunk CRCs and compressed raster, not just the PNG header.
    pos, idat = 8, []
    while pos + 12 <= len(png):
        count = int.from_bytes(png[pos:pos + 4], "big")
        end = pos + 12 + count
        check(end <= len(png), "Social preview has a truncated PNG chunk")
        if end > len(png):
            break
        kind = png[pos + 4:pos + 8]
        payload = png[pos + 8:pos + 8 + count]
        expected_crc = int.from_bytes(png[pos + 8 + count:end], "big")
        check(zlib.crc32(kind + payload) & 0xffffffff == expected_crc,
              "Social preview contains a corrupt PNG chunk")
        if kind == b"IDAT":
            idat.append(payload)
        pos = end
        if kind == b"IEND":
            break
    check(bool(idat), "Social preview has no image pixel data")
    if idat:
        try:
            check(len(zlib.decompress(b"".join(idat))) > 1000,
                  "Social preview raster has too little data")
        except zlib.error:
            check(False, "Social preview raster cannot be decoded")
    check((SITE / social_path.relative_to(ROOT)).is_file(),
          "Social preview omitted from site build")
expected_share = BASE + "/assets/brand/lynch-social-preview.png"
check(home.meta.get("og:image") == expected_share, "Homepage social preview URL mismatch")
check(home.meta.get("og:image:width") == "1200", "Homepage social image width missing")
check(home.meta.get("og:image:height") == "630", "Homepage social image height missing")
check(home.meta.get("og:image:type") == "image/png", "Homepage social image type missing")
check(home.meta.get("twitter:card") == "summary_large_image",
      "Homepage Twitter/X card should use large image format")

check(home.headings.count("h1") == 1, "Homepage should contain exactly one primary H1")
covers = [image for image in home.images if "post-thumbnail-image" in image.get("class", "")]
check(len(covers) == 12, f"Homepage should expose 12 native cover <img> tags, found {len(covers)}")
for cover in covers:
    check(cover.get("src", "").startswith("/assets/uploads/"), "Homepage cover missing original asset src")
    check(bool(cover.get("alt")), "Homepage cover has missing/empty accessible alt text")
    check(bool(cover.get("width")) and bool(cover.get("height")), "Homepage cover missing original dimensions")
check(len([source for source in home.sources if source.get("type") == "image/webp"]) == 12,
      "Homepage must render 12 responsive WebP picture sources")

# Regression guard: optimized <picture> images must fill 4:5 cover cards.
css_text = (SITE / "assets/css/site.css").read_text(encoding="utf-8")
image_rule = ".post-cover-picture > img.post-thumbnail-image{"
rule_at = css_text.find(image_rule)
check(
    rule_at >= 0
    and "height:100%" in css_text[rule_at:rule_at + 400]
    and "object-fit:cover" in css_text[rule_at:rule_at + 400],
    "Optimized homepage/archive cover must fill its 4:5 card",
)

expected_post_count = len(list((ROOT / "_posts").glob("*.md")))
archive_html, archive = inspect("/archive/")
check(archive.headings.count("h1") == 1, "Archive should have exactly one H1")
archive_covers = [image for image in archive.images if "post-thumbnail-image" in image.get("class", "")]
check(len(archive_covers) == expected_post_count, f"Archive should expose {expected_post_count} cover <img> tags, found {len(archive_covers)}")
check(len([source for source in archive.sources if source.get("type") == "image/webp"]) == expected_post_count,
      f"Archive should render {expected_post_count} responsive WebP picture sources")

post_sources = sorted((ROOT / "_posts").glob("*.md"))
check(len(post_sources) >= 55, f"Expected at least 55 published post sources, found {len(post_sources)}")
post_urls: dict[str, str] = {}
for path in post_sources:
    match = re.search(r"^permalink:\s*(/\S+/)\s*$", path.read_text(encoding="utf-8"), re.M)
    check(match is not None, path.name + ": missing permalink")
    if match:
        post_urls[path.name[11:-3]] = match.group(1)

for slug, url in post_urls.items():
    content, parsed = inspect(url)
    check(parsed.meta.get("og:type") == "article", slug + ": OG article type missing")
    check(any('"@type": "BlogPosting"' in value for value in parsed.ld_json),
          slug + ": missing BlogPosting schema")

featured = ROOT / "_data" / "featured.yml"
for line in featured.read_text(encoding="utf-8").splitlines():
    if not line or line.startswith("#") or ": " not in line:
        continue
    slug, rel = line.split(": ", 1)
    file_path = ROOT / "assets" / "uploads" / rel.strip()
    check(file_path.is_file(), slug + ": missing featured image " + rel.strip())

flags = ROOT / "_data" / "content_flags.yml"
flagged = re.findall(r"^\s*-\s+([a-z0-9-]+)\s*$", flags.read_text(encoding="utf-8"), re.M)
check(len(flagged) == 9, f"Expected nine classified gallery slugs, found {len(flagged)}")
for slug in flagged:
    url = post_urls.get(slug)
    check(bool(url), "Flagged gallery has no matching permalink: " + slug)
    if url:
        html = rendered(url).read_text(encoding="utf-8")
        check("pagead2.googlesyndication.com/pagead/js/adsbygoogle.js" not in html,
              "AdSense library must be excluded from " + slug)
        check('<ins class="adsbygoogle"' not in html,
              "Manual ad units must be excluded from " + slug)

# People & Credits: verify person associations, readable credits and structured data.
expected_people = {
    "mcavelle": ["mcavelle", "mcavelle-returns", "bk", "sblv1"],
    "complex-ricki": ["bk", "fabricki", "ricki-ticki", "russian-rickolette"],
    "jada-kingdom": ["jada-the-iphone", "kingdom", "sblv1", "yada",
                     "no-rest-for-the-wicked-ft-jada-kingdom"],
    "runkus": ["anchor-studio-with-runkus", "god-ting",
               "new-wave-february-6-2017", "my-gf",
               "dubwise-ft-chronixx-friends"],
    "amanyea": ["my-gf", "phone-secks"],
    "iotosh": ["new-wave-february-6-2017"],
    "blvk-h3ro": ["new-wave-february-6-2017"]
}
people_data = (ROOT / "_data/people.yml").read_text(encoding="utf-8")
people_names = {
    "mcavelle": "McAvellé",
    "complex-ricki": "Complex Ricki", "jada-kingdom": "Jada Kingdom",
    "runkus": "Runkus", "amanyea": "Amanyea",
    "iotosh": "Iotosh", "blvk-h3ro": "Blvk H3ro"
}
for person_id, slugs in expected_people.items():
    check((person_id + ":") in people_data, "Missing person in canonical registry: " + person_id)
    for slug in slugs:
        path = next((p for p in post_sources if p.name[11:-3] == slug), None)
        check(path is not None, "Credited post missing: " + slug)
        if path is None:
            continue
        source = path.read_text(encoding="utf-8")
        front_matter = source.split("\n---\n", 1)[0]
        check(("  - " + person_id + "\n") in front_matter + "\n",
              slug + ": missing credits association for " + person_id)
        url = post_urls[slug]
        html = rendered(url).read_text(encoding="utf-8")
        check('class="lynch-credits"' in html, slug + ": missing visible credit section")
        check(people_names[person_id] in html,
              slug + ": missing visible credit for " + person_id)
        _, parsed = inspect(url)
        items = [json.loads(x) for x in parsed.ld_json]
        blog = [x for x in items if x.get("@type") == "BlogPosting"]
        check(bool(blog) and people_names[person_id] in [
              m.get("name") for m in blog[0].get("mentions", [])],
              slug + ": missing structured-data mention for " + person_id)

# Preserve normalized subject tags while retaining original story-specific tags.
for slug in expected_people["complex-ricki"]:
    post_path = next(p for p in post_sources if p.name[11:-3] == slug)
    front = post_path.read_text(encoding="utf-8").split("\n---\n", 1)[0]
    for tag in ("complex ricki", "ricki"):
        check(front.count('  - "' + tag + '"') == 1,
              slug + ": missing or repeated canonical tag " + tag)
for slug in expected_people["mcavelle"]:
    post_path = next(p for p in post_sources if p.name[11:-3] == slug)
    front = post_path.read_text(encoding="utf-8").split("\n---\n", 1)[0]
    check(front.count('  - "mcavelle"') == 1,
          slug + ": missing or duplicated McAvellé tag")
# B***K is a shared-feature gallery; both credits must survive.
bk_post = next(p for p in post_sources if p.name[11:-3] == "bk")
bk_front = bk_post.read_text(encoding="utf-8").split("\n---\n", 1)[0]
check("  - complex-ricki" in bk_front and "  - mcavelle" in bk_front,
      "B***K should credit both Complex Ricki and McAvellé")

# SBL Vol. 1 is a group compilation; preserve both confirmed subjects.
sblv1_path = next(p for p in post_sources if p.name[11:-3] == "sblv1")
sblv1_front = sblv1_path.read_text(encoding="utf-8").split("\n---\n", 1)[0]
check("  - jada-kingdom" in sblv1_front and "  - mcavelle" in sblv1_front,
      "SBL Vol. 1 must credit both Jada Kingdom and McAvellé")
sblv1_html = rendered(post_urls["sblv1"]).read_text(encoding="utf-8")
check('class="lynch-credits"' in sblv1_html and
      "Jada Kingdom" in sblv1_html and "McAvellé" in sblv1_html,
      "SBL Vol. 1 missing visible credits")

for slug in expected_people["jada-kingdom"]:
    post_path = next(p for p in post_sources if p.name[11:-3] == slug)
    front = post_path.read_text(encoding="utf-8").split("\n---\n", 1)[0]
    check(front.count('  - "jada kingdom"') == 1, slug + ": missing Jada Kingdom tag")

for slug in ("new-wave-february-6-2017", "my-gf", "dubwise-ft-chronixx-friends"):
    html = rendered(post_urls[slug]).read_text(encoding="utf-8")
    check('class="lynch-credits"' in html, "Extended credits missing on " + slug)
for person_name in ("Iotosh", "Blvk H3ro", "Meleku", "Jimmy Q", "Seani B", "Toddla T"):
    html = rendered(post_urls["new-wave-february-6-2017"]).read_text(encoding="utf-8")
    check(person_name in html, "New Wave credit absent: " + person_name)
for person_name in ("GiARK", "Lila Iké", "Naomi Cowan", "Sevana", "Protoje",
                    "Popcaan", "Kabaka Pyramid", "Chronixx"):
    html = rendered(post_urls["dubwise-ft-chronixx-friends"]).read_text(encoding="utf-8")
    check(person_name in html, "Dubwise credit absent: " + person_name)

# Prevent an ad-supported person's related-posts block linking to B***K, the E-rated gallery.
rk = rendered(post_urls["ricki-ticki"]).read_text(encoding="utf-8")
credits = rk.split('<section class="lynch-credits"', 1)[-1].split("</section>", 1)[0]
check("/2022/08/01/bk/" not in credits,
      "Ad-eligible Ricki Ticki credits must not link into the E-rated gallery")
bk = rendered(post_urls["bk"]).read_text(encoding="utf-8")
check('class="lynch-credits"' in bk and "Complex Ricki" in bk,
      "B***K credits missing while maintaining classified-gallery exclusions")

# Non-mature McAvellé pages must not recommend the E-rated B***K gallery.
for slug in ("mcavelle", "mcavelle-returns"):
    mc_html = rendered(post_urls[slug]).read_text(encoding="utf-8")
    credit_section = mc_html.split('<section class="lynch-credits"', 1)[-1].split("</section>", 1)[0]
    check("/2022/08/01/bk/" not in credit_section,
          slug + ": credits must not link into an E-rated post from an ad-supported page")
bk_html = rendered(post_urls["bk"]).read_text(encoding="utf-8")
check('class="lynch-credits"' in bk_html and "McAvellé" in bk_html
      and "Complex Ricki" in bk_html,
      "B***K needs both featured subjects in its visible credit section")

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
        check("Setsuna is a fleeting moment." in archive_html,
              "Setsuna custom editorial archive blurb missing")
check("Everything" in archive_html and "chalice by the fire" in archive_html,
      "Kosher editorial archive blurb missing")

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
        check("Wednesday Addams never needed colour." in archive_html,
              "Roux Wednesday editorial card description missing")
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

# GA4 must remain independent of AdSense eligibility, including all nine mature galleries.
GA_ID = "G-K95ENNDT6F"
GA_LIBRARY = "https://www.googletagmanager.com/gtag/js?id=" + GA_ID
for slug, url in post_urls.items():
    html = rendered(url).read_text(encoding="utf-8")
    check(html.count(GA_LIBRARY) == 1, slug + ": expected exactly one GA4 loader")
    check(html.count("gtag('config', '" + GA_ID + "'") == 1,
          slug + ": expected exactly one GA4 configuration")
check(home_html.count(GA_LIBRARY) == 1, "Homepage GA4 script missing or duplicated")
check(archive_html.count(GA_LIBRARY) == 1, "Archive GA4 script missing or duplicated")
for url in ("/about/", "/privacy/", "/cookies/"):
    content = rendered(url).read_text(encoding="utf-8")
    check(content.count(GA_LIBRARY) == 1, url + ": GA4 script missing or duplicated")
layout_source = (ROOT / "_layouts/default.html").read_text(encoding="utf-8")
check(layout_source.index(GA_LIBRARY) < layout_source.index("{% if adsense_allowed %}"),
      "GA4 loader must not be placed behind the mature-gallery AdSense gate")
check("'analytics_storage': 'denied'" in layout_source and "'analytics_storage': 'granted'" in layout_source,
      "GA4 regional consent defaults are missing")
check("'allow_google_signals': false" in layout_source
      and "'allow_ad_personalization_signals': false" in layout_source,
      "GA4 privacy-oriented ad settings are missing")
check("'page_location': window.location.origin + window.location.pathname" in layout_source,
      "GA4 must not send arbitrary URL query parameters")

# Optimized image files are checked as actual built assets, not just srcset strings.
optimized = sorted((ROOT / "assets" / "optimized" / "covers").rglob("*.webp"))
header_variant_count = sum(2 for p in post_sources if "header_responsive:" in p.read_text(encoding="utf-8"))
expected_optimized = len(post_sources) * 2 + header_variant_count
check(len(optimized) == expected_optimized, f"Expected {expected_optimized} optimized covers, found {len(optimized)}")
for file in optimized:
    with file.open("rb") as handle:
        header = handle.read(12)
    check(header[:4] == b"RIFF" and header[8:12] == b"WEBP",
          "Invalid WebP signature: " + str(file.relative_to(ROOT)))
    check((SITE / file.relative_to(ROOT)).is_file(),
          "Optimized cover omitted from generated Jekyll site: " + str(file.relative_to(ROOT)))
for url in ("/2024/09/26/swove-in-ledish/", "/2020/01/04/fabricki/"):
    _, parsed = inspect(url)
    check(any(s.get("type") == "image/webp" for s in parsed.sources),
          url + ": missing mobile optimized hero picture source")
    check(any(img.get("data-featured-image") is not None for img in parsed.images),
          url + ": missing featured hero image element")

# Editorial UI policy: About page must use vector icons, not emoji/text arrows.
about_source = (ROOT / "about" / "index.html").read_text(encoding="utf-8")
about_html, about_parsed = inspect("/about/")
arrow_characters = "\u2192\u2190\u2197\u2196\u2198\u2199\u27a1\u27a4\u279c\u2794"
check(not any(ch in about_source for ch in arrow_characters),
      "About page must not contain Unicode navigation arrow glyphs")
check('class="lynch-about-icon' in about_html,
      "About navigation links should use consistent SVG icons")
check(about_html.count('class="lynch-about-icon') >= 10,
      "Expected vector marks on About external, archive, and location links")

# Ad configuration is deliberately not changed during SEO work.
ad_config = (ROOT / "_data" / "manual_ads.yml").read_text(encoding="utf-8")
for slot in ("9856514493", "7038779463", "8559569688"):
    check(slot in ad_config, "Existing manual ad slot unexpectedly missing: " + slot)

# Every credited entity must render as a linked name plus short role. Profile
# destinations are verified registry URLs; unresolved identities use search only.
registry = {}
for record in re.finditer(r"^([a-z0-9-]+):\n(.*?)(?=^[a-z0-9-]+:\n|\Z)", people_data, re.M | re.S):
    fields = {}
    for field in ("name", "role", "profile_url", "search_query", "schema_type"):
        match = re.search(r"^  " + field + r": (\".*\")$", record.group(2), re.M)
        if match:
            fields[field] = json.loads(match.group(1))
    registry[record.group(1)] = fields


class CreditRows(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.capture = None
        self.buffer = ""
        self.href = ""
        self.names = []
        self.roles = []
        self.paragraphs = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if tag == "section" and "lynch-credits" in classes:
            self.active = True
        if not self.active:
            return
        if tag == "p":
            self.paragraphs += 1
        if tag == "a" and "lynch-credit-name" in classes:
            self.capture, self.buffer, self.href = "name", "", attrs.get("href", "")
        elif tag == "span" and "lynch-credit-role" in classes:
            self.capture, self.buffer = "role", ""

    def handle_data(self, data):
        if self.active and self.capture:
            self.buffer += data

    def handle_endtag(self, tag):
        if tag == "a" and self.capture == "name":
            self.names.append((self.buffer.strip(), self.href))
            self.capture = None
        elif tag == "span" and self.capture == "role":
            self.roles.append(self.buffer.strip())
            self.capture = None
        elif tag == "section":
            self.active = False


for path in post_sources:
    front = path.read_text(encoding="utf-8").split("\n---\n", 1)[0] + "\n"
    ids = []
    for field in ("featured_people", "collaborators", "mentioned_people"):
        group = re.search(r"^" + field + r":\n((?:  - [a-z0-9-]+\n)+)", front, re.M)
        if group:
            ids.extend(re.findall(r"  - ([a-z0-9-]+)", group.group(1)))
    if not ids:
        continue
    check(len(ids) == len(set(ids)), path.name + ": repeated person across credit groups")
    check(all(person_id in registry for person_id in ids), path.name + ": unresolved registry credit")
    slug = path.name[11:-3]
    html, parsed = inspect(post_urls[slug])
    rows = CreditRows()
    rows.feed(html)
    check(len(rows.names) == len(ids) and len(rows.roles) == len(ids),
          slug + ": every credit needs a linked name and short role")
    check(rows.paragraphs == 0, slug + ": credit block must not contain biographies or helper paragraphs")
    blogs = [json.loads(text) for text in parsed.ld_json]
    article = next((item for item in blogs if item.get("@type") == "BlogPosting"), {})
    mentions = article.get("mentions", [])
    for index, person_id in enumerate(ids):
        person = registry.get(person_id, {})
        if index >= len(rows.names) or index >= len(rows.roles):
            continue
        name, href = rows.names[index]
        check(name == person.get("name") and rows.roles[index] == person.get("role"),
              slug + ": name/role mismatch for " + person_id)
        if person.get("profile_url"):
            check(href == person["profile_url"], slug + ": wrong profile link for " + person_id)
        else:
            dest = urlparse(href)
            query = parse_qs(dest.query).get("q", [""])[0]
            check(dest.scheme == "https" and dest.netloc == "www.google.com" and
                  dest.path == "/search" and query == person.get("search_query", person.get("name")),
                  slug + ": incorrect search fallback for " + person_id)
        entity = [item for item in mentions if item.get("@id") == BASE + "/#person-" + person_id]
        check(len(entity) == 1 and entity[0].get("name") == person.get("name") and
              entity[0].get("description") == person.get("role") and
              entity[0].get("@type") == person.get("schema_type", "Person"),
              slug + ": structured identity must match visible name/role for " + person_id)

if errors:
    print("\n".join("FAIL: " + error for error in errors), file=sys.stderr)
    sys.exit(1)
print(f"PASS: {len(post_urls)} post URLs, {len(covers)} homepage covers, "
      f"{len(archive_covers)} archive covers, sitemap, metadata and ad exclusions.")
