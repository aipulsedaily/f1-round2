import json, math, sys, os
sys.path.insert(0,os.path.expanduser("~/f1-round2/tools"))
from beat1_focus_track import cam_axes
D=json.load(open(os.path.expanduser("~/f1-round2/work/b1dof/dump.json")))
cams={e["f"]:e for e in D["frames"]}; geom=D["cluster_bbox"]
gfr=sorted(int(k) for k in geom); px=D["res"][0]/D["sensor_width"]
def proj(e,p):
    fwd,r,u=cam_axes(e["q"]); d=[p[i]-e["p"][i] for i in range(3)]
    z=sum(d[i]*fwd[i] for i in range(3))
    if z<=1e-6: return None
    return (sum(d[i]*r[i] for i in range(3))/z*e["lens"]*px,
            sum(d[i]*u[i] for i in range(3))/z*e["lens"]*px)
print("%5s %10s %14s %16s" % ("f","smear_px","smear_deg_img","predicted_surviving"))
for f in [int(x) for x in sys.argv[1].split(",")]:
    e0,e1=cams.get(f),cams.get(f+1)
    if not e1: print("%5d  (no f+1)"%f); continue
    gf=min(gfr,key=lambda g:abs(g-f))
    # the on-axis cluster
    fwd,_,_=cam_axes(e0["q"]); best=None
    for cl,(lo,hi) in geom[str(gf)].items():
        c=[(lo[i]+hi[i])/2 for i in range(3)]
        d=[c[i]-e0["p"][i] for i in range(3)]
        z=sum(d[i]*fwd[i] for i in range(3))
        if z<=0: continue
        rr=math.sqrt(sum(x*x for x in d))
        ang=math.degrees(math.acos(max(-1,min(1,z/rr))))
        if best is None or ang<best[0]: best=(ang,c)
    a,b=proj(e0,best[1]),proj(e1,best[1])
    du,dv=b[0]-a[0],b[1]-a[1]
    smear=0.5*math.hypot(du,dv)
    # image row increases downward, so dy_img = -dv
    ang_img=math.degrees(math.atan2(-dv,du))%180.0
    print("%5d %10.1f %14.1f %16.1f" % (f,smear,ang_img,(ang_img+90.0)%180.0))
