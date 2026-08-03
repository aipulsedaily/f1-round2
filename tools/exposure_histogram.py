"""PER-BEAT HISTOGRAM — is any beat of the film clipping?

    python3 tools/exposure_histogram.py <png> [<png> ...] [--label f400=1_assembly]

THE QUESTION, ASKED TWICE BY THE USER
--------------------------------------
"confirm the final video will NOT be over-exposed". Earlier vast output frames
looked blown out. Looking is not enough and has been wrong here before, so this
measures the numbers that decide it:

  clipped_hi_pct   percentage of pixels at or above CLIP_HI in the DISPLAY
                   image. AgX's shoulder means a legitimately bright frame
                   rolls off rather than flattening, so a real specular
                   highlight contributes a handful of pixels and a blown frame
                   contributes a region.
  flat_hi_pct      percentage of pixels that are clipped AND whose 3x3
                   neighbourhood is also clipped. THIS is the one that matters:
                   an isolated clipped pixel is a highlight, a clipped
                   NEIGHBOURHOOD is lost detail. The distinction exists because
                   the naive count alone calls a sun glint a defect.
  mean / p50 / p99 luminance, and the crushed-shadow percentage, because a
                   grade can be wrong in the other direction too and only
                   reporting the top would hide it.

CONTROLS
--------
`--selftest` runs the measurement against four synthetic images whose answers
are known before it runs: pure white (must be 100 % clipped and flat), an 18 %
mid grey (must be 0 %), a grey with ONE clipped pixel (must count as clipped and
NOT as flat), and a grey with a clipped 40x40 block (must count as both). A
check that has never failed has not been shown to work.
"""

import argparse
import json
import os
import sys

import numpy as np

# A 16-bit PNG through AgX reaches 1.0 only where the transform has run out.
# 0.996 is chosen so an 8-bit render (255/255 = 1.0, 254/255 = 0.996) and a
# 16-bit one give the same verdict rather than different ones.
CLIP_HI = 0.996
CRUSH_LO = 0.004

# The bar. Stated so it can be argued with rather than implied.
#   a frame with more than this much FLAT clipped area is over-exposed
FLAT_HI_LIMIT_PCT = 0.20
#   ... and this much crushed shadow is under
CRUSH_LIMIT_PCT = 1.00


def load(path):
    from PIL import Image
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float64)
    return a / (65535.0 if a.max() > 255.0 else 255.0)


def measure_array(rgb):
    # Rec.709 luminance: the eye's answer, not the arithmetic mean's.
    lum = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    clipped = (rgb >= CLIP_HI).all(-1)
    # "flat" = clipped and every 4-neighbour clipped too
    c = clipped
    flat = np.zeros_like(c)
    flat[1:-1, 1:-1] = (c[1:-1, 1:-1] & c[:-2, 1:-1] & c[2:, 1:-1]
                        & c[1:-1, :-2] & c[1:-1, 2:])
    crushed = (rgb <= CRUSH_LO).all(-1)
    n = lum.size
    return {"pixels": int(n),
            "mean_luma": round(float(lum.mean()), 5),
            "p50_luma": round(float(np.percentile(lum, 50)), 5),
            "p99_luma": round(float(np.percentile(lum, 99)), 5),
            "max_luma": round(float(lum.max()), 5),
            "clipped_hi_pct": round(100.0 * clipped.sum() / n, 5),
            "flat_hi_pct": round(100.0 * flat.sum() / n, 5),
            "crushed_lo_pct": round(100.0 * crushed.sum() / n, 5)}


def verdict(m):
    bad = []
    if m["flat_hi_pct"] > FLAT_HI_LIMIT_PCT:
        bad.append("OVER-EXPOSED: %.4f %% of the frame is a flat clipped "
                   "region (limit %.2f %%)" % (m["flat_hi_pct"], FLAT_HI_LIMIT_PCT))
    if m["crushed_lo_pct"] > CRUSH_LIMIT_PCT:
        bad.append("UNDER-EXPOSED: %.4f %% of the frame is crushed to black "
                   "(limit %.2f %%)" % (m["crushed_lo_pct"], CRUSH_LIMIT_PCT))
    return bad


HDR = ("%-26s %9s %9s %9s %9s %11s %10s %11s" %
       ("frame", "mean", "p50", "p99", "max", "clipped %", "flat %", "crushed %"))


def line(name, m):
    return ("%-26s %9.5f %9.5f %9.5f %9.5f %11.5f %10.5f %11.5f" %
            (name[:26], m["mean_luma"], m["p50_luma"], m["p99_luma"],
             m["max_luma"], m["clipped_hi_pct"], m["flat_hi_pct"],
             m["crushed_lo_pct"]))


def selftest():
    print("CONTROLS — every answer is known before the measurement runs")
    print(HDR)
    ok = True
    g = np.full((400, 400, 3), 0.18)
    cases = []
    cases.append(("POSITIVE pure white", np.ones((400, 400, 3)), True, True))
    cases.append(("NEGATIVE flat 18% grey", g.copy(), False, False))
    one = g.copy(); one[200, 200] = 1.0
    cases.append(("POSITIVE one clipped px", one, True, False))
    blk = g.copy(); blk[100:140, 100:140] = 1.0
    cases.append(("POSITIVE 40x40 clipped", blk, True, True))
    for name, arr, want_clip, want_flat in cases:
        m = measure_array(arr)
        print(line(name, m))
        got_clip = m["clipped_hi_pct"] > 0.0
        got_flat = m["flat_hi_pct"] > 0.0
        good = (got_clip == want_clip) and (got_flat == want_flat)
        ok &= good
        print("      expect clipped=%s flat=%s   got clipped=%s flat=%s   %s"
              % (want_clip, want_flat, got_clip, got_flat,
                 "ok" if good else "BROKEN -- the measurement does not do what "
                                   "it claims"))
    print(">> STAGE RESULT: " + ("HISTOGRAM_SELFTEST_OK" if ok
                                 else "HISTOGRAM_SELFTEST_BROKEN"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pngs", nargs="*")
    ap.add_argument("--label", action="append", default=[],
                    help="basename=beat name, repeatable")
    ap.add_argument("--out", default="")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    labels = dict(x.split("=", 1) for x in a.label)
    print(HDR)
    rows, fails = {}, []
    for p in a.pngs:
        base = os.path.splitext(os.path.basename(p))[0]
        name = labels.get(base, base)
        m = measure_array(load(p))
        m["path"] = os.path.abspath(p)
        rows[name] = m
        print(line(name, m))
        for b in verdict(m):
            fails.append("%s: %s" % (name, b))
    if a.out:
        json.dump(rows, open(a.out, "w"), indent=1)
    print()
    for f in fails:
        print("   FAIL " + f)
    print(">> STAGE RESULT: " + ("NO_BEAT_CLIPS" if not fails
                                 else "EXPOSURE_OUT_OF_RANGE"))
    return 0 if not fails else 1



# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised: `blender -b -P x.py`
    # prints the traceback and exits 0, MEASURED on this box. A gate that
    # crashed was indistinguishable from one that passed. guard() makes an
    # uncaught exception a status 2 and passes any real verdict through
    # unchanged. One shared helper, not N copies -- see tools/gate_exit.py.
    gate_exit.guard(main, tool="exposure_histogram")
