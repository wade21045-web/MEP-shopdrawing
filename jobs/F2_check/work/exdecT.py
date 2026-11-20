import ezdxf,collections,numpy as np,re,math,pickle
from ezdxf import bbox
from ezdxf.math import Matrix44
from lib import walk
OFF=pickle.load(open('off_dec.pkl','rb'))
d=ezdxf.readfile('dxf/L2-大平面-升版9.2.dxf'); m=d.modelspace()
TERM={'方形风口','$风口$00000092','DIFF-WLL','$轴流风机$00000011','$电动风口$00000009','$风口$00000101'}
def stop(e,ef,ch): return e.dxf.name in TERM
out=[]
for e,M,ef,ch in walk(d,m,stop=stop):
    if e.dxftype()!='INSERT' or e.dxf.name not in TERM: continue
    b=d.blocks.get(e.dxf.name)
    ents=[x for x in b if x.dxftype() not in('ATTDEF',)]
    bl=bbox.extents(ents,fast=True); bp=b.block.dxf.base_point
    Mi=(Matrix44.translate(*(-bp))@e.matrix44())@M
    c=Mi.transform(bl.center)
    u=Mi.transform_direction((1,0,0)); w=Mi.transform_direction((0,1,0)); sx=math.hypot(u.x,u.y); sy=math.hypot(w.x,w.y)
    ang=math.degrees(math.atan2(Mi[0,1],Mi[0,0]))%360
    ox,oy=bl.size.x*sx,bl.size.y*sy
    # outline polylines in world
    pts=[]
    from ezdxf import path as EP
    for x in ents:
        try:
            p=EP.make_path(x).transform(Mi)
            for sp in p.sub_paths():
                v=np.array([(q.x+OFF[0],q.y+OFF[1]) for q in sp.flattening(5)])
                if len(v)>1: pts.append(v)
        except Exception: pass
    out.append(dict(name=e.dxf.name,layer=ef,chain=ch,x=c.x+OFF[0],y=c.y+OFF[1],ox=ox,oy=oy,rot=ang,pts=pts,handle=e.dxf.handle,atts={a.dxf.tag:a.dxf.text for a in e.attribs}))
print(len(out))
c=collections.Counter((o['name'],o['chain'][:1],round(min(o['ox'],o['oy'])),round(max(o['ox'],o['oy']))) for o in out)
for k,v in c.most_common(): print(v,k)
pickle.dump(out,open('dec_raw.pkl','wb'))
