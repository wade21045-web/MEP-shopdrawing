import ezdxf,collections
d=ezdxf.readfile('dxf_out/GF.dxf')
def summ(n,dep=0):
    c=collections.Counter(); t=[]
    for e in d.blocks.get(n):
        c[(e.dxf.layer,e.dxftype())]+=1
        if e.dxftype() in('TEXT','MTEXT','ATTDEF'): t.append((e.plain_text() if e.dxftype()=='MTEXT' else e.dxf.text)[:20])
        if e.dxftype()=='INSERT': t.append('B:'+e.dxf.name)
    return dict(c),t[:6]
for n in ['GTFEB','GFFDG','*U1414','*U1440','*U1470','*U1506','检修口','1F$0$$equip_U$00000824(WIN-ZKD00809)','A$C7FB758C8']: print(n,summ(n))
b=d.blocks.get('dsadasdqwqwqq')
for e in b:
    if e.dxftype()=='MTEXT': print('MT',e.plain_text()[:200])
