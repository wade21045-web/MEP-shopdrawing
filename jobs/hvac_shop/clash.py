import ezdxf,pickle,json
from ezdxf import path
from common import *
arch=pickle.load(open('arch.pkl','rb'))
walls=[(a,b,L) for a,b,L in arch if L.startswith('AR-WALL') or L=='墙体完成面']
log=json.load(open('build_log.json'))
d=ezdxf.readfile('out_after.dxf'); db=d.entitydb; m=d.modelspace()
new=set(h for v in log['added'].values() for h in v)
def inter(p1,p2,p3,p4):
    def cr(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    d1,d2,d3,d4=cr(p3,p4,p1),cr(p3,p4,p2),cr(p1,p2,p3),cr(p1,p2,p4)
    return (d1*d2<0) and (d3*d4<0)
X0,X1,Y0,Y1=-65000,-48000,-37000,-24000
others=[]
for e in m.query('LINE'):
    if e.dxf.handle in new: continue
    L=e.dxf.layer
    if not (L.startswith('DUCT') or L.startswith('管道') or L.startswith('EQ') or L.startswith('PIPE')): continue
    a,b=e.dxf.start,e.dxf.end
    if max(a.x,b.x)<X0 or min(a.x,b.x)>X1 or max(a.y,b.y)<Y0 or min(a.y,b.y)>Y1: continue
    others.append((a,b,L,e.dxf.handle))
O=DIFF['D043']
for room,hs in log['added'].items():
    nw=0; no=[]
    for h in hs:
        e=db[h]
        if e.dxftype()=='LINE': segs=[(e.dxf.start,e.dxf.end)]
        elif e.dxftype()=='LWPOLYLINE':
            p=list(e.get_points('xy')); segs=list(zip(p,p[1:]))
        else: continue
        for a,b in segs:
            for w in walls:
                if inter(a,b,w[0],w[1]):
                    nw+=1; print(room,'WALL',h,e.dxf.layer,[round(v) for v in loc(a,O)],[round(v) for v in loc(b,O)],w[2]); break
            for oa,ob,oL,oh in others:
                if inter(a,b,oa,ob): no.append((h,e.dxf.layer,oh,oL))
    print(room,'new segments crossing walls:',nw)
    from collections import Counter
    print(room,'crossings with existing MEP lines:',len(no),Counter((x[1],x[3]) for x in no).most_common())
print('--- detail 管道1 x 管道1')
for room,hs in log['added'].items():
    for h in hs:
        e=db[h]
        if e.dxf.layer!='管道1' or e.dxftype()!='LINE': continue
        for oa,ob,oL,oh in others:
            if oL=='管道1' and inter(e.dxf.start,e.dxf.end,oa,ob):
                print(room,h,[round(v,1) for v in loc(e.dxf.start,O)],[round(v,1) for v in loc(e.dxf.end,O)],oh,[round(v,1) for v in loc(oa,O)],[round(v,1) for v in loc(ob,O)])
