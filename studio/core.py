"""Pure Pillow engine for Slime House Studios. No Qt dependency."""
from dataclasses import dataclass, field
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import math, random, json, hashlib

@dataclass
class Layer:
    name: str
    image: Image.Image
    x: int = 0
    y: int = 0
    visible: bool = True
    scale: float = 1.0
    angle: float = 0.0

@dataclass
class Region:
    name: str
    rect: tuple
    effect: str = 'Float'
    strength: int = 2
    color: tuple = (160, 255, 190, 255)
    enabled: bool = True
    direction: str = "Right"
    beam_length: int = 18
    mask: list = field(default_factory=list)  # freehand pixel coordinates, canvas-space
    particle_count: int = 12
    speed: int = 2
    start_frame: int = 0
    active_frames: int = 0  # 0 means full timeline
    cycle_frames: int = 0   # 0 means timeline length
    phase_offset: int = 0
    repeat: bool = True

EFFECTS = ['Float','Bounce','Twitch','Pulse','Blink','Glow','Flash','Shake','Sparkle','Color Cycle','Squash','Slide','Vertical Breathing','Horizontal Twitch','Laser Eyes','Gush']

def transformed(layer):
    im=layer.image.convert('RGBA')
    s=max(.05,min(16.,layer.scale))
    if s!=1: im=im.resize((max(1,round(im.width*s)),max(1,round(im.height*s))),Image.Resampling.NEAREST)
    if layer.angle%360: im=im.rotate(-layer.angle,Image.Resampling.NEAREST,expand=True)
    return im

def composite(layers,size):
    out=Image.new('RGBA',size)
    for layer in layers:
        if layer.visible: out.alpha_composite(transformed(layer),(layer.x,layer.y))
    return out

def paint_pixel(layer,x,y,color,radius=1,erase=False):
    if not (0<=x<layer.image.width and 0<=y<layer.image.height):return
    d=ImageDraw.Draw(layer.image)
    box=(x-radius+1,y-radius+1,x+radius-1,y+radius-1)
    if erase:
        # clear pixels rather than painting opaque background
        for yy in range(max(0,box[1]),min(layer.image.height,box[3]+1)):
            for xx in range(max(0,box[0]),min(layer.image.width,box[2]+1)):
                layer.image.putpixel((xx,yy),(0,0,0,0))
    else:d.rectangle(box,fill=color)

