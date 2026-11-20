import pickle,numpy as np,collections
from scipy.spatial import cKDTree
A=pickle.load(open('gp_d1.pkl','rb'))['A$C76C4695F']; B=pickle.load(open('gp_d2.pkl','rb'))['A$C66761927']
def match(GA,GB,t0=None):
    bb=collections.defaultdict(list)
    for s,x,y,*_ in GB: bb[s].append((x,y))
    if t0 is None:
        diffs=[(round(bx-x,-1),round(by-y,-1)) for s,x,y,*_ in GA for bx,by in bb[s]]
        t0=np.array(collections.Counter(diffs).most_common(1)[0][0],float)
    P=[];Q=[];L=[]
    for s,x,y,*_ in GA:
        c=[np.hypot(bx-(x+t0[0]),by-(y+t0[1])) for bx,by in bb[s]]
        if c and min(c)<100: k=int(np.argmin(c)); P.append((x,y)); Q.append(bb[s][k]); L.append(s)
    return t0,np.array(P),np.array(Q),L
def fit(P,Q):
    ca,cb=P.mean(0),Q.mean(0); H=(P-ca).T@(Q-cb); U,S,Vt=np.linalg.svd(H); R=Vt.T@U.T
    if np.linalg.det(R)<0: Vt[-1]*=-1; R=Vt.T@U.T
    return R,cb-R@ca
t0,P,Q,L=match(A['G'],B['G'])
R,t=fit(P,Q); res=np.hypot(*((P@R.T+t)-Q).T)
ang=np.degrees(np.arctan2(R[1,0],R[0,0]))
print('labels d1',len(A['G']),'d2',len(B['G']),'matched',len(P),'t0',t0,'rot',ang,'t',t,'resid mean/max',res.mean(),res.max())
tt=(Q-P).mean(0); rt=np.hypot(*((P+tt)-Q).T); print('pure translation',tt,'resid',rt.mean(),rt.max())
# wall check
TB=cKDTree(B['P']); TA=cKDTree(A['P'])
for name,tr in (('t=0',np.zeros(2)),('t=fit',tt)):
    dd,_=TB.query(A['P']+tr); de,_=TA.query(B['P']-tr)
    print(name,'d1 walls->d2: <=1mm %.3f <=5mm %.3f <=20mm %.3f'%tuple(np.mean(dd<=k) for k in (1,5,20)),' d2->d1: <=1 %.3f <=5 %.3f <=20 %.3f'%tuple(np.mean(de<=k) for k in (1,5,20)))
# vote refine
idx=np.random.default_rng(0).choice(len(A['P']),min(5000,len(A['P'])),replace=False); votes=collections.Counter()
for p in A['P'][idx]:
    for j in TB.query_ball_point(p+tt,30): votes[tuple(np.round(B['P'][j]-p,0))]+=1
print('wall vote',votes.most_common(5))
pickle.dump(dict(t=tt,R=R,tfit=t,n=len(P),res=float(rt.max()),labels=L),open('reg_d1d2.pkl','wb'))
# label diffs
ga=collections.Counter(s for s,*_ in A['G']); gb=collections.Counter(s for s,*_ in B['G'])
print('labels only d1',sorted(set(ga)-set(gb))[:40]); print('labels only d2',sorted(set(gb)-set(ga))[:40])
