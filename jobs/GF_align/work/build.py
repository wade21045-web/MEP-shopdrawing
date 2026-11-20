import ezdxf,pickle,re,numpy as np
from ezdxf.math import Matrix44
d=ezdxf.readfile('/workspace/GF_hvac/output/GF_暖通+建筑结构底图.dxf'); m=d.modelspace()
for n,c in [('装饰-风口',6),('风口核对-标记',1),('风口核对-编号',1),('风口核对-连线',1)]:
    if n not in d.layers: d.layers.add(n,color=c)
if 'CJK' not in d.styles: d.styles.add('CJK',font='simhei.ttf')
cnt=0
for key,zone in [('01','GF01'),('23','GF0203'),('off','OFF')]:
    G=pickle.load(open(f'geo_{key}.pkl','rb')); bmap={}
    for n,polys in G['blocks'].items():
        nm='DEC_'+zone+'_'+re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]','_',n)
        b=d.blocks.new(nm); bmap[n]=nm
        for v in polys: b.add_lwpolyline(v.tolist(),dxfattribs={'layer':'0','color':0})
    for it in G['items']:
        if it['block']:
            ins=m.add_blockref(bmap[it['block']],(0,0),dxfattribs={'layer':'装饰-风口'})
            ins.transform(Matrix44([x for r in it['M'] for x in r]))
        else:
            m.add_lwpolyline(it['pts'].tolist(),close=True,dxfattribs={'layer':'装饰-风口'})
        cnt+=1
print('decor copied',cnt)
R=pickle.load(open('result.pkl','rb'))
for s in R['ISS']:
    x,y=s['x'],s['y']; r=700 if s['dist'] is None else max(700,s['dist']/2+400)
    m.add_circle((x,y),r,dxfattribs={'layer':'风口核对-标记'})
    m.add_text(s['no'],height=350,dxfattribs={'layer':'风口核对-编号','style':'CJK'}).set_placement((x+r*0.75,y+r*0.75))
    if s['dist'] is not None:
        m.add_line((s['hx'],s['hy']),(s['dx'],s['dy']),dxfattribs={'layer':'风口核对-连线'})
        m.add_text(f"{s['dist']:.0f}",height=200,dxfattribs={'layer':'风口核对-编号','style':'CJK'}).set_placement((x+r*0.75,y+r*0.75-450))
d.saveas('GF_风口核对.dxf'); print('saved')
