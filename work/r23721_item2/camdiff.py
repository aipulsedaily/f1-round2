"""R2-3721 item 2: reproduce the R2-3243 C4 camera diff, then correct it for film24.

Reproduces the exact C4 metric from tools/r2_3241_exposure.py:563-580 --
  position : ||p_a - p_b|| > 1e-6 m
  lens     : |lens_a - lens_b| > 1e-6 mm
  orient   : max |q_a[i] - q_b[i]| > 1e-6   (RAW stored components, no
             re-normalisation and NO SIGN FIX -- so a quaternion that is the
             negative of the other, i.e. the SAME rotation, counts as differing,
             and so does six-decimal rounding noise)
-- and alongside it the honest geodesic angle on re-normalised, sign-normalised
quaternions, which is what tools/campath_diff.py uses and what R2-103 says you
must use if you want the number to mean "the camera is pointed somewhere else".
"""
import json
import math
import os
import sys

import numpy as np

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "tools"))
import live_campath as L  # noqa: E402

WHY = ("R2-3721 item 2 (defect #159): reproducing the R2-3243 C4 diff so the "
       "two cameras being compared are known to be the ones named, before any "
       "re-sweep is trusted.")


def track(rel):
    d = L.load_explicit(rel, why=WHY)
    p = d["path"]
    return (np.array([e["p"] for e in p], float),
            np.array([e["q"] for e in p], float),
            np.array([e["lens"] for e in p], float),
            np.array([e["f"] for e in p], int))


def geodesic_deg(qa, qb):
    na = qa / np.linalg.norm(qa, axis=1, keepdims=True)
    nb = qb / np.linalg.norm(qb, axis=1, keepdims=True)
    d = np.abs((na * nb).sum(axis=1)).clip(-1, 1)
    return np.degrees(2.0 * np.arccos(d))


def report(na, nb, beat1_last):
    Pa, Qa, La, Fa = track(na)
    Pb, Qb, Lb, Fb = track(nb)
    m = min(len(Pa), len(Pb))
    assert (Fa[:m] == Fb[:m]).all()
    dpos = np.linalg.norm(Pa[:m] - Pb[:m], axis=1)
    dlen = np.abs(La[:m] - Lb[:m])
    dq_raw = np.abs(Qa[:m] - Qb[:m]).max(axis=1)
    dq_geo = geodesic_deg(Qa[:m], Qb[:m])

    print("\n" + "=" * 78)
    print("%s  vs  %s      %d common frames" % (na, nb, m))
    print("  C4 METRIC, AS R2-3243 COMPUTED IT (raw components, tol 1e-6)")
    print("    position    %4d/%d frames differ   max %8.4f m  @f%d"
          % (int((dpos > 1e-6).sum()), m, dpos.max(), Fa[int(dpos.argmax())]))
    print("    lens        %4d/%d frames differ   max %8.4f mm @f%d"
          % (int((dlen > 1e-6).sum()), m, dlen.max(), Fa[int(dlen.argmax())]))
    print("    orientation %4d/%d frames differ   max component %.6f"
          % (int((dq_raw > 1e-6).sum()), m, dq_raw.max()))
    print("  GEODESIC ANGLE, re-normalised + sign-normalised (R2-103-safe)")
    print("    orientation %4d/%d frames > 0.2 deg  max %8.3f deg @f%d"
          % (int((dq_geo > 0.2).sum()), m, dq_geo.max(), Fa[int(dq_geo.argmax())]))
    print("    p50 over the >0.2 deg span   %.3f deg"
          % (np.median(dq_geo[dq_geo > 0.2]) if (dq_geo > 0.2).any() else 0.0))

    div = (dpos > 1e-3) | (dlen > 1e-3) | (dq_geo > 0.2)
    idx = np.nonzero(div)[0]
    print("  DIVERGENT (1 mm / 1 um / 0.2 deg): %d frames" % len(idx))
    if len(idx):
        print("    span f%d .. f%d" % (Fa[idx[0]], Fa[idx[-1]]))
        b1 = idx[Fa[idx] <= beat1_last]
        b2 = idx[Fa[idx] > beat1_last]
        for tag, g in (("inside beat 1 (f1-f%d)" % beat1_last, b1),
                       ("outside beat 1", b2)):
            if len(g):
                print("    %-24s %4d frames  worst dp %7.3f m @f%-5d  "
                      "dlens %6.2f mm @f%-5d  dq %7.3f deg @f%d"
                      % (tag, len(g), dpos[g].max(), Fa[g[dpos[g].argmax()]],
                         dlen[g].max(), Fa[g[dlen[g].argmax()]],
                         dq_geo[g].max(), Fa[g[dq_geo[g].argmax()]]))
            else:
                print("    %-24s    0 frames" % tag)
        # p50 over the divergent span, the way LIVE-CAMERA.md quotes it
        print("    p50 over divergent span   dp %.3f m   dlens %.3f mm   dq %.3f deg"
              % (np.median(dpos[idx]), np.median(dlen[idx]), np.median(dq_geo[idx])))
    return {"frames": int(m),
            "n_pos_1e6": int((dpos > 1e-6).sum()),
            "n_lens_1e6": int((dlen > 1e-6).sum()),
            "n_quat_raw_1e6": int((dq_raw > 1e-6).sum()),
            "n_quat_geo_0p2deg": int((dq_geo > 0.2).sum()),
            "max_pos_m": float(dpos.max()), "max_pos_frame": int(Fa[int(dpos.argmax())]),
            "max_lens_mm": float(dlen.max()), "max_lens_frame": int(Fa[int(dlen.argmax())]),
            "max_quat_deg": float(dq_geo.max()), "max_quat_frame": int(Fa[int(dq_geo.argmax())]),
            "n_divergent": int(len(idx)),
            "divergent_span": [int(Fa[idx[0]]), int(Fa[idx[-1]])] if len(idx) else None}


