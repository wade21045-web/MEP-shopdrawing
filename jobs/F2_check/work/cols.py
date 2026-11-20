import ezdxf,collections,numpy as np,re,sys,pickle
from ezdxf import path as EP
from lib import walk
f,tag=sys.argv[1],sys.argv[2]
d=ezdxf.readfile(f); m=d.modelspace()
CL=re.compile(r'COLU|柱',re.I)
lc=collections.Counter(); out=[]
for e,M,ef,ch in walk(d,m):
    if not CL.search(ef): continue
    lc[(ef,e.dxftype())]+=1
    if e.dxftype() in('LWPOLYLINE','POLYLINE','HATCH'):
        try:
            p=EP.make_path(e) if e.dxftype()!='HATCH' else None
            if e.dxftype()=='HATCH':
                ps=EP.from_hatch(e)
                for q in ps:
                    v=np.array([(a.x,a.y) for a in q.transform(M).flattening(5)])
                    if len(v)>2: out.append((ef,'H',v.min(0),v.max(0)))
                continue
            v=np.array([(a.x,a.y) for a in p.transform(M).flattening(5)])
            if len(v)>2: out.append((ef,'P',v.min(0),v.max(0)))
        except Exception as ex: pass
print(tag,lc.most_common(20))
pickle.dump(out,open(f'cols_{tag}.pkl','wb'))
sz=np.array([o[3]-o[2] for o in out]); 
ok=[(o[2]+o[3])/2 for o,s in zip(out,sz) if 250<s[0]<1600 and 250<s[1]<1600]
print('polys',len(out),'colsize',len(ok))
if ok: a=np.array(ok); print(a.min(0).round(),a.max(0).round())
