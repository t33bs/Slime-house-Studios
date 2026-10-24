# v41 — Phase 3 visual body-part selection

- Adds **Pet Region Select** tool to the canvas.
- In Desktop Pet Builder → Advanced / Export → Optional body-part regions, choose the part and click **Draw selected body part on canvas**.
- Drag a rectangle directly over the creature on the main canvas. The pixel bounds save into the existing body-region model, visible in the list and reusable by the rigged animation generator.
- Saved regions are drawn as labeled outlines while the selector is active. Existing numeric region editing and all recipe workflows remain available.
- To avoid coordinate mismatch, this tool requires the creature on the main canvas (not an independently selected template path).
- Windows GUI mouse interaction is still pending verification.
