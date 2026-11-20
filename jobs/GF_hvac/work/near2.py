import ezdxf
from ezdxf import path
from ezdxf.math import Matrix44
d=ezdxf.readfile('GF_clean.dxf'); m=d.modelspace()
pts=[(-118739,19000),(-108627,19450),(-111124,19000)]
def go(lay,M,eff,root,chain,depth=0):
    for e in lay:
        t=e.dxftype(); L=e.dxf.layer; ef=eff if L=='0' and eff else L
        if t=='INSERT':
            if depth>10 or e.dxf.name not in d.blocks: continue
            b=d.blocks.get(e.dxf.name)
            go(b,(Matrix44.translate(*(-b.block.dxf.base_point))@e.matrix44())@M,ef,root or e.dxf.name,chain+[(e.dxf.name,L)],depth+1); continue
        if t not in('CIRCLE','ARC','LWPOLYLINE','HATCH'): continue
        try: p=path.make_path(e).transform(M)
        except: continue
        bb=p.bbox() if hasattr(p,'bbox') else None
        try:
            import ezdxf.path as P; bb=P.bbox([p])
        except: continue
        if bb.size.x>600: continue
        for x,y in pts:
            if abs(bb.center.x-x)<250 and abs(bb.center.y-y)<400: print((x,y),t,'layer',L,'eff',ef,'root',root,chain[-2:],[round(v) for v in bb.center][:2],round(bb.size.x))
go(m,Matrix44(),None,None,[])
