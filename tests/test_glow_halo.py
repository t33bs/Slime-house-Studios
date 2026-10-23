import unittest
from PIL import Image
from studio.core import Region, apply_region

class GlowHaloTests(unittest.TestCase):
    def test_glow_creates_colored_halo_outside_opaque_sprite(self):
        sprite=Image.new('RGBA',(20,20))
        sprite.putpixel((10,10),(255,255,255,255))
        r=Region('glow',(7,7,7,7),effect='Glow',color=(10,220,50,255),strength=3)
        result=apply_region(sprite.copy(),r,2,8)
        self.assertGreater(result.getpixel((9,10))[3],0)
        self.assertEqual(result.getpixel((9,10))[:3],(10,220,50))
        self.assertEqual(result.getpixel((10,10))[3],255)
    def test_glow_uses_effect_color_and_phase(self):
        sprite=Image.new('RGBA',(20,20))
        sprite.putpixel((10,10),(255,255,255,255))
        r=Region('glow',(7,7,7,7),effect='Glow',color=(200,30,210,255))
        bright=apply_region(sprite.copy(),r,2,8)
        dim=apply_region(sprite.copy(),r,6,8)
        self.assertGreater(bright.getpixel((9,10))[3],dim.getpixel((9,10))[3])
