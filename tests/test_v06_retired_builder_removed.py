from pathlib import Path

APP=(Path(__file__).resolve().parents[1]/'studio/app.py').read_text(encoding="utf-8")

def test_retired_dock_and_canvas_hooks_removed():
    for text in ('self.pet_workshop_dock=QDockWidget', 'self.pet_workshop_dock.hide()', 'self.refresh_pet_anchors();self.refresh_pet_regions()', "if tool=='Pet Region Select':", "if tool=='Pose Anchor':"):
        assert text not in APP

def test_legacy_project_metadata_preserved():
    assert "obj['pet_anchors']" in APP
    assert "obj['pet_regions']" in APP
    assert "obj.get('pet_anchors',{})" in APP
