import ezdxf,sys,pickle,collections,re
from lib import walk,txt
f,out=sys.argv[1],sys.argv[2]
d=ezdxf.readfile(f); m=d.modelspace()
G=[]; LC=collections.Counter()
for e,M,ef,ch in walk(d,m):
    t=e.dxftype()
    if t in('TEXT','MTEXT') :
        s=txt(e).strip()
        if ('DOTE' in ef.upper() or 'AXIS' in ef.upper() or '轴' in ef) and re.fullmatch(r'[0-9A-Z/\-]{1,5}',s):
            p=M.transform(e.dxf.insert); G.append((s,p.x,p.y,ef,ch[:1])); LC[ef]+=1
pickle.dump(G,open(out,'wb')); print(f,len(G),LC.most_common(10))
