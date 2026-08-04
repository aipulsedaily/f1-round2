"""ITEM A/B — did placing the item change the picture, and does its OCCLUDED
half stay still?

    python3 tools/item_ab_measure.py --before B.png --after A.png --null N.png \
        --occlusion work/r2226/after_verify.json --frame 654 --item crew_figure \
        --out work/r2226/ab_654.json

THE UNIT IS THE REPEAT RENDER, NOT ZERO
=======================================
`NULL.png` is the BEFORE scene rendered a second time, same farm, same seed,
same settings.  Cycles is not bit-identical across two GPU runs, so "some
pixels moved" is not evidence; every figure below only means something as a
multiple of that floor.  `tools/r2179_ab_measure.py` and
`tools/glass_winding_ab_measure.py` established this shape on this project.

AND THE STRONGEST CONTROL IS INTERNAL — R2-150
==============================================
    "Row 2 is the strongest control in this entire log, and it costs nothing to
     obtain.  It is the same void region, in the same two builds, under the
     same fix, differing only in that a wall stands between it and the lens.
     It must not move.  At 1.47 % against 74.40 % it does not."

An item placed into a world has exactly that structure for free: some of its
units are in frustum and lit, and some are in frustum and **behind a
building**.  The second set is a negative control that no external reference
can match, because it is the same geometry, the same build, the same render.

  * If the occluded region moves as much as the visible one, the change is not
    the item -- it is light leaking, an exposure shift, or the two renders not
    being the same scene.
  * The occlusion split is computed by RAYCAST in `work/r2226/verify_after.py`,
    against the named occluders' own BVHs, **before** any image is compared.
    Deriving it from the diff would be circular.

AND FIRST, THE TRAP THIS WHOLE FAMILY OF MEASUREMENT FELL INTO — R2-182
=======================================================================
    "an item absent from the world produces two identical images before and
     after a fix, which reads as 'the change is invisible, close it'."

So this refuses to report unless it is handed the placement gate's verdict for
the blend the AFTER frame came from.  A null is only a null once the thing you
were looking for was in the file.
"""

import argparse
import json
import os

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def load(p):
    return np.asarray(Image.open(p).convert("RGB"), dtype=np.int16)


def mask_from_boxes(shape, boxes, pad=6):
    """Union of screen boxes, in image coordinates.

    The camera model puts v = 0 at the TOP of the frame here because the
    projection in `verify_after.py` adds RES_Y/2 to a +Y-up camera coordinate;
    numpy rows also run top-down, so `y` maps straight to the row index. The
    `--flip-v` switch exists because getting that backwards silently measures
    the mirror image of the region, which looks like a beautifully clean
    negative control.
    """
    h, w = shape[:2]
    m = np.zeros((h, w), bool)
    for (x0, y0, x1, y1) in boxes:
        a = max(0, int(np.floor(x0)) - pad); b = min(w, int(np.ceil(x1)) + pad)
        c = max(0, int(np.floor(y0)) - pad); d = min(h, int(np.ceil(y1)) + pad)
        if b > a and d > c:
            m[c:d, a:b] = True
    return m


