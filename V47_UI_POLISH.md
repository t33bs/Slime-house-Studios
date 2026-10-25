# Slime House Studios v47 — UI polish

Based on the expanded v46 crash-stability source.

- **Delete hotkey:** `Del` invokes the existing confirmed, undoable layer deletion. It does nothing with no selected layer, and leaves native Delete behavior alone in worksheet tables and text-editing widgets.
- **Cursor edge:** Move the tool crosshair 2 pixels inward on its transparent cursor bitmap; shift its hotspot by the same amount to preserve click alignment. This addresses the clipped left-side stroke without changing the canvas coordinate mapping.
- **NFT Worksheet:** Add 7 px inset to the "Column containing NFT numbers" label, and 9 px header padding to keep "Worksheet column" legible.

## Validation

Python syntax and source-level tests can run in this environment. PySide6 and a Windows GUI are not available here; visual appearance, keyboard focus and Windows builds must still be tested on Windows.

## Follow-up keyboard safety correction

Qt may consume a Delete shortcut before its callback decides to return. The
asset Delete shortcut is now disabled at focus-change time for text editors,
combo boxes, numeric inputs and non-layer item views, so worksheet Delete
continues to behave natively. This has been source-tested, not Windows GUI-tested.

## Follow-up deletion safety pass

- Guard the shared `remove_layer` handler against stale layer-list selection indices after project restore/reset.
- Add three source-level regression checks for model bounds, confirmed deletion routing, and focus-sensitive Delete shortcut.
- Validation: `python -m unittest discover -s tests -q` — 98 passed; `compileall` passed.
- Remaining: Windows GUI testing of maximize/restore, cursor appearance, native Delete in worksheet, undo after layer deletion, and installer output.
