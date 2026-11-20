import ezdxf,sys,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy, LineweightPolicy
src,tag=sys.argv[1],sys.argv[2]
d=ezdxf.readfile(src); m=d.modelspace()
fig=plt.figure(figsize=(24,13),dpi=150); ax=fig.add_axes([0,0,1,1])
cfg=Configuration(background_policy=BackgroundPolicy.WHITE,color_policy=ColorPolicy.COLOR,lineweight_policy=LineweightPolicy.RELATIVE_FIXED,lineweight_scaling=0.15,min_lineweight=0.08)
ctx=RenderContext(d); Frontend(ctx,MatplotlibBackend(ax),config=cfg).draw_layout(m,finalize=True)
views={'全图':(-150000,95000,-100000,35000),'局部1_中部':(-60000,-20000,-20000,5000),'局部2_剖面':(-121000,-101000,14000,22000),'结构底图':(-530000,-240000,-100000,160000)}
for k,(x0,x1,y0,y1) in views.items():
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal',adjustable='datalim')
    fig.savefig(f'prev_{tag}_{k}.png',dpi=150,facecolor='white'); print('saved',k,flush=True)
