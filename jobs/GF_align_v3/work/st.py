import ezdxf,collections,re,pickle
from lib import walk,txt
d=ezdxf.readfile('odxf/d2.dxf'); m=d.modelspace()
for e0 in m.query('INSERT'):
    if e0.dxf.name not in ('A$C40F3171B','DSDSAD'): continue
    c=collections.Counter(); ex=collections.defaultdict(list); G=[]
    for e,M,ef,ch in walk(d,[e0]):
        if e.dxftype() in('TEXT','MTEXT','ATTRIB'):
            s=txt(e).strip(); c[(ef,e.dxftype())]+=1
            if len(ex[ef])<8: ex[ef].append(s[:20])
            if 'AXIS' in ef.upper(): p=M.transform(e.dxf.insert); G.append((s,p.x,p.y,ef))
    print(e0.dxf.name, c.most_common(15)); 
    for k,v in ex.items(): print('  ',k,v)
    pickle.dump(G,open(f'gs_{e0.dxf.name}.pkl','wb'))
