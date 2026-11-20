import ezdxf,math,sys,pickle
d=ezdxf.readfile('out/input.dxf'); m=d.modelspace()
pickle.dump(None,open('/dev/null','wb'))
O={'FLOUR':(-102931.3,-45922.5),'STOR':(-106877.7,-49347.1),'OFF':(-109523.6,-51626.7)}
a=math.radians(-40.8688)
def loc(p,o):
    x,y=p[0]-o[0],p[1]-o[1]; return (round(x*math.cos(a)-y*math.sin(a)), round(x*math.sin(a)+y*math.cos(a)))
res=pickle.load(open('region.pkl','rb'))
skip=('M_AX_CV','新底图','核对','TH_DIM','C-天花','DIM_MODI')
for k in sys.argv[1:]:
  o=O[k]; print('=====',k)
  for r in res:
    if r[2].startswith(skip): continue
    e=d.entitydb[r[0]]
    c=((r[6][0]+r[7][0])/2,(r[6][1]+r[7][1])/2); l=loc(c,o)
    if not(-2500<l[0]<3000 and -3800<l[1]<3000): continue
    t=e.dxftype()
    if t=='LINE': g=f"{loc(e.dxf.start,o)}->{loc(e.dxf.end,o)} z={e.dxf.start[2]:.0f}"
    elif t=='LWPOLYLINE':
        p=list(e.get_points('xy')); g=f"n={len(p)} {loc(p[0],o)}..{loc(p[-1],o)} w={e.dxf.get('const_width',0)}"
    elif t=='INSERT': g=f"{e.dxf.name} ins={loc(e.dxf.insert,o)} rot={e.dxf.rotation:.1f}"
    elif t=='TEXT': g=f"'{e.dxf.text}' ins={loc(e.dxf.insert,o)} h={e.dxf.height} rot={e.dxf.rotation:.1f}"
    else: g=f"c={l}"
    print(r[0],t,e.dxf.layer,e.dxf.get('color',256),e.dxf.get('linetype','BL'),g)
