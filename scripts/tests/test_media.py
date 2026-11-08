"""Negative fixtures prove generic media checks catch real regressions."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_media as media


class MediaTests(unittest.TestCase):
    def test_missing_duplicate_dimensions_and_corrupt_webp(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(media, 'ROOT', Path(directory)):
            root = Path(directory)
            photo = root / 'assets/uploads/photo.webp'
            photo.parent.mkdir(parents=True)
            Image.new('RGB', (80, 120)).save(photo)
            built = root / '_site/assets/uploads/photo.webp'
            built.parent.mkdir(parents=True)
            built.write_bytes(photo.read_bytes())
            def parser(width=80):
                p = media.Media()
                p.feed(f'<img src="/assets/uploads/photo.webp" width="{width}" height="120">')
                return p
            self.assertEqual(media.check_images(parser(), 'fixture', unique=True), 1)
            p = parser()
            p.images *= 2
            with self.assertRaisesRegex(ValueError, 'repeated'):
                media.check_images(p, 'fixture', unique=True)
            with self.assertRaisesRegex(ValueError, 'dimensions'):
                media.check_images(parser(120), 'fixture')
            built.unlink()
            with self.assertRaisesRegex(ValueError, 'omitted'):
                media.check_images(parser(), 'fixture')
            built.write_bytes(b'invalid')
            photo.write_bytes(b'invalid')
            media.dimensions.cache_clear()
            with self.assertRaisesRegex(ValueError, 'WebP signature'):
                media.dimensions(photo)
