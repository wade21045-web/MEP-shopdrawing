import ezdxf,math,sys,pickle
from common import *
d=ezdxf.readfile('out/input.dxf'); db=d.entitydb
res=pickle.load(open('region.pkl','rb'))
skip=('M_AX_CV','新底图','TH_DIM','C-天花','DIM_MODI','M_18-LEGENDE')
o=DIFF[sys.argv[1]]
X0,X1,Y0,Y1=[float(v) for v in sys.argv[2].split(',')]
rows=[]
for r in res:
    if r[2].startswith(skip): continue
    e=db[r[0]]
    c=((r[6][0]+r[7][0])/2,(r[6][1]+r[7][1])/2); l=loc(c,o)
    if not(X0<l[0]<X1 and Y0<l[1]<Y1): continue
    t=e.dxftype()
    R=lambda p:tuple(round(v) for v in loc(p,o))
    if t=='LINE': g=f"{R(e.dxf.start)}->{R(e.dxf.end)} z={e.dxf.start[2]:.0f}/{e.dxf.end[2]:.0f}"
    elif t=='LWPOLYLINE':
        p=list(e.get_points('xy')); g=f"n={len(p)} {R(p[0])}..{R(p[-1])} w={e.dxf.get('const_width',0)} closed={e.closed}"
    elif t=='INSERT': g=f"{e.dxf.name} ins={R(e.dxf.insert)} rot={e.dxf.rotation:.2f} sc={e.dxf.xscale:.2f}"
    elif t=='TEXT': g=f"'{e.dxf.text}' ins={R(e.dxf.insert)} h={e.dxf.height} rot={e.dxf.rotation:.1f}"
    elif t=='SPLINE': g=f"cp0={R(e.control_points[0])} cpN={R(e.control_points[-1])} n={len(e.control_points)}"
    else: g=f"c={tuple(round(v) for v in l)}"
    rows.append((e.dxf.layer,t,g,r[0],e.dxf.get('color',256),e.dxf.get('linetype','BL')))
for x in sorted(rows): print(*x)
print(len(rows))
