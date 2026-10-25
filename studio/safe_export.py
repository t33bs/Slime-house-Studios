"""Atomic replacement for exported image files.

Write and validate a sibling temporary file before replacing the destination.
A failed export never removes or truncates a previously exported file.
"""
from pathlib import Path
import os
import tempfile


def safe_export(destination, writer, validator=None):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f'.{destination.stem}.', suffix=destination.suffix, dir=destination.parent)
    os.close(fd)
    temporary = Path(temporary)
    try:
        writer(temporary)
        if validator is not None:
            validator(temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination
