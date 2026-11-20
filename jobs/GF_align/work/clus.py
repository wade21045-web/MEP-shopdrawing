import pickle,numpy as np
from scipy.spatial import cKDTree
O=pickle.load(open('loose.pkl','rb'))
C={}
for k,items in O.items():
    n=len(items); par=list(range(n))
    def f(i):
        while par[i]!=i: par[i]=par[par[i]]; i=par[i]
        return i
    allp=[];own=[]
    for i,it in enumerate(items):
        for p in it['pts']: allp.append(p); own.append(i)
    if not n: continue
    tr=cKDTree(allp)
    for a,b in tr.query_pairs(60):
        par[f(own[a])]=f(own[b])
    g={}
    for i in range(n): g.setdefault(f(i),[]).append(i)
    cl=[]
    for v in g.values():
        P=np.vstack([items[i]['pts'] for i in v]); lo,hi=P.min(0),P.max(0)
        cl.append(dict(idx=v,lo=lo,hi=hi,c=(lo+hi)/2,types=sorted(set(items[i]['t'] for i in v))))
    C[k]=cl
    for c in sorted(cl,key=lambda c:(c['c'][0])): print(k,len(c['idx']),np.round(c['c']),np.round(c['hi']-c['lo']),c['types'])
pickle.dump(C,open('clus.pkl','wb'))
