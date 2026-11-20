import ezdxf,pickle,re,math,sys,collections,numpy as np
from ezdxf import bbox, path as EP
from ezdxf.math import Matrix44,Vec3
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree
from lib import walk
MODE='check'
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
# ================= CHECK-ONLY annotation =================
from shapely.geometry import LineString,Polygon,MultiPoint
from shapely.strtree import STRtree
LAYS=[('核对-装饰风口(参照)',6),('核对-位置偏差',1),('核对-形式不一致',30),('核对-装饰有暖通无',4),('核对-暖通有装饰无',3),('核对-弧形风口',200),('核对-待确认',2),('核对-引线',1),('核对-新底图冲突',210),('核对-编号',7)]
for n,c in LAYS:
    if n not in d.layers: d.layers.add(n,color=c)
if 'CJK' not in d.styles: d.styles.add('CJK',font='simhei.ttf')
exec(open('check_decor.py').read().replace("'装饰-风口'","'核对-装饰风口(参照)'"))
def cloud(lo,hi,layer,arc=300):
    lo=np.asarray(lo)-250; hi=np.asarray(hi)+250; pts=[]
    for a,b in [((lo[0],lo[1]),(hi[0],lo[1])),((hi[0],lo[1]),(hi[0],hi[1])),((hi[0],hi[1]),(lo[0],hi[1])),((lo[0],hi[1]),(lo[0],lo[1]))]:
        a=np.array(a);b=np.array(b); L=np.hypot(*(b-a)); n=max(1,int(L//arc))
        for k in range(n): q=a+(b-a)*k/n; pts.append((q[0],q[1],0,0,-0.5))
    m.add_lwpolyline(pts,format='xyseb',close=True,dxfattribs={'layer':layer})
def txt(s,p,layer,h=200):
    m.add_text(s,height=h,dxfattribs={'layer':layer,'style':'CJK'}).set_placement((float(p[0]),float(p[1])))
def ang_long(rot,ox,oy): return (rot+(0 if ox>=oy else 90))%180
def compass(v):
    a=np.degrees(np.arctan2(v[1],v[0]))%360
    names=['右(东)','右上(东北)','上(北)','左上(西北)','左(西)','左下(西南)','下(南)','右下(东南)']
    return names[int(((a+22.5)%360)//45)]
def hsize(h): return '弧形' if h['cat']=='arc' else f"{min(h['ox'],h['oy']):.0f}×{max(h['ox'],h['oy']):.0f}"
def dsize(o): return '弧形' if o['cat']=='arc' else f"{min(o['ox'],o['oy']):.0f}×{max(o['ox'],o['oy']):.0f}"
def zone_of(c):
    j=np.argmin(np.hypot(*(B-c).T)); return DEC[j]['zone']
ROWS=[]; hid={}
order=sorted(range(len(H)),key=lambda i:(-round(H[i]['c'][1]/5000),H[i]['c'][0]))
for n,i in enumerate(order,1): hid[id(H[i])]=f'H{n:03d}'
pm={p[0]:p for p in pairs}; md={p[1] for p in pairs}
hci={id(h):k for k,h in enumerate(Hc)}
for i in order:
    h=H[i]; no=hid[id(h)]; c=h['c']
    row=dict(no=no,zone='',room=room(*c),htype=h['type']+(f"({h['sys']})" if h['sys'] else ''),hform=FAMCN[h['fam']],hsize=hsize(h),hblock=h['name'],hlabel=h.get('label',''),hx=c[0],hy=c[1],
             dtype='',dform='',dsize='',dx='',dy='',dist='',issues=[],note=[])
    k=hci.get(id(h))
    if k is None:
        row['zone']=''; row['issues'].append('暖通有装饰无'); row['note'].append('3m内无装饰天花点位(不在装饰图范围)，未核对')
        cloud(h['lo'],h['hi'],'核对-暖通有装饰无'); txt(f'{no} 暖通有装饰无(不在装饰图范围)',h['hi']+[300,0],'核对-暖通有装饰无')
        ROWS.append(row); continue
    if k not in pm:
        dup=[g for g in Hc if g is not h and np.hypot(*(g['c']-c))<20]
        row['zone']=zone_of(c); row['issues'].append('暖通有装饰无'+('(重复图元)' if dup else ''))
        row['note'].append('3m内无未对应的装饰风口；建议取消、由装饰补设或指定位置'+('；与另一暖通风口完全重叠' if dup else ''))
        lay='核对-弧形风口' if h['cat']=='arc' else '核对-暖通有装饰无'
        cloud(h['lo'],h['hi'],lay); txt(f"{no} 暖通有装饰无{'(重复)' if dup else ''}",h['hi']+[300,0],lay)
        ROWS.append(row); continue
    _,j,dist,stage=pm[k]; o=DEC[j]; o['_hid']=no
    row.update(zone=o['zone'],dtype=o['type'],dform=FAMCN[o['fam']],dsize=dsize(o),dblock=o['name'],dx=o['c'][0],dy=o['c'][1],dist=round(dist))
    form=h['fam']!=o['fam']
    dang=0
    if not form and h['fam']=='linear' and max(h['ox'],h['oy'])/max(1,min(h['ox'],h['oy']))>=1.5:
        dang=(ang_long(o['rot'],o['ox'],o['oy'])-ang_long(h['rot'],h['ox'],h['oy'])+90)%180-90
        if abs(dang)<5: dang=0
    lo=np.minimum(h['lo'],o['c']-300); hi=np.maximum(h['hi'],o['c']+300); tp=hi+[300,0]; lines=[]
    v=o['c']-c
    if dist>100:
        row['issues'].append('位置偏差'); s=f"偏差{dist:.0f}mm→装饰在{compass(v)} (dx{v[0]:+.0f}, dy{v[1]:+.0f})"; row['note'].append(s); lines.append(('核对-位置偏差',f'{no} {s}'))
        m.add_line(tuple(c),tuple(o['c']),dxfattribs={'layer':'核对-引线','lineweight':13})
    if form:
        row['issues'].append('形式不一致'); s=f"形式：暖通{FAMCN[h['fam']]} {hsize(h)} / 装饰{FAMCN[o['fam']]} {dsize(o)}"; row['note'].append(s); lines.append(('核对-形式不一致',f'{no} {s}'))
    if dang:
        row['issues'].append('条缝方向不一致'); s=f'条缝方向差{dang:+.0f}°'; row['note'].append(s); lines.append(('核对-形式不一致',f'{no} {s}'))
    if h['cat']=='arc' or o['cat']=='arc':
        if lines: row['issues'].append('弧形风口'); lines=[('核对-弧形风口',t) for _,t in lines]
    if stage==2:
        row['issues'].append('待确认(二次配对1.5–3m)'); row['note'].append('原位置1.5m内无装饰风口，按最近未对应装饰风口配对，请确认'); lines.append(('核对-待确认',f'{no} 二次配对，待确认'))
    if not form and not dang and dist>0 and o['fam']!='arc' and h['ox'] and abs(max(h['ox'],h['oy'])-max(o['ox'],o['oy']))/max(o['ox'],o['oy'])>0.25:
        row['note'].append(f'尺寸不同(暖通{hsize(h)}/装饰{dsize(o)})，仅提示')
    if not lines:
        row['issues'].append('一致'); ROWS.append(row); continue
    cloud(lo,hi,lines[0][0])
    for q,(L_,t_) in enumerate(lines): txt(t_,tp-[0,q*300],L_)
    ROWS.append(row)
# decor-only
DLS={r:[(np.array([e.dxf.start.x,e.dxf.start.y]),np.array([e.dxf.end.x,e.dxf.end.y]),e.dxf.handle) for e in LAY[r] if e.dxftype()=='LINE' and re.match(r'DUCT-.*管$',e.dxf.layer)] for r in ROOTS}
DROWS=[]; DMID=np.array([(a_+b_)/2 for a_,b_,hd in DLS['MS']]); DMT=cKDTree(DMID)
fsegs=[e for e in m if e.dxftype()=='LINE' and e.dxf.layer=='EQ-风机盘管']
FP=cKDTree([((e.dxf.start.x+e.dxf.end.x)/2,(e.dxf.start.y+e.dxf.end.y)/2) for e in fsegs])
def plenum_here(o):
    A_=np.vstack(o['pts']); n_=0
    for k in set(DMT.query_ball_point(o['c'],np.ptp(A_,axis=0).max()/2+900)):
        a_,b_,hd=DLS['MS'][k]; ab=b_-a_; L_=np.linalg.norm(ab)
        if L_<1: continue
        t_=np.clip((A_-a_)@ab/L_**2,0,1); dd_=np.linalg.norm(a_+t_[:,None]*ab-A_,axis=1)
        if dd_.min()<700: n_+=1
    return n_>=4 and len(FP.query_ball_point(o['c'],3500))>0
allHc=np.array([h['c'] for h in H])
dl=[j for j in range(len(DEC)) if j not in md]; dl.sort(key=lambda j:(-round(DEC[j]['c'][1]/5000),DEC[j]['c'][0]))
for n,j in enumerate(dl,1):
    o=DEC[j]; no=f'D{n:03d}'; near=np.hypot(*(allHc-o['c']).T).min()
    lo=o['c']-max(o['ox'],o['oy'],300)/2; hi=o['c']+max(o['ox'],o['oy'],300)/2
    if o['cat']=='arc': A_=np.vstack(o['pts']); lo,hi=A_.min(0),A_.max(0)
    if o['cat']=='arc' and plenum_here(o):
        iss='弧形风口：装饰有、暖通仅有静压箱'; note='暖通静压箱+风机盘管已在此处，但暖通图无弧形条缝风口图形'; lay='核对-弧形风口'; t_=f'{no} 弧形条缝：暖通有静压箱无风口图形'
    else:
        iss='装饰有暖通无'+('(弧形)' if o['cat']=='arc' else ''); note=f'最近暖通风口{near:.0f}mm；请确认装饰假风口/回风口或暖通补设'; lay='核对-弧形风口' if o['cat']=='arc' else '核对-装饰有暖通无'; t_=f'{no} 装饰有暖通无'
    cloud(lo,hi,lay); txt(t_,hi+[300,0],lay)
    DROWS.append(dict(no=no,zone=o['zone'],room=room(*o['c']),dtype=o['type'],dform=FAMCN[o['fam']],dsize=dsize(o),dblock=o['name'],dx=o['c'][0],dy=o['c'][1],near=round(near),issue=iss,note=note))
print('rows',len(ROWS),'decor-only',len(DROWS))
# ================= background conflicts on original HVAC =================
BG=pickle.load(open('bg_conf.pkl','rb'))
WALLS=[LineString([tuple(a),tuple(b)]) for a,b,e in BG['NW']]; WNEW=list(BG['newseg']); WLAY=[e for a,b,e in BG['NW']]; WT=STRtree(WALLS)
COLS=[Polygon(v).buffer(0) for v,e in BG['COL']]; CLAY=[e for v,e in BG['COL']]; CT=STRtree(COLS)
BEAMS=[LineString([tuple(a),tuple(b)]) for a,b,e in BG['BEAM']]; BT=STRtree(BEAMS)
HT_=cKDTree(allHc)
def tid(c):
    dd,i=HT_.query(c); return hid[id(H[i])] if dd<500 else ''
ISS=[]
def add(kind,sev,c,hv,bg,src,note): ISS.append(dict(kind=kind,sev=sev,c=np.array(c,float),room=room(*c),hv=hv,bg=bg,src=src,note=note))
for h in H:
    pts=[p for v in h['pts'] for p in v]
    if len(pts)<3: continue
    hull=MultiPoint([tuple(p) for p in pts]).convex_hull; core=hull.buffer(-30) if hull.area>10000 else hull
    if core.is_empty: continue
    hv=f"{hid[id(h)]} {h['layer']} {h['name']}"; c=h['c']
    ws=[i for i in WT.query(core) if WALLS[i].intersects(core)]
    if ws: add('风口与墙体重叠','高',c,hv,'/'.join(sorted(set(WLAY[i] for i in ws)))[:60],'新底图新增/移位墙体' if any(WNEW[i] for i in ws) else '新旧底图均有此墙','风口外形与墙线相交')
    cs=[i for i in CT.query(core) if COLS[i].intersects(core)]
    if cs: add('风口与柱重叠','高',c,hv,'/'.join(sorted(set(CLAY[i] for i in cs))),'结构柱(新底图叠加)','风口落在柱截面内')
    bs=[i for i in BT.query(core) if BEAMS[i].intersects(core)]
    if bs and not ws and not cs: add('风口与梁边线重叠(平面)','低',c,hv,'BEAM','结构L01梁(新底图叠加)','核对梁底标高与吊顶/风口安装高度')
DL=re.compile(r'^DUCT-.*管$'); segs=[]
for e in m:
    if e.dxftype()=='LINE' and DL.match(e.dxf.layer):
        a=(e.dxf.start.x,e.dxf.start.y); b=(e.dxf.end.x,e.dxf.end.y)
        if inplan(((a[0]+b[0])/2,(a[1]+b[1])/2)) and np.hypot(a[0]-b[0],a[1]-b[1])>20: segs.append((LineString([a,b]),e.dxf.layer))
hits=collections.defaultdict(list)
for ls,L in segs:
    for i in CT.query(ls):
        if COLS[i].buffer(-10).intersects(ls): hits[i].append(L)
for i,Ls in hits.items(): add('风管与柱冲突','高',np.array(COLS[i].centroid.coords[0]),'/'.join(sorted(set(Ls))),CLAY[i],'柱(新底图)','风管外轮廓穿过柱截面')
X=[]
for ls,L in segs:
    for i in WT.query(ls):
        if WNEW[i] and WALLS[i].intersects(ls):
            p=WALLS[i].intersection(ls)
            if p.geom_type=='Point': X.append((p.x,p.y,L,WLAY[i]))
if X:
    P=np.array([(x,y) for x,y,_,_ in X]); par=list(range(len(X)))
    def f(i):
        while par[i]!=i: par[i]=par[par[i]]; i=par[i]
        return i
    for i,j in cKDTree(P).query_pairs(1500): par[f(i)]=f(j)
    G=collections.defaultdict(list)
    for i in range(len(X)): G[f(i)].append(i)
    for g in G.values():
        add('风管穿越新增/移位墙体','中',P[g].mean(0),'/'.join(sorted(set(X[i][2] for i in g)))[:60],'/'.join(sorted(set(X[i][3] for i in g)))[:60],'新底图新增/移位墙体',f'风管轮廓与新墙线交叉{len(g)}处：核对开洞/套管，防火墙需设防火阀')
pts=[];own=[]
for i,e in enumerate(fsegs):
    a=np.array([e.dxf.start.x,e.dxf.start.y]); b=np.array([e.dxf.end.x,e.dxf.end.y]); k=max(1,int(np.linalg.norm(b-a)//40))
    for t in np.linspace(0,1,k+1): pts.append(a+(b-a)*t); own.append(i)
pts=np.array(pts); own=np.array(own); par=list(range(len(fsegs)))
def f(i):
    while par[i]!=i: par[i]=par[par[i]]; i=par[i]
    return i
for a,b in cKDTree(pts).query_pairs(25): par[f(own[a])]=f(own[b])
G=collections.defaultdict(list)
for k,i in enumerate(own): G[f(i)].append(k)
for g in G.values():
    Pg=pts[g]
    if len(Pg)<10: continue
    hull=MultiPoint([tuple(p) for p in Pg]).convex_hull; c=np.array(hull.centroid.coords[0])
    if not inplan(c) or hull.area<0.2e6: continue
    core=hull.buffer(-30)
    cs=[i for i in CT.query(core) if COLS[i].intersects(core)]
    if cs: add('风机盘管与柱冲突','高',c,'EQ-风机盘管',CLAY[cs[0]],'柱(新底图)','风机盘管外形与柱截面重叠')
    ws=[i for i in WT.query(core) if WALLS[i].intersects(core) and WNEW[i]]
    if ws: add('风机盘管与新增/移位墙体冲突','高',c,'EQ-风机盘管','/'.join(sorted(set(WLAY[i] for i in ws)))[:60],'新底图新增/移位墙体','风机盘管外形与新墙线相交')
ISS.sort(key=lambda s:({'高':0,'中':1,'低':2}[s['sev']],s['kind'],-round(s['c'][1]/5000),s['c'][0]))
for n,s in enumerate(ISS,1):
    s['id']=f'B{n:03d}'; x,y=s['c']; r=500
    m.add_lwpolyline([(x,y+r),(x-0.87*r,y-0.5*r),(x+0.87*r,y-0.5*r)],close=True,dxfattribs={'layer':'核对-新底图冲突'})
    txt(f"{s['id']} {s['kind']}",(x+450,y-450),'核对-新底图冲突',200)
print('conflicts',collections.Counter((s['sev'],s['kind']) for s in ISS))
# appids fix
used=set()
for e in d.entitydb.values():
    xd=getattr(e,'xdata',None)
    if xd:
        for a in list(xd.data.keys()): used.add(a)
for a in used:
    if a not in d.appids:
        try: d.appids.new(a)
        except Exception as ex: print('appid',a,ex)
print('appids added check done',len(used))
d.saveas('check.dxf')
pickle.dump(dict(ROWS=ROWS,DROWS=DROWS,ISS=ISS,nH=len(H),nHc=len(Hc),nDEC=len(DEC),npairs=len(pairs)),open('check.pkl','wb')); print('saved')
