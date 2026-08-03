"""COUNT THE VOID. Full-width black rows in a rendered frame, with controls.

    python3 tools/black_row_count.py FRAME.png [FRAME.png ...] [--json OUT]

WHAT IT COUNTS AND WHY THAT DEFINITION
======================================
A **full-width black row** is an image row in which the maximum of R, G and B
over every pixel is below `THRESH` = 0.02. That is the definition the beat-6
finding was stated in, and it is deliberately harsh: one lit pixel anywhere in
the row disqualifies it. It cannot be satisfied by a dark subject, a shadow, or
a low exposure — only by a row in which nothing at all returned light.

It exists because `work/film6/evidence/sky_ab/r2b56_sky_002860.png` has 56 of
them, rows 220-275 of 720, 7.8 % of the closing frame, and the film's last
11 seconds hold on that shot.

THE COUNTER NEEDS ITS OWN CONTROLS, AND THIS IS WHY
----------------------------------------------------
Twenty-seven times on this project the instrument has been the broken thing
rather than the work. A row counter that returns 0 is indistinguishable from a
row counter that is pointed at the wrong file, reading the wrong channel, or
comparing against a threshold nothing can reach. So every run reports, from the
SAME image:

  * `rows_all_black`      the measurement
  * `rows_any_black`      rows with at least one black pixel: if this is 0 too,
                          the frame has no true black anywhere and a `0` in the
                          line above is uninformative rather than good news
  * `darkest_row`         the row index and value of the darkest row present,
                          so a near-miss at 0.021 cannot hide behind the
                          threshold
  * `p01 / mean / max`    the frame's own luminance spread, which is how a
                          black frame, a blown frame and a graded frame are told
                          apart without opening it

and the control (on by default; `--no-control` turns it off) synthesises
two images with known answers — a frame with a band
of exact zeros, and the same frame with that band at 0.03 — and requires the
counter to return the band height for the first and 0 for the second. A checker
that cannot fail is not a check.
"""

import argparse
import json
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(R2, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(R2, "tools"))
import gate_exit                                             # noqa: E402

THRESH = 0.02


def load(path):
    from PIL import Image
    im = Image.open(path)
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    if a.max() > 1.5:
        a /= 255.0
    return a


def measure(rgb):
    px = rgb.max(axis=2)
    row_max = px.max(axis=1)
    allb = np.where(row_max < THRESH)[0]
    anyb = np.where((px < THRESH).any(axis=1))[0]
    lum = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    d = int(np.argmin(row_max))
    return {
        "height": int(rgb.shape[0]), "width": int(rgb.shape[1]),
        "rows_all_black": int(len(allb)),
        "rows_all_black_pct": round(100.0 * len(allb) / rgb.shape[0], 3),
        "span": [int(allb[0]), int(allb[-1])] if len(allb) else None,
        "rows_any_black": int(len(anyb)),
        "any_span": [int(anyb[0]), int(anyb[-1])] if len(anyb) else None,
        "darkest_row": d, "darkest_row_max": round(float(row_max[d]), 5),
        "lum_p01": round(float(np.percentile(lum, 1)), 5),
        "lum_mean": round(float(lum.mean()), 5),
        "lum_max": round(float(lum.max()), 5),
        "threshold": THRESH,
    }


def control():
    """A positive and a negative the counter must get right."""
    h, w = 200, 320
    base = np.full((h, w, 3), 0.35, np.float32)
    pos = base.copy()
    pos[60:88, :, :] = 0.0                    # 28 rows of exact zero
    neg = base.copy()
    neg[60:88, :, :] = 0.03                   # the same band, just above THRESH
    p, n = measure(pos), measure(neg)
    ok = (p["rows_all_black"] == 28 and p["span"] == [60, 87]
          and n["rows_all_black"] == 0)
    print(">> CONTROL positive: a 28-row band of zeros -> %d rows %s"
          % (p["rows_all_black"], p["span"]))
    print(">> CONTROL negative: the same band at 0.030 -> %d rows (darkest row "
          "max %.4f, threshold %.3f)"
          % (n["rows_all_black"], n["darkest_row_max"], THRESH))
    return ok, {"positive": p, "negative": n}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="*")
    ap.add_argument("--json", default=None)
    ap.add_argument("--no-control", action="store_true")
    ap.add_argument("--max-allowed", type=int, default=0)
    a = ap.parse_args()

    rep = {"threshold": THRESH, "images": {}}
    if not a.no_control:
        ok, rep["control"] = control()
        if not ok:
            return gate_exit.verdict(
                "BLACK_ROW_COUNTER_BROKEN_FAIL",
                " the counter failed its own synthetic positive/negative")
        print()

    missing = [p for p in a.images if not os.path.exists(p)]
    if missing:
        return gate_exit.verdict("BLACK_ROW_NO_IMAGE_REFUSED",
                                 " %s" % missing)
    if not a.images:
        return gate_exit.verdict("BLACK_ROW_NOTHING_TESTED",
                                 " no images given")

    worst = 0
    for p in a.images:
        m = measure(load(p))
        rep["images"][p] = m
        worst = max(worst, m["rows_all_black"])
        print("%-58s %4d x %4d  ALL-BLACK ROWS %4d (%5.2f %%) span %-12s  "
              "any-black rows %4d  darkest row %4d at %.4f  lum p01 %.4f "
              "mean %.4f max %.4f"
              % (os.path.basename(p), m["width"], m["height"],
                 m["rows_all_black"], m["rows_all_black_pct"], str(m["span"]),
                 m["rows_any_black"], m["darkest_row"], m["darkest_row_max"],
                 m["lum_p01"], m["lum_mean"], m["lum_max"]))

    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)) or ".",
                    exist_ok=True)
        json.dump(rep, open(a.json, "w"), indent=1)
        print(">> report -> %s" % a.json)

    if worst > a.max_allowed:
        return gate_exit.verdict(
            "BLACK_ROWS_PRESENT_FAIL",
            " worst frame carries %d full-width black rows (allowed %d)"
            % (worst, a.max_allowed))
    return gate_exit.verdict("BLACK_ROWS_CLEAN",
                             " %d image(s), worst %d rows" % (len(a.images), worst))


if __name__ == "__main__":
    gate_exit.guard(main, tool="black_row_count")
