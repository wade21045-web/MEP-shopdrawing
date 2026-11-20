import pickle,numpy as np,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
PA=pickle.load(open('pa.pkl','rb')); PB=pickle.load(open('pb.pkl','rb'))
fig,ax=plt.subplots(figsize=(24,16))
for P,c,s in((PA,'blue',1),(PB,'red',1)):
    a=np.vstack([v for L,v in P.items() if L.startswith('DUCT-') or L.startswith('EQ-') and len(v)])
    ax.scatter(a[:,0],a[:,1],s=s,c=c,alpha=0.4)
off=pickle.load(open('off_dec.pkl','rb'))
G=pickle.load(open('grid_acd.pkl','rb'))
for o in G:
    if 'AXISO' in o[1]: continue
    if 200000<o[6]<400000: ax.text(o[5],o[6],o[2][0],fontsize=8)
ax.set_xlim(-140000,60000); ax.set_ylim(225000,365000); ax.set_aspect('equal'); ax.grid(True)
fig.savefig('ov.png',dpi=60)
