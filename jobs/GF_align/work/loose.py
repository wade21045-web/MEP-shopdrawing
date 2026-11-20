import ezdxf,collections,sys,re,pickle,numpy as np
from lib import walk
from ezdxf import path as P
L=re.compile(r'C-暖通设备|风口|顶面设备')
out={}
for key,f,T,skip in [('23',"dxf/1.GF-02&03大平标新位置-0914.dxf",(36446.00,-20918.06),('02-03组','0905建筑')),('01',"dxf/1.GF-01-0914.dxf",(36446.53,-20917.40),('0905jianzhu',)),('off',"dxf/Office-F00 plan 1017.dxf",(-151883.20,-20917.26),())]:
    d=ezdxf.readfile(f); items=[]
    frames=[('MS',d.modelspace(),T)]
    if key=='01': frames.append(('A$C3087fbf4',d.blocks.get('A$C3087fbf4'),(-56314.20,-23735.08)))
    for fr,lay,t in frames:
      for e,M,ef,ch in walk(d,lay):
        if fr=='MS' and ch and ch[0] in skip+('A$C3087fbf4',): continue
        if not L.search(ef): continue
        if len(ch)>(0 if fr=='MS' else 0) and ch: continue  # loose only (not inside blocks)
        tp=e.dxftype()
        if tp not in('LINE','ARC','LWPOLYLINE','SPLINE','ELLIPSE','CIRCLE','POLYLINE'): continue
        try: pts=np.array([(v.x,v.y) for v in P.make_path(e).transform(M).flattening(5)])
        except Exception: continue
        if len(pts)<2: continue
        items.append(dict(fr=fr,layer=ef,t=tp,h=e.dxf.handle,pts=pts+np.array(t)))
    out[key]=items; print(key,len(items),collections.Counter((i['fr'],i['layer'],i['t']) for i in items).most_common(12))
pickle.dump(out,open('loose.pkl','wb'))
