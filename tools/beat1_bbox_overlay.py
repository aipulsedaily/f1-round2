"""Draw the cluster's predicted bbox projection onto the frame it was measured on.

If the framing arithmetic in beat1_present_gate / build_beatsheet is right, the
box lands on the part. If it is wrong, this shows it immediately, in the only
currency this project accepts.
"""
import os
import json, math, sys
sys.path.insert(0,os.path.expanduser("~/f1-round2/tools"))
from beat1_focus_track import cam_axes
from PIL import Image, ImageDraw
D=json.load(open(os.path.expanduser("~/f1-round2/work/b1dof/dump.json")))
cams={e["f"]:e for e in D["frames"]}; geom=D["cluster_bbox"]
gfr=sorted(int(k) for k in geom); RX,RY=D["res"]; SW=D["sensor_width"]
px=RX/SW
f=int(sys.argv[1]); src=sys.argv[2]; dst=sys.argv[3]
cl=sys.argv[4] if len(sys.argv)>4 else None
e=cams[f]; gf=min(gfr,key=lambda g:abs(g-f))
fwd,r,u=cam_axes(e["q"])
if cl is None:
    best=None
    for k,(lo,hi) in geom[str(gf)].items():
        c=[(lo[i]+hi[i])/2 for i in range(3)]
        d=[c[i]-e["p"][i] for i in range(3)]
        z=sum(d[i]*fwd[i] for i in range(3))
        if z<=0: continue
        rr=math.sqrt(sum(x*x for x in d))
        a=math.degrees(math.acos(max(-1,min(1,z/rr))))
        if best is None or a<best[0]: best=(a,k)
    cl=best[1]
lo,hi=geom[str(gf)][cl]
def scr(p):
    d=[p[i]-e["p"][i] for i in range(3)]
    z=sum(d[i]*fwd[i] for i in range(3))
    if z<=1e-6: return None
    uu=sum(d[i]*r[i] for i in range(3))/z*e["lens"]*px
    vv=sum(d[i]*u[i] for i in range(3))/z*e["lens"]*px
    return (RX/2+uu, RY/2-vv)
C=[]
for i in (0,1):
    for j in (0,1):
        for k in (0,1):
            C.append([lo[0] if i==0 else hi[0], lo[1] if j==0 else hi[1],
                      lo[2] if k==0 else hi[2]])
S=[scr(c) for c in C]
E=[(0,1),(0,2),(0,4),(1,3),(1,5),(2,3),(2,6),(3,7),(4,5),(4,6),(5,7),(6,7)]
im=Image.open(src).convert("RGB"); dr=ImageDraw.Draw(im)
for a,b in E:
    if S[a] and S[b]: dr.line([S[a],S[b]], fill=(255,60,60), width=8)
c=[(lo[i]+hi[i])/2 for i in range(3)]; sc=scr(c)
if sc: dr.ellipse([sc[0]-24,sc[1]-24,sc[0]+24,sc[1]+24], outline=(60,255,60), width=8)
xs=[s[0] for s in S if s]; ys=[s[1] for s in S if s]
print("f%d  %s   projected box spans x %.0f..%.0f  y %.0f..%.0f  in a %dx%d frame"
      % (f, cl, min(xs),max(xs),min(ys),max(ys),RX,RY))
print("     that is %.2f of frame width and %.2f of frame height"
      % ((max(xs)-min(xs))/RX, (max(ys)-min(ys))/RY))
im.resize((1280,720), Image.LANCZOS).save(dst)
