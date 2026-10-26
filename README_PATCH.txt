Slime House Studios — Hotkeys + Junior Animator duration update

Files in this ZIP replace their corresponding files in your existing repository.
Keep your existing .git directory and all other files. Do not overwrite the entire repo.

Changes:
- Tool dropdown displays hotkeys while preserving internal tool identifiers.
- M Move/Transform, P Pencil, B Mask Brush, E Eraser, I Eyedropper.
- Number shortcuts 1-7 assigned to remaining tools.
- Junior Animator defaults to 12 frames at 250 ms each (3 seconds).
- Cycle length selector 0.5-15 seconds with 1/2/3/5/10 second presets.
- Preview and GIF/APNG exports use the same frame timing.
- Play-once checkbox for exported GIF/APNG; infinite looping remains default.
- Duration and play-once settings stored in project snapshots.
- Tests updated to match new keyboard mapping.

Validation:
- 136 pytest tests passed, 45 subtests passed in this environment.
- Python syntax compiled.
- Native Windows Qt GUI/EXE was NOT run in this environment (PySide6 unavailable).

To apply:
1. Back up your existing repo or make a git commit.
2. Extract this ZIP into the Slime-house-Studios repository root, replacing only these listed files.
3. Review changes in GitHub Desktop, commit and push normally (no force push).
4. Let GitHub Actions build the Windows portable EXE and test the UI and exports.
