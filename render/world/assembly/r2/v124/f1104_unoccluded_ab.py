"""The f1104 A/B restricted to the void the camera can ACTUALLY SEE.  R2-150.

    blender -b render/film13.blend --factory-startup \
        -P render/world/assembly/r2/v124/f1104_unoccluded_ab.py

`v124/f1104_attribution.py` is bpy-free and does not resolve occlusion, so its
34.57 % is a LOWER bound: the pit building shell hides about half the in-frustum
void in BOTH builds and those pixels correctly do not move.  This resolves it.

WHY IT RUNS ON film13 AND NOT film14.  The region of interest is the 390 m2 the
apron never had.  In film14 that ground is PAVED, so a ray from the camera to a
void sample stops on the new slab and every sample would report "occluded" --
the mask would erase itself on the very build it is meant to measure.
Occlusion is resolved once, in the DEFECTIVE world, against the things that
occlude it in BOTH builds, and the pixel set is applied to both renders.

WHY IT IS FAST, where the first version of this took over an hour and was
killed.  `scene.ray_cast` walks a depsgraph BVH over 29,415 objects, 28,314 of
which are vegetation nowhere near the pit exit.  R2-140 already measured WHAT
occludes this region -- ARCH_PitBuilding_Shell 854 of 860, then _Detail,
_Markings, _PitWall -- so this ray_casts against those four objects' own BVHs
and nothing else.  That is a narrower question than "is anything in the way",
and it is the right one: an occluder outside that list would have shown up in
R2-140's blocker census, which named every object it hit.
"""
import os
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Vector

R2 = os.path.expanduser("~/f1-round2")
sys.path.insert(0, R2 + "/world")
import world_contract as WC                                       # noqa: E402

                                                                  # noqa: E402
# TWO PROCESSES, AND THE SPLIT IS FORCED.  Blender 5.2's bundled Python has no
# PIL, and `world_contract` + the scene's BVH only exist inside Blender.  So the
# Blender half writes the pixel SETS to an .npz and the project venv half reads
# the PNGs.  The first version of this file did the import at the top and died
# on it -- and Blender exited 0 while doing so, which is exactly why the printed
# `STAGE RESULT` line and not `$?` is the evidence on this project.
OUT_NPZ = R2 + "/work/r2148/f1104_unocc.npz"

W, H, FRAME = 3840, 2160, 1104
BEFORE = R2 + "/work/r2148/f1104_film13.png"
REPEAT = R2 + "/work/r2148/f1104_film13_REPEAT.png"
AFTER = R2 + "/work/r2148/f1104_film14.png"
PATH = R2 + "/render/film14_path.json"
OCCLUDERS = ("ARCH_PitBuilding_Shell", "ARCH_PitBuilding_Detail",
             "ARCH_Markings", "ARCH_PitWall")

PLAT = dict(WC.APRON_REGIONS_CIRCUIT)


def in_rect(cx, cy, r, i=0.0):
    x0, x1, y0, y1 = r
    return (cx >= x0 + i) & (cx <= x1 - i) & (cy >= y0 + i) & (cy <= y1 - i)


S = np.arange(3360, 3500.01, 0.25)
U = np.arange(10, 42.01, 0.05)
A, B = np.meshgrid(S, U, indexing="ij")
A, B = A.ravel(), B.ravel()
P = WC.su_to_world(A, B)
z, own = WC.world_ground_z(P[:, 0], P[:, 1])
cx, cy = WC.world_to_circuit(P[:, 0], P[:, 1])
hand = np.zeros(len(A), bool)
for nm in ("pit_lane", "garages", "paddock"):
    hand |= in_rect(cx, cy, PLAT[nm])
VOID = (np.isfinite(z) & (B > WC.platform_edge(A, +1))
        & in_rect(cx, cy, PLAT["apron"]) & ~hand & (own == WC.OWNER_APRON))
pts = P[VOID].copy()
pts[:, 2] = z[VOID]
CELL = 0.25 * 0.05
print("STAGE void %d samples = %.2f m2" % (VOID.sum(), VOID.sum() * CELL))

