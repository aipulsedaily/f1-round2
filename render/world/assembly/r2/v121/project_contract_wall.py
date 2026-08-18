"""Project the CONTRACT's declared north-wall line into the ONER camera.

    blender -b world/camera_rig.blend --factory-startup -P project_contract_wall.py -- OUT.json

Two methods have already said the wall in assembly5 is 3.3 m outboard: the
module's own `transit_wall_offset` and a per-object vertex fingerprint.  This is
the third, and it is the one that answers in the picture's own coordinates:
where, in pixels, does `TRANSIT_NORTH_OFFSET_M` = +8.000 land?  Overlay that on
both renders and the wall either sits under the line or it does not.

Also emits the same line for assembly5's ACTUAL built offset so both
predictions can be drawn.
"""
import sys, os, re, json
import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view

R2 = os.path.expanduser("~/f1-round2")
sys.path.insert(0, os.path.join(R2, "world"))
import world_contract as WC   # noqa: E402

# WHERE THIS WRITES.  Was a bare `OUT = sys.argv[-1]` (fixed 2026-08-02).  With
# no `--` on the command line, sys.argv[-1] is THIS FILE, and `open(OUT, "w")`
# then overwrites the script with its own JSON output -- reproduced 2026-08-02
# on a copy, which destroyed itself in one run.  resolve_out() takes only the
# args after `--`, resolves to an absolute path, and refuses when told nothing.
_LIB = os.path.expanduser("~/f1-round2/render/world/assembly/r2/lib_probe.py")
_BLK = re.search(r"^# --- BEGIN resolve_out.*?^# --- END resolve_out.*?$",
                 open(_LIB).read(), re.S | re.M)
if not _BLK:
    raise SystemExit("[wall] no resolve_out block in %s" % _LIB)
exec(compile(_BLK.group(0), _LIB, "exec"))
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="project_contract_wall")
print("[wall] output ->", OUT)
scn = bpy.context.scene
cam = bpy.data.objects["ONER"]

# assembly5's BUILT inner-face offset, measured off assembly5.blend earlier
# (t, lateral offset of the inner face).  Linear between samples.
A5_T = np.array([6, 63, 66, 69, 72, 75, 78, 81, 84, 87, 90, 93, 96], float)
A5_V = np.array([7.840, 7.840, 8.0177, 8.7364, 9.1211, 9.687, 10.0729,
                 10.3237, 10.6694, 10.8332, 11.0355, 11.1336, 11.1729], float)

TT = np.linspace(6.0, 96.0, 361)
X, Y, H = WC.access_route_arrays(TT)
ZTOP = WC.APRON_Z + WC.TRANSIT_NORTH_TOP_Z

lines = {}
for tag, off in (("contract_8m", np.full(len(TT), 8.0)),
                 ("assembly5_built", np.interp(TT, A5_T, A5_V))):
    P = np.stack([X - np.sin(H) * off, Y + np.cos(H) * off,
                  np.full(len(TT), ZTOP)], axis=1)
    lines[tag] = P

res = {}
for f in (1078, 1081, 1090):
    scn.frame_set(f)
    W, Hh = scn.render.resolution_x, scn.render.resolution_y
    d = {"res": [W, Hh], "cam": [round(float(v), 3) for v in cam.matrix_world.translation]}
    for tag, P in lines.items():
        px = []
        for p in P:
            u = world_to_camera_view(scn, cam, bpy.types.Object.bl_rna and __import__("mathutils").Vector(p))
            if u.z > 0.0 and -0.2 < u.x < 1.2 and -0.2 < u.y < 1.2:
                px.append([round(float(u.x * W), 1), round(float((1.0 - u.y) * Hh), 1)])
            else:
                px.append(None)
        d[tag] = px
    res[str(f)] = d
    vis = {t: sum(1 for q in d[t] if q) for t in lines}
    print("frame %d  visible samples: %s" % (f, vis))

json.dump(res, open(OUT, "w"), indent=0)
print("wrote", OUT)