def main():
    sheet = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))
    b = sheet["beats"][0]
    b1 = int(round((b["start_s"] + b["duration_s"]) * 24))
    print("beat 1 = %s, f1..f%d (from docs/beat_sheet.json, not a literal)"
          % (b["name"], b1))

    out = {}
    # 1. the claim as R2-3243 made it: orphan vs film22 (the then-delivered)
    out["orphan_vs_film22"] = report("world/camera_rig_path.json",
                                     "render/film22_path.json", b1)
    # 2. the claim as it stands TODAY: orphan vs film24 (the delivered camera)
    out["orphan_vs_film24"] = report("world/camera_rig_path.json",
                                     "render/film24_path.json", b1)
    # 3. what film22 -> film24 alone did, so the two legs are separable
    out["film22_vs_film24"] = report("render/film22_path.json",
                                     "render/film24_path.json", b1)
    # 4. THE CORRECTION. `docs/screen_presence*.json` was NOT swept against the
    #    bytes that are in world/camera_rig_path.json today. The npz's own
    #    `campos` array reproduces render/film14_path.json to 5 micrometres and
    #    today's world/camera_rig_path.json only to 8.86 m; retier_a9/inputs.json
    #    stamps sha f1c65c46 (= film13 = film14 = git HEAD's copy of
    #    world/camera_rig_path.json), and the working-tree copy acquired film16's
    #    bytes at 2026-08-04 15:49, FOURTEEN HOURS AFTER the sweep.  So the
    #    orphan that actually produced the delivered tiering is film14's bytes.
    out["orphan14_vs_film24"] = report("render/film14_path.json",
                                       "render/film24_path.json", b1)
    # 5. and the two generations of the orphan against each other
    out["orphan14_vs_orphan16"] = report("render/film14_path.json",
                                         "world/camera_rig_path.json", b1)

    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "camdiff.json")
    json.dump(out, open(dst, "w"), indent=1)
    print("\nwrote %s" % dst)
    print("\n>> STAGE RESULT: CAMDIFF_REPRODUCED "
          "orphan_vs_film22=%d/%d/%d  orphan_vs_film24=%d/%d/%d"
          % (out["orphan_vs_film22"]["n_pos_1e6"],
             out["orphan_vs_film22"]["n_lens_1e6"],
             out["orphan_vs_film22"]["n_quat_raw_1e6"],
             out["orphan_vs_film24"]["n_pos_1e6"],
             out["orphan_vs_film24"]["n_lens_1e6"],
             out["orphan_vs_film24"]["n_quat_raw_1e6"]))


main()
