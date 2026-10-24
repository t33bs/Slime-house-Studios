from PIL import Image
from studio.creature_rig import CreatureRig
import json

def test_rig_roundtrip_and_atlas(tmp_path):
    rig=CreatureRig((16,16))
    rig.add_part('head',Image.new('RGBA',(4,4),(255,0,0,255)),2,3)
    rig.save_frame('Idle')
    rig.parts[0]['x']=6
    rig.save_frame('Walking')
    assert rig.render(rig.animations['Idle'][0]).getpixel((2,3))==(255,0,0,255)
    assert rig.render(rig.animations['Walking'][0]).getpixel((6,3))==(255,0,0,255)
    path=tmp_path/'pet.json';rig.save_project(path)
    loaded=CreatureRig.load_project(path)
    assert loaded.animations==rig.animations
    sheet=loaded.export(tmp_path,columns=2)
    assert Image.open(sheet).size==(32,16)
    metadata=json.loads((tmp_path/'creature_sheet.json').read_text())
    assert [f['animation'] for f in metadata['frames']]==['Idle','Walking']
