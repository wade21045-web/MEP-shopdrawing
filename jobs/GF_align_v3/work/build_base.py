import ezdxf,pickle,collections,json,hashlib,time
from ezdxf.addons.importer import Importer
from ezdxf.math import Vec3
t0=time.time()
d=ezdxf.readfile('odxf/d1.dxf'); m=d.modelspace()
src=ezdxf.readfile('odxf/d2.dxf'); sm=src.modelspace()
print('loaded',time.time()-t0,flush=True)
OLD='A$C76C4695F'
def sig(doc):
    c=collections.Counter(); h=hashlib.md5()
    for e in doc.modelspace():
        if e.dxftype()=='INSERT' and e.dxf.name==OLD: continue
        if e.dxf.layer=='AR-WALL-PLST 墙面抹灰': continue
        c[e.dxf.layer]+=1
        try: h.update((e.dxf.handle+e.dxftype()+str(e.dxf.get('insert',''))+str(e.dxf.get('start',''))+str(e.dxf.get('end',''))).encode())
        except Exception: pass
    return c,h.hexdigest()
c_before,h_before=sig(d)
log=dict(removed=[],imported=[],kept_note=[])
# 1 remove old background
for e in list(m):
    if e.dxftype()=='INSERT' and e.dxf.name==OLD:
        log['removed'].append(dict(kind='INSERT',name=OLD,layer=e.dxf.layer,insert=list(e.dxf.insert),handle=e.dxf.handle)); m.delete_entity(e)
    elif e.dxf.layer=='AR-WALL-PLST 墙面抹灰':
        log['removed'].append(dict(kind=e.dxftype(),layer=e.dxf.layer,handle=e.dxf.handle)); m.delete_entity(e)
# purge old arch block tree (only blocks not referenced elsewhere)
def refs(layout,acc,skip=None):
    for e in layout:
        n=e.dxf.name if e.dxftype()=='INSERT' else (e.dxf.get('geometry') if e.dxftype()=='DIMENSION' else None)
        if n and n not in acc and n in d.blocks and n!=skip: acc.add(n); refs(d.blocks.get(n),acc,skip)
used=set()
for lay in d.layouts: refs(lay,used)
tree=set([OLD]); refs(d.blocks.get(OLD),tree)
drop=[n for n in tree if n not in used]
for n in drop:
    try: d.blocks.delete_block(n,safe=False)
    except Exception as ex: print('del fail',n,ex)
log['purged_blocks']=len(drop); print('purged blocks',len(drop),flush=True)
# 2 import new background
for n,c in [('新底图-建筑(d2)',7),('新底图-结构L01(d2原位)',7),('新底图-结构M层(d2原位)',7),('新底图-结构L01(配准叠加)',8)]:
    if n not in d.layers: d.layers.add(n,color=c)
imp=Importer(src,d)
NEW={}
for n in ('A$C66761927','A$C40F3171B','DSDSAD'):
    NEW[n]=imp.import_block(n,rename=True)
imp.finalize()
print('imported',NEW,time.time()-t0,flush=True)
R=pickle.load(open('reg_d1d2.pkl','rb')); T=R['t']   # arch d2->d1 translation (expected 0)
ST=pickle.load(open('reg_struct.pkl','rb'))['t']
for e in sm.query('INSERT'):
    n=e.dxf.name
    if n not in NEW: continue
    lay={'A$C66761927':'新底图-建筑(d2)','A$C40F3171B':'新底图-结构L01(d2原位)','DSDSAD':'新底图-结构M层(d2原位)'}[n]
    ins=e.dxf.insert+Vec3(T[0],T[1],0) if n=='A$C66761927' else e.dxf.insert
    r=m.add_blockref(NEW[n],ins,dxfattribs={'layer':lay,'rotation':e.dxf.rotation,'xscale':e.dxf.xscale,'yscale':e.dxf.yscale,'zscale':e.dxf.get('zscale',1)})
    log['imported'].append(dict(src_block=n,new_block=NEW[n],layer=lay,insert=list(ins),src_layer=e.dxf.layer))
    if n=='A$C40F3171B':
        ins2=e.dxf.insert+Vec3(ST[0],ST[1],0)
        m.add_blockref(NEW[n],ins2,dxfattribs={'layer':'新底图-结构L01(配准叠加)'})
        log['imported'].append(dict(src_block=n,new_block=NEW[n],layer='新底图-结构L01(配准叠加)',insert=list(ins2),note='按轴线配准平移叠加到平面上'))
c_after,h_after=sig(d)
# exclude new layers
for k in list(c_after):
    if k.startswith('新底图'): del c_after[k]
log['hvac_unchanged']= (c_before==c_after)
print('HVAC/other MS entities unchanged:',c_before==c_after, sum(c_before.values()), sum(c_after.values()))
d.saveas('base.dxf'); print('saved',time.time()-t0)
json.dump(log,open('base_log.json','w'),ensure_ascii=False,indent=1,default=str)
