from pathlib import Path

def test_mask_brush_initialized_before_signal_connected():
    text = (Path(__file__).resolve().parents[1] / 'studio' / 'app.py').read_text(encoding='utf-8')
    creation = text.index('self.mask_brush=QSpinBox()')
    connection = text.index('self.mask_brush.valueChanged.connect(self._remember_active_tool_size)')
    assert creation < connection
