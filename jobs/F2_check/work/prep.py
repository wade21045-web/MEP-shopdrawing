import ezdxf,pickle,numpy as np,re,collections
from lib import walk
from ezdxf import path as EP
OFF=pickle.load(open('off_dec.pkl','rb'))
d=ezdxf.readfile('dxf/L2-大平面-升版9.2.dxf'); m=d.modelspace()
CL=re.compile(r'综合末端-天花|C-天花灯具|C-天花轮廓线|C-暖通设备|C-平面灯具|C-面板灯|C-顶面')
cov=[]
for e,M,ef,ch in walk(d,m):
    if CL.search(ef) and e.dxftype() in('INSERT','LINE','LWPOLYLINE','CIRCLE','ARC'):
        try:
            if e.dxftype()=='LINE': p=e.dxf.start
            elif e.dxftype() in('CIRCLE','ARC'): p=e.dxf.center
            elif e.dxftype()=='LWPOLYLINE': p=list(e.get_points('xy'))[0]+(0,)
            else: p=e.dxf.insert
            p=M.transform(p); cov.append((p.x+OFF[0],p.y+OFF[1]))
        except Exception: pass
cov=np.array(cov); cov=cov[(cov[:,0]>-130000)&(cov[:,0]<60000)&(cov[:,1]>220000)&(cov[:,1]<370000)]
print('cov',len(cov))
T=pickle.load(open('dec_texts.pkl','rb'))
RL=[(L,s,x,y) for L,s,x,y,ch in T if L=='SPACE-IDEN' and s and not re.search(r'm²|m2$',s) and not re.fullmatch(r'[\d\s\.]+',s)]
print('rooms',len(RL),RL[:10])
pickle.dump(dict(cov=cov,RL=RL),open('prep.pkl','wb'))
