"""Pixel-peep helper: cut 1:1 crops out of a 4K frame, and build A/B strips.

    .venv/bin/python tools/peep.py grid  IN.png OUT_DIR --n 3
    .venv/bin/python tools/peep.py crop  IN.png OUT.png --box X Y W H
    .venv/bin/python tools/peep.py ab    BEFORE.png AFTER.png OUT.png --box X Y W H
    .venv/bin/python tools/peep.py stats IN.png [--box X Y W H]

Crops are written at 1:1 — never downscaled — because a downscaled preview
hides exactly the class of defect this project's macro gate exists to catch.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw


def load(p):
    im = Image.open(p)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    return im


def cmd_grid(a):
    im = load(a.inp)
    W, H = im.size
    os.makedirs(a.out, exist_ok=True)
    n = a.n
    cw, ch = a.size
    for j in range(n):
        for i in range(n):
            cx = int((i + 0.5) / n * W)
            cy = int((j + 0.5) / n * H)
            x = max(0, min(W - cw, cx - cw // 2))
            y = max(0, min(H - ch, cy - ch // 2))
            im.crop((x, y, x + cw, y + ch)).save(
                os.path.join(a.out, f"c{j}{i}_{x}_{y}.png"))
    print(f">> {n*n} crops of {cw}x{ch} -> {a.out}")


def cmd_crop(a):
    im = load(a.inp)
    x, y, w, h = a.box
    im.crop((x, y, x + w, y + h)).save(a.out)
    print(f">> {w}x{h} @ {x},{y} -> {a.out}")


def cmd_ab(a):
    x, y, w, h = a.box
    A = load(a.before).crop((x, y, x + w, y + h))
    B = load(a.after).crop((x, y, x + w, y + h))
    gap = 12
    out = Image.new("RGB", (w * 2 + gap, h + 26), (20, 20, 22))
    out.paste(A, (0, 26))
    out.paste(B, (w + gap, 26))
    d = ImageDraw.Draw(out)
    d.text((6, 8), f"BEFORE  {os.path.basename(a.before)}  [{x},{y} {w}x{h}]",
           fill=(230, 230, 230))
    d.text((w + gap + 6, 8), f"AFTER  {os.path.basename(a.after)}",
           fill=(255, 210, 120))
    out.save(a.out)
    print(f">> A/B -> {a.out}")


def cmd_stats(a):
    im = load(a.inp)
    if a.box:
        x, y, w, h = a.box
        im = im.crop((x, y, x + w, y + h))
    v = np.asarray(im.convert("L"), dtype=np.float64) / 255.0
    rgb = np.asarray(im.convert("RGB"), dtype=np.float64) / 255.0
    lap = (np.abs(4 * v[1:-1, 1:-1] - v[:-2, 1:-1] - v[2:, 1:-1]
                  - v[1:-1, :-2] - v[1:-1, 2:]))
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    print(f"{os.path.basename(a.inp)}  mean={v.mean():.5f} std={v.std():.5f} "
          f"sharp(varLap)={lap.var()*1e4:.4f}e-4 sat={sat.mean():.5f} "
          f"clipped={float((v > 0.995).mean()):.5f} crushed={float((v < 0.005).mean()):.5f}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grid"); g.add_argument("inp"); g.add_argument("out")
    g.add_argument("--n", type=int, default=3)
    g.add_argument("--size", type=int, nargs=2, default=[640, 640])
    c = sub.add_parser("crop"); c.add_argument("inp"); c.add_argument("out")
    c.add_argument("--box", type=int, nargs=4, required=True)
    b = sub.add_parser("ab"); b.add_argument("before"); b.add_argument("after")
    b.add_argument("out"); b.add_argument("--box", type=int, nargs=4, required=True)
    s = sub.add_parser("stats"); s.add_argument("inp")
    s.add_argument("--box", type=int, nargs=4, default=None)
    a = p.parse_args()
    {"grid": cmd_grid, "crop": cmd_crop, "ab": cmd_ab, "stats": cmd_stats}[a.cmd](a)


if __name__ == "__main__":
    main()
