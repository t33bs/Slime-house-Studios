import json
import tempfile
import unittest
from pathlib import Path
from studio.pet_sprite_wizard import ANIMATIONS, animation_guide, format_animation_guide, export_animation_guides

class AnimationRecipeTests(unittest.TestCase):
    def test_every_animation_has_specific_guidance(self):
        for name in ANIMATIONS:
            guide=animation_guide(name, 8, 'Four-legged')
            self.assertEqual(len(guide['frames']),8)
            self.assertTrue(guide['parts_to_prepare'])
            self.assertGreaterEqual(len(guide['key_poses']),3)
            self.assertIn('FRAME-BY-FRAME PLAN',format_animation_guide(guide))
        self.assertIn('mouth', animation_guide('Eat')['parts_to_prepare'].lower())
        self.assertIn('tail', animation_guide('Poop')['parts_to_prepare'].lower())
        self.assertIn('eyelid', animation_guide('Sleep')['parts_to_prepare'].lower())

    def test_export_recipes_as_text_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            export_animation_guides(['Eat','Sleep','Poop'],tmp,'My Pet!',6,'Two-legged')
            guide=Path(tmp)/'My_Pet_animation_guide.txt'
            data=Path(tmp)/'My_Pet_animation_recipes.json'
            self.assertTrue(guide.exists())
            self.assertIn('chew',guide.read_text(encoding='utf-8').lower())
            payload=json.loads(data.read_text(encoding='utf-8'))
            self.assertEqual(len(payload['recipes']),3)
            self.assertEqual(payload['recipes'][0]['frames'][-1]['frame'],6)

    def test_invalid_recipe(self):
        with self.assertRaises(ValueError):animation_guide('Unknown')

if __name__=='__main__':unittest.main()
