import unittest
from PIL import Image
from studio.core import Region, apply_region

class VisualPolishTests(unittest.TestCase):
    def test_blink_preserves_unselected_face(self):
        base=Image.new('RGBA',(16,16),(200,120,60,255))
        base.putpixel((5,5),(0,0,0,255))
        r=Region('eye',(4,4,3,3),effect='Blink',mask=[(5,5)])
        out=apply_region(base.copy(),r,4,8)
        self.assertEqual(out.getpixel((8,8)),base.getpixel((8,8)))
        self.assertEqual(out.getpixel((5,5)),(0,0,0,255))
    def test_laser_core_is_bright(self):
        base=Image.new('RGBA',(32,32))
        r=Region('beam',(2,8,3,3),effect='Laser Eyes',beam_length=12,color=(255,0,0,255))
        out=apply_region(base.copy(),r,4,9)
        self.assertEqual(out.getpixel((10,9)),(255,255,255,255))
    def test_sparkle_is_more_than_one_pixel(self):
        base=Image.new('RGBA',(32,32))
        r=Region('stars',(0,0,32,32),effect='Sparkle',strength=3)
        out=apply_region(base.copy(),r,0,8)
        self.assertGreater(sum(1 for px in out.get_flattened_data() if px[3]),1)
    def test_breathing_default_movement_is_gentle(self):
        base=Image.new('RGBA',(32,32))
        base.putpixel((15,15),(255,255,255,255))
        r=Region('body',(14,14,3,3),effect='Vertical Breathing',strength=20)
        out=apply_region(base.copy(),r,2,8)
        self.assertEqual(out.getpixel((15,17))[3],255)
