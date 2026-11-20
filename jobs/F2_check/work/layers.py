import ezdxf,sys,collections,pickle,time
t=time.time()
f=sys.argv[1]; tag=sys.argv[2]
d=ezdxf.readfile(f); m=d.modelspace()
print(tag,'loaded',time.time()-t,'ents',len(m))
c=collections.Counter((e.dxf.layer,e.dxftype()) for e in m)
L=collections.Counter(e.dxf.layer for e in m)
with open(f'lay_{tag}.txt','w') as o:
    for l,n in L.most_common(): o.write(f'{n}\t{l}\n')
ins=collections.Counter((e.dxf.layer,e.dxf.name) for e in m if e.dxftype()=='INSERT')
with open(f'ins_{tag}.txt','w') as o:
    for (l,n),k in ins.most_common(): o.write(f'{k}\t{l}\t{n}\t{len(d.blocks.get(n)) if n in d.blocks else -1}\n')
from ezdxf import bbox
try:
    bb=bbox.extents(m,fast=True); print('ext',bb.extmin,bb.extmax)
except Exception as ex: print(ex)
print('layouts',[l.name for l in d.layouts], 'blocks',len(d.blocks))
