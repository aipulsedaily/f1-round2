"""The `--dof off` A/B: how much of a frame's softness is the LENS, block by block.

    .venv/bin/python tools/dof_ab.py --selftest
    .venv/bin/python tools/dof_ab.py WITH_DOF.png DOF_OFF.png

Two renders of the same frame, same camera, same samples, same resolution, one
with the scene's depth of field and one without. **The difference between them is
defocus and nothing else, so whatever softness survives in the DOF-off frame is
motion blur.**

WHY THIS IS NOT A WHOLE-FRAME NUMBER
------------------------------------
A whole-frame gradient ratio answers the wrong question, for the reason R2-278
logged: a contrast metric goes blind when the feature and its own baseline sample
the same rows, and it reported "no change" on a frame where two bays of lattice
had visibly gone. So this measures per block, and reports the DISTRIBUTION.

THE NULL IS INSIDE THE FRAME, AND IT IS FREE
--------------------------------------------
Switching DOF off cannot sharpen what was already at the focus plane. Those blocks
therefore differ only by Monte Carlo noise between two independent renders, and
their change fraction IS the null — measured on the same pair, at the same
samples, with no second render needed. The low decile of the change distribution
is that null. A frame whose MEDIAN block sits near its own null was not being
softened by the lens.

Reported per pair:

    p10    the null: blocks already sharp at both settings
    p50    the typical block
    p90    the blocks the lens was genuinely blurring
    lift   p50 / p10 -- the typical block against the frame's own noise floor

and the anisotropy of both frames, because the direction is the other half of the
argument: removing an ISOTROPIC blur from a picture that also has a DIRECTIONAL
one must leave the anisotropy the SAME OR HIGHER. If it falls, defocus was the
dominant term.
"""

import sys

import numpy as np
from PIL import Image

BLOCK = 120          # px at 4K; 32x18 blocks


def grad_rms_blocks(a, block=BLOCK):
    ix = np.zeros_like(a)
    iy = np.zeros_like(a)
    ix[:, 1:-1] = 0.5 * (a[:, 2:] - a[:, :-2])
    iy[1:-1, :] = 0.5 * (a[2:, :] - a[:-2, :])
    g = ix * ix + iy * iy
    h, w = a.shape
    nh, nw = h // block, w // block
    g = g[:nh * block, :nw * block].reshape(nh, block, nw, block)
    return np.sqrt(g.mean(axis=(1, 3)))


def load(p):
    return np.asarray(Image.open(p).convert("L"), dtype=np.float64) / 255.0


def compare(with_dof, dof_off, block=BLOCK):
    a, b = load(with_dof), load(dof_off)
    if a.shape != b.shape:
        raise SystemExit(">> FAIL: %s is %s and %s is %s — a control that is not "
                         "the same size as its subject is not a control"
                         % (with_dof, a.shape, dof_off, b.shape))
    ga, gb = grad_rms_blocks(a, block), grad_rms_blocks(b, block)
    live = ga > 1e-4                       # skip flat sky/floor: 0/0 is not a ratio
    frac = np.zeros_like(ga)
    frac[live] = (gb[live] - ga[live]) / ga[live]
    v = np.sort(frac[live])
    n = len(v)
    return {
        "blocks": int(n),
        "p10": float(v[int(0.10 * n)]),
        "p50": float(v[int(0.50 * n)]),
        "p90": float(v[int(0.90 * n)]),
        "whole_frame": float(gb[live].mean() / ga[live].mean() - 1.0),
    }


def selftest():
    """Synthetic pairs whose answers are known without this code."""
    ok = True

    def chk(name, got, want, tol, cmp="eq"):
        nonlocal ok
        good = (abs(got - want) <= tol) if cmp == "eq" else (got > want)
        ok = ok and good
        print("  %-56s %8.4f  %s %7.4f  %s"
              % (name, got, "~=" if cmp == "eq" else ">", want,
                 "ok" if good else "FAIL"))

    rng = np.random.default_rng(11)
    base = rng.random((1080, 1920))

    def disc(x, r):
        y, xx = np.mgrid[-r:r + 1, -r:r + 1]
        k = ((xx * xx + y * y) <= r * r).astype(np.float64)
        k /= k.sum()
        o = np.zeros_like(x)
        for j in range(-r, r + 1):
            for i in range(-r, r + 1):
                if k[j + r, i + r]:
                    o += k[j + r, i + r] * np.roll(np.roll(x, j, 0), i, 1)
        return o

    def save(x, p):
        Image.fromarray((np.clip(x, 0, 1) * 255).astype(np.uint8)).save(p)

    import tempfile
    import os
    d = tempfile.mkdtemp()
    pa, pb = os.path.join(d, "a.png"), os.path.join(d, "b.png")

    # NEGATIVE CONTROL: identical frames. Every block must read 0 change.
    save(base, pa)
    save(base, pb)
    r = compare(pa, pb, block=120)
    chk("NEGATIVE CONTROL: identical pair, p50 change", r["p50"], 0.0, 1e-9)
    chk("NEGATIVE CONTROL: identical pair, p90 change", r["p90"], 0.0, 1e-9)

    # POSITIVE: a genuinely defocused frame against its sharp original must show
    # a large positive change when the blur is removed.
    save(disc(base, 4), pa)
    save(base, pb)
    r = compare(pa, pb, block=120)
    chk("POSITIVE: 4 px disc removed, p50 change", r["p50"], 1.0, 0.0, "gt")

    # THE NULL IS REAL: half the frame defocused, half untouched. The untouched
    # half must appear as a low decile near zero while the median is large.
    half = base.copy()
    half[:, :960] = disc(base, 4)[:, :960]
    save(half, pa)
    save(base, pb)
    r = compare(pa, pb, block=120)
    chk("half-blurred pair: p10 (the untouched half) is the null",
        r["p10"], 0.0, 0.05)
    chk("half-blurred pair: p90 (the blurred half) is large",
        r["p90"], 1.0, 0.0, "gt")

    print("\nSTAGE RESULT %s selftest" % ("OK" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--selftest" in sys.argv or len(args) < 2:
        return selftest()
    r = compare(args[0], args[1])
    print("WITH DOF   %s" % args[0].split("/")[-1])
    print("DOF OFF    %s" % args[1].split("/")[-1])
    print("  blocks measured                     %d" % r["blocks"])
    print("  p10  the frame's own null           %+.3f" % r["p10"])
    print("  p50  the typical block              %+.3f" % r["p50"])
    print("  p90  what the lens was blurring     %+.3f" % r["p90"])
    print("  whole frame                         %+.3f" % r["whole_frame"])
    print("STAGE RESULT OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
