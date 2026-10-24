"""Editable layered creature rig, frame poses, and transparent atlas export."""
import json, math
from pathlib import Path
from PIL import Image

class CreatureRig:
    def __init__(self, size=(128,128)):
        self.size=tuple(size);self.parts=[];self.animations={};self.current='Idle'
    def add_part(self, name, image, x=0,y=0):
        if image.mode!='RGBA':image=image.convert('RGBA')
        self.parts.append({'name':name,'image':image.copy(),'x':int(x),'y':int(y),'visible':True})
    def snapshot(self):
        return [{k:v for k,v in part.items() if k!='image'} for part in self.parts]
    def save_frame(self,animation=None):
        name=animation or self.current
        self.animations.setdefault(name,[]).append(self.snapshot())
    def render(self, pose=None):
        canvas=Image.new('RGBA',self.size)
        states=pose if pose is not None else self.snapshot()
        for i,state in enumerate(states):
            if i>=len(self.parts):break
            if state.get('visible',True):canvas.alpha_composite(self.parts[i]['image'],(int(state['x']),int(state['y'])))
        return canvas
    def export(self,folder,basename='creature',columns=4,spacing=0):
        folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
        frames=[];meta=[]
        for animation,poses in self.animations.items():
            for index,pose in enumerate(poses):
                frames.append(self.render(pose));meta.append({'animation':animation,'frame':index,'duration_ms':125})
        if not frames:frames=[self.render()];meta=[{'animation':'Idle','frame':0,'duration_ms':125}]
        columns=max(1,min(int(columns),len(frames)));spacing=max(0,int(spacing));w,h=self.size
        rows=math.ceil(len(frames)/columns)
        sheet=Image.new('RGBA',(columns*w+(columns-1)*spacing,rows*h+(rows-1)*spacing))
        for i,frame in enumerate(frames):
            x=(i%columns)*(w+spacing);y=(i//columns)*(h+spacing)
            sheet.alpha_composite(frame,(x,y));meta[i]['rect']={'x':x,'y':y,'w':w,'h':h}
        png=folder/(basename+'_sheet.png');sheet.save(png)
        manifest={'version':1,'frame_size':[w,h],'sheet_size':list(sheet.size),'frames':meta}
        (folder/(basename+'_sheet.json')).write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        return png
    def save_project(self,path):
        path=Path(path);assets=path.with_suffix('');assets.mkdir(parents=True,exist_ok=True)
        for i,p in enumerate(self.parts):p['image'].save(assets/f'part_{i:03d}.png')
        data={'version':1,'size':list(self.size),'parts':self.snapshot(),'animations':self.animations,'current':self.current}
        path.write_text(json.dumps(data,indent=2),encoding='utf-8')
    @classmethod
    def load_project(cls,path):
        path=Path(path);data=json.loads(path.read_text(encoding='utf-8'));rig=cls(data['size'])
        for i,p in enumerate(data['parts']):
            image=Image.open(path.with_suffix('')/f'part_{i:03d}.png').convert('RGBA')
            rig.add_part(p['name'],image,p['x'],p['y']);rig.parts[-1]['visible']=p.get('visible',True)
        rig.animations=data.get('animations',{});rig.current=data.get('current','Idle')
        return rig
