import ezdxf,sys
from ezdxf import bbox
d=ezdxf.readfile('GF_clean.dxf'); m=d.modelspace()
pts=[(-118739,19000),(-108627,19450),(34873,9480),(-111124,19000)]
for e in m:
    try: b=bbox.extents([e],fast=True)
    except: continue
    if not b.has_data: continue
    for (x,y) in pts:
        if b.extmin.x-50<x<b.extmax.x+50 and b.extmin.y-300<y<b.extmax.y+300 and b.size.x<3000:
            print((x,y),e.dxftype(),e.dxf.layer,e.dxf.get('name',''),[round(v) for v in b.center][:2],[round(v) for v in b.size][:2])
