"""ROAD CORRIDOR, GROUND-REFERENCED — the check `tools/placement_gate.py` cannot make.

    blender -b <assembly>.blend --factory-startup -P v120/probe_roadclear.py -- OUT.json

WHY THIS EXISTS
---------------
`tools/placement_gate.py:227` builds the road-corridor keep-out as an ABSOLUTE
world-z band:

    volumes["road_corridor"] = {..., "zlo": -0.5, "zhi": ROAD_CLEAR_H, ...
                                "pts": [(x, y, 0.0) for ...]}

The centreline points are pinned at z = 0.0 and the band is -0.5 .. +4.5 m of
WORLD z.  This circuit's centreline `ground_z` runs **-3.670 .. +7.964 m**.
Measured over the 14 700-station 0.25 m grid:

    centreline ground_z inside the band            49.48 % of stations
    road surface entirely ABOVE the band (no test) 28.08 %
    road surface below -0.5 (the band floats)      22.44 %
    stations with ZERO tested headroom             28.08 %

So over a quarter of the lap the gate tests a slab of air that the road is not
in, and its "road corridor CLEAN" is CLEAN over the half of the lap where the
band happens to line up.  That is not a wrong number, it is an exactly-right
number about the wrong volume -- the failure mode this project has hit before
(a polygon count 0.14 % from its prediction and a factor of 11 out).

WHAT THIS DOES INSTEAD
----------------------
Same corridor, same margins, same allow/edge-family semantics, but the z band
is referenced PER SAMPLE to `C.ground_z(s, u)` -- so it is the 5.0 m of air
directly above the road, everywhere on the lap.  Positions come from
`C.project`, which is exact on this circuit (every element is a straight or a
circular arc), not from a KD-tree over a sampled centreline.

VEGETATION is excluded from the per-vertex sweep and reported separately: the
28 314 VEG emitters realize 4.7 M instances and are covered, ground-referenced
by construction, by probeC's P1/P9 ray sweep over the racing surface.  Saying
so here rather than silently dropping them.
"""
import os
exec(open(os.path.expanduser("~/f1-round2/render/world/assembly/r2/lib_probe.py")).read())

# Was `sys.argv[-1] if ... else "probe_roadclear.json"` (fixed 2026-08-02): it
# read the LAST argument whatever it was, and given nothing usable it silently
# invented a relative filename resolved against the caller's CWD.  resolve_out()
# resolves to an absolute path and refuses rather than guessing; a bare
# positional OUT.json still works for the battery scripts.
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="probe_roadclear")
print("[RC] output ->", OUT)

# Printed ROADCLEAR_FAIL and exited 0 until 2026-08-03. Blender 5.2 also returns
# 0 for a script that raised, so a probe that died halfway through was
# indistinguishable from a clean corridor. install() closes both.
sys.path.insert(0, os.path.expanduser("~/f1-round2/tools"))
import gate_exit                                                 # noqa: E402
gate_exit.install(tool="probe_roadclear")

ROAD_MARGIN = 0.50
ROAD_CLEAR_H = 4.50
ZLO_REL = -0.50

ALLOW = ("SURF_", "TER_Ground", "BR_Runoff", "BR_Gravel",
         "ARCH_Paving", "ARCH_Markings", "Floor", "Turntable_", "Platform_")
EDGE_FAMILIES = ("DR_Kerb", "SURF_Kerb", "KPU_", "BR_Subbase", "BR_Verge",
                 "ARCH_PitWall", "ARCH_RetainEdge")

R = {"contract": C.__version__, "scene": bpy.data.filepath}
T0 = time.time()

# ------------------------------------------------------------- the band ---
sg = np.arange(0.0, LAP, 0.25)
gz_c = C.ground_z(sg, np.zeros_like(sg))
R["ground_z_on_centreline"] = {
    "min": round(float(gz_c.min()), 4), "max": round(float(gz_c.max()), 4)}
inside = (gz_c >= -0.5) & (gz_c <= ROAD_CLEAR_H)
R["shipped_gate_band_alignment"] = {
    "stations": int(len(gz_c)),
    "frac_road_inside_absolute_band": round(float(inside.mean()), 4),
    "frac_road_above_band": round(float((gz_c > ROAD_CLEAR_H).mean()), 4),
    "frac_road_below_band": round(float((gz_c < -0.5).mean()), 4)}
