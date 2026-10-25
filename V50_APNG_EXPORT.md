# v50 — APNG export discoverability and safety

- Export → Choose Your Formats writes `<name>_animated.apng`, `<name>_animated.gif`, and `<name>_still.png` when all three are selected.
- Previously the APNG was named `<name>_animated.png`, which could be mistaken for a still PNG or missed by extension-based searches.
- The single APNG export dialog now defaults to `animation.apng`.
- The multi-format exporter removes an invalid partially written file on validation failure and reports the error.
- An APNG still requires at least two visually different frames; without a visible animation, the exporter reports a validation error rather than pretending it created an animation.
- The Windows GUI and actual user project have not yet been tested.
