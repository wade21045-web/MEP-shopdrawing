import ezdxf,sys,numpy as np,matplotlib,pickle,collections
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from ezdxf import path as P
from lib import walk
f=sys.argv[1]; T=np.array(list(map(float,sys.argv[2].split(','))))
views=[tuple(map(float,v.split(','))) for v in sys.argv[3:]]
d=ezdxf.readfile(f)
segs=collections.defaultdict(list)
for e,M,ef,ch in walk(d,d.modelspace()):
    if ch and ch[0] in ('0905建筑','0905jianzhu'): continue
    try: v=np.array([(q.x,q.y) for q in P.make_path(e).transform(M).flattening(10)])+T
    except Exception: continue
    if len(v)<2: continue
    if not any(abs(v[:,0].mean()-x)<w*1.5 and abs(v[:,1].mean()-y)<w*1.5 for x,y,w in views): continue
    segs[ef].append(v)
pickle.dump(dict(segs),open('dz_'+sys.argv[2]+'.pkl','wb'))
for n,(x,y,w) in enumerate(views):
    fig,ax=plt.subplots(figsize=(12,12)); cnt=collections.Counter()
    for L,vs in segs.items():
        sel=[v for v in vs if abs(v[:,0].mean()-x)<w and abs(v[:,1].mean()-y)<w]
        if not sel: continue
        cnt[L]+=len(sel)
        c='red' if ('暖通' in L or '风口' in L or '末端-天花' in L) else ('blue' if '天花' in L else '0.75')
        ax.add_collection(LineCollection(sel,colors=c,linewidths=0.6))
    ax.set_xlim(x-w,x+w); ax.set_ylim(y-w,y+w); ax.set_aspect('equal'); fig.savefig(f'dz{n}.png',dpi=80); plt.close(fig)
    print(n,[k for k in cnt.most_common(25)])
