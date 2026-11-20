import ezdxf,collections,json,sys
from sigs import esig
def norm(k): return k[:2]+k[3:] if k[0]=='INSERT' else k
def coll(f):
    d=ezdxf.readfile(f); c=collections.Counter(); per=collections.Counter()
    for e in d.modelspace(): c[norm(esig(e))]+=1
    return c
M=coll('mg_back/2F_机电合并.dxf'); print('M',sum(M.values()),flush=True)
O=coll(sys.argv[1]); print('O',sum(O.values()),flush=True)
miss=M-O; extra=O-M
HV=lambda L: L.startswith(('DUCT-','EQ-','管道','VANNE','M_','Misc-Hvac','hvac','PIPE','DIM-风机盘管','M-HVAC'))
LM=collections.Counter(k[1] for k in M.elements())
rows=[[L,n,n-sum(v for k,v in miss.items() if k[1]==L),HV(L)] for L,n in sorted(LM.items())]
print('merged entities missing/changed in check output:',sum(miss.values()),collections.Counter(k[:2] for k in miss).most_common(5))
print('new entities:',sum(extra.values()),collections.Counter(k[1] for k in extra))
json.dump(dict(nM=sum(M.values()),nO=sum(O.values()),miss=sum(miss.values()),newL=collections.Counter(k[1] for k in extra),rows=rows,hv=sum(n for L,n,_,h in rows if h),hvL=sum(1 for r in rows if r[3])),open('vcheck.json','w'),ensure_ascii=False,indent=1)
