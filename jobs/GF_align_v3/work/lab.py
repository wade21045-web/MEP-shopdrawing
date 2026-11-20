import ezdxf,pickle,re
from lib import walk,txt
d=ezdxf.readfile('base.dxf'); m=d.modelspace()
HL=[];RL=[]
for e in m:
    if e.dxftype() in('TEXT','MTEXT'):
        s=re.sub(r'\s+',' ',txt(e)).strip()
        if s and re.match(r'^(SAD|RAD|EAD|FAD|SAG|RAG|EAG|FAG|SAL|RAL|LSD|LAD|SA|RA|EA|FA|A/S|VD|R/A|S/A)',s):
            p=e.dxf.insert; HL.append(('MS',e.dxf.layer,s,p.x,p.y))
for e0 in m.query('INSERT'):
    if e0.dxf.name!='A$C66761927': continue
    for e,M,ef,ch in walk(d,[e0]):
        if e.dxftype() in('TEXT','MTEXT') and ('FLOR-IDEN' in ef or 'AREA' in ef or 'ROOM' in ef.upper()):
            s=re.sub(r'\s+',' ',txt(e)).strip()
            if s: p=M.transform(e.dxf.insert); RL.append(('A$C66761927',ef,s,p.x,p.y))
pickle.dump((HL,RL),open('labels_v3.pkl','wb')); print(len(HL),len(RL))
