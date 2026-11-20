import ezdxf,pickle
from ezdxf import bbox
d=ezdxf.readfile('/workspace/hvac_shop/out/input.dxf'); m=d.modelspace()
X0,X1,Y0,Y1=-80500,-63000,-5000,5500
res=[];cache=bbox.Cache()
for e in m:
    try: b=bbox.extents([e],cache=cache,fast=True)
    except Exception: continue
    if not b.has_data: continue
    if b.extmax.x<X0 or b.extmin.x>X1 or b.extmax.y<Y0 or b.extmin.y>Y1: continue
    nm=e.dxf.name if e.dxftype()=='INSERT' else ''
    res.append((e.dxf.handle,e.dxftype(),e.dxf.layer,nm,tuple(b.extmin)[:2],tuple(b.extmax)[:2]))
pickle.dump(res,open('region.pkl','wb')); print(len(res))
import collections
c=collections.Counter(r[2] for r in res)
for k,v in c.most_common(): print(v,k)
