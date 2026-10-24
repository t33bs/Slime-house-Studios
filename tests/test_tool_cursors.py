import unittest
from pathlib import Path
APP=(Path(__file__).resolve().parents[1]/'studio/app.py').read_text(encoding='utf-8')
class CursorWiringTests(unittest.TestCase):
    def test_each_tool_has_icon(self):
        for name in ('Pencil','Eraser','Mask Brush','Mask Eraser','Frame Pencil','Frame Eraser','Animation Region'):
            self.assertIn("'"+name+"':",APP)
    def test_tool_switch_updates_cursor(self):
        self.assertIn('self.canvas.setCursor(cursor_for_tool(tool))',APP)
        self.assertIn('return QCursor(pix,3,3)',APP)
    def test_transform_uses_hand(self):
        self.assertIn('Qt.CursorShape.OpenHandCursor',APP)
