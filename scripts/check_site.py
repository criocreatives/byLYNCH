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

archive_html, archive = inspect("/archive/")
check(archive.headings.count("h1") == 1, "Archive should have exactly one H1")
archive_covers = [image for image in archive.images if "post-thumbnail-image" in image.get("class", "")]
check(len(archive_covers) == 52, f"Archive should expose 52 cover <img> tags, found {len(archive_covers)}")
check(len([source for source in archive.sources if source.get("type") == "image/webp"]) == 52,
      "Archive should render 52 responsive WebP picture sources")

post_sources = sorted((ROOT / "_posts").glob("*.md"))
check(len(post_sources) == 52, f"Expected 52 published post sources, found {len(post_sources)}")
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
check(len(optimized) == 104, f"Expected 104 curated optimized covers, found {len(optimized)}")
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

if errors:
    print("\n".join("FAIL: " + error for error in errors), file=sys.stderr)
    sys.exit(1)
print(f"PASS: {len(post_urls)} post URLs, {len(covers)} homepage covers, "
      f"{len(archive_covers)} archive covers, sitemap, metadata and ad exclusions.")
