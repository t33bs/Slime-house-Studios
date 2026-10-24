import unittest
from PIL import Image
from studio.core import Layer,compose_layer_motion_frames,interpolate_pose_anchors
from pathlib import Path

class LayerMotionTests(unittest.TestCase):
    def test_one_layer_moves_other_remains(self):
        red=Layer('red',Image.new('RGBA',(1,1),(255,0,0,255)))
        blue=Layer('blue',Image.new('RGBA',(1,1),(0,0,255,255)))
        blue.x=5
        frames=compose_layer_motion_frames([red,blue],(12,4),[],3,layer_keys={'0':{'0':[0,0],'2':[2,0]}})
        self.assertEqual([f.getpixel((i,0)) for i,f in enumerate(frames)],[(255,0,0,255)]*3)
        self.assertEqual([f.getpixel((5,0)) for f in frames],[(0,0,255,255)]*3)
        self.assertEqual((red.x,blue.x),(0,5))
    def test_global_and_layer_offsets_combine(self):
        layer=Layer('pixel',Image.new('RGBA',(1,1),(255,0,0,255)))
        frames=compose_layer_motion_frames([layer],(8,8),[],2,layer_keys={'0':{'0':[1,0]}},global_keys={'0':[0,2]})
        self.assertEqual(frames[0].getpixel((1,2)),(255,0,0,255))
    def test_paint_overlay_after_layer_movement(self):
        layer=Layer('pixel',Image.new('RGBA',(1,1),(255,0,0,255)))
        frames=compose_layer_motion_frames([layer],(8,8),[],2,edits={'0':[[1,1,0,255,0,255]]},layer_keys={'0':{'0':[2,0]}})
        self.assertEqual(frames[0].getpixel((1,1)),(0,255,0,255))
    def test_anchor_transition(self):
        frames=interpolate_pose_anchors({'Idle':{'Sword':[0,0]},'Walk':{'Sword':[4,2]}},'Idle','Walk',3)
        self.assertEqual([f['Sword'] for f in frames],[[0,0],[2,1],[4,2]])
    def test_source_has_persistence_and_layer_remapping(self):
        s=(Path(__file__).resolve().parents[1]/'studio/app.py').read_text()
        for term in ("obj['layer_motion_keys']","obj.get('layer_motion_keys',{})",'keys_i=self.layer_motion_keys.pop','self.layer_motion_keys={str(int(k)-'):
            self.assertIn(term,s)
