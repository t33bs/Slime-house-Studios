import tempfile
import unittest
from pathlib import Path
from studio.safe_export import safe_export

class TestAtomicExports(unittest.TestCase):
    def test_success_replaces_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'art.apng';p.write_bytes(b'old')
            safe_export(p,lambda tmp:tmp.write_bytes(b'new'),lambda tmp:self.assertEqual(tmp.read_bytes(),b'new'))
            self.assertEqual(p.read_bytes(),b'new')
            self.assertEqual(sorted(x.name for x in Path(folder).iterdir()),['art.apng'])

    def test_write_failure_preserves_existing(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'art.apng';p.write_bytes(b'old')
            def fail(tmp):
                tmp.write_bytes(b'partial')
                raise RuntimeError('encoder failed')
            with self.assertRaises(RuntimeError):safe_export(p,fail)
            self.assertEqual(p.read_bytes(),b'old')
            self.assertEqual(sorted(x.name for x in Path(folder).iterdir()),['art.apng'])

    def test_validation_failure_preserves_existing(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'art.gif';p.write_bytes(b'old')
            def fail_validation(tmp):raise ValueError('not animated')
            with self.assertRaises(ValueError):safe_export(p,lambda tmp:tmp.write_bytes(b'bad'),fail_validation)
            self.assertEqual(p.read_bytes(),b'old')
            self.assertEqual(sorted(x.name for x in Path(folder).iterdir()),['art.gif'])

    def test_failure_does_not_create_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'art.png'
            with self.assertRaises(ValueError):safe_export(p,lambda tmp:(_ for _ in ()).throw(ValueError('failed')))
            self.assertFalse(p.exists())
            self.assertEqual(list(Path(folder).iterdir()),[])

if __name__=='__main__':unittest.main()
