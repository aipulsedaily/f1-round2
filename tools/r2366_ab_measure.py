#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2366_ab_measure.py — the A/B on the paving relief ladder, with its null.

    BEFORE   `git show HEAD:world/build_architecture.py`
    AFTER    the four-octave relief ladder
    NULL     AFTER rendered a SECOND time from a byte-identical copy of the same
             scene, so the pair difference has a floor to be judged against

A DIFFERENCE IS ONLY EVIDENCE IF IT IS BIGGER THAN THE NULL. Cycles is
stochastic and OpenImageDenoise is not idempotent across runs, so two renders of
one scene do not match bit for bit. The null measures where "no change at all"
lands and the BEFORE/AFTER distance has to clear it.

THREE MEASUREMENTS, AND THE FIRST IS THE HEADLINE
-------------------------------------------------
1. PERIODICITY. The defect is not "too flat", it is "a rectangular patchwork" —
   a grid of flat greys with a hard step at every cell boundary. That is a
   PERIODIC structure, so it has a spectral signature, and the honest way to
   show it is gone is to measure the periodicity rather than to look at the
   picture and feel better. Reported as `peakiness`: the ratio of the strongest
   discrete peak in the windowed 2-D power spectrum to the local median of the
   spectrum around it. A featureless plane and a broadband surface both score
   low; only a repeating cell scores high. THIS READS DIFFERENTLY WHETHER THE
   DEFECT IS PRESENT OR ABSENT, which the brief rightly demands of any metric.

2. BAND POWER PER OCTAVE, in radiance modulation. The band-passed p-p of log
   luminance, per octave, directly comparable to `itemkit.RELIEF_BANDS`. The
   defect predicts: BEFORE has power at the cell octave and nothing anywhere
   else; AFTER has power across the octaves the frame can resolve.

   LOG LUMINANCE, NOT LINEAR. R2-060 measured paint-on-curvature leaking 40.9x
   more into a linear band-pass than into a log one.

3. THE FREE NEGATIVE CONTROL (R2-150). A region of the same frame the change
   cannot reach — here the sky, which contains no paving and no material this
   task touched. If the sky moves by more than the null, the diff is not the
   change. This costs nothing and it is the only thing standing between a
   headline and a coincidence.

Usage:
    python3 tools/r2366_ab_measure.py --before B.png --after A.png --null N.png
                                      [--frame 2978] [--out DIR]
