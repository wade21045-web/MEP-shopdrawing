import ezdxf,pickle
d=ezdxf.readfile('out/input.dxf'); m=d.modelspace()
for h in ['107D44','107D46','107D50','107D52','107D54','107D56']:
    e=d.entitydb[h]
    print(h,e.dxf.name,tuple(round(v,1) for v in e.dxf.insert),e.dxf.rotation,e.dxf.xscale)
    for v in e.virtual_entities():
        if v.dxftype() in('LWPOLYLINE','POLYLINE'):
            pts=[(round(p[0],1),round(p[1],1)) for p in (v.get_points('xy') if v.dxftype()=='LWPOLYLINE' else [x.dxf.location for x in v.vertices])]
            print('  ',v.dxftype(),v.dxf.layer,pts[:5])
        else: print('  ',v.dxftype(),v.dxf.layer)
