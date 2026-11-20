import ezdxf,collections,json
A=ezdxf.readfile('r1o/d1.dxf'); B=ezdxf.readfile('r2o/check_p.dxf')
def sig(e):
    t=e.dxftype(); r=lambda v:(round(v[0],1),round(v[1],1))
    try:
        if t=='INSERT': n=e.dxf.name; n=(n[:2]+'#'+str(len(e.doc.blocks.get(n)))) if n.startswith('*') else n; return (t,n,r(e.dxf.insert),round(e.dxf.rotation,2),round(e.dxf.xscale,4))
        if t=='LINE': return (t,)+tuple(sorted([r(e.dxf.start),r(e.dxf.end)]))
        if t in('CIRCLE','ARC'): return (t,r(e.dxf.center),round(e.dxf.radius,1))
        if t=='LWPOLYLINE': p=list(e.get_points('xy')); return (t,len(p),r(p[0]) if p else None)
        if t in('TEXT','MTEXT'): return (t,r(e.dxf.insert),e.plain_text()[:30] if t=='MTEXT' else e.dxf.text[:30])
    except Exception: pass
    return (t,)
BGL={'AR-WALL-PLST 墙面抹灰'}
def coll(d):
    c=collections.defaultdict(collections.Counter)
    for e in d.modelspace(): c[e.dxf.layer][sig(e)]+=1
    return c
ca,cb=coll(A),coll(B)
rows=[];bad=[]
HV=lambda L: L.startswith(('DUCT-','EQ-','管道','VANNE','天花末端点位','M_','Misc-Hvac','hvac','-AATC'))
for L in sorted(ca):
    na=sum(ca[L].values()); nb=sum(cb.get(L,{}).values()) if L in cb else 0
    same= ca[L]==cb.get(L,collections.Counter())
    rows.append((L,na,nb,same,HV(L)))
    if not same and L not in BGL: bad.append((L,na,nb))
removed=[(e.dxftype(),e.dxf.name if e.dxftype()=='INSERT' else '',e.dxf.layer) for e in A.modelspace() if sig(e) not in cb.get(e.dxf.layer,{})]
newL=sorted(set(cb)-set(ca)); print('new layers',[(L,sum(cb[L].values())) for L in newL])
print('layers in d1',len(ca),'identical',sum(r[3] for r in rows),'mismatch(excluding bg)',bad)
print('d1 entities not present in output:',removed[:20],len(removed))
hv=[r for r in rows if r[4]]; print('HVAC-ish layers',len(hv),'all identical',all(r[3] for r in hv),'entities',sum(r[1] for r in hv))
# HVAC block defs
blk=lambda d,n: len(d.blocks.get(n)) if n in d.blocks else None
names={e.dxf.name for e in A.modelspace() if e.dxftype()=='INSERT' and HV(e.dxf.layer)}
diffb=[(n,blk(A,n),blk(B,n)) for n in names if not n.startswith('*') and blk(A,n)!=blk(B,n)]
print('HVAC insert block defs',len(names),'differ',diffb[:10])
json.dump(dict(rows=rows,newL=[(L,sum(cb[L].values())) for L in newL],removed=removed),open('verify.json','w'),ensure_ascii=False)
