"""TWO RENDERS, AND THE FLOOR UNDER THEM.

    .venv/bin/python work/r2187/frame_ab.py A.png B.png [--tiles 8 6] [--diff OUT.png]

Cycles does not have to agree with itself, so "5 % of the frame changed" is not
a finding until you know what 0 % looks like.  This prints the same table for a
signal pair and for a control pair, and a tile grid so a difference confined to
one corner of the frame -- which is what a 400 m distant apron would look like
-- cannot hide inside a whole-frame mean.
"""
import argparse
import sys

import numpy as np
from PIL import Image


def load(p):
    im = Image.open(p).convert("RGB")
    return np.asarray(im).astype(np.int32), im.size


def main():
    p = argparse.ArgumentParser()
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--tiles", nargs=2, type=int, default=[8, 6])
    p.add_argument("--diff", default="")
    p.add_argument("--label", default="")
    a = p.parse_args()

    A, sa = load(a.a)
    B, sb = load(a.b)
    if sa != sb:
        print("REFUSE: %s is %s, %s is %s" % (a.a, sa, a.b, sb))
        print(">> STAGE RESULT: AB_REFUSED_SIZE")
        return 3
    D = np.abs(A - B).max(axis=2)
    W, H = sa
    print("%s  %s  vs  %s   %dx%d" % (a.label, a.a.split("/")[-1],
                                      a.b.split("/")[-1], W, H))
    print("  whole frame: changed %.2f %%   >2/255 %.4f %%   >8/255 %.4f %%   "
          "mean|d| %.3f   MAX %d"
          % (100 * (D > 0).mean(), 100 * (D > 2).mean(), 100 * (D > 8).mean(),
             D.mean(), D.max()))
    nx, ny = a.tiles
    worst = []
    for j in range(ny):
        for i in range(nx):
            t = D[j * H // ny:(j + 1) * H // ny, i * W // nx:(i + 1) * W // nx]
            worst.append((100 * (t > 8).mean(), t.mean(), t.max(), i, j))
    worst.sort(reverse=True)
    print("  worst tiles of %d (%dx%d grid), by %% over 8/255:" % (nx * ny, nx, ny))
    for pc, mn, mx, i, j in worst[:4]:
        print("    tile (%d,%d)  >8/255 %6.2f %%   mean|d| %6.3f   max %3d"
              % (i, j, pc, mn, mx))
    if a.diff:
        Image.fromarray(np.clip(D * 8, 0, 255).astype(np.uint8)).save(a.diff)
        print("  diff x8 -> %s" % a.diff)
    print(">> STAGE RESULT: AB_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
