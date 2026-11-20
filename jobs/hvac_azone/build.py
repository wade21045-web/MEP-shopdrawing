import ezdxf,pickle,json
from ezdxf.math import Vec3
from common import *
d=ezdxf.readfile('out/input.dxf'); m=d.modelspace(); db=d.entitydb
res=pickle.load(open('region.pkl','rb'))
eq_flour=pickle.load(open('eq_flour.pkl','rb'))
U=Vec3(C,S,0)
def cluster(layer,x0,x1,y0,y1):
    return [r[0] for r in res if r[2]==layer and r[6][0]>=x0-1 and r[7][0]<=x1+1 and r[6][1]>=y0-1 and r[7][1]<=y1+1]
OLD_EQ={'STOR':cluster('EQ-风机盘管',-106348,-105594,-48854,-48118),
        'OFF':cluster('EQ-风机盘管',-109896,-109131,-51914,-51178)}
DELETE={
 'STOR':OLD_EQ['STOR']+['CD762','CD763','CD764','CD765','CD766','CD767','CD768','CD769','CD76A','CD76B','CD996','CD997',
        'D0524','D0525','D0526','D0527','D053A','D0530','D052B','D052C','D052D','D0533','D0534','D0535','D052E','D052F'],
 'OFF':OLD_EQ['OFF']+['CD749','CD74A','CD74B','CD74C','CD74D','CD74E','CD74F','CD750','CD751','CD752','CD968','CD969','CF3F0',
        'D05A4','D05A5','D05A6','D05A7','D060B','D05B0','D05AB','D05AC','D05AD','D05B3','D05B4','D05B5','D05AE','D05AF']}
# old drop lines kept (handles sorted by side) -> extension start points
OLD_DROP={'STOR':{'CWR':['D0528','D0529','D052A'],'CWS':['D0539','D0538','D0537']},
          'OFF':{'CWR':['D05AA','D05A9','D05A8'],'CWS':['D05B7','D05B8','D05B9']}}
FL_DROP={'CWR':['D053F','D0543','D0541'],'CWS':['D0550','D054F','D054E']}  # left,center,right by x
CHAIN={'CWR':['D053B','D0547','D0542','D0544','D053D'],'CWS':['D05A2','D053C','D054A','D054B','D054C','D053E']}
SPL={'CWR':'D0545','CWS':'D0546'}
log={'deleted':{},'added':{}}
# dedupe FCU lines
seen=set(); eq_u=[]
for h in eq_flour:
    e=db[h]; k=(e.dxf.layer,)+tuple(sorted([tuple(round(v,1) for v in e.dxf.start),tuple(round(v,1) for v in e.dxf.end)]))
    if k in seen: continue
    seen.add(k); eq_u.append(h)
log['flour_fcu_lines_total']=len(eq_flour); log['flour_fcu_lines_unique']=len(eq_u)
NOTE_LAYER='修改-风机盘管调整20261118'
if NOTE_LAYER not in d.layers: d.layers.add(NOTE_LAYER,color=2)
def add_copy(h,vec,lst):
    n=db[h].copy(); m.add_entity(n); n.translate(vec.x,vec.y,0); lst.append(n.dxf.handle); return n
