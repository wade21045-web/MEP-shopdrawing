import ezdxf,collections,sys
from ezdxf import bbox
d=ezdxf.readfile(sys.argv[1]); m=d.modelspace()
memo={}
def cnt(n,depth=0):
    if n in memo: return memo[n]
    c=collections.Counter()
    if n not in d.blocks or depth>15: return c
    for e in d.blocks.get(n):
        if e.dxftype()=='INSERT': 
            for k,v in cnt(e.dxf.name,depth+1).items(): c[k]+=v
        else: c[e.dxf.layer]+=1
    memo[n]=c; return c
for e in m:
    if e.dxftype()!='INSERT': continue
    c=cnt(e.dxf.name); tot=sum(c.values())
    if tot<20: continue
    try: bb=bbox.extents([e],fast=True); bs=f'[{bb.extmin.x:.0f},{bb.extmax.x:.0f}]x[{bb.extmin.y:.0f},{bb.extmax.y:.0f}]'
    except Exception as ex: bs='?'
    print(e.dxf.layer,e.dxf.name,tuple(round(v,1) for v in e.dxf.insert),round(e.dxf.rotation,3),round(e.dxf.xscale,4),tot,bs, c.most_common(12))
