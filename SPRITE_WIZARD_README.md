# v25 — Desktop Pet Sprite Sheet Wizard (first working implementation)

Built on the existing v24 Windows encoding-fix source; preserves the three studios and existing features.

## Using it
1. Open Desktop Pet & Creature Studio.
2. In Sprite Sheet Wizard, choose a transparent PNG, or leave blank for the current canvas.
3. Tick animation presets and set frames/FPS.
4. Click Generate Sprite Sheet Package, choose an export folder and prefix.
5. Find `*_sheet.png`, `*_animations.json`, optional frame PNGs, GIFs and APNG previews.

## Current limits
This first pass animates flattened images with deterministic whole-sprite movements and simple pixel effects. It does not create newly drawn poses or articulated limbs. Blink deliberately stays unchanged without marked eye regions. Eating uses bobbing, sleeping uses squash/breathing, pooping uses squat plus tiny pixel prop. The resulting frames are starter frames intended for later editing. Identical GIF/APNG frames may be coalesced by Pillow, but the sprite sheet retains every cell. Generated frames are not yet automatically imported into the Intermediate Studio timeline.

## Validation
79 automated tests pass. Windows EXE/installer and visual GUI verification remain outstanding.
