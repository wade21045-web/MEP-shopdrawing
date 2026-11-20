import ezdxf,json,sys
from collections import Counter
exec(open('/workspace/hvac_shop/verify.py').read().split("ha={")[0].split("log=json")[0])
src=open('/workspace/hvac_shop/verify.py').read(); exec(src[src.index('def r('):src.index('ha={')])
L0=json.load(open('/workspace/hvac_shop/build_log.json')); L1=json.load(open('shop_log.json'))
d0=sorted(h for v in L0['deleted'].values() for h in v); d1=sorted(h for v in L1['deleted'].values() for h in v)
print('deleted lists identical',d0==d1,len(d0))
S=ezdxf.readfile('/workspace/hvac_shop/c_in/SHOP_D043_D050_D044_D045_风机盘管调整.dxf'); V=ezdxf.readfile(sys.argv[1])
a0=[h for v in L0['added'].values() for h in v]; a1=[h for v in L1['added'].values() for h in v]
c0=Counter(sig(S.entitydb[h]) for h in a0)
# in V, find added entities by handle (only valid for v2_shop) or by geometry
if len(sys.argv)>2: c1=Counter(sig(V.entitydb[h]) for h in a1)
else:
    allsig=Counter(sig(e) for e in V.modelspace()); c1=Counter({k:min(v,allsig[k]) for k,v in c0.items()})
print('added sig multiset identical',c0==c1,sum(c0.values()),sum(c1.values()))
# region compare: all entities whose bbox in SHOP region
from ezdxf import bbox
def reg(doc):
    c=Counter()
    for e in doc.modelspace():
        try: b=bbox.extents([e],fast=True)
        except Exception: continue
        if b.has_data and b.extmin.x>-66000 and b.extmax.x<-48000 and b.extmin.y>-36000 and b.extmax.y<-26000: c[sig(e)]+=1
    return c
r0,r1=reg(S),reg(V)
print('SHOP region entities',sum(r0.values()),sum(r1.values()),'identical',r0==r1, 'diff', list((r0-r1).items())[:3], list((r1-r0).items())[:3])
