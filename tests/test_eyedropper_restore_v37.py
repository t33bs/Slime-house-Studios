from pathlib import Path

def test_eyedropper_restores_brush_not_eraser():
    source = (Path(__file__).resolve().parents[1] / 'studio' / 'app.py').read_text(encoding='utf-8')
    assert "'Eraser':'Pencil'" in source
    assert "'Frame Eraser':'Frame Pencil'" in source
    assert "'Mask Eraser':'Mask Brush'" in source
    assert 'self.eyedropper_previous_tool=previous' in source
    assert 'm.tool.setCurrentText(previous)' in source
