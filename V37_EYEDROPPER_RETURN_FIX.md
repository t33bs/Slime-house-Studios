# v37 Eyedropper restoration hotfix

After sampling an opaque pixel, the tool returns to the matching drawing brush instead of an eraser: Eraser -> Pencil, Frame Eraser -> Frame Pencil, Mask Eraser -> Mask Brush. The sampled drawing color is retained. Both the I shortcut and direct tool dropdown selection are supported. Right-click temporary erasing is unchanged.

97 automated tests and 45 subtests passed. Windows GUI testing is still required.
