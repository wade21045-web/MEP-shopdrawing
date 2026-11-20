import ezdxf,pickle,re,math,sys,collections,numpy as np
from ezdxf import bbox, path as EP
from ezdxf.math import Matrix44,Vec3
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree
from lib import walk
MODE=sys.argv[1]  # 'before' or 'after'
BASE='base.dxf'
d=ezdxf.readfile(BASE); m=d.modelspace()
ROOTS=['MS']
LAY={'MS':m}
OFF={'MS':np.zeros(2)}
RM={'MS':Matrix44()}
PLAN=(-140000,25000,-75000,19500)
def inplan(c): return PLAN[0]<c[0]<PLAN[1] and PLAN[2]<c[1]<PLAN[3] and not (c[0]<-100000 and c[1]>14000)
def flat(e,M):
    out=[]
    if e.dxftype()=='INSERT':
        for x,Mx,ef,ch in walk(d,[e],M=M):
            out+=flat(x,Mx)
        return out
    try: p=EP.make_path(e).transform(M)
    except Exception: return out
    for sp in p.sub_paths():
        v=np.array([(q.x,q.y) for q in sp.flattening(2)])
        if len(v)>1: out.append(v)
    return out
# ---------------- HVAC terminals
HT={'$风口$00000105':'条形/百叶风口','$风口$00000060':'方形散流器','$风口$00000097':'方形风口(排)','$风口$00000106':'圆形风口','$风口$00000103':'侧送/喷口',
'$风口$00000133':'百叶回风口','$风口$00000107':'方形风口(排)','$风口$00000144':'大型百叶风口'}
def blk_ext(name):
    b=d.blocks.get(name); bb=bbox.extents(b); bp=Vec3(b.block.dxf.base_point); return bb.size.x,bb.size.y,(bb.center-bp)
H=[]
for r in ROOTS:
    for e in LAY[r]:
        if e.dxftype()=='INSERT' and e.dxf.name.startswith('$风口$') and e.dxf.layer.startswith('DUCT-'):
            bb=bbox.extents([e]); c=np.array([bb.center.x,bb.center.y])+OFF[r]
            if not inplan(c): continue
            w,h,_=blk_ext(e.dxf.name); ox,oy=abs(w*e.dxf.xscale),abs(h*e.dxf.yscale)
            t=HT.get(e.dxf.name,e.dxf.name); L=e.dxf.layer
            sysn='送风' if '送风' in L else '排风' if '排风' in L else '回风' if '回风' in L else '新风' if '新风' in L else ''
            cat='round' if e.dxf.name=='$风口$00000106' else 'jet' if e.dxf.name=='$风口$00000103' else ('linear' if max(ox,oy)/max(1,min(ox,oy))>=2.5 else 'panel')
            H.append(dict(kind='INS',root=r,e=e,h=e.dxf.handle,name=e.dxf.name,layer=L,c=c,ox=ox,oy=oy,rot=e.dxf.rotation,type=t,sys=sysn,cat=cat,
                          pts=flat(e,RM[r]),lo=np.array([bb.extmin.x,bb.extmin.y])+OFF[r],hi=np.array([bb.extmax.x,bb.extmax.y])+OFF[r]))
# HVAC arc terminals (天花末端点位 ARC/LINE groups inside A$C124230B8)
r='MS'; ents=[e for e in m if e.dxf.layer=='天花末端点位' and e.dxftype() in('ARC','LINE')]
P=[flat(e,RM[r]) for e in ents]
par=list(range(len(ents)))
def f(i):
    while par[i]!=i: par[i]=par[par[i]]; i=par[i]
    return i
allp=np.vstack([np.vstack(p) for p in P]); own=np.concatenate([[i]*sum(len(q) for q in p) for i,p in enumerate(P)])
for a,b in cKDTree(allp).query_pairs(120): par[f(own[a])]=f(own[b])
G=collections.defaultdict(list)
for i in range(len(ents)): G[f(i)].append(i)
ARC_SKIP=[]
for g in G.values():
    if sum(ents[i].dxftype()=='ARC' for i in g)<3: ARC_SKIP.append([ents[i].dxf.handle for i in g]); continue
    pts=[q for i in g for q in P[i]]; A=np.vstack(pts); lo,hi=A.min(0),A.max(0)
    H.append(dict(kind='ARC',root=r,ents=[ents[i] for i in g],h=','.join(ents[i].dxf.handle for i in g[:2]),name='天花末端点位(弧线组)',layer='天花末端点位',c=(lo+hi)/2,ox=0,oy=0,rot=0,
                  type='弧形条缝风口',sys='',cat='arc',pts=pts,lo=lo,hi=hi))
print('HVAC',len(H),collections.Counter(h['cat'] for h in H))
# labels
HL,RL=pickle.load(open('labels_v3.pkl','rb'))
hlT=cKDTree([(l[3],l[4]) for l in HL]); rlT=cKDTree([(l[3],l[4]) for l in RL])
for h in H:
    dd,j=hlT.query(h['c'],k=3); h['label']=' / '.join(dict.fromkeys(HL[i][2] for dist,i in zip(dd,j) if dist<1500))[:60]
def room(x,y):
    dist,i=rlT.query((x,y)); return RL[i][2].replace('\n',' ')[:40] if dist<12000 else ''
