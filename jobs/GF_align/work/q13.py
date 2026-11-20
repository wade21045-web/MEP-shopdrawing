import pickle,numpy as np,collections,sys
from scipy.spatial import cKDTree
for key in ('01','23','off'):
    out=pickle.load(open(f'prim_{key}.pkl','rb'))
    G=collections.defaultdict(list)
    for it in out:
        nm=it['chain'][-1] if it['chain'] else '-'
        G[(it['top'],nm)].append(it)
    S=collections.defaultdict(list)
    for (top,nm),its in G.items():
        # cluster
        n=len(its); par=list(range(n))
        def f(i):
            while par[i]!=i: par[i]=par[par[i]]; i=par[i]
            return i
        P=np.vstack([i['pts'] for i in its]); own=np.concatenate([[k]*len(i['pts']) for k,i in enumerate(its)])
        for a,b in cKDTree(P).query_pairs(60): par[f(own[a])]=f(own[b])
        cl=collections.defaultdict(list)
        for k in range(n): cl[f(k)].append(its[k])
        for v in cl.values():
            A=np.vstack([i['pts'] for i in v]); sz=A.max(0)-A.min(0)
            S[nm].append((round(max(sz)),round(min(sz)),any(i['curved'] for i in v),np.round((A.max(0)+A.min(0))/2)))
    for nm,v in S.items():
        if nm in('-','A$C35197B1C','zfdgzdfsgv','A$C0e6695ef','A$C0e912e2c','A$C29fd46cf','A$C4283960c','A$C513c4c30','A$C9b0beead','A$C918e9cae') or nm.startswith('*U41'):
            big=[x for x in v if x[0]>=250]
            print(key,nm,len(v),'big',len(big),[x[:3] for x in big][:12], [tuple(x[3]) for x in big][:4])
