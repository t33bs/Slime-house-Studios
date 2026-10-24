"""Template-driven pixel-perfect pet animation generation and atlas export.

No inferred anatomy: flattened templates use non-destructive whole-sprite motions;
optional eye masks and separate artwork can be added in later rigging passes.
"""
import json
import math
import re
from pathlib import Path
from PIL import Image, ImageDraw

LIFE_ANIMATIONS = ('Idle breathing', 'Sleeping', 'Eating', 'Pooping', 'Happy bounce', 'Curious head tilt', 'Walking', 'Hopping', 'Being petted', 'Yawning', 'Drinking', 'Sitting down', 'Grooming', 'Stretching', 'Confused', 'Excited', 'Sad / Lonely', 'Angry / Pouting', 'Shy / Blushing', 'Startled', 'Bored', 'Affectionate', 'Running', 'Flying / Hovering', 'Turning around', 'Sniffing', 'Looking around', 'Getting picked up', 'Waving hello', 'Celebrating', 'Falling asleep')
BATTLE_ANIMATIONS = ('Attack', 'Block', 'Dodge', 'Hit', 'Victory', 'Defeat')
ANIMATIONS = LIFE_ANIMATIONS + ('Idle', 'Blink', 'Walk', 'Hop', 'Eat', 'Sleep', 'Poop') + BATTLE_ANIMATIONS
DEFAULT_FPS = 8

# Human-readable frame recipes are intentionally separate from automatic transforms.
# A flattened image cannot reveal hidden limbs, closed eyelids or mouth interiors.
ANIMATION_RECIPES = {
 'Idle': ('Standing body; optional head, chest and tail layers', 'Breath in → hold → breath out → neutral', 'Keep feet planted; use a 1-pixel chest rise or squash', 'Seamless loop'),
 'Blink': ('Eyes or eyelid overlay; neutral face', 'Eyes open → half closed → closed → half closed → open', 'Mark eye pixels or draw an eyelid layer; flattened templates cannot detect eyes reliably', 'Seamless loop with a pause'),
 'Walk': ('Separate front/back legs or alternate leg poses; grounded feet', 'Contact → passing → opposite contact → passing', 'Alternate paws; avoid sliding the whole body as the final animation', 'Seamless loop'),
 'Hop': ('Body and shadow layers; optional ears', 'Crouch → launch → airborne → land → recover', 'Raise body while shadow stays on ground; squash on landing', 'Seamless loop'),
 'Eat': ('Head, mouth/cheeks, food prop and front paws', 'Notice food → head lowers → mouth opens → chew twice → swallow → idle', 'Make 2 mouth shapes and alternate them; food can shrink or disappear', 'Play once or loop chewing'),
 'Sleep': ('Closed eyelids, body and optional Zzz overlay', 'Get comfortable → eyes close → breathing in → breathing out → wake', 'Draw closed eyelids; small slow chest motion; keep feet stable', 'Loop sleeping section'),
 'Poop': ('Body/legs, tail and optional tiny poop prop', 'Prepare → squat → strain → prop appears → stand → idle', 'Lower body 1–2 pixels, move tail aside, reveal prop behind creature', 'Play once'),
 'Attack': ('Arm/weapon or attacking limb; optional slash effect', 'Anticipate → wind-up → strike → follow-through → recover', 'Keep weapon anchored to paw; use a readable silhouette', 'Play once'),
 'Block': ('Defending arm/shield or defensive body pose', 'Notice threat → brace → hold → release', 'Hold the strongest block pose for several frames', 'Play once or hold'),
 'Dodge': ('Body, legs and optional motion trail', 'Anticipate → sidestep → farthest point → return', 'Shift feet or add squash; preserve ground contact', 'Play once'),
 'Hit': ('Body and optional flash overlay', 'Impact → recoil → shake → settle', 'Keep recoil short and readable; flash should not hide face', 'Play once'),
 'Victory': ('Arms, face, optional confetti', 'React → jump/raise arms → celebrate → idle', 'Make a clear happy face and one peak celebration pose', 'Play once'),
 'Defeat': ('Body, face and optional dust', 'Stagger → slump → collapse → still', 'Create a deliberate collapsed pose instead of shrinking alone', 'Play once; hold final frame'),
}


