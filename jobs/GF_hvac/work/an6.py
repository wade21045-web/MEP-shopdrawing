import ezdxf,collections
d=ezdxf.readfile('dxf_out/GF.dxf'); m=d.modelspace()
b=d.blocks.get('dsadasdqwqwqq'); c=collections.Counter()
for e in b: c[(e.dxf.layer,e.dxftype(),e.dxf.name if e.dxftype()=='INSERT' else (e.dxf.text if e.dxftype()=='TEXT' else ''))]+=1
for k,n in c.most_common(): print(n,k)
print('---XREFblk'); 
for e in d.blocks.get('A$C7FB758C8'): print(e.dxftype(),e.dxf.layer, getattr(e.dxf,'radius',None), e.dxf.get('name',''))
for e in m:
  if e.dxf.layer=='0' and e.dxftype()=='CIRCLE': print('circ',[round(v) for v in e.dxf.center][:2],e.dxf.radius)
