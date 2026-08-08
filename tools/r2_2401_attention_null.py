#!/usr/bin/env python3
"""R2-2401: IS A CROWD CAMERA A TEST OF ATTENTION, OR ONLY A PICTURE OF ONE?

`spectator_crowd.preflight` answers "can this camera RESOLVE its subject" -- 40
px of head, unoccluded, face toward the lens. That is a NECESSARY condition and
the whole 2026-08-03 camera repair was carried out against it. It is not a
SUFFICIENT one, and the missing half is what this tool measures.

    A camera that returns the same reading for a crowd rapt on the car and a
    crowd looking at nothing is not a test of attention, however sharp it is.

This repository's own rule for gates is: *test every new gate against an
artefact already known to be bad and confirm it fails -- this is the only
technique that has reliably worked.* `compose_stand(attention=0.0)` IS that
artefact for an attention camera, and until R2-2401 nobody had run one against
the other. Two cameras were deleted in 2026-08-03 for resolving 8 px of head;
this asks the question that survives fixing the pixels.

WHAT IT REPORTS, and why each column is there
---------------------------------------------
`delta`   n_faces_resolved(shipped) - n_faces_resolved(attention = 0).
`seed sd` the same statistic over `--seeds` independent draws of the SAME
          attention-on crowd. This is how far `delta` moves for reasons that
          have nothing to do with attention, and without it a delta is a number
          with nothing to be compared with (R2-018's whole lesson). FOUR SEEDS
          IS NOT ENOUGH: at n=4 CAM_ATTN_PROFILE scored z = 11.4 and at n=12 it
          scores 3.8, because a 3-dof variance estimate flattered it by 3x.
`z`       |delta| / seed sd.
`sign`    declared from geometry BEFORE the numbers are read, per camera. A lens
          near the car's bearing gains faces when the crowd watches (+1); a lens
          90 deg off the car LOSES them (-1), because heads turning toward the
          car turn away from it. The first version of this tool required faces
          to increase, which is a bar written before the quantity was understood
          -- CAM_ATTN_PROFILE failed it while behaving perfectly.
`bar`     the camera's OWN preflight bar, run against the null. This is the
          sharpest column: a camera whose bar returns PASS on a crowd that is
          not watching is not gating attention whatever it is named.

TWO CONTROLS THE COMPARISON NEEDS, and both are easy to get wrong
-----------------------------------------------------------------
* THE CAMERAS ARE PLANNED ONCE, ON THE SHIPPED CROWD, and both crowds are then
  projected through those same cameras. A control allowed to re-plan its own
  camera compares two instruments, not two crowds.
* `attention` INDEXES THE LIBRARY -- the gaze bin picks the source mesh -- so
  switching it off swaps meshes and could change what is VISIBLE rather than
  what is FACING. `--confound` reports in-frame / unoccluded / heads-resolved
  either side. Measured on TRIBUNE PRINCIPALE they match to within one figure
  in six hundred (613/612, 330/333, 593/593), so the delta is gaze and nothing
  else. Re-run it if the block or the LOD changes.

    python3 tools/r2_2401_attention_null.py --seeds 12
    python3 tools/r2_2401_attention_null.py --confound
"""

import argparse
import math
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "world"), os.path.join(_ROOT, "world", "items")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import spectator_crowd as SC                                    # noqa: E402

# Declared from geometry, before any number is read. See the docstring.
EXPECTED_SIGN = {
    "SPECX_CAM_CROWD_ALONG": +1,
    "SPECX_CAM_ATTN_ONAXIS": +1,
    "SPECX_CAM_ATTN_PROFILE": -1,
    "SPECX_CAM_ROW": +1,
    "SPECX_CAM_FEET": +1,
    "SPECX_CAM_HANDS": +1,
}
Z_BAR = 4.0                # |delta| must clear this many seed-null sd
MIN_HEADS = 120            # ... and the camera must resolve a crowd at all


def build(block, frame, seeds):
    seats, facings = SC.seat_array(tuple(block.split("+")))
    focus = SC.car_at(frame)
    on = SC.plan_block(SC.SEED, seats, facings, focus)
    off = SC.plan_block(SC.SEED, seats, facings, focus, attention=0.0)
    null = [SC.plan_block(SC.SEED + 1000 * k, seats, facings, focus)
            for k in range(1, seeds + 1)]
    return on, off, null, focus


def old_pair(on, focus):
    """The two cameras deleted on 2026-08-03, rebuilt by the arithmetic that
    produced them (span*1.15 / span*0.85, 50 mm, 9 and 11 deg of down-tilt), so
    this tool reports on the artefact it was written about rather than only on
    the survivors. A check that cannot speak about the known-bad case is worth
    little."""
    _, _, _, P = SC.block_axes(on)
    span = float(max(np.ptp(P[:, 0]), np.ptp(P[:, 1])))
    ctr = P.mean(axis=0)
    carb = math.degrees(math.atan2(focus[1] - ctr[1], focus[0] - ctr[0]))

    def at(dist, bearing, elev):
        a, e = math.radians(bearing), math.radians(elev)
        return ctr + dist * np.array([math.cos(e) * math.cos(a),
                                      math.cos(e) * math.sin(a), math.sin(e)])

    return [("ctl_BLOCK_ONAXIS", at(span * 1.15, carb, 9.0), ctr, 50.0, +1, None),
            ("ctl_BLOCK_CROSS", at(span * 0.85, carb + 78.0, 11.0), ctr, 50.0,
             -1, None)]


