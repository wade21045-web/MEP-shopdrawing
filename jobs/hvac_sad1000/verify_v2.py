import ezdxf,json
exec(open('verify.py').read().split("A=ezdxf")[0])
from ezdxf.math import Vec3
src=open('verify.py').read(); fpsrc=src[src.index('def r('):src.index('bm={')]
exec(fpsrc)
A=ezdxf.readfile('out_after.dxf'); B=ezdxf.readfile(__import__('sys').argv[1])
L=json.load(open('build_v2_log.json'))
bm={e.dxf.handle:e for e in B.modelspace()}
res={'v1':0,'unchanged':0,'moved_ok':0,'stretched_ok':0,'deleted_ok':0,'modified':0,'bad':[],'missing':[],'new':[]}
dele=set(L['deleted']); mod=L['modified']; mv=L['moved']; st=L['stretched']
for e in A.modelspace():
    h=e.dxf.handle; res['v1']+=1
    if h in dele: res['deleted_ok']+= h not in bm; continue
    if h not in bm: res['missing'].append(h); continue
    f=bm[h]
    if h in mod or h in L['compound']: res['modified']+=1; continue
    if h in mv:
        c=e.copy(); c.translate(mv[h][0],mv[h][1],0); ok=fp(c)==fp(f); res['moved_ok']+=ok
    elif h in st:
        DX,DY=st[h][0],st[h][1]; ok=True; n=0
        for p,q in ((e.dxf.start,f.dxf.start),(e.dxf.end,f.dxf.end)):
            dd=q-p
            if dd.magnitude<1e-6: continue
            n+=1; ok&=abs(dd.x-DX)<1e-6 and abs(dd.y-DY)<1e-6
        ok&= n==1; res['stretched_ok']+=ok
    else: ok=fp(e)==fp(f); res['unchanged']+=ok
    if not ok: res['bad'].append(h)
ah={e.dxf.handle for e in A.modelspace()}
res['new']=[(h,bm[h].dxftype(),bm[h].dxf.layer) for h in bm if h not in ah]
res['n_after']=len(bm)
print(json.dumps({k:(v if not isinstance(v,list) else [len(v)]+v[:8]) for k,v in res.items()},ensure_ascii=False))
