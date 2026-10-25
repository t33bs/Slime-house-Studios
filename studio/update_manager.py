"""Signed, opt-in Windows installer update checks. Never executes downloads."""
import base64
import hashlib
import json
import re
import urllib.request
from pathlib import Path

MAX_MANIFEST_BYTES = 65536
MAX_INSTALLER_BYTES = 600 * 1024 * 1024


def parse_version(version):
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError("Version must use major.minor.patch")
    return tuple(int(n) for n in match.groups())


def verify_manifest(envelope, public_key_b64):
    """Ed25519 signs canonical JSON payload; key must ship in the app, not the feed."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    if not public_key_b64:
        raise ValueError("No trusted update signing key configured")
    if not isinstance(envelope, dict) or set(envelope) != {'payload', 'signature'}:
        raise ValueError("Invalid signed update envelope")
    payload = envelope['payload']
    if not isinstance(payload, dict):
        raise ValueError("Invalid update payload")
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    key = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64, validate=True))
    key.verify(base64.b64decode(envelope['signature'], validate=True), canonical)
    version = payload.get('version')
    parse_version(version)
    url = payload.get('installer_url', '')
    if not isinstance(url, str) or not url.startswith('https://github.com/') or '/releases/download/' not in url:
        raise ValueError('Installer must be hosted on a GitHub release')
    sha = payload.get('sha256')
    if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', sha):
        raise ValueError('Missing or invalid installer SHA-256')
    size = payload.get('size')
    if type(size) is not int or not 0 < size <= MAX_INSTALLER_BYTES:
        raise ValueError('Invalid installer size')
    return payload


def check_update(current_version, manifest_url, public_key_b64, opener=None):
    if not manifest_url.startswith('https://'):
        raise ValueError('Update feed requires HTTPS')
    opener = opener or urllib.request.urlopen
    with opener(urllib.request.Request(manifest_url, headers={'User-Agent':'SlimeHouseStudios-Updater'}), timeout=8) as response:
        raw = response.read(MAX_MANIFEST_BYTES + 1)
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError('Update manifest too large')
    payload = verify_manifest(json.loads(raw), public_key_b64)
    return payload if parse_version(payload['version']) > parse_version(current_version) else None


def download_verified_installer(payload, destination, opener=None):
    """Download to a temporary file; verify size/hash before atomic rename. No execution."""
    opener = opener or urllib.request.urlopen
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_name(destination.name + '.partial')
    digest = hashlib.sha256()
    total = 0
    try:
        with opener(urllib.request.Request(payload['installer_url']), timeout=30) as response, temp.open('wb') as out:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > payload['size'] or total > MAX_INSTALLER_BYTES:
                    raise ValueError('Installer larger than expected')
                digest.update(chunk)
                out.write(chunk)
        if total != payload['size'] or digest.hexdigest().lower() != payload['sha256'].lower():
            raise ValueError('Installer integrity check failed')
        temp.replace(destination)
        return destination
    finally:
        temp.unlink(missing_ok=True)
