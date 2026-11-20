import ezdxf,json,collections
exec(open('verify.py').read().split("bm={")[0])
bm={e.dxf.handle:e for e in B.modelspace()}
am={e.dxf.handle:e for e in A.modelspace()}
res=json.load(open('verify.json'))
c=collections.Counter((am[h].dxftype(), h in mv) for h in res['bad']); print(c)
shown=collections.Counter()
for h in res['bad']:
    t=am[h].dxftype()
    if shown[t]>=1: continue
    shown[t]+=1
    e=am[h]; f=bm[h]
    if h in mv: e=e.copy(); e.translate(-DX,0,0)
    a,b=fp(e),fp(f)
    da=dict(a[1]); dbb=dict(b[1])
    print(t,h,'moved' if h in mv else '', {k:(da.get(k),dbb.get(k)) for k in set(da)|set(dbb) if da.get(k)!=dbb.get(k)}, 'geom-eq',a[2]==b[2])