def main():
    p = argparse.ArgumentParser(prog="r2_2401_attention_null")
    p.add_argument("--block", default="TRIBUNE PRINCIPALE")
    p.add_argument("--frame", type=int, default=1009)
    p.add_argument("--seeds", type=int, default=12,
                   help="draws of the attention-on crowd for the seed null. "
                        "Below ~8 the sd is too noisy to fail a camera on.")
    p.add_argument("--confound", action="store_true",
                   help="report visibility either side instead of the verdict")
    a = p.parse_args()

    on, off, null, focus = build(a.block, a.frame, a.seeds)
    cams = old_pair(on, focus)
    for s in SC.camera_plan(on, focus):
        if s["bar"] is None:
            continue
        cams.append((s["name"], s["loc"], s["aim"], s["lens"],
                     EXPECTED_SIGN[s["name"]], s["bar"]))

    if a.confound:
        print("%-24s %13s %13s %13s %13s"
              % ("camera", "in frame", "unoccluded", "HEADS", "faces"))
        print("-" * 82)
        for nm, loc, aim, lens, _sgn, _bar in cams:
            x = SC.preflight(nm, loc, aim, lens, on)
            y = SC.preflight(nm, loc, aim, lens, off)
            print("%-24s %6d/%-6d %6d/%-6d %6d/%-6d %6d/%-6d"
                  % (nm.replace("SPECX_", ""),
                     x["n_in_frame"], y["n_in_frame"],
                     x["n_unoccluded"], y["n_unoccluded"],
                     x["n_heads_resolved"], y["n_heads_resolved"],
                     x["n_faces_resolved"], y["n_faces_resolved"]))
        print("\nHEADS must match either side. If it does not, `delta` in the "
              "main report is a visibility artefact and not a gaze signal.")
        return 0

    print("%-22s %7s %6s %6s %6s %7s %7s %6s %-13s %s"
          % ("camera", "head px", "heads", "on", "off", "delta", "seedsd",
             "z", "sign", "own bar vs null"))
    print("-" * 108)
    rows = []
    for nm, loc, aim, lens, sgn, bar in cams:
        x = SC.preflight(nm, loc, aim, lens, on)
        y = SC.preflight(nm, loc, aim, lens, off)
        ns = [SC.preflight(nm, loc, aim, lens, q)["n_faces_resolved"]
              for q in null]
        sd = float(np.std(ns, ddof=1)) if len(ns) > 1 else 0.0
        fa, fb = x["n_faces_resolved"], y["n_faces_resolved"]
        d = fa - fb
        z = (abs(d) / sd) if sd > 1e-9 else (float("inf") if d else 0.0)
        ok_sign = bool(d) and np.sign(d) == sgn
        if bar is None:
            barv = "n/a"
        else:
            barv = ("REJECTS null" if SC.preflight(
                nm, loc, aim, lens, off, what="", **bar)["verdict"]
                else "PASSES null")
        print("%-22s %7.1f %6d %6d %6d %+7d %7.1f %6s %-13s %s"
              % (nm.replace("SPECX_", ""), x["head_px_median"],
                 x["n_heads_resolved"], fa, fb, d, sd,
                 ("%.1f" % z) if np.isfinite(z) else "inf",
                 ("as predicted" if ok_sign else "WRONG SIGN") if d
                 else "no move", barv))
        rows.append((nm, x["n_heads_resolved"], d, z, ok_sign, barv))

    print()
    print("A CAMERA IS A TEST OF ATTENTION IF ALL THREE HOLD:")
    print("  resolves  >= %d unoccluded heads at >= 40 px" % MIN_HEADS)
    print("  responds  |delta| >= %.0f sd of the seed null" % Z_BAR)
    print("  sign      delta has the sign the geometry predicted")
    print()
    good = []
    for nm, heads, d, z, ok_sign, barv in rows:
        ok = heads >= MIN_HEADS and z >= Z_BAR and ok_sign
        if ok and not nm.startswith("ctl_"):
            good.append(nm)
        print("  %-22s %s" % (nm.replace("SPECX_", ""),
                              "A TEST OF ATTENTION" if ok else "NOT A TEST"))
    blind = [r for r in rows if r[0].startswith("ctl_")]
    print()
    print(">> STAGE RESULT: %s (%d camera(s): %s)"
          % ("ATTENTION_HAS_AN_INSTRUMENT" if good
             else "ATTENTION_HAS_NO_INSTRUMENT", len(good),
             ", ".join(n.replace("SPECX_", "") for n in good) or "none"))
    print(">> STAGE RESULT: %s"
          % ("REJECTED_PAIR_CONFIRMED_BLIND"
             if all(h == 0 and d == 0 for _n, h, d, _z, _s, _b in blind)
             else "REJECTED_PAIR_NOT_BLIND"))
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
