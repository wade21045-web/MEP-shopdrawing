import ezdxf,sys,collections,re
from lib import walk,txt
from ezdxf import bbox
f=sys.argv[1]; frames=sys.argv[2].split('|'); skip=set(sys.argv[3].split('|'))
d=ezdxf.readfile(f)
TL=re.compile(r'综合末端-天花|C-暖通设备|顶面设备|风口',re.I)
def stop(e,ef,ch): return bool(TL.search(ef))
for fr in frames:
    lay=d.modelspace() if fr=='MS' else d.blocks.get(fr)
    ins=collections.Counter(); raw=collections.Counter(); ex={}
    for e,M,ef,ch in walk(d,lay,stop=stop):
        if fr=='MS' and ch and ch[0] in skip: continue
        if not TL.search(ef): continue
        if e.dxftype()=='INSERT':
            ins[(e.dxf.name,ef)]+=1
            if e.dxf.name not in ex:
                try: bb=bbox.extents([e],fast=True); ex[e.dxf.name]=(round(bb.size.x),round(bb.size.y))
                except: ex[e.dxf.name]=None
        else: raw[(e.dxftype(),ef)]+=1
    print('###',fr)
    for (n,ef),c in ins.most_common():
        b=d.blocks.get(n); lays=collections.Counter(x.dxf.layer for x in b); ts=[txt(x)[:15] for x in b if x.dxftype() in('TEXT','MTEXT')][:4]
        ads=[x.dxf.tag for x in b if x.dxftype()=='ATTDEF'][:4]
        print(f'  {c:4d} {n[:45]:45s} {ef:12s} size={ex.get(n)} n={len(b)} {dict(lays.most_common(3))} {ts} {ads}')
    print('  RAW',raw.most_common(12))
