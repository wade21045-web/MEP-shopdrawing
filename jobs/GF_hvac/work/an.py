import ezdxf,collections,pickle,sys
d=ezdxf.readfile('dxf_out/GF.dxf')
m=d.modelspace()
print('ver',d.dxfversion,'layouts',[l.name for l in d.layouts])
cnt=collections.Counter(); typ=collections.defaultdict(collections.Counter); txt=collections.defaultdict(list)
for e in m:
    L=e.dxf.layer; cnt[L]+=1; typ[L][e.dxftype()]+=1
    if e.dxftype() in('TEXT','MTEXT','ATTRIB') and len(txt[L])<6:
        try: t=e.plain_text() if e.dxftype()=='MTEXT' else e.dxf.text
        except: t=''
        txt[L].append(t[:30])
    if e.dxftype()=='INSERT' and len(txt[L])<6: txt[L].append('B:'+e.dxf.name[:30])
print('total',len(m), 'layers',len(d.layers))
for L in sorted(d.layers, key=lambda l:-cnt[l.dxf.name]):
    n=L.dxf.name
    print(f"{n}|{L.dxf.color}|{'off' if L.is_off() else ''}{'frz' if L.is_frozen() else ''}|{cnt[n]}|{dict(typ[n].most_common(4))}|{txt[n]}")
print('XREF',[b.name for b in d.blocks if b.is_xref])
tt=collections.Counter(e.dxftype() for e in m); print(tt)
