import ezdxf,sys
F=sys.argv[1]
d=ezdxf.readfile(F)
used=[l.rstrip('\n') for l in open('appids_used.txt',encoding='utf-8') if l.strip()]
miss=[a for a in used if a not in d.appids]
print('missing',len(miss),miss[:30])
for a in miss:
    try: d.appids.new(a)
    except Exception as ex: print('fail',a,ex)
d.saveas(F); print('saved')
