import ezdxf,pickle,json,math
from ezdxf.math import Vec3,Vec2
from ezdxf import bbox
from common import *
d=ezdxf.readfile('out/input.dxf'); m=d.modelspace(); db=d.entitydb
res=pickle.load(open('region.pkl','rb'))
# room: anchor diffuser used as frame origin, return diffuser, supply diffuser
ROOMS={'L':{'anchor':'D043','ret':'D050','sup':'D043','name':'SHOP(左,D050/D043)'},
       'R':{'anchor':'D044','ret':'D044','sup':'D045','name':'SHOP(右,D044/D045)'}}
NOTE_LAYER='修改-风机盘管调整20261119'
if NOTE_LAYER not in d.layers: d.layers.add(NOTE_LAYER,color=2)
JOG={'CWR':-1900.0,'CWS':-1700.0,'CD':-1500.0}
cache=bbox.Cache()
def bc(e):
    b=bbox.extents([e],cache=cache,fast=True); return (b.extmin+b.extmax)/2
log={'deleted':{},'added':{},'info':{}}
for rk,cfg in ROOMS.items():
    O=DIFF[cfg['anchor']]
    L=lambda p:loc(p,O)
    W=lambda x,y:Vec3(*wld((x,y),O),0)
    cand=[db[r[0]] for r in res if r[0] in db and db[r[0]].is_alive]
    def inwin(e,x0,x1,y0,y1):
        c=L(bc(e)); return x0<=c[0]<=x1 and y0<=c[1]<=y1
    eq=[e for e in cand if e.dxf.layer=='EQ-风机盘管' and inwin(e,-2500,3000,-100,1400)]
    xs=[L(p)[0] for e in eq for p in (e.dxf.start,e.dxf.end)]; ys=[L(p)[1] for e in eq for p in (e.dxf.start,e.dxf.end)]
    cx=(min(xs)+max(xs))/2
    duct=[e for e in cand if e.dxf.layer.startswith('DUCT-送风') and inwin(e,cx-400,cx+2300,150,1150)]
    cl=[e for e in duct if e.dxf.layer=='DUCT-送风中心线'][0]
    yc=L(cl.dxf.start)[1]
    tag=[e for e in cand if e.dxftype()=='TEXT' and e.dxf.text=='FCU-06' and inwin(e,cx-1500,cx+500,0,2000)]
    outlet=[e for e in cand if e.dxf.layer=='天花末端点位' and inwin(e,cx,cx+2500,0,1200)]
    # valve chain (moves with FCU)
    chain=[e for e in cand if e.dxf.layer in('VANNE','管道1','管道2') and inwin(e,cx-450,cx+150,-800,150)
           and not (e.dxftype()=='LINE' and min(L(e.dxf.start)[1],L(e.dxf.end)[1])<-700)]
    drops={}
    for kind,lay,xc in (('CWR','管道2',-232),('CWS','管道1',-32)):
        drops[kind]=[e for e in cand if e.dxf.layer==lay and e.dxftype()=='LINE' and inwin(e,cx-450,cx+150,-2900,-500)
                     and abs(L(e.dxf.start)[1]-L(e.dxf.end)[1])>1500]
    cdsym=[e for e in cand if e.dxf.layer=='管道5' and inwin(e,cx+60,cx+250,-100,100)]
    drops['CD']=[e for e in cand if e.dxf.layer=='管道5' and inwin(e,cx+60,cx+250,-2400,-150) and e.dxftype() in('LINE','LWPOLYLINE')]
    # target
    rx=L(DIFF[cfg['ret']])[0]; sx=L(DIFF[cfg['sup']])[0]
    dx=rx-cx; dy=-yc
    D=Vec3(*(wld((dx,dy),(0,0))),0)  # vector in world
    xend=sx+300.0
    info={'fcu_center_local':[round(cx,1),round((min(ys)+max(ys))/2,1)],'duct_centerline_y':round(yc,1),'shift_local':[round(dx,1),round(dy,1)],
          'n':{'eq':len(eq),'duct':len(duct),'tag':len(tag),'outlet':len(outlet),'chain':len(chain),'cdsym':len(cdsym),
               'drops':{k:len(v) for k,v in drops.items()}}}
    print(rk,info)
    assert len(tag)==1 and len(outlet)==1 and len(drops['CWR'])==3 and len(drops['CWS'])==3 and len(drops['CD'])==3
    added=[]; deleted=[]
    def addcopy(e):
        n=e.copy(); m.add_entity(n); added.append(n.dxf.handle); return n
    # 1 FCU, tag, chain, condensate symbol: copy translated
    for e in eq+tag+chain+cdsym:
        n=addcopy(e); n.translate(D.x,D.y,0)
    # 2 duct: copy translated, stretch far end to xend
    for e in duct:
        n=addcopy(e)
        if e.dxftype()=='LINE':
            ps=[]
            for p in (e.dxf.start,e.dxf.end):
                q=L(p)
                nx=xend if q[0]>cx+1500 else q[0]+dx
                w=W(nx,q[1]+dy); ps.append(Vec3(w.x,w.y,p[2]))
            n.dxf.start,n.dxf.end=ps
        else: n.translate(D.x,D.y,0)
    # 3 supply outlet 600x600 ($风口$00000060, DUCT-送风风口) centred on the supply decorative diffuser
    proto=db['DA072']; n=addcopy(proto)
    c=DIFF[cfg['sup']]; n.dxf.insert=Vec3(c[0],c[1],proto.dxf.insert.z); n.dxf.rotation=ANG
    # 4 pipes: L-shaped re-route from the main (old drop bottoms) to new valve chain / FCU
    for kind,ents in drops.items():
        # centre x from the 3 lines
        def pts(e): return [Vec3(e.dxf.start),Vec3(e.dxf.end)] if e.dxftype()=='LINE' else [Vec3(p[0],p[1],e.dxf.elevation) for p in e.get_points('xy')]
        xs_=[L(pts(e)[0])[0] for e in ents]; xc=sorted(xs_)[1]
        for e in ents:
            P=pts(e); P=sorted(P,key=lambda p:L(p)[1]); bot,top=P[0],P[-1]
            lb,lt=L(bot),L(top)
            off=-(lb[0]-xc)  # left-of-travel offset (travel up => left normal (-1,0))
            yj=JOG[kind]
            path=[Vec2(xc,lb[1]),Vec2(xc,yj),Vec2(xc+dx,yj),Vec2(xc+dx,lt[1]+dy)]
            # offset polyline
            def nrm(a,b):
                t=(b-a).normalize(); return Vec2(-t.y,t.x)
            ns=[nrm(path[i],path[i+1]) for i in range(3)]
            op=[path[0]+ns[0]*off]+[path[i]+(ns[i-1]+ns[i])*off for i in (1,2)]+[path[3]+ns[2]*off]
            # keep exact original bottom point
            op[0]=Vec2(lb[0],lb[1])
            zs=[bot.z,top.z,top.z,top.z]
            for i in range(3):
                a=W(*op[i]); b=W(*op[i+1])
                n=addcopy(e)
                if e.dxftype()=='LINE':
                    n.dxf.start=Vec3(a.x,a.y,zs[i]); n.dxf.end=Vec3(b.x,b.y,zs[i+1])
                else:
                    n.set_points([(a.x,a.y),(b.x,b.y)],format='xy')
    # 5 delete originals
    for e in eq+tag+chain+cdsym+duct+outlet+drops['CWR']+drops['CWS']+drops['CD']:
        deleted.append(e.dxf.handle)
    for h in deleted: m.delete_entity(db[h])
    # 6 note
    st=db['10885D'].dxf.style
    t=m.add_text('MEP修改20261119:FCU-06移至回风口(兼检修口)上方,送风口与装饰风口重合',
        dxfattribs={'layer':NOTE_LAYER,'height':100,'rotation':ANG,'color':2,'style':st})
    t.set_placement(W(rx+500,-800)); added.append(t.dxf.handle)
    info['ret']=cfg['ret']; info['sup']=cfg['sup']; info['xend']=xend
    log['deleted'][rk]=deleted; log['added'][rk]=added; log['info'][rk]=info
    print(rk,'deleted',len(deleted),'added',len(added))
json.dump(log,open('build_log.json','w'),ensure_ascii=False,indent=1)
d.saveas('out_after.dxf')
