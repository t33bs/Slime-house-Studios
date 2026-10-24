import tempfile
import unittest
from pathlib import Path
from PIL import Image
from studio.core import Layer
from studio.history import UndoHistory, capture, decode, atomic_write
import json

class HistoryTests(unittest.TestCase):
    def test_snapshot_is_independent_and_restores_pixels(self):
        layer = Layer('test', Image.new('RGBA', (4, 4), (255, 0, 0, 255)))
        snap = capture((4, 4), [layer], [], {}, {}, 8, 100, 0, 0)
        layer.image.putpixel((0, 0), (0, 0, 255, 255))
        size, layers, _ = decode(snap)
        self.assertEqual(size, (4, 4))
        self.assertEqual(layers[0].image.getpixel((0, 0)), (255, 0, 0, 255))

    def test_undo_redo_and_branch(self):
        h = UndoHistory(2)
        h.record({'value': 1})
        self.assertEqual(h.undo({'value': 2}), {'value': 1})
        self.assertEqual(h.redo({'value': 1}), {'value': 2})
        h.record({'value': 2})
        self.assertIsNone(h.redo({'value': 3}))

    def test_atomic_backup_and_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'backup.json'
            atomic_write(path, {'size': [64, 64], 'layers': []})
            self.assertEqual(json.loads(path.read_text(encoding='utf-8'))['size'], [64, 64])
            self.assertEqual(list(Path(directory).glob('*.tmp')), [])

    def test_reject_bad_dimensions(self):
        with self.assertRaises(ValueError):
            decode({'size': [True, 64], 'layers': []})
