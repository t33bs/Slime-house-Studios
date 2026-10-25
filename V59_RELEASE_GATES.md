# v59 — Windows release quality gates

- Preserve v58 functionality; no changes to the editor or export engine.
- Windows CI now runs both unittest discovery and the complete pytest suite (including real-byte PNG/GIF/APNG export regression tests).
- Keep the existing Qt GUI smoke test before packaging.
- Check that both the portable EXE and Inno Setup installer exist and are nontrivial in size before uploading.
- Log SHA-256 hashes for both deliverables in the Actions output.

**Important:** These checks have not yet run on GitHub Actions. The executable and installer are not signed, and the build gate does not substitute for a hands-on Windows test.

## Outstanding gates

1. Run workflow on `t33bs/Slime-house-Studios` and verify all jobs pass.
2. Download and run portable EXE and installer on Windows; check Windows Defender/SmartScreen warnings and application launch.
3. Confirm animation playback and file-save dialog behavior in packaged build.
4. Review whether legacy Desktop Pet Builder code can be safely deleted (it is already retired in the UI).