# Body-part templates are instructions, not guessed anatomy.
POSE_TEMPLATES = {
    'General / unknown': ('body', 'head', 'eyes', 'mouth', 'feet', 'tail'),
    'Two-legged': ('torso', 'head', 'eyes', 'mouth', 'arms', 'legs'),
    'Four-legged': ('torso', 'head', 'eyes', 'mouth', 'front paws', 'back paws', 'tail'),
    'Flying / winged': ('body', 'head', 'eyes', 'wings', 'tail'),
    'Floating / limbless': ('body', 'head', 'eyes', 'mouth'),
    'Crawling': ('body', 'head', 'eyes', 'mouth', 'feet', 'tail'),
}
# Each entry includes editable key poses and a truthful hint about required art.
LIFE_RECIPES = {
'Idle breathing': ('body, chest and optional tail', 'neutral → inhale → hold → exhale → neutral', 'Keep feet planted; vary the chest by a single pixel.', 'Loop'),
'Sleeping': ('closed eyelids, body and Zzz overlay', 'settle → close eyes → inhale → exhale', 'Draw closed eyes separately for a convincing sleep.', 'Loop'),
'Eating': ('head, mouth, paws and food prop', 'notice food → lower head → open mouth → chew → swallow → neutral', 'Provide open and closed mouth sprites; food may shrink.', 'Once or chew loop'),
'Pooping': ('body, tail and small prop', 'prepare → squat → strain → poop appears → recover', 'Put the prop behind the creature, not over its face.', 'Once'),
'Happy bounce': ('body, feet, shadow', 'crouch → jump → peak → land → neutral', 'Keep the shadow grounded and add a happy face.', 'Loop'),
'Curious head tilt': ('separate head and neck', 'notice → tilt head → hold → return', 'A separate head layer gives a cleaner tilt.', 'Once'),
'Walking': ('front/back legs and feet', 'contact → passing → opposite contact → passing', 'Use alternate paw poses to avoid sliding.', 'Loop'),
'Hopping': ('body and ground shadow', 'crouch → rise → apex → land → recover', 'Keep the shadow still while the body rises.', 'Loop'),
'Being petted': ('head, eyes and optional hearts', 'notice hand → lean → close eyes → content → neutral', 'Head and eye layers make this feel affectionate.', 'Once'),
'Yawning': ('head, mouth and eyelids', 'sleepy → mouth opens → wide yawn → close → neutral', 'Create a large open-mouth drawing for the middle frames.', 'Once'),
'Drinking': ('head, mouth and water bowl', 'notice water → lower head → sip → ripple → lift', 'Keep the bowl fixed and animate a small ripple.', 'Once or sip loop'),
'Sitting down': ('legs and lower torso', 'standing → bend knees → lower → seated', 'Draw a seated pose; squash alone is only a placeholder.', 'Once'),
'Grooming': ('paw, head, tongue', 'raise paw → lick paw → rub face → lower paw', 'Requires a paw-up pose for convincing grooming.', 'Once or loop'),
'Stretching': ('front legs, back and head', 'prepare → reach forward → arch back → hold → relax', 'Separate limb art improves the silhouette.', 'Once'),
'Confused': ('head, eyes and question-mark overlay', 'notice → tilt → question mark → wobble → neutral', 'Use a tiny question mark as a removable overlay.', 'Once'),
'Excited': ('body, feet and optional sparkles', 'anticipate → bounce → bounce → settle', 'Faster body bobbing and a smiling face sell excitement.', 'Once or loop'),
'Sad / Lonely': ('eyes, mouth, head and tear overlay', 'neutral → head droops → sigh → hold → recover', 'A downturned mouth and eyes need separate face art.', 'Once'),
'Angry / Pouting': ('eyes, eyebrows and body', 'notice → fur puff → shake → pout → neutral', 'Draw eyebrows separately for a readable expression.', 'Once'),
'Shy / Blushing': ('eyes, cheeks and head', 'notice → glance away → blush → hide → neutral', 'Blush overlay is easy; eye direction needs face edits.', 'Once'),
'Startled': ('body, eyes and feet', 'neutral → recoil → jump → land → settle', 'Use a sudden 1–3 pixel jump and wide-eye art.', 'Once'),
'Bored': ('eyes, head and body', 'idle → slow blink → slouch → sigh → idle', 'Long holds make boredom legible.', 'Loop'),
'Affectionate': ('head, body and hearts', 'approach → lean → nuzzle → hearts → return', 'Nuzzling works best with an independent head layer.', 'Once'),
'Running': ('legs, feet and body', 'contact → push-off → airborne → contact', 'Needs leg poses; body bob is only a draft.', 'Loop'),
'Flying / Hovering': ('wings, body and shadow', 'wings down → lift → wings up → hover → lower', 'Wing layers enable proper flapping.', 'Loop'),
'Turning around': ('front, side and back views', 'front → three-quarter → side → back', 'Cannot infer unseen back artwork from one flattened PNG.', 'Once'),
'Sniffing': ('head, nose and optional sniff marks', 'notice → lean down → sniff → sniff → lift', 'Nose and head motion work best on separate layers.', 'Once'),
'Looking around': ('eyes and head', 'center → left → center → right → center', 'Create eye-direction drawings or use eye masks.', 'Loop'),
'Getting picked up': ('body, paws and optional hand', 'notice → lift → dangle → hold → lower', 'Separate paws let them dangle naturally.', 'Once'),
'Waving hello': ('arm/paw and shoulder', 'raise paw → wave left → wave right → lower', 'Needs a raised-paw pose or a rigged arm.', 'Once'),
'Celebrating': ('body, arms and confetti', 'anticipate → jump → cheer → confetti → land', 'Optional confetti can be generated without new poses.', 'Once'),
'Falling asleep': ('eyelids, head and body', 'drowsy → yawn → droop → close eyes → sleep', 'Draw closed eyelids and a resting pose.', 'Once'),
}
ANIMATION_RECIPES.update(LIFE_RECIPES)

