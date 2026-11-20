import ezdxf,pickle,sys
from ezdxf import bbox
src,X0,X1,Y0,Y1,out=sys.argv[1],*map(float,sys.argv[2:6]),sys.argv[6]
d=ezdxf.readfile(src); m=d.modelspace()
res=[];cache=bbox.Cache()
for e in m:
    if e.dxf.layer.startswith('新底图'): continue
    try: b=bbox.extents([e],cache=cache,fast=True)
    except Exception: continue
    if not b.has_data: continue
    if b.extmax.x<X0 or b.extmin.x>X1 or b.extmax.y<Y0 or b.extmin.y>Y1: continue
    nm=e.dxf.name if e.dxftype()=='INSERT' else ''
    res.append((e.dxf.handle,e.dxftype(),e.dxf.layer,nm,tuple(b.extmin)[:2],tuple(b.extmax)[:2]))
pickle.dump(res,open(out,'wb')); print(len(res))
