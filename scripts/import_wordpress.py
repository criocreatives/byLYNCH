#!/usr/bin/env python3
"""
Import the public byLYNCH WordPress archive into this Jekyll repo.

Usage:
  python scripts/import_wordpress.py \
    --xml "/path/to/bylynch.wordpress.com....xml" \
    --media "/path/to/extracted-media" \
    --repo "/path/to/byLYNCH"

What it does:
- imports published, non-password-protected posts only
- preserves original publish dates and /YYYY/MM/DD/slug/ permalinks
- preserves categories, tags and approved historical comments
- converts WordPress [gallery] and [caption] shortcodes to static HTML
- rewrites WordPress upload URLs to /assets/uploads/...
- copies only media referenced by public posts
- never imports private or password-protected post bodies
"""
from __future__ import annotations
import argparse, html, json, re, shutil
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

UPLOAD_RE = re.compile(r"https?://(?:www\.)?bylynch\.com/wp-content/uploads/([^\s\"'<>?#)]+)(?:\?[^\s\"'<>)]*)?", re.I)
GALLERY_RE = re.compile(r"\[gallery\s+([^\]]*?)\]", re.I)
CAPTION_RE = re.compile(r"\[caption[^\]]*\](.*?)\[/caption\]", re.I | re.S)
YOUTUBE_RE = re.compile(r"\[youtube\s+(https?://[^\s&\]]+)[^\]]*\]", re.I)
SOUNDCLOUD_RE = re.compile(r'\[soundcloud[^\]]*url="([^"]+)"[^\]]*\]', re.I)
IDS_RE = re.compile(r'ids="([^"]+)"', re.I)

def t(node, path, default=""):
    return node.findtext(path, default=default, namespaces=NS) or default

def yq(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)

def normalize_upload_rel(url_or_rel: str) -> str | None:
    if not url_or_rel:
        return None
    m = UPLOAD_RE.search(url_or_rel)
    if m:
        return m.group(1)
    x = url_or_rel.replace("\\", "/").lstrip("/")
    if re.match(r"^\d{4}/\d{2}/", x):
        return x
    return None

def find_media(media_root: Path, rel: str) -> Path | None:
    direct = media_root / rel
    if direct.exists():
        return direct
    # WordPress media exports can add a wrapper directory.
    matches = list(media_root.rglob(Path(rel).name))
    if not matches:
        return None
    # Prefer a path whose suffix matches year/month/name.
    suffix = rel.replace("\\", "/")
    for p in matches:
        if str(p).replace("\\", "/").endswith(suffix):
            return p
    return matches[0]

