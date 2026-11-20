import ezdxf,sys,pickle,numpy as np
from lib import walk
f,out,roots=sys.argv[1],sys.argv[2],sys.argv[3].split(',')
d=ezdxf.readfile(f); m=d.modelspace()
P=[]
for e,M,ef,ch in walk(d,m):
    if roots!=['*'] and (not ch or ch[0] not in roots): continue
    if roots==['*'] and not (ef.startswith('AR-WALL') or ef.startswith('A-WALL') or ef.startswith('AR-WALL-CONC')): continue
    t=e.dxftype()
    if t=='LINE': P+= [tuple(M.transform(e.dxf.start))[:2],tuple(M.transform(e.dxf.end))[:2]]
    elif t=='LWPOLYLINE': P+= [tuple(M.transform((x,y,0)))[:2] for x,y in e.get_points('xy')]
P=np.array(P,dtype=float); pickle.dump(P,open(out,'wb')); print(f,P.shape)
