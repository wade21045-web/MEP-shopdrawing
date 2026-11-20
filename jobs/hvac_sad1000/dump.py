import ezdxf,pickle,sys
d=ezdxf.readfile('/workspace/hvac_shop/out/input.dxf'); db=d.entitydb
res=pickle.load(open('region.pkl','rb'))
pickle.dump(None,open('/dev/null','wb'))
out=open('dump.txt','w')
for r in sorted(res,key=lambda r:(r[2],r[4][0])):
    e=db[r[0]]; t=e.dxftype()
    if t=='LINE': g=f"({e.dxf.start.x:.1f},{e.dxf.start.y:.1f})-({e.dxf.end.x:.1f},{e.dxf.end.y:.1f})"
    elif t=='LWPOLYLINE': g=' '.join(f"({p[0]:.0f},{p[1]:.0f})" for p in e.get_points('xy'))[:200]+(' C' if e.closed else '')
    elif t=='INSERT': g=f"ins({e.dxf.insert.x:.1f},{e.dxf.insert.y:.1f}) rot{e.dxf.rotation:.1f} sc{e.dxf.xscale:.2f},{e.dxf.yscale:.2f} {e.dxf.name}"
    elif t in('TEXT','MTEXT'): g=f"ins({e.dxf.insert.x:.1f},{e.dxf.insert.y:.1f}) {(e.dxf.text if t=='TEXT' else e.plain_text())[:40]!r}"
    elif t in('CIRCLE','ARC'): g=f"c({e.dxf.center.x:.1f},{e.dxf.center.y:.1f}) r{e.dxf.radius:.1f}"
    else: g=f"bb {r[4]} {r[5]}"
    out.write(f"{r[2]}\t{r[0]}\t{t}\t{g}\n")
