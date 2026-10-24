import unittest
from PIL import Image
from studio.bucket_fill import flood_fill

class BucketTests(unittest.TestCase):
    def test_enclosed_region(self):
        im=Image.new('RGBA',(7,7),(0,0,0,0))
        for x in range(1,6):im.putpixel((x,1),(0,0,0,255));im.putpixel((x,5),(0,0,0,255))
        for y in range(1,6):im.putpixel((1,y),(0,0,0,255));im.putpixel((5,y),(0,0,0,255))
        out=flood_fill(im,(3,3),(255,0,0,255))
        self.assertEqual(out.getpixel((3,3)),(255,0,0,255))
        self.assertEqual(out.getpixel((0,0)),(0,0,0,0))
        self.assertEqual(out.getpixel((1,3)),(0,0,0,255))
        self.assertEqual(im.getpixel((3,3)),(0,0,0,0))
    def test_noop_and_bounds(self):
        im=Image.new('RGBA',(2,2),(1,2,3,4))
        self.assertIsNone(flood_fill(im,(0,0),(1,2,3,4)))
        self.assertIsNone(flood_fill(im,(-1,0),(0,0,0,0)))
    def test_large_region(self):
        im=Image.new('RGBA',(512,512))
        out=flood_fill(im,(0,0),(10,20,30,255))
        self.assertEqual(out.getpixel((511,511)),(10,20,30,255))
