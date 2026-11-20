import ezdxf,collections,numpy as np,re
from ezdxf import bbox
from lib import walk
d=ezdxf.readfile('dxf/L2-大平面-升版9.2.dxf'); m=d.modelspace()
c=collections.Counter(); pos=collections.defaultdict(list)
for e,M,ef,ch in walk(d,m):
    if e.dxftype()=='INSERT':
        n=e.dxf.name
        if re.search('风口|散流|diff|grill|格栅|回风|送风',n+ef,re.I) or ef in('综合末端-天花','C-暖通设备'):
            p=M.transform(e.dxf.insert); c[(ef,n,tuple(ch[:1]))]+=1; pos[(ef,n)].append((p.x,p.y))
for k,v in c.most_common(80): print(v,k)
for k,v in pos.items():
    a=np.array(v); print(k,len(a),a.min(0).round(),a.max(0).round())
# layer counts of everything in nested
L=collections.Counter(ef for e,M,ef,ch in walk(d,m))
print(L.most_common(60))
