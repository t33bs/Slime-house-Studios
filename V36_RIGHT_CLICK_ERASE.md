# v36 — Right-click universal eraser

Right-click and drag temporarily erases in the active drawing context: base pixel layer, Intermediate frame-paint track, or Junior animation mask. It does not switch the selected tool or change the paint color. Existing E shortcut remains available. Right-click on a non-drawing tool uses the most recently selected drawing context; right-click on empty base layers or absent mask regions is a no-op. Right-click does not add layers.

This is a first implementation and still needs hands-on Windows mouse/Qt GUI verification. Automated tests cover source wiring and regression; they do not simulate physical mouse input.
