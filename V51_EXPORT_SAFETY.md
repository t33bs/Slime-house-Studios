# v51 — Atomic multi-format export safety

The Export → Choose Your Formats workflow now writes each selected output to a temporary sibling file, validates it, and atomically replaces the destination only after success. A failed APNG/GIF/PNG export cannot delete or truncate an older exported file even if the user approved overwriting existing files. Partial temporary files are cleaned up. Existing naming conventions remain unchanged.

Tests cover successful replacement, encoder failure, validation failure, and cleanup. Windows GUI integration and actual user artwork still require testing. Single-format export paths remain outside this patch.
