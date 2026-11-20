import ezdxf,sys,collections
from ezdxf import bbox
d=ezdxf.readfile(sys.argv[1]); m=d.modelspace()
print(collections.Counter(e.dxftype() for e in m))
def size(n,seen=None):
    b=d.blocks.get(n); s=0
    for e in b:
        s+=1
        if e.dxftype()=='INSERT' and e.dxf.name in d.blocks and e.dxf.name!=n: s+=size(e.dxf.name)
    return s
for e in m:
    if e.dxftype()=='INSERT' and e.dxf.name in d.blocks:
        s=size(e.dxf.name)
        if s>2000:
            try: bb=bbox.extents([e],fast=True); ext=(bb.extmin.round(0),bb.extmax.round(0))
            except Exception: ext=None
            print(e.dxf.layer,e.dxf.name,s,e.dxf.insert.round(0),ext)
