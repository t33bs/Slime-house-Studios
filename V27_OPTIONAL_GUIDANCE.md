# v27: Optional assistance and manual sprite export

- Independent persistent Show animation suggestions/recipes switch. When off, hides the recipe panel and omits recipe files from generated packages.
- Independent persistent Enable automatic preset generation switch (off by default). Preset generation is explicitly opt-in.
- Existing global Guided Mode remains independently switchable and persistent.
- Manual sprite-sheet export button works with auto-generation off, no preset or body-type selection, and exports a single-frame `Custom` PNG atlas and JSON with optional individual PNG.
- Does not restrict the main editor, Intermediate Studio, or other export routes.

## Limits
Manual export currently starts with one frame; it does not yet provide a custom multi-frame sheet layout editor. Windows GUI validation remains necessary.
