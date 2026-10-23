# Slime House Studios — Python Windows desktop app

A **native Python + PySide6 desktop app**, not Electron, Java, or a browser wrapper. Includes dark mode, three soft-colored transparent pixel slimes, adjustable canvas dimensions, PNG layer imports, dragging, layer ordering, project JSON, and a first working animation/export engine.

## Get the Windows `.exe` with GitHub (no Python required on your PC)

1. Create a GitHub repository and upload **the contents** of this ZIP (including `.github/workflows/build-windows.yml`). GitHub's web uploader may hide dotfolders on some systems; verify the workflow file exists in your repository.
2. Open **Actions** → **Build Windows EXE** → **Run workflow**.
3. Wait for the build to finish. Download **SlimeHouseStudios-Windows** from the run's **Artifacts** section.
4. Extract the downloaded artifact and run `SlimeHouseStudios.exe`.

Windows SmartScreen may warn about an unsigned new executable. Do not disable security software; verify the file came from your own GitHub build.

## Developer launch (only if developing locally)

```bash
python -m pip install -r requirements.txt
python main.py
```

## App branding

The Windows executable, application title, and taskbar/window icon use **Slime House Studios**. The launcher icon comes from `assets/slime_house_studios.ico` (derived from the transparent `assets/slime_mascot.png`).

## Features in this first milestone

- Native dark Qt interface, small transparent happy pixel slimes (not included in exports)
- Canvas presets 32, 64, 128, 256, 512, and custom dimensions up to 2048 per side
- Import PNG or WebP as RGBA layers, select, drag, change X/Y, reorder, delete
- Export transparent PNG, save/reopen editable JSON project (PNG images embedded)
- Float, Bounce, Twitch, Pulse and Blink preview effects
- Pillow APNG export; validates frame count, size, and nonidentical decoded frames
- GitHub Actions build for standalone Windows executable

## Not yet implemented

This is **milestone 1**, not the full editor. Resizing/rotating layers, pixel paintbrushes, animation-region masks, frame-by-frame timeline, advanced effects (fire, laser, glow), NFT trait/rarity generation, and batch export are still to be built. No Windows executable has been compiled or run in this environment; the GitHub workflow will compile it on Windows.
