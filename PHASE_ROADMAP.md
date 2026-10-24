# Slime House Studios — v20 onward

Keep the native Python/PySide6 Windows desktop app. All new features are additive to v20.

## Phase 1 — Animation Workshop foundation (IMPLEMENTED, WINDOWS GUI QA PENDING)
- [x] Merge Senior/Advanced into Intermediate Studio without changing saved dock identity
- [x] Guided Mode on by default, with persistent on/off preference
- [x] Separate closable/detachable Desktop Pet Builder dock
- [x] Named per-pose attachment anchors (Idle/Walk/Run/Jump/Sleep/Crawl/Sit/Attack/Custom)
- [x] Store anchors in editable project files, undo/redo snapshots and recovery
- [x] Visual anchor handles and snapping on canvas
- [x] Multiple editable frame-paint tracks with merged playback (keyframe transforms remain Phase 2)
- [x] Layer mesh-transform reset, pose-anchor eraser, and frame reset tools
- [ ] Full Windows GUI validation

## Phase 2 — Frame Workshop depth (FEATURES IMPLEMENTED; WINDOWS QA PENDING)
- [x] Whole-sprite movement keyframes with interpolated pixel-snapped offsets
- [x] Reusable named frame-paint clips and range pasting
- [x] Persist clips and keyframes in project snapshots and undo/redo
- [x] Per-layer independent pixel-offset tracks and visual keyframe markers
- [x] Shared-anchor rig compatibility and interpolated anchor transition preview (not artwork morphing)
- [ ] Live Windows GUI tests and export verification
- Multiple tracks, layer/frame timeline, onion skins, playback, reusable clips
- Movement anchors and rig compatibility, pose transitions
- Non-destructive per-frame transforms, reset and eraser tools

## Phase 3 — Desktop Pet Builder (IN PROGRESS — v40)
- [x] Existing creature templates, body-part regions, anchors and starter-motion generator
- [x] 31 everyday-life animation recipes and additional battle recipes
- [x] v39 simplified Step-by-Step / Advanced layout
- [x] v40 context-sensitive pose drawing, preview, and export navigation
- [x] v40 optional per-recipe step checkmarks (current session only)
- [ ] Illustrated pose references and visual region-selection tools
- [ ] Persistent creature animation-state library and editable rigging workflow
- [ ] Integrated creature preview, export validation and Windows GUI QA
- [ ] Battle-animation workflow refinement without adding gameplay to Studio

## Phase 4 — Variation and evolution workflow (PLANNED)
- Recolor/material/element variations and creature family organization
- Batch generation and validation without breaking non-NFT workflows

## Phase 5 — Integration and release hardening (PLANNED)
- Export reliability across APNG/GIF/PNG/sprite sheets
- Windows end-to-end GUI tests, installer and portable EXE, packaging and documentation
- NFT metadata/blockchain integration later, separate from the base art tools

**Do not mark phases 2–5 complete until implemented and tested.**
