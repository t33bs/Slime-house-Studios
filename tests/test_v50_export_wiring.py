from pathlib import Path
import unittest


class TestChooseFormatsWiring(unittest.TestCase):
    def test_apng_uses_explicit_extension(self):
        source = (Path(__file__).resolve().parents[1] / 'studio' / 'app.py').read_text(encoding="utf-8")
        block = source.split('    def export_choose_formats(self):', 1)[1].split('    def save_gif(self):', 1)[0]
        self.assertIn("('_animated.apng','_animated.gif','_still.png')", block)
        self.assertIn("output/(name+'_animated.apng')", block)
        self.assertIn('export_apng(frames,path,', block)
        self.assertIn("path.suffix in ('.gif','.apng')", block)
        self.assertIn('safe_export(path,write,validator)', block)


if __name__ == '__main__':
    unittest.main()
