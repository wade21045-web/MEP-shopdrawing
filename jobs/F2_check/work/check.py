import ezdxf,pickle,re,math,collections,numpy as np,json,time
from ezdxf import bbox, path as EP
from ezdxf.math import Matrix44,Vec3
from ezdxf.addons.importer import Importer
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree
from sigs import bhash
t0=time.time()
OFF=pickle.load(open('off_dec.pkl','rb'))
d=ezdxf.readfile('merged.dxf'); m=d.modelspace()
nM0=len(m)
ACDH={o['h'] for o in pickle.load(open('hv_ACD.pkl','rb'))['H']}
print('loaded',time.time()-t0,flush=True)
# ---------------- HVAC terminals
HT={'$风口$00000105':'条形/百叶风口','$风口$00000060':'方形散流器','$风口$00000097':'方形风口(排)','$风口$00000137':'方形风口(块137)',
'$风口$00000101':'加压送风口','$电动风口$00000009':'电动加压送风口'}
def blk_geom(e):
    b=d.blocks.get(e.dxf.name); ents=[x for x in b if x.dxftype()!='ATTDEF']
    bl=bbox.extents(ents,fast=True); bp=b.block.dxf.base_point
    Mi=Matrix44.translate(*(-Vec3(bp)))@e.matrix44()
    c=Mi.transform(bl.center); u=Mi.transform_direction((1,0,0)); w=Mi.transform_direction((0,1,0))
    pts=[]
    for x in ents:
        try:
            for sp in EP.make_path(x).transform(Mi).sub_paths():
                v=np.array([(q.x,q.y) for q in sp.flattening(5)])
                if len(v)>1: pts.append(v)
        except Exception: pass
    A=np.vstack(pts)
    return np.array([c.x,c.y]),bl.size.x*math.hypot(u.x,u.y),bl.size.y*math.hypot(w.x,w.y),math.degrees(math.atan2(u.y,u.x))%360,pts,A.min(0),A.max(0)
H=[]
for e in m:
    if e.dxftype()=='INSERT' and '风口' in e.dxf.name and e.dxf.layer.startswith('DUCT-'):
        c,ox,oy,rot,pts,lo,hi=blk_geom(e); L=e.dxf.layer; nm=e.dxf.name
        base=re.sub(r'(\$\d{8})\d+$',r'\1',nm)  # renamed copies
        sysn='加压送风' if '加压' in L else '送风' if '送风' in L else '排风' if '排风' in L else '回风' if '回风' in L else '新风' if '新风' in L else ''
        fam='wall' if base in('$风口$00000101','$电动风口$00000009') else 'linear' if base=='$风口$00000105' else 'square'
        H.append(dict(e=e,h=e.dxf.handle,src='ACD' if e.dxf.handle in ACDH else 'B',name=nm,layer=L,c=c,ox=ox,oy=oy,rot=rot,type=HT.get(base,base),sys=sysn,fam=fam,pts=pts,lo=lo,hi=hi))
print('HVAC',len(H),collections.Counter((h['src'],h['type']) for h in H))
# labels
LT=[]
for e in m:
    if e.dxftype() in('TEXT','MTEXT') and (e.dxf.layer.startswith('DUCT-') and '标注' in e.dxf.layer or e.dxf.layer in('00AC-TXT','M_AX_CV_EG_TX')):
        try: LT.append(((e.plain_text() if e.dxftype()=='MTEXT' else e.dxf.text).strip(),e.dxf.insert.x,e.dxf.insert.y))
        except Exception: pass
lT=cKDTree([(x,y) for s,x,y in LT])
for h in H:
    dd,j=lT.query(h['c'],k=3); h['label']=' / '.join(dict.fromkeys(LT[i][0] for di,i in zip(dd,j) if di<1500 and LT[i][0]))[:60]
P=pickle.load(open('prep.pkl','rb')); RL=P['RL']; rlT=cKDTree([(x,y) for L,s,x,y in RL])
def room(x,y):
    dist,i=rlT.query((x,y)); return RL[i][1].replace('\n',' ')[:40]+('' if dist<6000 else '(附近)') if dist<12000 else ''
def area(c,src=None):
    x,y=c
    if src=='B': return 'B区-酒店'
    if x<-62000 and y<300500: return 'ACD-西南斜翼'
    if x<-32000: return 'ACD-中部'
    return 'ACD-东北'
