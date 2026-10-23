import unittest,tempfile
from pathlib import Path
from PIL import Image
from studio.core import Layer,Region,frames_for,export_apng,EFFECTS

class HtmlEffectsTests(unittest.TestCase):
    def test_html_effects_produce_real_frames(self):
        art=Image.new('RGBA',(64,64),(0,0,0,0))
        for y in range(20,38):
            for x in range(20,38):art.putpixel((x,y),(80,190,120,255))
        layer=Layer('sprite',art)
        for effect in ('Vertical Breathing','Horizontal Twitch','Blink','Glow','Laser Eyes'):
            with self.subTest(effect=effect):
                region=Region('eyes',(22,22,12,12),effect,3)
                frames=frames_for([layer],(64,64),count=8,regions=[region])
                self.assertGreater(len({f.tobytes() for f in frames}),1)
                with tempfile.TemporaryDirectory() as d:
                    output=Path(d)/'test.apng';export_apng(frames,output)
                    with Image.open(output) as apng:self.assertGreaterEqual(apng.n_frames,2)
    def test_presets_present(self):
        for name in ('Vertical Breathing','Horizontal Twitch','Blink','Glow','Laser Eyes'):self.assertIn(name,EFFECTS)
