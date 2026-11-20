import ezdxf,collections,sys,re
from lib import walk
L=re.compile(r'风口|末端|天花|暖通|顶面|DIFF|AC',re.I)
for f,T,skip in [("dxf/1.GF-02&03大平标新位置-0914.dxf",(36446.00,-20918.06),('02-03组','0905建筑')),("dxf/1.GF-01-0914.dxf",(36446.53,-20917.40),('A$C3087fbf4','0905jianzhu')),("dxf/Office-F00 plan 1017.dxf",(-151883.20,-20917.26),())]:
    d=ezdxf.readfile(f); c=collections.Counter()
    for e,M,ef,ch in walk(d,d.modelspace()):
        if ch and ch[0] in skip: continue
        if not L.search(ef): continue
        t=e.dxftype()
        cur = t in('ARC','SPLINE','ELLIPSE') or (t=='LWPOLYLINE' and any(b!=0 for b in e.get_points('b')))
        if not cur: continue
        try:
            p=M.transform(e.dxf.center if t=='ARC' else (e.control_points[0] if t=='SPLINE' else (e.dxf.center if t=='ELLIPSE' else list(e.get_points('xy'))[0]+(0,))))
        except Exception: continue
        x,y=p.x+T[0],p.y+T[1]
        if -40000<x<-20000 and -40000<y<-18000:
            c[(ef,t,ch[-1] if ch else '')]+=1
    print(f); [print('  ',n,k) for k,n in c.most_common(30)]
