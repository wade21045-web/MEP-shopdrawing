import pickle,numpy as np,collections
S=pickle.load(open('flat_d2.pkl','rb'))
def axes(top,lay):
    X=[];Y=[]
    for e,t,v in S:
        if t==top and e==lay and len(v)==2:
            d=v[1]-v[0]
            if abs(d[0])<1 and abs(d[1])>3000: X.append(round(float(v[0][0]),1))
            if abs(d[1])<1 and abs(d[0])>3000: Y.append(round(float(v[0][1]),1))
    return np.unique(X),np.unique(Y)
ax,ay=axes('A$C66761927','AR-GENR-DOTE'); sx,sy=axes('A$C40F3171B','COLU&WALL-lower$0$AXIS')
print('arch X',len(ax),np.diff(ax)[:30]); print('arch Y',len(ay),np.diff(ay))
print('str X',len(sx),np.diff(sx)[:40]); print('str Y',len(sy),np.diff(sy))
def best(a,s):
    c=collections.Counter()
    for p in a:
        for q in s: c[round(p-q,0)]+=1
    return c.most_common(5)
print('dx',best(ax,sx)); print('dy',best(ay,sy))
mx=[(p,q) for p in ax for q in sx if abs(p-q-271402)<3]; my=[(p,q) for p in ay for q in sy if abs(p-q+127532)<3]
tx=np.mean([p-q for p,q in mx]); ty=np.mean([p-q for p,q in my]); print('t',tx,ty,len(mx),len(my),max(abs(p-q-tx) for p,q in mx),max(abs(p-q-ty) for p,q in my))
from scipy.spatial import cKDTree
AP=np.vstack([v for e,t,v in S if t=='A$C66761927' and e.startswith(('AR-WALL','A-WALL','墙体','CURTWALL','ST '))])
SC=[v for e,t,v in S if t=='A$C40F3171B' and e in('COLU','COLU-LOWER')]
T=cKDTree(AP); hit=0
for v in SC:
    dd,_=T.query(v+[tx,ty]); hit+= (np.median(dd)<=30)
print('columns with arch outline coincident',hit,len(SC))
pickle.dump(dict(t=np.array([tx,ty]),nx=len(mx),ny=len(my)),open('reg_struct.pkl','wb'))
