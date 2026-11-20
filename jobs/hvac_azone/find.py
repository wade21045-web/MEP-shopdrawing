import ezdxf,re
d=ezdxf.readfile('out/input.dxf'); m=d.modelspace()
print(len(m), len(d.layouts), [l.name for l in d.layouts])
for e in m.query('TEXT MTEXT'):
    t=e.dxf.text if e.dxftype()=='TEXT' else e.text
    if re.search(r'FLOUR|STORAGE|OFFICE|D06[1-5]',t,re.I):
        print(e.dxftype(),e.dxf.layer,repr(t[:60]),tuple(round(c) for c in e.dxf.insert))
