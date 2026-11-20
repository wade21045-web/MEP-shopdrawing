import ezdxf,sys,pickle,numpy as np
from ezdxf import path
from ezdxf.math import Matrix44
src,out=sys.argv[1],sys.argv[2]
d=ezdxf.readfile(src); m=d.modelspace()
S=[]
def go(layout,M,effL,top,depth=0):
    for e in layout:
        t=e.dxftype(); L=e.dxf.layer; eff=effL if (L=='0' and effL) else L
        if t=='INSERT':
            if depth>10 or e.dxf.name not in d.blocks: continue
            b=d.blocks.get(e.dxf.name)
            try: go(b,(Matrix44.translate(*(-b.block.dxf.base_point))@e.matrix44())@M,eff,top or (e.dxf.name,e.dxf.handle),depth+1)
            except Exception: pass
            continue
        if t in('TEXT','MTEXT','HATCH','DIMENSION','ATTRIB','ATTDEF'): continue
        try: v=np.array([(q.x,q.y) for q in path.make_path(e).transform(M).flattening(20)],dtype=np.float32)
        except Exception: continue
        if len(v)>1: S.append((eff,top[0] if top else '',v))
go(m,Matrix44(),None,None)
pickle.dump(S,open(out,'wb')); print(len(S))
