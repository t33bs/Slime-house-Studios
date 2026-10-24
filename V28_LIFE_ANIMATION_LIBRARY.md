# v28 — Everyday Life Animation Library

This update builds on v27, preserving all three studios and the optional-guidance controls.

## Added
- 31 named non-battle animation recipes in the Desktop Pet Builder, grouped separately from the legacy and battle presets.
- Each recipe includes needed body parts, key poses, drawing advice, looping suggestions and frame-by-frame instructions.
- Starter motion generation for all 31 names, reusing existing simple whole-sprite motion families.
- Six body-type pose preparation templates with suggested editable body parts.
- Export-compatible names (e.g. `sad_lonely`, `flying_hovering`) for JSON and frame folders.
- Original legacy and battle presets remain available.

## Important limits
- This does NOT yet animate individual limbs, facial features, or true 3D turning from a single flat PNG. Motion is a draft, not an inferred creature rig.
- Body-type templates currently provide *guidance*, not articulated pose generation.
- Some actions currently share the same starter motion pattern; their recipe text describes the distinct art needed.
- Automatic generation is still opt-in; recipes can be hidden; manual export remains available.
- The Windows executable has not been visually tested in this environment.

## Verification
Run `python -m pytest -q` in the project root. Last run: 87 passed, 45 subtests passed.
