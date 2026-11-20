import pickle,numpy as np,collections
from scipy.spatial import cKDTree
S=pickle.load(open('flat_d2.pkl','rb'))
def cents(top,lay):
    return np.array([v.mean(0) for e,t,v in S if t==top and e==lay and np.ptp(v,axis=0).max()<2500 and np.hypot(*(v[0]-v[-1]))<5])
A=cents('A$C66761927','AR-GENR-DOTE-N'); B=cents('A$C40F3171B','COLU&WALL-lower$0$AXIS')
votes=collections.Counter()
for b in B:
    for a in A: votes[tuple(np.round((a-b)/25)*25)]+=1
AP=np.vstack([v for e,t,v in S if t=='A$C66761927' and (e.startswith(('AR-WALL','A-WALL','墙体','CURTWALL','AR-WALL-CONC')))])
# densify not needed: use vertices
TA=cKDTree(AP)
SC=np.vstack([v for e,t,v in S if t=='A$C40F3171B' and e in('COLU','COLU-LOWER')])
res=[]
for tv,n in votes.most_common(300):
    t=np.array(tv,float); dd,_=TA.query(SC+t); res.append((np.mean(dd<=30),np.mean(dd<=150),n,tv))
res.sort(reverse=True)
for r in res[:8]: print(r)