# ---------------- decor
raw=pickle.load(open('dec_raw.pkl','rb'))
DEC=[]; grp=collections.defaultdict(list)
DT={'方形风口':'方形风口','$风口$00000092':'方形散流器(符号)','$轴流风机$00000011':'换气扇(轴流风机)','$电动风口$00000009':'电动加压送风口','$风口$00000101':'加压送风口'}
for o in raw:
    if o['name']=='DIFF-WLL':
        for k,g in grp.items():
            if k[0]==o['chain'] and any(np.hypot(o['x']-q['x'],o['y']-q['y'])<300 for q in g): g.append(o); break
        else: grp[(o['chain'],len(grp))].append(o)
        continue
    DEC.append(dict(name=o['name'],type=DT[o['name']],c=np.array([o['x'],o['y']]),ox=o['ox'],oy=o['oy'],rot=o['rot'],pts=o['pts'],fam='wall' if '加压' in DT[o['name']] else 'square'))
for k,g in grp.items():
    A=np.vstack([v for o in g for v in o['pts']])
    DEC.append(dict(name='A/E标记('+g[0]['chain'][0]+')',type='排风口(A/E符号)',c=A.mean(0),ox=np.ptp(A[:,0]),oy=np.ptp(A[:,1]),rot=g[0]['rot'],pts=[v for o in g for v in o['pts']],fam='square'))
# dedupe
keep=[]
for o in DEC:
    if any(np.hypot(*(o['c']-q['c']))<20 and o['name']==q['name'] for q in keep): continue
    keep.append(o)
print('decor',len(DEC),'->',len(keep)); DEC=keep
cT=cKDTree(P['cov'])
Hc=[h for h in H if cT.query_ball_point(h['c'],3000)]
B=np.array([o['c'] for o in DEC])
for h in H: h['area']=area(h['c'],h['src'])
hT=cKDTree([h['c'] for h in H])
for o in DEC:
    dd,j=hT.query(o['c']); o['area']=H[j]['area']
print('DEC',len(DEC),collections.Counter(o['type'] for o in DEC),'Hc',len(Hc))
FAMCN={'linear':'条形/条缝','square':'方形/矩形','wall':'侧墙/加压送风口'}
# ---------------- matching (same as GF)
nH,nD=len(Hc),len(DEC)
A_=np.array([h['c'] for h in Hc])
Dm=np.hypot(A_[:,None,0]-B[None,:,0],A_[:,None,1]-B[None,:,1])
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
print('pairs',len(pairs),collections.Counter(p[3] for p in pairs),flush=True)
# ================= annotation (same layers/colors as GF)
LAYS=[('核对-装饰风口(参照)',6),('核对-位置偏差',1),('核对-形式不一致',30),('核对-装饰有暖通无',4),('核对-暖通有装饰无',3),('核对-待确认',2),('核对-引线',1),('核对-编号',7),('核对-装饰底图(参照)',8)]
for n,c in LAYS:
    if n not in d.layers: d.layers.add(n,color=c)
if 'CJK' not in d.styles: d.styles.add('CJK',font='simhei.ttf')
for o in DEC:
    for v in o['pts']: m.add_lwpolyline(v.tolist(),dxfattribs={'layer':'核对-装饰风口(参照)'})
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
def hsize(h): return f"{min(h['ox'],h['oy']):.0f}×{max(h['ox'],h['oy']):.0f}"
dsize=hsize
ROWS=[]; hid={}
order=sorted(range(len(H)),key=lambda i:(-round(H[i]['c'][1]/5000),H[i]['c'][0]))
for n,i in enumerate(order,1): hid[id(H[i])]=f'H{n:03d}'
pm={p[0]:p for p in pairs}; md={p[1] for p in pairs}
hci={id(h):k for k,h in enumerate(Hc)}
MARK=[]
for i in order:
    h=H[i]; no=hid[id(h)]; c=h['c']
    row=dict(no=no,zone=h['area'],src=h['src'],room=room(*c),htype=h['type']+(f"({h['sys']})" if h['sys'] else ''),hform=FAMCN[h['fam']],hsize=hsize(h),hblock=h['name'],hlabel=h.get('label',''),hx=c[0],hy=c[1],
             dtype='',dform='',dsize='',dx='',dy='',dist='',issues=[],note=[])
    dup=[g for g in H if g is not h and np.hypot(*(g['c']-c))<20]
    k=hci.get(id(h))
    if k is None:
        row['issues'].append('暖通有装饰无'); row['note'].append('3m内无装饰天花点位(不在装饰图范围)，未核对')
        cloud(h['lo'],h['hi'],'核对-暖通有装饰无'); txt(f'{no} 暖通有装饰无(不在装饰图范围)',h['hi']+[300,0],'核对-暖通有装饰无'); MARK.append(c)
        ROWS.append(row); continue
    if k not in pm:
        row['issues'].append('暖通有装饰无'+('(重复图元)' if dup else ''))
        row['note'].append('3m内无未对应的装饰风口；建议取消、由装饰补设或指定位置'+('；与另一暖通风口完全重叠' if dup else ''))
        cloud(h['lo'],h['hi'],'核对-暖通有装饰无'); txt(f"{no} 暖通有装饰无{'(重复)' if dup else ''}",h['hi']+[300,0],'核对-暖通有装饰无'); MARK.append(c)
        ROWS.append(row); continue
    _,j,dist,stage=pm[k]; o=DEC[j]; o['_hid']=no
    row.update(dtype=o['type'],dform=FAMCN[o['fam']],dsize=dsize(o),dblock=o['name'],dx=o['c'][0],dy=o['c'][1],dist=round(dist))
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
    if stage==2:
        row['issues'].append('待确认(二次配对1.5–3m)'); row['note'].append('原位置1.5m内无装饰风口，按最近未对应装饰风口配对，请确认'); lines.append(('核对-待确认',f'{no} 二次配对，待确认'))
    if dup: row['note'].append('与另一暖通风口完全重叠(重复图元)')
    if not form and not dang and o['ox']>0 and abs(max(h['ox'],h['oy'])-max(o['ox'],o['oy']))/max(o['ox'],o['oy'])>0.25:
        row['note'].append(f'尺寸不同(暖通{hsize(h)}/装饰{dsize(o)})，仅提示')
    if not lines:
        row['issues'].append('一致'); ROWS.append(row); continue
    cloud(lo,hi,lines[0][0]); MARK.append(c)
    for q,(L_,t_) in enumerate(lines): txt(t_,tp-[0,q*300],L_)
    ROWS.append(row)
