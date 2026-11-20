import ezdxf,collections,json,sys
from sigs import esig
OFF=(28961.42114549,285185.2827819)
def norm(k):
    # block names may be renamed by Importer (suffix digits) -> drop name for INSERT
    return k[:2]+k[3:] if k[0]=='INSERT' else k
def coll(f,off=(0,0)):
    d=ezdxf.readfile(f); c=collections.Counter()
    for e in d.modelspace(): c[norm(esig(e,off))]+=1
    return c,d
A,_=coll('dxf/F02-MEP-ACD.dxf'); print('A',sum(A.values()),flush=True)
B,_=coll('dxf/F02-MEP-B_hotel.dxf',OFF); print('B',sum(B.values()),flush=True)
O,od=coll(sys.argv[1]); print('O',sum(O.values()),flush=True)
missA=A-O; print('ACD entities missing/changed in output:',sum(missA.values()),collections.Counter(k[:2] for k in missA).most_common(10))
rest=O-A
missB=B-rest
print('B entities not found in output (expected = dedup 4547 identical + 26 proxy):',sum(missB.values()),collections.Counter(k[:2] for k in missB).most_common(10))
extra=rest-B; print('output entities not from ACD or B:',sum(extra.values()),collections.Counter(k[:2] for k in extra).most_common(10))
L=collections.Counter(k[1] for k in missB)
json.dump(dict(nA=sum(A.values()),nB=sum(B.values()),nO=sum(O.values()),missA=sum(missA.values()),missB=sum(missB.values()),missB_types=collections.Counter(k[0] for k in missB),extra=sum(extra.values()),extra_layers=collections.Counter(k[1] for k in extra)),open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
