import ezdxf,pickle,json,math
from ezdxf.math import Vec3
from ezdxf import bbox
d=ezdxf.readfile('out_after.dxf'); m=d.modelspace(); db=d.entitydb
cache=bbox.Cache()
def bb(e):
    b=bbox.extents([e],cache=None,fast=True); return b
LOG={'halls':{},'branch':{},'deleted':[],'moved':{},'stretched':{},'modified':{},'compound':{}}
def rec(kind,h,info):
    LOG[kind][h]=info
# ---------- generic stretch (same rules as v1) ----------
SUP=('DUCT-送风中心线','DUCT-送风管','DUCT-送风管端线','DUCT-送风法兰','DUCT-送风标注','DUCT-送风阀门','DUCT-送风风口',
     'DUCT-回风中心线','DUCT-回风管','DUCT-回风管端线','DUCT-回风法兰','DUCT-回风标注','DUCT-回风阀门','DUCT-排风风口','M-EQPM','A-DETL',
     'VANNE','管道1','管道2','管道5','HVAC-P-VA','DUCT-新风标注')
def stretch(win,DX,DY,selfn,tag):
    XC,XR,Y0,Y1=win
    def inw(x,y): return XC<x<XR and Y0<y<Y1
    mv=[];st=[];sk=[]
    for e in list(m):
        L=e.dxf.layer
        if L.startswith(('新底图','核对')): continue
        try: b=bbox.extents([e],fast=True)
        except Exception: continue
        if not b.has_data: continue
        mn,mx=b.extmin,b.extmax
        if mx.x<=XC or mn.x>=XR or mx.y<=Y0 or mn.y>=Y1: continue
        if not selfn(e,mn,mx): continue
        t=e.dxftype(); h=e.dxf.handle
        if t=='LINE':
            s,en=e.dxf.start,e.dxf.end; a,c=inw(s.x,s.y),inw(en.x,en.y)
            if a and c: e.translate(DX,DY,0); mv.append(h)
            elif a or c:
                if a: e.dxf.start=Vec3(s.x+DX,s.y+DY,s.z)
                if c: e.dxf.end=Vec3(en.x+DX,en.y+DY,en.z)
                st.append(h)
            else: sk.append((h,t,L))
        elif t=='LWPOLYLINE':
            pts=list(e.get_points('xyseb')); f=[inw(p[0],p[1]) for p in pts]
            if all(f): e.translate(DX,DY,0); mv.append(h)
            elif any(f): sk.append((h,t,L,'POLY-CROSS'))
            else: sk.append((h,t,L))
        else:
            if t in('TEXT','MTEXT','INSERT'): p=e.dxf.insert; ok=inw(p.x,p.y)
            elif t in('CIRCLE','ARC'): p=e.dxf.center; ok=inw(p.x,p.y)
            else: ok=inw(mn.x,mn.y) and inw(mx.x,mx.y)
            if ok: e.translate(DX,DY,0); mv.append(h)
            else: sk.append((h,t,L))
    for h in mv:
        if h in LOG['stretched']: LOG['compound'][h]=tag
        elif h in LOG['moved']: o=LOG['moved'][h]; LOG['moved'][h]=[o[0]+DX,o[1]+DY,o[2]+'+'+tag]
        else: LOG['moved'][h]=[DX,DY,tag]
    for h in st:
        if h in LOG['moved'] or h in LOG['stretched']: LOG['compound'][h]=tag
        LOG['stretched'][h]=[DX,DY,tag,list(win)]
    return mv,st,sk
def hall_sel(cdband):
    def f(e,mn,mx):
        L=e.dxf.layer; t=e.dxftype()
        if L in SUP: return True
        if L.startswith(('DUCT-排烟','DUCT-加压送风')): return True
        if L.startswith('DUCT-新风'):
            if mn.x>=-70300 and mx.x<=-68300: return True
            return t=='LINE' and mn.y>=cdband[0] and mx.y<=cdband[1]
        if L=='综合末端-天花': return t=='INSERT' and e.dxf.name.startswith('$风口$')
        if L=='hvac-hide': return mx.x<-70000
        return False
    return f
HALLS={'mid':{'band':(-12500,-4600),'cd':(-7125,-7085),'mep':'CD117','dec':'1083B2','ys':-9100,
              'bdiff':'CD110','bceil':'CCEC9','bdec':'1083AC','ldiff':'CD111','ldec':'1083AE','lceil':'CCECA','uw':('CD114','1083B0')},
       'bot':{'band':(-21300,-13300),'cd':(-16180,-16135),'mep':'CD12F','dec':'1083BA','ys':-18100,
              'bdiff':'CD128','bceil':'CCECD','bdec':'1083B4','ldiff':'CD129','ldec':'1083B6','lceil':'CCECE','uw':('CD12C','1083B8')}}
