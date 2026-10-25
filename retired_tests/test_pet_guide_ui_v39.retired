from pathlib import Path

def test_pet_builder_guided_entry_and_advanced_export():
    source=(Path(__file__).resolve().parents[1]/'studio'/'app.py').read_text()
    for phrase in ('Create • Step by Step', 'Advanced / Export', 'Prepare your creature',
                   'Preview and refine the timing', 'Export your sprite sheet',
                   'def move_pet_guide', 'def refresh_pet_guide',
                   'self.pet_guide_action.currentTextChanged.connect'):
        assert phrase in source
