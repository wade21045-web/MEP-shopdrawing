import ezdxf,collections,re,pickle
from lib import walk,txt
from ezdxf import bbox
d=ezdxf.readfile('/workspace/GF_hvac/output/GF_暖通+建筑结构底图.dxf'); m=d.modelspace()
FL=re.compile(r'风口|天花末端|DIFF|GRILL',re.I)
def stop(e,ef,ch): return bool(FL.search(ef)) or bool(re.search(r'风口|DIFF|GRILL|散流|百叶',e.dxf.name,re.I))
ins=collections.Counter(); raw=collections.Counter(); R=[]; ex={}
for e,M,ef,ch in walk(d,m,stop=stop):
    if ch and ch[0] not in('A$C5E357C2F','A$C124230B8') and ch: pass
    root=ch[0] if ch else 'MS'
    if not (FL.search(ef) or (e.dxftype()=='INSERT' and stop(e,ef,ch))): continue
    if e.dxftype()=='INSERT':
        ins[(e.dxf.name,ef,root)]+=1
        try: bb=bbox.extents([e],fast=True); c=M.transform(bb.center); sz=(bb.size.x,bb.size.y)
        except: c=M.transform(e.dxf.insert); sz=(0,0)
        import math
        R.append(dict(kind='INSERT',name=e.dxf.name,layer=ef,x=c.x,y=c.y,sx=sz[0],sy=sz[1],rot=(e.dxf.rotation+math.degrees(math.atan2(M[0,1],M[0,0])))%360,root=root,chain=ch,atts={a.dxf.tag:a.dxf.text for a in e.attribs}))
    else:
        raw[(e.dxftype(),ef,root)]+=1
        try: bb=bbox.extents([e],fast=True); c=M.transform(bb.center); sz=(bb.size.x,bb.size.y)
        except: continue
        R.append(dict(kind=e.dxftype(),name='',layer=ef,x=c.x,y=c.y,sx=sz[0],sy=sz[1],root=root,chain=ch,text=txt(e)))
pickle.dump(R,open('hv_raw.pkl','wb'))
for k,n in ins.most_common(60):
    b=d.blocks.get(k[0]); print(n,k,len(b),[x.dxf.tag for x in b if x.dxftype()=='ATTDEF'][:3])
print('RAW'); 
for k,n in raw.most_common(30): print(n,k)
