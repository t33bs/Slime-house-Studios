import tempfile
import unittest
from pathlib import Path
from PIL import Image
from studio.pet_sprite_wizard import LIFE_ANIMATIONS, POSE_TEMPLATES, animation_guide, generate, export_package

class LifeAnimationTests(unittest.TestCase):
    def test_31_named_life_recipes(self):
        self.assertEqual(len(LIFE_ANIMATIONS),31)
        self.assertEqual(len(set(LIFE_ANIMATIONS)),31)
        for action in LIFE_ANIMATIONS:
            guide=animation_guide(action,8,'Four-legged')
            self.assertEqual(len(guide['frames']),8)
            self.assertTrue(guide['parts_to_prepare'])
            self.assertGreaterEqual(len(guide['key_poses']),3)
    def test_body_templates(self):
        self.assertIn('front paws',POSE_TEMPLATES['Four-legged'])
        self.assertIn('wings',POSE_TEMPLATES['Flying / winged'])
    def test_new_presets_generate_transparent_frames(self):
        img=Image.new('RGBA',(24,24))
        for y in range(8,17):
            for x in range(8,17):img.putpixel((x,y),(100,200,40,255))
        animations=generate(img,LIFE_ANIMATIONS,8)
        self.assertEqual(len(animations),31)
        self.assertTrue(all(len(frames)==8 and frames[0].size==(24,24) for frames in animations.values()))
        self.assertEqual(animations['Sleeping'][0].getpixel((0,0))[3],0)
        with tempfile.TemporaryDirectory() as tmp:
            meta=export_package({'Sad / Lonely':animations['Sad / Lonely'], 'Flying / Hovering':animations['Flying / Hovering']},tmp,'test',gif=False,apng=False)
            self.assertIn('sad_lonely',meta['animations'])
            self.assertIn('flying_hovering',meta['animations'])
            self.assertTrue((Path(tmp)/'test_frames'/'sad_lonely'/'000.png').exists())
