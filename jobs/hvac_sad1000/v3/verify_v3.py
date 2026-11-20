import ezdxf,json,sys
from ezdxf.math import Vec3
src=open('/workspace/hvac_sad1000/verify.py').read(); exec(src[src.index('def r('):src.index('bm={')])
A=ezdxf.readfile('v2_shop.dxf'); B=ezdxf.readfile(sys.argv[1]); L=json.load(open('v3_log.json'))
bm={e.dxf.handle:e for e in B.modelspace()}; dele=set(L['deleted']); mod=L['modified']
res={'base':0,'unchanged':0,'deleted_ok':0,'modified':0,'bad':[],'missing':[]}
for e in A.modelspace():
    h=e.dxf.handle; res['base']+=1
    if h in dele: res['deleted_ok']+= h not in bm; continue
    if h not in bm: res['missing'].append(h); continue
    if h in mod: res['modified']+=1; continue
    if fp(e)==fp(bm[h]): res['unchanged']+=1
    else: res['bad'].append(h)
ah={e.dxf.handle for e in A.modelspace()}
res['new']=[(h,bm[h].dxftype(),bm[h].dxf.layer) for h in bm if h not in ah]; res['n']=len(bm)
print(json.dumps({k:(v if not isinstance(v,list) else [len(v)]+v[:6]) for k,v in res.items()},ensure_ascii=False))