for room,cfg in ROOMS.items():
    T=Vec3(cfg['T'][0],cfg['T'][1],0); o=cfg['O']
    base=T+U*DX
    added=[]
    # 1 delete old FCU group
    dl=DELETE[room]
    for h in dl:
        assert h in db, h
        m.delete_entity(db[h])
    log['deleted'][room]=dl
    # 2 FCU + supply duct + VD + tag
    for h in eq_u+SUPPLY+TAG: add_copy(h,base,added)
    arr=db[{'STOR':'CD081','OFF':'CD077'}[room]]; src=db['CD08B']
    log.setdefault('moved',{})[room]={'handle':arr.dxf.handle,'from':list(arr.dxf.insert),'rot_from':arr.dxf.rotation}
    arr.dxf.insert=Vec3(src.dxf.insert)+base; arr.dxf.rotation=src.dxf.rotation
    log['moved'][room].update({'to':list(arr.dxf.insert),'rot_to':arr.dxf.rotation})
    # 3 valve chains (OFF: swap positions to match existing CWS-left/CWR-right drops)
    for kind in ('CWR','CWS'):
        fl_center=db[FL_DROP[kind][1]]
        flc=loc(fl_center.dxf.end,OF)[0]  # chain center x (local, FLOUR)
        oldc=db[OLD_DROP[room][kind][1]]
        oc=loc(oldc.dxf.end,o)[0] if loc(oldc.dxf.end,o)[1]<loc(oldc.dxf.start,o)[1] else loc(oldc.dxf.start,o)[0]
        dxk=oc-flc
        vec=T+U*dxk
        for h in CHAIN[kind]: add_copy(h,vec,added)
        # spline: start at chain, end at FCU connection (blend)
        s=db[SPL[kind]].copy(); m.add_entity(s)
        cps=[Vec3(p) for p in s.control_points]; n=len(cps)
        newc=[p+base+U*((dxk-DX)*(1-i/(n-1))) for i,p in enumerate(cps)]
        s.control_points=newc; added.append(s.dxf.handle)
        # extension lines from old drop bottom to chain top
        for oh,fh in zip(OLD_DROP[room][kind],FL_DROP[kind]):
            od=db[oh]; a,b=Vec3(od.dxf.start),Vec3(od.dxf.end)
            low=a if loc(a,o)[1]<loc(b,o)[1] else b
            fl=db[fh]; fa,fb=Vec3(fl.dxf.start),Vec3(fl.dxf.end)
            flow=fa if loc(fa,OF)[1]<loc(fb,OF)[1] else fb
            nl=fl.copy(); m.add_entity(nl)
            nl.dxf.start=Vec3(low.x,low.y,flow.z); nl.dxf.end=flow+vec
            added.append(nl.dxf.handle)
    # 4 fresh air extension
    def P(x,y): w=wld((x,y),o); return Vec3(w[0],w[1],0)
    def newline(proto,p1,p2):
        n=db[proto].copy(); m.add_entity(n); n.dxf.start=p1; n.dxf.end=p2; added.append(n.dxf.handle)
    fx=loc(Vec3(db['10D5A7'].dxf.end),OF)[0]+DX, loc(Vec3(db['10D5A9'].dxf.end),OF)+(0,), loc(Vec3(db['10D5AB'].dxf.end),OF)
    xL,xC,xR=1109.0,1189.0,1269.0
    yL=loc(db['10D5A7'].dxf.start,OF)[1]; yC=loc(db['10D5A9'].dxf.start,OF)[1]; yR=loc(db['10D5AB'].dxf.start,OF)[1]
    if room=='STOR':
        topL=topC=topR=369.0
        # snap to existing drop bottom
        newline('CD78B',P(xL,topL),P(xL,yL)); newline('CD786',P(xC,topC),P(xC,yC)); newline('CD783',P(xR,topR),P(xR,yR))
    else:
        yb,yc,yt=77.0,157.0,237.0; x0=-523.0
        newline('CD78B',P(x0,yt),P(xR,yt)); newline('CD78B',P(x0,yb),P(xL,yb)); newline('CD786',P(x0,yc),P(xC,yc))
        newline('CD78B',P(xL,yb),P(xL,yL)); newline('CD786',P(xC,yc),P(xC,yC)); newline('CD783',P(xR,yt),P(xR,yR))
    for proto,xs,ys in (('10D5A7',xL,yL),('10D5A9',xC,yC),('10D5AB',xR,yR)):
        pe=loc(db[proto].dxf.end,OF)
        newline(proto,P(xs,ys),P(pe[0]+DX,pe[1]))
    # 5 note
    t=m.add_text('MEP修改20261118:同FLOUR STORAGE做法',
        dxfattribs={'layer':NOTE_LAYER,'height':100,'rotation':ANG,'color':2})
    t.set_placement(P(-1350,-3450)); added.append(t.dxf.handle)
    log['added'][room]=added
    print(room,'deleted',len(dl),'added',len(added))
json.dump(log,open('build_log.json','w'),ensure_ascii=False,indent=1)
d.saveas('out_after.dxf')
