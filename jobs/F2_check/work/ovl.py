import ezdxf,collections,numpy as np,pickle
OFF=np.array([28961.42114549,285185.2827819])
def sigs(f,off):
    d=ezdxf.readfile(f); m=d.modelspace(); S=collections.defaultdict(set); P=collections.defaultdict(list)
    for e in m:
        t=e.dxftype()
        try:
            if t=='LINE': k=(t,e.dxf.layer,round(e.dxf.start.x+off[0]),round(e.dxf.start.y+off[1]),round(e.dxf.end.x+off[0]),round(e.dxf.end.y+off[1]))
            elif t=='INSERT': k=(t,e.dxf.layer,e.dxf.name,round(e.dxf.insert.x+off[0]),round(e.dxf.insert.y+off[1]))
            elif t in('TEXT',): k=(t,e.dxf.layer,e.dxf.text,round(e.dxf.insert.x+off[0]),round(e.dxf.insert.y+off[1]))
            else: continue
        except Exception: continue
        S[e.dxf.layer].add(k)
        if t=='LINE': P[e.dxf.layer].append(((e.dxf.start.x+e.dxf.end.x)/2+off[0],(e.dxf.start.y+e.dxf.end.y)/2+off[1]))
    return S,P
A,PA=sigs('dxf/F02-MEP-ACD.dxf',(0,0)); B,PB=sigs('dxf/F02-MEP-B_hotel.dxf',OFF)
tot=collections.Counter(); 
for L in sorted(set(B)|set(A), key=lambda L:-len(B.get(L,()))):
    b=B.get(L,set()); a=A.get(L,set()); 
    if len(b)+len(a)<30: continue
    print(f'{L[:40]:40s} A={len(a):6d} B={len(b):6d} common={len(a&b):6d}')
pickle.dump({L:np.array(v) for L,v in PA.items()},open('pa.pkl','wb')); pickle.dump({L:np.array(v) for L,v in PB.items()},open('pb.pkl','wb'))
