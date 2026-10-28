import os
import tempfile
import unittest
from pathlib import Path
from PIL import Image
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
try:
    from PySide6.QtWidgets import QApplication
    from studio.app import MainWindow
except ImportError:
    QApplication = None
    MainWindow = None

@unittest.skipIf(QApplication is None, "PySide6 unavailable in this environment")
class ExternalPNGTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def test_open_edit_save_png_and_canvas_size(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'frame.png'
            img=Image.new('RGBA',(128,128),(0,0,0,0))
            img.putpixel((20,30),(20,220,90,255))
            img.save(path)
            win=MainWindow()
            try:
                win.open_external_png(path)
                self.assertFalse(win._dirty, 'Opening a PNG must not trigger an unsaved-changes dialog')
                self.assertEqual(win.size_px,(128,128))
                self.assertEqual(win.layers[0].image.getpixel((20,30)),(20,220,90,255))
                self.assertTrue(win.external_save_button.isVisible() or not win.isVisible())
                win.layers[0].image.putpixel((20,30),(240,10,10,255))
                win.save_external_png()
                self.assertFalse(win._dirty, 'Saving linked PNG should clear unsaved changes')
                with Image.open(path) as result:
                    self.assertEqual(result.size,(128,128))
                    self.assertEqual(result.convert('RGBA').getpixel((20,30)),(240,10,10,255))
                    self.assertEqual(result.convert('RGBA').getpixel((0,0)),(0,0,0,0))
            finally:
                # A modal unsaved-changes prompt blocks headless CI indefinitely.
                # Explicitly suppress dialogs during test teardown even if an
                # assertion fails before the save-back step.
                win._dirty = False
                win.close()
