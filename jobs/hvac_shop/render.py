import ezdxf,sys,pickle,math,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from ezdxf import path
from ezdxf.colors import aci2rgb
from ezdxf.math import Matrix44
src,out=sys.argv[1],sys.argv[2]
X0,X1,Y0,Y1=[float(v) for v in sys.argv[3].split(',')]
hl=sys.argv[4].split(',') if len(sys.argv)>4 and sys.argv[4] else []
d=ezdxf.readfile(src); m=d.modelspace()
lay={l.dxf.name:l for l in d.layers}
def lcol(L):
    l=lay.get(L)
    if l is None: return 7
    if l.has_dxf_attrib('true_color'): return l.dxf.true_color
    return abs(l.dxf.color)
def frozen(L):
    l=lay.get(L); return l is not None and (l.is_off() or l.is_frozen())
def rgb(c):
    if isinstance(c,tuple): return tuple(v/255 for v in c)
    if c in(7,0,256,257): return (0.9,0.9,0.9)
    r=aci2rgb(c); return (r[0]/255,r[1]/255,r[2]/255)
segs=[];cols=[];texts=[];NERR=0
def ecol(e,parent_col,eff):
    if e.dxf.hasattr('true_color'):
        tc=e.dxf.true_color; return ((tc>>16)&255,(tc>>8)&255,tc&255)
    c=e.dxf.get('color',256)
    if c==0: return parent_col
    if c==256: return lcol(eff)
    return c
def inside(pts):
    a=np.array(pts); return not(a[:,0].max()<X0 or a[:,0].min()>X1 or a[:,1].max()<Y0 or a[:,1].min()>Y1)
def go(ents,M,effL,pcol,depth):
    for e in ents:
        t=e.dxftype(); L=e.dxf.layer; eff=effL if (L=='0' and effL) else L
        if frozen(eff): continue
        c=ecol(e,pcol,eff)
        if t=='INSERT':
            if depth>8: continue
            try:
                bp=d.blocks.get(e.dxf.name)
                go(bp,Matrix44.translate(*(-bp.block.dxf.base_point))@e.matrix44()@M,eff,c,depth+1)
            except Exception as ex: pass
            continue
        if t in('TEXT','MTEXT'):
            try:
                p=M.transform(e.dxf.insert)
                if X0<p.x<X1 and Y0<p.y<Y1:
                    s=e.dxf.text if t=='TEXT' else e.plain_text()
                    h=(e.dxf.get('height',100) if t=='TEXT' else e.dxf.get('char_height',100))*M.transform_direction((1,0,0)).magnitude
                    rot=e.dxf.get('rotation',0)
                    if t=='MTEXT':
                        v=e.dxf.get('text_direction',None)
                        if v is not None: rot=math.degrees(math.atan2(v[1],v[0]))
                    rd=M.transform_direction(ezdxf.math.Vec3.from_deg_angle(rot))
                    texts.append((p.x,p.y,s,h,math.degrees(math.atan2(rd.y,rd.x)),c,e.dxf.handle))
            except Exception as ex:
                global NERR
                NERR=NERR+1
                if NERR<3: print('TXTERR',repr(ex))
            continue
        if t in('HATCH','SOLID','DIMENSION','ATTDEF','ATTRIB','POINT','VIEWPORT','WIPEOUT','IMAGE'): continue
        try: p=path.make_path(e)
        except Exception: continue
        try: p=p.transform(M); pts=[(v.x,v.y) for v in p.flattening(5)]
        except Exception: continue
        if len(pts)<2 or not inside(pts): continue
        cc=c
        if hl and any(L.startswith(h) for h in hl): cc=(255,255,0)
        for a,b in zip(pts,pts[1:]): segs.append((a,b)); cols.append(rgb(cc))
go(m,Matrix44(),None,7,0)
W=X1-X0;H=Y1-Y0
fig=plt.figure(figsize=(14,14*H/W),dpi=110); ax=fig.add_axes([0,0,1,1]); ax.set_facecolor((0.13,0.15,0.18)); fig.patch.set_facecolor((0.13,0.15,0.18))
ax.add_collection(LineCollection(segs,colors=cols,linewidths=0.6))
for x,y,s,h,r,c,hd in texts:
    fs=max(3,h/W*14*72*1.0)
    ax.text(x,y,s,fontsize=fs,rotation=r,color=rgb(c),fontfamily=['Noto Sans CJK SC','DejaVu Sans'],ha='left',va='bottom',rotation_mode='anchor',clip_on=True)
ax.set_xlim(X0,X1);ax.set_ylim(Y0,Y1);ax.set_aspect('equal');ax.axis('off')
fig.savefig(out); print(len(segs),len(texts))
pickle.dump(texts,open(out+'.texts.pkl','wb'))
