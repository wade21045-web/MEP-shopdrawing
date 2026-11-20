import pickle,sys,numpy as np,matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
S=pickle.load(open(sys.argv[5] if len(sys.argv)>5 else 'hvsegs.pkl','rb'))
R=pickle.load(open('result.pkl','rb'))
x,y,w=float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3]); out=sys.argv[4]
def colr(L):
    if '风口' in L: return 'blue'
    if '中心线' in L: return 'orange'
    if L.startswith('DUCT'): return 'green'
    if L.startswith('EQ') or 'M-EQ' in L: return 'red'
    if '管道' in L or 'PIPE' in L: return 'purple'
    if '末端' in L: return 'magenta'
    return 'grey'
fig,ax=plt.subplots(figsize=(10,10)); cols={}
for L,p,ch in S:
    if np.all(np.abs(p[:,0]-x)>w) or np.all(np.abs(p[:,1]-y)>w): continue
    cols.setdefault(colr(L),[]).append(p)
for c,v in cols.items(): ax.add_collection(LineCollection(v,colors=c,linewidths=0.6))
for o in R['DEC']:
    if abs(o['x']-x)<w and abs(o['y']-y)<w: ax.plot(o['x'],o['y'],'m*',ms=10)
ax.set_xlim(x-w,x+w); ax.set_ylim(y-w,y+w); ax.set_aspect('equal'); fig.savefig(out,dpi=90)
O=pickle.load(open('loose.pkl','rb'))
for k,its in O.items():
    for it in its:
        p=it['pts']
        if np.any(np.abs(p[:,0]-x)<w) and np.any(np.abs(p[:,1]-y)<w): ax.plot(p[:,0],p[:,1],'c-',lw=0.8)
fig.savefig(out,dpi=90)
