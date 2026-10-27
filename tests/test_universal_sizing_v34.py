from pathlib import Path
import ast

APP = Path(__file__).resolve().parents[1] / 'studio' / 'app.py'

def test_shortcuts_and_size_controls_exist():
    src = APP.read_text(encoding='utf-8')
    assert "('B',self.activate_universal_brush)" in src
    assert "('E',self.activate_universal_eraser)" in src
    assert "('I',self.activate_eyedropper)" in src
    assert "('+',lambda:self.adjust_brush_size(1))" in src
    assert "('-',lambda:self.adjust_brush_size(-1))" in src
    assert 'self._tool_sizes[tool] = value' in src
    assert 'self._restore_active_tool_size(tool)' in src
    ast.parse(src)

def test_all_drawable_tools_have_size_controls():
    src = APP.read_text(encoding='utf-8')
    for name in ('Pencil', 'Eraser', 'Frame Pencil', 'Frame Eraser', 'Mask Brush', 'Mask Eraser'):
        assert name in src
    assert 'if control is None:' in src
