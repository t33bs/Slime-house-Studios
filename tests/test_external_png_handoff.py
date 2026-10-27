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
                self.assertEqual(win.size_px,(128,128))
                self.assertEqual(win.layers[0].image.getpixel((20,30)),(20,220,90,255))
                self.assertTrue(win.external_save_button.isVisible() or not win.isVisible())
                win.layers[0].image.putpixel((20,30),(240,10,10,255))
                win.save_external_png()
                with Image.open(path) as result:
                    self.assertEqual(result.size,(128,128))
                    self.assertEqual(result.convert('RGBA').getpixel((20,30)),(240,10,10,255))
                    self.assertEqual(result.convert('RGBA').getpixel((0,0)),(0,0,0,0))
            finally:
                win.close()
