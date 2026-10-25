# v48 — Canvas and export actions

- Visible **New Project**, **Clear Canvas**, **Save PNG**, and **Save Project** buttons in the left sidebar.
- **Clear Canvas** asks for confirmation, preserves canvas size, and records an Undo checkpoint. It removes artwork, animation regions, and animation tracks while retaining the current trait metadata.
- **New Project** uses the existing unsaved-work confirmation and resets the document.
- **Save PNG** exports a flattened still image; **Save Project** retains editable JSON.
- Added File menu entries for PNG and Clear Canvas.
- Removed duplicate Ctrl+N shortcut registration; the File menu owns it.

Validation: Python compilation and 111 available automated tests passed. PySide6 is not installed in the test environment, so actual Qt/Windows GUI interaction remains unverified.