# ---------------- decor
R1=pickle.load(open('result.pkl','rb'))
DEC=[o for o in R1['DEC'] if o['cat']!='floor']
for o in DEC: o['c']=np.array([o['x'],o['y']])
GEO={}
for k in ('01','23','off'): GEO[k]=pickle.load(open(f'geo_{k}.pkl','rb'))
EXTRA=pickle.load(open('extra.pkl','rb'))
DEC+=EXTRA
print('DEC',len(DEC),collections.Counter(o['cat'] for o in DEC))
# coverage
COV=[]
for k in ('01','23','off'): COV+=pickle.load(open(f'cov_{k}.pkl','rb'))
cT=cKDTree(COV)
Hc=[h for h in H if cT.query_ball_point(h['c'],3000)]; Hn=[h for h in H if not cT.query_ball_point(h['c'],3000)]
def fam_h(h):
    if h['cat']=='arc': return 'arc'
    return {'$风口$00000105':'linear','$风口$00000106':'round','$风口$00000103':'jet'}.get(h['name'],'square')
def fam_d(o):
    t=o['type']
    if o['cat'] in('arc','round','jet'): return o['cat']
    if t in('条形风口','组合条形风口'): return 'linear'
    if t=='百叶/矩形风口': return 'linear' if max(o['ox'],o['oy'])/max(1,min(o['ox'],o['oy']))>=2.5 else 'square'
    return 'square'
for h in H: h['fam']=fam_h(h)
for o in DEC: o['fam']=fam_d(o)
FAMCN={'linear':'条形/条缝','square':'方形/矩形','round':'圆形','jet':'喷口','arc':'弧形条缝'}
# ---------------- matching
def dpts(o):
    return np.vstack(o['pts']) if o['cat']=='arc' else o['c'][None,:]
def gdist(h,o):
    A=dpts(h); B=dpts(o)
    if len(A)==1 and len(B)==1: return float(np.hypot(*(A[0]-B[0])))
    if h['cat']=='arc' and o['cat']=='arc':
        return float(0.5*(cKDTree(B).query(A)[0].mean()+cKDTree(A).query(B)[0].mean()))
    return float(cKDTree(B).query(A)[0].min()) if len(B)>1 else float(cKDTree(A).query(B)[0].min())
nH,nD=len(Hc),len(DEC)
A=np.array([h['c'] for h in Hc]); B=np.array([o['c'] for o in DEC])
Dm=np.hypot(A[:,None,0]-B[None,:,0],A[:,None,1]-B[None,:,1])
for i,h in enumerate(Hc):
    for j,o in enumerate(DEC):
        if (h['cat']=='arc' or o['cat']=='arc') and Dm[i,j]<6000: Dm[i,j]=gdist(h,o)
pen=np.array([[0 if h['fam']==o['fam'] or {h['fam'],o['fam']}=={'square','linear'} else 300 for o in DEC] for h in Hc])
pairs=[]
for stage,cut in ((1,1500),(2,3000)):
    mh={p[0] for p in pairs}; md={p[1] for p in pairs}
    ri=[i for i in range(nH) if i not in mh]; cj=[j for j in range(nD) if j not in md]
    if not ri or not cj: break
    sub=Dm[np.ix_(ri,cj)]+pen[np.ix_(ri,cj)]; cost=np.where(Dm[np.ix_(ri,cj)]<=cut,sub,1e9)
    r_,c_=linear_sum_assignment(cost)
    for a,b in zip(r_,c_):
        if cost[a,b]<1e9: pairs.append((ri[a],cj[b],float(Dm[ri[a],cj[b]]),stage))
print('pairs',len(pairs),collections.Counter(p[3] for p in pairs))
pickle.dump(dict(H=H,Hc=Hc,Hn=Hn,DEC=DEC,pairs=pairs),open('v2_match.pkl','wb')) if False else None
# ---------------- layers / decor copy
for n,c in [('装饰-风口',6),('调整前-暖通风口',8),('调整前-暖通风管',8),('调整-修改云线',1),('调整-编号',1),('调整-风口连接软管',3),('调整-待定',30),('调整前-暖通设备及水管',8)]:
    if n not in d.layers: d.layers.add(n,color=c)
for ln in ('调整前-暖通风口','调整前-暖通风管','调整前-暖通设备及水管'):
    if 'DASHED' not in d.linetypes:
        try: d.linetypes.add('DASHED',pattern=[600.0,400.0,-200.0],description='Dashed __ __')
        except Exception: pass
    if 'DASHED' in d.linetypes: d.layers.get(ln).dxf.linetype='DASHED'
if 'CJK' not in d.styles: d.styles.add('CJK',font='simhei.ttf')
for key,zone in [('01','GF01'),('23','GF0203'),('off','OFF')]:
    Gk=GEO[key]; bmap={}
    for n,polys in Gk['blocks'].items():
        nm='DEC_'+zone+'_'+re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]','_',n)
        if nm not in d.blocks:
            b=d.blocks.new(nm)
            for v in polys: b.add_lwpolyline(v.tolist(),dxfattribs={'layer':'0','color':0})
        bmap[n]=nm
    for it in Gk['items']:
        if it['o']['cat']=='floor': continue
        if it['block']:
            ins=m.add_blockref(bmap[it['block']],(0,0),dxfattribs={'layer':'装饰-风口'}); ins.transform(Matrix44([x for r_ in it['M'] for x in r_]))
        else: m.add_lwpolyline(it['pts'].tolist(),close=True,dxfattribs={'layer':'装饰-风口'})