def region_stats(A, B, m):
    if not m.any():
        return {"px": 0, "note": "empty region"}
    d = np.abs(A - B).max(axis=2)[m]
    return {"px": int(m.sum()),
            "frac_changed_gt0": round(float((d > 0).mean()), 6),
            "frac_changed_gt2": round(float((d > 2).mean()), 6),
            "frac_changed_gt8": round(float((d > 8).mean()), 6),
            "mean_abs_levels": round(float(d.mean()), 4),
            "max_levels": int(d.max())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--null", required=True,
                    help="the BEFORE scene rendered a SECOND time")
    ap.add_argument("--occlusion", required=True,
                    help="work/.../after_verify.json -- the raycast split, "
                         "computed before any image was compared")
    ap.add_argument("--frame", required=True)
    ap.add_argument("--item", required=True)
    ap.add_argument("--gate", default=None,
                    help="the placement gate report for the AFTER blend. "
                         "Without it this refuses: R2-182.")
    ap.add_argument("--flip-v", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    # --- R2-182: was the item in the file at all? -------------------------- #
    gate_ok, gate_note = None, "no --gate given"
    if a.gate and os.path.exists(a.gate):
        g = json.load(open(a.gate))
        row = next((r for r in g.get("items", []) if r["key"] == a.item), None)
        gate_ok = bool(row and row.get("verdict") == "PLACED")
        gate_note = ("%s: %s, %s objects" % (a.gate, row and row.get("verdict"),
                                             row and row.get("objects")))
    if not gate_ok:
        print("REFUSING to interpret an A/B: the placement gate has not "
              "confirmed %r is in the AFTER blend (%s).\n"
              "R2-182: an item absent from the world produces two identical "
              "images and the null reads as 'the change is invisible'."
              % (a.item, gate_note))
        print(">> STAGE RESULT: ITEM_AB_REFUSED_UNVERIFIED_PLACEMENT")
        return 3

    A, B, N = load(a.before), load(a.after), load(a.null)
    if not (A.shape == B.shape == N.shape):
        raise SystemExit("shape mismatch: %s %s %s" % (A.shape, B.shape, N.shape))

    occ = json.load(open(a.occlusion))
    fr = occ["frames"][str(a.frame)]["items"][a.item]
    vis_boxes, occ_boxes = [], []
    for u in fr["units"]:
        if not u.get("in_frustum"):
            continue
        bx = u["box"]
        if a.flip_v:
            bx = [bx[0], A.shape[0] - bx[3], bx[2], A.shape[0] - bx[1]]
        (occ_boxes if u.get("occluded") else vis_boxes).append(bx)

    mvis = mask_from_boxes(A.shape, vis_boxes)
    mocc = mask_from_boxes(A.shape, occ_boxes)
    # A unit that is occluded but whose box overlaps a visible unit's box is
    # not a control -- the visible neighbour is inside it. Take the difference.
    mocc_pure = mocc & ~mvis
    mall = np.ones(A.shape[:2], bool)
    mrest = ~(mvis | mocc)

    rep = {"frame": int(a.frame), "item": a.item,
           "before": a.before, "after": a.after, "null": a.null,
           "gate": gate_note,
           "resolution": [int(A.shape[1]), int(A.shape[0])],
           "units": {"in_frustum": fr["n_in_frustum"],
                     "visible": fr["n_visible"], "occluded": fr["n_occluded"]},
           "regions": {}}

    for name, m in (("whole_frame", mall),
                    ("visible_units", mvis),
                    ("occluded_units_CONTROL", mocc_pure),
                    ("rest_of_frame_CONTROL", mrest)):
        rep["regions"][name] = {"ab": region_stats(A, B, m),
                                "null": region_stats(A, N, m)}

    print("frame %s   item %s   %d units in frustum: %d visible, %d occluded"
          % (a.frame, a.item, fr["n_in_frustum"], fr["n_visible"],
             fr["n_occluded"]))
    print("%-26s %10s %14s %12s | %14s %12s"
          % ("region", "px", "AB >8/255", "AB mean|d|", "NULL >8/255", "NULL mean|d|"))
    for name, r in rep["regions"].items():
        ab, nu = r["ab"], r["null"]
        if not ab.get("px"):
            print("%-26s %10d  (empty)" % (name, 0)); continue
        print("%-26s %10d %13.2f%% %12.2f | %13.2f%% %12.2f"
              % (name, ab["px"], 100 * ab["frac_changed_gt8"],
                 ab["mean_abs_levels"], 100 * nu["frac_changed_gt8"],
                 nu["mean_abs_levels"]))

    v = rep["regions"]["visible_units"]["ab"]
    o = rep["regions"]["occluded_units_CONTROL"]["ab"]
    ok = True
    notes = []
    if v.get("px") and v["frac_changed_gt8"] < 0.02:
        ok = False
        notes.append("the VISIBLE units barely moved (%.2f %%): either the item "
                     "is not where the projection says, or the frame does not "
                     "see it" % (100 * v["frac_changed_gt8"]))
    if o.get("px") and v.get("px"):
        ratio = v["frac_changed_gt8"] / max(o["frac_changed_gt8"], 1e-9)
        rep["visible_over_occluded"] = round(ratio, 1)
        print("\nR2-150 CONTROL: visible %.2f %% vs occluded %.2f %%  ->  %.1fx"
              % (100 * v["frac_changed_gt8"], 100 * o["frac_changed_gt8"], ratio))
        if ratio < 5.0:
            ok = False
            notes.append("the OCCLUDED half moved almost as much as the visible "
                         "half (%.1fx). That is not the item arriving; that is "
                         "the two renders not being the same scene." % ratio)
    elif not o.get("px"):
        notes.append("no occluded unit at this frame, so the internal control "
                     "is unavailable here and only the repeat-render null "
                     "applies")
    for n in notes:
        print("  NOTE %s" % n)
    rep["ok"] = ok
    rep["notes"] = notes
    if a.out:
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        json.dump(rep, open(a.out, "w"), indent=1)
        print("wrote %s" % a.out)
    print(">> STAGE RESULT: %s" % ("ITEM_AB_OK" if ok else "ITEM_AB_FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
