import tempfile
import unittest
from pathlib import Path
from PIL import Image
from studio.pet_sprite_wizard import ANIMATIONS, generate, export_package

class PetSpriteWizardTests(unittest.TestCase):
    def test_all_presets_and_package(self):
        image=Image.new('RGBA',(32,32))
        for y in range(8,25):
            for x in range(8,25):image.putpixel((x,y),(20,220,100,255))
        animations=generate(image,ANIMATIONS,6)
        self.assertEqual(len(animations),len(ANIMATIONS))
        with tempfile.TemporaryDirectory() as tmp:
            data=export_package(animations,tmp,'test_pet',8,True,True,True,{'Idle':{'Head':[16,8]}})
            with Image.open(Path(tmp)/'test_pet_sheet.png') as sheet:
                self.assertEqual(sheet.size,(192,32*len(ANIMATIONS)))
                self.assertEqual(sheet.mode,'RGBA')
            with Image.open(Path(tmp)/'test_pet_idle.png') as apng:
                self.assertGreater(apng.n_frames,1)
            with Image.open(Path(tmp)/'test_pet_idle.gif') as gif:
                self.assertGreater(gif.n_frames,1)
            self.assertEqual(data['animations']['idle']['frames'][0]['duration_ms'],125)
            self.assertTrue((Path(tmp)/'test_pet_frames'/'eat'/'000.png').exists())
    def test_invalid_frames(self):
        with self.assertRaises(ValueError):generate(Image.new('RGBA',(8,8)),['Idle'],1)

if __name__=='__main__':unittest.main()
