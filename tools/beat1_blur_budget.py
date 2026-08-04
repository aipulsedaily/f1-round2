import json, math, sys
sys.path.insert(0,"/home/zany/f1-round2/tools")
from beat1_focus_track import cam_axes, blur_px
D=json.load(open("/home/zany/f1-round2/work/b1dof/dump.json"))
cams={e["f"]:e for e in D["frames"]}; geom=D["cluster_bbox"]
gfr=sorted(int(k) for k in geom); px=D["res"][0]/D["sensor_width"]
rows=[]
for f in range(1,792):
    e0,e1=cams.get(f),cams.get(f+1)
    if not e1: continue
    gf=min(gfr,key=lambda g:abs(g-f))
    fwd,_,_=cam_axes(e0["q"]); best=None
    for cl,(lo,hi) in geom[str(gf)].items():
        c=[(lo[i]+hi[i])/2 for i in range(3)]
        d=[c[i]-e0["p"][i] for i in range(3)]
        z=sum(d[i]*fwd[i] for i in range(3))
        if z<=0: continue
        rr=math.sqrt(sum(x*x for x in d))
        a=math.degrees(math.acos(max(-1,min(1,z/rr))))
        if best is None or a<best[0]: best=(a,c,rr)
    if not best: continue
    _,c,rng=best
    pr=[]
    for e in (e0,e1):
        fw,r,u=cam_axes(e["q"]); d=[c[i]-e["p"][i] for i in range(3)]
        z=sum(d[i]*fw[i] for i in range(3))
        if z<=1e-6: pr=None; break
        pr.append((sum(d[i]*r[i] for i in range(3))/z*e["lens"]*px,
                   sum(d[i]*u[i] for i in range(3))/z*e["lens"]*px))
    if not pr: continue
    sm=0.5*math.hypot(pr[1][0]-pr[0][0], pr[1][1]-pr[0][1])
    df=blur_px(e0["lens"], e0["fstop"], e0["focus_m"], max(rng,1e-3), px)
    rows.append((f,sm,df))
def rep(lo,hi,name):
    R=[r for r in rows if lo<=r[0]<=hi]
    if not R: return
    n=len(R)
    mot=sum(1 for _,s,d in R if s>d)
    both_ok=sum(1 for _,s,d in R if max(s,d)<=2.0)
    print("%-26s n=%4d  motion>defocus in %4d (%3.0f%%)   both under 2 px in %4d (%2.0f%%)   median motion %6.1f  median defocus %6.1f"
          % (name,n,mot,100*mot/n,both_ok,100*both_ok/n,
             sorted(s for _,s,_ in R)[n//2], sorted(d for _,_,d in R)[n//2]))
rep(1,791,"beat 1, all")
rep(1,590,"  the presentation tour")
rep(591,647,"  CORNER_FL + close-out")
rep(648,791,"  PROTECTED f648-792")
