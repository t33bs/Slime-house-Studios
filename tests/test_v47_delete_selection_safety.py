"""Regression checks for asset deletion and native worksheet editing."""
import ast
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / 'studio' / 'app.py'

class DeleteSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse(APP.read_text(encoding='utf-8'))
        cls.window = next(n for n in cls.tree.body if isinstance(n, ast.ClassDef) and n.name == 'MainWindow')

    def method(self, name):
        return next(n for n in self.window.body if isinstance(n, ast.FunctionDef) and n.name == name)

    def test_remove_layer_checks_model_bounds(self):
        method = self.method('remove_layer')
        source = ast.get_source_segment(APP.read_text(encoding='utf-8'), method)
        self.assertIn('if 0<=i<len(self.layers):', source)
        self.assertIn('self.checkpoint()', source)
        self.assertIn('self.layers.pop(i)', source)

    def test_delete_hotkey_uses_existing_confirmed_delete(self):
        source = ast.get_source_segment(APP.read_text(encoding='utf-8'), self.method('delete_selected_asset'))
        self.assertIn('self.remove_layer()', source)
        self.assertIn('QAbstractItemView', source)

    def test_focus_disables_shortcut_for_worksheet_and_text(self):
        source = ast.get_source_segment(APP.read_text(encoding='utf-8'), self.method('update_delete_shortcut_focus'))
        self.assertIn('current.parentWidget()', source)
        self.assertIn('current is not self.layer_list', source)
        self.assertIn('self.delete_asset_shortcut.setEnabled(allowed)', source)

if __name__ == '__main__': unittest.main()