for o in DEC:
    if o.get('extra'):
        for v in o['pts']: m.add_lwpolyline(v.tolist(),dxfattribs={'layer':'装饰-风口'})
# ---------------- modifications
TPL={'square':'$风口$00000060','linear':'$风口$00000105','round':'$风口$00000106','jet':'$风口$00000103'}
CH=[]; Q=[]
EQ={r:[] for r in ROOTS}
for r in ROOTS:
    for e in LAY[r]:
        if e.dxf.layer in('EQ-风机盘管','M-EQPM','EQ-新风机') and e.dxftype()=='LINE':
            EQ[r].append(((e.dxf.start.x+e.dxf.end.x)/2+OFF[r][0],(e.dxf.start.y+e.dxf.end.y)/2+OFF[r][1]))
EQT={r:cKDTree(EQ[r]) for r in ROOTS if EQ[r]}
termh=set(h['h'] for h in H if h['kind']=='INS')
def inwin(p,lo,hi): return lo[0]<=p[0]<=hi[0] and lo[1]<=p[1]<=hi[1]
# ---- FCU clusters & terminal branch centerlines (pre-modification)
FCU={}
for r in ROOTS:
    segs=[e for e in LAY[r] if e.dxftype()=='LINE' and e.dxf.layer=='EQ-风机盘管']
    if not segs: FCU[r]=None; continue
    n=len(segs); par=list(range(n))
    def ff(i):
        while par[i]!=i: par[i]=par[par[i]]; i=par[i]
        return i
    pts=[];own=[]
    for i,e in enumerate(segs):
        a_=np.array([e.dxf.start.x,e.dxf.start.y]); b_=np.array([e.dxf.end.x,e.dxf.end.y]); k=max(1,int(np.linalg.norm(b_-a_)//40))
        for t in np.linspace(0,1,k+1): pts.append(a_+(b_-a_)*t); own.append(i)
    pts=np.array(pts); own=np.array(own)
    for a,b_ in cKDTree(pts).query_pairs(25): par[ff(own[a])]=ff(own[b_])
    lab=np.array([ff(i) for i in own])
    FCU[r]=dict(pts=pts,lab=lab,tree=cKDTree(pts))
FCULAB={r:[(np.array([t.dxf.insert.x,t.dxf.insert.y]),t.dxf.text) for t in LAY[r] if t.dxftype()=='TEXT' and t.dxf.layer=='DIM-风机盘管'] for r in ROOTS}
def find_cl(r,lo,hi):
    best=None
    for e in LAY[r]:
        if e.dxftype()=='LINE' and e.dxf.layer.startswith('DUCT-') and '中心线' in e.dxf.layer:
            s_,en=e.dxf.start,e.dxf.end
            for a,b_ in ((s_,en),(en,s_)):
                if inwin(a,lo,hi) and not inwin(b_,lo,hi):
                    L=(b_-a).magnitude
                    if best is None or L>best[0]: best=(L,np.array([a.x,a.y]),np.array([b_.x,b_.y]))
    return best
for h in H:
    h['cl']=None; h['fcu']=None
    if h['kind']!='INS': continue
    r=h['root']; lo=h['lo']-OFF[r]-150; hi=h['hi']-OFF[r]+150
    cl=find_cl(r,lo,hi); h['cl']=cl
    if cl and FCU[r]:
        idx=FCU[r]['tree'].query_ball_point(cl[2],400)
        if idx:
            labs=set(FCU[r]['lab'][idx]); 
            if len(labs)>=1: h['fcu']=frozenset(labs)
FCU_USE=collections.Counter()
for h in H:
    if h['fcu']:
        for l in h['fcu']: FCU_USE[(h['root'],l)]+=1
ASM_L=('管道','PIPE','VANNE','接头','HVAC-P-VA','VRV','M_AX_CV','EQ-','M-EQPM','DIM-风机盘管','DUCT-','7-MCF')
CLS={r:[(np.array([e.dxf.start.x,e.dxf.start.y]),np.array([e.dxf.end.x,e.dxf.end.y])) for e in LAY[r] if e.dxftype()=='LINE' and e.dxf.layer.startswith('DUCT-') and '中心线' in e.dxf.layer] for r in ROOTS}
def on_main(r,F,v):
    for a_,b_ in CLS[r]:
        ab=b_-a_; L=np.linalg.norm(ab)
        if L<500: continue
        t=np.clip((F-a_)@ab/L**2,0,1); dist=np.linalg.norm(a_+t*ab-F)
        if dist<40 and abs(ab@v)/L>0.9 and 0.02<t<0.98: return True
    return False
DLS={r:[(np.array([e.dxf.start.x,e.dxf.start.y]),np.array([e.dxf.end.x,e.dxf.end.y]),e.dxf.handle) for e in LAY[r] if e.dxftype()=='LINE' and re.match(r'DUCT-.*管$',e.dxf.layer)] for r in ROOTS}
def ray_hits(r,P):
    out=[]
    for dvec in ((1,0),(-1,0),(0,1),(0,-1)):
        dvec=np.array(dvec,float); best=None
        for a_,b_,hd in DLS[r]:
            if np.linalg.norm((a_+b_)/2-P)>4000: continue
            e_=b_-a_; M_=np.array([dvec,-e_]).T
            if abs(np.linalg.det(M_))<1e-9: continue
            t,s_=np.linalg.solve(M_,a_-P)
            if t>0 and 0<=s_<=1 and t<2500 and (best is None or t<best[0]): best=(t,hd)
        out.append(best[1] if best else None)
    return out
def in_box(r,C,N):
    a=ray_hits(r,C); b=ray_hits(r,N)
    return all(a) and a==b
def assembly_move(h,Lv,with_fcu):
    r=h['root']; cl=h['cl']; C0=cl[1]; u=(cl[2]-cl[1]); Lb=np.linalg.norm(u); u=u/Lb; v=np.array([-u[1],u[0]])
    tl=np.vstack([h['lo'],h['hi'],[h['lo'][0],h['hi'][1]],[h['hi'][0],h['lo'][1]]])-OFF[r]
    Q=[tl,cl[2][None,:]]
    if with_fcu:
        F=FCU[r]; Q.append(F['pts'][np.isin(F['lab'],list(h['fcu']))])
    Q=np.vstack(Q); pu=(Q-C0)@u; pv=(Q-C0)@v
    if with_fcu: u0,u1,v0,v1=pu.min()-150,pu.max()+150,pv.min()-150,pv.max()+150
    else:
        hv=max(np.abs(((tl-C0)@v)).max(),200)+100
        u0,u1,v0,v1=pu.min()-150,Lb+60,-hv,hv
    if with_fcu:
        EQL=[(np.array([e.dxf.start.x,e.dxf.start.y]),np.array([e.dxf.end.x,e.dxf.end.y])) for rr in ROOTS for e in LAY[rr] if e.dxftype()=='LINE' and e.dxf.layer=='EQ-风机盘管']
        bu=(u0,u1,v0,v1)
        for _ in range(6):
            ch_=False
            for a_,b_ in EQL:
                qa=((a_-C0)@u,(a_-C0)@v); qb=((b_-C0)@u,(b_-C0)@v)
                ia=u0<=qa[0]<=u1 and v0<=qa[1]<=v1; ib=u0<=qb[0]<=u1 and v0<=qb[1]<=v1
                if ia!=ib:
                    q=qb if ia else qa
                    nu0,nu1,nv0,nv1=min(u0,q[0]-30),max(u1,q[0]+30),min(v0,q[1]-30),max(v1,q[1]+30)
                    if nu1-nu0<=bu[1]-bu[0]+2000 and nv1-nv0<=bu[3]-bu[2]+2000: u0,u1,v0,v1=nu0,nu1,nv0,nv1; ch_=True
            if not ch_: break
    def win(p):
        q=np.array([p[0],p[1]])-C0; a=q@u; b_=q@v; return u0<=a<=u1 and v0<=b_<=v1
    cnt=collections.Counter(); old=[]; dv=Vec3(Lv[0],Lv[1],0); fl=[]
    for rr in ROOTS:
        if not with_fcu and rr!=r: continue
        b=LAY[rr]
        for e in list(b):
            L=e.dxf.layer
            if e.dxf.handle in termh: continue
            if not L.startswith(ASM_L) or '立管' in L or '风口' in L: continue
            if not with_fcu and not (L.startswith('DUCT-') or L=='hvac-hide'): continue
            t=e.dxftype()
            try:
                if t=='LINE':
                    si,ei=win(e.dxf.start),win(e.dxf.end)
                    if si or ei:
                        old.append((L,flat(e,RM[rr])))
                        if si: e.dxf.start=e.dxf.start+dv
                        if ei: e.dxf.end=e.dxf.end+dv
                        cnt[(L,'整体移动' if si and ei else '拉伸')]+=1
                elif t=='LWPOLYLINE':
                    pts=list(e.get_points('xyseb')); hit=[win(p) for p in pts]
                    if any(hit):
                        old.append((L,flat(e,RM[rr])))
                        e.set_points([(p[0]+Lv[0],p[1]+Lv[1])+tuple(p[2:]) if k else p for p,k in zip(pts,hit)],format='xyseb')
                        cnt[(L,'整体移动' if all(hit) else '拉伸')]+=1
                elif t in('INSERT','TEXT','MTEXT'):
                    if win(e.dxf.insert):
                        if t=='TEXT' and L=='DIM-风机盘管': fl.append(e.dxf.text)
                        old.append((L,flat(e,RM[rr]) if t=='INSERT' else [])); e.translate(Lv[0],Lv[1],0); cnt[(L,'整体移动')]+=1
                else:
                    vv=np.vstack(flat(e,Matrix44())); ins=[win(p) for p in vv]
                    if all(ins): old.append((L,flat(e,RM[rr]))); e.translate(Lv[0],Lv[1],0); cnt[(L,'整体移动')]+=1
                    elif any(ins): cnt[(L,'部分在窗口内-未改')]+=1
            except Exception: pass
    return cnt,old,fl
def inwin(p,lo,hi): return lo[0]<=p[0]<=hi[0] and lo[1]<=p[1]<=hi[1]
def stretch(r,lo,hi,delta,skip,Rm=None,win=None,partial=True,jog=None):
    """AutoCAD STRETCH in root-block local coords (rigid: p->Rm@p+delta)"""
    b=LAY[r]; cnt=collections.Counter(); old=[]
    if Rm is None: Rm=np.eye(2)
    M4=Matrix44([Rm[0,0],Rm[1,0],0,0, Rm[0,1],Rm[1,1],0,0, 0,0,1,0, delta[0],delta[1],0,1])
    def mp(p): q=Rm@np.array([p[0],p[1]])+delta; return Vec3(q[0],q[1],p[2] if len(p)>2 else 0)
    inwin=(lambda p,lo_,hi_: win(p)) if win else globals()['inwin']
    for e in list(b):
        L=e.dxf.layer
        if e.dxf.handle in skip or e.dxf.handle in termh: continue
        if not (L.startswith('DUCT-') or L=='hvac-hide') or '风口' in L: continue
        if '立管' in L:
            try:
                v=np.vstack(flat(e,Matrix44()))
                if any(inwin(p,lo,hi) for p in v): cnt[(L,'立管-未移动')]+=1
            except Exception: pass
            continue
        t=e.dxftype()
        if t=='LINE':
            s_,en=e.dxf.start,e.dxf.end; si,ei=inwin(s_,lo,hi),inwin(en,lo,hi)
            if (si or ei) and not partial and not (si and ei): cnt[(L,'部分在窗口内-未改')]+=1; continue
            if si or ei:
                old+=flat(e,RM[r])
                if jog is not None and (si!=ei):
                    ju,J=jog; dd_=np.array([en.x-s_.x,en.y-s_.y]); Ll=np.linalg.norm(dd_)
                    if Ll>J+100 and abs(dd_@ju)/Ll>0.95:
                        a_,b_=(s_,en) if si else (en,s_)   # a_ inside (terminal end)
                        di=np.array([b_.x-a_.x,b_.y-a_.y])/Ll; P=Vec3(a_.x+di[0]*J,a_.y+di[1]*J,0)
                        b.add_line(P,b_,dxfattribs={'layer':L,'color':e.dxf.get('color',256),'linetype':e.dxf.get('linetype','BYLAYER')})
                        if si: e.dxf.start=mp(s_); e.dxf.end=P
                        else: e.dxf.end=mp(en); e.dxf.start=P
                        cnt[(L,'乙字弯(偏移段)')]+=1; continue
                if si: e.dxf.start=mp(s_)
                if ei: e.dxf.end=mp(en)
                cnt[(L,'整体移动' if si and ei else '拉伸')]+=1
        elif t=='LWPOLYLINE':
            pts=list(e.get_points('xyseb')); hit=[inwin(p,lo,hi) for p in pts]
            if any(hit) and not partial and not all(hit): cnt[(L,'部分在窗口内-未改')]+=1; continue
            if any(hit):
                old+=flat(e,RM[r])
                if all(hit): e.transform(M4)
                else:
                    e.set_points([tuple(mp(p))[:2]+tuple(p[2:]) if k else p for p,k in zip(pts,hit)],format='xyseb')
                cnt[(L,'整体移动' if all(hit) else '拉伸')]+=1
        elif t in('ARC','CIRCLE'):
            try: v=np.vstack(flat(e,Matrix44()))
            except Exception: continue
            ins=[inwin(p,lo,hi) for p in v]
            if all(ins): old+=flat(e,RM[r]); e.transform(M4); cnt[(L,'整体移动')]+=1
            elif any(ins): cnt[(L,'弧线部分在窗口内-未改')]+=1
        elif t=='INSERT':
            if inwin(e.dxf.insert,lo,hi): old+=flat(e,RM[r]); e.transform(M4); cnt[(L,'整体移动')]+=1
    return cnt,old
def rigid_fit(A,B):
    """fit A (hvac arc pts) onto B (decor arc pts): returns R,t world"""
    TB=cKDTree(B); best=None
    ca,cb=A.mean(0),B.mean(0)
    ua=np.linalg.svd(A-ca)[2][0]; ub=np.linalg.svd(B-cb)[2][0]
    for flip in (0,np.pi):
        th=np.arctan2(ub[1],ub[0])-np.arctan2(ua[1],ua[0])+flip
        R=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]]); t=cb-R@ca
        for _ in range(40):
            Q=A@R.T+t; dd,j=TB.query(Q); Y=B[j]
            mx,my=A.mean(0),Y.mean(0); Hm=(A-mx).T@(Y-my); U,S,Vt=np.linalg.svd(Hm); R=Vt.T@U.T
            if np.linalg.det(R)<0: Vt[-1]*=-1; R=Vt.T@U.T
            t=my-R@mx
        res=TB.query(A@R.T+t)[0].mean()
        if best is None or res<best[0]: best=(res,R,t)
    return best
