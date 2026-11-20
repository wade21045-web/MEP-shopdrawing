import ezdxf,collections
from lib import walk
from ezdxf import bbox
d=ezdxf.readfile('/workspace/GF_hvac/output/GF_暖通+建筑结构底图.dxf')
c=collections.Counter(); sz={}
def stop(e,ef,ch): return True   # only top level inside the HVAC block
for root in ['A$C5E357C2F','A$C124230B8']:
  for e in d.blocks.get(root):
    if e.dxftype()=='INSERT':
        c[(root[:6],e.dxf.name[:50],e.dxf.layer)]+=1
        if e.dxf.name not in sz:
            try: bb=bbox.extents([e],fast=True); sz[e.dxf.name]=(round(bb.size.x),round(bb.size.y))
            except: sz[e.dxf.name]=None
for k,n in c.most_common(80): print(n,k,sz.get(k[1]) if k[1] in sz else '')