DROWS=[]; allHc=np.array([h['c'] for h in H])
dl=[j for j in range(len(DEC)) if j not in md]; dl.sort(key=lambda j:(-round(DEC[j]['c'][1]/5000),DEC[j]['c'][0]))
for n,j in enumerate(dl,1):
    o=DEC[j]; no=f'D{n:03d}'; near=np.hypot(*(allHc-o['c']).T).min()
    lo=o['c']-max(o['ox'],o['oy'],300)/2; hi=o['c']+max(o['ox'],o['oy'],300)/2
    cloud(lo,hi,'核对-装饰有暖通无'); txt(f'{no} 装饰有暖通无',hi+[300,0],'核对-装饰有暖通无'); MARK.append(o['c'])
    DROWS.append(dict(no=no,zone=o['area'],room=room(*o['c']),dtype=o['type'],dform=FAMCN[o['fam']],dsize=dsize(o),dblock=o['name'],dx=o['c'][0],dy=o['c'][1],near=round(near),
                      issue='装饰有暖通无',note=f'最近暖通风口{near:.0f}mm；请确认装饰假风口/回风口或暖通补设'))
print('rows',len(ROWS),'decor-only',len(DROWS),flush=True)
nAnn=len(m)-nM0
# ---------------- decor plan overlay as one block reference (reference only, layer frozen)
src=ezdxf.readfile('dxf/L2-大平面-升版9.2.dxf')
imp=Importer(src,d); ms_,mt_={}, {}
same=0
for b in src.blocks:
    if b.block_record.is_any_layout: continue
    if b.name in d.blocks and bhash(src,b.name,ms_)==bhash(d,b.name,mt_): imp.imported_blocks[b.name]=b.name; same+=1
BN='L2装饰平面_升版9.2(参照)'
blk=d.blocks.new(BN)
before=collections.Counter(e.dxftype() for e in src.modelspace())
imp.import_entities(src.modelspace(),blk); imp.finalize()
skippedD=sum(before.values())-len(blk)
m.add_blockref(BN,(OFF[0],OFF[1]),dxfattribs={'layer':'核对-装饰底图(参照)'})
d.layers.get('核对-装饰底图(参照)').freeze()
print('decor overlay ents',len(blk),'skipped',skippedD,'blocks reused',same,flush=True)
used=set()
for e in d.entitydb.values():
    xd=getattr(e,'xdata',None)
    if xd:
        for a in list(xd.data.keys()): used.add(a)
for a in used:
    if a not in d.appids:
        try: d.appids.new(a)
        except Exception: pass
d.saveas('check.dxf')
pickle.dump(dict(ROWS=ROWS,DROWS=DROWS,nH=len(H),nHc=len(Hc),nDEC=len(DEC),npairs=len(pairs),pairstage=collections.Counter(p[3] for p in pairs),MARK=MARK,nAnn=nAnn,decor_overlay=len(blk),decor_skipped=skippedD,
    DECc=[(o['type'],o['area'],o['c']) for o in DEC]),open('check.pkl','wb')); print('saved',time.time()-t0)
