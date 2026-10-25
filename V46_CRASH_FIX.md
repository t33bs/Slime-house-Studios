# v46 — Crash stability source patch

## Fixed in source
- Keep retired hidden Desktop Pet dock alive as the QObject owner of legacy widgets still referenced by canvas and project restoration; no `deleteLater()` on the dock.
- Check shiboken widget validity before reading the pose-overlay checkbox, pose selector, anchor list, or region list.
- Block list selection signals while repopulating anchor/region lists to avoid reentrant callbacks during project reset, undo/redo, and recovery.
- Defer maximize/restore redraw and check canvas validity again when the queued callback executes.
- Keep existing project recovery, autosave, features, and installer workflow unchanged.

## Validation
- Python compileall: passed.
- Automated suite: 104 passed, 45 subtests passed on Linux.
- Windows GUI maximize/restore: NOT YET TESTED. No Windows installer included.

## Remaining Windows acceptance checks
1. Maximize/restore 10 times, then minimize and resize.
2. New project; undo/redo; save and reopen.
3. Recovery dialog after simulated interruption; confirm data is preserved.
4. Close/reopen surviving panels and inspect `%USERPROFILE%\\.slime_house_studios\\crash.log` for new errors.

## Scope note
This is a stabilization patch, not the later complete Desktop Pet Builder removal. The old dock is hidden but still retained to avoid dangling references. The patch cannot be considered confirmed fixed until tested on Windows.
