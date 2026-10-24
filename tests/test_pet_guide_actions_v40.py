from pathlib import Path

def test_pet_guide_action_wiring():
    source=(Path(__file__).resolve().parents[1]/'studio/app.py').read_text()
    for expected in ('def open_pet_guide_tool', 'def mark_pet_guide_step',
                     "self.tool.setCurrentText('Frame Pencil')", 'self.pet_studio_tabs.setCurrentIndex(1)',
                     'self.pet_guide_done.blockSignals(True)', 'self.pet_guide_tool.clicked.connect'):
        assert expected in source
