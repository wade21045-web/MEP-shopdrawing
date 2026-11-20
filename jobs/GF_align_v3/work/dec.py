import ezdxf,sys,pickle,re,math,numpy as np
from lib import walk,txt
from ezdxf import bbox
cfg={
 '01':dict(f="dxf/1.GF-01-0914.dxf",frames={'MS':(36446.53,-20917.40),'A$C3087fbf4':(-56314.20,-23735.08)},skip={'A$C3087fbf4','0905jianzhu'},
      wl={'$风口$00000092','*U237','*U238','*U239','*U240','*U498'}),
 '23':dict(f="dxf/1.GF-02&03大平标新位置-0914.dxf",frames={'MS':(36446.00,-20918.06),'02-03组':(36445.99,-20918.04)},skip={'02-03组','0905建筑'},
      wl={'$风口$00000092','*U415','*U417','*U416','*U414','*U203','方形风口'}),
 'off':dict(f="dxf/Office-F00 plan 1017.dxf",frames={'MS':(-151883.20,-20917.26)},skip=set(),
      wl={'we4r5tsedrfgedrf','A$C1f993f10','A$Cd3d333b5','A$Cef661f1d','A$C68218307','A$C20e4a109','A$Cbec9e21a','$风口$00000092','$风口$00000103','$风口$00000106','A$C83c4c107','A$Cf005e70a','A$Ca2480d82','A$C48ba2794','A$Cab93dd95','A$Ccff64bc9','A$C78ab460a','A$Cf07cd09a','*U4153','*U4154','*U4155'}),
}
key=sys.argv[1]; C=cfg[key]
d=ezdxf.readfile(C['f'])
TL=re.compile(r'综合末端-天花|C-暖通设备|顶面设备|风口',re.I)
def isterm(e): 
    n=e.dxf.name
    if n in C['wl']: return True
    try:
        b=d.blocks.get(n); return any(x.dxftype()=='ATTDEF' and x.dxf.tag=='A/S' for x in b)
    except: return False
def stop(e,ef,ch): return isterm(e) and bool(TL.search(ef))
out=[]; cov=[]
CL=re.compile(r'综合末端-天花|C-天花灯具|C-天花轮廓线|C-暖通设备|C-平面灯具')
for fr,t in C['frames'].items():
    lay=d.modelspace() if fr=='MS' else d.blocks.get(fr)
    for e,M,ef,ch in walk(d,lay,stop=stop):
        if fr=='MS' and ch and ch[0] in C['skip']: continue
        if CL.search(ef) and e.dxftype() in('INSERT','LINE','LWPOLYLINE','CIRCLE','ARC'):
            try:
                p=M.transform(e.dxf.insert if e.dxftype()=='INSERT' else (e.dxf.start if e.dxftype()=='LINE' else (e.dxf.center if e.dxftype() in ('CIRCLE','ARC') else (list(e.get_points('xy'))[0]+(0,)))))
                cov.append((p.x+t[0],p.y+t[1]))
            except Exception: pass
        if e.dxftype()=='INSERT' and stop(e,ef,ch):
            try: bb=bbox.extents([e],fast=True); c=M.transform(bb.center); sz=(bb.size.x,bb.size.y)
            except: continue
            # oriented size: use block extents in block coords * scale
            b=d.blocks.get(e.dxf.name)
            try:
                bl=bbox.extents(b,fast=True); osz=(abs(bl.size.x*e.dxf.xscale),abs(bl.size.y*e.dxf.yscale))
            except: osz=sz
            ang=(e.dxf.rotation+math.degrees(math.atan2(M[0,1],M[0,0])))%360
            out.append(dict(src=key,frame=fr,name=e.dxf.name,layer=ef,x=c.x+t[0],y=c.y+t[1],sx=sz[0],sy=sz[1],ox=osz[0],oy=osz[1],rot=ang,chain=ch,handle=e.dxf.handle,M=[list(M.get_row(i)) for i in range(4)],atts={a.dxf.tag:a.dxf.text for a in e.attribs}))
        elif e.dxftype()=='LWPOLYLINE' and ef=='F-地面回风口' and e.closed:
            try: bb=bbox.extents([e],fast=True); c=M.transform(bb.center)
            except: continue
            out.append(dict(src=key,frame=fr,name='F-地面回风口(多段线)',layer=ef,x=c.x+t[0],y=c.y+t[1],sx=bb.size.x,sy=bb.size.y,ox=bb.size.x,oy=bb.size.y,rot=0,chain=ch,handle=e.dxf.handle,M=[list(M.get_row(i)) for i in range(4)],atts={}))
pickle.dump(out,open(f'dec_{key}.pkl','wb')); pickle.dump(cov,open(f'cov_{key}.pkl','wb')); print('cov',len(cov))
import collections
print(key,len(out),collections.Counter((o['frame'],o['name'][:25]) for o in out).most_common(40))
