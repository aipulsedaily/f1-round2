"""The f1104 regions of interest, as PIXEL SETS at the render resolution.

    blender -b render/film13.blend --factory-startup -P work/r2148/f1104_masks.py \
        -- --path render/film14_path.json --res 3840 2160 --out work/r2148/f1104_masks.npz

WHY THIS RUNS ON film13 AND NOT film14.  The region of interest is the 390 m2
the apron never had.  In film14 that ground is PAVED, so a ray from the camera
to a void sample stops on the new slab and every sample reports "occluded" --
the mask would erase itself on the very build it is meant to measure.  So
occlusion is resolved once, in the DEFECTIVE world, against the things that
occlude it in BOTH builds (the pit building shell, mostly), and the resulting
pixel set is then applied to both renders unchanged.  R2-140's own occlusion
pass did the same thing for the same reason.

TWO CONTROLS, and neither is optional:

  CTL_PAVED   track asphalt at s 3380-3480, u 0-9.  Ground that is built in
              BOTH builds.  If this moves as much as the void region does, the
              renderer's sampling noise is the signal and nothing has been
              measured.  This is the 1.33 % control R2-132's diagnostic camera
              used.
  CTL_SKY     the top 8 % of the frame.  Nothing in this fix can reach it.  A
              second, independent floor on "how much does a re-render of the
              same frame differ from itself".
"""
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Quaternion, Vector

sys.path.insert(0, "/home/zany/f1-round2/world")
import world_contract as WC                                       # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default=None, n=1):
    if "--" + name in argv:
        i = argv.index("--" + name)
        return argv[i + 1:i + 1 + n] if n > 1 else argv[i + 1]
    return default


PATH = opt("path", "/home/zany/f1-round2/render/film14_path.json")
RES = [int(x) for x in opt("res", ["3840", "2160"], n=2)]
OUT = opt("out", "/home/zany/f1-round2/work/r2148/f1104_masks.npz")
FRAME = int(opt("frame", "1104"))
W, H = RES

# ---- the void, exactly as R2-132 / R2-140 define it -----------------------
PLAT = dict(WC.APRON_REGIONS_CIRCUIT)


def in_rect(cx, cy, r, i=0.0):
    x0, x1, y0, y1 = r
    return (cx >= x0 + i) & (cx <= x1 - i) & (cy >= y0 + i) & (cy <= y1 - i)


S = np.arange(3360, 3500.01, 0.25)
U = np.arange(10, 42.01, 0.05)
A, B = np.meshgrid(S, U, indexing="ij")
A = A.ravel()
B = B.ravel()
P = WC.su_to_world(A, B)
z, own = WC.world_ground_z(P[:, 0], P[:, 1])
pe = WC.platform_edge(A, +1)
cx, cy = WC.world_to_circuit(P[:, 0], P[:, 1])
hand = np.zeros(len(A), bool)
for nm in ("pit_lane", "garages", "paddock"):
    hand |= in_rect(cx, cy, PLAT[nm])
VOID = (np.isfinite(z) & (B > pe) & in_rect(cx, cy, PLAT["apron"])
        & ~hand & (own == WC.OWNER_APRON))
print("STAGE void samples %d = %.2f m2" % (VOID.sum(), VOID.sum() * 0.25 * 0.05))

# ---- the camera, read from the path the film was BUILT with ---------------
e = [p for p in json.load(open(PATH))["path"] if p["f"] == FRAME][0]
C = np.array(e["p"])
lens = e["lens"]
M = Quaternion(e["q"]).to_matrix()
F = np.array(M @ Vector((0, 0, -1)))
F /= np.linalg.norm(F)
R = np.array(M @ Vector((1, 0, 0)))
R /= np.linalg.norm(R)
Uv = np.array(M @ Vector((0, 1, 0)))
Uv /= np.linalg.norm(Uv)
thx = (36.0 / 2) / lens
thy = thx * H / W
print("STAGE cam f%d loc %s lens %.3f view-axis pitch %.2f deg"
      % (FRAME, np.round(C, 3).tolist(), lens,
         -math.degrees(math.asin(F[2]))))

scn = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()


def project(pts):
    d = pts - C
    zc = d @ F
    ok = zc > 1e-6
    tx = np.where(ok, (d @ R) / np.where(ok, zc, 1), 9)
    ty = np.where(ok, (d @ Uv) / np.where(ok, zc, 1), 9)
    vis = ok & (np.abs(tx) <= thx) & (np.abs(ty) <= thy)
    px = np.clip(((tx / thx * 0.5 + 0.5) * W).astype(int), 0, W - 1)
    py = np.clip(((0.5 - ty / thy * 0.5) * H).astype(int), 0, H - 1)
    return vis, px, py, np.linalg.norm(d, axis=1)


def region(tag, pts, occlude=True, sub=4000):
    pts = pts[::max(1, len(pts) // sub)]
    vis, px, py, dist = project(pts)
    n_in = int(vis.sum())
    if not n_in:
        print("STAGE %-14s NOT IN FRAME" % tag)
        return np.zeros(0, np.int64), {}
    sel = np.nonzero(vis)[0]
    keep = np.ones(len(sel), bool)
    blockers = {}
    if occlude:
        for j, i in enumerate(sel):
            o = Vector(C.tolist())
            dv = Vector(pts[i].tolist()) - o
            L = dv.length
            dv.normalize()
            hit, _loc, _n, _fi, obj, _m = scn.ray_cast(dg, o, dv,
                                                       distance=L - 0.25)
            if hit:
                keep[j] = False
                blockers[obj.name] = blockers.get(obj.name, 0) + 1
    k = sel[keep]
    idx = np.unique(py[k].astype(np.int64) * W + px[k])
    los = np.degrees(np.arcsin((C[2] - pts[k][:, 2]) / dist[k])) if len(k) else []
    print("STAGE %-14s %d samples in frustum, %d unoccluded -> %d distinct px "
          "| LOS %s | blockers %s"
          % (tag, n_in, int(keep.sum()), len(idx),
             ("[%.1f, %.1f] deg" % (min(los), max(los))) if len(k) else "-",
             sorted(blockers.items(), key=lambda kv: -kv[1])[:3]))
    return idx, blockers


void_px, _ = region("VOID", P[VOID], occlude=True)

CS = np.arange(3380, 3480.01, 0.5)
CU = np.arange(0.0, 9.01, 0.25)
CA, CB = np.meshgrid(CS, CU, indexing="ij")
ctl_pts = WC.su_to_world(CA.ravel(), CB.ravel())
ctl_px, _ = region("CTL_PAVED", ctl_pts, occlude=True)

sky_rows = np.arange(0, int(H * 0.08))
sky_px = (sky_rows[:, None] * W + np.arange(W)[None, :]).ravel()
print("STAGE %-14s %d px (top 8 %% of frame)" % ("CTL_SKY", len(sky_px)))

np.savez_compressed(OUT, void=void_px, ctl_paved=ctl_px, ctl_sky=sky_px,
                    res=np.array([W, H]), cam=C, lens=np.array([lens]),
                    frame=np.array([FRAME]))
print("STAGE wrote %s" % OUT)
print(">> STAGE RESULT: F1104_MASKS_OK")
