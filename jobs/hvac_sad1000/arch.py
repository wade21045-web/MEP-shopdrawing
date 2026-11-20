import ezdxf,pickle
from ezdxf.math import Matrix44
from ezdxf import path
d=ezdxf.readfile('/workspace/hvac_shop/out/input.dxf'); m=d.modelspace(); db=d.entitydb
segs=[]
def go(ents,M,depth,L0):
    for e in ents:
        t=e.dxftype(); L=e.dxf.layer if e.dxf.layer!='0' else L0
        if t=='INSERT':
            if depth>8: continue
            bp=d.blocks.get(e.dxf.name)
            if bp is None: continue
            go(bp,Matrix44.translate(*(-bp.block.dxf.base_point))@e.matrix44()@M,depth+1,L); continue
        if t not in('LINE','LWPOLYLINE','POLYLINE','ARC','CIRCLE'): continue
        try: p=path.make_path(e).transform(M); pts=[(v.x,v.y) for v in p.flattening(5)]
        except Exception: continue
        for a,b in zip(pts,pts[1:]):
            if -73000<max(a[0],b[0]) and min(a[0],b[0])<-68000 and -4000<max(a[1],b[1]) and min(a[1],b[1])<3000:
                segs.append((a,b,L))
go([db['1054E9']],Matrix44(),0,'')
pickle.dump(segs,open('arch.pkl','wb')); print(len(segs))
