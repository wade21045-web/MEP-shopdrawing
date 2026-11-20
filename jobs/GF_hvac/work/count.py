import ezdxf,collections,sys,json
d=ezdxf.readfile(sys.argv[1]); m=d.modelspace()
acc=collections.Counter(); ty=collections.Counter()
def walk(name,eff,depth=0):
    for e in d.blocks.get(name):
        L=e.dxf.layer; L2=eff if L=='0' and eff else L
        if e.dxftype()=='INSERT':
            if depth<12 and e.dxf.name in d.blocks: walk(e.dxf.name,L2,depth+1)
        else: acc[L2]+=1; ty[e.dxftype()]+=1
walk('*Model_Space',None)
json.dump({'layers':dict(acc),'types':dict(ty),'nlayers':len(d.layers),'nblocks':len(d.blocks)},open(sys.argv[2],'w'),ensure_ascii=False)
print(sys.argv[1],sum(acc.values()),len(d.layers),len(d.blocks),dict(ty))
