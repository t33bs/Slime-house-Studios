import unittest
from PIL import Image
from studio.core import interpolate_offsets,shift_frame,paste_clip,apply_motion_keyframes
class PhaseTwoTests(unittest.TestCase):
 def test_interpolate(self):
  self.assertEqual(interpolate_offsets({'0':[0,0],'4':[8,-4]},5),[(0,0),(2,-1),(4,-2),(6,-3),(8,-4)])
 def test_empty_keys(self):self.assertEqual(interpolate_offsets({},3),[(0,0)]*3)
 def test_motion_does_not_mutate(self):
  a=Image.new('RGBA',(8,8));a.putpixel((1,1),(255,0,0,255))
  moved=apply_motion_keyframes([a,a],{'0':[1,0],'1':[2,0]})
  self.assertEqual(moved[0].getpixel((2,1)),(255,0,0,255))
  self.assertEqual(moved[1].getpixel((3,1)),(255,0,0,255))
  self.assertEqual(a.getpixel((1,1)),(255,0,0,255))
 def test_clip_paste_bounds_and_copy(self):
  src={'0':[[1,1,1,2,3,255]],'1':[[2,2,4,5,6,255]]}
  result=paste_clip({},src,3,4)
  self.assertEqual(list(result),['3'])
  result['3'][0][0]=99
  self.assertEqual(src['0'][0][0],1)
