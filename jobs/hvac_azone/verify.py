import ezdxf,json
from collections import Counter
log=json.load(open('build_log.json'))
A=ezdxf.readfile('out/input.dxf'); B=ezdxf.readfile('rt_out/rt.dxf')
ma,mb=A.modelspace(),B.modelspace()
deleted=set(h for v in log['deleted'].values() for h in v)
moved=set(v['handle'] for v in log['moved'].values())
def sig(e):
    t=e.dxftype(); s=[t,e.dxf.layer,e.dxf.get('color',256),e.dxf.get('linetype','')]
    if t=='LINE': s+= [tuple(round(v,2) for v in e.dxf.start),tuple(round(v,2) for v in e.dxf.end)]
    elif t=='INSERT': s+=[e.dxf.name,tuple(round(v,2) for v in e.dxf.insert),round(e.dxf.rotation,3)]
    elif t in('TEXT',): s+=[e.dxf.text,tuple(round(v,2) for v in e.dxf.insert)]
    elif t=='MTEXT': s+=[e.text,tuple(round(v,2) for v in e.dxf.insert)]
    elif t=='LWPOLYLINE': s+=[tuple((round(p[0],2),round(p[1],2)) for p in e.get_points('xy'))]
    elif t in('CIRCLE','ARC'): s+=[tuple(round(v,2) for v in e.dxf.center),round(e.dxf.radius,2)]
    return tuple(s)
ha={e.dxf.handle:e for e in ma}; hb={e.dxf.handle:e for e in mb}
print('model entities input',len(ha),'output',len(hb))
kept=[h for h in ha if h not in deleted]
missing=[h for h in kept if h not in hb]
changed=[h for h in kept if h in hb and h not in moved and sig(ha[h])!=sig(hb[h])]
print('deleted',len(deleted),'moved',len(moved),'kept',len(kept),'missing',len(missing),'changed',len(changed))
print('missing sample',missing[:10]); print('changed sample',[(h,sig(ha[h]),sig(hb[h])) for h in changed[:5]])
new=[h for h in hb if h not in ha]
print('new entities',len(new),Counter((hb[h].dxftype(),hb[h].dxf.layer) for h in new).most_common())
print('expected new',sum(len(v) for v in log['added'].values()))
print('deleted by layer',Counter((ha[h].dxftype(),ha[h].dxf.layer) for h in deleted).most_common())
# other layouts / blocks
print('blocks',len(A.blocks),len(B.blocks),'layers',len(A.layers),len(B.layers))
pa=sum(1 for _ in A.objects); pb=sum(1 for _ in B.objects); print('objects',pa,pb)
print('paperspace', [ (l.name,len(l)) for l in A.layouts if l.name!='Model'], [(l.name,len(l)) for l in B.layouts if l.name!='Model'])
for room,v in log['moved'].items(): print('moved',room,v)
json.dump({'input':len(ha),'output':len(hb),'deleted':len(deleted),'added':len(new),'missing':len(missing),'changed':len(changed)},open('verify.json','w'))
