import unittest
from PIL import Image
from studio.core import Layer, compose_timeline_frames, export_apng
from tempfile import TemporaryDirectory
from pathlib import Path

class TimelineTests(unittest.TestCase):
    def test_frame_edit_and_erase(self):
        layer=Layer('base',Image.new('RGBA',(8,8),(10,20,30,255)))
        edits={'1':[[2,3,255,0,0,255]],'2':[[2,3,0,0,0,0]]}
        frames=compose_timeline_frames([layer],(8,8),[],4,edits)
        self.assertEqual(frames[0].getpixel((2,3)),(10,20,30,255))
        self.assertEqual(frames[1].getpixel((2,3)),(255,0,0,255))
        self.assertEqual(frames[2].getpixel((2,3)),(0,0,0,0))
        with TemporaryDirectory() as tmp:
            p=export_apng(frames,Path(tmp)/'animation.apng')
            with Image.open(p) as im:
                self.assertGreaterEqual(im.n_frames,2)
                self.assertEqual(im.size,(8,8))

    def test_frame_edit_out_of_bounds(self):
        frames=compose_timeline_frames([], (4,4), [], 2, {'1':[[50,50,1,2,3,255]]})
        self.assertEqual(frames[1].getbbox(),None)
