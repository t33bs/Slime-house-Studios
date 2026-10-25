# Slime House Studios v0.6 — Windows release candidate

Includes two distribution options:

- Portable `SlimeHouseStudios.exe` — runs without installation.
- `SlimeHouseStudios-v0.6-Setup.exe` — Inno Setup per-user installer with optional desktop shortcut, Start Menu entry, and uninstall support.

GitHub Actions builds both on Windows, runs Python regression and GUI smoke tests, checks output files, and performs silent install/uninstall validation. Publishing a GitHub Release with a tag starting `v0.6` triggers asset upload.

**Important:** This source bundle is not a compiled Windows installer. Windows workflow, installer, launch, and SmartScreen behavior still need verification in GitHub Actions and on a Windows machine. Code signing is not included.
