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
    ("/2021/02/18/falling-edge/", "falling-edge"),
    ("/2020/01/10/kraka/", "kraka"),
    ("/2017/01/04/hermina/", "hermina"),
    ("/2024/09/26/swove-in-ledish/", "swove"),
    ("/contact/", "contact"),
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
    context.add_init_script("""(() => {
      window.__bylynchLabVitals = {lcpMs:0, cls:0};
      try {
        new PerformanceObserver(list => {
          for (const item of list.getEntries()) {
            window.__bylynchLabVitals.lcpMs = Math.round(item.startTime);
          }
        }).observe({type:'largest-contentful-paint',buffered:true});
      } catch (_) {}
      try {
        new PerformanceObserver(list => {
          for (const item of list.getEntries()) {
            if (!item.hadRecentInput) window.__bylynchLabVitals.cls += item.value;
          }
        }).observe({type:'layout-shift',buffered:true});
      } catch (_) {}
    })();""")
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
      localTransferBytes: Math.round(performance.getEntriesByType('resource').filter(x=>x.name.startsWith(location.origin)).reduce((s,x)=>s+(x.transferSize||0),0)),
      lcpMs: window.__bylynchLabVitals?.lcpMs || null,
      cls: Number((window.__bylynchLabVitals?.cls || 0).toFixed(4)),
      javascriptErrors: window.__bylynchCaptureErrors || [],
      headerBottomPx: Math.ceil(document.querySelector('.site-header')?.getBoundingClientRect().bottom || 0)
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
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_function(
                "document.querySelectorAll('[data-post-feed] > .hentry.format-gallery.has-post-thumbnail').length >= 24",
                timeout=15000,
            )
            assert page.locator("[data-post-feed] > [data-home-grid-ad]").count() == 4, (
                "Homepage ad-card placement changed after infinite scrolling"
            )
        if path == "/2017/01/04/hermina/":
            assert page.locator("#hermina-password-form").count() == 0, "Old password gate remains"
            assert page.locator(".content-rating-badge").count() >= 1, "Hermina E badge missing"
            assert page.locator(".entry-content img").count() == 12, "Hermina needs 12 article images"
            assert page.locator(".entry-hero img[src*='img_4444.webp']").count() == 1, "Original hero missing"
            assert page.locator("ins.adsbygoogle").count() == 0, "Explicit post must not have ad units"
        if path == "/2024/10/26/setsuna/":
            gallery_image = page.locator(".entry-content img").first
            assert gallery_image.count() == 1, "Setsuna gallery must contain images"
            gallery_image.focus()
            page.keyboard.press("Enter")
            assert page.locator(".photo-lightbox.is-open").count() == 1, "Keyboard lightbox must open"
            page.keyboard.press("Tab")
            assert page.locator(".photo-lightbox").locator(":focus").count() == 1, "Focus must stay in dialog"
            page.keyboard.press("Escape")
            assert page.locator(".photo-lightbox.is-open").count() == 0, "Lightbox must close"
            assert gallery_image.evaluate("(img) => document.activeElement === img"), "Return focus to gallery photo"
        if path == "/" and width < 600:
            # Check narrow phones and the full pre-tablet breakpoint.
            for phone_width in (320, 390, 599):
                page.set_viewport_size({"width": phone_width, "height": height})
                search = page.locator(".search-toggle")
                nav = page.locator(".menu-toggle")
                assert search.is_visible(), f"Search hidden at {phone_width}px"
                assert nav.is_visible(), f"Mobile menu hidden at {phone_width}px"
                a, b = search.bounding_box(), nav.bounding_box()
                assert a and b and a["x"] >= b["x"] + b["width"] - 1, (
                    f"Mobile search overlaps navigation at {phone_width}px"
                )
                assert a["x"] + a["width"] <= phone_width, "Mobile search outside viewport"
                logo = page.locator(".site-logo-link img").bounding_box()
                assert logo and logo["x"] + logo["width"] <= b["x"] + 1, (
                    f"Header logo overlaps controls at {phone_width}px"
                )
                search.click()
                assert page.locator(".site-search-panel.is-open").count() == 1, "Mobile search did not open"
                page.wait_for_function(
                    "document.activeElement === document.querySelector('.site-search-input')",
                    timeout=5000,
                )
                page.locator(".site-search-input").fill("setsuna")
                page.wait_for_function(
                    "document.querySelectorAll('.site-search-result').length > 0",
                    timeout=10000,
                )
                page.keyboard.press("Escape")
                assert page.locator(".site-search-panel.is-open").count() == 0, "Mobile search did not close"
                nav.click()
                assert nav.get_attribute("aria-expanded") == "true", "Mobile menu should expand"
                nav.click()
                assert nav.get_attribute("aria-expanded") == "false", "Mobile menu should collapse"
    context.close()
    return data, image_path

