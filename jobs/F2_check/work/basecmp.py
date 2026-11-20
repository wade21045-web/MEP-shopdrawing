import ezdxf,collections,pickle
from lib import walk
from ezdxf import bbox
def flat(f,off,names):
    d=ezdxf.readfile(f); m=d.modelspace(); res={}
    for ins in m.query('INSERT'):
        if ins.dxf.name not in names: continue
        c=collections.Counter()
        for e,M,ef,ch in walk(d,[ins]):
            try:
                bb=bbox.extents([e],fast=True)
                if not bb.has_data: c[(e.dxftype(),ef,'nobb')]+=1; continue
                lo=M.transform(bb.extmin); hi=M.transform(bb.extmax)
                c[(e.dxftype(),ef,round(min(lo.x,hi.x)+off[0]),round(min(lo.y,hi.y)+off[1]),round(max(lo.x,hi.x)+off[0]),round(max(lo.y,hi.y)+off[1]))]+=1
            except Exception: c[(e.dxftype(),ef,'err')]+=1
        res[(ins.dxf.name,round(ins.dxf.insert.x+off[0]),round(ins.dxf.insert.y+off[1]))]=c
    return res
N={'A$C25902DC9','C15358-00-AATC-DD-BASE-AR1','C15358-00-AATC-DD-BASE-AR2'}
import sys
A=flat('dxf/F02-MEP-ACD.dxf',(0,0),N); B=flat('dxf/F02-MEP-B_hotel.dxf',(28961.42114549,285185.2827819),N)
for k,cb in B.items():
    ca=A.get(k)
    if ca is None: print(k,'no A counterpart'); continue
    d1=ca-cb; d2=cb-ca
    print(k,sum(ca.values()),sum(cb.values()),'onlyA',sum(d1.values()),'onlyB',sum(d2.values()))
    print('  onlyA sample',list(d1.items())[:5]); print('  onlyB sample',list(d2.items())[:5])
