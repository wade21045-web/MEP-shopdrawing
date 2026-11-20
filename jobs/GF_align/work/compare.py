import ezdxf,pickle,re,numpy as np,collections,math
from scipy.spatial import cKDTree
from scipy.optimize import linear_sum_assignment
from lib import walk,txt
BX=(-150000,95000,-100000,35000)
# ---------- decor
DEC=[]
TYPE={'$风口$00000092':'方形散流器','方形风口':'方形散流器','we4r5tsedrfgedrf':'方形散流器','*U498':'方形风口(圆颈)',
'$风口$00000106':'圆形旋流风口','A$Cd3d333b5':'圆形旋流风口','$风口$00000103':'球形/侧送喷口',
'A$Cef661f1d':'方形散流器','A$C68218307':'方形回风口','A$Cbec9e21a':'条形风口','*U4153':'条形风口','*U4154':'条形风口','*U4155':'条形风口',
'A$Ccff64bc9':'组合条形风口','F-地面回风口(多段线)':'地面回风口'}
def cat(t,ax,ay):
    if '圆' in t and '圆颈' not in t: return 'round'
    if '喷口' in t: return 'jet'
    if '地面' in t: return 'floor'
    a=max(ax,ay)/max(1,min(ax,ay))
    return 'linear' if a>=2.5 else 'panel'
for k,zone in [('01','GF-01'),('23','GF-02&03'),('off','Office-F00')]:
    seen=[]
    for o in pickle.load(open(f'dec_{k}.pkl','rb')):
        if not(BX[0]<o['x']<BX[1] and BX[2]<o['y']<BX[3]): continue
        if any(abs(o['x']-s[0])<20 and abs(o['y']-s[1])<20 for s in seen): continue
        seen.append((o['x'],o['y']))
        t=TYPE.get(o['name'])
        if t is None:
            a=max(o['ox'],o['oy'])/max(1,min(o['ox'],o['oy'])); t='条形风口' if a>=2.5 else '百叶/矩形风口'
        o['type']=t; o['cat']=cat(t,o['ox'],o['oy']); o['zone']=zone; DEC.append(o)
print('decor',len(DEC),collections.Counter((o['zone'],o['type']) for o in DEC))
# ---------- hvac
H=[h for h in pickle.load(open('hv_raw.pkl','rb')) if h['kind']=='INSERT' and h['root'] in('A$C5E357C2F','A$C124230B8') and h['name'].startswith('$风口$') and h['layer'].startswith('DUCT-')]
REF=[h for h in pickle.load(open('hv_raw.pkl','rb')) if h['kind']=='INSERT' and h['root']=='A$C124230B8' and (h['name']=='DIFF-WLL' or h['layer']=='天花末端点位')]
print('excluded decor-reference items inside HVAC block',len(REF))
d=ezdxf.readfile('/workspace/GF_hvac/output/GF_暖通+建筑结构底图.dxf')
LAB=[]; ROOM=[]
for root in ('A$C5E357C2F','A$C124230B8','A$C66761927'):
    for e,M,ef,ch in walk(d,d.blocks.get(root)):
        if e.dxftype() in('TEXT','MTEXT'):
            s=re.sub(r'\s+',' ',txt(e)).strip()
            if not s: continue
            p=M.transform(e.dxf.insert)
            # block-local to world: HVAC/ARCH root inserted at (8046,18544) in MS
            LAB.append((root,ef,s,p.x,p.y))
ins={e.dxf.name:e for e in d.modelspace() if e.dxftype()=='INSERT'}
def W(root,x,y):
    e=ins[root]; v=e.matrix44().transform((x,y,0)); return v.x,v.y
LAB=[(r,ef,s)+W(r,x,y) for r,ef,s,x,y in LAB]
HL=[l for l in LAB if l[0]!='A$C66761927' and re.match(r'^(SAD|RAD|EAD|FAD|SAG|RAG|EAG|FAG|SAL|RAL|LSD|LAD|SA|RA|EA|FA|A/S|VD|R/A|S/A)',l[2])]
RL=[l for l in LAB if l[0]=='A$C66761927' and ('FLOR-IDEN' in l[1] or 'AREA' in l[1] or 'ROOM' in l[1].upper())]
pickle.dump((HL,RL),open('labels.pkl','wb'))
hlT=cKDTree([(l[3],l[4]) for l in HL]); rlT=cKDTree([(l[3],l[4]) for l in RL])
HT={'$风口$00000105':'条形/百叶送风口','$风口$00000060':'方形散流器','$风口$00000097':'方形排风口','$风口$00000106':'圆形风口','$风口$00000103':'侧送/喷口',
'$风口$00000133':'百叶回风口','$风口$00000107':'方形排风口','$风口$00000144':'大型百叶风口','DIFF-WLL':'侧送风口(侧墙)'}
for h in H:
    t=HT.get(h['name'],'天花末端点位(A/S)' if h['layer']=='天花末端点位' else h['name'])
    sysn='送风' if '送风' in h['layer'] else '排风' if '排风' in h['layer'] else '回风' if '回风' in h['layer'] else ''
    h['type']=t; h['sys']=sysn
    h['cat']='round' if '圆' in t else 'jet' if '喷口' in t else ('linear' if max(h['sx'],h['sy'])/max(1,min(h['sx'],h['sy']))>=2.5 else 'panel')
    dd,j=hlT.query((h['x'],h['y']),k=3); labs=[HL[i][2] for dist,i in zip(dd,j) if dist<1500]
    h['label']=' / '.join(dict.fromkeys(labs))[:60]
