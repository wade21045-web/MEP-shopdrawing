import ezdxf
from ezdxf.math import Matrix44, Vec3
def walk(d, layout, M=None, eff=None, chain=(), depth=0, stop=None):
    """yield (e, M, effLayer, chain). stop(e,eff,chain)->True to yield INSERT and not descend"""
    if M is None: M=Matrix44()
    for e in layout:
        t=e.dxftype(); L=e.dxf.layer
        ef = eff if (L=='0' and eff) else L
        if t=='INSERT':
            if stop and stop(e,ef,chain):
                yield e,M,ef,chain; continue
            if depth>12 or e.dxf.name not in d.blocks: continue
            b=d.blocks.get(e.dxf.name)
            try: M2=(Matrix44.translate(*(-Vec3(b.block.dxf.base_point)))@e.matrix44())@M
            except Exception: continue
            yield from walk(d,b,M2,ef,chain+(e.dxf.name,),depth+1,stop)
        else:
            yield e,M,ef,chain
def txt(e):
    t=e.dxftype()
    try:
        if t=='MTEXT': return e.plain_text()
        if t in('TEXT','ATTRIB'): return e.dxf.text
    except Exception: pass
    return ''
