import ezdxf,pickle,sys,numpy as np,matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from ezdxf import path as P
from lib import walk
d=ezdxf.readfile(sys.argv[1] if len(sys.argv)>1 else '/workspace/GF_hvac/output/GF_暖通+建筑结构底图.dxf'); m=d.modelspace()
segs=[]
for e,M,ef,ch in walk(d,m):
    if not ch or ch[0] not in('A$C5E357C2F','A$C124230B8'): continue
    try: pts=np.array([(v.x,v.y) for v in P.make_path(e).transform(M).flattening(20)])
    except Exception: continue
    if len(pts)<2: continue
    segs.append((ef,pts,ch))
pickle.dump([(a,b,c) for a,b,c in segs],open(sys.argv[2] if len(sys.argv)>2 else 'hvsegs.pkl','wb'))
print(len(segs))
