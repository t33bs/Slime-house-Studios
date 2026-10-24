"""Standalone pet-suite model; original imported images stay untouched."""
from .creature_rig import CreatureRig
from PIL import Image

class PetSuiteModel(CreatureRig):
    def __init__(self,size=(128,128)):
        super().__init__(size)
        self.originals=[]
    def import_part(self,name,image,width=None,height=None):
        image=image.convert('RGBA'); original=image.copy()
        w=width or image.width; h=height or image.height
        self.add_part(name,image.resize((int(w),int(h)),Image.Resampling.NEAREST))
        self.originals.append(original)
    def resize_part(self,index,width,height):
        original=self.originals[index] if index<len(self.originals) else self.parts[index]['image']
        self.parts[index]['image']=original.resize((max(1,int(width)),max(1,int(height))),Image.Resampling.NEAREST)
    @classmethod
    def load_project(cls,path):
        base=CreatureRig.load_project(path)
        obj=cls(base.size);obj.parts=base.parts;obj.animations=base.animations;obj.current=base.current
        obj.originals=[p['image'].copy() for p in obj.parts]
        return obj
