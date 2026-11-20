import ezdxf,json
from ezdxf.math import Vec3
A=ezdxf.readfile('/workspace/hvac_shop/out/input.dxf'); B=ezdxf.readfile('out_after.dxf')
log=json.load(open('build_log.json')); DX=log['dx']
mv=set(log['moved']); st=set(log['stretched'])
def r(v):
    if isinstance(v,(Vec3,tuple)) and len(v) in(2,3): return tuple(round(float(x),4) for x in v)
    if isinstance(v,float): return round(v,6)
    return v
def fp(e):
    a={}
    for k,v in e.dxf.all_existing_dxf_attribs().items():
        if k in('handle','owner'): continue
        try: dflt=e.DXFATTRIBS.get(k).default
        except Exception: dflt=None
        if dflt is not None and r(v)==r(dflt if not isinstance(dflt,tuple) else Vec3(dflt)): continue
        if k=='angle' and v==0: continue
        a[k]=r(v)
    t=e.dxftype(); g=None
    if t=='LWPOLYLINE': g=[tuple(round(x,4) for x in p) for p in e.get_points('xyseb')]
    elif t=='SPLINE': g=[r(Vec3(p)) for p in e.control_points]+[r(Vec3(p)) for p in e.fit_points]
    elif t=='INSERT': g=[fp(x) for x in e.attribs]
    elif t=='HATCH': g=len(e.paths)
    return (t,sorted(a.items(),key=lambda kv:kv[0]),g)
bm={e.dxf.handle:e for e in B.modelspace()}
res={'before':0,'unchanged_ok':0,'moved_ok':0,'stretched_ok':0,'bad':[],'missing':[],'new':[]}
for e in A.modelspace():
    h=e.dxf.handle; res['before']+=1
    if h not in bm: res['missing'].append(h); continue
    f=bm[h]
    if h in mv:
        c=e.copy(); c.translate(-DX,0,0)
        ok=fp(c)==fp(f); res['moved_ok']+=ok
    elif h in st:
        ok=e.dxftype()=='LINE' and f.dxftype()=='LINE'
        if ok:
            for p,q in ((e.dxf.start,f.dxf.start),(e.dxf.end,f.dxf.end)):
                d=q-p
                ok&= (abs(d.y)<1e-6 and abs(d.z)<1e-6 and (abs(d.x)<1e-6 or abs(d.x+DX)<1e-6))
            ok&= abs((e.dxf.start-f.dxf.start).x)+abs((e.dxf.end-f.dxf.end).x)>DX-1e-3
        res['stretched_ok']+=ok
    else:
        ok=fp(e)==fp(f); res['unchanged_ok']+=ok
    if not ok: res['bad'].append(h)
ah={e.dxf.handle for e in A.modelspace()}
res['new']=[(h,bm[h].dxftype(),bm[h].dxf.layer) for h in bm if h not in ah]
print({k:(v if not isinstance(v,list) else (len(v),v[:10])) for k,v in res.items()})
json.dump(res,open('verify.json','w'),ensure_ascii=False)
