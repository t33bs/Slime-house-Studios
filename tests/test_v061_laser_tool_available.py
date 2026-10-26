import unittest
from pathlib import Path

class LaserToolAvailability(unittest.TestCase):
    def test_laser_tool_in_dropdown_and_selected_by_button(self):
        source = (Path(__file__).resolve().parents[1] / 'studio' / 'app.py').read_text(encoding='utf-8')
        self.assertIn("'Move Laser Asset':'1'", source)
        self.assertIn("self.tool.setCurrentText('Move Laser Asset')", source)

if __name__ == '__main__':
    unittest.main()
