import ezdxf,collections,sys,re,pickle
from ezdxf import bbox
f=sys.argv[1]; d=ezdxf.readfile(f); m=d.modelspace()
print('FILE',f,'units',d.header.get('$INSUNITS'),'layouts',[(l.name,len(l)) for l in d.layouts])
print('MS ents',len(m))
tc=collections.Counter(e.dxftype() for e in m); print(tc)
KW=re.compile(r'风口|送风|回风|排风|新风|散流|百叶|条形|条缝|diffus|grille|slot|SAD|RAD|EAD|FAD|AC|HVAC|空调|DIFF|GRIL|VENT|天花|RCP|CEIL|吊顶',re.I)
lay=collections.Counter(); 
for e in m: lay[e.dxf.layer]+=1
print('LAYERS',len(d.layers))
for L in d.layers:
    n=L.dxf.name
    if KW.search(n): print('  KWL',n,L.dxf.color,'off' if L.is_off() else '', 'frz' if L.is_frozen() else '', lay[n])
bn=collections.Counter(e.dxf.name for e in m if e.dxftype()=='INSERT')
print('MS inserts top', bn.most_common(40))
for b in d.blocks:
    if KW.search(b.name): print('  KWB',b.name,len(b),bn.get(b.name,0))
# titles
ts=[]
for e in m:
    if e.dxftype() in('TEXT','MTEXT'):
        t=e.plain_text() if e.dxftype()=='MTEXT' else e.dxf.text
        if re.search(r'天花|平面|PLAN|CEILING|RCP|图例|LEGEND',t,re.I) and len(t)<60:
            try: p=e.dxf.insert; ts.append((round(p.x),round(p.y),t.replace('\n',' '),round(e.dxf.get('height',0) or e.dxf.get('char_height',0))))
            except: pass
print('TITLES',len(ts))
for t in ts[:150]: print('  ',t)
print('LAYERS-ALL'); 
for n,c in lay.most_common(80): print('  ',c,n)
