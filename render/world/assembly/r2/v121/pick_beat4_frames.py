"""Which beat-4 frames actually LOOK at the stretch of north wall that moved?

    blender -b <scene with ONER> --factory-startup -P pick_beat4_frames.py -- OUT.json

The wall was pushed outboard over route t 63.6 -> 96.0 (world x 78 -> 110,
y 8.6 -> 14.7).  A frame is only evidence if the camera can see that stretch, so
this scores every beat-4 frame by:
    * distance from the camera to the pushed wall segment
    * the angle between the camera's -Z and the segment (is it in shot at all)
and prints the frames where the answer is "yes, close, and in front".
"""
import sys, os, re, json, math
import bpy
import numpy as np
from mathutils import Vector

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "world"))
import world_contract as WC   # noqa: E402

# WHERE THIS WRITES.  Was a bare `OUT = sys.argv[-1]` (fixed 2026-08-02).  With
# no `--` on the command line, sys.argv[-1] is THIS FILE, and `open(OUT, "w")`
# then overwrites the script with its own JSON output -- reproduced 2026-08-02
# on a copy, which destroyed itself in one run.  resolve_out() takes only the
# args after `--`, resolves to an absolute path, and refuses when told nothing.
_LIB = "/home/zany/f1-round2/render/world/assembly/r2/lib_probe.py"
_BLK = re.search(r"^# --- BEGIN resolve_out.*?^# --- END resolve_out.*?$",
                 open(_LIB).read(), re.S | re.M)
if not _BLK:
    raise SystemExit("[beat4] no resolve_out block in %s" % _LIB)
exec(compile(_BLK.group(0), _LIB, "exec"))
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="pick_beat4_frames")
print("[beat4] output ->", OUT)
scn = bpy.context.scene
cam = bpy.data.objects.get("ONER")
assert cam is not None, "no ONER camera in %s" % bpy.data.filepath

# the pushed stretch, as the contract puts it (+8.000) and as assembly5 built it
TT = np.linspace(63.6, 96.0, 40)
X, Y, H = WC.access_route_arrays(TT)
WALL = np.stack([X - np.sin(H) * 8.0, Y + np.cos(H) * 8.0,
                 np.full(len(TT), WC.APRON_Z + 1.2)], axis=1)

F0, F1 = 1057, 1190
rows = []
for f in range(F0, F1 + 1):
    scn.frame_set(f)
    p = np.array(cam.matrix_world.translation)
    fwd = np.array((cam.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized())
    d = WALL - p
    r = np.linalg.norm(d, axis=1)
    u = d / r[:, None]
    cosang = u @ fwd
    ang = np.degrees(np.arccos(np.clip(cosang, -1, 1)))
    infront = ang < 35.0
    rows.append(dict(frame=f, cam=[round(float(x), 2) for x in p],
                     min_dist_m=round(float(r.min()), 2),
                     nearest_t=round(float(TT[int(r.argmin())]), 1),
                     best_ang_deg=round(float(ang.min()), 1),
                     seg_in_fov_frac=round(float(infront.mean()), 3),
                     score=round(float(infront.mean() / max(r.min(), 1.0)), 5)))

rows.sort(key=lambda r: -r["score"])
print("\nBEST BEAT-4 FRAMES FOR SEEING THE PUSHED WALL STRETCH (t 63.6..96.0):")
print("  frame   cam xyz                    min_dist  nearest_t  best_ang  frac_in_fov")
for r in rows[:15]:
    print("  %5d   %-26s %7.2f m   t=%5.1f    %5.1f deg   %.2f"
          % (r["frame"], str(r["cam"]), r["min_dist_m"], r["nearest_t"],
             r["best_ang_deg"], r["seg_in_fov_frac"]))
rows.sort(key=lambda r: r["frame"])
json.dump({"scene": bpy.data.filepath, "rows": rows}, open(OUT, "w"), indent=0)
print("\nwrote", OUT)
