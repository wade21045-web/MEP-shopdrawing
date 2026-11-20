import ezdxf,sys,pickle,re,numpy as np,collections
from lib import walk,txt
f,tag,roots=sys.argv[1],sys.argv[2],sys.argv[3].split(',')
d=ezdxf.readfile(f); m=d.modelspace()
WL=re.compile(r'^(AR-WALL|A-WALL|AR-WALL-CURT|墙体完成面|COLU|S-COLU|BEAM)',re.I)
R={}
for e0 in m.query('INSERT'):
    if e0.dxf.name not in roots: continue
    G=[];P=[];LC=collections.Counter()
    for e,M,ef,ch in walk(d,[e0]):
        t=e.dxftype()
        if t in('TEXT','MTEXT'):
            s=txt(e).strip()
            if ('DOTE' in ef.upper() or 'AXIS' in ef.upper() or '轴' in ef) and re.fullmatch(r'[0-9A-Z/\-]{1,5}',s):
                p=M.transform(e.dxf.insert); G.append((s,p.x,p.y,ef)); LC[ef]+=1
        elif WL.search(ef) and t in('LINE','LWPOLYLINE'):
            if t=='LINE': seg=[(e.dxf.start,e.dxf.end)]
            else:
                pts=[(x,y,0) for x,y in e.get_points('xy')]; seg=list(zip(pts[:-1],pts[1:]))
            for a,b in seg:
                a=np.array(tuple(M.transform(a))[:2]); b=np.array(tuple(M.transform(b))[:2]); L=np.hypot(*(b-a)); n=max(1,int(L//150))
                for k in range(n+1): P.append(a+(b-a)*k/n)
    R[e0.dxf.name]=dict(G=G,P=np.array(P),ins=tuple(e0.dxf.insert),LC=LC)
    print(tag,e0.dxf.name,len(G),len(P),LC.most_common(5))
pickle.dump(R,open(f'gp_{tag}.pkl','wb'))
