import unittest
from pathlib import Path
APP=(Path(__file__).resolve().parents[1]/'studio/app.py').read_text(encoding='utf-8')

class V47PolishTests(unittest.TestCase):
    def test_delete_shortcut_uses_existing_undoable_layer_delete(self):
        self.assertIn("QShortcut(QKeySequence('Delete'),self)",APP)
        self.assertIn('self.remove_layer()  # Existing confirmation, undo checkpoint and cleanup.',APP)
        self.assertIn('if not 0<=self.layer_list.currentRow()<len(self.layers):',APP)
    def test_delete_respects_worksheet_editing(self):
        self.assertIn('self.delete_asset_shortcut.setEnabled(allowed)',APP)
        self.assertIn('focusChanged.connect(self.update_delete_shortcut_focus)',APP)
        self.assertIn('QAbstractItemView) and current is not self.layer_list',APP)
        self.assertIn('QLineEdit,QTextEdit,QPlainTextEdit',APP)
    def test_cursor_left_edge_has_clearance(self):
        self.assertIn('painter.drawLine(5,2,5,9);painter.drawLine(2,5,9,5)',APP)
        self.assertIn('return QCursor(pix,5,5)',APP)
    def test_worksheet_padding(self):
        self.assertIn('worksheet_column_label.setContentsMargins(7,0,0,0)',APP)
        self.assertIn('padding-left: 9px',APP)
