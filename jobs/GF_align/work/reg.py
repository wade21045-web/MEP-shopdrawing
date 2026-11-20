import pickle,numpy as np,collections,json
from scipy.spatial import cKDTree
B=pickle.load(open('g_base.pkl','rb')); PB=np.unique(np.round(pickle.load(open('p_base.pkl','rb')),1),axis=0); TB=cKDTree(PB)
def fit(A,Bp,allow_rot=True):
    A=np.array(A);Bp=np.array(Bp); ca,cb=A.mean(0),Bp.mean(0)
    H=(A-ca).T@(Bp-cb); U,S,Vt=np.linalg.svd(H); R=Vt.T@U.T
    if np.linalg.det(R)<0: Vt[-1]*=-1; R=Vt.T@U.T
    s=1.0
    if not allow_rot: R=np.eye(2)
    t=cb-(R@ca)
    return R,t
def geo(P,R,t,n=20000):
    idx=np.random.default_rng(0).choice(len(P),min(n,len(P)),replace=False); Q=(R@P[idx].T).T+t
    dd,_=TB.query(Q); return {f'<={k}mm':float(np.mean(dd<=k)) for k in (1,5,20)}
res={}
for tag in ['off','01']:
    G=pickle.load(open(f'g_{tag}.pkl','rb'))
    # initial translation by voting label diffs
    bb=collections.defaultdict(list)
    for s,x,y,*_ in B: bb[s].append((x,y))
    diffs=[ (round(bx-x,-1),round(by-y,-1)) for s,x,y,*_ in G for bx,by in bb[s]]
    t0=np.array(collections.Counter(diffs).most_common(1)[0][0])
    A=[];Bp=[];labs=[]
    for s,x,y,*_ in G:
        c=[np.hypot(bx-(x+t0[0]),by-(y+t0[1])) for bx,by in bb[s]]
        if c and min(c)<50: k=int(np.argmin(c)); A.append((x,y)); Bp.append(bb[s][k]); labs.append(s)
    R,t=fit(A,Bp); r=np.hypot(*((R@np.array(A).T).T+t-np.array(Bp)).T)
    ang=np.degrees(np.arctan2(R[1,0],R[0,0]))
    P=pickle.load(open(f'p_{tag}.pkl','rb'))
    R0=np.eye(2); 
    res[tag]=dict(t0=t0.tolist(),n=len(A),rot_deg=ang,t=t.tolist(),resid_mean=float(r.mean()),resid_max=float(r.max()),geo_fit=geo(P,R,t),geo_trans=geo(P,R0,t0))
    print(tag,res[tag])
# 23: vote translation via arch points
P=pickle.load(open('p_23.pkl','rb'))
for t0 in [np.array(res['01']['t0']), np.array(res['01']['t0'])+[1,0]]:
    print('23 hyp',t0,geo(P,np.eye(2),t0))
# refine 23 by voting offsets
idx=np.random.default_rng(1).choice(len(P),3000,replace=False); t0=np.array(res['01']['t0'])
votes=collections.Counter()
for p in P[idx]:
    for j in TB.query_ball_point(p+t0,20): votes[tuple(np.round(PB[j]-p-t0,0))]+=1
print('23 votes',votes.most_common(5))
json.dump(res,open('reg.json','w'),indent=1)
