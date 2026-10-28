#!/usr/bin/env python3
"""Compare built byLYNCH routes in headless Chromium without live third parties.

Build both Jekyll revisions first. This script does not modify either site.
It saves repeatable viewport captures, reports first-party transfer information,
and rejects meaningful visual differences. Live Core Web Vitals are separate.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROUTES = (
    ("/", "home"),
    ("/archive/", "archive"),
    ("/about/", "about"),
    ("/2024/10/26/setsuna/", "setsuna"),
    ("/2017/11/14/dubwise-ft-chronixx-friends/", "dubwise"),
    ("/2022/08/01/bk/", "excluded-gallery"),
)
VIEWPORTS = (
    ("desktop", 1440, 900),
    ("mobile", 390, 844),
)

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass

@contextlib.contextmanager
def serve(root: Path):
    handler = partial(QuietHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

def capture(browser, root_url, path, label, width, height, output):
    context = browser.new_context(
        viewport={"width": width, "height": height},
        device_scale_factor=1,
        reduced_motion="reduce",
        locale="en-US",
    )
    page = context.new_page()
    page.route("**/*", lambda route: (
        route.continue_() if route.request.url.startswith(root_url + "/")
        else route.abort()
    ))
    response = page.goto(root_url + path, wait_until="domcontentloaded", timeout=30000)
    if response is None or response.status != 200:
        raise RuntimeError(f"{label} {path}: HTTP {response.status if response else 'none'}")
    try:
        page.wait_for_load_state("load", timeout=18000)
    except Exception:
        pass  # Browser screenshot still demonstrates the fallback.
    page.wait_for_timeout(450)
    page.add_style_tag(content="*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}")
    image_path = output / f"{label}.png"
    page.screenshot(path=str(image_path), animations="disabled", full_page=False)
    data = page.evaluate("""() => ({
      title: document.title,
      images: document.images.length,
      firstPartyRequests: performance.getEntriesByType('resource').filter(x=>x.name.startsWith(location.origin)).length,
      durationMs: Math.round(performance.getEntriesByType('navigation')[0]?.duration || 0),
      firstContentfulPaintMs: Math.round(performance.getEntriesByType('paint').find(x=>x.name==='first-contentful-paint')?.startTime || 0),
      imageTransferBytes: Math.round(performance.getEntriesByType('resource').filter(x=>x.initiatorType==='img' || x.initiatorType==='image').reduce((s,x)=>s+(x.transferSize||0),0)),
      javascriptErrors: window.__bylynchCaptureErrors || []
    })""")
    if label.startswith("candidate-"):
        if path == "/" and width >= 600:
            assert page.locator("[data-post-feed] > .hentry").count() == 12, "Homepage must list 12 posts initially"
            page.locator(".search-toggle").click()
            assert page.locator(".site-search-panel.is-open").count() == 1, "Search must open"
            page.locator(".site-search-input").fill("setsuna")
            page.wait_for_timeout(750)
            assert page.locator(".site-search-result").count() > 0, "Search must return Setsuna"
            page.keyboard.press("Escape")
        if path == "/2024/10/26/setsuna/":
            image = page.locator(".entry-content img").first
            assert image.count() == 1, "Setsuna gallery must contain images"
            image.click()
            assert page.locator(".photo-lightbox.is-open").count() == 1, "Lightbox must open"
            page.keyboard.press("Escape")
            assert page.locator(".photo-lightbox.is-open").count() == 0, "Lightbox must close"
        if path == "/2022/08/01/bk/":
            assert page.locator('script[src*="adsbygoogle"]').count() == 0, "E-rated AdSense loader found"
    context.close()
    return data, image_path

def compare_images(left: Path, right: Path):
    with Image.open(left) as a, Image.open(right) as b:
        if a.size != b.size:
            return {"equal": False, "differenceFraction": 1, "sizeMismatch": True}
        if hashlib.sha256(left.read_bytes()).digest() == hashlib.sha256(right.read_bytes()).digest():
            return {"equal": True, "differenceFraction": 0, "sizeMismatch": False}
        delta = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
        pixels = delta.convert("L")
        histogram = pixels.histogram()
        # Ignore sub-4/255 antialiasing/channel noise.
        changed = sum(histogram[4:])
        return {"equal": changed / (a.width * a.height) <= 0.001,
                "differenceFraction": round(changed / (a.width * a.height), 6),
                "sizeMismatch": False}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    report = []
    failures = []
    with serve(args.baseline.resolve()) as baseline_url, serve(args.candidate.resolve()) as candidate_url:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
            for route, slug in ROUTES:
                for viewport, width, height in VIEWPORTS:
                    key = slug + "-" + viewport
                    before, before_png = capture(browser, baseline_url, route, "baseline-" + key, width, height, args.out)
                    after, after_png = capture(browser, candidate_url, route, "candidate-" + key, width, height, args.out)
                    diff = compare_images(before_png, after_png)
                    report.append({"route": route, "viewport": viewport, "baseline": before,
                                   "candidate": after, "visual": diff})
                    if not diff["equal"]:
                        failures.append(f"{key}: screenshot changed {diff['differenceFraction']:.2%}")
                    print(f"{key}: visual diff {diff['differenceFraction']:.2%}", flush=True)
            browser.close()
    (args.out / "report.json").write_text(json.dumps({"checks":report,"failures":failures},indent=2)+"\n")
    if failures:
        raise SystemExit("Visual regression: " + "; ".join(failures))
    print("PASS: representative desktop/mobile screenshots and interaction smoke checks")

if __name__ == "__main__":
    main()
