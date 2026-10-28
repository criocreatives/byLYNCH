#!/usr/bin/env python3
"""Add verified intrinsic gallery dimensions from original photo bytes.

Dry-run by default, --apply writes only missing width/height attributes in
published Markdown <img> elements. No photos, order, titles, alt text, captions,
links, publication dates or embeds are rewritten. Source dimensions are
calculated after EXIF orientation correction.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
UPLOADS = (ROOT / "assets" / "uploads").resolve()
POSTS = ROOT / "_posts"
IMAGE_TAG = re.compile(r"<img\b[^>]*>", re.I | re.S)
SRC = re.compile(r"""\bsrc\s*=\s*["']([^"']+)["']""", re.I)
WIDTH = re.compile(r"""\bwidth\s*=\s*["']?\d+""", re.I)
HEIGHT = re.compile(r"""\bheight\s*=\s*["']?\d+""", re.I)
cache: dict[str, tuple[int, int]] = {}


def dimensions(src: str) -> tuple[int, int] | None:
    if not src.startswith("/assets/uploads/"):
        return None
    rel = Path(unquote(src.split("?", 1)[0]).lstrip("/"))
    file = (ROOT / rel).resolve()
    if not file.is_relative_to(UPLOADS) or not file.is_file():
        raise RuntimeError(f"Unresolvable original photo: {src}")
    key = file.as_posix()
    if key not in cache:
        with Image.open(file) as image:
            cache[key] = ImageOps.exif_transpose(image).size
    return cache[key]


def normalize(source: str, stats: Counter) -> str:
    def edit(match: re.Match) -> str:
        tag = match.group(0)
        found = SRC.search(tag)
        if not found:
            return tag
        measured = dimensions(found.group(1))
        if measured is None:
            return tag
        stats["images"] += 1
        if re.search(r"""\balt\s*=\s*["']\s*["']""", tag, re.I):
            stats["alt_empty"] += 1
        if not re.search(r"""\balt\s*=""", tag, re.I):
            stats["alt_missing"] += 1
        missing = []
        if not WIDTH.search(tag):
            missing.append(f'width="{measured[0]}"')
        if not HEIGHT.search(tag):
            missing.append(f'height="{measured[1]}"')
        if not missing:
            return tag
        stats["dimensions_added"] += 1
        if tag.endswith("/>"):
            return tag[:-2].rstrip() + " " + " ".join(missing) + " />"
        return tag[:-1].rstrip() + " " + " ".join(missing) + ">"
    return IMAGE_TAG.sub(edit, source)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write metadata into source posts")
    parser.add_argument("--report", type=Path, help="Save a JSON report outside public site")
    args = parser.parse_args()
    stats = Counter()
    modified = []
    for file in sorted(POSTS.glob("*.md")):
        current = file.read_text(encoding="utf-8")
        updated = normalize(current, stats)
        if updated != current:
            modified.append(file.name)
            if args.apply:
                file.write_text(updated, encoding="utf-8")
    report = {"mode": "apply" if args.apply else "dry-run",
              "post_sources_changed": len(modified), "post_files": modified,
              "images_scanned": stats["images"],
              "missing_dimensions_corrected": stats["dimensions_added"],
              "blank_alt_preserved_for_editorial_review": stats["alt_empty"],
              "missing_alt_preserved_for_editorial_review": stats["alt_missing"],
              "original_photographs_modified": 0}
    print(json.dumps(report, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
