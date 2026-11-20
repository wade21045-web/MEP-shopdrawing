import ezdxf,collections,numpy as np,re,sys,pickle
from ezdxf import bbox
from lib import walk
f,tag=sys.argv[1],sys.argv[2]
d=ezdxf.readfile(f); m=d.modelspace()
pos=collections.defaultdict(list)
for e in m:
    if e.dxftype()=='INSERT' and ('风口' in e.dxf.name):
        p=e.dxf.insert; pos[(e.dxf.layer,e.dxf.name)].append((round(p.x),round(p.y)))
for k,v in pos.items():
    a=np.array(v); print(k,len(a),a.min(0),a.max(0))
# nested terminals inside blocks?
cnt=collections.Counter()
for e,M,ef,ch in walk(d,m,stop=lambda e,ef,ch:'风口' in e.dxf.name):
    if e.dxftype()=='INSERT' and ch: cnt[(ef,e.dxf.name,ch[0])]+=1
print('nested',cnt.most_common(20))
# axis text labels: find texts on axis-like layers
ax=collections.Counter()
for e in m:
    if e.dxftype() in('TEXT','MTEXT','INSERT') and re.search('AXIS|轴|DOTE|GRID',e.dxf.layer,re.I): ax[(e.dxf.layer,e.dxftype())]+=1
print(ax.most_common(20))
# overall layers with DUCT positions
P=[]
for e in m:
    if e.dxf.layer.startswith('DUCT-') and e.dxftype()=='LINE': P.append((e.dxf.start.x,e.dxf.start.y))
P=np.array(P); print('duct lines',len(P),np.percentile(P,[0,5,50,95,100],axis=0).round())
