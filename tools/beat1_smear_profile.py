import os
import json, math, sys
sys.path.insert(0,os.path.expanduser("~/f1-round2/tools"))
from beat1_focus_track import cam_axes
D=json.load(open(os.path.expanduser("~/f1-round2/work/b1dof/dump.json")))
cams={e["f"]:e for e in D["frames"]}; geom=D["cluster_bbox"]
gfr=sorted(int(k) for k in geom); px=D["res"][0]/D["sensor_width"]
def sm(f):
    e0,e1=cams.get(f),cams.get(f+1)
    if not e1: return None
    gf=min(gfr,key=lambda g:abs(g-f))
    fwd,_,_=cam_axes(e0["q"]); best=None
    for cl,(lo,hi) in geom[str(gf)].items():
        c=[(lo[i]+hi[i])/2 for i in range(3)]
        d=[c[i]-e0["p"][i] for i in range(3)]
        z=sum(d[i]*fwd[i] for i in range(3))
        if z<=0: continue
        rr=math.sqrt(sum(x*x for x in d))
        a=math.degrees(math.acos(max(-1,min(1,z/rr))))
        if best is None or a<best[0]: best=(a,c)
    if not best: return None
    out=[]
    for e in (e0,e1):
        fw,r,u=cam_axes(e["q"]); d=[best[1][i]-e["p"][i] for i in range(3)]
        z=sum(d[i]*fw[i] for i in range(3))
        if z<=1e-6: return None
        out.append((sum(d[i]*r[i] for i in range(3))/z*e["lens"]*px,
                    sum(d[i]*u[i] for i in range(3))/z*e["lens"]*px))
    return 0.5*math.hypot(out[1][0]-out[0][0], out[1][1]-out[0][1])
vals={f:sm(f) for f in range(1,792)}
vals={f:v for f,v in vals.items() if v is not None}
def stats(lo,hi,name):
    s=sorted(v for f,v in vals.items() if lo<=f<=hi)
    if not s: print(name,"no data"); return
    n=len(s)
    over=[x for x in s if x>20]
    print("%-28s n=%4d  median %6.1f  p90 %7.1f  max %7.1f   frames over 20 px: %4d (%.0f%%)"
          % (name,n,s[n//2],s[int(n*0.9)],s[-1],len(over),100*len(over)/n))
stats(1,791,"beat 1, all")
stats(1,590,"  the presentation tour")
stats(591,647,"  CORNER_FL + close-out")
stats(648,791,"  PROTECTED f648-792")
print("STAGE RESULT OK")
