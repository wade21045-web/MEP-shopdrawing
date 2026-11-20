import ezdxf,sys,numpy as np,matplotlib,json
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from ezdxf import path,colors
from ezdxf.math import Matrix44
src,tag,outdir=sys.argv[1],sys.argv[2],sys.argv[3]; views=json.loads(sys.argv[4])
d=ezdxf.readfile(src); m=d.modelspace()
segs={}; texts=[]
CK={'核对-装饰风口(参照)':6,'核对-位置偏差':1,'核对-形式不一致':30,'核对-装饰有暖通无':4,'核对-暖通有装饰无':3,'核对-弧形风口':200,'核对-待确认':2,'核对-引线':1,'核对-新底图冲突':210}
def col(eff):
    if eff in CK: return CK[eff]
    if eff.startswith('调整-新底图冲突'): return 200
    if eff.startswith('新底图-结构'): return 'st'
    if eff.startswith('综合末端') or eff.startswith('C-') or eff in('灯具编号',): return 'ref'
    if eff.startswith('调整前'): return 'old'
    if eff.startswith('调整-待定'): return 30
    if eff.startswith('调整-风口连接软管'): return 3
    if eff.startswith('调整'): return 1
    if eff=='装饰-风口': return 6
    if '风口' in eff or eff=='天花末端点位': return 5
    if eff.startswith('DUCT') or eff=='hvac-hide': return 151
    if eff.startswith('EQ') or eff.startswith('M-EQ') or 'PIPE' in eff or '管道' in eff: return 141
    return 8
def go(layout,M,effL,depth=0):
    for e in layout:
        t=e.dxftype(); L=e.dxf.layer; eff=effL if (L=='0' and effL) else L
        if t=='INSERT':
            if depth>10 or e.dxf.name not in d.blocks: continue
            b=d.blocks.get(e.dxf.name)
            try: go(b,(Matrix44.translate(*(-b.block.dxf.base_point))@e.matrix44())@M,eff,depth+1)
            except Exception: pass
            continue
        if t in('TEXT','MTEXT'):
            try:
                p=M.transform(e.dxf.insert); s=e.plain_text() if t=='MTEXT' else e.dxf.text
                h=e.dxf.get('char_height' if t=='MTEXT' else 'height',100)
                c=col(eff)
                if c==2: c=2
                if s and c in(1,30,3,200,4,2,210): texts.append((p.x,p.y,s[:30],h,c))
            except: pass
            continue
        try: v=np.array([(q.x,q.y) for q in path.make_path(e).transform(M).flattening(20)])
        except Exception: continue
        if len(v)>1: segs.setdefault(col(eff),[]).append(v)
go(m,Matrix44(),None)
order=['ref','st',8,141,151,6,5,4,3,2,30,200,210,1]
for k,(x0,x1,y0,y1,title) in views.items():
    W=20; Hh=W*(y1-y0)/(x1-x0)
    fig=plt.figure(figsize=(W,Hh),dpi=130); ax=fig.add_axes([0,0,1,1])
    for c in order:
        vs=segs.get(c,[])
        sel=[v for v in vs if v[:,0].max()>=x0 and v[:,0].min()<=x1 and v[:,1].max()>=y0 and v[:,1].min()<=y1]
        if not sel: continue
        rgb=(0.35,0.35,0.35) if c=='old' else (0.85,0.85,0.85) if c=='ref' else (0.72,0.6,0.45) if c=='st' else np.array(colors.aci2rgb(c))/255
        lw={'ref':0.3,'st':0.35,8:0.3,141:0.4,151:0.4,6:0.9,5:1.1,3:1.2,30:1.0,1:1.0,200:1.2,4:1.0,2:1.2,210:1.2}.get(c,0.5)
        ax.add_collection(LineCollection(sel,colors=[rgb],linewidths=lw,linestyles=('--' if c in('old','st') else '-')))
    sc=(W*130)/(x1-x0)
    for x,y,s,h,c in texts:
        if x0<=x<=x1 and y0<=y<=y1: ax.text(x,y,s,fontsize=max(5,min(14,h*sc*0.6)),color=np.array(colors.aci2rgb(c))/255,family='Noto Sans CJK SC')
    ax.text(x0+(x1-x0)*0.01,y1-(y1-y0)*0.03,title,fontsize=16,family='Noto Sans CJK SC',va='top',bbox=dict(fc='white',ec='black'))
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal'); ax.axis('off')
    fig.savefig(f'{outdir}/{tag}_{k}.png',dpi=130,facecolor='white'); plt.close(fig); print('saved',k,flush=True)
