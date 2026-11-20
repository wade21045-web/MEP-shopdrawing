import pickle,numpy as np,ezdxf
from scipy.spatial import cKDTree
B=pickle.load(open('fp_base.pkl','rb'))['A$C66761927']
off=np.array([8046.452163030306, 18543.75074625024])
TBl=cKDTree(B); TBw=cKDTree(B+off)
for k,fr,t in [('01','MS',(28400.08,-39461.15)),('23','MS',(28399.55,-39461.81)),('off','MS',(-151883.20,-20917.26))]:
    A=pickle.load(open(f'fp_{k}.pkl','rb'))[fr]; A=A[::5]
    for nm,T,tt in [('local',TBl,np.array(t)),('world',TBw,np.array(t)),('local+off',TBw,np.array(t)+off)]:
        d,_=T.query(A+tt); print(k,nm,round(np.mean(d<2),3),round(np.mean(d<50),3))
