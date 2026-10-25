# v52 — Single-format export safety

Extends v51 atomic replacement to File > Save PNG, standalone still PNG, GIF, APNG, and sprite-sheet exports. Each selected output is written to a temporary sibling file, validated with Pillow, and atomically moved to its destination only on success. Existing output survives encoder/validation failures. Filename extensions are normalized. Added regression tests for export wiring and preserving an existing still PNG after a failed write.

Limitations: Windows GUI testing and actual Windows EXE builds have not been performed. This does not address the separate legacy Desktop Pet export workflows.
