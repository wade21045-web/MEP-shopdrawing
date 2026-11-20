import ezdxf,sys,numpy as np,matplotlib,pickle
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from ezdxf import disassemble, path, colors
from ezdxf.fonts import fonts
src,tag=sys.argv[1],sys.argv[2]
d=ezdxf.readfile(src); m=d.modelspace()
lc={L.dxf.name:abs(L.dxf.color) for L in d.layers}
segs={}; texts=[]
HL=('风口','核对','装饰-风口','天花末端点位')
def col(e,eff):
    if not any(k in eff for k in HL):
        if 'DUCT' in eff or 'Hvac' in eff: return 151
        return 8
    if eff.startswith('风口核对'): return 1
    if eff=='装饰-风口': return 6
    return 5
def _old(e,eff):
    c=e.dxf.get('color',256)
    if c in(0,256) or c is None:
        c=lc.get(eff,7)
    if c==7 or c>255: c=250
    return c
n=0
def go(layout,M,effL,depth=0):
    global n
    for e in layout:
        t=e.dxftype(); L=e.dxf.layer
        eff=effL if (L=='0' and effL) else L
        if t=='INSERT':
            if depth>10 or e.dxf.name not in d.blocks: continue
            try:
                for M2 in [e.matrix44()]:
                    b=d.blocks.get(e.dxf.name); 
                    # account for block base point
                    go(b, (ezdxf.math.Matrix44.translate(*(-b.block.dxf.base_point)) @ M2) @ M if True else None, eff, depth+1)
            except Exception as ex: pass
            continue
        if t=='DIMENSION':
            g=e.dxf.get('geometry')
            if g in d.blocks: go(d.blocks.get(g),M,eff,depth+1)
            continue
        if t in('TEXT','MTEXT','ATTDEF','ATTRIB'):
            try:
                p=M.transform(e.dxf.insert); s=(e.plain_text() if t=='MTEXT' else e.dxf.text) if t!='ATTDEF' else ''
                h=e.dxf.get('char_height' if t=='MTEXT' else 'height',100)*abs(M.get_row(0)[0] or 1)
                if s: texts.append((p.x,p.y,s[:40],h,col(e,eff)))
            except: pass
            continue
        if t=='HATCH':
            try:
                for bp in e.paths.rendering_paths(e.dxf.hatch_style) if False else []: pass
            except: pass
        try:
            p=path.make_path(e)
        except Exception: 
            if t=='HATCH':
                try:
                    ps=path.from_hatch(e)
                except: continue
                for p in ps:
                    v=np.array([(q.x,q.y) for q in p.transform(M).flattening(50)])
                    if len(v)>1: segs.setdefault(col(e,eff),[]).append(v)
            continue
        try:
            v=np.array([(q.x,q.y) for q in p.transform(M).flattening(20)])
        except: continue
        if len(v)>1: segs.setdefault(col(e,eff),[]).append(v); n+=1
go(m,ezdxf.math.Matrix44(),None)
print('paths',n,'texts',len(texts),flush=True)
views={'总览':(-135000,10000,-85000,25000),'局部A_办公北区西':(-92000,-55000,-28000,0),'局部B_办公北区东':(-50000,8000,-8000,22000),'局部C_GF02-03':(-64000,-24000,-48500,-19500),'局部D_GF01':(-117000,-87000,-61500,-25500),'局部E_中部':(-62000,-35000,-50000,-22000)}
for k,(x0,x1,y0,y1) in views.items():
    W=24; Hh=W*(y1-y0)/(x1-x0)
    fig=plt.figure(figsize=(W,Hh),dpi=150); ax=fig.add_axes([0,0,1,1]); ax.set_facecolor('white')
    for c,vs in segs.items():
        sel=[v for v in vs if v[:,0].max()>=x0 and v[:,0].min()<=x1 and v[:,1].max()>=y0 and v[:,1].min()<=y1]
        if sel: ax.add_collection(LineCollection(sel,colors=[np.array(colors.aci2rgb(c))/255],linewidths=(0.25 if k=='总览' else 0.4)*(3 if c in (1,6,5) else 1)))
    if k!='总览':
        sc=(W*150)/(x1-x0)  # px per unit
        for x,y,s,h,c in texts:
            if x0<=x<=x1 and y0<=y<=y1 and h*sc>2.5 and c in (1,6,5): ax.text(x,y,s,fontsize=max(2,h*sc*0.5),color=np.array(colors.aci2rgb(c))/255,family='Noto Sans CJK SC')
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal'); ax.axis('off')
    fig.savefig(f'/workspace/GF_align/output/{tag}_{k}.png',dpi=150,facecolor='white'); plt.close(fig); print('saved',k,flush=True)
