# v0.6 Signed Update Checker

Help → Check for Updates checks a signed HTTPS manifest in a background thread. An Ed25519 signature is verified before offering an update. The user explicitly approves opening the GitHub release; no silent installation. Configure UPDATE_MANIFEST_URL and UPDATE_PUBLIC_KEY_B64 in studio/release_config.py after provisioning an offline signing key and publishing the official feed. Never commit private signing keys. Windows GUI integration has not yet been validated.
