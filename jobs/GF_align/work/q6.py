import ezdxf,re,pickle
from lib import walk,txt
for f,T in [("dxf/1.GF-02&03大平标新位置-0914.dxf",(36446.00,-20918.06)),("dxf/1.GF-01-0914.dxf",(36446.53,-20917.40)),("dxf/Office-F00 plan 1017.dxf",(-151883.20,-20917.26))]:
    d=ezdxf.readfile(f)
    for e,M,ef,ch in walk(d,d.modelspace()):
        if e.dxftype() in('TEXT','MTEXT'):
            s=txt(e)
            if re.search(r'ALL ?DAY|KITCHEN|PREP|COOKING|全日',s,re.I):
                p=M.transform(e.dxf.insert); print(f[4:12],ch[:1],ef,repr(s[:40]),round(p.x+T[0]),round(p.y+T[1]))
