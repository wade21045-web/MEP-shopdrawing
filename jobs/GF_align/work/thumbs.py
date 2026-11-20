import ezdxf,sys,matplotlib,numpy as np
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from ezdxf import path
from lib import walk
f,out=sys.argv[1],sys.argv[2]; names=sys.argv[3].split('|')
d=ezdxf.readfile(f)
n=len(names); cols=6; rows=(n+cols-1)//cols
fig,axs=plt.subplots(rows,cols,figsize=(cols*3,rows*3.3))
for ax,nm in zip(np.array(axs).ravel(),names):
    b=d.blocks.get(nm)
    for e,M,ef,ch in walk(d,b):
        try: p=path.make_path(e).transform(M); v=np.array([(q.x,q.y) for q in p.flattening(5)])
        except Exception: continue
        if len(v)>1: ax.plot(v[:,0],v[:,1],lw=0.6,color='k')
    ax.set_aspect('equal'); ax.set_title(nm[:22],fontsize=8,family='Noto Sans CJK SC'); ax.tick_params(labelsize=5)
for ax in np.array(axs).ravel()[n:]: ax.axis('off')
fig.tight_layout(); fig.savefig(out,dpi=110)
