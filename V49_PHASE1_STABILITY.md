# v49 — Phase 1 stability hardening

Changes made on top of v48:

- Recovery backups now report success or failure. Closing an unsaved project is blocked if the backup write fails, rather than silently risking data loss.
- Recovery restore failures are logged and the backup is preserved for retry.
- Snapshot restoration blocks layer/region selection callbacks while replacing list items, preventing reentrant selection events against deleted Qt items.
- Added recovery atomic-write failure tests and undo/redo snapshot independence tests.

Validation: Python compilation passed; 102 unit tests passed in this Linux environment. PySide6 is unavailable, so no native GUI, Windows maximize, panel-lifecycle, or GitHub Actions build was run. The v46 legacy hidden dock workaround remains; full removal is a separate phase. The test suite includes source-level assertions and does not substitute for real Windows UI testing.

Windows acceptance checklist:
1. Maximize/restore repeatedly; minimize and resize; inspect crash.log.
2. Close/reopen panels; New Project; Undo/Redo; save and reopen project.
3. Make unsaved changes, close with recovery, restart and restore; verify layers.
4. Simulate an unwritable recovery directory; confirm closing is blocked and manual Save Project remains possible.
5. Check the recovery file remains after an invalid/corrupt backup triggers a restore error.
