import ezdxf,json
from collections import Counter
log=json.load(open('build_log.json'))
d=ezdxf.readfile('out/input.dxf'); db=d.entitydb; m=d.modelspace()
dl=set(h for v in log['deleted'].values() for h in v)
def inter(p1,p2,p3,p4):
    def cr(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    d1,d2,d3,d4=cr(p3,p4,p1),cr(p3,p4,p2),cr(p1,p2,p3),cr(p1,p2,p4)
    return (d1*d2<0) and (d3*d4<0)
X0,X1,Y0,Y1=-65000,-48000,-37000,-24000
others=[]
for e in m.query('LINE'):
    if e.dxf.handle in dl: continue
    L=e.dxf.layer
    if not (L.startswith('DUCT') or L.startswith('管道') or L.startswith('EQ') or L.startswith('PIPE')): continue
    a,b=e.dxf.start,e.dxf.end
    if max(a.x,b.x)<X0 or min(a.x,b.x)>X1 or max(a.y,b.y)<Y0 or min(a.y,b.y)>Y1: continue
    others.append((a,b,L))
for room,hs in log['deleted'].items():
    no=[]
    for h in hs:
        e=db[h]
        if e.dxftype()=='LINE': segs=[(e.dxf.start,e.dxf.end)]
        elif e.dxftype()=='LWPOLYLINE': p=list(e.get_points('xy')); segs=list(zip(p,p[1:]))
        else: continue
        for a,b in segs:
            for oa,ob,oL in others:
                if inter(a,b,oa,ob): no.append((e.dxf.layer,oL))
    print(room,'ORIGINAL crossings',len(no),Counter(no).most_common())
