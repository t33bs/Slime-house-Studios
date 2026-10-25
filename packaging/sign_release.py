"""Sign a GitHub-hosted Windows installer manifest with an offline Ed25519 key.
Usage: python packaging/sign_release.py VERSION INSTALLER GITHUB_RELEASE_URL PRIVATE_KEY_FILE OUTPUT
PRIVATE_KEY_FILE contains 32 raw Ed25519 bytes (never commit this file).
"""
import base64
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def build_manifest(version, installer, url, private_key):
    from studio.update_manager import parse_version, MAX_INSTALLER_BYTES
    parse_version(version)
    parsed = urlparse(url)
    if parsed.scheme != 'https' or parsed.hostname != 'github.com' or '/releases/download/' not in parsed.path:
        raise ValueError('Installer URL must be a GitHub release download')
    path = Path(installer)
    size = path.stat().st_size
    if not 0 < size <= MAX_INSTALLER_BYTES:
        raise ValueError('Installer size out of range')
    payload = {'version': version, 'installer_url': url, 'size': size,
               'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    key = Ed25519PrivateKey.from_private_bytes(private_key)
    signature = base64.b64encode(key.sign(canonical)).decode('ascii')
    return {'payload': payload, 'signature': signature}


if __name__ == '__main__':
    if len(sys.argv) != 6:
        raise SystemExit(__doc__)
    _, version, installer, url, keyfile, output = sys.argv
    # The key is provided locally by the release owner, never through CI source.
    signed = build_manifest(version, installer, url, Path(keyfile).read_bytes())
    Path(output).write_text(json.dumps(signed, indent=2) + '\n', encoding='utf-8')
    print('Signed release manifest written to', output)
