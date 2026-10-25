"""Consistent pixel targeting for the zoomed sprite canvas."""
import math


def screen_to_pixel(screen_x, screen_y, origin_x, origin_y, zoom):
    """Map the pointer to the pixel containing it, never round to a neighbor.

    Values outside the canvas remain outside, so the caller can reject them.
    """
    if not math.isfinite(zoom) or zoom <= 0:
        raise ValueError('Canvas zoom must be positive and finite')
    return (math.floor((screen_x - origin_x) / zoom),
            math.floor((screen_y - origin_y) / zoom))
