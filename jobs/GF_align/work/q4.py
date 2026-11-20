import ezdxf,collections
d=ezdxf.readfile('/workspace/GF_hvac/output/GF_暖通+建筑结构底图.dxf')
for r in ('A$C5E357C2F','A$C124230B8'):
    b=d.blocks.get(r); c=collections.Counter((e.dxf.layer,e.dxftype()) for e in b)
    print(r,len(b))
    for k,n in sorted(c.items()): print('  ',n,k)
