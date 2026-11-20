import ezdxf,re,pickle
d=ezdxf.readfile('/workspace/hvac_shop/out/input.dxf'); m=d.modelspace()
out=[]
for e in m.query('TEXT MTEXT'):
    s=e.dxf.text if e.dxftype()=='TEXT' else e.plain_text()
    if re.search(r'SAD\s*1000|SAD\s*1600|RAD\s*1100|SAO\s*1600|SAD\s*1100',s):
        p=e.dxf.insert; out.append((s,round(p.x),round(p.y),e.dxf.layer,e.dxf.handle))
for o in sorted(out,key=lambda o:(o[1],o[2])): print(o)
