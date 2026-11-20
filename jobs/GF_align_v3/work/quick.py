import pickle,sys,numpy as np,matplotlib,json
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
S=pickle.load(open(sys.argv[1],'rb')); x0,x1,y0,y1=map(float,sys.argv[2].split(',')); out=sys.argv[3]
extra=pickle.load(open(sys.argv[4],'rb')) if len(sys.argv)>4 else []
def col(e,t):
    if '风口' in e or '末端' in e: return 'blue' if not e.startswith('综合') else 'orange'
    if e.startswith('DUCT') or e=='hvac-hide': return 'teal'
    if e.startswith('EQ') or '管道' in e or 'PIPE' in e: return 'green'
    if e.startswith('C-'): return 'orange'
    return '0.75'
G={}
for e,t,v in S:
    if v[:,0].max()<x0 or v[:,0].min()>x1 or v[:,1].max()<y0 or v[:,1].min()>y1: continue
    G.setdefault(col(e,t),[]).append(v)
fig=plt.figure(figsize=(18,18*(y1-y0)/(x1-x0)),dpi=110); ax=fig.add_axes([0,0,1,1])
for c in ['0.75','green','teal','orange','blue']:
    if c in G: ax.add_collection(LineCollection(G[c],colors=c,linewidths=0.4 if c=='0.75' else 0.8))
for o in extra:
    ax.add_collection(LineCollection([np.asarray(p) for p in o['pts']],colors='magenta',linewidths=1.2))
    if 'label' in o: ax.text(o['c'][0],o['c'][1],o['label'],color='red',fontsize=8)
ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal'); ax.axis('off'); fig.savefig(out,facecolor='white')
