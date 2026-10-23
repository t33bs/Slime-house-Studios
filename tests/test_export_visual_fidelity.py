import tempfile
import unittest
from pathlib import Path
from PIL import Image
from studio.core import export_gif, export_apng

class VisualExportFidelityTests(unittest.TestCase):
    def test_gif_transparency_and_solid_colors(self):
        frames=[]
        for x in (2, 5, 8):
            im=Image.new('RGBA',(16,16),(0,0,0,0))
            for dx in range(3):
                for dy in range(3):im.putpixel((x+dx,4+dy),(255,0,0,255))
            im.putpixel((12,12),(0,255,0,255))
            frames.append(im)
        with tempfile.TemporaryDirectory() as d:
            path=export_gif(frames,Path(d)/'test.gif',100)
            with Image.open(path) as im:
                for i in range(im.n_frames):
                    im.seek(i); got=im.convert('RGBA')
                    self.assertEqual(got.getpixel((0,0))[3],0)
                    self.assertEqual(got.getpixel((12,12))[:3],(0,255,0))
                    self.assertEqual(got.getpixel(((2,5,8)[i],4))[:3],(255,0,0))

    def test_apng_preserves_rgba_pixels(self):
        frames=[]
        for x in (2,5,8):
            im=Image.new('RGBA',(16,16),(0,0,0,0))
            im.putpixel((x,3),(128,40,220,128));frames.append(im)
        with tempfile.TemporaryDirectory() as d:
            path=export_apng(frames,Path(d)/'test.apng',100)
            with Image.open(path) as im:
                for i in range(im.n_frames):
                    im.seek(i)
                    self.assertEqual(im.convert('RGBA').tobytes(),frames[i].tobytes())

    def test_gif_rejects_sub_centisecond_timing(self):
        frames=[Image.new('RGBA',(8,8)) for _ in range(2)]
        frames[1].putpixel((1,1),(255,0,0,255))
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'multiple of 10'):
                export_gif(frames,Path(d)/'bad.gif',67)
            self.assertFalse((Path(d)/'bad.gif').exists())
