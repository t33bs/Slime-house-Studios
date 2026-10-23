import unittest, tempfile
from pathlib import Path
from PIL import Image
from studio.core import Layer,Region,frames_for,compose_timeline_frames,export_apng

class TestMultiEffects(unittest.TestCase):
    def setUp(self):
        self.layer=Layer('sprite',Image.new('RGBA',(12,12),(255,100,40,255)),10,10)
        self.size=(40,40)
    def test_independent_timing(self):
        a=Region('early',(10,10,12,12),'Vertical Breathing',3,start_frame=0,active_frames=4,cycle_frames=4)
        b=Region('late',(10,10,12,12),'Horizontal Twitch',3,start_frame=4,active_frames=4,cycle_frames=4)
        early=frames_for([self.layer],self.size,count=8,regions=[a])
        late=frames_for([self.layer],self.size,count=8,regions=[b])
        base=frames_for([self.layer],self.size,count=8,regions=[])[0]
        self.assertNotEqual(early[1].tobytes(),base.tobytes())
        self.assertEqual(early[5].tobytes(),base.tobytes())
        self.assertEqual(late[1].tobytes(),base.tobytes())
        self.assertNotEqual(late[5].tobytes(),base.tobytes())
    def test_two_effects_simultaneous_and_export(self):
        a=Region('breath',(10,10,12,12),'Vertical Breathing',2,cycle_frames=8)
        b=Region('laser',(16,14,2,2),'Laser Eyes',2,cycle_frames=4,phase_offset=1)
        together=compose_timeline_frames([self.layer],self.size,[a,b],8)
        alone=compose_timeline_frames([self.layer],self.size,[a],8)
        self.assertTrue(any(x.tobytes()!=y.tobytes() for x,y in zip(together,alone)))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'two.apng';export_apng(together,p,90)
            with Image.open(p) as im:
                self.assertGreater(im.n_frames,1)
    def test_nonrepeat(self):
        r=Region('once',(10,10,12,12),'Horizontal Twitch',3,cycle_frames=4,repeat=False)
        frames=frames_for([self.layer],self.size,count=8,regions=[r])
        self.assertEqual(frames[4].tobytes(),frames[7].tobytes())
    def test_backward_compatible_region(self):
        old={'name':'old','rect':[0,0,12,12],'effect':'Glow','strength':2,'color':[160,255,190,255],'enabled':True,'direction':'Right','beam_length':18,'mask':[],'particle_count':12,'speed':2}
        self.assertEqual(Region(**old).start_frame,0)
        self.assertTrue(Region(**old).repeat)

if __name__=='__main__':unittest.main()
