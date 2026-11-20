import ezdxf,json
from collections import Counter
log=json.load(open('build_log.json'))
A=ezdxf.readfile('out/input.dxf'); B=ezdxf.readfile('rt_out/rt.dxf')
ma,mb=A.modelspace(),B.modelspace()
deleted=set(h for v in log['deleted'].values() for h in v)
def r(v): return tuple(round(x,2) for x in v)
def sig(e):
    t=e.dxftype(); s=[t,e.dxf.layer,e.dxf.get('color',256),e.dxf.get('linetype','')]
    try:
        if t=='LINE': s+=[r(e.dxf.start),r(e.dxf.end)]
        elif t=='INSERT': s+=[e.dxf.name,r(e.dxf.insert),round(e.dxf.rotation,3),round(e.dxf.xscale,4),round(e.dxf.yscale,4)]
        elif t=='TEXT': s+=[e.dxf.text,r(e.dxf.insert),round(e.dxf.height,3)]
        elif t=='MTEXT': s+=[e.text,r(e.dxf.insert)]
        elif t=='LWPOLYLINE': s+=[tuple((round(p[0],2),round(p[1],2)) for p in e.get_points('xy'))]
        elif t in('CIRCLE','ARC'): s+=[r(e.dxf.center),round(e.dxf.radius,2)]
        elif t=='SPLINE': s+=[tuple(r(p) for p in e.control_points)]
        elif t=='ELLIPSE': s+=[r(e.dxf.center),r(e.dxf.major_axis)]
    except Exception: pass
    return tuple(s)
ha={e.dxf.handle:e for e in ma}; hb={e.dxf.handle:e for e in mb}
print('model entities input',len(ha),'output',len(hb))
kept=[h for h in ha if h not in deleted]
missing=[h for h in kept if h not in hb]
changed=[h for h in kept if h in hb and sig(ha[h])!=sig(hb[h])]
gone=[h for h in deleted if h in hb]
print('deleted',len(deleted),'still present',len(gone),'kept',len(kept),'missing',len(missing),'changed',len(changed))
print('changed sample',[(h,sig(ha[h]),sig(hb[h])) for h in changed[:5]])
new=[h for h in hb if h not in ha]
print('new entities',len(new),Counter((hb[h].dxftype(),hb[h].dxf.layer) for h in new).most_common())
print('expected new',sum(len(v) for v in log['added'].values()))
print('deleted by layer',Counter((ha[h].dxftype(),ha[h].dxf.layer) for h in deleted).most_common())
print('blocks',len(A.blocks),len(B.blocks),'layers',len(A.layers),len(B.layers))
print('paperspace',[(l.name,len(l)) for l in A.layouts if l.name!='Model']==[(l.name,len(l)) for l in B.layouts if l.name!='Model'])
print('new layer present', '修改-风机盘管调整20261119' in B.layers)
json.dump({'input':len(ha),'output':len(hb),'deleted':len(deleted),'added':len(new),'missing':len(missing),'changed':len(changed)},open('verify.json','w'))
