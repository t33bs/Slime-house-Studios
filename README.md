# Slime House Studios v0.6 — Windows (Python / PySide6)

Incremental upgrade of v0.5, retaining all existing tools. Adds **Mask Brush**, **Mask Eraser**, per-region freehand pixel masks, and **Gush** (16th effect). Select or draw an animation region, select Mask Brush and paint over pixels, then choose an effect. Gush settings: direction (including radial), distance, strength/spread, particle count, speed and RGBA color. Masks and settings save with project JSON. Regions with empty masks still use rectangular selections for backward compatibility.

## Build
Upload all files and folders, including `.github/workflows/build-windows.yml`, to the existing GitHub repo. In Actions run **Build Windows EXE**, then download **SlimeHouseStudios-Windows-v06**. No Python required on the Windows computer running the built EXE.

## Development / tests
`pip install -r requirements.txt` then `python -m unittest discover -s tests -v`; launch with `python main.py`.

## Limitations
Gush uses deterministic pixel particles; not fluid simulation. Freehand masks are stored as canvas coordinates. Rectangle effects with masks may still have compositing limitations when overlapping other sprite layers. Windows UI and GitHub EXE must be tested on Windows. NFT batch artwork generation and timeline remain future work.

## v0.7 — Frame timeline

This version extends v0.6 (no features removed). The Animation tab now has a frame
slider, previous/next buttons, **Frame Pencil**, **Frame Eraser**, duplicate-previous-frame
edits, clear-frame-edits, and optional onion skin of the preceding frame. These are
non-destructive per-frame RGBA overrides composited after procedural region effects.
Frame edits, frame count, and duration persist in the project JSON. APNG preview/export
uses the same composed frames. Existing v0.6 project files remain loadable.

**Current limitations:** Timeline painting is per-pixel color/erase overrides, not a
full Photoshop-like editable layer stack per frame. Duplicate copies painted overrides,
not the rendered procedural pixels. GIF export and sophisticated tweening are not
included. The Qt GUI and packaged Windows EXE still require Windows validation.

## v0.8 — Simultaneous animation effects and independent timing

Builds on v0.7 without removing its features. Every animation region now has its own **start frame**, **active-frame window**, **cycle length**, **phase offset**, and **repeat** setting. Multiple regions are evaluated in list order and can animate simultaneously, including different effects on different painted masks. Timeline frame edits are applied after procedural effects, as before. Timing settings persist in project JSON and older projects load using defaults.

To use: add two or more regions, select each in the Animation tab, assign an effect and timing settings, then preview or export. A zero active-frame count means the whole remaining timeline; a zero cycle length uses the full timeline length. A non-repeating region stops after its first cycle. Overlapping effects are sequentially composited and may obscure earlier effects; this is not a physics-based compositing engine.

The GUI and Windows EXE still require real Windows validation. This is a Python source build; do not replace your existing GitHub project until ready for the consolidated release.

## v0.9 — NFT worksheet lookup and editor

Adds a simple **NFT Worksheet** tab, separate from the existing optional Trait Generator. Import `.xlsx` or `.csv`, choose the column containing NFT numbers, enter a number (e.g. `0059`), and click **Load NFT**. All worksheet columns for that row appear in an editable two-column table. Click **Save edits to session**, then **Export updated worksheet** to save a new `.xlsx` or `.csv`. Original source is not overwritten automatically. Numeric IDs match regardless of leading zeros (`0059` matches `59`). Duplicate IDs are reported instead of silently choosing the wrong row.

There is **no** asset checklist, asset matching, compatibility rules, visual preview in the worksheet manager, or collection progress tracking. The separate pre-existing Trait Generator remains available for backward compatibility. Worksheet data is managed separately from sprite project JSON; export edits before closing. Excel import reads the active worksheet tab and values, not formulas. Export writes a new single-sheet workbook (other original sheets and formatting are not preserved).

No GitHub update is required until the user is ready for the consolidated release. Windows GUI still requires actual Windows testing.


## Dockable Animation Studio update
The **Open Animation Studio** button in the left toolbar opens the full existing animation controls in a resizable Qt dock. Drag its title bar to reposition it or float it as a separate window; close it to hide without discarding project state. Selecting an animation-specific canvas tool opens it automatically. The NFT Worksheet, Trait Generator and Project tabs stay in the right sidebar.


