# v33 — Universal drawing hotkeys

- **B** selects Pencil, Frame Pencil, or Mask Brush depending on the current drawing tool.
- **E** selects Eraser, Frame Eraser, or Mask Eraser in the same context.
- **I** still activates Eyedropper.
- Switching B/E back and forth preserves the relevant drawing context.
- Existing tools remain available in the tool dropdown; no destructive tool merging.

For a fresh project or when a non-drawing tool is selected, B/E default to the normal artwork pencil/eraser. To draw on timeline frames, select Frame Pencil once; B/E then switch between frame drawing and frame erasing. Similarly, select Mask Brush once to switch between highlight/erase using B/E.

**Validation:** automated tests passed in Linux. Windows GUI shortcut focus handling still needs hands-on verification.
