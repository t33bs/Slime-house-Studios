# v43 — Main Window Stability / Crash Diagnostics

Reported: Windows main window closes/crashes when maximized.

Changes:
- Disable Qt animated docking relayout during maximize/restore.
- Record main-window state changes in a persistent log.
- Enable Python exception and faulthandler diagnostics in the frozen EXE.

If it crashes again, inspect `%USERPROFILE%\.slime_house_studios\crash.log` and share the last lines. Native GPU/Qt crashes may still require Windows Event Viewer; this is a defensive patch, not proof the underlying issue is fixed.

The creature rig, recipes, editor tools and sprite exporter are unchanged.
