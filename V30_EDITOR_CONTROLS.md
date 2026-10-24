# v30 — Classic editor controls

## New
- Application-wide File / Edit / View menu in the upper-left.
- File > New Project (Ctrl+N) with Save / Discard / Cancel confirmation for unsaved changes; clears the document, animation tracks, rig regions and undo history.
- File > Open, Save, Import PNG, Export.
- Edit > Undo / Redo; existing Ctrl+Z, Ctrl+Shift+Z and Ctrl+Y shortcuts retained.
- Canvas wheel zoom about mouse pointer; View > Reset Canvas Zoom (Ctrl+0), Zoom In / Zoom Out.
- `+`, `=` and `-` shortcuts increase/decrease brush size by one pixel. Works on Pencil, Eraser, Frame Pencil and Frame Eraser; for Mask Brush/Mask Eraser adjusts the mask brush size.

## Testing
- Python syntax compiled successfully.
- 90 automated tests and 45 subtests passed.
- Qt GUI and Windows EXE could not be launched here (PySide6 is not installed in this test environment). Please verify wheel zoom, menu behavior and keyboard focus in the Windows build.

## Notes
- Scroll zoom only affects canvas display, not the artwork or export resolution.
- Zoom remains nearest-neighbor.
- New Project starts at 64x64 and resets the zoom.