def media_html(rel: str, alt: str = "") -> str:
    return f'<img loading="lazy" src="/assets/uploads/{html.escape(rel)}" alt="{html.escape(alt)}">'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", required=True, type=Path)
    ap.add_argument("--media", required=True, type=Path)
    ap.add_argument("--repo", required=True, type=Path)
    args = ap.parse_args()

    root = ET.parse(args.xml).getroot()
    channel = root.find("channel")
    if channel is None:
        raise SystemExit("Invalid WordPress export: channel not found")

    attachments: dict[str, dict] = {}
    public_posts = []

    for item in channel.findall("item"):
        typ = t(item, "wp:post_type")
        status = t(item, "wp:status")
        pid = t(item, "wp:post_id")
        if typ == "attachment":
            rel = None
            for meta in item.findall("wp:postmeta", NS):
                if t(meta, "wp:meta_key") == "_wp_attached_file":
                    rel = t(meta, "wp:meta_value")
                    break
            url = t(item, "wp:attachment_url")
            rel = normalize_upload_rel(rel or url)
            attachments[pid] = {
                "rel": rel,
                "url": url,
                "title": t(item, "title"),
            }
            continue

        if typ != "post" or status != "publish":
            continue
        if t(item, "wp:post_password"):
            continue

        public_posts.append(item)

    posts_dir = args.repo / "_posts"
    uploads_dir = args.repo / "assets" / "uploads"
    posts_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Remove only generated Markdown post files, never the rest of the repo.
    for f in posts_dir.glob("*.md"):
        f.unlink()

    used_media: set[str] = set()
    manifest = []

    def rewrite_content(content: str) -> str:
        def gallery_sub(m):
            ids_m = IDS_RE.search(m.group(1))
            if not ids_m:
                return ""
            imgs = []
            for aid in [x.strip() for x in ids_m.group(1).split(",") if x.strip()]:
                a = attachments.get(aid)
                if not a or not a.get("rel"):
                    continue
                rel = a["rel"]
                used_media.add(rel)
                imgs.append(f'<figure class="gallery-item">{media_html(rel, a.get("title") or "")}</figure>')
            return '<div class="wp-gallery">' + "".join(imgs) + "</div>"

        content = GALLERY_RE.sub(gallery_sub, content)

        def caption_sub(m):
            inner = m.group(1).strip()
            # Keep the original image HTML and turn trailing text into a figcaption where possible.
            img_match = re.search(r"(<img\b[^>]*>)", inner, re.I | re.S)
            if not img_match:
                return inner
            img = img_match.group(1)
            caption = (inner[:img_match.start()] + inner[img_match.end():]).strip()
            return f"<figure>{img}" + (f"<figcaption>{caption}</figcaption>" if caption else "") + "</figure>"

        content = CAPTION_RE.sub(caption_sub, content)

        def upload_sub(m):
            rel = m.group(1)
            used_media.add(rel)
            return "/assets/uploads/" + rel

        content = UPLOAD_RE.sub(upload_sub, content)

        content = YOUTUBE_RE.sub(
            lambda m: f'<div class="embed"><iframe src="https://www.youtube.com/embed/{youtube_id(m.group(1))}" title="YouTube video" loading="lazy" allowfullscreen></iframe></div>',
            content,
        )
        content = SOUNDCLOUD_RE.sub(
            lambda m: f'<p><a href="{html.escape(m.group(1))}" target="_blank" rel="noopener">Listen on SoundCloud</a></p>',
            content,
        )
        return content

    def youtube_id(url: str) -> str:
        parsed = urlparse(url)
        if "youtu.be" in parsed.netloc:
            return parsed.path.strip("/")
        if "youtube.com" in parsed.netloc:
            if parsed.path.startswith("/watch"):
                from urllib.parse import parse_qs
                return parse_qs(parsed.query).get("v", [""])[0]
            return parsed.path.rstrip("/").split("/")[-1]
        return ""

    for item in public_posts:
        title = t(item, "title")
        slug = t(item, "wp:post_name")
        date_s = t(item, "wp:post_date")
        modified = t(item, "wp:post_modified")
        author = t(item, "dc:creator")
        content = rewrite_content(t(item, "content:encoded"))
        excerpt = re.sub(r"<[^>]+>", " ", t(item, "excerpt:encoded")).strip()

        cats, tags = [], []
        for c in item.findall("category"):
            val = (c.text or "").strip()
            if c.get("domain") == "category" and val:
                cats.append(val)
            elif c.get("domain") == "post_tag" and val:
                tags.append(val)

        comments = []
        for cm in item.findall("wp:comment", NS):
            if t(cm, "wp:comment_approved") != "1":
                continue
            comments.append({
                "author": t(cm, "wp:comment_author"),
                "date": t(cm, "wp:comment_date"),
                "content": t(cm, "wp:comment_content"),
            })

        dt = datetime.strptime(date_s, "%Y-%m-%d %H:%M:%S")
        front = [
            "---",
            "layout: post",
            f"title: {yq(html.unescape(title))}",
            f"date: {date_s} -0500",
            f"date_string: {yq(date_s)}",
            f"modified: {modified} -0500",
            f"permalink: /{dt:%Y/%m/%d}/{slug}/",
            f"author: {yq(author)}",
            "categories:",
        ]
        front += [f"  - {yq(html.unescape(x))}" for x in cats] or ['  - "Uncategorized"']
        front.append("tags:")
        front += [f"  - {yq(html.unescape(x))}" for x in tags] or ['  - ""']
        if excerpt:
            front.append(f"excerpt: {yq(html.unescape(excerpt))}")
        if comments:
            front.append("archived_comments:")
            for c in comments:
                front += [
                    f"  - author: {yq(html.unescape(c['author']))}",
                    f"    date: {yq(c['date'])}",
                    f"    content: {yq(html.unescape(c['content']))}",
                ]
        front.append("---")

        (posts_dir / f"{dt:%Y-%m-%d}-{slug}.md").write_text(
            "\n".join(front) + "\n" + content + "\n", encoding="utf-8"
        )
        manifest.append({
            "title": html.unescape(title),
            "date": date_s,
            "slug": slug,
            "url": f"/{dt:%Y/%m/%d}/{slug}/",
            "categories": [html.unescape(x) for x in cats],
            "comments": len(comments),
        })

    copied, missing = 0, []
    for rel in sorted(used_media):
        src = find_media(args.media, rel)
        if not src:
            missing.append(rel)
            continue
        dst = uploads_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1

    (args.repo / "migration-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.repo / "migration-missing-media.txt").write_text(
        "\n".join(missing) + ("\n" if missing else ""), encoding="utf-8"
    )

    print(f"Imported {len(manifest)} public posts.")
    print(f"Copied {copied} referenced media files.")
    print(f"Missing media files: {len(missing)}")
    print("Private and password-protected posts were not imported.")

if __name__ == "__main__":
    main()
