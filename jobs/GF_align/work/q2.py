import ezdxf
d=ezdxf.readfile('/workspace/GF_hvac/output/GF_暖通+建筑结构底图.dxf')
for e in d.modelspace().query('INSERT'):
    print(e.dxf.name,e.dxf.layer,e.dxf.insert,e.has_extension_dict, d.layers.get(e.dxf.layer).is_on() if d.layers.has_entry(e.dxf.layer) else None)
    if e.has_extension_dict:
        x=e.get_extension_dict(); print(' ext',list(x.keys()))
