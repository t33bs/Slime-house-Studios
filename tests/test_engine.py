import unittest,tempfile
from pathlib import Path
from PIL import Image
from studio.core import Layer,Region,composite,frames_for,export_apng,generate_traits,paint_pixel
class EngineTests(unittest.TestCase):
    def test_paint_erase(self):
        l=Layer('a',Image.new('RGBA',(16,16)))
        paint_pixel(l,5,5,(255,0,0,255));self.assertEqual(l.image.getpixel((5,5)),(255,0,0,255))
        paint_pixel(l,5,5,(0,0,0,0),erase=True);self.assertEqual(l.image.getpixel((5,5))[3],0)
    def test_transform(self):
        l=Layer('a',Image.new('RGBA',(4,4),(255,0,0,255)),3,3,True,2,0)
        self.assertEqual(composite([l],(16,16)).getpixel((8,8))[3],255)
    def test_regions_and_apng(self):
        l=Layer('a',Image.new('RGBA',(8,8),(255,0,0,255)),10,10)
        r=[Region('move',(10,10,8,8),'Float',3),Region('spark',(0,0,32,32),'Sparkle',4)]
        frames=frames_for([l],(32,32),count=8,regions=r)
        with tempfile.TemporaryDirectory() as td:
            p=export_apng(frames,Path(td)/'test.apng',100)
            with Image.open(p) as im:self.assertEqual(im.n_frames,8)
    def test_metadata_unique(self):
        result=generate_traits({'Fur':[{'name':'Orange','weight':3},{'name':'White','weight':1}],'Hat':[{'name':'None','weight':1},{'name':'Crown','weight':1}]},10,1)
        self.assertEqual(len(result),4)
if __name__=='__main__':unittest.main()
