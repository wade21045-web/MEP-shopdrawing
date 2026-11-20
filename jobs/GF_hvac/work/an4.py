import ezdxf,collections,pickle
d=ezdxf.readfile('dxf_out/GF.dxf'); m=d.modelspace()
from ezdxf import bbox
def walk(name,eff,acc,tx,depth=0):
    for e in d.blocks.get(name):
        L=e.dxf.layer; L2=eff if L=='0' and eff else L
        if e.dxftype()=='INSERT':
            if depth<12: walk(e.dxf.name,L2,acc,tx,depth+1)
        else:
            acc[L2]+=1
            if e.dxftype() in('TEXT','MTEXT','ATTDEF') and len(tx[L2])<5:
                try: t=e.plain_text() if e.dxftype()=='MTEXT' else e.dxf.text
                except: t=e.dxf.get('tag','')
                tx[L2].append(t.replace('\n',' ')[:25])
R={}
seen=set()
for e in m:
    if e.dxftype()=='INSERT' and e.dxf.name not in seen and len(d.blocks.get(e.dxf.name)):
        seen.add(e.dxf.name); acc=collections.Counter(); tx=collections.defaultdict(list)
        walk(e.dxf.name,e.dxf.layer if e.dxf.layer!='0' else None,acc,tx)
        R[e.dxf.name]=(acc,dict(tx))
        try:
            bb=bbox.extents([e],fast=True); print('##',e.dxf.name,'bbox',[round(v) for v in bb.extmin][:2],[round(v) for v in bb.extmax][:2])
        except Exception as ex: print('##',e.dxf.name,'bbox err',ex)
        for L,n in acc.most_common(): print('  ',n,L,tx.get(L,''))
pickle.dump(R,open('blk.pkl','wb'))
