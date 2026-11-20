import ezdxf,collections,numpy as np,re
from lib import walk
d=ezdxf.readfile('dxf/L2-大平面-升版9.2.dxf'); m=d.modelspace()
TL=('综合末端-天花','C-顶面设备（风口、换气扇、投影仪）','C-暖通设备')
def stop(e,ef,ch): return ef in TL or re.search('风口',e.dxf.name)
c=collections.Counter(); pos=collections.defaultdict(list)
for e,M,ef,ch in walk(d,m,stop=stop):
    if e.dxftype()=='INSERT':
        p=M.transform(e.dxf.insert); c[(ef,e.dxf.name,ch[:1])]+=1; pos[(ef,e.dxf.name)].append((round(p.x),round(p.y)))
for k,v in c.most_common(100): print(v,k)
print()
for k,v in sorted(pos.items(),key=lambda x:-len(x[1]))[:60]:
    a=np.array(v); print(k,len(a),a.min(0),a.max(0))
# non-insert entities on those layers
c2=collections.Counter((ef,e.dxftype(),ch[:2]) for e,M,ef,ch in walk(d,m,stop=stop) if ef in TL and e.dxftype()!='INSERT')
print(c2.most_common(30))
# top-level inserts big
for e in m:
    if e.dxftype()=='INSERT':
        b=d.blocks.get(e.dxf.name)
        if b is not None and len(b)>100: print('BIG',e.dxf.layer,e.dxf.name,len(b),e.dxf.insert,e.dxf.xscale,e.dxf.rotation)
