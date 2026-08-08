"""R2-3061: THE CROP A PERSON CAN LOOK AT.

    .venv/bin/python tools/r2_3061_crop.py --before <dir> --after <dir> \
        --delivered work/r22881/4k/r22881_4k_001787.png --out <png>

One tile, 480 x 360 native 4K pixels, NO SCALING, in four conditions:

    delivered      the frame the client is looking at (film22, the whole world)
    before live    the surface alone, same pose, same 0.5 shutter
    before still   the surface alone, same pose, camera stopped
    after  still   the same, with the 45-160 mm octave authored
    after  live    what the audience would receive

Each panel carries its own coarse 16-64 px @4K number, measured by
`tools/r2_3061_judge.py` conventions, so the picture and the number cannot drift
apart. The smear is drawn to scale as a bar: it is 219 px long on a 480 px tile,
which is the fact the eye needs in order to read the rest of the sheet.
"""
import argparse
import os
import sys

import numpy as np

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "tools"))

TILE = (3, 1)
TW4, TH4 = 480, 360
SMEAR_PX, SMEAR_DEG = 218.8, 105.8


def tile_of(png, r=TILE[0], c=TILE[1]):
    from PIL import Image
    im = Image.open(png).convert("RGB")
    if im.size != (3840, 2160):
        raise SystemExit("%s is %s, not 3840x2160" % (png, im.size))
    return im.crop((c * TW4, r * TH4, (c + 1) * TW4, (r + 1) * TH4))


def coarse_of(png, r=TILE[0], c=TILE[1]):
    import r2_2881_pixelpeep as PP
    from PIL import Image
    a = np.asarray(Image.open(png).convert("RGB"), np.float32) / 255.0
    lev = PP.pyramid(PP.lum_of(a), 6)
    M = PP.TILE_MARGIN * PP.UPSCALE

    def tm(x):
        b = x.reshape(PP.TY, TH4, PP.TX, TW4)[:, M:TH4 - M, :, M:TW4 - M]
        return b.mean(axis=(1, 3))

    return float(np.stack([tm(l) for l in lev])[4:6].mean(axis=0)[r, c])


def find(d, frame):
    if not d or not os.path.isdir(d):
        return None
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".png") and ("%06d" % frame) in fn:
            return os.path.join(d, fn)
    return None


def main():
    from PIL import Image, ImageDraw
    ap = argparse.ArgumentParser()
    ap.add_argument("--delivered", default=os.path.join(
        R2, "work/r22881/4k/r22881_4k_001787.png"))
    ap.add_argument("--before", default="")
    ap.add_argument("--after", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    panels = []
    if os.path.exists(a.delivered):
        panels.append(("DELIVERED f1787 (film22, whole world, shutter open)",
                       a.delivered))
    for label, d in (("BEFORE", a.before), ("AFTER", a.after)):
        for arm, fr in (("live  (shutter open)", 1787), ("still (camera stopped)", 4787)):
            p = find(d, fr)
            if p:
                panels.append(("%s %s" % (label, arm), p))
    if not panels:
        raise SystemExit("nothing to draw")

    pad, top, gap = 10, 46, 8
    W = pad * 2 + len(panels) * TW4 + (len(panels) - 1) * gap
    H = top + TH4 + 78
    out = Image.new("RGB", (W, H), (16, 16, 18))
    d = ImageDraw.Draw(out)
    d.text((pad, 8), "R2-3061  f1787  TILE (3,1) — THE ROAD — AT DELIVERY "
                     "RESOLUTION, 1:1, NO SCALING", fill=(255, 196, 64))
    d.text((pad, 24), "coarse band = 16-64 px @4K; a tile is EMPTY below 0.00200 "
                      "(r2_2881_pixelpeep Gates.TILE_COARSE)", fill=(180, 180, 190))
    x = pad
    for label, png in panels:
        out.paste(tile_of(png), (x, top))
        cb = coarse_of(png)
        col = (255, 110, 110) if cb < 0.0020 else (140, 240, 150)
        d.text((x, top + TH4 + 6), label, fill=(220, 220, 230))
        d.text((x, top + TH4 + 22), "coarse 16-64 px @4K  %.5f%s"
               % (cb, "   EMPTY" if cb < 0.0020 else ""), fill=col)
        x += TW4 + gap

    # the shutter, drawn to scale on the first panel: 219 px on a 480 px tile
    import math
    dx = SMEAR_PX * math.cos(math.radians(SMEAR_DEG))
    dy = SMEAR_PX * math.sin(math.radians(SMEAR_DEG))
    cx, cy = pad + TW4 * 0.5, top + TH4 * 0.5
    x0, y0 = cx - dx * 0.5, cy - dy * 0.5
    d.line((x0, y0, x0 + dx, y0 + dy), fill=(255, 196, 64), width=3)
    for e in ((x0, y0), (x0 + dx, y0 + dy)):
        d.line((e[0] - 8, e[1], e[0] + 8, e[1]), fill=(255, 196, 64), width=3)
    d.text((pad + 6, top + 8), "219 px, to scale: how far this ground travels "
                               "across the open shutter", fill=(255, 196, 64))
    out.save(a.out)
    print(">> wrote %s  (%d panels)" % (a.out, len(panels)))
    print(">> STAGE RESULT: CROP_OK")


main()
