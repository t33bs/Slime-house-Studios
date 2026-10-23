import unittest
from PIL import Image, ImageDraw
from studio.core import EFFECTS, Layer, Region, frames_for


class AllEffectsTests(unittest.TestCase):
    def test_every_effect_renders_distinct_frames(self):
        sprite = Image.new('RGBA', (64, 64))
        ImageDraw.Draw(sprite).rectangle((15, 15, 42, 42), fill=(250, 100, 40, 255))
        for effect in EFFECTS:
            with self.subTest(effect=effect):
                frames = frames_for([Layer('Sprite', sprite)], (64, 64), count=12,
                                    regions=[Region('Area', (15, 15, 28, 28),
                                                    effect=effect, strength=4)])
                self.assertEqual(len(frames), 12)
                self.assertGreater(len({f.tobytes() for f in frames}), 1)
                self.assertTrue(all(f.size == (64, 64) for f in frames))
