"""Source wiring checks; live Windows GUI verification still required."""
import unittest
from pathlib import Path
APP=(Path(__file__).resolve().parents[1]/'studio/app.py').read_text(encoding='utf-8')
class ToolActivationTests(unittest.TestCase):
    def test_selection_changes_activate_tool(self):
        self.assertIn('self.tool.currentTextChanged.connect(self.activate_tool)',APP)
        self.assertIn('self.active_tool_banner.setText(',APP)
    def test_no_accidental_transform_with_other_tools(self):
        self.assertIn("if tool!='Move / Transform':return",APP)
    def test_highlighter_and_preview_help(self):
        self.assertIn('self.highlight_button.clicked.connect(self.begin_highlighting)',APP)
        self.assertIn('if not any(r.mask for r in self.regions):',APP)
    def test_auto_select_layer_when_drawing(self):
        self.assertIn("self.layer_list.setCurrentRow(len(self.layers)-1)",APP)
