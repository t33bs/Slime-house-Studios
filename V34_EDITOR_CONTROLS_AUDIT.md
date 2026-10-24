# v34 — Editor control consistency pass

- Retains File/Edit/View menus, New Project, Undo/Redo, wheel zoom, B/E/I shortcuts, and animation tools from previous versions.
- `+`, `=` and `-` now target the **currently selected adjustable tool**. Pencil, Eraser, Frame Pencil, Frame Eraser, Mask Brush, and Mask Eraser each remember their own brush diameter during the session.
- Tools with no brush diameter do not silently change the pencil size.
- Main canvas and frame drawing still share the same on-screen brush-size spinbox, and Junior masks use the mask-size spinbox; switching tools restores the active tool's own value.
- Current range is 1–32 pixels; zoom remains a separate mouse-wheel control.

## Validation
Automated Python tests pass. GUI mouse interactions, shortcut focus handling, and Windows EXE/installer still require manual Windows testing. No claim of comprehensive end-to-end verification is made.

## Known limitations
- The size settings are per-session, not persisted across launches.
- Shape/selection region and pose anchor are coordinate/selection tools, not brushes; no artificial size control has been added to them.
- Earlier reports of Pencil not drawing in all animator contexts need a Windows GUI regression test; automated source tests alone cannot verify mouse behavior.
