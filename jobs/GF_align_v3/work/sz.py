import ezdxf,collections,sys
d=ezdxf.readfile(sys.argv[1])
ref=collections.Counter()
def scan(lay):
    for e in lay:
        if e.dxftype()=='INSERT': ref[e.dxf.name]+=1
        if e.dxftype()=='DIMENSION' and e.dxf.hasattr('geometry'): ref[e.dxf.geometry]+=1
for b in d.blocks: scan(b)
used=set(); stack=[l.block_record.dxf.name for l in d.layouts]
bl={b.name:b for b in d.blocks}
# reachability
child={b.name:{e.dxf.name for e in b if e.dxftype()=='INSERT'}|{e.dxf.geometry for e in b if e.dxftype()=='DIMENSION' and e.dxf.hasattr('geometry')} for b in d.blocks}
while stack:
    n=stack.pop()
    if n in used: continue
    used.add(n); stack+= [c for c in child.get(n,()) if c in bl]
un=[(len(bl[n]),n) for n in bl if n not in used]
un.sort(reverse=True)
print('blocks',len(bl),'unreachable',len(un),'ents',sum(x for x,_ in un)); print(un[:25])
tot=[(len(b),b.name) for b in d.blocks]; tot.sort(reverse=True); print('largest',tot[:15])
print('ms',len(d.modelspace()))
print(collections.Counter(e.dxf.layer for e in d.modelspace()).most_common(30))
print('objects',len(d.objects), collections.Counter(o.dxftype() for o in d.objects).most_common(10))
