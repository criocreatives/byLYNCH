#!/usr/bin/env python3
"""Legacy in-place JPEG optimizer, locked against accidental archive overwrites.

Dry-run by default. Only a deliberately approved one-off archival operation
should use --apply-in-place with a backup directory outside assets/uploads/.
New byLYNCH publishing should use non-destructive WebP derivatives instead.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent / "assets" / "uploads"
MAX_EDGE = 2400
QUALITY = 85


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply-in-place", action="store_true",
        help="Explicitly allow rewriting the original JPEGs (not for regular publishing).",
    )
    parser.add_argument(
        "--backup-dir", type=Path,
        help="Required with --apply-in-place; stores copies of every original before editing.",
    )
    args = parser.parse_args()
    originals = sorted(
        p for p in ROOT.rglob("*")
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg"}
    )
    if not args.apply_in_place:
        print(f"DRY RUN: {len(originals)} original JPEGs found; zero files modified.")
        print("Use scripts/build_responsive_covers.py for non-destructive derivatives.")
        print("Legacy overwrite requires --apply-in-place --backup-dir /outside/this/archive.")
        return

    if args.backup_dir is None:
        parser.error("--backup-dir is required with --apply-in-place")
    backup_root = args.backup_dir.expanduser().resolve()
    archive_root = ROOT.resolve()
    if backup_root == archive_root or backup_root.is_relative_to(archive_root):
        parser.error("--backup-dir must be outside assets/uploads/")
    if backup_root.exists() and any(backup_root.iterdir()):
        parser.error("--backup-dir must be empty to prevent overwriting existing backups")
    backup_root.mkdir(parents=True, exist_ok=True)

    processed = 0
    saved = 0
    for path in originals:
        rel = path.relative_to(ROOT)
        backup = backup_root / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        before = path.stat().st_size
        try:
            with Image.open(path) as source:
                image = ImageOps.exif_transpose(source)
                if image.mode not in ("RGB", "L"):
                    image = image.convert("RGB")
                width, height = image.size
                scale = min(1, MAX_EDGE / max(width, height))
                if scale < 1:
                    image = image.resize(
                        (round(width * scale), round(height * scale)),
                        Image.Resampling.LANCZOS,
                    )
                image.save(path, "JPEG", quality=QUALITY, optimize=True, progressive=True)
            saved += max(0, before - path.stat().st_size)
            processed += 1
        except Exception:
            shutil.copy2(backup, path)
            raise

    print(f"Processed {processed} JPEGs; backups at {backup_root}")
    print(f"Saved {saved / (1024**3):.2f} GiB (originals retained in backup).")


if __name__ == "__main__":
    main()
