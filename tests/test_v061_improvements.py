import unittest
from PIL import Image
from studio.core import Region, Layer, frames_for
from studio.history import capture, decode

class ImprovementTests(unittest.TestCase):
    def test_laser_angle_persists(self):
        r=Region('Laser',(3,4,1,1),effect='Laser Eyes',beam_angle=137)
        data=capture((32,32),[],[r],{}, {},3,100,0,'GIF')
        self.assertEqual(decode(data)[2][0].beam_angle,137)
    def test_legacy_laser_defaults_to_right(self):
        self.assertEqual(Region('Laser',(0,0,1,1)).beam_angle,0)

if __name__=='__main__':unittest.main()
