import ezdxf,pickle,re,numpy as np,collections,math
from scipy.spatial import cKDTree
from scipy.optimize import linear_sum_assignment
from lib import walk,txt
BX=(-150000,95000,-100000,35000)
# ---------- decor
DEC=[]
TYPE={'$风口$00000092':'方形散流器','方形风口':'方形散流器','we4r5tsedrfgedrf':'方形散流器','*U498':'方形风口(圆颈)',
'$风口$00000106':'圆形旋流风口','A$Cd3d333b5':'圆形旋流风口','$风口$00000103':'球形/侧送喷口',
'A$Cef661f1d':'方形散流器','A$C68218307':'方形回风口','A$Cbec9e21a':'条形风口','*U4153':'条形风口','*U4154':'条形风口','*U4155':'条形风口',
'A$Ccff64bc9':'组合条形风口','F-地面回风口(多段线)':'地面回风口'}
def cat(t,ax,ay):
    if '圆' in t and '圆颈' not in t: return 'round'
    if '喷口' in t: return 'jet'
    if '地面' in t: return 'floor'
    a=max(ax,ay)/max(1,min(ax,ay))
    return 'linear' if a>=2.5 else 'panel'
for k,zone in [('01','GF-01'),('23','GF-02&03'),('off','Office-F00')]:
    seen=[]
    for o in pickle.load(open(f'dec_{k}.pkl','rb')):
        if not(BX[0]<o['x']<BX[1] and BX[2]<o['y']<BX[3]): continue
        if any(abs(o['x']-s[0])<20 and abs(o['y']-s[1])<20 for s in seen): continue
        seen.append((o['x'],o['y']))
        t=TYPE.get(o['name'])
        if t is None:
            a=max(o['ox'],o['oy'])/max(1,min(o['ox'],o['oy'])); t='条形风口' if a>=2.5 else '百叶/矩形风口'
        o['type']=t; o['cat']=cat(t,o['ox'],o['oy']); o['zone']=zone; DEC.append(o)
print('decor',len(DEC),collections.Counter((o['zone'],o['type']) for o in DEC))
pickle.dump(dict(DEC=DEC),open('result.pkl','wb'))
