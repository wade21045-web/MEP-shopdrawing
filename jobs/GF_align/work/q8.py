import ezdxf,numpy as np,collections
from ezdxf import path as P
d=ezdxf.readfile('/workspace/GF_hvac/output/GF_暖通+建筑结构底图.dxf')
off=np.array([8046.452163030306, 18543.75074625024])
b=d.blocks.get('A$C124230B8')
for e in b:
    if e.dxf.layer=='天花末端点位':
        t=e.dxftype()
        if t=='INSERT':
            print('INS',e.dxf.name,np.round(np.array(e.dxf.insert[:2])+off),e.dxf.rotation, e.dxf.color)
        else:
            pts=np.array([(v.x,v.y) for v in P.make_path(e).flattening(5)])+off
            print(t,np.round(pts.mean(0)),e.dxf.color)
