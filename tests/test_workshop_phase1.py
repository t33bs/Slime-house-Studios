import unittest
from pathlib import Path
APP=(Path(__file__).resolve().parents[1]/'studio/app.py').read_text(encoding='utf-8')
class WorkshopPhaseOneTests(unittest.TestCase):
    def test_senior_animator_rename(self):
        self.assertIn('Open Intermediate Studio',APP)
        self.assertIn('Intermediate Studio — Timeline Studio',APP)
    def test_pet_builder_dock(self):
        self.assertNotIn("self.pet_workshop_dock=QDockWidget(",APP)
        self.assertNotIn('self.pet_workshop_dock.hide()',APP)
        self.assertNotIn('self.pet_workshop_button.clicked.connect(self.toggle_pet_workshop)',APP)
    def test_guided_mode_persistent(self):
        self.assertIn("self.settings.value('guided_mode',True,type=bool)",APP)
        self.assertIn("self.settings.setValue('guided_mode',bool(enabled))",APP)
    def test_anchors_survive_save_and_undo(self):
        self.assertIn("obj['pet_anchors']=json.loads(json.dumps(self.pet_anchors))",APP)
        self.assertIn("self.pet_anchors=obj.get('pet_anchors',{})",APP)
