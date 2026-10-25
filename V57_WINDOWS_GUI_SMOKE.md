# v57 — Windows GUI smoke testing in GitHub Actions

Adds a real PySide6 GUI smoke test before PyInstaller packaging in `.github/workflows/build-windows.yml`.

The test creates the main window and processes real Qt events while maximizing/restoring ten times, resizing, opening/closing the NFT and animation docks, restoring a project snapshot, and repainting the canvas. Uncaught Qt/Python exceptions fail the build instead of silently passing unit tests. It disables recovery prompts and autosave only within the smoke test, not in the application.

## Validation
- Python compileall: passed.
- Linux non-GUI unit tests: 114 tests passed (subtests are counted separately by unittest).
- Windows GUI test: NOT RUN HERE. It runs on the Windows GitHub Actions runner before building the EXE.
- GitHub push/build: NOT PERFORMED.

## Limitations
The smoke test does not replace hands-on Windows testing, nor does it verify a frozen EXE's runtime, visual cursor placement, or real crash recovery after an abrupt shutdown.
