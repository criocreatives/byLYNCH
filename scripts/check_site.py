#!/usr/bin/env python3
"""Sanity-check a built byLYNCH Jekyll site. Standard library only.

Run from repository root after: jekyll build
This is deliberately a regression guard, not a substitute for browser testing.
"""
from __future__ import annotations

import json
import re
import sys
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
check(home.headings.count("h1") == 1, "Homepage should contain exactly one primary H1")
covers = [image for image in home.images if "post-thumbnail-image" in image.get("class", "")]
check(len(covers) == 12, f"Homepage should expose 12 native cover <img> tags, found {len(covers)}")
for cover in covers:
    check(cover.get("src", "").startswith("/assets/uploads/"), "Homepage cover missing original asset src")
    check(bool(cover.get("alt")), "Homepage cover has missing/empty accessible alt text")
    check(bool(cover.get("width")) and bool(cover.get("height")), "Homepage cover missing original dimensions")
check(len([source for source in home.sources if source.get("type") == "image/webp"]) == 12,
      "Homepage must render 12 responsive WebP picture sources")

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

# Ad configuration is deliberately not changed during SEO work.
ad_config = (ROOT / "_data" / "manual_ads.yml").read_text(encoding="utf-8")
for slot in ("9856514493", "7038779463", "8559569688"):
    check(slot in ad_config, "Existing manual ad slot unexpectedly missing: " + slot)

if errors:
    print("\n".join("FAIL: " + error for error in errors), file=sys.stderr)
    sys.exit(1)
print(f"PASS: {len(post_urls)} post URLs, {len(covers)} homepage covers, "
      f"{len(archive_covers)} archive covers, sitemap, metadata and ad exclusions.")
