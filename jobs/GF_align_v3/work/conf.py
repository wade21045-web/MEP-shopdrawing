import ezdxf,pickle,re,collections,numpy as np
from ezdxf import bbox, path as EP
from ezdxf.math import Matrix44
from shapely.geometry import LineString,Polygon,MultiPoint,Point
from shapely.strtree import STRtree
from scipy.spatial import cKDTree
from lib import walk
d=ezdxf.readfile('v3_after.dxf'); m=d.modelspace()
BG=pickle.load(open('bg_conf.pkl','rb')); V=pickle.load(open('v3_after.pkl','rb'))
HL,RL=pickle.load(open('labels_v3.pkl','rb')); rlT=cKDTree([(l[3],l[4]) for l in RL])
def room(x,y):
    dist,i=rlT.query((x,y)); return RL[i][2][:40] if dist<12000 else ''
PLAN=(-140000,25000,-75000,19500)
def inplan(c): return PLAN[0]<c[0]<PLAN[1] and PLAN[2]<c[1]<PLAN[3] and not (c[0]<-100000 and c[1]>14000)
def flat(e):
    out=[]
    if e.dxftype()=='INSERT':
        for x,M,ef,ch in walk(d,[e]):
            try: p=EP.make_path(x).transform(M)
            except Exception: continue
            for sp in p.sub_paths():
                v=[(q.x,q.y) for q in sp.flattening(5)]
                if len(v)>1: out.append(v)
        return out
    try: p=EP.make_path(e)
    except Exception: return out
    for sp in p.sub_paths():
        v=[(q.x,q.y) for q in sp.flattening(5)]
        if len(v)>1: out.append(v)
    return out
# ---- background
WALLS=[LineString([tuple(a),tuple(b)]) for a,b,e in BG['NW']]; WNEW=list(BG['newseg']); WLAY=[e for a,b,e in BG['NW']]
WT=STRtree(WALLS)
COLS=[Polygon(v).buffer(0) for v,e in BG['COL']]; CLAY=[e for v,e in BG['COL']]
CT=STRtree(COLS)
BEAMS=[LineString([tuple(a),tuple(b)]) for a,b,e in BG['BEAM']]; BT=STRtree(BEAMS)
# ---- terminal ids
CHn={c['id']:np.array(c['new']) for c in V['CH']}
QH=[(q['id'],np.array(q['c'])) for q in V['Q'] if q['kind'].startswith('暖通')]
def tid(c):
    best=None
    for k,p in list(CHn.items())+QH:
        dd=np.hypot(*(p-c))
        if dd<400 and (best is None or dd<best[0]): best=(dd,k)
    return best[1] if best else '(已重合/未改)'
ISS=[]
def add(kind,sev,c,hv,bg,src,note):
    ISS.append(dict(kind=kind,sev=sev,c=np.array(c,float),room=room(*c),hv=hv,bg=bg,src=src,note=note))
# ---- terminals
for e in m:
    L=e.dxf.layer; t=e.dxftype()
    is_t=(t=='INSERT' and e.dxf.name.startswith('$风口$') and L.startswith('DUCT-')) or (L=='天花末端点位' and t in('ARC','LWPOLYLINE'))
    if not is_t: continue
    pts=[p for v in flat(e) for p in v]
    if len(pts)<3: continue
    hull=MultiPoint(pts).convex_hull
    c=np.array(hull.centroid.coords[0])
    if not inplan(c): continue
    core=hull.buffer(-30) if hull.area>10000 else hull
    if core.is_empty: continue
    nm=e.dxf.name if t=='INSERT' else '弧形条缝'
    hv=f"{tid(c)} {L} {nm}"
    ws=[i for i in WT.query(core) if WALLS[i].intersects(core)]
    if ws:
        new=any(WNEW[i] for i in ws); lays=sorted(set(WLAY[i] for i in ws))
        add('风口与墙体重叠','高',c,hv,'/'.join(lays)[:60],'新底图新增/移位墙体' if new else '新旧底图均有此墙',
            '风口外形与墙线相交，需移位或调整装饰点位')
    cs=[i for i in CT.query(core) if COLS[i].intersects(core)]
    if cs: add('风口与柱重叠','高',c,hv,'/'.join(sorted(set(CLAY[i] for i in cs))),'结构柱(新底图叠加)','风口落在柱截面内，需移位')
    bs=[i for i in BT.query(core) if BEAMS[i].intersects(core)]
    if bs and not ws and not cs: add('风口与梁边线重叠(平面)','低',c,hv,'BEAM','结构L01梁(新底图叠加)','平面上风口与梁边线重叠，核对梁底标高与吊顶/风口安装高度及支管接口')
