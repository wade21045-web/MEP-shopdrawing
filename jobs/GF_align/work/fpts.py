import ezdxf,sys,pickle,re,numpy as np
from lib import walk
f,out=sys.argv[1],sys.argv[2]; frames=sys.argv[3].split('|'); skip=set(sys.argv[4].split('|')) if len(sys.argv)>4 else set()
WL=re.compile(r'^(AR-WALL|A-WALL|CURTWALL|AR-GLAZ|A-GLAZ|AR-DOOR|墙体完成面|AR-FLOR-STRS|A-土建墙线|AR-WALL-CURT)',re.I)
d=ezdxf.readfile(f); R={}
for fr in frames:
    lay=d.modelspace() if fr=='MS' else d.blocks.get(fr)
    P=[];Lc={}
    for e,M,ef,ch in walk(d,lay):
        if fr=='MS' and ch and ch[0] in skip: continue
        if not WL.search(ef): continue
        t=e.dxftype()
        if t=='LINE': seg=[(e.dxf.start,e.dxf.end)]
        elif t=='LWPOLYLINE':
            pts=[(x,y,0) for x,y in e.get_points('xy')]; seg=list(zip(pts[:-1],pts[1:]))
            if e.closed and len(pts)>2: seg.append((pts[-1],pts[0]))
        else: continue
        for a,b in seg:
            a=np.array(tuple(M.transform(a))[:2]); b=np.array(tuple(M.transform(b))[:2]); L=np.hypot(*(b-a))
            n=max(1,int(L//150)); 
            for k in range(n+1): P.append(a+(b-a)*k/n)
        Lc[ef]=Lc.get(ef,0)+1
    R[fr]=np.array(P); print(fr,len(P),sorted(Lc.items(),key=lambda x:-x[1])[:8])
pickle.dump(R,open(out,'wb'))
