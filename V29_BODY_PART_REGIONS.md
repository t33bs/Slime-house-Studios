# v29: Optional body-part regions

Desktop Pet Builder now provides an optional body-part panel for marking head, eyes, mouth, left/right paw, tail, and wings with pixel-coordinate rectangles. Regions are validated against the uploaded PNG/canvas and against each other. They are stored in project JSON. The automatic animation generator moves marked parts independently for relevant actions and falls back to previous whole-body starter motion otherwise. Generation remains opt-in, suggestions remain optional, and manual export is unchanged.

**Limitations:** This is a first rigging pass, not a polished visual brush/selection tool. Regions are entered using X/Y/Width/Height, not painted directly on canvas. Rectangular selections can capture unwanted background pixels, and moving a region may expose gaps; use transparent art and non-overlapping regions. It does not invent new artwork, redraw hidden pixels, rotate articulated joints, or import generated frames into the Intermediate timeline. Windows UI testing remains outstanding.

**Tests:** 90 passed, 45 subtests passed in Linux test environment.
