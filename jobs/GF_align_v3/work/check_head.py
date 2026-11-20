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