def apply_region(frame,region,i,count):
    if not region.enabled:return frame
    start=max(0,int(region.start_frame))
    if i<start:return frame
    elapsed=i-start
    active=max(0,int(region.active_frames))
    if active and elapsed>=active:return frame
    cycle=max(2,int(region.cycle_frames) if region.cycle_frames else count)
    if not region.repeat and elapsed>=cycle:return frame
    local_i=(elapsed+int(region.phase_offset))%cycle
    i,count=local_i,cycle
    x,y,w,h=map(int,region.rect)
    x=max(0,x);y=max(0,y);w=min(w,frame.width-x);h=min(h,frame.height-y)
    if w<=0 or h<=0:return frame
    phase=2*math.pi*i/count
    crop=frame.crop((x,y,x+w,y+h)); effect=region.effect; strength=region.strength
    # Masks select exact pixels, unlike the legacy rectangular selection.
    # A painted mask can be used as the origin for all region effects.
    mask_points=[(int(px),int(py)) for px,py in region.mask if 0<=int(px)<frame.width and 0<=int(py)<frame.height]
    if mask_points:
        alpha=Image.new('L',frame.size,0)
        for px,py in mask_points:alpha.putpixel((px,py),255)
        mask_crop=alpha.crop((x,y,x+w,y+h))
        selected_alpha=Image.new('L',crop.size,0)
        from PIL import ImageChops
        selected_alpha=ImageChops.multiply(crop.getchannel('A'),mask_crop)
        crop.putalpha(selected_alpha)
    else:mask_crop=None
    if effect in ('Float','Bounce','Twitch','Shake','Slide','Vertical Breathing','Horizontal Twitch'):
        dx=round(math.sin(phase)*strength) if effect in ('Twitch','Shake','Slide') else 0
        dy=round(math.sin(phase)*strength) if effect=='Float' else (-round(abs(math.sin(phase))*strength) if effect=='Bounce' else 0)
        if effect=='Vertical Breathing':dy=round(math.sin(phase)*min(2,max(1,strength)))
        if effect=='Horizontal Twitch':dx=round(math.sin(phase)*min(2,max(1,strength)))
        if effect=='Slide':dy=round(math.cos(phase)*strength)
        if mask_crop is None:ImageDraw.Draw(frame).rectangle((x,y,x+w-1,y+h-1),fill=(0,0,0,0))
        else:frame.paste((0,0,0,0),(x,y,x+w,y+h),mask_crop)
        frame.alpha_composite(crop,(x+dx,y+dy))
    elif effect=='Glow':
        # Pixel-crisp halo around selected opaque pixels, not a flat tint.
        # MaxFilter expands alpha without interpolation or blurred edges.
        source_alpha=crop.getchannel('A')
        glow_level=(1+math.sin(phase))/2
        radius=1 if strength<=2 else 2 if strength<=5 else 3
        expanded=source_alpha.filter(ImageFilter.MaxFilter(radius*2+1))
        halo=Image.new('RGBA',crop.size,tuple(region.color))
        halo_alpha=expanded.point(lambda v:round(v*glow_level*0.7*region.color[3]/255))
        # Only draw outside the original silhouette, so the original pixels
        # stay crisp and recognizable.
        from PIL import ImageChops
        halo_alpha=ImageChops.subtract(halo_alpha,source_alpha)
        halo.putalpha(halo_alpha)
        frame.alpha_composite(halo,(x,y))
        # Add a subtle interior shimmer without washing out the artwork.
        tint=Image.new('RGBA',crop.size,tuple(region.color))
        tint.putalpha(source_alpha.point(lambda v:round(v*glow_level*.18*region.color[3]/255)))
        frame.alpha_composite(tint,(x,y))
    elif effect in ('Pulse','Flash'):
        factor=(.65+.35*(1+math.sin(phase))/2) if effect=='Pulse' else (.35+.65*(1+math.sin(phase))/2)
        if effect=='Flash':factor=1 if i%2 else .2
        overlay=crop.copy()
        if effect=='Pulse':overlay.putalpha(overlay.getchannel('A').point(lambda v:round(v*factor)))
        else:
            tint=Image.new('RGBA',overlay.size,region.color)
            overlay=Image.blend(overlay,tint,factor*.65)
            overlay.putalpha(crop.getchannel('A'))
        frame.paste(overlay,(x,y),mask_crop) if mask_crop is not None else frame.paste(overlay,(x,y))
    elif effect=='Blink':
        # Close only the selected eye pixels, rather than compressing a whole face.
        # With a painted mask the surrounding fur remains untouched.
        if abs(i-count//2)<=max(0,count//12):
            if mask_crop is None:
                ImageDraw.Draw(frame).rectangle((x,y,x+w-1,y+h-1),fill=(0,0,0,0))
            else:
                frame.paste((0,0,0,0),(x,y,x+w,y+h),mask_crop)
            # Retain the original eye color as a thin closed eyelid.
            cy=y+h//2
            for xx in range(w):
                pixels=[crop.getpixel((xx,yy)) for yy in range(h) if crop.getpixel((xx,yy))[3]>0]
                if pixels and 0<=x+xx<frame.width and 0<=cy<frame.height:
                    frame.alpha_composite(Image.new('RGBA',(1,1),pixels[len(pixels)//2]),(x+xx,cy))
    elif effect=='Squash':
        hh=max(1,round(h*(1-.2*(1+math.sin(phase))/2)))
        if mask_crop is None:ImageDraw.Draw(frame).rectangle((x,y,x+w-1,y+h-1),fill=(0,0,0,0))
        else:frame.paste((0,0,0,0),(x,y,x+w,y+h),mask_crop)
        frame.alpha_composite(crop.resize((w,hh),Image.Resampling.NEAREST),(x,y+h-hh))
    elif effect=='Color Cycle':
        tint=Image.new('RGBA',crop.size,region.color)
        blend=Image.blend(crop,tint,(1+math.sin(phase))*.4)
        blend.putalpha(crop.getchannel('A'));frame.paste(blend,(x,y),mask_crop) if mask_crop is not None else frame.paste(blend,(x,y))
    elif effect=='Laser Eyes':
        intensity=max(0.0,math.sin(math.pi*i/max(1,count-1)))
        if intensity>0.1:
            d=ImageDraw.Draw(frame)
            direction=region.direction.lower()
            dx,dy={'right':(1,0),'left':(-1,0),'up':(0,-1),'down':(0,1)}.get(direction,(1,0))
            length=max(1,round(max(1,min(2048,int(region.beam_length)))*intensity))
            ox=x+w//2;oy=y+h//2
            col=tuple(region.color)
            # Colored outer beam plus a bright pixel core for readability.
            for off in (-1,0,1):
                d.line((ox-dy*off,oy+dx*off,ox+dx*length-dy*off,oy+dy*length+dx*off),fill=col,width=1)
            core=(255,255,255,col[3])
            d.line((ox,oy,ox+dx*length,oy+dy*length),fill=core,width=1)
    elif effect=='Gush':
        # Coherent directional stream: particles follow a common arc with
        # modest deterministic spread and taper, instead of random scattered dots.
        if i:
            origins=mask_points if mask_points else [(x+w//2,y+h//2)]
            direction=region.direction.lower()
            vx,vy={'right':(1,0),'left':(-1,0),'up':(0,-1),'down':(0,1),'radial':(0,0)}.get(direction,(1,0))
            travel=max(1,int(region.beam_length))
            n=max(1,min(250,int(region.particle_count)))
            speed=max(1,int(region.speed))
            d=ImageDraw.Draw(frame)
            for j in range(n):
                ox,oy=origins[(j*37)%len(origins)]
                progress=((i*speed+j*count//max(1,n))%count)/max(1,count-1)
                distance=round(travel*progress)
                spread=((j*19)%7-3)*min(4,max(1,strength))/4
                if direction=='radial':
                    theta=2*math.pi*((j*0.61803398875)%1)
                    px=ox+round(math.cos(theta)*distance)
                    py=oy+round(math.sin(theta)*distance)
                else:
                    # Gravity gives sideways spray a recognizable falling arc.
                    gravity=round(3*progress*progress) if vx else 0
                    px=ox+vx*distance-round(vy*spread)
                    py=oy+vy*distance+round(vx*spread)+gravity
                if 0<=px<frame.width and 0<=py<frame.height:
                    radius=2 if strength>=4 and j%4==0 else 1
                    d.rectangle((px,py,min(frame.width-1,px+radius-1),min(frame.height-1,py+radius-1)),fill=tuple(region.color))
    elif effect=='Sparkle':
        d=ImageDraw.Draw(frame)
        for n in range(max(1,strength)):
            xx=x+(n*17+i*7)%w;yy=y+(n*13+i*11)%h
            if (n+i)%3==0:
                d.point((xx,yy),fill=region.color)
                if w>=5 and h>=5:
                    for px,py in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)):
                        if x<=px<x+w and y<=py<y+h:d.point((px,py),fill=region.color)
    else:raise ValueError(f'Unknown effect: {effect}')
    return frame

def frames_for(layers,size,effect='Float',count=8,strength=2,regions=None):
    base=composite(layers,size)
    if regions is None:regions=[Region('Entire canvas',(0,0,*size),effect,strength)]
    frames=[]
    for i in range(count):
        f=base.copy()
        for region in regions:apply_region(f,region,i,count)
        frames.append(f)
    return frames

def validate_animation_export(frames, duration, loop):
    """Reject invalid timeline settings before creating an output file."""
    if len(frames) < 2:
        raise ValueError('At least two animation frames are required')
    if any(f.size != frames[0].size for f in frames):
        raise ValueError('Frame dimensions differ')
    if frames[0].width < 1 or frames[0].height < 1:
        raise ValueError('Frame dimensions must be positive')
    if not isinstance(duration, int) or not 20 <= duration <= 2000:
        raise ValueError('Frame duration must be between 20 and 2000 milliseconds')
    if not isinstance(loop, int) or not 0 <= loop <= 65535:
        raise ValueError('Loop count must be between 0 and 65535 (0 means forever)')
    if len({f.convert('RGBA').tobytes() for f in frames}) < 2:
        raise ValueError('Animation is static. Select a visible region or increase strength.')


def export_apng(frames,filename,duration=100,loop=0):
    validate_animation_export(frames, duration, loop)
    filename=Path(filename)
    frames[0].save(filename,format='PNG',save_all=True,append_images=frames[1:],duration=[duration]*len(frames),loop=loop,disposal=0,blend=0,default_image=False,optimize=False)
    with Image.open(filename) as im:
        if im.n_frames<2 or im.size!=frames[0].size:raise RuntimeError('Exported APNG is static or has incorrect dimensions')
        decoded=[];total_ms=0
        for n in range(im.n_frames):
            im.seek(n);decoded.append(im.convert('RGBA').tobytes())
            total_ms+=im.info.get('duration',0)
        if len(set(decoded))<2:raise RuntimeError('Decoded APNG frames are identical')
        if abs(total_ms-len(frames)*duration)>2:raise RuntimeError('APNG playback duration does not match timeline')
    return filename

def export_gif(frames, filename, duration=100, loop=0):
    """Export pixel-sharp GIF with a consistent palette and reserved transparency.

    GIF only supports 256 palette entries and 10 ms timing increments. APNG is
    recommended when exact RGBA colors or alpha gradients are important.
    """
    validate_animation_export(frames, duration, loop)
    if duration % 10:
        raise ValueError('GIF frame duration must be a multiple of 10 ms; use APNG for exact timing.')
    filename = Path(filename)
    rgba = [f.convert('RGBA') for f in frames]
    # Build one shared palette from all visible frames to prevent palette flicker.
    # Index zero is always transparent; opaque pixels occupy indices 1..255.
    thumbnails = []
    for frame in rgba:
        rgb = Image.new('RGB', frame.size, (0, 0, 0))
        rgb.paste(frame, mask=frame.getchannel('A').point(lambda a: 255 if a >= 128 else 0))
        thumbnails.append(rgb)
    atlas_width = max(im.width for im in thumbnails)
    atlas = Image.new('RGB', (atlas_width, sum(im.height for im in thumbnails)))
    y = 0
    for im in thumbnails:
        atlas.paste(im, (0, y)); y += im.height
    palette_source = atlas.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    source_colors = palette_source.getpalette()[:255*3]
    shared = Image.new('P', (1, 1))
    shared.putpalette([0, 0, 0] + source_colors + [0] * (768 - 3 - len(source_colors)))
    indexed = []
    for frame, rgb in zip(rgba, thumbnails):
        quant = rgb.quantize(palette=palette_source, dither=Image.Dither.NONE)
        # Reserve index 0 for transparency, shift opaque indices up one.
        pixels = bytes((i + 1 if alpha >= 128 else 0)
                       for i, alpha in zip(quant.tobytes(), frame.getchannel('A').tobytes()))
        out = Image.frombytes('P', frame.size, pixels)
        out.putpalette(shared.getpalette())
        out.info['transparency'] = 0
        indexed.append(out)
    indexed[0].save(filename, format='GIF', save_all=True, append_images=indexed[1:],
                    duration=[duration] * len(indexed), loop=loop,
                    disposal=2, transparency=0, optimize=False)
    with Image.open(filename) as im:
        if im.n_frames < 2:
            raise RuntimeError('GIF export has no visible animation')
        total = 0
        for i in range(im.n_frames):
            im.seek(i); total += im.info.get('duration', 0)
        if abs(total - len(frames) * duration) > 10:
            raise RuntimeError('GIF export playback duration does not match timeline')
    return filename


def export_sprite_sheet(frames,filename,max_width=32768):
    """Export every timeline frame as a separate horizontal cell, including duplicates."""
    if not frames:raise ValueError('No frames to export')
    width,height=frames[0].size
    if any(f.size!=(width,height) for f in frames):
        raise ValueError('Frame dimensions differ')
    if width*len(frames)>max_width:
        raise ValueError('Sprite sheet is too wide; use fewer frames')
    sheet=Image.new('RGBA',(width*len(frames),height))
    for i,frame in enumerate(frames):sheet.paste(frame.convert('RGBA'),(i*width,0))
    filename=Path(filename);sheet.save(filename,format='PNG')
    with Image.open(filename) as check:
        if check.size!=sheet.size:raise RuntimeError('Sprite sheet dimensions are incorrect')
    return filename


def generate_traits(groups,count,seed=None):
    """groups: {category: [{name, weight, image?}]}"""
    rng=random.Random(seed);seen=set();result=[]
    for _ in range(count):
        for attempt in range(200):
            selected={}
            for category,options in groups.items():
                if not options:continue
                item=rng.choices(options,weights=[max(0,float(o.get('weight',1))) for o in options])[0]
                selected[category]=item['name']
            key=tuple(sorted(selected.items()))
            if key not in seen:seen.add(key);result.append(selected);break
        else:break
    return result


def compose_timeline_frames(layers, size, regions, count, edits=None):
    """Render procedural effects and apply per-frame RGBA paint/erase overlays.

    edits maps frame indices to lists of [x, y, r, g, b, a] entries.
    Alpha zero means erase that pixel from the final frame.
    """
    frames = frames_for(layers, size, count=count, regions=regions)
    for key, strokes in (edits or {}).items():
        idx = int(key)
        if not 0 <= idx < count:
            continue
        frame = frames[idx]
        for stroke in strokes:
            x, y, *rgba = map(int, stroke)
            if 0 <= x < size[0] and 0 <= y < size[1] and len(rgba) == 4:
                frame.putpixel((x, y), tuple(max(0, min(255, c)) for c in rgba))
    return frames
