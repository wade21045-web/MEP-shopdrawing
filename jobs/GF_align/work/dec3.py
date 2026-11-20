import pickle,numpy as np,collections,re
from scipy.spatial import cKDTree
R1=pickle.load(open('result.pkl','rb'))
DEC=[o for o in R1['DEC'] if o['cat']!='floor']
KN=set(o['name'] for o in R1['DEC'])
EX=re.compile(r'^\*U413$|GTFEB|GFFDG|检修口|equip_U|半球摄像机|^serg$|TwtSys|WAP|SPEAKER|[Gg]as|GAS|cctv|MKFCH|publicaddress|A\$C35197B1C|zfdgzdfsgv|asergdfgdgf|排水沟')
dT=cKDTree([(o['x'],o['y']) for o in DEC])
ZONE={'01':'GF-01','23':'GF-02&03','off':'Office-F00'}
EXTRA=[]; LOG=[]
for key in ('01','23','off'):
    out=pickle.load(open(f'prim_{key}.pkl','rb'))
    G=collections.defaultdict(list)
    for it in out:
        if it['ef']=='F-地面回风口': continue
        if any(n in KN for n in it['chain']): continue
        if any(EX.search(n) for n in it['chain']): continue
        G[(it['fr'],it['top'])].append(it)
    for (fr,top),its in G.items():
        n=len(its); par=list(range(n))
        def f(i):
            while par[i]!=i: par[i]=par[par[i]]; i=par[i]
            return i
        P=np.vstack([i['pts'] for i in its]); own=np.concatenate([[k]*len(i['pts']) for k,i in enumerate(its)])
        for a,b in cKDTree(P).query_pairs(150): par[f(own[a])]=f(own[b])
        cl=collections.defaultdict(list)
        for k in range(n): cl[f(k)].append(its[k])
        for v in cl.values():
            A=np.vstack([i['pts'] for i in v]); lo,hi=A.min(0),A.max(0); c=(lo+hi)/2
            mu=A.mean(0); U,S,Vt=np.linalg.svd(A-mu,full_matrices=False); ax=Vt[0]
            pr=(A-mu)@Vt.T; ox=np.ptp(pr[:,0]); oy=np.ptp(pr[:,1])
            if max(ox,oy)<300 or (min(ox,oy)<15): LOG.append((key,'drop-small',np.round(c),round(ox),round(oy),v[0]['chain'][-1:] if v[0]['chain'] else '-')); continue
            if max(ox,oy)>12000: LOG.append((key,'drop-huge',np.round(c),round(ox))); continue
            if dT.query(c)[0]<300: continue
            # arc test: deviation from chord of the long-axis centre line
            curved=any(i['curved'] for i in v)
            # sagitta: fit quadratic of cross-axis vs axis
            co=np.polyfit(pr[:,0],pr[:,1],2); sag=abs(co[0])*(ox/2)**2
            cat='arc' if (curved and 60<sag<=oy and ox>1000) else ('linear' if ox/max(oy,1)>=2.5 else 'panel')
            typ={'arc':'弧形条缝风口','linear':'条形风口','panel':'百叶/矩形风口'}[cat]
            rot=float(np.degrees(np.arctan2(ax[1],ax[0])))
            nm=(v[0]['chain'][-1] if v[0]['chain'] else '散线')+'('+v[0]['ef']+')'
            EXTRA.append(dict(src=key,frame=fr,name=nm,layer=v[0]['ef'],x=c[0],y=c[1],c=c,ox=float(ox),oy=float(oy),rot=rot,type=typ,cat=cat,zone=ZONE[key],
                              pts=[i['pts'] for i in v],handle=v[0]['h'],sag=float(sag),extra=True,lo=lo,hi=hi,area=float(ox*oy)))
keep=[]
for e in sorted(EXTRA,key=lambda e:-e['area']):
    if any(k['lo'][0]-50<=e['c'][0]<=k['hi'][0]+50 and k['lo'][1]-50<=e['c'][1]<=k['hi'][1]+50 for k in keep): continue
    keep.append(e)
EXTRA=keep
print(len(EXTRA),collections.Counter((e['zone'],e['cat']) for e in EXTRA))
for e in EXTRA: print(e['zone'],e['name'][:40],np.round(e['c']),round(e['ox']),round(e['oy']),e['cat'],round(e['sag']))
pickle.dump(EXTRA,open('extra.pkl','wb'))
print(collections.Counter((l[0],l[1],str(l[-1])) for l in LOG).most_common(15))
