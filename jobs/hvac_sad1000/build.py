import ezdxf,pickle,json
from ezdxf.math import Vec3
from ezdxf import bbox
SRC='/workspace/hvac_shop/out/input.dxf'
d=ezdxf.readfile(SRC); m=d.modelspace(); db=d.entitydb
res=pickle.load(open('region.pkl','rb'))
MEP=db['CCEC8'].dxf.insert; DEC=db['1083AA'].dxf.insert
DX=MEP.x-DEC.x            # shift left by DX
XC,XR,Y0,Y1=-74900.0,-67500.0,-4300.0,3300.0
def inw(x,y): return XC<x<XR and Y0<y<Y1
PIPE_Y=(-2850,-2500); CD_Y=(-1900,-1855)
def selected(r):
    h,t,L,nm,mn,mx=r
    if mx[0]<=XC or mn[0]>=XR or mx[1]<=Y0 or mn[1]>=Y1: return False
    if L in('DUCT-送风中心线','DUCT-送风管','DUCT-送风管端线','DUCT-送风法兰','DUCT-送风标注','DUCT-送风阀门','DUCT-送风风口',
            'DUCT-回风中心线','DUCT-回风管','DUCT-回风标注','DUCT-回风阀门','DUCT-排风风口','M-EQPM','A-DETL',
            'VANNE','管道1','管道2','管道5','HVAC-P-VA','DUCT-新风标注'): return True
    if L.startswith(('DUCT-排烟','DUCT-加压送风')): return mn[1]>=PIPE_Y[0] and mx[1]<=PIPE_Y[1]
    if L in('DUCT-新风管','DUCT-新风中心线'): return mn[1]>=CD_Y[0] and mx[1]<=CD_Y[1]
    if L=='综合末端-天花': return t=='INSERT' and nm.startswith('$风口$')
    if L=='hvac-hide': return mx[0]<-70000
    if L=='0': return h=='DBDCA'
    return False
sel=[r for r in res if selected(r)]
log={'dx':DX,'moved':[],'stretched':[],'skipped':[],'bylayer':{}}
for h,t,L,nm,mn,mx in sel:
    e=db[h]
    if t=='LINE':
        s,en=e.dxf.start,e.dxf.end; a,b=inw(s.x,s.y),inw(en.x,en.y)
        if a and b: e.translate(-DX,0,0); log['moved'].append(h)
        elif a or b:
            if a: e.dxf.start=Vec3(s.x-DX,s.y,s.z)
            if b: e.dxf.end=Vec3(en.x-DX,en.y,en.z)
            log['stretched'].append(h)
        else: log['skipped'].append((h,'line-no-endpoint'))
    elif t=='LWPOLYLINE':
        pts=list(e.get_points('xyseb')); f=[inw(p[0],p[1]) for p in pts]
        if all(f): e.translate(-DX,0,0); log['moved'].append(h)
        elif any(f):
            e.set_points([(p[0]-DX if k else p[0],)+tuple(p[1:]) for p,k in zip(pts,f)],format='xyseb'); log['stretched'].append(h)
        else: log['skipped'].append((h,'poly'))
    else:
        if t in('TEXT','MTEXT','INSERT'): p=e.dxf.insert; ok=inw(p.x,p.y)
        elif t in('CIRCLE','ARC'): p=e.dxf.center; ok=inw(p.x,p.y)
        else: ok=inw(mn[0],mn[1]) and inw(mx[0],mx[1])
        if ok: e.translate(-DX,0,0); log['moved'].append(h)
        else: log['skipped'].append((h,t))
    if h in log['moved'] or h in log['stretched']:
        log['bylayer'][L]=log['bylayer'].get(L,0)+1
NL='修改-风管缩短20261119'
if NL not in d.layers: d.layers.add(NL,color=2)
note=m.add_text('修改20261119: SAD1000×250直管段缩短%.0fmm, 其下游送风管/支管/风口/机组/回风管整体左移%.0fmm, 使SAD%%%%C300风口与装饰圆形风口对齐'%(DX,DX),
                dxfattribs={'layer':NL,'height':150,'insert':(-77800,3000)})
log['note']=note.dxf.handle
d.saveas('out_after.dxf')
json.dump(log,open('build_log.json','w'),ensure_ascii=False,indent=0)
print('DX',DX,'moved',len(log['moved']),'stretched',len(log['stretched']),'skipped',log['skipped'])
print(log['bylayer']); print('stretched',log['stretched'])
