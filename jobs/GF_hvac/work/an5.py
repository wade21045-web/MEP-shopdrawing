import ezdxf,collections
from ezdxf import bbox
d=ezdxf.readfile('dxf_out/GF.dxf'); m=d.modelspace()
for e in m:
    L=e.dxf.layer
    if L.startswith('Misc-Hvac') or L in('DUCT-送风风口',): continue
    try: bb=bbox.extents([e],fast=True); c=[round(v) for v in bb.center][:2]; s=[round(v) for v in bb.size][:2]
    except: c=s=None
    t=''
    if e.dxftype()=='MTEXT': t=e.plain_text()
    elif e.dxftype()=='TEXT': t=e.dxf.text
    elif e.dxftype()=='DIMENSION': t='dim'
    elif e.dxftype()=='INSERT': t='B:'+e.dxf.name
    if L in('0','ACS_COM','PUB_HATCH','支吊架','WALL','DOTE','COLUMN','A-WALL-1','S-楼板-截面线','AR-WALL-CONC-F','MENUISERI1','图层1','桥架','CABLETRAY','桥架中心线','DUCT-新风管端线','DUCT-新风法兰') and not t: 
        print(L,e.dxftype(),c,s); continue
    print(L,e.dxftype(),c,s,repr(t[:60]))
