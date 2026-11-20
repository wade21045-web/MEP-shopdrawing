import ezdxf,collections
d=ezdxf.readfile('dxf_out/GF.dxf'); m=d.modelspace()
def walk(name,eff,acc,depth=0):
    for e in d.blocks.get(name):
        L=e.dxf.layer; L2=eff if L=='0' and eff else L
        if e.dxftype()=='INSERT':
            if depth<12: walk(e.dxf.name,L2,acc,depth+1)
        else: acc[L2]+=1
seen=set()
for e in m:
    if e.dxftype()=='INSERT' and e.dxf.name not in seen:
        seen.add(e.dxf.name); acc=collections.Counter(); walk(e.dxf.name,e.dxf.layer if e.dxf.layer!='0' else None,acc)
        print('==',e.dxf.name,sum(acc.values())); print('   ',acc.most_common(25))
# proxies
pc=collections.Counter()
for b in d.blocks:
    for e in b:
        if e.dxftype()=='ACAD_PROXY_ENTITY': pc[(b.name[:20],e.dxf.layer)]+=1
print('PROXY',pc.most_common(30))
