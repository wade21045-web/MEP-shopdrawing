import hashlib,numpy as np
from ezdxf import bbox
R=lambda v:round(float(v),0)
def esig(e,off=(0,0)):
    t=e.dxftype(); L=e.dxf.layer; ox,oy=off
    try:
        if t=='LINE': g=(R(e.dxf.start.x+ox),R(e.dxf.start.y+oy),R(e.dxf.end.x+ox),R(e.dxf.end.y+oy))
        elif t=='INSERT': g=(e.dxf.name,R(e.dxf.insert.x+ox),R(e.dxf.insert.y+oy),round(e.dxf.rotation,2),round(e.dxf.xscale,4),round(e.dxf.yscale,4),tuple(a.dxf.text for a in e.attribs))
        elif t in('TEXT','ATTDEF'): g=(e.dxf.text,R(e.dxf.insert.x+ox),R(e.dxf.insert.y+oy))
        elif t=='MTEXT': g=(e.text,R(e.dxf.insert.x+ox),R(e.dxf.insert.y+oy))
        elif t in('CIRCLE','ARC'): g=(R(e.dxf.center.x+ox),R(e.dxf.center.y+oy),R(e.dxf.radius),round(e.dxf.get('start_angle',0),1),round(e.dxf.get('end_angle',0),1))
        elif t=='LWPOLYLINE': g=tuple((R(x+ox),R(y+oy)) for x,y in e.get_points('xy'))+(e.closed,)
        elif t=='DIMENSION': g=(R(e.dxf.defpoint.x+ox),R(e.dxf.defpoint.y+oy),e.dxf.get('text',''),R(e.dxf.get('defpoint2',(0,0,0))[0]+ox) if e.dxf.hasattr('defpoint2') else 0)
        elif t=='POINT': g=(R(e.dxf.location.x+ox),R(e.dxf.location.y+oy))
        else:
            bb=bbox.extents([e],fast=True)
            g=(R(bb.extmin.x+ox),R(bb.extmin.y+oy),R(bb.extmax.x+ox),R(bb.extmax.y+oy)) if bb.has_data else ('nobb',)
    except Exception as ex: g=('err',str(ex)[:20])
    return (t,L)+g
def bhash(doc,name,memo):
    if name in memo: return memo[name]
    memo[name]='CYCLE'
    b=doc.blocks.get(name); h=hashlib.md5()
    items=[]
    for e in b:
        s=esig(e)
        if e.dxftype()=='INSERT' and e.dxf.name in doc.blocks: s=s+(bhash(doc,e.dxf.name,memo),)
        items.append(repr(s))
    for x in sorted(items): h.update(x.encode())
    bp=b.block.dxf.base_point; h.update(repr((R(bp[0]),R(bp[1]))).encode())
    memo[name]=h.hexdigest(); return memo[name]
