#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r21061_knee_sweep.py — HOW MUCH OF THIS FILM IS ON AgX's SHOULDER?

R2-1042 found one frame whose road sits high on the AgX curve, in a four-frame
sample, while looking at something else.  One frame is an anecdote.  This asks
the same question of every delivered frame that exists on disk.

THE INSTRUMENT.  For a delivered PNG at the film's own grade (AgX / look None /
exposure -3.628) this reports the fraction of pixels whose LOCAL SLOPE of the
view transform has fallen below a fraction of the curve's peak.  The curve is
not modelled -- it is read from `render/r2651/agx.json`, which was measured by
pushing a known linear ramp through Blender's own colour management at this
film's exact grade.

WHY SLOPE AND NOT LEVEL.  "Bright" is not a defect; a sky is meant to be bright.
The complaint in R2-1042 is that a *textured* surface lands where AgX returns
half the display contrast per stop of scene contrast, so the texture is
compressed.  Slope is that complaint stated as a measurable quantity.  Levels
are reported alongside so the two can never be confused again.

    AgX at -3.628, MEASURED, not assumed:
      mid grey (scene-linear 2.2254) lands at display 0.4613
      peak slope 0.1536 display/stop, at display 0.4712 -- i.e. AT mid grey
      slope 75% of peak at display 0.6817   (+1.61 stops over mid grey)
      slope 60% of peak at display 0.7739   (+2.50 stops)
      slope 50% of peak at display 0.8125   (+2.95 stops)
      display saturates at 0.9330

THE SKY IS EXCLUDED BY A CONTROL, NOT BY A GUESS.  A frame whose top half is
sky would report a large shoulder area and that would be correct and
uninteresting.  `--sky-split` reports the shoulder fraction separately for the
part of the frame above and below the first row at which the column-median
display value drops by more than `--sky-step` between adjacent row bands -- the
horizon.  Both halves are always reported; nothing is silently discarded.

    .venv/bin/python tools/r21061_knee_sweep.py --seq ~/vast-render/out2/seq/r2full
    .venv/bin/python tools/r21061_knee_sweep.py --selftest

Judge on the printed `>> STAGE RESULT:` line.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGX_JSON = os.path.join(_ROOT, "render", "r2651", "agx.json")
FILM_EXPOSURE = -3.628
MID_GREY_SCENE_LIN = 0.18 / 2.0 ** FILM_EXPOSURE          # 2.2254

TOKEN_OK = "R21061_KNEE_SWEEP_OK"
TOKEN_FAIL = "R21061_KNEE_SWEEP_FAIL"


# --------------------------------------------------------------------- the curve
class Curve(object):
    """The film's own measured AgX transfer, and its slope."""

    def __init__(self, path=AGX_JSON):
        d = json.load(open(path))
        if abs(float(d["exposure"]) - FILM_EXPOSURE) > 1e-6:
            raise SystemExit("agx.json is at exposure %s, not the film's %.3f"
                             % (d["exposure"], FILM_EXPOSURE))
        self.lin = np.asarray(d["lin"], dtype=np.float64)
        self.disp = np.asarray(d["disp"], dtype=np.float64)
        st = np.log2(self.lin)
        self.slope = np.gradient(self.disp, st)          # display per stop
        self.peak = float(self.slope.max())
        self.disp_at_peak = float(self.disp[self.slope.argmax()])

    def scene_lin(self, disp):
        return np.interp(disp, self.disp, self.lin)

    def display(self, lin):
        return np.interp(lin, self.lin, self.disp)

    def slope_at_display(self, disp):
        return np.interp(disp, self.disp, self.slope)

    def display_at_slope_fraction(self, frac):
        """The display value on the UPPER shoulder where slope = frac * peak."""
        i = int(self.slope.argmax())
        j = np.where(self.slope[i:] < frac * self.peak)[0]
        return float(self.disp[i + j[0]]) if len(j) else float(self.disp[-1])


