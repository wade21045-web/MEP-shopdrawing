import pickle,numpy as np,sys,json
from scipy.signal import fftconvolve
from scipy.spatial import cKDTree
from scipy import ndimage
B=pickle.load(open('fp_base.pkl','rb'))['A$C66761927']
CELL=250
def raster(P,org,shape):
    ij=np.floor((P-org)/CELL).astype(int); ok=(ij[:,0]>=0)&(ij[:,1]>=0)&(ij[:,0]<shape[0])&(ij[:,1]<shape[1])
    g=np.zeros(shape,np.float32); np.add.at(g,(ij[ok,0],ij[ok,1]),1); g=np.minimum(g,1); return ndimage.binary_dilation(g,iterations=1).astype(np.float32)
bo=B.min(0)-20000; bs=(np.ceil((B.max(0)+20000-bo)/CELL)).astype(int)
GB=raster(B,bo,tuple(bs)); TB=cKDTree(B)
def rot(t): c,s=np.cos(t),np.sin(t); return np.array([[c,-s],[s,c]])
def search(A,angles):
    best=[]
    for a in angles:
        R=rot(np.radians(a)); Q=A@R.T; qo=Q.min(0); qs=(np.ceil((Q.max(0)-qo)/CELL)+1).astype(int)
        GQ=raster(Q,qo,tuple(qs))
        C=fftconvolve(GB,GQ[::-1,::-1],mode='full')
        k=np.unravel_index(np.argmax(C),C.shape); sc=C[k]/GQ.sum()
        off=(np.array(k)-(np.array(GQ.shape)-1))*CELL+bo-qo
        best.append((sc,a,off))
    best.sort(key=lambda x:-x[0]); return best
def icp(A,a,t,it=30):
    R=rot(np.radians(a))
    for r in [2000,500,100,30,10]:
        for _ in range(8):
            Q=A@R.T+t; d,j=TB.query(Q); ok=d<r
            if ok.sum()<50: break
            X=A[ok]; Y=B[j[ok]]; cx,cy=X.mean(0),Y.mean(0); H=(X-cx).T@(Y-cy); U,S,Vt=np.linalg.svd(H); R=Vt.T@U.T
            if np.linalg.det(R)<0: Vt[-1]*=-1; R=Vt.T@U.T
            t=cy-R@cx
    Q=A@R.T+t; d,_=TB.query(Q)
    return R,t,{f'<={k}':float(np.mean(d<=k)) for k in (2,10,50,200)}
key=sys.argv[1]; fr=sys.argv[2]
A=pickle.load(open(f'fp_{key}.pkl','rb'))[fr]
idx=np.random.default_rng(0).choice(len(A),min(30000,len(A)),replace=False); A=A[idx]
coarse=search(A,np.arange(0,360,1.0))
print('coarse top',[(round(s,3),a) for s,a,o in coarse[:5]])
res=[]
for s,a,o in coarse[:3]:
    fine=search(A,np.arange(a-1,a+1.01,0.1))[0]
    R,t,q=icp(A,fine[1],fine[2])
    ang=np.degrees(np.arctan2(R[1,0],R[0,0]))
    res.append(dict(score=float(fine[0]),angle=float(ang),t=t.tolist(),q=q)); print(res[-1])
best=max(res,key=lambda r:r['q']['<=10'])
json.dump(best,open(f'reg_{key}_{fr}.json','w'),indent=1); print('BEST',best)
