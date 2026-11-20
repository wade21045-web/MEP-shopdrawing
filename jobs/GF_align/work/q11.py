import ezdxf,sys,collections,numpy as np,re
from ezdxf import path as P
from lib import walk
f=sys.argv[1]; T=np.array(list(map(float,sys.argv[2].split(',')))); x0,x1,y0,y1=map(float,sys.argv[3].split(','))
d=ezdxf.readfile(f)
c=collections.Counter()
for e,M,ef,ch in walk(d,d.modelspace()):
    if not re.search('末端-天花|暖通',ef): continue
    try: v=np.array([(q.x,q.y) for q in P.make_path(e).transform(M).flattening(10)])+T
    except Exception: continue
    if len(v) and x0<v[:,0].mean()<x1 and y0<v[:,1].mean()<y1: c[(ef,e.dxftype(),ch)]+=1
for k,n in c.most_common(30): print(n,k)
