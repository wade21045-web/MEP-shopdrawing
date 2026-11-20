import pickle,numpy as np,collections
from scipy.spatial import cKDTree
def cen(tag,lays=None,reg=None):
    out=pickle.load(open(f'cols_{tag}.pkl','rb')); r=[]
    for ef,k,lo,hi in out:
        s=hi-lo
        if lays and not any(l==ef for l in lays): continue
        if 250<s[0]<1600 and 250<s[1]<1600:
            c=(lo+hi)/2
            if reg is None or (reg[0]<c[0]<reg[1] and reg[2]<c[1]<reg[3]): r.append(c)
    r=np.array(r)
    # dedupe
    t=cKDTree(r); keep=[]; seen=set()
    for i in range(len(r)):
        if i in seen: continue
        for j in t.query_ball_point(r[i],50): seen.add(j)
        keep.append(r[i])
    return np.array(keep)
A=cen('acd',['COLU','COLU-LOWER','S-COLU-HATCH','S-COLU'],(-200000,200000,200000,400000))
D=cen('dec',['S-COLU'],(-420000,-280000,-40000,40000))
print(len(A),len(D))
diff=(A[:,None,:]-D[None,:,:]).reshape(-1,2)
q=np.round(diff/100).astype(int); c=collections.Counter(map(tuple,q))
for k,v in c.most_common(5): print(np.array(k)*100,v)
best=np.array(c.most_common(1)[0][0])*100.
# refine
tA=cKDTree(A)
for it in range(3):
    dd,j=tA.query(D+best); ok=dd<300
    best=best+np.median((A[j[ok]]-(D[ok]+best)),axis=0); print(it,ok.sum(),best,np.percentile(dd[ok],[50,90]))
dd,j=tA.query(D+best); print('residual',np.round(np.sort(dd)[:len(D)],1)[-30:])
pickle.dump(best,open('off_dec.pkl','wb'))
