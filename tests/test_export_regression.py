import tempfile
import unittest
from pathlib import Path
from PIL import Image
from studio.core import export_apng, export_gif, export_sprite_sheet


class ExportRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def frames(self, size=(64, 64), count=12):
        result=[]
        for i in range(count):
            im=Image.new('RGBA',size,(0,0,0,0))
            im.putpixel((i%3,2),(255,30,80,255))
            result.append(im)
        return result

    def test_apng_preserves_total_playback_time_with_repeated_frames(self):
        frames=self.frames()
        path=export_apng(frames,self.folder/'anim.apng',100,2)
        with Image.open(path) as im:
            self.assertGreaterEqual(im.n_frames,2)
            duration=0
            for i in range(im.n_frames):
                im.seek(i);duration+=im.info['duration']
            self.assertAlmostEqual(duration,1200,delta=2)

    def test_gif_playback_time(self):
        path=export_gif(self.frames(),self.folder/'anim.gif',100,0)
        with Image.open(path) as im:
            self.assertGreater(im.n_frames,1)
            self.assertEqual(im.info.get('loop'),0)

    def test_sheet_keeps_duplicate_frames(self):
        frames=self.frames((32,32))
        path=export_sprite_sheet(frames,self.folder/'sheet.png')
        with Image.open(path) as im:
            self.assertEqual(im.size,(384,32))
            for i,frame in enumerate(frames):
                self.assertEqual(im.crop((i*32,0,(i+1)*32,32)).convert('RGBA').tobytes(),frame.tobytes())

    def test_static_animations_rejected(self):
        frames=[Image.new('RGBA',(16,16)) for _ in range(4)]
        with self.assertRaises(ValueError):export_apng(frames,self.folder/'static.apng')
        with self.assertRaises(ValueError):export_gif(frames,self.folder/'static.gif')

    def test_sheet_width_guard(self):
        with self.assertRaises(ValueError):export_sprite_sheet(self.frames(),self.folder/'wide.png',max_width=100)
