"""Is this frame soft because of the LENS or because of the CAMERA? From pixels.

Defocus is isotropic: the circle of confusion is a circle, so it suppresses
gradients equally in every direction. A 180-degree shutter is not: it is a line
integral along ONE direction, so it suppresses gradients ALONG the smear and
leaves gradients ACROSS it almost untouched.

So the structure tensor of the image separates them without needing a second
render:

    J = [[<Ix Ix>, <Ix Iy>], [<Ix Iy>, <Iy Iy>]]   summed over the frame
    lambda1 >= lambda2,   anisotropy = (l1 - l2) / (l1 + l2)

and the eigenvector of lambda1 is the direction gradients SURVIVE in, which is
perpendicular to the smear. The prediction is independent: `tools/beat1_smear.py`
computes the smear direction from the camera path, and the two must agree.

    .venv/bin/python tools/blur_anisotropy.py --selftest
    .venv/bin/python tools/blur_anisotropy.py FRAME.png [FRAME.png ...]

READ THIS WITH ITS LIMIT IN MIND. A frame full of parallel man-made edges is
anisotropic before anything blurs it — a wall of louvres reads as smeared. The
selftest therefore includes a sharp, strongly-oriented negative control, and the
verdict below is only ever taken as "this frame is MORE anisotropic than the same
scene rendered without motion", never as an absolute threshold.
"""

import math
import sys

import numpy as np
from PIL import Image


def tensor(img):
    """(anisotropy, angle of the surviving-gradient axis in degrees, |grad|)."""
    a = np.asarray(img.convert("L"), dtype=np.float64) / 255.0
    ix = np.zeros_like(a)
    iy = np.zeros_like(a)
    ix[:, 1:-1] = 0.5 * (a[:, 2:] - a[:, :-2])
    iy[1:-1, :] = 0.5 * (a[2:, :] - a[:-2, :])
    jxx = float((ix * ix).sum())
    jyy = float((iy * iy).sum())
    jxy = float((ix * iy).sum())
    tr = jxx + jyy
    d = math.sqrt(max((jxx - jyy) ** 2 + 4.0 * jxy * jxy, 0.0))
    l1, l2 = 0.5 * (tr + d), 0.5 * (tr - d)
    aniso = (l1 - l2) / l1 if l1 > 0 else 0.0
    ang = 0.5 * math.degrees(math.atan2(2.0 * jxy, jxx - jyy))
    return aniso, ang % 180.0, math.sqrt(tr / a.size)


def _blur_line(a, dx, dy, n):
    """Box-average along a direction: a synthetic 180-degree shutter."""
    out = np.zeros_like(a)
    for k in range(n):
        s = k - (n - 1) / 2.0
        out += np.roll(np.roll(a, int(round(s * dy)), axis=0),
                       int(round(s * dx)), axis=1)
    return out / n


def _disc(a, r):
    """Isotropic blur: a disc, which is what a circle of confusion is."""
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    k = ((x * x + y * y) <= r * r).astype(np.float64)
    k /= k.sum()
    out = np.zeros_like(a)
    for j in range(-r, r + 1):
        for i in range(-r, r + 1):
            w = k[j + r, i + r]
            if w:
                out += w * np.roll(np.roll(a, j, axis=0), i, axis=1)
    return out


def selftest():
    ok = True

    def chk(name, got, want, tol, cmp="eq"):
        nonlocal ok
        good = (abs(got - want) <= tol) if cmp == "eq" else (got > want)
        ok = ok and good
        print("  %-54s %8.4f  %s %8.4f  %s"
              % (name, got, "~=" if cmp == "eq" else ">", want,
                 "ok" if good else "FAIL"))

    rng = np.random.default_rng(7)
    base = rng.random((256, 256))

    def an(a):
        return tensor(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)))

    a0, g0, _ = an(base)
    chk("isotropic noise, unblurred: anisotropy", a0, 0.0, 0.05)

    a1, g1, _ = an(_disc(base, 4))
    chk("NEGATIVE CONTROL: disc blur stays isotropic", a1, 0.0, 0.10)

    a2, g2, _ = an(_blur_line(base, 1, 0, 13))
    chk("POSITIVE: horizontal smear is anisotropic", a2, 0.60, 0.0, "gt")
    chk("  and the surviving axis is VERTICAL (90 deg)", g2, 90.0, 6.0)

    a3, g3, _ = an(_blur_line(base, 0, 1, 13))
    chk("POSITIVE: vertical smear, surviving axis HORIZONTAL", g3 % 180.0, 0.0, 6.0)
    chk("  same magnitude either way", abs(a3 - a2), 0.0, 0.08)

    # A SHARP but strongly oriented picture -- the failure mode of this metric.
    stripes = np.zeros((256, 256))
    stripes[::4, :] = 1.0
    a4, g4, _ = an(stripes)
    print("  %-54s %8.4f  (this metric CANNOT call this one; see the docstring)"
          % ("sharp horizontal stripes read as anisotropic", a4))

    print("\nSTAGE RESULT %s selftest" % ("OK" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--selftest" in sys.argv or not args:
        return selftest()
    print("%-34s %10s %12s %10s" % ("frame", "anisotropy", "surviving deg",
                                    "rms grad"))
    for p in args:
        a, g, rms = tensor(Image.open(p))
        print("%-34s %10.4f %12.1f %10.5f" % (p.split("/")[-1], a, g, rms))
    print("STAGE RESULT OK frames=%d" % len(args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
