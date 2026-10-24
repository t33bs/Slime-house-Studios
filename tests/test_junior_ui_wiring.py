"""Source-level checks for Junior animator controls (not a Qt runtime test)."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class JuniorWiringTests(unittest.TestCase):
    def test_highlighter_button_connects_to_tool(self):
        app=(ROOT/'studio/app.py').read_text(encoding='utf-8')
        self.assertIn('self.highlight_button.clicked.connect(self.begin_highlighting)',app)
        self.assertIn("self.tool.setCurrentText('Mask Brush')",app)
        self.assertIn('m.add_region((0,0,*m.size_px))',app)
    def test_preview_button_and_timer_connected(self):
        app=(ROOT/'studio/app.py').read_text(encoding='utf-8')
        self.assertIn('self.junior_preview_button.clicked.connect(self.start_preview)',app)
        self.assertIn('self.timer.start(self.duration.value())',app)
        self.assertIn('self.preview=self.make_frames()',app)
    def test_installer_and_workflow_exist(self):
        iss=(ROOT/'installer.iss').read_text(encoding='utf-8')
        flow=(ROOT/'.github/workflows/build-windows.yml').read_text(encoding='utf-8')
        self.assertIn('SlimeHouseStudios-Setup',iss)
        self.assertIn('ISCC.exe',flow)
        self.assertIn('SlimeHouseStudios-Installer-Windows',flow)
