import ezdxf,collections,json,time,numpy as np,pickle
from ezdxf.addons.importer import Importer
from sigs import esig,bhash
t0=time.time()
OFF=(28961.42114549,285185.2827819)
d=ezdxf.readfile('dxf/F02-MEP-ACD.dxf'); m=d.modelspace()
s=ezdxf.readfile('dxf/F02-MEP-B_hotel.dxf'); sm=s.modelspace()
print('loaded',time.time()-t0,flush=True)
nA0=len(m)
sigA=collections.Counter(esig(e) for e in m); sigA0=set(sigA)
mt,ms={}, {}
imp=Importer(s,d)
same=[];renamed=[]
for b in s.blocks:
    n=b.name
    if b.block_record.is_any_layout: continue
    if n in d.blocks:
        if bhash(s,n,ms)==bhash(d,n,mt): imp.imported_blocks[n]=n; same.append(n)
        else: renamed.append(n)
print('blocks same',len(same),'differ (renamed on import)',len(renamed),time.time()-t0,flush=True)
log=collections.Counter(); dup=collections.Counter(); skipped=collections.Counter(); imported=[]
srcsig=[]; basedup=[]; diffins=[]; RS=set(renamed)
for e in sm:
    k=esig(e,OFF)
    VER={('C15358-00-AATC-DD-BASE-AR1',130192,323428),('C15358-00-AATC-DD-BASE-AR2',98849,323428),('C15358-00-AATC-DD-BASE-AR2',197757,289564),('A$C25902DC9',28854,344009)}
    isins=e.dxftype()=='INSERT'
    if isins and e.dxf.name in RS and not ((e.dxf.name,round(e.dxf.insert.x+OFF[0]),round(e.dxf.insert.y+OFF[1])) in VER and sigA.get(k,0)>0):
        diffins.append((e.dxf.layer,e.dxf.name,sigA.get(k,0)>0))
    elif sigA.get(k,0)>0:
        if isins and e.dxf.name in RS: basedup.append(e.dxf.name)
        sigA[k]-=1; dup[(e.dxf.layer,e.dxftype())]+=1; continue
    t=e.dxftype()
    before=len(m)
    imp.import_entity(e,m)
    if len(m)==before: skipped[(t,e.dxf.layer)]+=1; continue
    ne=m[-1] if False else None
    imported.append((e,k))
imp.finalize()
print('imported',len(imported),'dup',sum(dup.values()),'skipped',sum(skipped.values()),time.time()-t0,flush=True)
# translate the new entities (they are the last ones in modelspace)
allm=list(m); newents=allm[nA0:]
assert len(newents)==len(imported),(len(newents),len(imported))
bad=collections.Counter()
for ne in newents:
    try: ne.translate(OFF[0],OFF[1],0)
    except Exception as ex: bad[(ne.dxftype(),str(ex)[:40])]+=1
print('translate errors',bad)
BASEL='合并-B图自带底图(与ACD图底图版本不同)'
d.layers.add(BASEL,color=8)
relayer=[]
for ne,(e,k) in zip(newents,imported):
    if ne.dxftype()=='INSERT' and e.dxf.name in RS and e.dxf.layer in ('0','0-1') and k in sigA0:
        relayer.append((e.dxf.layer,e.dxf.name,ne.dxf.name)); ne.dxf.layer=BASEL
print('relayer',relayer)
# check that each new entity signature equals source signature with offset (block names may be renamed)
mis=0
for ne,(e,k) in zip(newents,imported):
    k2=esig(ne)
    if k2!=k:
        if ne.dxftype()=='INSERT' and k2[3:]==k[3:]: continue
        mis+=1
        if ne.dxf.layer=='合并-B图自带底图(与ACD图底图版本不同)' and k2[2:]==k[2:]: mis-=1
print('sig mismatch after import',mis)
# appids
used=set()
for e in d.entitydb.values():
    xd=getattr(e,'xdata',None)
    if xd:
        for a in list(xd.data.keys()): used.add(a)
for a in used:
    if a not in d.appids:
        try: d.appids.new(a)
        except Exception as ex: pass
d.saveas('merged.dxf')
json.dump(dict(OFF=OFF,nA=nA0,nB=len(sm),imported=len(imported),dup=sorted([[*k,v] for k,v in dup.items()],key=lambda x:-x[2]),skipped=[[*k,v] for k,v in skipped.items()],blocks_same=len(same),blocks_renamed=renamed,diffins=diffins,basedup=basedup,relayer=relayer,translate_err=[[*k,v] for k,v in bad.items()],mis=mis),open('merge_log.json','w'),ensure_ascii=False,indent=1)
print('saved',time.time()-t0)
