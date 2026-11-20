import ezdxf,sys,collections,numpy as np,re
from ezdxf import bbox
from lib import walk
f=sys.argv[1]; T=np.array(list(map(float,sys.argv[2].split(',')))); skip=set(sys.argv[3].split('|')) if len(sys.argv)>3 else set()
exec(open('dec.py').read().split("key=sys.argv[1]")[0])
WL=set().union(*[c['wl'] for c in cfg.values()])
d=ezdxf.readfile(f)
L=re.compile(r'综合末端-天花|C-暖通设备|风口|顶面设备')
def stop(e,ef,ch): return bool(L.search(ef))
c=collections.defaultdict(list)
for e,M,ef,ch in walk(d,d.modelspace(),stop=stop):
    if ch and ch[0] in skip: continue
    if e.dxftype()=='INSERT' and L.search(ef):
        try: bb=bbox.extents([e],fast=True); p=M.transform(bb.center); sz=(bb.size.x,bb.size.y)
        except Exception: continue
        c[(e.dxf.name,ef)].append((p.x+T[0],p.y+T[1],sz[0],sz[1]))
for k,v in sorted(c.items(),key=lambda x:-len(x[1])):
    a=np.array(v); print(len(v),k,'WL' if k[0] in WL else '', np.round(a[:,2:].mean(0)), np.round(a[0,:2]))
