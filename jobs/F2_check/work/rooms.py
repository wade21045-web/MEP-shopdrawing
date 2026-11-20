import ezdxf,collections,pickle,numpy as np,re
from lib import walk
OFF=pickle.load(open('off_dec.pkl','rb'))
d=ezdxf.readfile('dxf/L2-大平面-升版9.2.dxf'); m=d.modelspace()
T=[]
for e,M,ef,ch in walk(d,m):
    if e.dxftype() in('TEXT','MTEXT','ATTRIB'):
        try:
            s=e.plain_text() if e.dxftype()=='MTEXT' else e.dxf.text; p=M.transform(e.dxf.insert)
            T.append((ef,s.strip(),p.x+OFF[0],p.y+OFF[1],ch[:1]))
        except Exception: pass
# also attribs on inserts
for e in m.query('INSERT'):
    for a in e.attribs: T.append((a.dxf.layer,a.dxf.text,a.dxf.insert.x+OFF[0],a.dxf.insert.y+OFF[1],('ATT',e.dxf.name)))
c=collections.Counter(t[0] for t in T if -90000<t[2]<35000 and 255000<t[3]<350000)
print(c.most_common(30))
for L in [k for k,v in c.most_common(12)]:
    print(L,[t[1][:25] for t in T if t[0]==L][:25])
pickle.dump(T,open('dec_texts.pkl','wb'))