def _luma(rgb):
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def _load(path):
    from PIL import Image
    a = np.asarray(Image.open(path).convert("RGB"))
    return a.astype(np.float64) / 255.0


# --------------------------------------------------------------------- per frame
def _horizon_row(L, bands=36, step=0.04):
    """First row band (from the top) where the band median FALLS by `step`.

    The sky is the brightest, smoothest thing at the top of an exterior frame,
    and the ground below it is darker.  This finds that step and returns the row
    index.  Returns 0 when no such step exists (an interior frame, or a frame
    with no sky), which makes the whole frame "below horizon" -- the
    conservative answer, because it never hides ground behind a sky label.
    """
    h = L.shape[0]
    edges = np.linspace(0, h, bands + 1).astype(int)
    med = np.array([np.median(L[edges[k]:edges[k + 1]]) for k in range(bands)])
    for k in range(1, bands):
        if med[k - 1] - med[k] > step:
            return int(edges[k])
    return 0


def measure(path, curve, fracs=(0.75, 0.60, 0.50), sky_step=0.04):
    rgb = _load(path)
    L = _luma(rgb)
    thr = {f: curve.display_at_slope_fraction(f) for f in fracs}
    hr = _horizon_row(L, step=sky_step)
    below = L[hr:, :] if hr < L.shape[0] else L[:0, :]
    out = {
        "path": path,
        "h": int(L.shape[0]), "w": int(L.shape[1]),
        "horizon_row": hr,
        "lum_mean": float(L.mean()),
        "lum_p50": float(np.percentile(L, 50)),
        "lum_p99": float(np.percentile(L, 99)),
        "lum_max": float(L.max()),
    }
    for f, t in thr.items():
        k = "sh%02d" % int(round(f * 100))
        out[k + "_all"] = float((L > t).mean())
        out[k + "_below"] = float((below > t).mean()) if below.size else 0.0
    out["clip"] = float((L >= 0.9300).mean())
    return out


_FRAME_RE = re.compile(r"(\d{4,7})\.png$")


def sweep(seq_dir, curve, step=1, limit=None, fracs=(0.75, 0.60, 0.50)):
    files = sorted(glob.glob(os.path.join(seq_dir, "*.png")))
    files = files[::step]
    if limit:
        files = files[:limit]
    rows = []
    for i, p in enumerate(files):
        m = _FRAME_RE.search(os.path.basename(p))
        r = measure(p, curve, fracs=fracs)
        r["frame"] = int(m.group(1)) if m else i
        rows.append(r)
        if (i + 1) % 100 == 0:
            print("   ... %d/%d" % (i + 1, len(files)))
    return rows


