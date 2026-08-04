"""THE UN-BEND, IN PIXELS.  Differences the two halves of the one-variable A/B.

    .venv/bin/python sim/unbend_diff.py \
        --a render/breach/r2607_A_repaired_f870.png \
        --b render/breach/r2607_B_bent_f870.png \
        --out sim/out/unbend_diff.json

A is `film14_breach_r6.blend` at f870 -- the ship candidate, in which the wall
has already repaired itself.  B is the same frame from
`r2607_unbend_BENT_DO_NOT_SHIP.blend`, identical in every respect except that
the 30 pieces which spring back are held at their f861 pose.  The difference
between the two images is the defect and nothing else.

WHY NOT A TEMPORAL DIFF.  Projected through the camera track's own pose and
lens, the camera moves a STATIC point 1,478.9 px between f861 and f870 while
the member itself moves 41.1 px.  An f861/f870 diff would be 97 % camera.

THE WINDOWS, and the free negative control
==========================================
  WOUND    the projected extent of the pinned pieces that are actually in
           frame at f870 -- `MUL05_S02` (71.5 px of shift), `TRN_z0_b04`
           (38.8 px) and `TRN_z0_b05` (46.8 px).  Computed from the camera
           track, not eyeballed.
  CONTROL  the same window mirrored to the far side of the frame.  Same two
           builds, same frame, same camera, same lighting, no line of sight to
           any pinned piece.  It should read ~0.
           If it does NOT read ~0 that is a RESULT, not contamination: the only
           way the change reaches it is through a reflection or a bounce, and
           that would mean the un-bend is visible somewhere it does not stand.
           Reported either way, never subtracted.
  WHOLE    the full frame, for scale.

The threshold is 8/255 per channel, the same one `WOUND_bridged` was measured
with (R2-281), so this number is comparable with the 11.33 % already in the log.
"""
import argparse
import json
import os
import sys

import numpy as np

THRESH = 8


def load(p):
    try:
        from PIL import Image
    except ImportError:
        print("PIL not available", file=sys.stderr)
        raise
    im = Image.open(p).convert("RGB")
    return np.asarray(im, np.int16)


def stats(A, B, box=None, name=""):
    if box is not None:
        x0, x1, y0, y1 = box
        A = A[y0:y1, x0:x1]
        B = B[y0:y1, x0:x1]
    d = np.abs(A - B).max(axis=2)
    n = d.size
    return dict(window=name, px=int(n),
                changed_gt_8_pct=round(100.0 * float((d > THRESH).sum()) / n, 4),
                changed_gt_2_pct=round(100.0 * float((d > 2).sum()) / n, 4),
                max_delta=int(d.max()), mean_delta=round(float(d.mean()), 4),
                box=None if box is None else [int(v) for v in box])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--out", default="sim/out/unbend_diff.json")
    ap.add_argument("--wound", nargs=4, type=int,
                    default=[336, 1603, 351, 866],
                    help="x0 x1 y0 y1 in pixels, origin top-left")
    a = ap.parse_args()

    A, B = load(a.a), load(a.b)
    if A.shape != B.shape:
        print(">> STAGE RESULT: UNBEND_DIFF_SHAPE_MISMATCH %s vs %s"
              % (A.shape, B.shape))
        return 1
    H, W = A.shape[:2]
    x0, x1, y0, y1 = a.wound
    ctrl = [W - x1, W - x0, y0, y1]

    rows = [stats(A, B, (x0, x1, y0, y1), "WOUND"),
            stats(A, B, tuple(ctrl), "CONTROL_mirrored"),
            stats(A, B, None, "WHOLE_FRAME")]
    rep = dict(a=a.a, b=a.b, res=[W, H], threshold=THRESH, rows=rows)

    w = rows[0]["changed_gt_8_pct"]
    c = rows[1]["changed_gt_8_pct"]
    rep["wound_over_control"] = (round(w / c, 1) if c > 1e-9 else None)
    # The claim is "the un-bend is visible".  It is carried by the WOUND window
    # reading substantially above a control that has no sight of the change.
    rep["VISIBLE"] = bool(w > 1.0 and (c < 1e-9 or w > 10.0 * c))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(rep, open(a.out, "w"), indent=1)

    print("  %-18s %10s %14s %12s %10s" %
          ("window", "px", "changed>8/255", "max delta", "mean"))
    for r in rows:
        print("  %-18s %10d %13.4f %% %12d %10.4f"
              % (r["window"], r["px"], r["changed_gt_8_pct"],
                 r["max_delta"], r["mean_delta"]))
    print("")
    print("  wound / control ratio: %s" % rep["wound_over_control"])
    print(">> STAGE RESULT: %s"
          % ("UNBEND_VISIBLE" if rep["VISIBLE"] else "UNBEND_NOT_VISIBLE"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
