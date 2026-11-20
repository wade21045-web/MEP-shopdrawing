import ezdxf
d=ezdxf.readfile('dxf_out/GF.dxf'); m=d.modelspace()
for e in m:
  if e.dxf.layer=='0' and e.dxftype() in('CIRCLE','ARC'): print(e.dxftype(),[round(v) for v in e.dxf.center][:2],round(e.dxf.radius),e.dxf.get('color'))
  if e.dxf.layer=='TH_DIM' and e.dxftype()=='MTEXT': print('T',[round(v) for v in e.dxf.insert][:2],e.plain_text().replace('\n',' '))
