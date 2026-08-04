"""R2-179 A/B: what the cap-winding fix did to the picture, in pixels.

    python3 tools/r2179_ab_measure.py BEFORE.png AFTER.png NULL.png [--out J]

NULL.png is the AFTER scene rendered a second time. It is the unit: Cycles is
deterministic for identical geometry, so the null should be ~0, and any figure
from the A/B only means something as a multiple of it. `tools/glass_winding_ab
_measure.py` established this shape on this project and its own positive
control refuted a first attempt whose instrument floor sat above its signal.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def load(p):
    return np.asarray(Image.open(p).convert("RGB"), dtype=np.int16)


def stats(a, b):
    d = np.abs(a - b).max(axis=2)
    n = d.size
    return {"n_px": int(n),
            "px_changed": int((d > 0).sum()),
            "px_gt1": int((d > 1).sum()),
            "px_gt2": int((d > 2).sum()),
            "px_gt8": int((d > 8).sum()),
            "frac_changed": float((d > 0).mean()),
            "mean_levels": float(d.mean()),
            "max_levels": int(d.max())}, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("null")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    A, B, N = load(a.before), load(a.after), load(a.null)
    if not (A.shape == B.shape == N.shape):
        raise SystemExit("shape mismatch: %s %s %s"
                         % (A.shape, B.shape, N.shape))
    null, _ = stats(B, N)
    live, d = stats(A, B)

    ys, xs = np.nonzero(d > 2)
    bbox = ([int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
            if len(xs) else None)

    ratio = live["px_changed"] / max(null["px_changed"], 1)
    rep = {"before": a.before, "after": a.after, "null": a.null,
           "resolution": [int(A.shape[1]), int(A.shape[0])],
           "null_stats": null, "ab_stats": live,
           "changed_bbox_xyxy": bbox,
           "ratio_px_changed_over_null": round(ratio, 1)}
    print(json.dumps(rep, indent=1))

    # A DETECTION, NOT A DIFFERENCE. Two renders of the same scene are not
    # bit-identical on a GPU, so "some pixels moved" is not evidence; the
    # question is whether it moved far more than the floor.
    ok = live["px_changed"] > 10 * max(null["px_changed"], 1)
    print(">> null %d px changed (max %d levels); A/B %d px changed "
          "(%.2f %% of frame, max %d levels, mean %.4f)"
          % (null["px_changed"], null["max_levels"], live["px_changed"],
             100.0 * live["frac_changed"], live["max_levels"],
             live["mean_levels"]))
    if bbox:
        print(">> pixels differing by more than 2 levels span x %d..%d, "
              "y %d..%d" % (bbox[0], bbox[2], bbox[1], bbox[3]))
    print(">> STAGE RESULT: %s (%.1fx the null)"
          % ("R2179_AB_VISIBLE" if ok else "R2179_AB_NOT_DISTINGUISHABLE",
             ratio))
    if a.out:
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(json.dumps(rep, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