TOP={'bdiff':'CD0C4','bceil':'CCEC5','bdec':'1083A4','ldiff':'CD0C5','ldec':'1083A6','lceil':'CCEC6','uw':('CD0C8','1083A8'),'mep':'CD0CB','dec':'1083AA'}
DX_TOP=json.load(open('build_log.json'))['dx']
for hn,H in HALLS.items():
    dx=db[H['mep']].dxf.insert.x-db[H['dec']].dxf.insert.x
    mv,st,sk=stretch((-74900,-67000,H['band'][0],H['band'][1]),-dx,0,hall_sel(H['cd']),hn+'-shift')
    # vertical fix of the boxed lower diffuser (concentric): stretch its branch below ys
    dy=db[H['dec']].dxf.insert.y-db[H['mep']].dxf.insert.y
    mx0=db[H['mep']].dxf.insert.x
    def lowsel(e,mn,mx_):
        L=e.dxf.layer
        return L in('DUCT-送风中心线','DUCT-送风管','DUCT-送风管端线','DUCT-送风法兰','DUCT-送风标注','DUCT-排风风口') or (L=='hvac-hide')
    mv2,st2,sk2=stretch((mx0-700,mx0+1500,H['band'][0],H['ys']),0,dy,lowsel,hn+'-lowdy')
    LOG['halls'][hn]={'dx':dx,'dy_fix':dy,'moved':len(mv),'stretched':len(st),'stretched_h':st,'skipped':sk,'dy_moved':len(mv2),'dy_stretched':st2,'dy_skipped':sk2}
    print(hn,'dx',round(dx,1),'moved',len(mv),'stretched',len(st),st,'skipped',sk,'| dy',round(dy,1),len(mv2),st2,sk2)
for ch,dh in (('CCECC','1083B2'),('CCED0','1083BA')):
    e=db[ch]; e.dxf.insert=Vec3(db[dh].dxf.insert); LOG['modified'][ch]='ceiling copy snapped to decorative centre (boxed lower)'
# ---------- branch reroute (upper-left middle group) ----------
NECK=['CDCF6','CDCF7','CDCF8','CDCF9','CDCFA']
ELB=['CDD06','CDCFB','CDCFF','CDD00','CDD01','CDD02','CDD03','CDD04','CDD05','CDD07','CDD08','CDCFC','CDCFD','CDCFE','CDD09','CDD0A']
COLLAR=['CDD06','CDCFB','CDCFF']; CEND=['CDD03','CDD09']
VST=['CDCF1','CDCF2','CDCF5']; VTOP=['CDCF4']
def geo(e):
    t=e.dxftype()
    if t=='LINE': return [e.dxf.start,e.dxf.end]
    if t=='ARC': return [e.dxf.center,Vec3(e.dxf.radius,e.dxf.start_angle,e.dxf.end_angle)]
    raise Exception(t)
cands=[e for e in m if e.dxf.layer.startswith('DUCT-送风') and e.dxftype() in('LINE','ARC')]
def find(h,ox,oy):
    e=db[h]; g=geo(e); t=e.dxftype()
    for c in cands:
        if not c.is_alive: continue
        if c.dxftype()!=t or c.dxf.layer!=e.dxf.layer: continue
        gc=geo(c)
        if t=='LINE':
            if all((gc[i]-(g[i]+Vec3(ox,oy,0))).magnitude<0.5 for i in (0,1)): return c
        else:
            if (gc[0]-(g[0]+Vec3(ox,oy,0))).magnitude<0.5 and (gc[1]-g[1]).magnitude<0.05: return c
    return None
def centre(ins):
    e=db[ins]; b=bbox.extents([e]); return (b.extmin+b.extmax)/2
