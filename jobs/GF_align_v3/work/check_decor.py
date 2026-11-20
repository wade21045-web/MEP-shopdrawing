for key,zone in [('01','GF01'),('23','GF0203'),('off','OFF')]:
    Gk=GEO[key]; bmap={}
    for n,polys in Gk['blocks'].items():
        nm='DEC_'+zone+'_'+re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]','_',n)
        if nm not in d.blocks:
            b=d.blocks.new(nm)
            for v in polys: b.add_lwpolyline(v.tolist(),dxfattribs={'layer':'0','color':0})
        bmap[n]=nm
    for it in Gk['items']:
        if it['o']['cat']=='floor': continue
        if it['block']:
            ins=m.add_blockref(bmap[it['block']],(0,0),dxfattribs={'layer':'装饰-风口'}); ins.transform(Matrix44([x for r_ in it['M'] for x in r_]))
        else: m.add_lwpolyline(it['pts'].tolist(),close=True,dxfattribs={'layer':'装饰-风口'})
for o in DEC:
    if o.get('extra'):
        for v in o['pts']: m.add_lwpolyline(v.tolist(),dxfattribs={'layer':'装饰-风口'})
