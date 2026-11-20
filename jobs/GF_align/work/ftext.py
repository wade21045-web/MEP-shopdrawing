import ezdxf,sys,pickle,re
from lib import walk,txt
f,out=sys.argv[1],sys.argv[2]; frames=sys.argv[3].split('|')
d=ezdxf.readfile(f)
R={}
for fr in frames:
    if fr=='MS':
        lay=d.modelspace(); skipfirst=set(sys.argv[4].split('|')) if len(sys.argv)>4 else set()
    else: lay=d.blocks.get(fr); skipfirst=set()
    T=[]
    for e,M,ef,ch in walk(d,lay):
        if ch and ch[0] in skipfirst: continue
        if e.dxftype() in('TEXT','MTEXT','ATTRIB'):
            s=re.sub(r'\s+',' ',txt(e)).strip()
            if len(s)>=3 and re.search(r'[A-Za-z0-9]',s):
                p=M.transform(e.dxf.insert); T.append((s,p.x,p.y,ef))
    R[fr]=T; print(fr,len(T))
pickle.dump(R,open(out,'wb'))
