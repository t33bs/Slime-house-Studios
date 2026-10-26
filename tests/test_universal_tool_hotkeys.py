from pathlib import Path

def test_universal_shortcuts_are_registered():
    source=(Path(__file__).resolve().parents[1]/'studio'/'app.py').read_text(encoding='utf-8')
    assert "('B',lambda:self.tool.setCurrentText('Mask Brush'))" in source
    assert "('E',self.activate_universal_eraser)" in source
    assert "('I',self.activate_eyedropper)" in source

def test_universal_tools_preserve_editor_context():
    source=(Path(__file__).resolve().parents[1]/'studio'/'app.py').read_text(encoding='utf-8')
    assert "'frame':'Frame Pencil'" in source
    assert "'frame':'Frame Eraser'" in source
    assert "'mask':'Mask Brush'" in source
    assert "'mask':'Mask Eraser'" in source
