# Slime House Studios v45 source patch

- Paint Bucket fills contiguous exact RGBA pixels in the selected unrotated/unscaled layer. Supports undo via existing checkpoint mechanism.
- Main brush palette moved above Guided Mode controls.
- Retired Desktop Pet Builder button hidden and dock removed from live main window layout; underlying compatibility helpers remain in code pending full removal.
- Deferred canvas repaint after native window-state changes; existing crash log remains at ~/.slime_house_studios/crash.log.
- Installer and Windows GitHub Actions build scripts retained; this is source only, not a Windows-validated installer.
- WARNING: This patch is not verified to resolve every maximize crash; a Windows crash log and GUI run are required.
