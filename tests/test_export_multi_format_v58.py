"""Real-byte regression tests for all three formats and safe replacement."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from studio.core import export_apng, export_gif
from studio.safe_export import safe_export


class MultiFormatExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.frames = []
        for x in (1, 5, 9):
            frame = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            for dx in range(3):
                frame.putpixel((x+dx, 6), (240, 80, 120, 255))
            self.frames.append(frame)

    @staticmethod
    def validate_animated(path):
        with Image.open(path) as im:
            if im.n_frames < 2:
                raise ValueError('single-frame animation')
            pixels = []
            for index in range(im.n_frames):
                im.seek(index)
                pixels.append(im.convert('RGBA').tobytes())
            if len(set(pixels)) < 2:
                raise ValueError('no visible motion')

    def test_all_three_formats_written_and_decodable(self):
        outputs = [
            (self.folder/'cat_animated.apng', lambda p: export_apng(self.frames,p,100,0)),
            (self.folder/'cat_animated.gif', lambda p: export_gif(self.frames,p,100,0)),
            (self.folder/'cat_still.png', lambda p: self.frames[0].save(p,format='PNG')),
        ]
        for path, writer in outputs:
            safe_export(path,writer,self.validate_animated if path.suffix!='.png' else None)
            with Image.open(path) as image:
                self.assertEqual(image.size,(16,16))
                if path.suffix != '.png':
                    self.assertGreaterEqual(image.n_frames,2)
        self.assertEqual(len(list(self.folder.glob('cat_*'))),3)

    def test_failed_validation_preserves_existing_apng(self):
        path = self.folder/'cat_animated.apng'
        safe_export(path,lambda p: export_apng(self.frames,p,100,0),self.validate_animated)
        original = path.read_bytes()
        with self.assertRaises(ValueError):
            safe_export(path,lambda p: Image.new('RGBA',(16,16)).save(p,format='PNG'),self.validate_animated)
        self.assertEqual(path.read_bytes(),original)
        self.assertEqual(list(self.folder.iterdir()),[path])

    def test_failed_writer_preserves_existing_gif(self):
        path = self.folder/'cat_animated.gif'
        safe_export(path,lambda p: export_gif(self.frames,p,100,0),self.validate_animated)
        original = path.read_bytes()
        def failing_writer(candidate):
            candidate.write_bytes(b'partial')
            raise OSError('disk write failed')
        with self.assertRaises(OSError):
            safe_export(path,failing_writer,self.validate_animated)
        self.assertEqual(path.read_bytes(),original)
        self.assertEqual(list(self.folder.iterdir()),[path])
