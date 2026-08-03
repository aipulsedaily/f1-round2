"""Measure a driver-mask render, so the imperfection ramps are set from the
geometry's actual distribution instead of from a guess.

    .venv/bin/python tools/mask_stats.py work/raw_SW.png work/raw_MB.png ...

Expects an RGBA render made with `render_local.py --standard --alpha --nocomp`
of a blend built by `imperfections.py --debug Point,Occl,Micro`. Alpha is the
part mask; the RGB channels are the raw drivers, sRGB-encoded by the Standard
view transform, so they are decoded back to linear before any percentile.

WHY THIS EXISTS: the first calibration was read off a render that had gone
through the scene's Glare compositor and included the black showroom shell in
its percentiles. Both make the numbers meaningless in the same direction — they
say "the mask is everywhere" — and both are invisible unless you look.
"""
import sys

import numpy as np
from PIL import Image

CH = ("Pointiness", "Occlusion", "Micro")
POINT_T = (0.505, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.60, 0.65)
OCCL_T = (0.05, 0.10, 0.20, 0.30, 0.36, 0.45, 0.55, 0.65, 0.78)


def s2l(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def main(paths):
    for p in paths:
        im = np.asarray(Image.open(p).convert("RGBA"), dtype=np.float64) / 255.0
        a = im[..., 3]
        fg = a > 0.98
        if not fg.any():
            print(f"{p}: no opaque pixels — was --alpha/--isolate used?")
            continue
        print(f"\n=== {p}   {int(fg.sum())} px ({100*fg.mean():.1f}% of frame)")
        vals = [s2l(im[..., i])[fg] for i in range(3)]
        for nm, v in zip(CH, vals):
            q = np.percentile(v, [1, 5, 25, 50, 75, 90, 95, 99])
            print(f"  {nm:11s} mean={v.mean():.4f} std={v.std():.4f}  "
                  f"p1/5/25/50/75/90/95/99 " + " ".join(f"{x:.3f}" for x in q))
        print("  surface fraction above threshold")
        print("    pointiness " + "  ".join(
            f"{t:.3f}:{100*float((vals[0] > t).mean()):5.1f}%" for t in POINT_T))
        print("    occlusion  " + "  ".join(
            f"{t:.2f}:{100*float((vals[1] > t).mean()):5.1f}%" for t in OCCL_T))


if __name__ == "__main__":
    main(sys.argv[1:])