TX={r:[e for e in LAY[r] if e.dxftype() in('TEXT','MTEXT') and e.dxf.layer.startswith('DUCT-') and '标注' in e.dxf.layer] for r in ROOTS}
allHc=np.array([h['c'] for h in H])
def move_labels(h,delta):
    r=h['root']; n=0; s=[]
    for t in TX[r]:
        p=np.array([t.dxf.insert.x,t.dxf.insert.y])+OFF[r]
        if np.hypot(*(p-h['c']))<1200:
            j=np.argmin(np.hypot(*(allHc-p).T))
            if H[j] is h:
                if MODE=='after': t.dxf.insert=t.dxf.insert+Vec3(delta[0],delta[1],0)
                n+=1; s.append((t.plain_text() if t.dxftype()=='MTEXT' else t.dxf.text))
    return n,s
def cloud(lo,hi,arc=350):
    lo=lo-300; hi=hi+300
    pts=[]
    for a,b in [((lo[0],lo[1]),(hi[0],lo[1])),((hi[0],lo[1]),(hi[0],hi[1])),((hi[0],hi[1]),(lo[0],hi[1])),((lo[0],hi[1]),(lo[0],lo[1]))]:
        a=np.array(a);b=np.array(b); L=np.hypot(*(b-a)); n=max(1,int(L//arc))
        for k in range(n): q=a+(b-a)*k/n; pts.append((q[0],q[1],0,0,-0.5))
    m.add_lwpolyline(pts,format='xyseb',close=True,dxfattribs={'layer':'调整-修改云线'})
def ang_long(rot,ox,oy): return (rot+(0 if ox>=oy else 90))%180
cid=0; qid=0
def nid(p):
    global cid,qid
    if p=='C': cid+=1; return f'C{cid:03d}'
    qid+=1; return f'Q{qid:03d}'
mh={p[0] for p in pairs}; md={p[1] for p in pairs}
def zone_of(c):
    j=np.argmin(np.hypot(*(B-c).T)); return DEC[j]['zone']
pairs.sort(key=lambda p:(DEC[p[1]]['zone'],-round(DEC[p[1]]['c'][1]/5000),DEC[p[1]]['c'][0]))
for i,j,dist,stage in pairs:
    h=Hc[i]; o=DEC[j]; r=h['root']; off=OFF[r]
    form = h['fam']!=o['fam']
    dang=0
    if not form and h['fam']=='linear' and o['fam']=='linear' and max(h['ox'],h['oy'])/max(1,min(h['ox'],h['oy']))>=1.5:
        dang=(ang_long(o['rot'],o['ox'],o['oy'])-ang_long(h['rot'],h['ox'],h['oy'])+90)%180-90
        if abs(dang)<5: dang=0
    if dist<=100 and not form and dang==0: continue
    rec=dict(id=nid('C'),stage=stage,zone=o['zone'],room=room(*o['c']),h_type=h['type']+(f"({h['sys']})" if h['sys'] else ''),h_block=h['name'],h_layer=h['layer'],h_label=h['label'],
             old=h['c'].copy(),new=o['c'].copy(),dist=float(np.hypot(*(o['c']-h['c']))),d_type=o['type'],d_size=(f"{min(o['ox'],o['oy']):.0f}×{max(o['ox'],o['oy']):.0f}" if o['cat']!='arc' else f"弧长约{sum(np.hypot(*np.diff(v,axis=0).T).sum() for v in o['pts'][:1]):.0f}"),
             d_block=o['name'],form=('' if not form else f"{FAMCN[h['fam']]}→{FAMCN[o['fam']]}"),rot=dang,notes=[],duct='',labels='',flex='',eq='')
    delta=o['c']-h['c']
    # original grey copy
    if MODE=='after':
        for v in h['pts']: m.add_lwpolyline(v.tolist(),dxfattribs={'layer':'调整前-暖通风口'})
    lo_w=h['lo']-150; hi_w=h['hi']+150
    if h['cat']=='arc': lo_w=h['lo']-450; hi_w=h['hi']+450
    if MODE=='after':
        b=LAY[r]
        # --- terminal
        if h['kind']=='INS':
            e=h['e']
            if form and o['fam']=='arc':
                for v in o['pts']: b.add_lwpolyline((v-off).tolist(),dxfattribs={'layer':h['layer']})
                b.delete_entity(e); rec['notes'].append('原风口块删除，按装饰弧形条缝外形重画(多段线)')
            else:
                if form:
                    tn=TPL[o['fam']]; tw,th,_=blk_ext(tn); e.dxf.name=tn
                    if o['fam'] in('round','jet'): s=max(o['ox'],o['oy'])/max(tw,th); e.dxf.xscale=s; e.dxf.yscale=s
                    else: e.dxf.xscale=o['ox']/tw; e.dxf.yscale=o['oy']/th
                    e.dxf.rotation=o['rot']; rec['notes'].append(f'改用{tn}({HT.get(tn)})，外形尺寸按装饰{o["ox"]:.0f}×{o["oy"]:.0f}，规格/风量需复核')
                elif dang: e.dxf.rotation=(e.dxf.rotation+dang)%360; rec['notes'].append(f'旋转{dang:+.0f}°与装饰条缝方向一致')
                bb=bbox.extents([e]); c=np.array([bb.center.x,bb.center.y])+off
                e.dxf.insert=e.dxf.insert+Vec3(*(o['c']-c),0)
                bb=bbox.extents([e]); newc=np.array([bb.center.x,bb.center.y])+off
                rec['resid']=float(np.hypot(*(newc-o['c'])))
                if EQT.get(r) is not None:
                    nl=np.array([bb.extmin.x,bb.extmin.y])+off+50; nh=np.array([bb.extmax.x,bb.extmax.y])+off-50
                    hits=[p for p in EQT[r].query_ball_point(o['c'],3000) if inwin(EQ[r][p],nl,nh)]
                    if hits: rec['eq']='新位置与风机盘管/设备图形重叠，需复核'
        Rm=None
        if h['kind']!='INS':
            for e in h['ents']: b.delete_entity(e)
            for v in o['pts']: b.add_lwpolyline((v-off).tolist(),dxfattribs={'layer':'天花末端点位'})
            res,Rw,tw=rigid_fit(np.vstack(h['pts']),np.vstack(o['pts']))
            Rm=Rw; delta_l=Rw@off+tw-off; ang=np.degrees(np.arctan2(Rw[1,0],Rw[0,0]))
            rec['notes'].append(f'原弧形风口删除，按装饰弧形条缝重画；静压箱及支管末端按刚体变换(旋转{ang:+.1f}°)随风口移动，拟合残差{res:.0f}mm；静压箱长度/弧度需复核')
            rec['rot']=float(ang)
        # --- ducts stretch
        if Rm is None:
            asm=None
            if h['cl'] is not None:
                u=h['cl'][2]-h['cl'][1]; u=u/np.linalg.norm(u); vv_=np.array([-u[1],u[0]])
                lat=float(delta@vv_); ax_=float(delta@u)
                rec['axial']=ax_; rec['lateral']=lat
                fcu_ok=bool(h['fcu']) and all(FCU_USE[(r,l)]==1 for l in h['fcu'])
                main_ok=(not h['fcu']) and on_main(r,h['cl'][2],vv_)
                if abs(lat)>50 and main_ok:
                    Lv=lat*vv_; c1,o1,fl=assembly_move(h,Lv,False)
                    for L_,vs in o1:
                        for v_ in vs: m.add_lwpolyline(v_.tolist(),dxfattribs={'layer':'调整前-暖通风管'})
                    rec['notes'].append(f'支管连同主风管上的接口沿主风管平移{abs(lat):.0f}mm')
                    asm=c1; lo_w=lo_w+Lv; hi_w=hi_w+Lv; delta=ax_*u
                elif abs(lat)>50:
                    if fcu_ok:
                        Lv=lat*vv_; c1,o1,fl=assembly_move(h,Lv,True)
                        for L_,vs in o1:
                            for v_ in vs: m.add_lwpolyline(v_.tolist(),dxfattribs={'layer':'调整前-暖通风管' if L_.startswith('DUCT') else '调整前-暖通设备及水管'})
                        rec['eq']=f"风机盘管{'/'.join(sorted(set(fl)))[:30] or '(未读到编号)'}连同送风支管横移{abs(lat):.0f}mm；"+'；'.join(f'{L} {k}×{n}' for (L,k),n in sorted(c1.items()) if not L.startswith('DUCT'))
                        asm=c1
                        lo_w=lo_w+Lv; hi_w=hi_w+Lv; delta=ax_*u
                    else:
                        rec['notes'].append(f"横向偏移{abs(lat):.0f}mm：{'该风机盘管带多个风口' if h['fcu'] else '支管首段末端不在风机盘管或直主风管上(有弯头)'}，未整体平移，支管末端斜向拉伸，需复核")
            jog=None; inbox=False
            if h['cl'] is not None and abs(rec.get('lateral',0))>50 and asm is None:
                inbox=in_box(r,h['c']-off,o['c']-off)
                if inbox:
                    rec['notes']=[n for n in rec['notes'] if '斜向' not in n]+['风口在原静压箱/风管箱体范围内移动，箱体不变']
                else:
                    J=max(abs(rec['lateral']),300.0); jog=(u,J)
                    rec['notes']=[n.replace('支管末端斜向拉伸','支管末端做乙字弯(偏移段长%.0f)'%J) for n in rec['notes']]
            if inbox: cnt,old=collections.Counter({('—','箱内移动'):1}),[]
            else: cnt,old=stretch(r,lo_w-off,hi_w-off,delta,set(),jog=jog)
            if asm: cnt=cnt+collections.Counter({k:v for k,v in asm.items() if k[0].startswith('DUCT')})
            delta=o['c']-h['c']
        else:
            A=np.vstack(h['pts'])-off; mu=A.mean(0); Vt=np.linalg.svd(A-mu)[2]; pr=(A-mu)@Vt.T; hl=np.ptp(pr[:,0])/2; hw=np.ptp(pr[:,1])/2
            cu=(pr.max(0)+pr.min(0))/2
            def win(p,mu=mu,Vt=Vt,hl=hl,hw=hw,cu=cu):
                q=(np.array([p[0],p[1]])-mu)@Vt.T-cu; return abs(q[0])<=hl+250 and abs(q[1])<=hw+250
            cnt,old=stretch(r,None,None,delta_l,set(),Rm,win,partial=False)
            c_new=o['c']; c_old=h['c']
            m.add_lwpolyline([tuple(c_old),tuple(c_new)],dxfattribs={'layer':'调整-风口连接软管'})
            m.add_text(f'风机盘管出风静压段→新静压箱 接驳风管/软管 L≈{np.hypot(*(c_new-c_old)):.0f} 需复核',height=150,dxfattribs={'layer':'调整-风口连接软管','style':'CJK'}).set_placement(tuple((c_old+c_new)/2+np.array([0,150])))
        for v in old: m.add_lwpolyline(v.tolist(),dxfattribs={'layer':'调整前-暖通风管'})
        rec['duct']='；'.join(f'{L} {k}×{n}' for (L,k),n in sorted(cnt.items()))
        ends=sum(n for (L,k),n in cnt.items() if '端线' in L or '法兰' in L or k=='拉伸')
        if h['kind']!='INS':
            rec['flex']='静压箱随弧形风口整体移动；风机盘管未动，风机盘管出风段与新静压箱之间需接驳风管/软管(图中绿色示意线)，需复核'
        elif not ends:
            L_=float(np.hypot(*delta))
            m.add_lwpolyline([tuple(h['c']),tuple(o['c'])],dxfattribs={'layer':'调整-风口连接软管'})
            m.add_text(f'软管/短支管 L≈{L_:.0f}',height=150,dxfattribs={'layer':'调整-风口连接软管','style':'CJK'}).set_placement(tuple((h['c']+o['c'])/2+np.array([0,120])))
            rec['flex']=f'风口不在支管末端，原接口→新位置用软管/短支管连接 L≈{L_:.0f}mm'+('（>1.5m，建议改为硬支管，需复核）' if L_>1500 else '')
        else:
            perp=None
            rec['flex']='支管末端随风口拉伸(STRETCH)，无需软管'
        if any(k=='弧线部分在窗口内-未改' for (L,k) in cnt): rec['notes'].append('窗口内有部分弧形风管弯头未改，需复核')
        if any(k=='立管-未移动' for (L,k) in cnt): rec['notes'].append('风口旁有风管立管，立管未移动，接口需复核')
        if not form and o['fam']!='arc' and h['ox'] and o['ox'] and abs(max(h['ox'],h['oy'])-max(o['ox'],o['oy']))/max(o['ox'],o['oy'])>0.25: rec['notes'].append(f"尺寸与装饰不一致(暖通{h['ox']:.0f}×{h['oy']:.0f} / 装饰{o['ox']:.0f}×{o['oy']:.0f})，未改规格")
    n_l,s_l=move_labels(h,delta); rec['labels']=f'{n_l}条标注随动' + (': '+' | '.join(s_l)[:60] if s_l else '')
    if stage==2: rec['notes'].append('二次配对(1.5–3m)：原位置附近无装饰风口，挪至最近的未对应装饰风口，请确认')
    if rec['dist']>1000: rec['notes'].append('移动>1m')
    if MODE=='after': cloud(np.minimum(h['lo'],o['c']-300),np.maximum(h['hi'],o['c']+300))
    if MODE=='after': m.add_text(rec['id'],height=300,dxfattribs={'layer':'调整-编号','style':'CJK'}).set_placement(tuple(np.maximum(h['hi'],o['c']+300)+300))
    CH.append(rec)
for i,h in enumerate(Hc):
    if i in mh: continue
    dup=[k for k,g in enumerate(Hc) if k!=i and np.hypot(*(g['c']-h['c']))<20]
    rec=dict(id=nid('Q'),kind='暖通有装饰无'+('(重复图元)' if dup else ''),zone=zone_of(h['c']),room=room(*h['c']),c=h['c'],type=h['type']+(f"({h['sys']})" if h['sys'] else ''),block=h['name'],label=h['label'],
             note='3m内无未对应的装饰风口，未移动；建议：取消该风口，或由装饰补设风口，或指定新位置')
    Q.append(rec)
DMID=np.array([(a_+b_)/2 for a_,b_,hd in DLS['MS']]); DMT=cKDTree(DMID)
FCUP=FCU['MS']['tree'] if FCU['MS'] else None
def plenum_here(o):
    A_=np.vstack(o['pts']); n_=0
    for k in set(DMT.query_ball_point(o['c'],np.ptp(A_,axis=0).max()/2+900)):
        a_,b_,hd=DLS['MS'][k]; ab=b_-a_; L_=np.linalg.norm(ab)
        if L_<1: continue
        t_=np.clip((A_-a_)@ab/L_**2,0,1); dd_=np.linalg.norm(a_+t_[:,None]*ab-A_,axis=1)
        if dd_.min()<700: n_+=1
    f_=FCUP is not None and len(FCUP.query_ball_point(o['c'],3500))>0
    return n_>=4 and f_
for j,o in enumerate(DEC):
    if j in md: continue
    near=np.hypot(*(allHc-o['c']).T).min()
    if o['cat']=='arc' and plenum_here(o):
        rec=dict(id=nid('Q'),kind='装饰有暖通无(静压箱已就位)',zone=o['zone'],room=room(*o['c']),c=o['c'],type=o['type'],block=o['name'],label='',
                 note=f'弧形条缝处暖通已有静压箱及风机盘管(按Wade已对过的位置)，但暖通图无弧形条缝风口图形；未自行补画(不臆造)，建议暖通按装饰弧形补画条缝风口并复核静压箱长度/弧度')
        Q.append(rec); continue
    rec=dict(id=nid('Q'),kind='装饰有暖通无',zone=o['zone'],room=room(*o['c']),c=o['c'],type=o['type'],block=o['name'],label='',
             note=f'最近暖通风口{near:.0f}mm；未新增暖通风口(新增需风量计算)，请确认是否为装饰假风口/回风口或需暖通补设')
    Q.append(rec)
for h in Hn:
    Q.append(dict(id=nid('Q'),kind='不在装饰图范围',zone='',room=room(*h['c']),c=h['c'],type=h['type'],block=h['name'],label=h['label'],note='3m内无装饰天花点位，未核对'))
for q in Q:
    x,y=q['c']; m.add_circle((x,y),600,dxfattribs={'layer':'调整-待定'})
    m.add_text(q['id'],height=300,dxfattribs={'layer':'调整-待定','style':'CJK'}).set_placement((x+450,y+450))
print('changes',len(CH),'open',len(Q),collections.Counter(q['kind'] for q in Q))
out='v3_after.dxf' if MODE=='after' else 'v3_before.dxf'
d.saveas(out)
for rec in CH: rec.pop('e',None)
pickle.dump(dict(CH=CH,Q=Q,nH=len(H),nHc=len(Hc),nDEC=len(DEC),pairs=[(Hc[i]['h'],DEC[j].get('handle'),dist,st) for i,j,dist,st in pairs],
   coinc=[(Hc[i]['type'],DEC[j]['type'],DEC[j]['zone'],dist) for i,j,dist,st in pairs]),open(f'v3_{MODE}.pkl','wb'))
print('saved',out)
