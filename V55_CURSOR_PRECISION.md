# v55 — Canvas pixel-targeting precision

- Corrected canvas pointer mapping from `round()` to `floor()` so clicking within the left or top half of a zoomed pixel no longer selects the adjacent pixel.
- Applied centrally in `Canvas.coord`, covering Pencil, Eraser, Paint Bucket, animation highlighter, and other tools using the shared canvas coordinate conversion.
- Added pure-Python coordinate regression tests for zoom, canvas offsets, pixel boundaries, and outside-canvas clicks.
- Preserves v54 highlight color, v53 laser emitters, and previous source changes.
- Windows PySide6 UI verification is still required; no Windows EXE built or GitHub push performed.