print('hvac',len(H),collections.Counter(h['type'] for h in H))
# coverage
COV=[]; 
for k in ('01','23','off'): COV+= [c for c in pickle.load(open(f'cov_{k}.pkl','rb')) if BX[0]<c[0]<BX[1] and BX[2]<c[1]<BX[3]]
cT=cKDTree(COV)
def covered(x,y,r=3000): return len(cT.query_ball_point((x,y),r))>0
Hc=[h for h in H if covered(h['x'],h['y'])]; Hn=[h for h in H if not covered(h['x'],h['y'])]
Dc=[o for o in DEC]
print('hvac covered',len(Hc),'not covered',len(Hn))
# matching
A=np.array([(h['x'],h['y']) for h in Hc]); B=np.array([(o['x'],o['y']) for o in Dc])
Dm=np.hypot(A[:,None,0]-B[None,:,0],A[:,None,1]-B[None,:,1]); BIG=1e7
cost=np.where(Dm<=1500,Dm,BIG); r,c=linear_sum_assignment(cost)
pairs=[(i,j,Dm[i,j]) for i,j in zip(r,c) if Dm[i,j]<=1500]
mh={i for i,_,_ in pairs}; md={j for _,j,_ in pairs}
def room(x,y):
    dist,i=rlT.query((x,y)); return RL[i][2] if dist<12000 else ''
def zone_of(x,y):
    dd,j=cKDTree(B).query((x,y)); return Dc[j]['zone']
ISS=[]
def hd(h): return dict(h_type=h['type']+('('+h['sys']+')' if h['sys'] else ''),h_size=f"{h['sx']:.0f}×{h['sy']:.0f}",h_label=h['label'],hx=h['x'],hy=h['y'],h_block=h['name'])
def dd_(o): return dict(d_type=o['type'],d_size=f"{min(o['ox'],o['oy']):.0f}×{max(o['ox'],o['oy']):.0f}",dx=o['x'],dy=o['y'],d_block=o['name'],zone=o['zone'])
stat=collections.Counter()
for i,j,dist in pairs:
    h=Hc[i]; o=Dc[j]; tm = h['cat']!=o['cat'] and not ({h['cat'],o['cat']}<= {'panel','linear'} and False)
    if dist<=100 and not tm: stat['重合']+=1; continue
    kind=[]
    if dist>100: kind.append('位置偏差')
    if tm: kind.append('类型不符')
    stat['+'.join(kind)]+=1
    ISS.append(dict(kind='+'.join(kind),dist=dist,**hd(h),**dd_(o),x=(h['x']+o['x'])/2,y=(h['y']+o['y'])/2))
for i,h in enumerate(Hc):
    if i not in mh: stat['暖通有装饰无']+=1; ISS.append(dict(kind='暖通有装饰无',dist=None,**hd(h),x=h['x'],y=h['y'],zone=zone_of(h['x'],h['y'])))
for j,o in enumerate(Dc):
    if j not in md: 
        k='装饰有暖通无' if o['cat']!='floor' else '装饰有暖通无(地面回风口)'
        stat[k]+=1; ISS.append(dict(kind=k,dist=None,**dd_(o),x=o['x'],y=o['y']))
HT_=cKDTree(np.array([(h['x'],h['y']) for h in H]))
for s in ISS:
    s['room']=room(s['x'],s['y'])
    s['note']=''
    if s['kind'].startswith('装饰有暖通无') and HT_.query((s['x'],s['y']))[0]>8000: s['note']='8m范围内暖通图无任何风口，可能暖通未覆盖此区域'
    if s.get('dist') and s['dist']>1000: s['note']='偏差>1m，配对可能不是同一风口，请核实'
    if s['kind']=='暖通有装饰无' and len(cT.query_ball_point((s['x'],s['y']),1500))==0: s['note']='1.5m内无任何装饰天花点位，可能为装饰未表达区域(核实)'
# sort by zone then position, number
ISS.sort(key=lambda s:(s.get('zone',''),-round(s['y']/5000),s['x']))
for n,s in enumerate(ISS,1): s['no']=f'K{n:03d}'
pickle.dump(dict(Hc=Hc,Dc=Dc,ISS=ISS,stat=stat,Hn=Hn,H=H,DEC=DEC,pairs=[(i,j,dist) for i,j,dist in pairs]),open('result.pkl','wb'))
print(stat); print('issues',len(ISS))
print('dist of pairs',sorted(round(p[2]) for p in pairs))
