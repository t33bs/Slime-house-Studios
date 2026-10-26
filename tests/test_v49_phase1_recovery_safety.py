import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from studio.history import atomic_write, UndoHistory


class RecoverySafetyTests(unittest.TestCase):
    def test_atomic_write_replaces_existing_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'recovery.json'
            atomic_write(path, {'layers': [1]})
            atomic_write(path, {'layers': [2]})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {'layers': [2]})
            self.assertEqual(list(Path(folder).glob('.slime-*.tmp')), [])

    def test_atomic_write_failure_preserves_previous_recovery(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'recovery.json'
            atomic_write(path, {'original': True})
            with patch('studio.history.os.replace', side_effect=OSError('disk error')):
                with self.assertRaises(OSError):
                    atomic_write(path, {'original': False})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {'original': True})
            self.assertEqual(list(Path(folder).glob('.slime-*.tmp')), [])

    def test_undo_redo_are_independent_snapshots(self):
        history = UndoHistory(limit=3)
        before = {'layers': [{'x': 1}]}
        history.record(before)
        before['layers'][0]['x'] = 500
        prior = history.undo({'layers': [{'x': 2}]})
        self.assertEqual(prior['layers'][0]['x'], 1)
        prior['layers'][0]['x'] = 700
        restored = history.redo({'layers': [{'x': 1}]})
        self.assertEqual(restored['layers'][0]['x'], 2)

    def test_close_guard_prevents_exit_when_recovery_fails(self):
        source = (Path(__file__).resolve().parents[1] / 'studio' / 'app.py').read_text(encoding="utf-8")
        self.assertIn('if not self.write_recovery():', source)
        self.assertIn('event.ignore();return', source)
        self.assertIn('The recovery file has been preserved', source)

if __name__ == '__main__':
    unittest.main()
