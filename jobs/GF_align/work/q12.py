import ezdxf,sys,collections,numpy as np,re,pickle
from ezdxf import path as P
from ezdxf.math import Matrix44,Vec3
key=sys.argv[1]
cfg={'23':("dxf/1.GF-02&03大平标新位置-0914.dxf",[('MS',(36446.00,-20918.06),{'02-03组','0905建筑'})]),
     '01':("dxf/1.GF-01-0914.dxf",[('MS',(36446.53,-20917.40),{'A$C3087fbf4','0905jianzhu'}),('A$C3087fbf4',(-56314.20,-23735.08),set())]),
     'off':("dxf/Office-F00 plan 1017.dxf",[('MS',(-151883.20,-20917.26),set())])}
f,frames=cfg[key]; d=ezdxf.readfile(f)
LY=re.compile(r'综合末端-天花|C-暖通设备|C-顶面设备|风口')
BX=(-150000,95000,-100000,35000)
out=[]
def walk(layout,M,eff,top,chain,depth):
    for e in layout:
        L=e.dxf.layer; ef=eff if (L=='0' and eff) else L
        t=e.dxftype()
        if t=='INSERT':
            if depth>12 or e.dxf.name not in d.blocks: continue
            b=d.blocks.get(e.dxf.name)
            try: M2=(Matrix44.translate(*(-Vec3(b.block.dxf.base_point)))@e.matrix44())@M
            except Exception: continue
            yield from walk(b,M2,ef,top or e.dxf.handle,chain+(e.dxf.name,),depth+1)
        else:
            if not LY.search(ef): continue
            try: v=np.array([(q.x,q.y) for q in P.make_path(e).transform(M).flattening(5)])
            except Exception: continue
            if len(v)<2: continue
            curved=t in('ARC','SPLINE','ELLIPSE','CIRCLE') or (t=='LWPOLYLINE' and any(b_!=0 for b_ in e.get_points('b')))
            yield dict(ef=ef,t=t,top=top,chain=chain,pts=v,curved=curved,h=e.dxf.handle)
for fr,T,skip in frames:
    lay=d.modelspace() if fr=='MS' else d.blocks.get(fr)
    for it in walk(lay,Matrix44(),None,None,(),0):
        if fr=='MS' and it['chain'] and it['chain'][0] in skip: continue
        it['pts']=it['pts']+np.array(T); c=it['pts'].mean(0)
        if not(BX[0]<c[0]<BX[1] and BX[2]<c[1]<BX[3]): continue
        it['fr']=fr; out.append(it)
pickle.dump(out,open(f'prim_{key}.pkl','wb'))
c=collections.Counter((it['chain'][-1] if it['chain'] else '-',it['ef']) for it in out)
for k,n in c.most_common(80): print(n,k)
