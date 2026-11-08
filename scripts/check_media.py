#!/usr/bin/env python3
"""Validate published media and registries without rewriting content or images."""
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from PIL import Image
import yaml

ROOT = Path(__file__).resolve().parents[1]


class Media(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.sources = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            self.images.append(dict(attrs))
        if tag == 'source':
            self.sources.append(dict(attrs))


def local_asset(url):
    parts = urlsplit(url)
    if parts.scheme or parts.netloc or not parts.path.startswith('/assets/'):
        return None
    path = (ROOT / unquote(parts.path).lstrip('/')).resolve()
    if not path.is_relative_to((ROOT / 'assets').resolve()) or not path.is_file():
        raise ValueError('Missing or unsafe local asset: ' + url)
    built = ROOT / '_site' / path.relative_to(ROOT)
    if not built.is_file():
        raise ValueError('Local asset omitted from build: ' + url)
    return path


@lru_cache(maxsize=None)
def dimensions(path):
    if path.suffix.lower() == '.webp':
        header = path.read_bytes()[:12]
        if header[:4] != b'RIFF' or header[8:] != b'WEBP':
            raise ValueError('Invalid WebP signature: ' + str(path))
    with Image.open(path) as image:
        size = image.size
        if image.getexif().get(274) in (5, 6, 7, 8):
            size = size[::-1]
    with Image.open(path) as image:
        image.verify()
    return size


def check_images(parser, label, unique=False):
    seen = set()
    for image in parser.images:
        path = local_asset(image.get('src', ''))
        if path is None or path.suffix.lower() == ".svg":
            continue
        if unique and path in seen:
            raise ValueError(label + ': repeated gallery image ' + str(path))
        seen.add(path)
        actual = dimensions(path)
        declared = tuple(int(image.get(key, 0)) for key in ('width', 'height'))
        # WordPress often declared a different resolution of the same image.
        # Preserve those authored attributes, requiring a positive size and the
        # same aspect ratio within one pixel at either source resolution.
        tolerance = max(1, declared[0] / actual[0])
        if min(declared) <= 0 or abs(declared[0] - actual[0] * declared[1] / actual[1]) > tolerance:
            raise ValueError(f'{label}: dimensions {declared} != {actual}: {path}')
    for source in parser.sources:
        for candidate in source.get('srcset', '').split(','):
            fields = candidate.strip().split()
            if fields:
                path = local_asset(fields[0])
                if path:
                    size = dimensions(path)
                    if len(fields) > 1 and fields[1].endswith('w') and int(fields[1][:-1]) != size[0]:
                        raise ValueError(label + ': incorrect srcset width: ' + candidate)
    return len(seen)


def check_cover(entry):
    for key in ('small', 'large'):
        if entry.get(key):
            path = local_asset('/assets/optimized/covers/' + entry[key])
            if dimensions(path)[0] != entry[key + '_width']:
                raise ValueError('Incorrect cover width: ' + entry[key])


def main():
    featured = yaml.safe_load((ROOT / '_data/featured.yml').read_text())
    covers = yaml.safe_load((ROOT / '_data/responsive_covers.yml').read_text())
    posts = sorted((ROOT / '_posts').glob('*.md'))
    slugs = {p.name[11:-3] for p in posts}
    if set(featured) != slugs or set(covers) != slugs:
        raise ValueError('Published posts, featured images and cover registry must match exactly')
    count = 0
    for post in posts:
        slug = post.name[11:-3]
        _, front, body = post.read_text().split('---', 2)
        metadata = yaml.safe_load(front)
        source = Media()
        source.feed(body)
        count += check_images(source, post.name, unique=True)
        page = ROOT / '_site' / metadata['permalink'].strip('/') / 'index.html'
        rendered = Media()
        rendered.feed(page.read_text())
        check_images(rendered, metadata['permalink'])
        original = local_asset('/assets/uploads/' + featured[slug])
        if dimensions(original) != (covers[slug]['original_width'], covers[slug]['original_height']):
            raise ValueError(slug + ': cover original dimensions differ from registry')
        check_cover(covers[slug])
        if metadata.get('header_image'):
            header = local_asset('/assets/uploads/' + metadata['header_image'])
            if metadata.get('header_responsive'):
                entry = metadata['header_responsive']
                if dimensions(header) != (entry['original_width'], entry['original_height']):
                    raise ValueError(slug + ': hero original dimensions differ from registry')
                check_cover(entry)
    print(f'PASS: {len(posts)} post media/cover registries; {count} local gallery images, dimensions and WebP assets')


if __name__ == '__main__':
    main()
