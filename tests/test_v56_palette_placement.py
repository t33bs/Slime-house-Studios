from pathlib import Path


def test_palette_above_tool_and_studio_buttons():
    source = (Path(__file__).resolve().parents[1] / 'studio' / 'app.py').read_text()
    assert source.index("color=QPushButton('Choose brush color')") < source.index("lv.addWidget(QLabel('YOUR ACTIVE TOOL'))")
    assert source.index('lv.addWidget(palette)') < source.index("self.animator_button=QPushButton")
    assert source.index('lv.addWidget(palette)') < source.index("self.advanced_animator_button=QPushButton")
    assert source.index('lv.addWidget(color)') < source.index('lv.addWidget(palette)')
