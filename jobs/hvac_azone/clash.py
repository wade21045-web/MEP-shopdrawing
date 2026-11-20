import ezdxf,pickle,json
from common import *
arch=pickle.load(open('arch.pkl','rb'))
walls=[(a,b) for a,b,L in arch if L.startswith('AR-WALL') or L=='墙体完成面']
log=json.load(open('build_log.json'))
d=ezdxf.readfile('out_after.dxf'); db=d.entitydb
def inter(p1,p2,p3,p4):
    def cr(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    d1,d2,d3,d4=cr(p3,p4,p1),cr(p3,p4,p2),cr(p1,p2,p3),cr(p1,p2,p4)
    return (d1*d2<0) and (d3*d4<0)
for room,hs in log['added'].items():
    n=0
    for h in hs:
        e=db[h]
        if e.dxftype()!='LINE': continue
        a,b=e.dxf.start,e.dxf.end
        for w in walls:
            if inter(a,b,w[0],w[1]): n+=1; print(room,h,e.dxf.layer,[round(v) for v in loc(a,ROOMS[room]['O'])],[round(v) for v in loc(b,ROOMS[room]['O'])]); break
    print(room,'lines crossing walls:',n)
