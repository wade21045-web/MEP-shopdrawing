import ezdxf,collections,numpy as np,re
from lib import walk
d=ezdxf.readfile('dxf/L2-大平面-升版9.2.dxf'); m=d.modelspace()
for n in ['VBRF','HEWEREWR','风口','A$C7F675982','*U411','*U412','*U413','*U414','GFFDG','A$C98236ec4','方形风口','$风口$00000092','Plot 05 Malcolm X 28FEB$0$Barnoval','$轴流风机$00000011','BTHEa nm','*U393','A$C20163122','VTBFW','A$Ca81f9e4e','4.8-机电末端']:
    b=d.blocks.get(n)
    c=collections.Counter((e.dxf.layer,e.dxftype(),e.dxf.name if e.dxftype()=='INSERT' else '') for e in b)
    print('##',n,len(b),c.most_common(12))
# where is C-顶面设备 layer
c=collections.Counter((ch,e.dxftype()) for e,M,ef,ch in walk(d,m) if ef.startswith('C-顶面设备'))
print(c.most_common(20))
