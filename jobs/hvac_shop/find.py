import ezdxf,re,pickle
d=ezdxf.readfile('out/input.dxf'); m=d.modelspace()
print(len(m))
for e in m.query('TEXT MTEXT'):
    t=e.dxf.text if e.dxftype()=='TEXT' else e.plain_text()
    if re.search(r'SHOP|CLNR|D04[3-5]|D050|FCU-06|装饰有',t,re.I):
        print(e.dxf.handle,e.dxftype(),e.dxf.layer,repr(t[:60]),tuple(round(c) for c in e.dxf.insert),round(e.dxf.get('rotation',0),1))