print("[RC] ground_z %.3f .. %.3f ; the shipped gate's absolute band contains "
      "the road at %.2f %% of stations"
      % (gz_c.min(), gz_c.max(), 100 * inside.mean()))

HW_MAX = float(C.half_width(sg).max())
REACH = HW_MAX + ROAD_MARGIN                       # horizontal half-width, max


def classify(nm):
    if nm.startswith(ALLOW):
        return "allowed"
    if nm.startswith(EDGE_FAMILIES):
        return "edge"
    if nm.startswith("VEG_"):
        return "vegetation"
    return "measured"


# --------------------------------------------------------- bbox reject ----
# An object can only reach the corridor if some part of its bbox projects to
# |u| <= REACH.  Projecting the 8 bbox corners is not sufficient on its own for
# a long object that straddles a corner, so the bbox is also sampled on a grid
# whenever it is bigger than 4 m -- cheap, and it cannot reject a real hit.
def bbox_pts(ob):
    m = ob.matrix_world
    cs = np.array([list(m @ Vector(c)) for c in ob.bound_box], float)
    lo, hi = cs.min(axis=0), cs.max(axis=0)
    n = [max(2, min(24, int((hi[i] - lo[i]) / 4.0) + 2)) for i in range(2)]
    gx = np.linspace(lo[0], hi[0], n[0])
    gy = np.linspace(lo[1], hi[1], n[1])
    X, Y = np.meshgrid(gx, gy)
    return X.ravel(), Y.ravel(), lo, hi


cand, skipped, veg = [], 0, 0
for ob in bpy.data.objects:
    if ob.type != "MESH":
        continue
    k = classify(ob.name)
    if k == "allowed":
        skipped += 1
        continue
    if k == "vegetation":
        veg += 1
        continue
    X, Y, lo, hi = bbox_pts(ob)
    s_, u_ = C.project(X, Y)
    if np.nanmin(np.abs(u_)) > REACH + 2.0:
        skipped += 1
        continue
    cand.append((ob, k))

print("[RC] %d candidate objects, %d rejected on bbox, %d vegetation deferred"
      % (len(cand), skipped, veg))
sys.stdout.flush()

D = dg()
viol, closest = [], None
n_meas = 0
for ob, kind in cand:
    P = world_verts(ob, D=D)
    if P is None:
        continue
    n_meas += 1
    s_, u_ = su_of(P)
    hw = C.half_width(s_)
    lim = hw if kind == "edge" else hw + ROAD_MARGIN
    gz = C.ground_z(s_, u_)
    dz = P[:, 2] - gz
    inband = (dz >= ZLO_REL) & (dz <= ROAD_CLEAR_H)
    depth = lim - np.abs(u_)                       # >0 means inside the corridor
    depth = np.where(inband, depth, -1e9)
    i = int(np.argmax(depth))
    d = float(depth[i])
    if closest is None or d > closest[0]:
        closest = (d, ob.name, [round(float(x), 3) for x in P[i]],
                   round(float(s_[i]), 2), round(float(u_[i]), 3),
                   round(float(dz[i]), 3))
    if d > 0:
        viol.append({"object": ob.name, "kind": kind,
                     "intrusion_m": round(d, 4),
                     "at_world": [round(float(x), 3) for x in P[i]],
                     "s": round(float(s_[i]), 2), "u": round(float(u_[i]), 3),
                     "height_above_ground_m": round(float(dz[i]), 3),
                     "n_verts_inside": int((depth > 0).sum())})

viol.sort(key=lambda v: -v["intrusion_m"])
R["objects_measured"] = n_meas
R["objects_rejected_on_bbox"] = skipped
R["vegetation_deferred_to_probeC_P1_P9"] = veg
R["violations"] = viol
R["closest_approach"] = ({"clearance_m": round(-closest[0], 4),
                          "object": closest[1], "at_world": closest[2],
                          "s": closest[3], "u": closest[4],
                          "height_above_ground_m": closest[5]}
                         if closest else None)

