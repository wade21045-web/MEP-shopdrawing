import ezdxf,collections,re,json,math
from ezdxf import bbox
d=ezdxf.readfile('dxf_out/GF.dxf'); m=d.modelspace()
OTHER_BLOCKS={'A$C4AC52382':'给水/热水','A$C7CBB6E43':'雨水/排水','A$C4F55710D':'污废水','A$C0DAF4DAC':'消防喷淋/消火栓','A$C552D5B8D':'电气桥架/母线','A$C1C7B7192':'电气/弱电桥架','dsadasdqwqwqq':'天花综合末端(灯具/报警按钮等)'}
MS_OTHER_LAYERS={'桥架','CABLETRAY','桥架中心线'}
INBLOCK_OTHER_LAYERS={'EQUIP_地漏'}
HVAC_BLOCKS={'A$C5E357C2F','A$C124230B8'}
log=collections.Counter(); deleted=[]
def txt(e):
    t=e.dxftype()
    return e.plain_text() if t=='MTEXT' else (e.dxf.text if t=='TEXT' else '')
def ctr(e):
    try: return bbox.extents([e],fast=True).center
    except: return None
# --- modelspace
notes=[]
for e in m:
    if e.dxf.layer=='TEL_TEXT' and e.dxftype() in('TEXT','MTEXT'): notes.append((e,ctr(e),txt(e)))
othernote=set()
for e,c,t in notes:
    if re.search('桥架|弱电|强电|弱点|强点',t): othernote.add(id(e))
# propagate to fragments on same line
for e,c,t in notes:
    if id(e) in othernote: continue
    for e2,c2,t2 in notes:
        if id(e2) in othernote and abs(c.y-c2.y)<600 and abs(c.x-c2.x)<26000 and len(t.strip())<=3: othernote.add(id(e)); break
noteinfo=[(c,id(e) in othernote) for e,c,t in notes if len(t.strip())>3]
kill=[]
for e in m:
    L=e.dxf.layer; t=e.dxftype()
    if t=='INSERT' and e.dxf.name in OTHER_BLOCKS: kill.append((e,'OTHER block '+OTHER_BLOCKS[e.dxf.name])); continue
    if L in MS_OTHER_LAYERS: kill.append((e,'MS layer '+L)); continue
    if L=='TH_DIM' and t in('TEXT','MTEXT') and re.match(r'^(PL|SW|WS|EL\d|ICT|UPS|FA\d)',txt(e).replace('\n',' ').strip()): kill.append((e,'section label non-HVAC: '+txt(e).replace('\n',' '))); continue
    if L=='TEL_TEXT' and id(e) in othernote: kill.append((e,'note non-HVAC: '+txt(e))); continue
    if L in('DIM_MODI','TEL_SYMB'):
        c=ctr(e)
        if c is None or not noteinfo: continue
        dist,oth=min(((math.dist((c.x,c.y),(n.x,n.y)),o) for n,o in noteinfo))
        # only small markers (triangles/'1'); big clouds keep unless clearly nearest an other note
        if oth and dist<15000: kill.append((e,'revision mark near non-HVAC note'))
plsw=[ctr(e) for e,why in kill if why.startswith('section label') and re.match(r'^(PL|SW|WS)',txt(e).strip())]
ks={id(e) for e,_ in kill}
for e in m:
    if id(e) in ks or e.dxftype() not in('CIRCLE','ARC','LWPOLYLINE','LINE','HATCH'): continue
    try: bb=bbox.extents([e],fast=True)
    except: continue
    if not bb.has_data or bb.size.x>200: continue
    c=bb.center
    for p in plsw:
        if abs(c.x-p.x)<60 and -50<c.y-p.y<450: kill.append((e,'section pipe symbol of PL/SW (mis-layered)')); ks.add(id(e)); break
for e,why in kill:
    log[why if not why.startswith(('section label','note non')) else why.split(':')[0]]+=1; deleted.append(('*Model_Space',e.dxf.layer,e.dxftype(),why))
    m.delete_entity(e)
# --- inside HVAC blocks
def walk_names(n,acc):
    for e in d.blocks.get(n):
        if e.dxftype()=='INSERT' and e.dxf.name not in acc: acc.add(e.dxf.name); walk_names(e.dxf.name,acc)
hv=set()
for n in HVAC_BLOCKS: hv.add(n); walk_names(n,hv)
for n in hv:
    b=d.blocks.get(n)
    for e in [e for e in b if e.dxf.layer in INBLOCK_OTHER_LAYERS]:
        log['in-HVAC-block layer '+e.dxf.layer]+=1; b.delete_entity(e)
# --- purge unreferenced blocks
def refs(layout,acc):
    for e in layout:
        t=e.dxftype()
        if t=='INSERT': n=e.dxf.name
        elif t=='DIMENSION': n=e.dxf.get('geometry')
        else: continue
        if n and n not in acc and n in d.blocks: acc.add(n); refs(d.blocks.get(n),acc)
used=set()
for lay in d.layouts: refs(lay,used)
# also blocks referenced by block_record of layouts
drop=[b.name for b in d.blocks if not b.name.startswith('*Model') and not b.name.startswith('*Paper') and b.name not in used and not b.name.startswith('*D') ]
# be conservative: only drop blocks that were reachable from deleted OTHER roots
other_reach=set()
for n in OTHER_BLOCKS: other_reach.add(n); walk_names(n,other_reach)
drop=[n for n in drop if n in other_reach or n in OTHER_BLOCKS]
for n in drop:
    try: d.blocks.delete_block(n,safe=False)
    except Exception as ex: print('blkdel fail',n,ex)
print('dropped blocks',len(drop))
# --- purge unused layers
usedL=collections.Counter()
for b in d.blocks:
    for e in b: usedL[e.dxf.layer]+=1
dl=[L.dxf.name for L in d.layers if usedL[L.dxf.name]==0 and L.dxf.name not in('0','Defpoints') and L.dxf.name!=d.header.get('$CLAYER','0')]
for n in dl: d.layers.remove(n)
print('dropped layers',len(dl))
d.saveas('GF_clean.dxf')
json.dump({'log':dict(log),'dropped_layers':dl,'dropped_blocks':len(drop)},open('clean_log.json','w'),ensure_ascii=False,indent=1)
print(dict(log))
