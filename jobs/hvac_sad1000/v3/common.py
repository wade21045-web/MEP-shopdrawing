import math
ANG=18.41; C=math.cos(math.radians(ANG)); S=math.sin(math.radians(ANG))
DIFF={'D050':(-61991.5,-32855.5),'D043':(-59145.0,-31908.0),'D044':(-55411.5,-30665.5),'D045':(-52565.0,-29717.5)}
def loc(p,o):
    x,y=p[0]-o[0],p[1]-o[1]; return (x*C+y*S, -x*S+y*C)
def wld(q,o): return (o[0]+q[0]*C-q[1]*S, o[1]+q[0]*S+q[1]*C)
