import ezdxf,math,pickle
d=ezdxf.readfile('out/input.dxf'); db=d.entitydb
res=pickle.load(open('region.pkl','rb'))
for r in res:
    if r[2] in ('核对-装饰风口(参照)','核对-装饰有暖通无','DIM-风机盘管','DUCT-回风风口','天花末端点位','PIPE-双管') or (r[1]=='INSERT' and r[2] in('VANNE','DUCT-送风阀门','管道1','管道2','接头')):
        e=db[r[0]]
        extra=''
        if e.dxftype()=='INSERT': extra=f"{e.dxf.name} ins={tuple(round(v) for v in e.dxf.insert)} rot={e.dxf.rotation:.2f} sc={e.dxf.xscale:.2f},{e.dxf.yscale:.2f}"
        if e.dxftype()=='TEXT': extra=f"{e.dxf.text!r} ins={tuple(round(v) for v in e.dxf.insert)} rot={e.dxf.rotation:.2f} h={e.dxf.height}"
        print(r[0],r[1],r[2],r[6],r[7],extra)
