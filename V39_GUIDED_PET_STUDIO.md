# v39: Guided Desktop Pet Studio (first UI pass)

The Desktop Pet & Creature Studio now opens on **Create • Step by Step** instead of presenting the full settings panel. Choose an existing creature PNG or use the current canvas, select an animation, and navigate a task-oriented recipe: preparation, individual key poses, preview, and export.

The old builder controls are preserved under **Advanced / Export**. No mandatory wizard, no removed presets, no forced automatic generation. This is a first usability pass; drawing-step auto-activation, visual pose references, and persistent per-animation completion tracking are not yet implemented.

## Validation
Python unit tests pass. Windows Qt interaction and layout must still be checked in a built EXE.
