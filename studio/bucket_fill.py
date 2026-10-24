"""Bounded non-recursive flood fill on a single editable RGBA layer."""
from collections import deque
from PIL import Image

def flood_fill(image, point, color):
    """Return filled copy or None for no change; never mutate original image."""
    if not isinstance(image, Image.Image):
        raise TypeError('Expected PIL image')
    img=image.convert('RGBA')
    x,y=map(int,point)
    w,h=img.size
    if not (0<=x<w and 0<=y<h):return None
    target=img.getpixel((x,y)); replacement=tuple(color)
    if len(replacement)!=4 or target==replacement:return None
    pixels=img.load();q=deque([(x,y)]);pixels[x,y]=replacement
    while q:
        cx,cy=q.popleft()
        for nx,ny in ((cx-1,cy),(cx+1,cy),(cx,cy-1),(cx,cy+1)):
            if 0<=nx<w and 0<=ny<h and pixels[nx,ny]==target:
                pixels[nx,ny]=replacement;q.append((nx,ny))
    return img
