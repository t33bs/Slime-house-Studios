import unittest
from pathlib import Path
APP=(Path(__file__).resolve().parents[1]/'studio/app.py').read_text(encoding='utf-8')
class PhaseOneCompletion(unittest.TestCase):
    def test_only_three_studios(self):
        self.assertIn('Open Junior Animator',APP)
        self.assertIn('Open Intermediate Studio',APP)
        self.assertIn('Legacy Desktop Pet Builder (retired)',APP)
        self.assertNotIn('Senior Animator',APP)
    def test_visual_pose_anchors(self):
        for term in ('Pose Anchor','place_anchor','show_pet_anchors','pet_anchors'):
            self.assertIn(term,APP)
    def test_multiple_frame_tracks(self):
        for term in ('frame_tracks','add_frame_track','remove_frame_track','sync_frame_edits'):
            self.assertIn(term,APP)
    def test_reset_and_erasers(self):
        for term in ('reset_current_frame','reset_layer_mesh','remove_pet_anchor','Frame Eraser'):
            self.assertIn(term,APP)
    def test_project_serialization(self):
        self.assertIn("obj['frame_tracks']",APP)
        self.assertIn("obj.get('frame_tracks')",APP)
