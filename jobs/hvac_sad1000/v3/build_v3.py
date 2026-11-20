import ezdxf,json,math
from ezdxf.math import Vec3
from ezdxf import bbox
d=ezdxf.readfile('/workspace/hvac_sad1000/v3/v2_shop.dxf'); m=d.modelspace(); db=d.entitydb
LOG={'deleted':[],'modified':{},'res':{}}
def mod(e,why): LOG['modified'][e.dxf.handle]=why
def centre(h):
    b=bbox.extents([db[h]]); return (b.extmin+b.extmax)/2
def geo(e):
    t=e.dxftype()
    if t=='LINE': return [e.dxf.start,e.dxf.end]
    if t=='ARC': return [e.dxf.center,Vec3(e.dxf.radius,e.dxf.start_angle,e.dxf.end_angle)]
cands=[e for e in m if e.dxf.layer.startswith('DUCT-送风') and e.dxftype() in('LINE','ARC')]
def find(h,ox,oy):
    if (ox,oy)==(0,0): return db[h]
    e=db[h]; g=geo(e); t=e.dxftype()
    for c in cands:
        if not c.is_alive or c.dxftype()!=t or c.dxf.layer!=e.dxf.layer: continue
        gc=geo(c)
        if t=='LINE' and all((gc[i]-(g[i]+Vec3(ox,oy,0))).magnitude<0.5 for i in (0,1)): return c
        if t=='ARC' and (gc[0]-(g[0]+Vec3(ox,oy,0))).magnitude<0.5 and (gc[1]-g[1]).magnitude<0.05: return c
    raise Exception('nomatch '+h)
HALL={'top':{'ldiff':'CD0C5','lceil':'CCEC6','ldec':'1083A6','uw':'CD0C8','uwc':'CCEC7','uwd':'1083A8','hide':['CD150','CDD48','CDD49','CDD4A']},
      'mid':{'ldiff':'CD111','lceil':'CCECA','ldec':'1083AE','uw':'CD114','uwc':'CCECB','uwd':'1083B0'},
      'bot':{'ldiff':'CD129','lceil':'CCECE','ldec':'1083B6','uw':'CD12C','uwc':'CCECF','uwd':'1083B8'}}
# offsets of mid/bot relative to top (geometry pattern) for lower-left group
for hn in ('mid','bot'):
    H=HALL[hn]; H['ox']=db[H['ldiff']].dxf.insert.x-db['CD0C5'].dxf.insert.x; H['oy']=db[H['ldiff']].dxf.insert.y-db['CD0C5'].dxf.insert.y
HALL['top']['ox']=HALL['top']['oy']=0
# ---------- (a) lower-left side diffuser: same method as v2, mirrored ----------
NECK=['CDDC5','CDDC6','CDDC7','CDDC8','CDDC9']
ELB=['CDDD5','CDDCA','CDDCE','CDDCF','CDDD0','CDDD1','CDDD2','CDDD3','CDDD4','CDDD6','CDDD7','CDDCB','CDDCC','CDDCD','CDDD8','CDDD9']
COLLAR=['CDDD5','CDDCA','CDDCE']; CEND=['CDDD2','CDDD8']; VST=['CDDC0','CDDC1','CDDC4']; VBOT=['CDDC3']
for hn in ('mid','bot','top'):
    H=HALL[hn]
    mp={h:find(h,H['ox'],H['oy']) for h in set(NECK+ELB+VST+VBOT)}
    dif=db[H['ldiff']]; P=Vec3(dif.dxf.insert); C=centre(H['ldec']); C0=centre(H['ldiff'])
    Pn=Vec3(C.x+(P.x-C0.x),C.y+(P.y-C0.y),P.z); ddy=Pn.y-P.y
    info={'before':[round(C0.x-C.x,1),round(C0.y-C.y,1)],'ddy':round(ddy,1)}
    for h in NECK: LOG['deleted'].append(mp[h].dxf.handle); m.delete_entity(mp[h])
    for h in ELB: mp[h].translate(0,ddy,0); mod(mp[h],'LL elbow dy')
    for h in VBOT: mp[h].translate(0,ddy,0); mod(mp[h],'LL vbot dy')
    for h in VST:
        e=mp[h]; s,t=e.dxf.start,e.dxf.end
        if s.y<t.y: e.dxf.start=Vec3(s.x,s.y+ddy,s.z)
        else: e.dxf.end=Vec3(t.x,t.y+ddy,t.z)
        mod(e,'LL vstraight')
    arcx=mp['CDDD6'].dxf.center.x
    if Pn.x<arcx-0.01:
        for h in COLLAR:
            e=mp[h]; s,t=e.dxf.start,e.dxf.end
            if s.x<t.x: e.dxf.start=Vec3(Pn.x,s.y,s.z)
            else: e.dxf.end=Vec3(Pn.x,t.y,t.z)
            mod(e,'LL collar')
        endx=Pn.x; info['collar']=round(arcx-Pn.x,1); info['overlap']=0
    else:
        for h in COLLAR: LOG['deleted'].append(mp[h].dxf.handle); m.delete_entity(mp[h])
        endx=arcx; info['collar']=0; info['overlap']=round(Pn.x-arcx,1)
    for h in CEND:
        e=mp[h]; cx=(geo(e)[0].x+geo(e)[1].x)/2; e.translate(endx-cx,0,0); mod(e,'LL end x')
    dif.dxf.insert=Pn; mod(dif,'LL diffuser')
    ce=db[H['lceil']]; de=db[H['ldec']]
    ce.dxf.insert=Vec3(de.dxf.insert); ce.dxf.rotation=(de.dxf.rotation+180)%360; ce.dxf.xscale=-1.0; ce.dxf.yscale=0.75; mod(ce,'LL ceil=dec')
    C1=centre(H['ldiff']); C2=centre(H['lceil'])
    info['after']=[round(C1.x-C.x,2),round(C1.y-C.y,2)]; info['ceil_after']=[round(C2.x-C.x,2),round(C2.y-C.y,2)]
    LOG['res'][hn+'_LL']=info; print(hn,'LL',info)
