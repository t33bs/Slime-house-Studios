"""Regression checks for the two-window architecture and its shared model."""
import ast
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from studio.core import Layer, Region, frames_for, compose_timeline_frames
from studio.history import capture, decode, UndoHistory

APP = Path(__file__).resolve().parents[1] / 'studio' / 'app.py'

class DualAnimatorQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = APP.read_text(encoding='utf-8')
        cls.tree = ast.parse(cls.source)

    def test_separate_dock_windows_have_independent_controls(self):
        src = self.source
        for name in ('animator_dock', 'advanced_animator_dock'):
            self.assertIn(f'self.{name}=QDockWidget(', src)
            self.assertIn(f'self.{name}.setWidget(', src)
            self.assertIn(f'self.{name}.hide()', src)
        self.assertIn('self.animator_button.clicked.connect(self.toggle_animator)', src)
        self.assertIn('self.advanced_animator_button.clicked.connect(self.toggle_advanced_animator)', src)
        self.assertIn('DockWidgetFloatable', src)
        self.assertIn('DockWidgetClosable', src)

    def test_quick_effect_and_timeline_controls_in_separate_layouts(self):
        src = self.source
        self.assertIn('av.addWidget(self.advanced_effects)', src)
        self.assertIn('av.addLayout(palette_row)', src)
        self.assertIn('self.advanced_layout.addWidget(self.frame_slider)', src)
        self.assertIn('self.advanced_layout.addWidget(self.export_settings)', src)
        self.assertIn('self.advanced_layout.addWidget(self.onion_enabled)', src)

    def test_effect_color_survives_project_roundtrip(self):
        layer = Layer('Cat', Image.new('RGBA', (64,64), (200, 100, 20, 255)))
        region = Region('Eyes', (10,10,8,8), effect='Laser Eyes', color=(255, 60, 70, 180))
        snapshot = capture((64,64), [layer], [region], [], {}, 12, 100, 0, 'Animated GIF (.gif)')
        size, layers, regions = decode(snapshot)
        self.assertEqual(size, (64,64))
        self.assertEqual(tuple(regions[0].color), (255,60,70,180))
        history = UndoHistory()
        history.record(snapshot)
        changed = capture((64,64), [layer], [Region('Eyes',(10,10,8,8), effect='Laser Eyes', color=(0,255,0,255))], [], {}, 12, 100, 0, 'Animated GIF (.gif)')
        restored = history.undo(changed)
        self.assertEqual(tuple(decode(restored)[2][0].color), (255,60,70,180))

    def test_all_effects_work_with_shared_frame_edits(self):
        sprite = Image.new('RGBA', (64,64))
        ImageDraw.Draw(sprite).rectangle((16,16,45,45), fill=(240,120,40,255))
        layer = Layer('Cat', sprite)
        region = Region('Head', (16,16,30,30), effect='Blink', strength=3)
        frames = frames_for([layer], (64,64), count=12, regions=[region])
        edits = {'3': [[4,4,255,0,255,255]]}
        combined = compose_timeline_frames([layer], (64,64), [region], 12, edits)
        self.assertEqual(len(combined), 12)
        self.assertEqual(combined[3].getpixel((4,4)), (255,0,255,255))
        self.assertEqual(combined[2].getpixel((4,4)), (0,0,0,0))

if __name__ == '__main__':
    unittest.main()
