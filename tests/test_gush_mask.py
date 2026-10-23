import unittest, tempfile, json
from pathlib import Path
from PIL import Image
from studio.core import Layer,Region,EFFECTS,frames_for,export_apng
class GushMaskTests(unittest.TestCase):
    def setUp(self):
        im=Image.new('RGBA',(64,64),(0,0,0,0))
        for y in range(20,30):
            for x in range(20,30):im.putpixel((x,y),(100,200,150,255))
        self.layers=[Layer('test',im)]
    def test_gush_and_apng(self):
        self.assertIn('Gush',EFFECTS)
        for direction in ('Right','Left','Up','Down','Radial'):
            with self.subTest(direction=direction):
                r=Region('mouth',(20,20,10,10),effect='Gush',direction=direction,beam_length=25,particle_count=35,speed=3,mask=[[25,25]])
                frames=frames_for(self.layers,(64,64),count=12,regions=[r])
                self.assertGreater(len({f.tobytes() for f in frames}),1)
                with tempfile.TemporaryDirectory() as d:
                    p=Path(d)/'gush.apng';export_apng(frames,p)
                    with Image.open(p) as im:
                        self.assertEqual(im.size,(64,64));self.assertGreater(im.n_frames,1)
    def test_masked_movement_keeps_unselected_pixels(self):
        r=Region('one pixel',(20,20,10,10),effect='Horizontal Twitch',strength=3,mask=[[25,25]])
        frames=frames_for(self.layers,(64,64),count=8,regions=[r])
        for f in frames:self.assertEqual(f.getpixel((20,20)),(100,200,150,255))
    def test_region_serializes(self):
        r=Region('r',(1,1,5,5),effect='Gush',mask=[[2,2]],particle_count=20)
        from dataclasses import asdict
        self.assertEqual(Region(**json.loads(json.dumps(asdict(r)))).mask,[[2,2]])
