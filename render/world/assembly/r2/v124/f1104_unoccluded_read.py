"""Read the f1104 A/B over the pixel sets `f1104_unoccluded_ab.py` resolved.

    .venv/bin/python render/world/assembly/r2/v124/f1104_unoccluded_read.py

The other half of R2-150's occlusion resolve; see that file's header for why
this is two processes.  The claim is the UNOCCLUDED row.  The two rows under it
are its controls, and they are the strong ones:

  * the SAME void region where the pit building hides it must NOT move -- same
    geometry, same fix, no line of sight, so any change there would be light
    leaking in from somewhere and would put the top row in doubt;
  * the repeat render of film13 against itself is the floor everything is read
    against.
"""
import sys

import numpy as np
from PIL import Image

R2 = "/home/zany/f1-round2"
NPZ = R2 + "/work/r2148/f1104_unocc.npz"
BEFORE = R2 + "/work/r2148/f1104_film13.png"
REPEAT = R2 + "/work/r2148/f1104_film13_REPEAT.png"
AFTER = R2 + "/work/r2148/f1104_film14.png"


def img(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.int32).reshape(-1, 3)


M = np.load(NPZ)
W, H = int(M["res"][0]), int(M["res"][1])
a, b, r = img(BEFORE), img(AFTER), img(REPEAT)
if a.shape[0] != W * H:
    print("REFUSE: masks are for %dx%d, the PNGs are not" % (W, H))
    print(">> STAGE RESULT: F1104_UNOCC_REFUSED_RES")
    sys.exit(3)
sig = np.abs(a - b).max(axis=1)
flo = np.abs(a - r).max(axis=1)

print("unoccluded %.2f m2 of %.2f m2 in frustum" % (M["m2"][0], M["m2"][1]))
print("%-40s %8s %10s %10s %11s %s"
      % ("region", "px", "sig>8/255", "flo>8/255", "sig mean|d|",
         "mean RGB before -> after"))
res = {}
for tag, key in (("VOID, UNOCCLUDED  (the claim)", "void_unoccluded"),
                 ("VOID, occluded in BOTH builds", "void_occluded"),
                 ("VOID, all in-frustum (lower bound)", "void_all")):
    idx = M[key]
    if not len(idx):
        print("%-40s (empty)" % tag)
        continue
    res[tag] = (100 * (sig[idx] > 8).mean(), 100 * (flo[idx] > 8).mean(),
                sig[idx].mean())
    print("%-40s %8d %9.2f%% %9.2f%% %11.3f   %s -> %s"
          % ((tag, len(idx)) + res[tag]
             + (np.round(a[idx].mean(axis=0), 1), np.round(b[idx].mean(axis=0), 1))))

v = res.get("VOID, UNOCCLUDED  (the claim)", (0,))[0]
o = res.get("VOID, occluded in BOTH builds", (0, 0, 0))[0]
print("\nunoccluded void %.2f %% over 8/255;  the SAME void behind the pit "
      "building %.2f %%;  repeat-render floor %.2f %%"
      % (v, o, res.get("VOID, UNOCCLUDED  (the claim)", (0, 0))[1]))
print(">> STAGE RESULT: %s" % ("F1104_UNOCCLUDED_VOID_CHANGED" if v > 25.0
                               else "F1104_UNOCCLUDED_VOID_UNCHANGED"))
