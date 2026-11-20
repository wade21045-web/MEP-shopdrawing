import ezdxf,pickle
from ezdxf import bbox
d=ezdxf.readfile('out/input.dxf'); m=d.modelspace()
X0,X1,Y0,Y1=-65000,-48000,-37000,-24000
cache=bbox.Cache()
res=[]
for e in m:
    try: b=bbox.extents([e],cache=cache,fast=True)
    except Exception: continue
    if not b.has_data: continue
    if b.extmax.x<X0 or b.extmin.x>X1 or b.extmax.y<Y0 or b.extmin.y>Y1: continue
    sz=(b.extmax-b.extmin)
    res.append((e.dxf.handle,e.dxftype(),e.dxf.layer,getattr(e.dxf,'name',''),round(sz.x),round(sz.y),tuple(round(v) for v in b.extmin),tuple(round(v) for v in b.extmax)))
print(len(res))
from collections import Counter
for k,v in Counter((r[1],r[2]) for r in res).most_common(100): print(k,v)
for r in res:
    if r[1]=='INSERT' and (r[4]>5000 or r[5]>5000): print(r)
pickle.dump(res,open('region.pkl','wb'))
