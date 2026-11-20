import pickle,math
res=pickle.load(open('region.pkl','rb'))
O={'FLOUR':(-102931.3,-45922.5),'STOR':(-106877.7,-49347.1),'OFF':(-109523.6,-51626.7)}
a=math.radians(-40.8688)
def loc(p,o):
    x,y=p[0]-o[0],p[1]-o[1]; return (x*math.cos(a)-y*math.sin(a), x*math.sin(a)+y*math.cos(a))
skip=('M_AX_CV','新底图','核对','TH_DIM','C-天花','DIM_MODI')
def win(o):
    out=[]
    for r in res:
        if r[2].startswith(skip): continue
        c=((r[6][0]+r[7][0])/2,(r[6][1]+r[7][1])/2); l=loc(c,o)
        if -1800<l[0]<2300 and -3800<l[1]<2600: out.append((r,l))
    return out
import sys
A,B=sys.argv[1],sys.argv[2]
wa,wb=win(O[A]),win(O[B])
def match(x,ws):
    r,l=x
    for r2,l2 in ws:
        if r2[1]==r[1] and r2[2]==r[2] and r2[3]==r[3] and abs(r2[4]-r[4])<6 and abs(r2[5]-r[5])<6 and abs(l2[0]-l[0])<8 and abs(l2[1]-l[1])<8: return True
    return False
from collections import Counter
ua=[x for x in wa if not match(x,wb)]; ub=[x for x in wb if not match(x,wa)]
print(A,'total',len(wa),'unique',len(ua)); print(Counter(x[0][2] for x in ua))
print(B,'total',len(wb),'unique',len(ub)); print(Counter(x[0][2] for x in ub))
pickle.dump((ua,ub),open(f'u_{A}_{B}.pkl','wb'))
