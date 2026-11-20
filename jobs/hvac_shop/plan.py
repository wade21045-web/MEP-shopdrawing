import ezdxf,pickle,matplotlib,sys
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from common import *
arch=pickle.load(open('arch.pkl','rb'))
O=DIFF['D043']
fig,ax=plt.subplots(figsize=(26,12))
for a,b,L in arch:
    qa,qb=loc(a,O),loc(b,O)
    if -5500<qa[0]<9500 and -4000<qa[1]<3500:
        col='k' if L.startswith('AR-WALL') or L=='墙体完成面' else '0.85'
        ax.plot([qa[0],qb[0]],[qa[1],qb[1]],color=col,lw=0.5 if col=='k' else 0.3)
src=sys.argv[1] if len(sys.argv)>1 else 'out/input.dxf'
d=ezdxf.readfile(src); m=d.modelspace()
from ezdxf import bbox
for e in m.query('LINE LWPOLYLINE INSERT'):
    L=e.dxf.layer
    if L.startswith(('M_','新底图','C-','TH_','7-MCF')): continue
    try:
        if e.dxftype()=='LINE': pts=[e.dxf.start,e.dxf.end]
        elif e.dxftype()=='LWPOLYLINE': pts=list(e.get_points('xy'))
        else:
            b=bbox.extents([e],fast=True); 
            if not b.has_data: continue
            pts=[b.extmin,(b.extmax[0],b.extmin[1]),b.extmax,(b.extmin[0],b.extmax[1]),b.extmin]
    except Exception: continue
    q=[loc(p,O) for p in pts]
    if not any(-5500<x<9500 and -4000<y<3500 for x,y in q): continue
    col='m' if L.startswith('核对') else ('b' if 'DUCT' in L else ('r' if L=='管道2' else ('g' if L=='管道1' else ('c' if L=='管道5' else ('orange' if L.startswith('EQ') else ('y' if L.startswith('修改') else '0.5'))))))
    ax.plot([p[0] for p in q],[p[1] for p in q],color=col,lw=0.6)
ax.set_xlim(-5500,9500);ax.set_ylim(-4000,3500);ax.set_aspect('equal');ax.grid(True,lw=0.2)
ax.set_xticks(range(-5500,9501,500)); ax.tick_params(labelsize=6)
fig.savefig(sys.argv[2] if len(sys.argv)>2 else 'plan.png',dpi=70,bbox_inches='tight')
