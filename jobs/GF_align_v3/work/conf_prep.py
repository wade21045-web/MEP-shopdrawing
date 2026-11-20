import pickle,numpy as np,re,collections
from scipy.spatial import cKDTree
B=pickle.load(open('flat_base.pkl','rb')); D1=pickle.load(open('flat_d1.pkl','rb'))
WL=re.compile(r'^(AR-WALL|A-WALL|墙体完成面|CURTWALL|AR-GLAZ$)')
PLAN=(-140000,25000,-75000,19500)
def inp(v): c=v.mean(0); return PLAN[0]<c[0]<PLAN[1] and PLAN[2]<c[1]<PLAN[3]
def segs(S,top,rx):
    out=[]
    for e,t,v in S:
        if t==top and rx.search(e) and inp(v):
            for a,b in zip(v[:-1],v[1:]):
                if np.hypot(*(b-a))>5: out.append((a,b,e))
    return out
NW=segs(B,'A$C66761927',WL); OW=segs(D1,'A$C76C4695F',WL)
def samp(sg,step=50):
    P=[];own=[]
    for i,(a,b,e) in enumerate(sg):
        n=max(1,int(np.hypot(*(b-a))//step))
        for k in range(n+1): P.append(a+(b-a)*k/n); own.append(i)
    return np.array(P),np.array(own)
NP,NO=samp(NW); OP,OO=samp(OW)
dd,_=cKDTree(OP).query(NP); newpt=dd>30
frac=np.bincount(NO,weights=newpt,minlength=len(NW))/np.maximum(1,np.bincount(NO,minlength=len(NW)))
newseg=frac>0.5
dd2,_=cKDTree(NP).query(OP); gone=dd2>30
fr2=np.bincount(OO,weights=gone,minlength=len(OW))/np.maximum(1,np.bincount(OO,minlength=len(OW)))
print('new walls segs',len(NW),'new/changed',newseg.sum(),'old segs',len(OW),'removed',(fr2>0.5).sum())
# columns from struct overlay (plan coords) + beams
COL=[];BEAM=[]
for e,t,v in B:
    if t!='A$C40F3171B0' or not inp(v): continue
    if e in('COLU','COLU-LOWER') and np.hypot(*(v[0]-v[-1]))<5 and len(v)>=4: COL.append((v,e))
    if e in('BEAM','BEAM_SE'):
        for a,b in zip(v[:-1],v[1:]): BEAM.append((a,b,e))
# arch concrete columns (AR-WALL-CONC closed small polys) too
for e,t,v in B:
    if t=='A$C66761927' and e.startswith('AR-WALL-CONC') and inp(v) and np.hypot(*(v[0]-v[-1]))<5 and np.ptp(v,axis=0).max()<1500: COL.append((v,e))
print('columns',len(COL),'beam segs',len(BEAM))
pickle.dump(dict(NW=NW,newseg=newseg,OW=OW,removed=fr2>0.5,COL=COL,BEAM=BEAM),open('bg_conf.pkl','wb'))
# cluster new walls for summary
C=np.array([(a+b)/2 for (a,b,e),f in zip(NW,newseg) if f])
if len(C):
    T=cKDTree(C); par=list(range(len(C)))
    def f(i):
        while par[i]!=i: par[i]=par[par[i]]; i=par[i]
        return i
    for i,j in T.query_pairs(1500): par[f(i)]=f(j)
    g=collections.Counter(f(i) for i in range(len(C))); print('new-wall clusters',len(g),sorted(g.values())[-10:])
