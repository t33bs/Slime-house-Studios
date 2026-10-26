# Slime House Studios v0.6.1 — Laser emitter tool fix

Restores **Move Laser Asset** to the main editor tool dropdown. The existing
Junior Animator **Add movable Laser Eyes** action selects this tool, and the
canvas mouse handlers already support it. This patch allows the handle to
remain available for repositioning while the tool is selected.

To test on Windows: stop preview, add movable Laser Eyes, select its region,
choose Move Laser Asset, drag emitter to the eye, preview, save/reopen project.

This is a source package; it is not a rebuilt Windows installer.
