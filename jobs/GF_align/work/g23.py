import ezdxf,pickle,re,collections
from lib import walk,txt
d=ezdxf.readfile("dxf/1.GF-02&03大平标新位置-0914.dxf"); m=d.modelspace()
G=[];LC=collections.Counter()
for e,M,ef,ch in walk(d,m):
    if e.dxftype() in('TEXT','MTEXT','ATTRIB'):
        s=txt(e).strip()
        if re.fullmatch(r'(\d{1,2}|[A-T]|1/[0-9A-Z]{1,2}|[23]/G)',s):
            p=M.transform(e.dxf.insert); G.append((s,p.x,p.y,ef,ch[:1])); LC[(ef,ch[:1])]+=1
print(LC.most_common(10)); pickle.dump(G,open('g_23.pkl','wb'))
