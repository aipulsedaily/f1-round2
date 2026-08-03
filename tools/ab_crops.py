"""Build the before/after 1:1 crop strips for the imperfection audit.

    .venv/bin/python tools/ab_crops.py --tag p1 --clusters SW,MB,CORNER_FL

Crops are fixed per cluster so every tuning pass is compared on exactly the same
pixels — a moving crop makes "it looks better now" unfalsifiable. Everything is
cut at 1:1; nothing here is ever resampled.
"""
import argparse
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (name, x, y, w, h) in 3840x2160 pixels — chosen on the BEFORE frames.
REGIONS = {
    "SW": [
        ("display_glass", 1620, 730, 800, 340),   # R2-014 lives here
        ("grip_left", 1400, 780, 420, 560),       # skin oil / polish-wear
        ("buttons", 1600, 950, 800, 460),         # dust in the wells
        ("shell_edge", 1330, 1180, 620, 420),     # carbon + edge wear
    ],
    "MB": [
        ("paint_panel", 1150, 300, 800, 560),     # livery: orange peel
        ("paint_shoulder", 900, 700, 800, 560),
        ("carbon_duct", 820, 20, 700, 420),
        ("fasteners", 1500, 60, 760, 380),
    ],
    # FW is the regression cluster: it was never used to tune anything, so if
    # numbers set on SW/MB/CORNER hold up here they are not overfitted to them.
    "FW": [
        ("endplate", 1500, 350, 800, 560),
        ("damper_pod", 2150, 720, 700, 460),
        ("vanes", 2050, 40, 800, 460),
    ],
    "CORNER_FL": [
        ("rod_ends", 2450, 330, 900, 560),        # titanium + anodised red
        ("wishbone", 1750, 700, 800, 500),
        ("tyre_sidewall", 380, 560, 800, 700),    # rubber dulling film
        ("rim_face", 380, 1180, 700, 560),
    ],
}


def band(im, x, y, w, h):
    W, H = im.size
    x = max(0, min(W - w, x)); y = max(0, min(H - h, y))
    return im.crop((x, y, x + w, y + h))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tag", required=True, help="after-render tag, e.g. p1")
    p.add_argument("--clusters", default="SW,MB,CORNER_FL")
    p.add_argument("--outdir", default=None)
    a = p.parse_args()
    out = a.outdir or os.path.join(ROOT, "render", "macro", "ab")
    os.makedirs(out, exist_ok=True)

    for c in [x.strip() for x in a.clusters.split(",")]:
        b = os.path.join(ROOT, "render", "macro", "before", f"{c}.png")
        f = os.path.join(ROOT, "render", "macro", "after", f"{a.tag}_{c}.png")
        if not (os.path.exists(b) and os.path.exists(f)):
            print(f"!! missing {b if not os.path.exists(b) else f}")
            continue
        A = Image.open(b).convert("RGB")
        B = Image.open(f).convert("RGB")
        for nm, x, y, w, h in REGIONS[c]:
            ca, cb = band(A, x, y, w, h), band(B, x, y, w, h)
            gap = 14
            img = Image.new("RGB", (w * 2 + gap, h + 30), (18, 18, 20))
            img.paste(ca, (0, 30)); img.paste(cb, (w + gap, 30))
            d = ImageDraw.Draw(img)
            d.text((6, 10), f"BEFORE  {c}/{nm}  [{x},{y} {w}x{h}]",
                   fill=(225, 225, 225))
            d.text((w + gap + 6, 10), f"AFTER {a.tag}", fill=(255, 205, 110))
            path = os.path.join(out, f"{a.tag}_{c}_{nm}.png")
            img.save(path)
            na = np.asarray(ca.convert("L"), np.float64) / 255
            nb = np.asarray(cb.convert("L"), np.float64) / 255
            print(f"{c}/{nm:15s} dMean={nb.mean()-na.mean():+.5f} "
                  f"dStd={nb.std()-na.std():+.5f} "
                  f"maxAbsDelta={np.abs(nb-na).max():.4f} "
                  f"px>2%={100*float((np.abs(nb-na) > 0.02).mean()):.2f}% -> {path}")


if __name__ == "__main__":
    main()
