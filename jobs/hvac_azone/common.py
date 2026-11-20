import math
OF=(-102931.3,-45922.5)
ROOMS={'STOR':{'O':(-106877.7,-49347.1),'T':(-3946.35,-3424.55)},
       'OFF':{'O':(-109523.6,-51626.7),'T':(-6590.65,-5706.05)}}
ANG=40.8688; C=math.cos(math.radians(ANG)); S=math.sin(math.radians(ANG))
DX=484.0
def loc(p,o):
    x,y=p[0]-o[0],p[1]-o[1]; return (x*C+y*S, -x*S+y*C)
def wld(q,o): return (o[0]+q[0]*C-q[1]*S, o[1]+q[0]*S+q[1]*C)
SUPPLY=['CD76C','CD76D','CD76E','CD76F','CD770','CD9C4','CD9C5','CD9C6','CD9C7','CD9C8','CD9C9','CD9CA','10D5A1','10D5A2','10D5A4']
VALVES=['D053B','D053C','D053D','D053E','D05A2','D0547']
PIPE_SHORT=['D0542','D0544','D0545','D0546','D054A','D054B','D054C']
PIPE_DROP=['D053F','D0541','D0543','D054E','D054F','D0550']
PIPE_TEE=['D054D','D0548','D0549']
TAG=['CF3F5']
FA_CONN=['10D5A7','10D5A9','10D5AB']
