import tempfile
import unittest
from pathlib import Path
from PIL import Image
from studio.core import export_apng, export_gif, export_sprite_sheet


class ExportValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = Path(self.tmp.name)
        self.frames = [Image.new('RGBA', (16, 16), (255, 0, 0, 255)),
                       Image.new('RGBA', (16, 16), (0, 255, 0, 255))]

    def test_invalid_duration_rejected_without_file(self):
        for exporter, ext in ((export_apng, 'apng'), (export_gif, 'gif')):
            for duration in (0, -10, 10, 2001, 100.5):
                path = self.dest / ('bad.' + ext)
                with self.subTest(exporter=ext, duration=duration):
                    with self.assertRaises(ValueError):
                        exporter(self.frames, path, duration=duration)
                    self.assertFalse(path.exists())

    def test_invalid_loops_rejected_without_file(self):
        for exporter, ext in ((export_apng, 'apng'), (export_gif, 'gif')):
            for loop in (-1, 65536, 1.5):
                path = self.dest / ('bad.' + ext)
                with self.subTest(exporter=ext, loop=loop):
                    with self.assertRaises(ValueError):
                        exporter(self.frames, path, loop=loop)
                    self.assertFalse(path.exists())

    def test_mismatched_frames_rejected(self):
        frames = self.frames + [Image.new('RGBA', (8, 8))]
        for exporter, ext in ((export_apng, 'apng'), (export_gif, 'gif'), (export_sprite_sheet, 'png')):
            with self.subTest(exporter=ext):
                with self.assertRaises(ValueError):
                    exporter(frames, self.dest / ('bad.' + ext))

    def test_valid_loop_and_duration(self):
        for exporter, ext in ((export_apng, 'apng'), (export_gif, 'gif')):
            path = exporter(self.frames, self.dest / ('valid.' + ext), duration=120, loop=3)
            with Image.open(path) as im:
                self.assertEqual(im.info.get('loop'), 3)
                self.assertGreaterEqual(im.n_frames, 2)