# ---------- (b) upper-right wall round diffuser: shorten vertical branch ----------
def ent_pts_shift(e,f,fx=0.0):
    t=e.dxftype()
    if t=='LINE':
        s,en=e.dxf.start,e.dxf.end; e.dxf.start=Vec3(s.x+fx,s.y+f(s.y),s.z); e.dxf.end=Vec3(en.x+fx,en.y+f(en.y),en.z)
    elif t in('ARC','CIRCLE'): e.translate(fx,f(e.dxf.center.y),0)
    elif t in('INSERT','TEXT','MTEXT'): e.translate(fx,f(e.dxf.insert.y),0)
    elif t=='LWPOLYLINE':
        e.set_points([(p[0]+fx,p[1]+f(p[1]))+tuple(p[2:]) for p in e.get_points('xyseb')],format='xyseb')
    else: raise Exception('type '+t)
def branch_ents(x0,x1,y0,y1):
    out=[]
    for e in m:
        L=e.dxf.layer
        if not (L.startswith(('DUCT-送风管','DUCT-送风中心线','DUCT-送风法兰','DUCT-排风风口','DUCT-送风标注')) or L in('hvac-hide','综合末端-天花')): continue
        try: b=bbox.extents([e],fast=True)
        except Exception: continue
        if b.has_data and b.extmin.x>=x0 and b.extmax.x<=x1 and b.extmin.y>=y0 and b.extmax.y<=y1: out.append(e)
    return out
for hn,H in HALL.items():
    U=db[H['uw']]; Ud=db[H['uwd']]
    dxu=Ud.dxf.insert.x-U.dxf.insert.x; dyu=Ud.dxf.insert.y-U.dxf.insert.y
    info={'before':[round(-dxu,1),round(-dyu,1)]}
    lab=[]
    if hn=='top':
        # x fix: shift upper branch (above main top edge) right by dxu inside the cross fitting
        for e in branch_ents(-72720,-72170,1327.0,2700):
            if e.dxf.handle in('CDD80','CDD81') or e.dxf.layer in('综合末端-天花',): continue
            if e.dxf.layer=='DUCT-送风标注': continue
            e.translate(dxu,0,0); mod(e,'UR x-shift')
        for h,which in (('CDD71','end'),('CDD74','start')):
            e=db[h]; p=getattr(e.dxf,which); setattr(e.dxf,which,Vec3(p.x+dxu,p.y,p.z)); mod(e,'UR x-stretch')
        # y: remove 300 straight (1916.3-2109.5), cut 400 straight at 1600 and neck at 2140
        need=-dyu; s_neck=60.0; s_300=2109.5-1916.3; s_400=need-s_neck-s_300
        for h in ('CDD44','CDD47','CDD54'): LOG['deleted'].append(h); m.delete_entity(db[h])
        def f(y):
            if y<1600: return 0.0
            if y<1916.4: return -s_400
            if y<2109.45: return -s_400   # labels only (piece deleted)
            if y<2140: return -(s_400+s_300)
            return -(s_400+s_300+s_neck)
        ents=branch_ents(-72720,-72170,1600,2700)
        info['cuts']={'400直管':round(s_400,1),'300直管(整段取消)':round(s_300,1),'Φ300颈管':s_neck}
    else:
        y0=db[H['uw']].dxf.insert.y
        # 400 straight piece: centreline from main+750 to main+1268 approx; cut at its middle
        cut=y0-1052.0
        def f(y,c=cut,s=dyu): return s if y>c else 0.0
        ents=branch_ents(-72720,-72190,cut-5,y0+400)
        info['cuts']={'400直管':round(-dyu,1)}
    for e in ents:
        if e.dxf.layer=='DUCT-送风标注': lab.append(e); continue
        if e.dxf.layer=='综合末端-天花': continue
        ent_pts_shift(e,f); mod(e,'UR y-shorten')
    for e in lab:   # labels/leaders move as a group with the duct end they describe
        e.translate(0,dyu,0); mod(e,'UR label')
    for h in (H['uw'],H['uwc']):
        e=db[h]; e.dxf.insert=Vec3(Ud.dxf.insert); mod(e,'UR diffuser=dec')
    if hn=='top':
        for h in H['hide']: pass
    A=db[H['uw']].dxf.insert; Cc=db[H['uwc']].dxf.insert
    info['after']=[round(A.x-Ud.dxf.insert.x,2),round(A.y-Ud.dxf.insert.y,2)]
    info['labels_moved']=len(lab)
    LOG['res'][hn+'_UR']=info; print(hn,'UR',info)
NL='修改-风管缩短20261119'
t=m.add_text('修改20261119(v3): 三个会议厅左下SAD%%C300侧送风口及墙边右上圆形风口与装饰风口同心(调整弯头/缩短直管), 并保留SHOP风机盘管修改',
             dxfattribs={'layer':NL,'height':150,'insert':(-77800,2560)})
LOG['note3']=t.dxf.handle
d.saveas('/workspace/hvac_sad1000/v3/v3.dxf'); json.dump(LOG,open('/workspace/hvac_sad1000/v3/v3_log.json','w'),ensure_ascii=False,indent=0)