def compare_images(left: Path, right: Path, ignore_top_px: int = 0):
    with Image.open(left) as a, Image.open(right) as b:
        if a.size != b.size:
            return {"equal": False, "differenceFraction": 1, "sizeMismatch": True}
        if not ignore_top_px and hashlib.sha256(left.read_bytes()).digest() == hashlib.sha256(right.read_bytes()).digest():
            return {"equal": True, "differenceFraction": 0, "sizeMismatch": False}
        if ignore_top_px:
            # An intentionally changed header is tested for layout and function
            # separately. Still compare all content below the header strictly.
            top = min(ignore_top_px, a.height - 1)
            a = a.crop((0, top, a.width, a.height))
            b = b.crop((0, top, b.width, b.height))
        delta = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
        pixels = delta.convert("L")
        histogram = pixels.histogram()
        # Ignore sub-4/255 antialiasing/channel noise.
        total = a.width * a.height
        changed = sum(histogram[4:])
        strong = sum(histogram[32:])
        mean_delta = sum(value * count for value, count in enumerate(histogram)) / total
        # A WebP derivative may vary a few colour values across many pixels,
        # despite retaining the same visual structure. Keep structural changes
        # subject to the stricter high-difference and average-difference gates.
        compression_equivalent = mean_delta <= 3.0 and strong / total <= 0.001
        return {"equal": changed / total <= 0.001 or compression_equivalent,
                "differenceFraction": round(changed / total, 6),
                "meanAbsoluteDifference": round(mean_delta, 4),
                "strongDifferenceFraction": round(strong / total, 6),
                "compressionEquivalent": compression_equivalent,
                "sizeMismatch": False}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--allow-visual-route", action="append", default=[],
                    help="Explicitly reviewed routes with intentional editorial changes")
    ap.add_argument("--allow-mobile-header-change", action="store_true",
                    help="Allow the mobile header to change, while comparing all content below it")
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
                    header_crop = (max(before["headerBottomPx"], after["headerBottomPx"]) + 4
                                   if args.allow_mobile_header_change and width < 600 else 0)
                    diff = compare_images(before_png, after_png, ignore_top_px=header_crop)
                    report.append({"route": route, "viewport": viewport, "baseline": before,
                                   "candidate": after, "ignoredHeaderPixels": header_crop,
                                   "visual": diff})
                    if not diff["equal"] and route not in args.allow_visual_route:
                        failures.append(f"{key}: screenshot changed {diff['differenceFraction']:.2%}")
                    print(f"{key}: raw pixel diff={diff['differenceFraction']:.2%}, equivalent={diff['equal']}, "
                          f"local FCP baseline/candidate={before['firstContentfulPaintMs']}/{after['firstContentfulPaintMs']}ms, "
                          f"LCP baseline/candidate={before['lcpMs']}/{after['lcpMs']}ms, "
                          f"transfer={before['localTransferBytes']}/{after['localTransferBytes']} bytes", flush=True)
            browser.close()
    (args.out / "report.json").write_text(json.dumps({"checks":report,"failures":failures},indent=2)+"\n")
    if failures:
        raise SystemExit("Visual regression: " + "; ".join(failures))
    print("PASS: representative desktop/mobile screenshots and interaction smoke checks")

if __name__ == "__main__":
    main()
