import ezdxf,collections,sys
d=ezdxf.readfile('check.dxf')
bl={b.name:b for b in d.blocks}
def kids(b):
    s=set()
    for e in b:
        if e.dxftype()=='INSERT': s.add(e.dxf.name)
        elif e.dxftype()=='DIMENSION' and e.dxf.hasattr('geometry'): s.add(e.dxf.geometry)
    return s
child={n:kids(b) for n,b in bl.items()}
def dyn(b):
    br=b.block_record
    try:
        xd=br.get_extension_dict()
        return 'ACAD_ENHANCEDBLOCK' in xd
    except Exception: return False
roots=[l.block_record.dxf.name for l in d.layouts]
H=set()
with open('check.dxf',encoding='utf-8',errors='ignore') as f:
    while True:
        c=f.readline()
        if not c: break
        v=f.readline()
        try: ci=int(c)
        except: continue
        if 340<=ci<=349 or 360<=ci<=369 or 320<=ci<=329 or 1005==ci or 390<=ci<=399 or 480<=ci<=481: H.add(v.strip().upper())
hr=[n for n,b in bl.items() if b.block_record.dxf.handle.upper() in H]
ds=set()
for st_ in d.dimstyles:
    for a in ('dimblk','dimblk1','dimblk2','dimldrblk'):
        v=st_.dxf.get(a)
        if v: ds.add(v); ds.add('_'+v)
print('handle-ref blocks',len(hr),'dimstyle',len(ds))
roots+=hr+[n for n in ds if n in bl]
dm=[n for n,b in bl.items() if not n.startswith('*') and dyn(b)]
keep=set(); st=roots+dm
while st:
    n=st.pop()
    if n in keep or n not in bl: continue
    keep.add(n); st+=list(child[n])
drop=[n for n in bl if n not in keep and not bl[n].block_record.is_any_layout]
print('dyn masters kept',len(dm),'drop',len(drop),'ents',sum(len(bl[n]) for n in drop))
for n in drop:
    try: d.blocks.delete_block(n,safe=False)
    except Exception as ex: print('fail',n,ex)
open('purged_blocks.txt','w').write('\n'.join(drop))
d.saveas('check_p.dxf'); print('saved')
