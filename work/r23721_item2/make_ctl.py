"""R2-3721 item 2: the CALIBRATED control cameras.

A comparison that cannot report a difference is not evidence of no difference.
So before "the tiering does not move" may be said about the orphan -> film24
swap, the same chain -- same points, same screen_presence.py, same
item_presence.py, same tier rule -- must be shown to REPORT a move when one is
really there, at a scale NO LARGER than the real camera change.

So the control is not a synthetic wobble of invented size. It is a FRACTION OF
THE REAL CHANGE: for each beat-1 frame, the camera is placed a fraction k of the
way from the delivered film24 pose back towards the orphan (film14) pose --
position lerped, lens lerped, orientation SLERPed on sign-normalised
quaternions. k = 1 reproduces the orphan exactly over beat 1; k = 0.25 is
literally "a quarter of the defect". Beats 2-6 are left byte-identical to
film24 in every arm, so anything the comparison reports is beat 1's.

If a quarter of the defect moves tiers and the whole defect does not, the null
is a measurement. If nothing moves at any k, the instrument is blind and the
null is worthless.
"""
import json
import math
import os
import sys

import numpy as np

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "tools"))
import live_campath as L  # noqa: E402

WHY = ("R2-3721 item 2: building a control camera that is a measured fraction "
       "of the real orphan-vs-film24 beat-1 change.")
OUT = os.environ.get("R23721_OUT") or os.path.dirname(os.path.abspath(__file__))
# THE ORPHAN THAT ACTUALLY PRODUCED THE DELIVERED TIERING is film14's bytes
# (sha f1c65c46), not the bytes in world/camera_rig_path.json today. See
# camdiff.py's note 4 and work/w2_0/retier_a9/inputs.json.
ORPHAN = "render/film14_path.json"


def slerp(qa, qb, t):
    qa = qa / np.linalg.norm(qa, axis=1, keepdims=True)
    qb = qb / np.linalg.norm(qb, axis=1, keepdims=True)
    d = (qa * qb).sum(axis=1)
    qb = np.where((d < 0)[:, None], -qb, qb)     # shortest arc
    d = np.abs(d).clip(-1, 1)
    th = np.arccos(d)
    s = np.sin(th)
    small = s < 1e-8
    a = np.where(small, 1.0 - t, np.sin((1 - t) * th) / np.where(small, 1, s))
    b = np.where(small, t, np.sin(t * th) / np.where(small, 1, s))
    q = a[:, None] * qa + b[:, None] * qb
    return q / np.linalg.norm(q, axis=1, keepdims=True)


def main():
    ks = [float(x) for x in (sys.argv[1:] or ["0.25"])]
    sheet = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))
    b = sheet["beats"][0]
    B1 = int(round((b["start_s"] + b["duration_s"]) * 24))

    orphan = L.load_explicit(ORPHAN, why=WHY)["path"]
    film24 = L.load_explicit("render/film24_path.json", why=WHY)["path"]
    Po = np.array([e["p"] for e in orphan], float)
    Pf = np.array([e["p"] for e in film24], float)
    Qo = np.array([e["q"] for e in orphan], float)
    Qf = np.array([e["q"] for e in film24], float)
    Lo = np.array([e["lens"] for e in orphan], float)
    Lf = np.array([e["lens"] for e in film24], float)
    F = np.array([e["f"] for e in film24], int)

    m1 = F <= B1
    dp = np.linalg.norm(Po - Pf, axis=1)
    nn = lambda q: q / np.linalg.norm(q, axis=1, keepdims=True)      # noqa: E731
    dq = np.degrees(2 * np.arccos(np.abs((nn(Qo) * nn(Qf)).sum(axis=1)).clip(-1, 1)))
    div1 = m1 & ((dp > 1e-3) | (dq > 0.2) | (np.abs(Lo - Lf) > 1e-3))
    print("REAL %s -> film24 divergence INSIDE beat 1 (f1..f%d):" % (ORPHAN, B1))
    print("  divergent frames %d of %d" % (int(div1.sum()), int(m1.sum())))
    print("  position    p50 %.3f m    p90 %.3f m    max %.3f m"
          % (np.median(dp[div1]), np.percentile(dp[div1], 90), dp[m1].max()))
    print("  orientation p50 %.3f deg  p90 %.3f deg  max %.3f deg"
          % (np.median(dq[div1]), np.percentile(dq[div1], 90), dq[m1].max()))
    print("  lens        p50 %.3f mm   max %.3f mm"
          % (np.median(np.abs(Lo - Lf)[div1]), np.abs(Lo - Lf)[m1].max()))

    for k in ks:
        Qk = slerp(Qf, Qo, k)
        path = []
        for i, e in enumerate(film24):
            f = e["f"]
            if f > B1:
                path.append({"f": f, "p": list(e["p"]), "q": list(e["q"]),
                             "lens": e["lens"]})
                continue
            path.append({"f": f,
                         "p": list(Pf[i] + k * (Po[i] - Pf[i])),
                         "q": [float(x) for x in Qk[i]],
                         "lens": float(Lf[i] + k * (Lo[i] - Lf[i]))})
        tag = ("k%03d" % round(k * 100))
        dst = os.path.join(OUT, "ctl_%s_path.json" % tag)
        # what this control ACTUALLY moved, measured on the file it wrote
        Pk = np.array([e["p"] for e in path], float)
        Qq = np.array([e["q"] for e in path], float)
        d1 = np.linalg.norm(Pk - Pf, axis=1)
        a1 = np.degrees(2 * np.arccos(
            np.abs((nn(Qq) * nn(Qf)).sum(axis=1)).clip(-1, 1)))
        json.dump({"frames": len(path), "path": path,
                   "CONTROL": ("R2-3721 item 2: film24 moved a fraction k=%g of "
                               "the way back to the ORPHAN (%s) over f1..f%d "
                               "only; position lerped, lens lerped, orientation "
                               "slerped. Beats 2-6 byte-identical to film24. "
                               "Realised beat-1 displacement: max %.3f m, "
                               "max %.3f deg." % (k, ORPHAN, B1,
                                                  d1[m1].max(), a1[m1].max()))},
                  open(dst, "w"))
        print("wrote %s   k=%g  beat-1 max %.3f m / %.3f deg   "
              "beats2-6 max %.6f m / %.6f deg"
              % (dst, k, d1[m1].max(), a1[m1].max(),
                 d1[~m1].max(), a1[~m1].max()))

    print(">> STAGE RESULT: CTL_PATHS_BUILT k=%s" % ks)


main()
