"""Stack crops of the same rectangle from N delivered frames, 1:1 and blown up.

    .venv/bin/python sim/sbs.py out.png A.png B.png C.png -- LABEL_A LABEL_B ...

The crop is the SAME pixel rectangle in every image, because they are the same
camera at the same frame at the same resolution; nothing is registered or
aligned, so any difference you see is a difference in the render.
"""
import sys

import numpy as np
from PIL import Image, ImageDraw

BOX = (1840, 1010, 2000, 1150)          # the wound at f2978, 4K, with margin
SCALE = 7


def main():
    args = sys.argv[1:]
    labels = []
    if "--" in args:
        i = args.index("--")
        labels = args[i + 1:]
        args = args[:i]
    out, srcs = args[0], args[1:]
    tiles = []
    for p in srcs:
        im = Image.open(p).convert("RGB").crop(BOX)
        tiles.append(im.resize((im.width * SCALE, im.height * SCALE),
                               Image.NEAREST))
    w, h = tiles[0].size
    pad, top = 8, 26
    canvas = Image.new("RGB", (len(tiles) * w + (len(tiles) + 1) * pad,
                               h + top + 2 * pad), (24, 24, 24))
    d = ImageDraw.Draw(canvas)
    for i, t in enumerate(tiles):
        x = pad + i * (w + pad)
        canvas.paste(t, (x, top + pad))
        lab = labels[i] if i < len(labels) else srcs[i].split("/")[-1]
        d.text((x + 4, 6), lab, fill=(235, 235, 235))
    canvas.save(out)
    print("wrote %s  %dx%d  crop=%s scale=%d" % (out, canvas.width,
                                                 canvas.height, BOX, SCALE))


main()
