#!/usr/bin/env python3
"""Build non-destructive cover WebPs with incremental, opt-in regeneration.

Normal runs generate only missing/outdated featured cover mappings. --only
explicitly rebuilds selected slugs, --header-post generates a custom hero, and
--rebuild-all is an intentional full resample. The original JPG/PNG files
are never modified, and unchanged manifest entries are preserved byte-for-byte.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageOps
import yaml

ROOT = Path(__file__).resolve().parent.parent
ORIGINALS = ROOT / "assets" / "uploads"
TARGET = ROOT / "assets" / "optimized" / "covers"
MANIFEST = ROOT / "_data" / "responsive_covers.yml"
POSTS = ROOT / "_posts"
WIDTHS = (480, 960)
QUALITY = 82  # Fixed quality for non-destructive derivative creation


def safe_original(rel_path: str) -> Path:
    rel = Path(str(rel_path))
    if rel.is_absolute() or ".." in rel.parts or rel.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        raise ValueError(f"Unsafe original image path: {rel_path}")
    path = ORIGINALS / rel
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def expected_paths(rel_path: str) -> list[str]:
    rel = Path(rel_path)
    return [rel.with_name(f"{rel.stem}-{w}.webp").as_posix() for w in WIDTHS]


def convert(rel_path: str, force: bool = False) -> dict:
    original = safe_original(rel_path)
    rel = Path(rel_path)
    with Image.open(original) as source:
        photo = ImageOps.exif_transpose(source)
        width, height = photo.size
        icc = source.info.get("icc_profile")
        if photo.mode not in ("RGB", "RGBA"):
            photo = photo.convert("RGBA" if "A" in photo.getbands() else "RGB")
        records = []
        for target_width in sorted({min(width, w) for w in WIDTHS}):
            target_height = max(1, round(height * target_width / width))
            dst_rel = rel.with_name(f"{rel.stem}-{target_width}.webp")
            dst = TARGET / dst_rel
            if force or not dst.is_file():
                resized = photo if target_width == width else photo.resize(
                    (target_width, target_height), Image.Resampling.LANCZOS
                )
                dst.parent.mkdir(parents=True, exist_ok=True)
                kwargs = {"format": "WEBP", "quality": QUALITY, "method": 6}
                if icc:
                    kwargs["icc_profile"] = icc
                resized.save(dst, **kwargs)
                print(f"Generated: {dst.relative_to(ROOT)}")
            records.append({"path": dst_rel.as_posix(), "width": target_width})

    entry = {"original_width": width, "original_height": height,
             "small": records[0]["path"], "small_width": records[0]["width"]}
    if len(records) > 1:
        entry["large"] = records[1]["path"]
        entry["large_width"] = records[1]["width"]
    return entry


def update_manifest_entry(text: str, slug: str, entry: dict) -> str:
    replacement = yaml.safe_dump({slug: entry}, sort_keys=True, allow_unicode=True)
    pattern = re.compile(r"^" + re.escape(slug) + r":\n(?:^  [^\n]*\n)*", re.M)
    matches = list(pattern.finditer(text))
    if len(matches) > 1:
        raise RuntimeError(f"Duplicate cover manifest entry: {slug}")
    if matches:
        return text[:matches[0].start()] + replacement + text[matches[0].end():]
    return text.rstrip("\n") + "\n" + replacement


def build_header(slug: str) -> None:
    matches = list(POSTS.glob("*-" + slug + ".md"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one post source for {slug}, found {len(matches)}")
    post = matches[0]
    contents = post.read_text(encoding="utf-8")
    front, delimiter, body = contents.partition("\n---\n")
    if not delimiter or not front.startswith("---\n"):
        raise RuntimeError(f"Invalid post front matter: {post}")
    found = re.search(r'^header_image:\s*["\']([^"\']+)["\']\s*$', front, re.M)
    if not found:
        raise RuntimeError(f"No custom header_image on {slug}")
    if re.search(r"^header_responsive:", front, re.M):
        print(f"Header already optimized for {slug}; no changes.")
        return
    entry = convert(found.group(1), force=True)
    lines = ["header_responsive:"] + [
        f"  {key}: {value}" for key, value in entry.items()
    ]
    new_front = front[:found.end()] + "\n" + "\n".join(lines) + front[found.end():]
    post.write_text(new_front + delimiter + body, encoding="utf-8")
    print(f"Added custom header WebP metadata: {post.relative_to(ROOT)}")


def generate() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", action="append", default=[], metavar="SLUG",
                        help="Regenerate only this cover slug (repeatable)")
    parser.add_argument("--header-post", action="append", default=[], metavar="SLUG",
                        help="Generate custom responsive header for the selected post")
    parser.add_argument("--rebuild-all", action="store_true",
                        help="Intentionally re-encode all 56 cards")
    args = parser.parse_args()
    if args.rebuild_all and args.only:
        parser.error("--rebuild-all and --only cannot be combined")
    featured = yaml.safe_load((ROOT / "_data" / "featured.yml").read_text(encoding="utf-8"))
    if not isinstance(featured, dict) or len(featured) != len(list(POSTS.glob("*.md"))):
        raise RuntimeError("Featured cover registry must match published posts")
    if any(slug not in featured for slug in args.only + args.header_post):
        parser.error("Unknown post slug in --only / --header-post")
    previous_text = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
    previous = yaml.safe_load(previous_text) or {}
    selected = []
    for slug, rel_path in sorted(featured.items()):
        expected = expected_paths(rel_path)
        prior = previous.get(slug, {})
        out_of_date = (prior.get("small") != expected[0]
                       or prior.get("large") != expected[1]
                       or any(not (TARGET / p).is_file() for p in expected))
        if args.rebuild_all or slug in args.only or out_of_date:
            selected.append((slug, rel_path))
    updated = previous_text
    for slug, rel_path in selected:
        entry = convert(rel_path, force=(args.rebuild_all or slug in args.only))
        updated = update_manifest_entry(updated, slug, entry)
    if updated != previous_text:
        MANIFEST.write_text(updated, encoding="utf-8")
    print(f"Generated/validated {len(selected)} changed card cover(s); "
          f"preserved {len(featured)-len(selected)} unrelated covers.")
    for slug in args.header_post:
        build_header(slug)


if __name__ == "__main__":
    generate()