# ----------------------------------------------------- POSITIVE CONTROL ---
# A 2 m cube standing on the road at the station where ground_z is HIGHEST --
# i.e. exactly where the shipped gate's absolute band cannot see it.  If this
# probe does not fire on it, this probe is worthless.
i_hi = int(np.argmax(gz_c))
s_hi = float(sg[i_hi])
xh, yh, _z = C.su_to_world(s_hi, 0.0)
gzh = float(C.ground_z(np.array([s_hi]), np.array([0.0]))[0])
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(float(xh), float(yh), gzh + 1.0))
ctl = bpy.context.object
ctl.name = "CTL_RoadObstacle"
bpy.context.view_layer.update()
Dc = dg()
Pc = world_verts(ctl, D=Dc)
sc_, uc_ = su_of(Pc)
gzc = C.ground_z(sc_, uc_)
dzc = Pc[:, 2] - gzc
inb = (dzc >= ZLO_REL) & (dzc <= ROAD_CLEAR_H)
depc = np.where(inb, C.half_width(sc_) + ROAD_MARGIN - np.abs(uc_), -1e9)
abs_band = (Pc[:, 2] >= -0.5) & (Pc[:, 2] <= ROAD_CLEAR_H)
R["positive_control"] = {
    "station": round(s_hi, 2), "ground_z": round(gzh, 4),
    "this_probe_intrusion_m": round(float(depc.max()), 4),
    "this_probe_fires": bool(depc.max() > 0),
    "verts_inside_shipped_gate_absolute_band": int(abs_band.sum()),
    "shipped_gate_would_fire": bool(abs_band.any())}
print("[RC] POSITIVE CONTROL at s=%.1f (ground_z %.3f): this probe %s "
      "(%.3f m in); the shipped gate's absolute band contains %d of its %d verts"
      % (s_hi, gzh, "FIRES" if depc.max() > 0 else "IS DEAD",
         depc.max(), abs_band.sum(), len(Pc)))

# ----------------------------------------------------- NEGATIVE CONTROL ---
ctl.location = (float(xh) + 3000.0, float(yh), gzh + 1.0)
bpy.context.view_layer.update()
Pn = world_verts(ctl, D=dg())
sn_, un_ = su_of(Pn)
gzn = C.ground_z(sn_, un_)
dzn = Pn[:, 2] - gzn
inbn = (dzn >= ZLO_REL) & (dzn <= ROAD_CLEAR_H)
depn = np.where(inbn, C.half_width(sn_) + ROAD_MARGIN - np.abs(un_), -1e9)
R["negative_control"] = {"this_probe_intrusion_m": round(float(depn.max()), 4),
                         "this_probe_fires": bool(depn.max() > 0)}
print("[RC] NEGATIVE CONTROL 3 km off the circuit: this probe %s"
      % ("WRONGLY FIRES" if depn.max() > 0 else "is silent, correctly"))

R["secs"] = round(time.time() - T0, 1)
R["verdict"] = ("ROADCLEAR_FAIL (%d)" % len(viol)) if viol else "ROADCLEAR_CLEAN"
print("[RC] %d violations; closest approach %s" % (len(viol), R["closest_approach"]))
for v in viol[:15]:
    print("     %-34s %8.3f m in   s=%8.2f u=%7.3f  h=%6.3f m"
          % (v["object"], v["intrusion_m"], v["s"], v["u"],
             v["height_above_ground_m"]))
write_out(OUT, R)
print("[RC] wrote", OUT, "in %.1fs" % R["secs"])

# THE CONTROLS DECIDE THE STATUS TOO, NOT ONLY THE VIOLATIONS.
#
# This probe carries its own positive and negative control (above). If the
# positive control does not fire, the probe is dead and its "CLEAN" means
# nothing; if the negative control fires, it is crying wolf. Either way the
# corridor result is unusable, and that has to reach the shell as a refusal
# rather than as the corridor verdict.
_pc = R["positive_control"]["this_probe_fires"]
_nc = R["negative_control"]["this_probe_fires"]
if not _pc or _nc:
    print("[RC] REFUSING TO REPORT: this probe's own controls misbehaved "
          "(positive fires=%s, negative fires=%s). The corridor result above "
          "is not evidence of anything." % (_pc, _nc))
    gate_exit.done("ROADCLEAR_VACUOUS")
gate_exit.done(R["verdict"])
