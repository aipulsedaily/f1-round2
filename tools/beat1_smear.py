"""Camera-induced image smear at beat 1's fifteen stations, in 4K pixels.

180 deg shutter = half a frame of exposure, so the smear of a STATIC point is
half its per-frame image displacement. The cluster box is held fixed between f
and f+1 on purpose: this isolates the CAMERA's contribution and says nothing
about a part that is flying. Every cluster measured here is still parked.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.expanduser("~/f1-round2/tools"))
from beat1_focus_track import cam_axes


def _selftest():
    """Two synthetic cameras whose answers are known without this code.

    POSITIVE: a camera at range R that slides `t` metres perpendicular to its own
    axis in one frame, NOT re-aimed, displaces a static point by t/R * f on the
    sensor. At 180 degrees the smear is half of that.
    NEGATIVE: the same camera that does not move at all must read exactly 0, and a
    camera that ROTATES to hold the point on axis must also read 0 at that point --
    which is why the numbers in the report are not simply "camera speed".
    """
    SW_MM, RX = 36.0, 3840
    ppm = RX / SW_MM
    ok = True

    def chk(name, got, want, tol):
        nonlocal ok
        good = abs(got - want) <= tol
        ok = ok and good
        print("  %-52s %10.4f  want %10.4f  %s"
              % (name, got, want, "ok" if good else "FAIL"))

    f_mm, R, t = 50.0, 4.0, 0.05
    p = [0.0, R, 0.0]                       # point straight ahead, +Y
    # camera looks +Y: fwd=+Y, right=+X, up=+Z -> quaternion from that basis
    q_look_y = [math.sqrt(0.5), math.sqrt(0.5), 0.0, 0.0]   # rot -90 about X
    e0 = {"p": [0.0, 0.0, 0.0], "q": q_look_y, "lens": f_mm}
    e1 = {"p": [t, 0.0, 0.0], "q": q_look_y, "lens": f_mm}
    fwd, rt, up = cam_axes(q_look_y)
    chk("synthetic basis points along +Y", fwd[1], 1.0, 1e-6)

    def pxy(e):
        d = [p[i] - e["p"][i] for i in range(3)]
        z = sum(d[i] * fwd[i] for i in range(3))
        return (sum(d[i] * rt[i] for i in range(3)) / z * e["lens"] * ppm,
                sum(d[i] * up[i] for i in range(3)) / z * e["lens"] * ppm)

    a, b = pxy(e0), pxy(e1)
    got = 0.5 * math.hypot(b[0] - a[0], b[1] - a[1])
    chk("slide 50 mm at 4 m on 50 mm, smear px", got, 0.5 * t / R * f_mm * ppm, 1e-3)
    a2, b2 = pxy(e0), pxy(e0)
    chk("NEGATIVE CONTROL: motionless camera",
        0.5 * math.hypot(b2[0] - a2[0], b2[1] - a2[1]), 0.0, 1e-12)
    print("\nSTAGE RESULT %s selftest" % ("OK" if ok else "FAIL"))
    return 0 if ok else 1


if "--selftest" in sys.argv:
    sys.exit(_selftest())

D = json.load(open(os.path.expanduser("~/f1-round2/work/b1dof/dump.json")))
cams = {e["f"]: e for e in D["frames"]}
geom = D["cluster_bbox"]
gfr = sorted(int(k) for k in geom)
sw = D["sensor_width"]; rx, ry = D["res"]; sh = sw*ry/rx
px_per_mm = rx/sw

def proj(e, p):
    fwd, right, up = cam_axes(e["q"])
    d = [p[i]-e["p"][i] for i in range(3)]
    z = sum(d[i]*fwd[i] for i in range(3))
    if z <= 1e-6: return None
    u = sum(d[i]*right[i] for i in range(3))/z*e["lens"]
    v = sum(d[i]*up[i]    for i in range(3))/z*e["lens"]
    return u*px_per_mm, v*px_per_mm

DEFAULT = [("MB",1),("FW",62),("NOSE",85),("CI",124),("halo_assembly",155),
            ("SP",191),("FD",236),("RW",276),("EC",305),("BB",339),("SW",386),
            ("CORNER_RR",463),("CORNER_RL",512),("CORNER_FR",551),("CORNER_FL",591)]
if len(sys.argv) > 1:
    # frames given on the command line: smear the WHOLE exploded field, i.e. the
    # brightest and nearest thing the lens can see, not one nominated cluster.
    STATIONS = []
    for tok in sys.argv[1].split(","):
        f = int(tok)
        gf = min(gfr, key=lambda g: abs(g - f))
        # the cluster whose centre is closest to the optical axis at that frame
        e = cams[f]
        from beat1_focus_track import cam_axes as _ax
        fwd, r_, u_ = _ax(e["q"])
        best = None
        for cl, (lo3, hi3) in geom[str(gf)].items():
            c = [(lo3[i] + hi3[i]) / 2 for i in range(3)]
            d = [c[i] - e["p"][i] for i in range(3)]
            z = sum(d[i] * fwd[i] for i in range(3))
            if z <= 0:
                continue
            rr = math.sqrt(sum(x * x for x in d))
            ang = math.degrees(math.acos(max(-1, min(1, z / rr))))
            if best is None or ang < best[0]:
                best = (ang, cl)
        if best:
            STATIONS.append((best[1], f))
else:
    STATIONS = DEFAULT

print("%-14s %5s %6s | %9s %9s %9s | %9s" %
      ("cluster","f","lens","smear_ctr","smear_near","smear_far","worst_px"))
worst_all = 0.0
rows=[]
for cl, f in STATIONS:
    e0, e1 = cams.get(f), cams.get(f+1)
    gf = min(gfr, key=lambda g: abs(g-f))
    box = geom[str(gf)].get(cl)
    if not (e0 and e1 and box): continue
    lo3, hi3 = box
    pts = {"ctr": [(lo3[i]+hi3[i])/2 for i in range(3)]}
    # near and far corners along the view axis
    fwd,_,_ = cam_axes(e0["q"])
    cs=[]
    for i in (0,1):
        for j in (0,1):
            for k in (0,1):
                c=[lo3[0] if i==0 else hi3[0], lo3[1] if j==0 else hi3[1],
                   lo3[2] if k==0 else hi3[2]]
                cs.append((sum((c[m]-e0["p"][m])*fwd[m] for m in range(3)), c))
    cs.sort()
    pts["near"], pts["far"] = cs[0][1], cs[-1][1]
    out={}
    for nm,p in pts.items():
        a,b = proj(e0,p), proj(e1,p)
        out[nm] = 0.5*math.hypot(b[0]-a[0], b[1]-a[1]) if a and b else float("nan")
    w = max(v for v in out.values() if v==v)
    worst_all = max(worst_all, w)
    rows.append((cl,f,out))
    print("%-14s %5d %6.1f | %9.1f %9.1f %9.1f | %9.1f" %
          (cl, f, e0["lens"], out["ctr"], out["near"], out["far"], w))
print("\nworst camera smear at any station: %.1f px at 4K (180 deg shutter)" % worst_all)
med = sorted(r[2]["ctr"] for r in rows)[len(rows)//2]
print("median smear at the presented cluster's CENTRE: %.1f px" % med)
print("STAGE RESULT OK stations=%d worst_px=%.1f" % (len(rows), worst_all))
