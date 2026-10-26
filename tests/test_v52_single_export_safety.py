import ast
import unittest
from pathlib import Path
from PIL import Image
from studio.safe_export import safe_export
import tempfile

class TestSingleFormatExportSafety(unittest.TestCase):
    def test_each_entrypoint_uses_safe_export(self):
        source=(Path(__file__).resolve().parents[1]/'studio'/'app.py').read_text(encoding="utf-8")
        tree=ast.parse(source)
        app=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MainWindow') if any(isinstance(n,ast.ClassDef) and n.name=='MainWindow' for n in tree.body) else None
        # Find methods independently of class naming.
        methods={n.name:n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        for method in ('save_apng','save_gif','save_png','export_canvas_png','export_selected_format'):
            self.assertIn(method,methods)
            calls=[n for n in ast.walk(methods[method]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='safe_export']
            self.assertTrue(calls,method)

    def test_still_failure_preserves_previous_png(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'art.png'
            Image.new('RGBA',(2,2),'red').save(p)
            original=p.read_bytes()
            def failed_writer(temp):
                Image.new('RGBA',(2,2),'blue').save(temp)
                raise RuntimeError('failed after write')
            with self.assertRaises(RuntimeError):safe_export(p,failed_writer)
            self.assertEqual(p.read_bytes(),original)

if __name__=='__main__':unittest.main()
