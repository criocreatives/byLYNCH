"""Exercise real encoding in temporary directories; never touch archive assets."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_responsive_covers as covers
from PIL import Image, ImageCms


class CoverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.uploads = self.root / 'assets/uploads'
        self.uploads.mkdir(parents=True)
        self.target = self.root / 'assets/optimized/covers'
        for name, value in [('ROOT', self.root), ('ORIGINALS', self.uploads), ('TARGET', self.target)]:
            p = patch.object(covers, name, value)
            p.start()
            self.addCleanup(p.stop)

    def test_formats_orientation_colour_and_original_preservation(self):
        icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        for suffix in ['jpg', 'png', 'webp']:
            with self.subTest(suffix=suffix):
                path = self.uploads / ('photo.' + suffix)
                exif = Image.Exif()
                exif[274] = 6
                Image.new('RGB', (1200, 800), '#456789').save(path, exif=exif, icc_profile=icc)
                before = hashlib.sha256(path.read_bytes()).digest()
                entry = covers.convert(path.name, force=True)
                self.assertEqual((entry['original_width'], entry['original_height']), (800, 1200))
                self.assertEqual(entry['small'], 'photo-480.webp')
                self.assertEqual(entry['large_width'], 800)
                for key in ['small', 'large']:
                    with Image.open(self.target / entry[key]) as image:
                        image.load()
                        self.assertEqual(image.format, 'WEBP')
                        self.assertEqual(image.info['icc_profile'], icc)
                        self.assertEqual(image.getexif().get(274, 1), 1)
                self.assertEqual(hashlib.sha256(path.read_bytes()).digest(), before)

    def test_safe_paths(self):
        for name in ['/tmp/out.jpg', '../out.jpg', 'dir/../../out.webp', 'photo.svg', '']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                covers.safe_original(name)
        external = self.root / 'external.webp'
        Image.new('RGB', (10, 10)).save(external)
        (self.uploads / 'link.webp').symlink_to(external)
        with self.assertRaises(ValueError):
            covers.safe_original('link.webp')
        with self.assertRaises(FileNotFoundError):
            covers.safe_original('missing.webp')

    def test_incremental_manifest_preserves_unrelated_bytes(self):
        old = '# curated registry\nother:\n  small: original.webp\n  original_width: 42\n'
        new = covers.update_manifest_entry(old, 'selected', {'small': 'new.webp'})
        self.assertTrue(new.startswith(old))
        self.assertEqual(covers.update_manifest_entry(new, 'selected', {'small': 'new.webp'}), new)

    def test_cli_selection_and_webp_header(self):
        posts = self.root / '_posts'
        posts.mkdir()
        data = self.root / '_data'
        data.mkdir()
        Image.new('RGB', (1200, 800)).save(self.uploads / 'source.webp')
        (data / 'featured.yml').write_text('story: source.webp\n')
        manifest = data / 'responsive_covers.yml'
        manifest.write_text('')
        post = posts / '2026-01-01-story.md'
        original = '---\nheader_image: "source.webp"\n---\nOwner copy remains.\n'
        post.write_text(original)
        with patch.object(covers, 'POSTS', posts), patch.object(covers, 'MANIFEST', manifest):
            with patch.object(sys, 'argv', ['covers', '--only', 'story', '--header-post', 'story']):
                covers.generate()
            self.assertIn('small: source-480.webp', manifest.read_text())
            self.assertIn('header_responsive:', post.read_text())
            self.assertEqual(post.read_text().split('\n---\n', 1)[1], 'Owner copy remains.\n')
            before = manifest.read_bytes()
            with patch.object(sys, 'argv', ['covers']):
                covers.generate()
            self.assertEqual(manifest.read_bytes(), before)

    def test_real_webp_card_and_header_sources(self):
        # Use actual Hermina and RafJam source bytes, but all output is disposable.
        repo = Path(__file__).resolve().parents[2]
        for rel in ['2016/12/img_4444.webp', '2026/11/IMG_0771.webp', '2026/11/IMG_0755.webp']:
            with self.subTest(rel=rel), patch.object(covers, 'ORIGINALS', repo / 'assets/uploads'):
                result = covers.convert(rel, force=True)
                self.assertTrue((self.target / result['small']).is_file())


if __name__ == '__main__':
    unittest.main()
