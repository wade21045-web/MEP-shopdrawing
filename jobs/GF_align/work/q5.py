import ezdxf,collections,math,sys
from lib import walk
d=ezdxf.readfile(sys.argv[1])
T=tuple(map(float,sys.argv[2].split(",")))
c=collections.Counter(); ex={}
for e,M,ef,ch in walk(d,d.modelspace()):
    if ch and ch[0] in('02-03组','0905建筑'): continue
    t=e.dxftype()
    if t in('ARC','LWPOLYLINE','POLYLINE','SPLINE','INSERT','LINE','CIRCLE','HATCH'):
        try:
            if t=='ARC': p=e.dxf.center
            elif t=='LWPOLYLINE': p=list(e.get_points('xy'))[0]+(0,)
            elif t=='LINE': p=e.dxf.start
            elif t=='CIRCLE': p=e.dxf.center
            elif t=='INSERT': p=e.dxf.insert
            elif t=='SPLINE': p=e.control_points[0]
            else: continue
            q=M.transform(p); x,y=q.x+T[0],q.y+T[1]
        except Exception: continue
        if -36000<x<-22000 and -36000<y<-20000:
            k=(ef,t,ch[-1] if ch else '')
            if t=='ARC' or (t=='LWPOLYLINE' and any(b!=0 for b in e.get_points('b'))) or t=='SPLINE':
                k=k+('CURVED',)
            c[k]+=1
for k,n in sorted(c.items(),key=lambda x:-x[1])[:70]: print(n,k)
