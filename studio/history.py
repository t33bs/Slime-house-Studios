"""Bounded, independent undo snapshots and crash-safe project persistence."""
import base64
import io
import json
import os
import tempfile
from pathlib import Path
from PIL import Image
from .core import Layer, Region


def capture(size, layers, regions, traits, edits, frames, duration, loops, fmt):
    encoded = []
    for layer in layers:
        buffer = io.BytesIO()
        layer.image.save(buffer, format='PNG')
        encoded.append(dict(name=layer.name, x=layer.x, y=layer.y, scale=layer.scale,
                            angle=layer.angle, visible=layer.visible,
                            png=base64.b64encode(buffer.getvalue()).decode('ascii')))
    return dict(version=10, size=list(size), layers=encoded,
                regions=[vars(region).copy() for region in regions],
                traits=json.loads(json.dumps(traits)),
                frame_edits=json.loads(json.dumps(edits)), frame_count=frames,
                frame_duration=duration, animation_loops=loops, export_format=fmt)


def decode(obj):
    size = obj['size']
    if len(size) != 2 or any(type(n) is not int or not 1 <= n <= 2048 for n in size):
        raise ValueError('Invalid canvas dimensions')
    layers = []
    for item in obj['layers']:
        with Image.open(io.BytesIO(base64.b64decode(item['png'], validate=True))) as img:
            image = img.convert('RGBA').copy()
        layers.append(Layer(item['name'], image, item.get('x', 0), item.get('y', 0),
                            item.get('visible', True), item.get('scale', 1), item.get('angle', 0)))
    regions = [Region(**r) for r in obj.get('regions', [])]
    return tuple(size), layers, regions


def atomic_write(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.slime-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(obj, handle, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


class UndoHistory:
    def __init__(self, limit=30):
        self.limit = limit
        self.undo_stack = []
        self.redo_stack = []

    def record(self, state):
        self.undo_stack.append(json.loads(json.dumps(state)))
        self.undo_stack = self.undo_stack[-self.limit:]
        self.redo_stack.clear()

    def undo(self, current):
        if not self.undo_stack:
            return None
        self.redo_stack.append(json.loads(json.dumps(current)))
        return self.undo_stack.pop()

    def redo(self, current):
        if not self.redo_stack:
            return None
        self.undo_stack.append(json.loads(json.dumps(current)))
        return self.redo_stack.pop()