def animation_guide(action, frame_count=8, body_type='General / unknown'):
    """Produce practical, honest guidance for a hand-refined animation."""
    if action not in ANIMATION_RECIPES:
        raise ValueError(f'Unknown animation: {action}')
    if not 2 <= frame_count <= 24:
        raise ValueError('Frame count must be between 2 and 24')
    parts, stages, notes, playback = ANIMATION_RECIPES[action]
    phases = [part.strip() for part in stages.split('→')]
    timeline = [{'frame': i+1, 'pose': phases[min(len(phases)-1, i*len(phases)//frame_count)]}
                for i in range(frame_count)]
    return {'action':action, 'body_type':body_type, 'parts_to_prepare':parts,
            'key_poses':phases, 'drawing_tip':notes, 'playback':playback,
            'frames':timeline, 'auto_generation_limit':
            'Automatic starter frames use whole-body movement; detailed face/limb poses require layers or hand edits.'}

def format_animation_guide(guide):
    lines = [f"{guide['action'].upper()} — {guide['body_type']}",
             f"PARTS: {guide['parts_to_prepare']}",
             f"POSES: {' → '.join(guide['key_poses'])}",
             f"TIP: {guide['drawing_tip']}", f"PLAYBACK: {guide['playback']}", '', 'FRAME-BY-FRAME PLAN:']
    lines.extend(f"  {entry['frame']:02d}. {entry['pose']}" for entry in guide['frames'])
    lines.extend(['', 'AUTO-GENERATION LIMIT:', guide['auto_generation_limit']])
    return '\n'.join(lines)

def export_animation_guides(actions, folder, basename, frame_count=8, body_type='General / unknown'):
    """Export a readable creation guide and structured recipes alongside the atlas."""
    basename = re.sub(r'[^a-zA-Z0-9_-]+', '_', basename).strip('_') or 'pet'
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    guides = [animation_guide(action, frame_count, body_type) for action in actions]
    (folder / f'{basename}_animation_guide.txt').write_text(
        'SLIME HOUSE STUDIOS — ANIMATION CREATION GUIDE\n\n' +
        '\n\n' + ('\n' + '='*54 + '\n\n').join(format_animation_guide(g) for g in guides),
        encoding='utf-8')
    (folder / f'{basename}_animation_recipes.json').write_text(
        json.dumps({'version':1,'body_type':body_type,'recipes':guides}, indent=2), encoding='utf-8')
    return guides

def _offset(image, dx=0, dy=0):
    output = Image.new('RGBA', image.size)
    output.alpha_composite(image, (int(dx), int(dy)))
    return output

def _scaled(image, width, height, bottom=True):
    width, height = max(1, int(width)), max(1, int(height))
    scaled = image.resize((width, height), Image.Resampling.NEAREST)
    output = Image.new('RGBA', image.size)
    output.alpha_composite(scaled, ((image.width-width)//2, image.height-height if bottom else (image.height-height)//2))
    return output

def _effect(image, kind, tick, total):
    """Generate deterministic nearest-neighbor motion from a flattened template."""
    w, h = image.size
    p = tick / max(1, total)
    amp = max(1, min(w, h)//24)
    # Starter movement families: pose-specific facial/limb art remains editable work.
    aliases = {
        'Idle breathing':'Idle', 'Sleeping':'Sleep', 'Eating':'Eat', 'Pooping':'Poop',
        'Happy bounce':'Victory', 'Walking':'Walk', 'Hopping':'Hop',
        'Excited':'Victory', 'Running':'Walk', 'Flying / Hovering':'Hop',
        'Celebrating':'Victory', 'Startled':'Hop', 'Falling asleep':'Sleep',
        'Sitting down':'Sleep', 'Stretching':'Idle', 'Getting picked up':'Hop',
        'Being petted':'Idle', 'Yawning':'Eat', 'Drinking':'Eat',
        'Grooming':'Eat', 'Sniffing':'Eat', 'Bored':'Sleep',
        'Sad / Lonely':'Sleep', 'Angry / Pouting':'Hit',
        'Affectionate':'Idle', 'Shy / Blushing':'Idle',
        'Curious head tilt':'Idle', 'Confused':'Hit', 'Turning around':'Idle',
        'Looking around':'Idle', 'Waving hello':'Idle'
    }
    if kind in aliases:
        kind = aliases[kind]
    if kind == 'Idle':
        return _scaled(image, w, h + (1 if tick % 4 < 2 else 0))
    if kind == 'Blink':
        # A flattened image has no reliable eye segmentation; don't fake an eye edit.
        return image.copy()
    if kind == 'Walk':
        return _offset(image, (tick % 4 - 1)*amp, -(tick % 2))
    if kind == 'Hop':
        return _offset(image, 0, -round(math.sin(math.pi * p)*min(5, amp*3)))
    if kind == 'Eat':
        return _offset(image, 0, tick % 3 == 1)
    if kind == 'Sleep':
        return _scaled(image, w, max(1, h - (tick % 4 < 2)))
    if kind == 'Poop':
        frame = _scaled(image, w, max(1, h - (2 if tick % 4 in (1,2) else 0)))
        if tick >= total//2:
            draw = ImageDraw.Draw(frame)
            x = min(w-2, w//2 + max(2, w//5))
            y = min(h-2, h-3)
            draw.rectangle((x,y,x+1,y+1), fill=(115,70,43,255))
        return frame
    if kind == 'Attack':
        return _offset(image, round(math.sin(math.pi*p)*min(5,amp*3)), 0)
    if kind == 'Block':
        return _offset(image, -amp, 0)
    if kind == 'Dodge':
        return _offset(image, -round(math.sin(math.pi*p)*min(7,amp*4)), 0)
    if kind == 'Hit':
        return _offset(image, (-amp if tick%2 else amp), 0)
    if kind == 'Victory':
        return _offset(image, 0, -round(abs(math.sin(2*math.pi*p))*min(4,amp*2)))
    if kind == 'Defeat':
        return _scaled(image, w, max(1,h-round(p*min(6,h//5))))
    raise ValueError(kind)

# Editable rectangular cutout regions: user defines the anatomy; no guessed pixels.
RIG_PARTS = ('head', 'eyes', 'mouth', 'left paw', 'right paw', 'tail', 'wings')
PART_ACTIONS = {
    'Eating': ('head','mouth'), 'Drinking': ('head','mouth'),
    'Yawning': ('head','mouth'), 'Grooming': ('head','left paw'),
    'Waving hello': ('right paw',), 'Being petted': ('head',),
    'Affectionate': ('head',), 'Curious head tilt': ('head',),
    'Looking around': ('eyes','head'), 'Sniffing': ('head',),
    'Sleeping': ('eyes',), 'Falling asleep': ('eyes','head'),
    'Flying / Hovering': ('wings',), 'Happy bounce': ('tail',),
}

def validate_regions(regions, size):
    """Normalize user-marked [x,y,width,height] pixel rectangles."""
    w,h=size
    clean={}
    for name, rect in (regions or {}).items():
        if name not in RIG_PARTS or not isinstance(rect,(list,tuple)) or len(rect)!=4:
            raise ValueError(f'Invalid body part: {name}')
        if any(isinstance(v,bool) or not isinstance(v,int) for v in rect):
            raise ValueError('Region coordinates must be integer pixels')
        x,y,rw,rh=rect
        if x<0 or y<0 or rw<1 or rh<1 or x+rw>w or y+rh>h:
            raise ValueError(f'{name} region is outside the template')
        clean[name]=[x,y,rw,rh]
    # Overlap would punch holes or create duplicate pixels; require clean partitions.
    occupied=set()
    for name,(x,y,rw,rh) in clean.items():
        for py in range(y,y+rh):
            for px in range(x,x+rw):
                if (px,py) in occupied:
                    raise ValueError(f'Overlapping body-part regions: {name}')
                occupied.add((px,py))
    return clean

def generate_rigged(source, actions, regions, frame_count=8):
    """Move manually identified body parts independently; no interpolation blur."""
    image=source.convert('RGBA')
    clean=validate_regions(regions,image.size)
    baseline=generate(image,actions,frame_count)
    if not clean:
        return baseline
    result={}
    for action,frames in baseline.items():
        moving=[part for part in PART_ACTIONS.get(action,()) if part in clean]
        if not moving:
            result[action]=frames
            continue
        output=[]
        for i,frame in enumerate(frames):
            # Remove source pixels at original regions from the generated frame,
            # then composite extracted parts at deterministic integer offsets.
            frame=frame.copy()
            phase=math.sin(2*math.pi*i/frame_count)
            for part in moving:
                x,y,w,h=clean[part]
                cutout=image.crop((x,y,x+w,y+h))
                dx=dy=0
                if part=='mouth':dy=1 if i%3==1 else 0
                elif part=='eyes':dy=1 if i%4==2 else 0
                elif part=='head':dy=round(phase*2)
                elif part=='wings':dy=round(phase*3)
                elif part in ('left paw','right paw'):dy=round(phase*2)
                elif part=='tail':dx=round(phase*2)
                # Punch out only nontransparent pixels from the original region.
                # The cutout is then restored at its new location.
                clear=Image.new('RGBA',(w,h))
                frame.paste(clear,(x,y))
                frame.alpha_composite(cutout,(x+dx,y+dy))
            output.append(frame)
        result[action]=output
    return result

def generate(source, actions, frame_count=8):
    """Return {action: [RGBA images]}; retain source pixels and transparency."""
    if not 2 <= frame_count <= 24:
        raise ValueError('Frame count must be between 2 and 24')
    if not actions or any(action not in ANIMATIONS for action in actions):
        raise ValueError('Select supported animation presets')
    image = source.convert('RGBA')
    if not (1 <= image.width <= 1024 and 1 <= image.height <= 1024):
        raise ValueError('Template dimensions must be 1–1024 pixels')
    return {action: [_effect(image, action, tick, frame_count) for tick in range(frame_count)] for action in actions}

def _slug(name):
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')

def export_package(animations, folder, basename='pet', fps=DEFAULT_FPS, frame_pngs=True, gif=True, apng=True, anchors=None):
    """Export a fixed-grid RGBA PNG atlas and readable, game-agnostic JSON."""
    if not animations or not 1 <= fps <= 30:
        raise ValueError('Provide animations and an FPS between 1 and 30')
    basename = re.sub(r'[^a-zA-Z0-9_-]+', '_', basename).strip('_') or 'pet'
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    first = next(iter(animations.values()))[0]
    w, h = first.size
    columns = max(len(frames) for frames in animations.values())
    rows = len(animations)
    if columns*w > 16384 or rows*h > 16384:
        raise ValueError('Sprite sheet exceeds 16384 pixels; use a smaller template')
    atlas = Image.new('RGBA', (columns*w, rows*h))
    duration = round(1000/fps)
    meta = {'version':1, 'image':f'{basename}_sheet.png', 'frame_size':{'width':w,'height':h}, 'fps':fps, 'animations':{}, 'anchors':anchors or {}}
    for row,(action, frames) in enumerate(animations.items()):
        if not frames or any(frame.size != (w,h) for frame in frames):
            raise ValueError('All frames must have identical dimensions')
        frames_info = []
        for col,frame in enumerate(frames):
            x,y=col*w,row*h
            atlas.alpha_composite(frame.convert('RGBA'), (x,y))
            frames_info.append({'x':x,'y':y,'w':w,'h':h,'duration_ms':duration})
            if frame_pngs:
                directory=folder / f'{basename}_frames' / _slug(action)
                directory.mkdir(parents=True,exist_ok=True)
                frame.save(directory/f'{col:03d}.png')
        meta['animations'][_slug(action)]={'loop':action in ('Idle','Blink','Walk','Hop','Eat','Sleep','Poop','Block','Idle breathing','Sleeping','Happy bounce','Walking','Hopping','Running','Flying / Hovering','Looking around','Bored'), 'frames':frames_info}
        if gif:
            frames[0].save(folder/f'{basename}_{_slug(action)}.gif',save_all=True,append_images=frames[1:],duration=duration,loop=0,disposal=2,optimize=False)
        if apng:
            frames[0].save(folder/f'{basename}_{_slug(action)}.png',format='PNG',save_all=True,append_images=frames[1:],duration=duration,loop=0)
    atlas.save(folder/meta['image'])
    (folder/f'{basename}_animations.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return meta
