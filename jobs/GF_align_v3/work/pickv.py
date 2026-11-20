import pickle,numpy as np,collections,json
R=pickle.load(open('check.pkl','rb'))
P=[];RM=[]
for r in R['ROWS']:
    if r['issues']!=['一致']: P.append((r['hx'],r['hy'])); RM.append(r['room'])
for r in R['DROWS']: P.append((r['dx'],r['dy'])); RM.append(r['room'])
for s in R['ISS']: P.append(tuple(s['c'])); RM.append(s['room'])
P=np.array(P,float); used=np.zeros(len(P),bool); W,Hh=26000,16000; V={}
for k in range(4):
    best=None
    for c in P[~used]:
        for ox in (0.3,0.5,0.7):
            for oy in (0.3,0.5,0.7):
                x0,y0=c[0]-W*ox,c[1]-Hh*oy
                ins=(P[:,0]>=x0)&(P[:,0]<=x0+W)&(P[:,1]>=y0)&(P[:,1]<=y0+Hh)&~used
                if best is None or ins.sum()>best[0]: best=(ins.sum(),x0,y0,ins)
    n,x0,y0,ins=best; used|=ins
    rm=collections.Counter(RM[i] for i in np.where(ins)[0] if RM[i]).most_common(2)
    name='_'.join(x[0].split(' ')[0] for x in rm)[:30].replace('/','_')
    V[f'{k+1}_{name}']=(x0,x0+W,y0,y0+Hh,f'核对标注 {k+1}：{name}（{n}处标记）')
    print(k,n,name)
json.dump(V,open('views.json','w'),ensure_ascii=False)
