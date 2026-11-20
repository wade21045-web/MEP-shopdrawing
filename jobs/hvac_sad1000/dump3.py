import ezdxf,sys
from ezdxf import bbox
d=ezdxf.readfile(sys.argv[2] if len(sys.argv)>2 else 'out_after.dxf'); m=d.modelspace()
X0,X1,Y0,Y1=[float(v) for v in sys.argv[1].split(',')]
c=bbox.Cache()
for e in m:
    if e.dxf.layer.startswith('新底图'): continue
    try: b=bbox.extents([e],cache=c,fast=True)
    except Exception: continue
    if not b.has_data or b.extmax.x<X0 or b.extmin.x>X1 or b.extmax.y<Y0 or b.extmin.y>Y1: continue
    t=e.dxftype()
    if t=='LINE': g=f"({e.dxf.start.x:.1f},{e.dxf.start.y:.1f})-({e.dxf.end.x:.1f},{e.dxf.end.y:.1f})"
    elif t=='LWPOLYLINE': g=' '.join(f"({p[0]:.0f},{p[1]:.0f},b{p[4]:.2f})" for p in e.get_points('xyseb'))[:250]
    elif t=='INSERT': g=f"ins({e.dxf.insert.x:.1f},{e.dxf.insert.y:.1f}) rot{e.dxf.rotation:.1f} sc{e.dxf.xscale:.2f},{e.dxf.yscale:.2f} {e.dxf.name}"
    elif t in('TEXT','MTEXT'): g=f"ins({e.dxf.insert.x:.1f},{e.dxf.insert.y:.1f}) {(e.dxf.text if t=='TEXT' else e.plain_text())[:40]!r}"
    elif t in('CIRCLE','ARC'): g=f"c({e.dxf.center.x:.1f},{e.dxf.center.y:.1f}) r{e.dxf.radius:.1f}"+(f" a{e.dxf.start_angle:.1f}-{e.dxf.end_angle:.1f}" if t=='ARC' else '')
    else: g=f"bb {tuple(round(v) for v in b.extmin)[:2]} {tuple(round(v) for v in b.extmax)[:2]}"
    print(f"{e.dxf.layer}\t{e.dxf.handle}\t{t}\t{g}\tlt={e.dxf.get('linetype','')}")