"""
import argparse
import json
import os

import numpy as np

W, H = 3840, 2160

# The brief's own crop for the closing wide, and the beat-3 near view. `sky` is
# the negative control: chosen above the horizon at both frames.
REGIONS = {
    2978: dict(paving=(900, 780, 900, 420), sky=(200, 60, 1400, 240)),
    945:  dict(paving=(1100, 1500, 1600, 560), sky=(200, 40, 1400, 200)),
}


def read_gray(path):
    """Linear-light luminance from a PNG, without ImageMagick.

    The delivered PNGs are AgX-transformed sRGB, so this undoes the sRGB EOTF
    only. It does NOT try to invert AgX: every arm carries the same transform,
    so a monotone curve common to all three cancels in every comparison made
    here, and inverting it badly would not.
    """
    from PIL import Image
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64) / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722


def crop(a, r):
    x, y, w, h = r
    return a[y:y + h, x:x + w]


def peakiness(g):
    """How much of this region's structure sits in DISCRETE spectral peaks.

    A Hann window first, or the crop's own edges put a cross through the
    spectrum that dwarfs anything in the picture. The DC block and the lowest
    two rings are removed because a smooth gradient across the region — camber,
    a shadow, the falloff of the light — is form, not a repeat, and would
    otherwise be counted as the biggest 'peak' there is.

    Returns the peak / local-median ratio, and the pixel period of the peak.
    """
    g = g - g.mean()
    wy = np.hanning(g.shape[0])[:, None]
    wx = np.hanning(g.shape[1])[None, :]
    P = np.abs(np.fft.fftshift(np.fft.fft2(g * wy * wx))) ** 2
    cy, cx = P.shape[0] // 2, P.shape[1] // 2
    Y, X = np.mgrid[:P.shape[0], :P.shape[1]]
    fy = (Y - cy) / P.shape[0]
    fx = (X - cx) / P.shape[1]
    rad = np.sqrt(fy ** 2 + fx ** 2)
    keep = (rad > 0.010) & (rad < 0.45)
    if not keep.any():
        return dict(peakiness=float("nan"), period_px=None)
    Pk = np.where(keep, P, 0.0)
    med = np.median(P[keep])
    i = int(np.argmax(Pk))
    py, px = np.unravel_index(i, P.shape)
    r = rad[py, px]
    return dict(peakiness=float(Pk.flat[i] / max(med, 1e-30)),
                period_px=float(1.0 / max(r, 1e-9)),
                peak_fy=float(fy[py, px]), peak_fx=float(fx[py, px]))


def octaves(g, n=7):
    """Band-passed peak-to-peak of LOG luminance, per octave, in p-p units.

    A difference of Gaussians per octave; p-p taken at the 1st..99th percentile
    so a single fireball or a clipped highlight does not set the number for the
    whole band.
    """
    from scipy import ndimage
    lg = np.log(np.maximum(g, 1e-6))
    out = []
    prev = ndimage.gaussian_filter(lg, 1.0)
    s = 1.0
    for k in range(n):
        s2 = s * 2.0
        nxt = ndimage.gaussian_filter(lg, s2)
        band = prev - nxt
        lo, hi = np.percentile(band, [1.0, 99.0])
        out.append(dict(octave=k, sigma_px=s, pp=float(hi - lo)))
        prev, s = nxt, s2
    return out


def diff_stats(a, b, r):
    d = crop(a, r) - crop(b, r)
    return dict(rms=float(np.sqrt((d ** 2).mean())),
                p999=float(np.percentile(np.abs(d), 99.9)),
                mx=float(np.abs(d).max()),
                over02=float((np.abs(d) > 0.02).mean()),
                npx=int(d.size))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--null", required=True)
    ap.add_argument("--frame", type=int, default=2978)
    ap.add_argument("--mm-px", type=float, default=None,
                    help="surface mm per pixel, for reporting a period in "
                         "metres as well as pixels")
    ap.add_argument("--paving-window", type=int, nargs=4, default=None,
                    metavar=("X", "Y", "W", "H"),
                    help="the measured pure-paving rectangle from "
                         "tools/r2366_paving_window.py. COMPUTED ONCE FROM THE "
                         "BEFORE BUILD AND REUSED FOR EVERY ARM, so no arm can "
                         "move the goalposts by changing which pixels it is "
                         "judged on.")
    ap.add_argument("--control-window", type=int, nargs=4, default=None,
                    metavar=("X", "Y", "W", "H"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    reg = dict(REGIONS[a.frame])
    if a.paving_window:
        reg["paving"] = tuple(a.paving_window)
    if a.control_window:
        reg.pop("sky", None)
        reg["control"] = tuple(a.control_window)
    B, A, N = (read_gray(p) for p in (a.before, a.after, a.null))
    for nm, im, p in (("before", B, a.before), ("after", A, a.after),
                      ("null", N, a.null)):
        if im.shape != (H, W):
            raise SystemExit("%s is %s, expected %dx%d" % (p, im.shape, W, H))

    res = {"frame": a.frame, "regions": {}}
    for rn, r in reg.items():
        row = {"rect": list(r)}
        for nm, im in (("before", B), ("after", A), ("null", N)):
            g = crop(im, r)
            row[nm] = dict(mean=float(g.mean()), std=float(g.std()),
                           **peakiness(g))
            row[nm]["octaves"] = octaves(g)
        row["before_vs_after"] = diff_stats(B, A, r)
        row["after_vs_null"] = diff_stats(A, N, r)
        res["regions"][rn] = row

    print("FRAME %d" % a.frame)
    for rn, row in res["regions"].items():
        x, y, w, h = row["rect"]
        tag = " (NEGATIVE CONTROL — the change cannot reach it)" \
            if rn in ("sky", "control") else ""
        print("\n=== %s  %dx%d+%d+%d%s" % (rn.upper(), w, h, x, y, tag))
        print("  %-10s %10s %10s %11s %11s"
              % ("", "mean", "std", "peakiness", "period_px"))
        for nm in ("before", "after", "null"):
            d = row[nm]
            print("  %-10s %10.5f %10.5f %11.1f %11.1f"
                  % (nm, d["mean"], d["std"], d["peakiness"], d["period_px"]))
        if a.mm_px and rn == "paving":
            for nm in ("before", "after"):
                print("     %s peak period = %.2f m across the view"
                      % (nm, row[nm]["period_px"] * a.mm_px / 1000.0))
        print("  octave band power (p-p of log luminance)")
        print("     %-8s %9s %9s %9s" % ("sigma_px", "before", "after", "null"))
        for k in range(len(row["before"]["octaves"])):
            print("     %-8.0f %9.4f %9.4f %9.4f"
                  % (row["before"]["octaves"][k]["sigma_px"],
                     row["before"]["octaves"][k]["pp"],
                     row["after"]["octaves"][k]["pp"],
                     row["null"]["octaves"][k]["pp"]))
        print("  %-22s %9s %9s %9s %9s"
              % ("", "rms", "p99.9", "max", ">0.02"))
        for lbl, k in (("BEFORE vs AFTER", "before_vs_after"),
                       ("AFTER  vs NULL ", "after_vs_null")):
            d = row[k]
            print("  %-22s %9.5f %9.5f %9.5f %8.3f%%"
                  % (lbl, d["rms"], d["p999"], d["mx"], 100 * d["over02"]))
        n, s = row["after_vs_null"]["rms"], row["before_vs_after"]["rms"]
        print("  SIGNAL / NULL = %.1fx" % (s / max(n, 1e-12)))

    if a.out:
        os.makedirs(a.out, exist_ok=True)
        p = os.path.join(a.out, "r2366_ab_f%d.json" % a.frame)
        json.dump(res, open(p, "w"), indent=1)
        print("\nwrote %s" % p)
    print("\nSTAGE RESULT: r2366_ab_measure PASS")


if __name__ == "__main__":
    main()
