import ezdxf,sys,pickle,re,collections,numpy as np
from lib import walk,txt
from ezdxf import bbox
f,out=sys.argv[1],sys.argv[2]
d=ezdxf.readfile(f); m=d.modelspace()
TL=re.compile(r'综合末端-天花|C-暖通设备|顶面设备|风口|HVAC|DIFF|GRILLE',re.I)
BN=re.compile(r'风口|DIFF|GRILL|SAD|RAD|EAD|ACC|散流|百叶|条形|条缝|侧向',re.I)
SKIP={'0905建筑','0905jianzhu'}
def stop(e,ef,ch):
    return bool(TL.search(ef)) or bool(BN.search(e.dxf.name))
R=[]
for e,M,ef,ch in walk(d,m,stop=stop):
    if ch and ch[0] in SKIP: continue
    if e.dxftype()!='INSERT': continue
    p=M.transform(e.dxf.insert)
    try:
        bb=bbox.extents([e],fast=True); 
        c=M.transform(bb.center); sz=(bb.size.x,bb.size.y)
    except Exception: c=p; sz=(0,0)
    # rotation in world
    import math
    ang=(e.dxf.rotation+math.degrees(math.atan2(M[0,1],M[0,0])))%360
    atts={a.dxf.tag:a.dxf.text for a in e.attribs} if e.attribs else {}
    R.append(dict(name=e.dxf.name,layer=ef,x=c.x,y=c.y,ix=p.x,iy=p.y,sx=sz[0],sy=sz[1],rot=ang,chain=ch,atts=atts))
pickle.dump(R,open(out,'wb'))
c=collections.Counter((r['name'][:40],r['layer']) for r in R)
print(f,len(R))
for k,n in c.most_common(70): print('  ',n,k)
cc=collections.Counter(r['chain'][:1] for r in R); print('roots',cc.most_common(10))
X=np.array([(r['x'],r['y']) for r in R]); print('extent',X.min(0),X.max(0))
