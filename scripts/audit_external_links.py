#!/usr/bin/env python3
"""Non-destructive external link audit.

An HTTP 403, 429, timeout, or bot challenge is inconclusive, not a broken
link. Never delete editorial links automatically based on this report.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
URLS = re.compile(r"https?://[^\s\"'<>\\)]+", re.I)
EXTENSIONS = {".md", ".html", ".yml", ".xml"}
ROOTS = ("_posts", "_data", "_layouts", "_includes", "about", "contact",
         "category", "content-rights", "cookies", "privacy", "terms")
MAX_WORKERS = 6
TIMEOUT_SECONDS = 8


def collect():
    seen = defaultdict(set)
    for dirname in ROOTS:
        for path in (ROOT / dirname).rglob("*"):
            if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
                continue
            source = path.read_text(encoding="utf-8", errors="replace")
            for match in URLS.findall(source):
                url = match.rstrip(".,;:}])")
                if "{" in url or "}}" in url or urlsplit(url).hostname is None:
                    continue
                host = urlsplit(url).hostname
                if host in {"bylynch.com", "www.bylynch.com"}:
                    continue
                # Connection hints to Google Fonts are not browsable pages;
                # their root endpoints commonly return 404 by design.
                if host in {"fonts.googleapis.com", "fonts.gstatic.com"} and urlsplit(url).path in {"", "/"}:
                    continue
                seen[url].add(path.relative_to(ROOT).as_posix())
    return seen


def check(url):
    request = urllib.request.Request(url, method="HEAD", headers={
        "User-Agent": "Mozilla/5.0 (compatible; byLYNCH editorial link audit)",
        "Accept": "*/*",
    })
    for method in ("HEAD", "GET"):
        try:
            if method == "GET":
                request = urllib.request.Request(url, method="GET", headers={
                    "User-Agent": "Mozilla/5.0 (compatible; byLYNCH link audit)",
                    "Range": "bytes=0-0",
                })
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as resp:
                code = resp.status
                return {"status": "ok" if 200 <= code < 400 else "review",
                        "code": code, "final_url": resp.url}
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (400, 403, 405, 406, 429, 500, 501, 503):
                continue
            return {"status": "broken" if e.code in (404, 410) else "inconclusive",
                    "code": e.code}
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if method == "HEAD":
                continue
            return {"status": "inconclusive", "error": str(e)[:160]}
    return {"status": "inconclusive", "error": "provider refused automated request"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    refs = collect()
    urls = sorted(refs)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        results = list(pool.map(check, urls))
    report = [{"url": url, "sources": sorted(refs[url]), **result}
              for url, result in zip(urls, results)]
    tally = {key: sum(r["status"] == key for r in report)
             for key in ("ok", "broken", "inconclusive", "review")}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"total": len(report), "counts": tally,
                                       "links": report}, indent=2) + "\n",
                           encoding="utf-8")
    print(f"External URLs: {len(report)}; statuses: {tally}")
    for entry in report:
        if entry["status"] == "broken":
            print(f"REVIEW confirmed HTTP {entry.get('code')}: {entry['url']}")
    # Reporting only: no automatic edits, no false failure for transient blocks.


if __name__ == "__main__":
    main()
