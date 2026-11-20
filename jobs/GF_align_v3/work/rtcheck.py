import ezdxf,sys,collections,json
d=ezdxf.readfile(sys.argv[1]); m=d.modelspace()
c=collections.Counter((e.dxf.layer,e.dxftype()) for e in m)
ins=collections.Counter(e.dxf.name for e in m.query('INSERT'))
json.dump(dict(n=len(m),layers={f'{k[0]}|{k[1]}':v for k,v in c.items()},ins=dict(ins),nblocks=len(d.blocks),nlayers=len(d.layers)),open(sys.argv[2],'w'),ensure_ascii=False)
print(sys.argv[2],len(m),len(d.blocks),len(d.layers))
