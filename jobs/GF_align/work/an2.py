import ezdxf,collections,sys
from ezdxf import bbox
f=sys.argv[1]; d=ezdxf.readfile(f); m=d.modelspace()
for b in d.blocks:
    fl=b.block.dxf.flags
    if fl&4: print('XREF',b.name,b.block.dxf.get('xref_path',''))
# top-level inserts with big content
def cnt(n,dep=0,memo={}):
    if n in memo: return memo[n]
    s=0
    for e in d.blocks.get(n):
        if e.dxftype()=='INSERT' and dep<10 and e.dxf.name in d.blocks: s+=cnt(e.dxf.name,dep+1)
        else: s+=1
    memo[n]=s; return s
for e in m:
    if e.dxftype()=='INSERT':
        c=cnt(e.dxf.name) if e.dxf.name in d.blocks else -1
        if c>300: print('BIG',e.dxf.layer,e.dxf.name,c,[round(v) for v in e.dxf.insert][:2],round(e.dxf.xscale,3),round(e.dxf.rotation,2))
try:
    bb=bbox.extents(m,fast=True); print('MS extents',bb.extmin,bb.extmax)
except Exception as ex: print(ex)
for l in d.layouts:
    if l.name!='Model':
        for e in l:
            if e.dxftype()=='VIEWPORT': print('VP',l.name,[round(v) for v in e.dxf.center][:2],round(e.dxf.width),round(e.dxf.height),'view',[round(v) for v in e.dxf.view_center_point][:2],round(e.dxf.view_height),round(e.dxf.get('view_twist_angle',0),2))