## Animator Duration & Export Settings (new)
In the dockable Animation Studio, expand **Duration & Export Settings** to choose speed presets, frame count, milliseconds per frame, looping, and output format. The summary shows effective FPS and total duration. Export choices: transparent APNG (recommended), GIF (limited palette), horizontal sprite sheet PNG, or still PNG. Loop count 0 means forever for animated formats. Settings are stored with the project.


## Beginner-friendly UI improvements
- Advanced laser/gush and independent-timing controls are collapsed by default.
- Clear quick-start guidance inside the Animator and tool-specific hover tips.
- Keyboard shortcuts: Ctrl+O open project, Ctrl+S save project, Ctrl+I import image, Ctrl+E export animation.
- Confirmations before deleting layers/regions or clearing highlights/frame edits.
- Existing tools and engine preserved. This update does not yet add a full undo/redo history.

### Phase 1.0 export regression checks (in progress)
- GIF and horizontal sprite-sheet exports now use independently testable engine functions.
- APNG and GIF exports validate total playback duration. Encoders may merge identical adjacent frames; this is normal when timing is preserved.
- Sprite-sheet export retains every timeline frame, including repeated frames.
- Five export regression tests added; 24 automated tests pass in this environment.
- Windows Qt GUI, installer, and end-to-end hands-on testing are **not yet verified**.

### Phase 1.0 quality pass (development snapshot)
- Added shared APNG/GIF export validation for invalid frame duration, loop counts,
  static frames, and inconsistent dimensions, before writing output files.
- Added regression tests for invalid export settings and all 16 effects.
- Windows executable and graphical UI remain unverified; this is not a release build.

## Phase 1.0 release-preparation checkpoint

- Added bounded snapshot undo/redo (`Ctrl+Z`, `Ctrl+Shift+Z`, `Ctrl+Y`) for canvas strokes, masks, frame painting, transforms and several structural operations.
- Added recovery snapshots at 60-second intervals after recorded edits, a restore prompt at startup, and atomic project saves.
- Added tests for snapshot pixel fidelity, undo/redo branching, recovery writes and malformed canvas dimensions.
- **Known gaps:** undo coverage of all settings/trait edits is incomplete; Qt interface not run here (PySide6 unavailable); Windows executable not built or tested here. This is NOT a validated v1.0 release.

### Animator effect colors
Six one-click color swatches plus a custom RGBA color picker. Colors are saved per animation region, so simultaneous effects can use different colors. Select a region before choosing a color.

## Dual animator workspaces (Phase 1.0 development)

The **Junior Animator** is a separate closable, dockable, detachable window for the 16 quick animation effects, per-region color palettes, masks, preview and quick export. The **Advanced Animator** is a separate closable, dockable, detachable window for frame-by-frame timeline editing, onion skin, duration/loop controls and output format selection. Both use the same project data. Use the two buttons in the left toolbar to open or close either workspace. Choosing a mask tool opens Junior; choosing a frame tool opens Advanced. The main editor remains available when either is closed.

Note: Automated engine tests pass, but Windows GUI and packaged EXE are not yet verified.


## Phase 1.0 visual polish
Refined Junior Animator blinking, gentler breathing/twitch, white-core laser beams, cohesive directional Gush particles, and larger sparkles. Four regression tests added (41 passing). GUI appearance on Windows is not yet verified.

### Phase 1.0 visual polish checkpoint (v13)
- Glow now renders a crisp colored halo outside the selected opaque pixels and a subtle interior shimmer, animated over the effect cycle.
- Added `tests/test_glow_halo.py` with halo color and timing checks.
- Moving selections can still expose transparent pixels; this remains open and requires background-aware compositing rather than a potentially destructive fill.
- The PySide6 GUI and Windows executable have not been tested in this environment.

## Export fidelity polish (Phase 1.0)
- GIF export now uses a consistent palette across frames, reserves palette index 0 for transparency, and disables dithering for sharp pixel edges.
- GIF rejects frame times not divisible by 10 ms rather than silently changing the requested timing; choose a compatible duration or APNG for exact timing.
- Added export tests for GIF transparent backgrounds, primary colors, APNG RGBA fidelity, and unsupported GIF timing.
- Note: GIF supports at most 255 opaque colors plus transparency and cannot retain partial alpha; use APNG for lossless RGBA artwork.
