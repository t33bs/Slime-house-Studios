import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'studio' / 'app.py'

def test_right_click_is_transient_and_context_aware():
    source = SOURCE.read_text(encoding='utf-8')
    ast.parse(source)
    assert 'Qt.MouseButton.RightButton' in source
    assert "self.drag=['right-erase',context]" in source
    assert "self.erase_at(x,y,self.drag[1])" in source
    assert 'def erase_at(self,x,y,context):' in source
    assert 'self.frame_paint_at(x,y,erase=True)' in source
    assert 'self.mask_at(x,y,erase=True)' in source
    assert 'self.paint_at(x,y,erase=True)' in source
    assert 'm.tool.setCurrentText(' not in source.split('    def erase_at(self,x,y,context):',1)[1].split('    def sample_color_at',1)[0]
