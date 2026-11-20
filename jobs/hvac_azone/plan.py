import ezdxf,pickle,matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from common import *
d=ezdxf.readfile('out/input.dxf')
arch=pickle.load(open('arch.pkl','rb')); res=pickle.load(open('region.pkl','rb'))
eq=[r[0] for r in res if r[2]=='EQ-风机盘管' and loc(((r[6][0]+r[7][0])/2,(r[6][1]+r[7][1])/2),OF)[1]<-1500]
print('flour eq',len(eq))
xs=[];ys=[]
for h in eq:
    e=d.entitydb[h]
    for p in (e.dxf.start,e.dxf.end):
        q=loc(p,OF); xs.append(q[0]); ys.append(q[1])
print('FCU local extents',min(xs),max(xs),min(ys),max(ys))
pickle.dump(eq,open('eq_flour.pkl','wb'))
fig,axs=plt.subplots(1,3,figsize=(24,10))
for ax,(name,o) in zip(axs,[('FLOUR',OF),('STOR',ROOMS['STOR']['O']),('OFF',ROOMS['OFF']['O'])]):
    for a,b,L in arch:
        if not(L.startswith('AR-WALL') or L=='墙体完成面' or L=='0'): continue
        qa,qb=loc(a,o),loc(b,o)
        if -3000<qa[0]<3500 and -4500<qa[1]<3500:
            ax.plot([qa[0],qb[0]],[qa[1],qb[1]],color='k' if L!='0' else '0.8',lw=0.5)
    for r in res:
        if r[2].startswith(('M_AX','新底图','C-','TH_')): continue
        e=d.entitydb[r[0]]
        if e.dxftype()!='LINE': continue
        qa,qb=loc(e.dxf.start,o),loc(e.dxf.end,o)
        if -3000<qa[0]<3500 and -4500<qa[1]<3500:
            col='m' if r[2].startswith('核对') else ('b' if 'DUCT' in r[2] else ('r' if r[2]=='管道2' else ('g' if r[2]=='管道1' else 'c')))
            ax.plot([qa[0],qb[0]],[qa[1],qb[1]],color=col,lw=0.6)
    if name!='FLOUR':
        for h in eq+SUPPLY:
            e=d.entitydb[h]
            if e.dxftype()!='LINE': continue
            qa,qb=loc(e.dxf.start,OF),loc(e.dxf.end,OF)
            ax.plot([qa[0]+DX,qb[0]+DX],[qa[1],qb[1]],color='orange',lw=0.8)
    ax.set_xlim(-3000,3500);ax.set_ylim(-4500,3500);ax.set_aspect('equal');ax.set_title(name);ax.grid(True,lw=0.2)
fig.savefig('plan.png',dpi=80)
