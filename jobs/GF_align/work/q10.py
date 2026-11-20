import ezdxf,sys,collections,numpy as np,re
from ezdxf import path as P
from lib import walk
f=sys.argv[1]; T=np.array(list(map(float,sys.argv[2].split(',')))); skip=set(sys.argv[3].split('|')) if len(sys.argv)>3 else set()
d=ezdxf.readfile(f)
L=re.compile(r'C-暖通设备|风口')
c=collections.defaultdict(list)
for e,M,ef,ch in walk(d,d.modelspace()):
    if ch and ch[0] in skip: continue
    if not L.search(ef) or not ch: continue
    try: v=np.array([(q.x,q.y) for q in P.make_path(e).transform(M).flattening(10)])+T
    except Exception: continue
    if len(v)<1: continue
    c[(ch[0],ch[-1],ef)].append(v.mean(0))
for k,v in sorted(c.items(),key=lambda x:-len(x[1]))[:40]:
    a=np.array(v); print(len(v),k,np.round(a.min(0)),np.round(a.max(0)))