e = [p for p in json.load(open(PATH))["path"] if p["f"] == FRAME][0]
C = np.array(e["p"])
lens = e["lens"]
w, x, y, q3 = e["q"]
M = np.array([[1 - 2 * (y * y + q3 * q3), 2 * (x * y - q3 * w), 2 * (x * q3 + y * w)],
              [2 * (x * y + q3 * w), 1 - 2 * (x * x + q3 * q3), 2 * (y * q3 - x * w)],
              [2 * (x * q3 - y * w), 2 * (y * q3 + x * w), 1 - 2 * (x * x + y * y)]])
F, Rx, Uv = M @ [0, 0, -1.0], M @ [1.0, 0, 0], M @ [0, 1.0, 0]
thx, thy = 18.0 / lens, (18.0 / lens) * H / W
print("STAGE cam f%d pitch %.2f deg lens %.2f mm"
      % (FRAME, -math.degrees(math.asin(F[2])), lens))

d = pts - C
zc = d @ F
ok = zc > 1e-6
tx = np.where(ok, (d @ Rx) / np.where(ok, zc, 1), 9)
ty = np.where(ok, (d @ Uv) / np.where(ok, zc, 1), 9)
vis = ok & (np.abs(tx) <= thx) & (np.abs(ty) <= thy)
sub = pts[vis]
px = np.clip(((tx[vis] / thx * .5 + .5) * W).astype(int), 0, W - 1)
py = np.clip(((.5 - ty[vis] / thy * .5) * H).astype(int), 0, H - 1)
los = np.degrees(np.arcsin((C[2] - sub[:, 2]) / np.linalg.norm(sub - C, axis=1)))
print("STAGE in-frustum %d samples = %.2f m2, line of sight [%.2f, %.2f] deg"
      % (len(sub), len(sub) * CELL, los.min(), los.max()))

obs = []
for nm in OCCLUDERS:
    o = bpy.data.objects.get(nm)
    if o is None:
        print("STAGE   occluder %s ABSENT from this scene" % nm)
        continue
    obs.append((nm, o, o.matrix_world.inverted()))
print("STAGE occluders resolved against: %s" % [n for n, _o, _i in obs])

keep = np.ones(len(sub), bool)
blockers = {}
for i in range(len(sub)):
    o = Vector(C.tolist())
    t = Vector(sub[i].tolist())
    for nm, ob, inv in obs:
        lo = inv @ o
        lt = inv @ t
        dv = lt - lo
        L = dv.length
        if L < 1e-6:
            continue
        dv.normalize()
        hit, _loc, _n, _fi = ob.ray_cast(lo, dv, distance=L - 0.25)
        if hit:
            keep[i] = False
            blockers[nm] = blockers.get(nm, 0) + 1
            break
    if i and i % 2000 == 0:
        print("STAGE   ...%d/%d resolved" % (i, len(sub)))
        sys.stdout.flush()

print("STAGE UNOCCLUDED %d of %d = %.2f m2 of %.2f in frustum"
      % (keep.sum(), len(sub), keep.sum() * CELL, len(sub) * CELL))
print("STAGE occluded by %s" % sorted(blockers.items(), key=lambda kv: -kv[1]))

k = np.nonzero(keep)[0]
void_un = np.unique(py[k].astype(np.int64) * W + px[k])
void_all = np.unique(py.astype(np.int64) * W + px)
occ = np.setdiff1d(np.unique(py[~keep].astype(np.int64) * W + px[~keep]), void_un)


np.savez_compressed(OUT_NPZ, void_unoccluded=void_un, void_occluded=occ,
                    void_all=void_all, res=np.array([W, H]),
                    frame=np.array([FRAME]),
                    m2=np.array([keep.sum() * CELL, len(sub) * CELL]))
print("STAGE wrote %s" % OUT_NPZ)
print(">> STAGE RESULT: F1104_UNOCC_MASKS_OK")
print("STAGE next:  .venv/bin/python "
      "render/world/assembly/r2/v124/f1104_unoccluded_read.py")
