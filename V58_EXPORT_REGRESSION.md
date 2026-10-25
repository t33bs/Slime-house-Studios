# v58 — Multi-format export reliability

- In Export → Choose Your Formats, frame generation failures now show a clear warning and stop before touching existing exports.
- Multi-format APNG and GIF files now receive the same decoded-motion validation as the standalone exporters, instead of checking frame count alone.
- Still PNG receives image decode/dimension validation before atomic replacement.
- Added real-file regression tests exporting PNG, GIF, and APNG together, and verifying failed writers/validators preserve previously saved files.
- Unit tests: 117 passed locally; Windows EXE and GitHub Actions not run here.
- Desktop Pet Builder retirement remains a separate pending cleanup, to avoid destabilizing the already-fixed Windows maximize issue.
