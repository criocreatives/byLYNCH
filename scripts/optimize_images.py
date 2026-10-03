from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(r".\assets\uploads")
MAX_EDGE = 2400
QUALITY = 85

processed = 0
saved = 0

for path in ROOT.rglob("*"):
    if not path.is_file():
        continue

    if path.suffix.lower() not in [".jpg", ".jpeg"]:
        continue

    before = path.stat().st_size

    try:
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im)

            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")

            w, h = im.size
            scale = min(1, MAX_EDGE / max(w, h))

            if scale < 1:
                im = im.resize(
                    (round(w * scale), round(h * scale)),
                    Image.Resampling.LANCZOS
                )

            im.save(
                path,
                "JPEG",
                quality=QUALITY,
                optimize=True,
                progressive=True
            )

        after = path.stat().st_size
        processed += 1
        saved += max(0, before - after)

    except Exception as e:
        print(f"SKIPPED: {path} - {e}")

print(f"Processed {processed} JPEGs")
print(f"Saved {saved / (1024**3):.2f} GB")
