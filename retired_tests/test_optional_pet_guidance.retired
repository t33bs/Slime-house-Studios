from pathlib import Path
from PIL import Image
from studio.pet_sprite_wizard import export_package

def test_manual_custom_sheet_exports_single_frame(tmp_path):
    frame = Image.new('RGBA', (16, 16), (12, 24, 36, 255))
    meta = export_package({'Custom': [frame]}, tmp_path, 'pet', frame_pngs=True, gif=False, apng=False)
    assert meta['animations']['custom']['frames'][0]['w'] == 16
    assert (tmp_path / 'pet_sheet.png').exists()
    assert (tmp_path / 'pet_animations.json').exists()

def test_optional_controls_wired():
    source = (Path(__file__).resolve().parents[1] / 'studio' / 'app.py').read_text(encoding='utf-8')
    assert 'pet_suggestions_toggle.toggled.connect(self.update_pet_suggestions)' in source
    assert 'pet_auto_toggle.toggled.connect(self.update_pet_auto_generation)' in source
    assert 'self.pet_recipe_group.setVisible(bool(enabled))' in source
    assert 'manual_button.clicked.connect(self.export_manual_pet_sprite)' in source
