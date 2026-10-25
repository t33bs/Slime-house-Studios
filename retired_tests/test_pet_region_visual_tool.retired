from pathlib import Path


def test_pet_region_canvas_workflow_wired():
    code = (Path(__file__).resolve().parents[1] / 'studio' / 'app.py').read_text()
    assert "'Pet Region Select'" in code
    assert "visual_region.clicked.connect(self.activate_pet_region_selector)" in code
    assert "self.drag=['pet-region',(x,y),(x,y)]" in code
    assert "m.save_pet_region()" in code
    assert "if self.drag and self.drag[0]=='pet-region':" in code
