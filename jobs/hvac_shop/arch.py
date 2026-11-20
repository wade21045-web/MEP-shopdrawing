import ezdxf,math,pickle
from ezdxf import path
d=ezdxf.readfile('out/input.dxf')
ins=d.entitydb['1054E9']
X0,X1,Y0,Y1=-65000,-48000,-37000,-24000
segs=[]
def go(e,depth=0):
    for v in e.virtual_entities():
        t=v.dxftype()
        if t=='INSERT':
            if depth<6: 
                try: go(v,depth+1)
                except Exception: pass
            continue
        try: p=path.make_path(v); pts=[(q.x,q.y) for q in p.flattening(5)]
        except Exception: continue
        if len(pts)<2: continue
        xs=[q[0] for q in pts]; ys=[q[1] for q in pts]
        if max(xs)<X0 or min(xs)>X1 or max(ys)<Y0 or min(ys)>Y1: continue
        for a,b in zip(pts,pts[1:]): segs.append((a,b,v.dxf.layer))
go(ins)
print(len(segs))
from collections import Counter; print(Counter(s[2] for s in segs).most_common(30))
pickle.dump(segs,open('arch.pkl','wb'))
