#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2256_ab_measure.py — the A/B on the La Passerelle fascia, with its null.

    BEFORE   the defect re-authored     (r2256_ab_before.blend)
    AFTER    the fix                    (r2256_ab_after.blend)
    NULL     AFTER rendered a second time from a byte-identical copy of the
             same scene, so the pair difference has a floor to be judged against

Every arm is the same camera (ONER, frame 2575), the same lens, the same DOF,
the same shutter, the same 400 samples / adaptive 0.01 / OpenImageDenoise and
the same border. The only thing that differs between BEFORE and AFTER is the
deleted `mb.text("PASSERELLE  2", ...)`.

A DIFFERENCE IS ONLY EVIDENCE IF IT IS BIGGER THAN THE NULL. Cycles is
stochastic and OIDN is not idempotent across runs, so two renders of the same
scene do not match bit for bit; the null measures exactly how far apart "no
change at all" lands, and the BEFORE/AFTER distance has to clear it.

Usage:  python3 tools/r2256_ab_measure.py BEFORE.png AFTER.png NULL.png [OUTDIR]
"""
import os
import subprocess
import sys

import numpy as np

W, H = 3840, 2160
# the sign band, in delivered-frame pixels (the review's crop, widened)
CX0, CX1, CY0, CY1 = 1500, 2200, 285, 420


# the border the jobs were submitted with, normalised, origin bottom-left
BORDER = (0.3125, 0.65104, 0.76852, 0.90741)
OFF = [0, 0]          # (x, y) of the returned image's top-left in frame pixels


def gray(path):
    """Return the image, and set OFF so frame pixel coords still address it.

    A border render may come back either as the full 3840x2160 with black
    outside the border, or cropped to the border itself.  Guessing wrong moves
    every measurement by 1200 px, so the size is read and the offset derived.
    """
    dim = subprocess.run(["/usr/bin/magick", "identify", "-format", "%w %h", path],
                         capture_output=True, text=True).stdout.split()
    w, h = int(dim[0]), int(dim[1])
    raw = subprocess.run(["/usr/bin/magick", path, "-colorspace", "RGB",
                          "-depth", "16", "gray:-"], capture_output=True).stdout
    a = np.frombuffer(raw, dtype=">u2").astype(np.float64).reshape(h, w) / 65535.0
    if (w, h) == (W, H):
        OFF[0] = OFF[1] = 0
    else:
        bx0 = int(round(BORDER[0] * W))
        by1 = int(round((1.0 - BORDER[3]) * H))       # top edge, top-origin
        OFF[0], OFF[1] = bx0, by1
        exp = (int(round(BORDER[1] * W)) - bx0,
               int(round((1.0 - BORDER[2]) * H)) - by1)
        if abs(w - exp[0]) > 2 or abs(h - exp[1]) > 2:
            raise SystemExit("%s is %dx%d; the border predicts %dx%d"
                             % (path, w, h, exp[0], exp[1]))
    return a


def band(a):
    return a[CY0 - OFF[1]:CY1 - OFF[1], CX0 - OFF[0]:CX1 - OFF[0]]


def stats(a, b):
    d = band(a) - band(b)
    return dict(rms=float(np.sqrt((d ** 2).mean())),
                p999=float(np.percentile(np.abs(d), 99.9)),
                mx=float(np.abs(d).max()),
                over02=float((np.abs(d) > 0.02).mean()),
                npx=int(d.size))


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    pb, pa, pn = sys.argv[1:4]
    outdir = sys.argv[4] if len(sys.argv) > 4 else os.path.dirname(pa) or "."
    B, A, N = gray(pb), gray(pa), gray(pn)

    sn = stats(A, N)
    sd = stats(B, A)
    print("SIGN BAND  x %d-%d, y %d-%d  (%d px)" % (CX0, CX1, CY0, CY1, sn["npx"]))
    print("")
    print("  %-34s %8s %8s %8s %9s" % ("", "rms", "p99.9", "max", ">0.02"))
    print("  %-34s %8.5f %8.5f %8.5f %8.2f%%"
          % ("NULL   after vs after-again", sn["rms"], sn["p999"], sn["mx"],
             100 * sn["over02"]))
    print("  %-34s %8.5f %8.5f %8.5f %8.2f%%"
          % ("A/B    before vs after", sd["rms"], sd["p999"], sd["mx"],
             100 * sd["over02"]))
    print("")
    r = sd["rms"] / max(sn["rms"], 1e-12)
    print("  the fix moves the sign band %.1fx the repeat-render floor" % r)

    # where the change is: the deleted run's own footprint vs everywhere else
    d = np.abs(band(B) - band(A))
    n = np.abs(band(A) - band(N))
    # the run projects to px (1818.7, 357.5); take a 260 x 70 px box on it
    gx0, gx1 = 1818 - 130 - CX0, 1818 + 130 - CX0    # band-local, so OFF cancels
    gy0, gy1 = 357 - 35 - CY0, 357 + 35 - CY0
    inside = d[gy0:gy1, gx0:gx1]
    mask = np.ones_like(d, bool)
    mask[gy0:gy1, gx0:gx1] = False
    print("")
    print("  ON the deleted run (260x70 px)   rms %.5f   max %.5f"
          % (float(np.sqrt((inside ** 2).mean())), float(inside.max())))
    print("  OFF it, rest of the sign band    rms %.5f   max %.5f"
          % (float(np.sqrt((d[mask] ** 2).mean())), float(d[mask].max())))
    print("  the NULL, same band              rms %.5f   max %.5f"
          % (n.mean() * 0 + float(np.sqrt((n ** 2).mean())), float(n.max())))

    for tag, path in (("before", pb), ("after", pa), ("null", pn)):
        o = os.path.join(outdir, "crop_%s.png" % tag)
        subprocess.run(["/usr/bin/magick", path, "-crop",
                        "%dx%d+%d+%d" % (CX1 - CX0, CY1 - CY0,
                                         CX0 - OFF[0], CY0 - OFF[1]),
                        "+repage", "-filter", "point", "-resize", "300%", o])
        print("  wrote", o)


if __name__ == "__main__":
    main()
