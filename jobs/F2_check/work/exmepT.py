import ezdxf,collections,numpy as np,math,pickle,sys
from ezdxf import bbox, path as EP
from ezdxf.math import Matrix44
f,tag,ox_,oy_=sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4])
d=ezdxf.readfile(f); m=d.modelspace()
out=[]
for e in m:
    if e.dxftype()=='INSERT' and ('风口' in e.dxf.name) and e.dxf.layer.startswith('DUCT-'):
        b=d.blocks.get(e.dxf.name); ents=[x for x in b if x.dxftype()!='ATTDEF']
        bl=bbox.extents(ents,fast=True); bp=b.block.dxf.base_point
        Mi=Matrix44.translate(*(-bp))@e.matrix44()
        c=Mi.transform(bl.center); u=Mi.transform_direction((1,0,0)); w=Mi.transform_direction((0,1,0))
        ox,oy=bl.size.x*math.hypot(u.x,u.y),bl.size.y*math.hypot(w.x,w.y)
        pts=[]
        for x in ents:
            try:
                p=EP.make_path(x).transform(Mi)
                for sp in p.sub_paths():
                    v=np.array([(q.x+ox_,q.y+oy_) for q in sp.flattening(5)])
                    if len(v)>1: pts.append(v)
            except Exception: pass
        A=np.vstack(pts) if pts else np.array([[c.x+ox_,c.y+oy_]])
        out.append(dict(src=tag,h=e.dxf.handle,name=e.dxf.name,layer=e.dxf.layer,c=np.array([c.x+ox_,c.y+oy_]),ox=ox,oy=oy,rot=math.degrees(math.atan2(u.y,u.x))%360,pts=pts,lo=A.min(0),hi=A.max(0),atts={a.dxf.tag:a.dxf.text for a in e.attribs},sig=(e.dxf.name,e.dxf.layer,round(e.dxf.insert.x+ox_),round(e.dxf.insert.y+oy_),round(e.dxf.rotation),round(e.dxf.xscale,3),round(e.dxf.yscale,3))))
# labels: texts on DUCT-*标注 / M_AX texts near
T=[]
for e in m:
    if e.dxftype() in('TEXT','MTEXT'):
        try:
            s=e.plain_text() if e.dxftype()=='MTEXT' else e.dxf.text; p=e.dxf.insert
            T.append((e.dxf.layer,s,p.x+ox_,p.y+oy_))
        except Exception: pass
print(tag,len(out),collections.Counter((o['name'],o['layer'],round(min(o['ox'],o['oy'])),round(max(o['ox'],o['oy']))) for o in out).most_common())
pickle.dump(dict(H=out,T=T),open(f'hv_{tag}.pkl','wb'))
