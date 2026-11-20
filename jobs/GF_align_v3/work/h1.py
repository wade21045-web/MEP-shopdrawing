import ezdxf,collections,pickle,numpy as np,math
from ezdxf import bbox
d=ezdxf.readfile('odxf/d1.dxf'); m=d.modelspace()
PB=(-140000,15000,-65000,22000)
def inb(x,y): return PB[0]<x<PB[1] and PB[2]<y<PB[3]
c=collections.Counter(); out=[]
for e in m:
    L=e.dxf.layer
    if not ('风口' in L or '末端' in L): continue
    try: bb=bbox.extents([e],fast=True); cx,cy=bb.center.x,bb.center.y
    except: continue
    k=(L,e.dxftype(),e.dxf.name if e.dxftype()=='INSERT' else '', 'plan' if inb(cx,cy) else 'out')
    c[k]+=1
    out.append(dict(L=L,t=e.dxftype(),n=e.dxf.name if e.dxftype()=='INSERT' else '',x=cx,y=cy,sx=bb.size.x,sy=bb.size.y,h=e.dxf.handle,
        r=e.dxf.get('radius',0) if e.dxftype()=='CIRCLE' else 0, rot=e.dxf.get('rotation',0) if e.dxftype()=='INSERT' else 0, xs=e.dxf.get('xscale',1) if e.dxftype()=='INSERT' else 1, ys=e.dxf.get('yscale',1) if e.dxftype()=='INSERT' else 1))
for k,n in sorted(c.items()): print(n,k)
pickle.dump(out,open('h1_raw.pkl','wb'))