def reroute(hn,cfg,ox,oy):
    mp={}
    for h in set(NECK+ELB+VST+VTOP):
        c=find(h,ox,oy) if (ox,oy)!=(0,0) else db[h]
        if c is None: raise Exception('nomatch %s %s'%(hn,h))
        mp[h]=c
    dif=db[cfg['bdiff']]; P=Vec3(dif.dxf.insert); C=centre(cfg['bdec']); C0=centre(cfg['bdiff'])
    Pn=Vec3(C.x+(P.x-C0.x),C.y+(P.y-C0.y),P.z)   # keep block offset insert->centre
    ddy=Pn.y-P.y
    info={'mep_centre_before':[round(C0.x,1),round(C0.y,1)],'dec_centre':[round(C.x,1),round(C.y,1)],'offset_before':[round(C0.x-C.x,1),round(C0.y-C.y,1)]}
    # delete straight neck
    for h in NECK: LOG['deleted'].append(mp[h].dxf.handle); m.delete_entity(mp[h])
    # elbow up/down by ddy
    for h in ELB: mp[h].translate(0,ddy,0); LOG['modified'][mp[h].dxf.handle]='elbow dy'
    for h in VTOP: mp[h].translate(0,ddy,0); LOG['modified'][mp[h].dxf.handle]='vtop dy'
    for h in VST:
        e=mp[h]; s,t=e.dxf.start,e.dxf.end
        if s.y>t.y: e.dxf.start=Vec3(s.x,s.y+ddy,s.z)
        else: e.dxf.end=Vec3(t.x,t.y+ddy,t.z)
        LOG['modified'][e.dxf.handle]='vstraight stretch'
    arc=mp['CDD07']; arcend_x=arc.dxf.center.x-arc.dxf.radius*0  # centre x is arc end x (arc 0..90 => end at angle 90 -> x=cx)
    arcend_x=arc.dxf.center.x
    if Pn.x<arcend_x-0.01:
        for h in COLLAR:
            e=mp[h]; s,t=e.dxf.start,e.dxf.end
            if s.x<t.x: e.dxf.start=Vec3(Pn.x,s.y,s.z)
            else: e.dxf.end=Vec3(Pn.x,t.y,t.z)
            LOG['modified'][e.dxf.handle]='collar stretch'
        endx=Pn.x; info['collar_mm']=round(arcend_x-Pn.x,1); info['overlap_mm']=0
    else:
        for h in COLLAR: LOG['deleted'].append(mp[h].dxf.handle); m.delete_entity(mp[h])
        endx=arcend_x; info['collar_mm']=0; info['overlap_mm']=round(Pn.x-arcend_x,1)
    for h in CEND:
        e=mp[h]; cx=(geo(e)[0].x+geo(e)[1].x)/2; e.translate(endx-cx,0,0); LOG['modified'][e.dxf.handle]='end/flange x'
    dif.dxf.insert=Pn; LOG['modified'][dif.dxf.handle]='diffuser moved'
    # combined-ceiling copy: same transform as decorative
    ce=db[cfg['bceil']]; de=db[cfg['bdec']]
    ce.dxf.insert=Vec3(de.dxf.insert); ce.dxf.rotation=(de.dxf.rotation+180)%360; ce.dxf.xscale=-1.0; ce.dxf.yscale=0.75
    LOG['modified'][ce.dxf.handle]='ceiling copy = decorative transform'
    C1=centre(cfg['bdiff']); C2=centre(cfg['bceil'])
    info['offset_after']=[round(C1.x-C.x,2),round(C1.y-C.y,2)]; info['ceil_offset_after']=[round(C2.x-C.x,2),round(C2.y-C.y,2)]
    info['ddy']=round(ddy,1); info['map']={k:v.dxf.handle for k,v in mp.items() if v.is_alive}
    # lower mirror group + upper wall diffuser report
    L0=centre(cfg['ldiff']); Ld=centre(cfg['ldec']); info['lower_group_offset']=[round(L0.x-Ld.x,1),round(L0.y-Ld.y,1)]
    U=db[cfg['uw'][0]].dxf.insert; Ud=db[cfg['uw'][1]].dxf.insert; info['upper_wall_offset']=[round(U.x-Ud.x,1),round(U.y-Ud.y,1)]
    Lm=db[cfg['mep']].dxf.insert; Lmd=db[cfg['dec']].dxf.insert; info['boxed_lower_wall_offset']=[round(Lm.x-Lmd.x,2),round(Lm.y-Lmd.y,2)]
    LOG['branch'][hn]=info; print(hn,info)
for hn,H in HALLS.items():
    ox=DX_TOP-LOG['halls'][hn]['dx']; oy=db[H['bdiff']].dxf.insert.y-db['CD0C4'].dxf.insert.y
    # note: top already rerouted; match against geometry before reroute -> use saved original top geometry
    reroute(hn,H,ox,oy)
reroute('top',TOP,0,0)
NL='修改-风管缩短20261119'
t=m.add_text('修改20261119(v2): 三个会议厅中部左上SAD%%C300风口移至装饰风口中心, 取消直管短节, 弯头随风口调整标高位置; 中/下会议厅同样缩短SAD1000直管并整体左移',
             dxfattribs={'layer':NL,'height':150,'insert':(-77800,2780)})
LOG['note2']=t.dxf.handle
d.saveas('out_v2.dxf'); json.dump(LOG,open('build_v2_log.json','w'),ensure_ascii=False,indent=0)
