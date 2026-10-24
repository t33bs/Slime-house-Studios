# v26 — Guided Desktop Pet Sprite Sheet Wizard

Built on the v25 sprite sheet wizard and the existing PySide6 application; no fourth studio.

## New in v26
- **Animation Recipe** panel in Desktop Pet & Creature Studio. Pick any of the 13 existing animation presets to see required parts, key poses, a drawing tip, playback recommendation, and a numbered frame-by-frame plan.
- Body-type dropdown records the creature type in the recipe output. **The recipes are not yet body-type-specific**; that is a future enhancement.
- Exporting a sprite sheet package also saves `<name>_animation_guide.txt` (human-readable instructions) and `<name>_animation_recipes.json` (structured creation guidance), in addition to the sprite sheet and its game metadata and optional PNG/GIF/APNG frames.
- Tests for every animation recipe and both guidance exports.

## Important limitations
- This is **guided planning**, not generative AI or automated drawing of new anatomy.
- The v25 motion generator remains limited to simple whole-body motion; eye, mouth and articulated limb animation need manually prepared artwork/layers.
- Generated frames are not automatically loaded into the Intermediate Studio timeline.
- Windows runtime GUI validation and installer build still need testing on Windows.

## Quick start
Open **Desktop Pet & Creature Studio** > **Sprite Sheet Wizard** > **Animation Recipe**. Choose Eat, Sleep, Poop, or any battle action to see how to prepare and draw its frames. Generate the package to save the guidance files alongside the sprite sheet.

## Tests
Run `python -m unittest discover -s tests -q` from the project root.
