"""Image compositing and verified APNG export, independent of the GUI."""
from dataclasses import dataclass
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance
import math

@dataclass
class Layer:
    name: str
    image: Image.Image
    x: int = 0
    y: int = 0
    visible: bool = True


def composite(layers, size):
    out = Image.new('RGBA', size, (0, 0, 0, 0))
    for layer in layers:
        if layer.visible:
            out.alpha_composite(layer.image.convert('RGBA'), (layer.x, layer.y))
    return out


def frames_for(layers, size, effect='Float', count=8, strength=2):
    base = composite(layers, size)
    frames = []
    for i in range(count):
        phase = 2 * math.pi * i / count
        f = Image.new('RGBA', size, (0, 0, 0, 0))
        if effect == 'Float':
            offset = round(math.sin(phase) * strength)
            f.alpha_composite(base, (0, offset))
        elif effect == 'Bounce':
            offset = -round(abs(math.sin(phase)) * strength)
            f.alpha_composite(base, (0, offset))
        elif effect == 'Twitch':
            offset = round(math.sin(phase) * strength)
            f.alpha_composite(base, (offset, 0))
        elif effect == 'Pulse':
            # Keep native pixel size: discrete alpha modulation, no blurry resampling.
            alpha = base.getchannel('A').point(lambda v: round(v * (0.75 + 0.25 * (1 + math.sin(phase)) / 2)))
            f = base.copy()
            f.putalpha(alpha)
        elif effect == 'Blink':
            f = base.copy()
            if i % count in (count // 2,):
                # A short one-frame horizontal squeeze across the middle.
                bbox = base.getbbox()
                if bbox:
                    left, top, right, bottom = bbox
                    mid = (top + bottom) // 2
                    band = Image.new('RGBA', (right-left, max(1, bottom-top)), (0,0,0,0))
                    # No guessing about eye position: indicate blink as a full sprite squash.
                    compressed = base.crop(bbox).resize((right-left, max(1, (bottom-top)*9//10)), Image.Resampling.NEAREST)
                    f = Image.new('RGBA', size, (0,0,0,0))
                    f.alpha_composite(compressed, (left, top+(bottom-top-compressed.height)//2))
        else:
            raise ValueError(f'Unknown effect: {effect}')
        frames.append(f)
    return frames


def export_apng(frames, filename, duration=100):
    if len(frames) < 2:
        raise ValueError('Animation needs at least two frames.')
    if any(f.size != frames[0].size for f in frames):
        raise ValueError('Animation frames have mismatched dimensions.')
    if not any(f.tobytes() != frames[0].tobytes() for f in frames[1:]):
        raise ValueError('All animation frames are identical. Increase movement strength or choose a different effect.')
    filename = Path(filename)
    frames[0].save(filename, format='PNG', save_all=True, append_images=frames[1:], duration=[duration]*len(frames), loop=0, disposal=0, blend=0, default_image=False)
    with Image.open(filename) as check:
        if not check.is_animated or check.n_frames != len(frames) or check.size != frames[0].size:
            filename.unlink(missing_ok=True)
            raise RuntimeError('APNG validation failed: missing frames or wrong dimensions.')
        actual = []
        for i in range(check.n_frames):
            check.seek(i)
            actual.append(check.convert('RGBA').tobytes())
        if len(set(actual)) < 2:
            filename.unlink(missing_ok=True)
            raise RuntimeError('APNG validation failed: decoded frames are identical.')
    return filename
