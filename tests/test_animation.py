import tempfile
import unittest
from pathlib import Path
from PIL import Image
from studio.core import Layer, composite, frames_for, export_apng

class AnimationTests(unittest.TestCase):
    def setUp(self):
        img=Image.new('RGBA',(8,8),(0,0,0,0))
        for x in range(2,6):
            for y in range(2,6):img.putpixel((x,y),(100,220,130,255))
        self.layers=[Layer('slime',img,8,8)]
    def test_transparency(self):
        self.assertEqual(composite(self.layers,(32,32)).getpixel((0,0))[3],0)
    def test_animated_export(self):
        frames=frames_for(self.layers,(32,32),'Float',8,3)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.apng';export_apng(frames,path,90)
            with Image.open(path) as im:
                self.assertEqual(im.n_frames,8)
                self.assertEqual(im.size,(32,32))
                images=[]
                for i in range(im.n_frames):
                    im.seek(i);images.append(im.convert('RGBA').tobytes())
                self.assertGreater(len(set(images)),1)
    def test_reject_static(self):
        im=Image.new('RGBA',(16,16),(0,0,0,0))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):export_apng([im,im.copy()],Path(tmp)/'static.apng')

if __name__=='__main__':unittest.main()
