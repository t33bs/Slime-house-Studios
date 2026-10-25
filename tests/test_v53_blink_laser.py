from PIL import Image
from studio.core import Region, apply_region

def test_blink_color_can_be_selected():
    image=Image.new('RGBA',(8,8),(0,0,0,0))
    for y in range(2,5):
        for x in range(2,6):image.putpixel((x,y),(10,20,30,255))
    reg=Region('eye',(2,2,4,3),effect='Blink',color=(255,0,255,255),blink_use_color=True)
    result=apply_region(image.copy(),reg,6,12)
    assert result.getpixel((3,3))==(255,0,255,255)

def test_laser_region_is_non_destructive_and_movable():
    image=Image.new('RGBA',(24,12),(0,0,0,0))
    reg=Region('laser',(2,4,1,1),effect='Laser Eyes',color=(255,0,0,255),beam_length=8)
    reg.rect=(8,4,1,1)
    result=apply_region(image.copy(),reg,3,12)
    assert image.getbbox() is None
    assert result.getbbox() is not None
