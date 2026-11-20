import ezdxf,collections,pickle
d=ezdxf.readfile('dxf_out/GF.dxf'); m=d.modelspace()
ins=[e for e in m if e.dxftype()=='INSERT']
for e in ins: 
    b=d.blocks.get(e.dxf.name); print('MS INSERT',e.dxf.layer,e.dxf.name,len(b),'xref' if b.block.is_xref else '', 'xscale',round(e.dxf.xscale,3), [round(v) for v in e.dxf.insert][:2])
# recursive weighted layer counts (effective layer), and types
memo={}
def walk(name,eff,mult,acc,depth=0):
    b=d.blocks.get(name)
    for e in b:
        L=e.dxf.layer; L2=eff if L=='0' and eff else L
        if e.dxftype()=='INSERT':
            acc['ins'][L2]+=mult
            if depth<12: walk(e.dxf.name,L2,mult,acc,depth+1)
        else:
            acc['ent'][L2]+=mult; acc['typ'][(L2,e.dxftype())]+=mult
acc={'ent':collections.Counter(),'ins':collections.Counter(),'typ':collections.Counter()}
walk('*Model_Space',None,1,acc)
pickle.dump(acc,open('acc.pkl','wb'))
print('TOTAL leaf ents',sum(acc['ent'].values()))
alltypes=collections.Counter()
for (L,t),n in acc['typ'].items(): alltypes[t]+=n
print(alltypes)
for L,n in acc['ent'].most_common(): print('L',n,L)
