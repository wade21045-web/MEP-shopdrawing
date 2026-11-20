import ezdxf,collections,sys
f=sys.argv[1]
d=ezdxf.readfile(f); m=d.modelspace()
cnt=collections.Counter(); typ=collections.defaultdict(collections.Counter); ext={}
blk=collections.defaultdict(collections.Counter); txt=collections.defaultdict(list)
for e in m:
    L=e.dxf.layer; cnt[L]+=1; typ[L][e.dxftype()]+=1
    if e.dxftype()=='INSERT': blk[L][e.dxf.name]+=1
    try:
        p=e.dxf.insert if e.dxf.hasattr('insert') else (e.dxf.start if e.dxf.hasattr('start') else (e.dxf.center if e.dxf.hasattr('center') else None))
        if p is None and e.dxftype()=='LWPOLYLINE': p=list(e.vertices())[0]
        if p is not None:
            x,y=p[0],p[1]; a=ext.get(L,[x,x,y,y]); ext[L]=[min(a[0],x),max(a[1],x),min(a[2],y),max(a[3],y)]
    except Exception: pass
    if e.dxftype() in('TEXT','MTEXT') and len(txt[L])<4:
        try: txt[L].append((e.plain_text() if e.dxftype()=='MTEXT' else e.dxf.text)[:25].replace('\n',' '))
        except: pass
print('total',len(m),'layers',len(d.layers),'xrefs',[b.name for b in d.blocks if b.block and (b.block.dxf.flags & 4)])
for L in sorted(cnt,key=lambda l:-cnt[l]):
    la=d.layers.get(L) if L in d.layers else None
    st='' if la is None else ('off' if la.is_off() else '')+('frz' if la.is_frozen() else '')
    e=ext.get(L); es='' if not e else f'[{e[0]:.0f},{e[1]:.0f}]x[{e[2]:.0f},{e[3]:.0f}]'
    print(f"{L}|{st}|{cnt[L]}|{dict(typ[L].most_common(3))}|{dict(blk[L].most_common(3))}|{es}|{txt[L]}")
