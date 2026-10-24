# Standalone Desktop Pet Suite v44 — first functional foundation

Entry point: `python desktop_pet_suite.py` (requires PySide6 and Pillow).
Windows EXE: run GitHub Actions **Build Desktop Pet Suite Windows EXE** after uploading to the repo.

Implemented: independent maximizable window, three work areas (assets, templates and frame editor, comparison), import multiple PNG parts, nearest-neighbor sizing with optional aspect lock, pixel placement, pose capture per animation, saved-frame preview, editable rig save/open, sprite-sheet PNG+JSON export. Existing main Slime House Studios entry point is retained.

**Not yet implemented**: drag-to-resize, pivot joints, actual generic animated reference footage (currently text guide), true sprite-sheet slot editing, onion skin, robust undo/redo, autosave/crash recovery, 31 full action templates, GIF/APNG export, hitboxes, body-type-aware generation, project portability bundling originals, transition editor. These are tracked requirements, not delivered functionality. Windows EXE has not been executed/tested on Windows in this environment.