# ---- ducts
DL=re.compile(r'^DUCT-.*管$')
segs=[]
for e in m:
    if e.dxftype()=='LINE' and DL.match(e.dxf.layer):
        a=(e.dxf.start.x,e.dxf.start.y); b=(e.dxf.end.x,e.dxf.end.y)
        if inplan(((a[0]+b[0])/2,(a[1]+b[1])/2)) and np.hypot(a[0]-b[0],a[1]-b[1])>20: segs.append((LineString([a,b]),e.dxf.layer))
# duct x column
hits=collections.defaultdict(list)
for ls,L in segs:
    for i in CT.query(ls):
        if COLS[i].buffer(-10).intersects(ls): hits[i].append(L)
for i,Ls in hits.items():
    c=np.array(COLS[i].centroid.coords[0]); add('风管与柱冲突','高',c,'/'.join(sorted(set(Ls))),CLAY[i],'结构柱(新底图叠加)' if CLAY[i].startswith('COLU') else '建筑混凝土柱/墙','风管外轮廓线穿过柱截面，需改线/翻弯')
# duct x new walls
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
        c=P[g].mean(0); Ls=sorted(set(X[i][2] for i in g)); W=sorted(set(X[i][3] for i in g))
        add('风管穿越新增/移位墙体','中',c,'/'.join(Ls)[:60],'/'.join(W)[:60],'新底图新增/移位墙体',f'风管轮廓与新底图墙线交叉{len(g)}处：需核对墙体开洞/套管，防火墙需设防火阀；如墙体位置变化导致风管/风口所在房间改变，需复核')
# ---- FCU vs walls/columns
fl=[e for e in m if e.dxftype()=='LINE' and e.dxf.layer=='EQ-风机盘管']
pts=[];own=[]
for i,e in enumerate(fl):
    a=np.array([e.dxf.start.x,e.dxf.start.y]); b=np.array([e.dxf.end.x,e.dxf.end.y]); k=max(1,int(np.linalg.norm(b-a)//40))
    for t in np.linspace(0,1,k+1): pts.append(a+(b-a)*t); own.append(i)
pts=np.array(pts); own=np.array(own); par=list(range(len(fl)))
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
    if core.is_empty: continue
    cs=[i for i in CT.query(core) if COLS[i].intersects(core)]
    if cs: add('风机盘管与柱冲突','高',c,'EQ-风机盘管',CLAY[cs[0]],'结构柱(新底图叠加)','风机盘管外形与柱截面重叠')
    ws=[i for i in WT.query(core) if WALLS[i].intersects(core) and WNEW[i]]
    if ws: add('风机盘管与新增/移位墙体冲突','高',c,'EQ-风机盘管','/'.join(sorted(set(WLAY[i] for i in ws)))[:60],'新底图新增/移位墙体','风机盘管外形与新底图墙线相交，需移位')
ISS.sort(key=lambda s:({'高':0,'中':1,'低':2}[s['sev']],s['kind'],-round(s['c'][1]/5000),s['c'][0]))
for n,s in enumerate(ISS,1): s['id']=f'B{n:03d}'
# ---- markers
if '调整-新底图冲突' not in d.layers: d.layers.add('调整-新底图冲突',color=200)
for s in ISS:
    x,y=s['c']; r=500
    m.add_lwpolyline([(x,y+r),(x-0.87*r,y-0.5*r),(x+0.87*r,y-0.5*r)],close=True,dxfattribs={'layer':'调整-新底图冲突'})
    m.add_text(s['id'],height=250,dxfattribs={'layer':'调整-新底图冲突','style':'CJK'}).set_placement((x+450,y-450))
print(collections.Counter((s['kind'],s['src']) for s in ISS))
pickle.dump(ISS,open('conf.pkl','wb'))
d.saveas('/workspace/GF_align_v3/output/GF_暖通风口调整_新底图.dxf'); print('saved')
