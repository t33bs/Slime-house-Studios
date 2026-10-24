import unittest
from PIL import Image
from studio.pet_sprite_wizard import generate_rigged,validate_regions

class RigTests(unittest.TestCase):
    def test_regions_validated(self):
        self.assertEqual(validate_regions({'head':[2,2,4,4]},(16,16))['head'],[2,2,4,4])
        with self.assertRaises(ValueError):validate_regions({'head':[15,15,4,4]},(16,16))
        with self.assertRaises(ValueError):validate_regions({'head':[2,2,4,4],'eyes':[3,3,2,2]},(16,16))
    def test_head_moves_independently_and_preserves_source(self):
        img=Image.new('RGBA',(32,32))
        for y in range(5,13):
            for x in range(12,20):img.putpixel((x,y),(255,50,30,255))
        for y in range(14,25):
            for x in range(10,22):img.putpixel((x,y),(30,150,255,255))
        before=img.tobytes()
        frames=generate_rigged(img,['Curious head tilt'],{'head':[12,5,8,8]},8)['Curious head tilt']
        self.assertEqual(len(frames),8)
        self.assertGreater(len({f.tobytes() for f in frames}),1)
        self.assertEqual(before,img.tobytes())
        self.assertTrue(all(f.size==img.size for f in frames))
    def test_no_regions_compatible_with_existing_generator(self):
        img=Image.new('RGBA',(16,16),(255,0,0,255))
        self.assertEqual(len(generate_rigged(img,['Sleeping'],{},8)['Sleeping']),8)