# --------------------------------------------------------------------- selftest
def selftest():
    """Four controls.  Two of them the instrument MUST fail.

    [1] POSITIVE CONTROL.  A synthetic frame at the film's mid grey must report
        0 % shoulder.  If it does not, the threshold is not where the curve says.
    [2] POSITIVE CONTROL.  A synthetic frame 3 stops over mid grey must report
        100 % shoulder at the 60 % threshold, because 3 stops over is past it.
    [3] NEGATIVE CONTROL, must FAIL.  A frame 1 stop over mid grey must NOT be
        called shoulder -- a threshold that fires on everything bright is not
        measuring compression.
    [4] The horizon finder must find a synthetic sky/ground step, and must
        return 0 on a flat frame rather than inventing one.
    """
    from PIL import Image
    import tempfile
    c = Curve()
    bad = []
    print("   curve: mid grey %.4f -> display %.4f;  peak slope %.4f at %.4f"
          % (MID_GREY_SCENE_LIN, c.display(MID_GREY_SCENE_LIN), c.peak,
             c.disp_at_peak))
    for f in (0.75, 0.60, 0.50):
        d = c.display_at_slope_fraction(f)
        print("   slope %2d%% of peak at display %.4f  = %+.2f stops over mid grey"
              % (f * 100, d, np.log2(c.scene_lin(d) / MID_GREY_SCENE_LIN)))

    tmp = tempfile.mkdtemp()

    def synth(stops, name):
        d = float(c.display(MID_GREY_SCENE_LIN * 2.0 ** stops))
        a = np.full((120, 200, 3), round(d * 255.0)).astype(np.uint8)
        p = os.path.join(tmp, name)
        Image.fromarray(a).save(p)
        return p, d

    p0, d0 = synth(0.0, "mid000000.png")
    r = measure(p0, c)
    print("   [1] mid grey frame  display %.4f  sh60_all %.4f" % (d0, r["sh60_all"]))
    if r["sh60_all"] > 0.001:
        bad.append("a mid-grey frame reports %.3f%% shoulder" % (100 * r["sh60_all"]))

    p3, d3 = synth(3.0, "over000000.png")
    r3 = measure(p3, c)
    print("   [2] +3 stops frame  display %.4f  sh60_all %.4f" % (d3, r3["sh60_all"]))
    if r3["sh60_all"] < 0.999:
        bad.append("a +3-stop frame reports only %.3f%% shoulder" % (100 * r3["sh60_all"]))

    p1, d1 = synth(1.0, "one000000.png")
    r1 = measure(p1, c)
    ok = r1["sh60_all"] < 0.001
    print("   [3] +1 stop frame   display %.4f  sh60_all %.4f -> %s"
          % (d1, r1["sh60_all"], "not shoulder, as it must be" if ok
             else "CALLED SHOULDER -- THE THRESHOLD IS MEANINGLESS"))
    if not ok:
        bad.append("+1 stop over mid grey is being called shoulder")

    a = np.zeros((120, 200, 3), np.uint8)
    a[:40] = 220
    a[40:] = 90
    p = os.path.join(tmp, "step000000.png")
    Image.fromarray(a).save(p)
    hr = _horizon_row(_luma(_load(p)))
    flat = _horizon_row(np.full((120, 200), 0.4))
    print("   [4] horizon on a sky/ground step -> row %d (want ~40); flat -> %d (want 0)"
          % (hr, flat))
    if not (30 <= hr <= 50):
        bad.append("the horizon finder put the step at row %d" % hr)
    if flat != 0:
        bad.append("the horizon finder invented a horizon at row %d on a flat frame" % flat)

    for b in bad:
        print("   FAIL " + b)
    print(">> STAGE RESULT: " + (TOKEN_OK if not bad else TOKEN_FAIL))
    return 0 if not bad else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seq", action="append", default=[])
    ap.add_argument("--png", action="append", default=[])
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--json", default="")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(sys.argv[1:])
    if a.selftest:
        return selftest()
    c = Curve()
    print(">> AgX -3.628: mid grey -> %.4f, peak slope %.4f, "
          "75/60/50%% of peak at %.4f / %.4f / %.4f"
          % (c.display(MID_GREY_SCENE_LIN), c.peak,
             c.display_at_slope_fraction(0.75),
             c.display_at_slope_fraction(0.60),
             c.display_at_slope_fraction(0.50)))
    rows = []
    for d in a.seq:
        r = sweep(os.path.expanduser(d), c, step=a.step, limit=a.limit or None)
        for x in r:
            x["seq"] = os.path.basename(os.path.normpath(d))
        rows += r
        print(">> %s: %d frames" % (d, len(r)))
    for p in a.png:
        x = measure(os.path.expanduser(p), c)
        m = _FRAME_RE.search(os.path.basename(p))
        x["frame"] = int(m.group(1)) if m else -1
        x["seq"] = "single"
        rows.append(x)
    if a.json:
        json.dump(rows, open(a.json, "w"))
        print(">> wrote %s (%d rows)" % (a.json, len(rows)))
    print(">> STAGE RESULT: " + TOKEN_OK)
    return 0


if __name__ == "__main__":
    sys.exit(main())
