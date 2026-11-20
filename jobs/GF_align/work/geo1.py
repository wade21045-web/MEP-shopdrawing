import ezdxf,pickle,sys,numpy as np
from ezdxf import path
from ezdxf.math import Matrix44,Vec3
from lib import walk
key=sys.argv[1]; F={'01':"dxf/1.GF-01-0914.dxf",'23':"dxf/1.GF-02&03大平标新位置-0914.dxf",'off':"dxf/Office-F00 plan 1017.dxf"}[key]
R=pickle.load(open('result.pkl','rb')); DEC=[o for o in R['DEC'] if o['src']==key]
d=ezdxf.readfile(F)
T={'01':(36446.53,-20917.40),'23':(36446.00,-20918.06),'off':(-151883.20,-20917.26)}
fr_t={'01':{'MS':(36446.53,-20917.40),'A$C3087fbf4':(-56314.20,-23735.08)},'23':{'MS':(36446.00,-20918.06),'02-03组':(36445.99,-20918.04)},'off':{'MS':(-151883.20,-20917.26)}}[key]
blocks={}; items=[]
for o in DEC:
    e=d.entitydb[o['handle']]; Mc=Matrix44([v for r in o['M'] for v in r]); t=fr_t[o['frame']]; Tm=Matrix44.translate(t[0],t[1],0)
    if e.dxftype()=='INSERT':
        n=e.dxf.name
        if n not in blocks:
            b=d.blocks.get(n); bp=Vec3(b.block.dxf.base_point); polys=[]
            for x,M,ef,ch in walk(d,b):
                try: p=path.make_path(x).transform(Matrix44.translate(*(-bp))@M if False else M)
                except Exception: continue
                for sp in p.sub_paths():
                    v=np.array([(q.x-bp.x,q.y-bp.y) for q in sp.flattening(1.0)])
                    if len(v)>1: polys.append(v)
            blocks[n]=polys
        Mi=Matrix44.translate(*(-Vec3(d.blocks.get(n).block.dxf.base_point)))@e.matrix44()
        # note: polys are already base-point-shifted, so use insert matrix without base shift
        items.append(dict(o=o,block=n,M=[list((e.matrix44()@Mc@Tm).get_row(i)) for i in range(4)]))
    else:
        v=np.array([tuple((Mc@Tm).transform((x,y,0)))[:2] for x,y in e.get_points('xy')])
        items.append(dict(o=o,block=None,pts=v))
pickle.dump(dict(blocks=blocks,items=items),open(f'geo_{key}.pkl','wb')); print(key,len(blocks),len(items))
