# Slime House Studios v0.6.1 — UI and Drawing Improvements

- Removed redundant Project tab (File menu and left sidebar retain save/open project actions).
- Added Recenter Canvas button to reset zoom and pan.
- Added Spray Can drawing tool with pixel radius and density controls, using crisp single-pixel spatter on editable paint layers.
- Added persistent Laser Eyes angle (0–359 degrees), numeric angle control, emitter handle and draggable yellow aiming handle in Move Laser Asset mode. Angles are stored in project JSON and used for rendering.

Notes: GUI smoke testing requires PySide6 on Windows; this environment lacks PySide6. Existing unit suite and source compilation pass. The source ZIP is not a Windows executable or installer.
