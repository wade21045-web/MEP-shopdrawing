import ezdxf,sys,collections
from lib import walk
f=sys.argv[1]; names=sys.argv[2].split('|')
d=ezdxf.readfile(f)
for n in names:
    b=d.blocks.get(n); c=collections.Counter(); 
    for e,M,ef,ch in walk(d,b): c[ef]+=1
    print('##',n,sum(c.values()),'base',b.block.dxf.base_point); print('  ',c.most_common(40))
m=d.modelspace()
for e in m:
    if e.dxftype()=='INSERT' and e.dxf.name in names: print('INS',e.dxf.name,e.dxf.layer,[round(v) for v in e.dxf.insert][:2],round(e.dxf.rotation,3),e.dxf.xscale,e.dxf.yscale)
