import pickle,math
res=pickle.load(open('region.pkl','rb'))
O={'FLOUR':(-102931.3,-45922.5),'STOR':(-106877.7,-49347.1),'OFF':(-109523.6,-51626.7)}
a=math.radians(-40.8688)
def loc(p,o):
    x,y=p[0]-o[0],p[1]-o[1]; return (x*math.cos(a)-y*math.sin(a), x*math.sin(a)+y*math.cos(a))
skip=('M_AX_CV','新底图','核对','TH_DIM','C-天花')
for k,o in O.items():
    print('=====',k)
    rows=[]
    for r in res:
        if r[2].startswith(skip): continue
        c=((r[6][0]+r[7][0])/2,(r[6][1]+r[7][1])/2)
        l=loc(c,o)
        if -2500<l[0]<3500 and -3800<l[1]<1500:
            rows.append((r[2],r[1],r[3],round(l[0]),round(l[1]),r[4],r[5],r[0]))
    for x in sorted(rows): print(x)
