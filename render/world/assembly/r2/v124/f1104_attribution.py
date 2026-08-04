"""Does the repaired apron read as a fix in the film AS SHOT?  R2-150.

    .venv/bin/python render/world/assembly/r2/v124/f1104_attribution.py

This is R2-133's one open question.  f1104 is the ONER's BEST view of the
pit-exit void -- 71.50 m2 unoccluded of 427.60, at 17-34 deg line of sight --
so it is the most favourable frame the film has and not a cherry-picked nadir.

NO bpy.  `world_contract` may not import it (Rule 2), so the void set and the
camera both come out of files: the contract for the geometry, `film14_path.json`
for the camera.  Occlusion is NOT resolved here; the pit building shell hides
about half the in-frustum void in both builds and those pixels correctly do not
move, which is why the void figure below is a LOWER bound on the visible change.

THE CONTROL IS A REPEAT RENDER, and without it none of this means anything.
Two Cycles renders of the SAME scene at the same settings do not have to agree
bit-for-bit, so "5 % of the frame changed" is not a finding until you know what
0 % looks like on this farm.  film13 rendered twice is that number.
"""
import json
import math
import sys

import numpy as np
from PIL import Image

R2 = "/home/zany/f1-round2"
sys.path.insert(0, R2 + "/world")
import world_contract as WC                                       # noqa: E402

W, H, FRAME = 3840, 2160, 1104
BEFORE = R2 + "/work/r2148/f1104_film13.png"
REPEAT = R2 + "/work/r2148/f1104_film13_REPEAT.png"
AFTER = R2 + "/work/r2148/f1104_film14.png"
PATH = R2 + "/render/film14_path.json"

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
print("void: %d samples = %.2f m2" % (VOID.sum(), VOID.sum() * 0.25 * 0.05))

e = [p for p in json.load(open(PATH))["path"] if p["f"] == FRAME][0]
C = np.array(e["p"])
lens = e["lens"]
w, x, y, q3 = e["q"]
M = np.array([[1 - 2 * (y * y + q3 * q3), 2 * (x * y - q3 * w), 2 * (x * q3 + y * w)],
              [2 * (x * y + q3 * w), 1 - 2 * (x * x + q3 * q3), 2 * (y * q3 - x * w)],
              [2 * (x * q3 - y * w), 2 * (y * q3 + x * w), 1 - 2 * (x * x + y * y)]])
F, Rx, Uv = M @ [0, 0, -1.0], M @ [1.0, 0, 0], M @ [0, 1.0, 0]
thx = 18.0 / lens
thy = thx * H / W
print("cam f%d pitch %.2f deg lens %.2f mm" % (FRAME, -math.degrees(math.asin(F[2])), lens))


def pixels(p3):
    d = p3 - C
    zc = d @ F
    ok = zc > 1e-6
    tx = np.where(ok, (d @ Rx) / np.where(ok, zc, 1), 9)
    ty = np.where(ok, (d @ Uv) / np.where(ok, zc, 1), 9)
    v = ok & (np.abs(tx) <= thx) & (np.abs(ty) <= thy)
    px = np.clip(((tx[v] / thx * .5 + .5) * W).astype(int), 0, W - 1)
    py = np.clip(((.5 - ty[v] / thy * .5) * H).astype(int), 0, H - 1)
    return np.unique(py.astype(np.int64) * W + px), int(v.sum())


void_px, n_in = pixels(pts)
print("void in frustum: %d samples = %.2f m2 -> %d px"
      % (n_in, n_in * 0.25 * 0.05, len(void_px)))

CS, CU = np.arange(3380, 3480.01, 0.5), np.arange(0, 9.01, 0.25)
CA, CB = np.meshgrid(CS, CU, indexing="ij")
cp = WC.su_to_world(CA.ravel(), CB.ravel())
cz, _ = WC.world_ground_z(cp[:, 0], cp[:, 1])
cp[:, 2] = np.nan_to_num(cz)
ctl_px, _ = pixels(cp)
sky_px = np.arange(0, int(H * 0.08) * W)


def img(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.int32).reshape(-1, 3)


a, b, r = img(BEFORE), img(AFTER), img(REPEAT)
sig = np.abs(a - b).max(axis=1)
flo = np.abs(a - r).max(axis=1)

print("\n%-40s %8s %10s %10s %10s %10s"
      % ("region", "px", "sig>8/255", "flo>8/255", "sig mean|d|", "flo mean|d|"))
out = {}
for tag, idx in (("VOID  (declared, owned, never laid)", void_px),
                 ("CTL_PAVED  track asphalt, built in BOTH", ctl_px),
                 ("CTL_SKY  top 8 % of frame", sky_px),
                 ("WHOLE FRAME", np.arange(W * H))):
    out[tag] = (100 * (sig[idx] > 8).mean(), 100 * (flo[idx] > 8).mean(),
                sig[idx].mean(), flo[idx].mean())
    print("%-40s %8d %9.2f%% %9.2f%% %10.3f %10.3f" % ((tag, len(idx)) + out[tag]))

v = out["VOID  (declared, owned, never laid)"][0]
c = out["CTL_PAVED  track asphalt, built in BOTH"][0]
print("\nvoid %.2f %% vs paved control %.2f %% vs render-repeat floor %.2f %%"
      % (v, c, out["VOID  (declared, owned, never laid)"][1]))
print(">> STAGE RESULT: %s" % ("F1104_FIX_READS_ON_SCREEN" if v > max(3 * c, 1.0)
                               else "F1104_NO_CLEAR_DIFFERENCE"))
