import pickle,numpy as np,collections
from scipy.spatial import cKDTree
S=pickle.load(open('flat_d2.pkl','rb'))
def cents(top,lay):
    out=[]
    for e,t,v in S:
        if t==top and e==lay:
            sz=np.ptp(v,axis=0)
            if sz.max()<2500 and np.hypot(*(v[0]-v[-1]))<5: out.append(v.mean(0)); 
    return np.array(out)
A=cents('A$C66761927','AR-GENR-DOTE-N'); B=cents('A$C40F3171B','COLU&WALL-lower$0$AXIS')
print(len(A),len(B))
votes=collections.Counter()
for b in B:
    for a in A: votes[tuple(np.round((a-b)/50)*50)]+=1
print(votes.most_common(6))
t0=np.array(votes.most_common(1)[0][0])
TA=cKDTree(A); d,j=TA.query(B+t0); ok=d<200
t=(A[j[ok]]-B[ok]).mean(0); r=np.hypot(*((B[ok]+t)-A[j[ok]]).T)
print('bubbles matched',ok.sum(),'t',t,'resid',r.mean(),r.max())
# axis lines/columns check
def pts(top,lays):
    P=[v for e,tp,v in S if tp==top and e in lays]
    return np.vstack(P) if P else np.zeros((0,2))
SA=pts('A$C40F3171B',{'COLU&WALL-lower$0$AXIS'}); AA=pts('A$C66761927',{'AR-GENR-DOTE'})
print('axis pts',len(SA),len(AA))
pickle.dump(dict(t=t,n=int(ok.sum()),res=float(r.max())),open('reg_struct.pkl','wb'))
# column check vs arch concrete
SC=pts('A$C40F3171B',{'COLU','COLU-LOWER'})+t; AC=pts('A$C66761927',{'AR-WALL-CONC-S','A-WALL'})
dd,_=cKDTree(AC).query(SC); print('struct column pts near arch conc <=20mm',np.mean(dd<=20),'<=100',np.mean(dd<=100))
