import ezdxf,collections,numpy as np,re,sys,pickle
from lib import walk
f,tag=sys.argv[1],sys.argv[2]
d=ezdxf.readfile(f); m=d.modelspace()
out=[]
def stop(e,ef,ch): return bool(e.attribs) if e.dxftype()=='INSERT' else False
for e,M,ef,ch in walk(d,m,stop=stop):
    t=e.dxftype()
    if t=='INSERT' and e.attribs:
        vals=[a.dxf.text for a in e.attribs]
        p=M.transform(e.dxf.insert)
        if re.search('GRID|AXIS|轴|DOTE',ef+e.dxf.name,re.I) or (len(vals)==1 and re.fullmatch(r'[A-Z]{0,3}-?\d{0,3}[A-Z]?\'?',vals[0].strip() or 'x')):
            # use attrib position too
            ap=[M.transform(a.dxf.insert) for a in e.attribs]
            out.append((ef,e.dxf.name,vals,p.x,p.y,ap[0].x,ap[0].y,ch))
    elif t in('TEXT','MTEXT') and re.search('AXIS|轴|DOTE|GRID',ef,re.I):
        s=e.plain_text() if t=='MTEXT' else e.dxf.text
        p=M.transform(e.dxf.insert); out.append((ef,t,[s],p.x,p.y,p.x,p.y,ch))
pickle.dump(out,open(f'grid_{tag}.pkl','wb'))
c=collections.Counter((o[0],o[1]) for o in out); print(tag,len(out),c.most_common(10))
for o in out[:400]: print(o[0][:20],o[1][:15],o[2],round(o[5]),round(o[6]),o[7][:2])
