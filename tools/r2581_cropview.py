"""R2-589. What a candidate focal ACTUALLY leaves in the frame, judged on pixels.

    .venv/bin/python tools/r2581_cropview.py --selftest
    .venv/bin/python tools/r2581_cropview.py --frame 2110 --zooms 1.3,1.5,1.7,1.94

WHY THIS EXISTS
---------------
R2-588 rendered four matched pairs and found the one thing no number showed: at
f2110 the biggest zoom "leaves a bare strip of asphalt -- the wide had more in
it." Choosing how far to pull the peak back is therefore a question about what
is INSIDE the frame at a given focal, and the answer is only visible in a
picture. This makes those pictures without buying GPU time for every trial.

WHAT IT DOES, AND WHAT IT IS NOT
--------------------------------
A lens-only zoom by factor z about the optical axis is a centre crop of the same
render to 1/z of its width and height. So the FRAMING of a candidate focal can
be previewed exactly by cropping the already-rendered `before` frame -- the
composition is right to the pixel. What it does NOT reproduce is RESOLUTION: the
real render at z puts z times more samples on the subject, so the preview is
pessimistic about how well the car reads and says nothing about detail. It is a
tool for "what is in the frame", never for "does the car read".

THE CONTROL, which it must both pass and fail
---------------------------------------------
R2-588 proved the emulation the other way round: `after` downscaled by its own
zoom correlates 0.98-1.00 with the centre of its own `before` and 0.10-0.21 with
a different frame's. `--selftest` re-derives that relation through THIS code
path: crop(before_F, z_F) must correlate high against the delivered after_F and
low against a different frame's after. A cropper with an off-by-one origin, the
wrong aspect, or a silent no-op would pass the first and, crucially, the no-op
would also fail the second -- both directions are asserted.
"""

import argparse
import os
import sys

import numpy as np
from PIL import Image

R2 = os.path.expanduser("~/f1-round2")
PEEP = os.path.join(R2, "docs/peep/r2581")

# the zooms R2-588 actually rendered, from variant A's focal at that frame
RENDERED = {2050: 1.9726, 2110: 2.0839, 2170: 1.7106, 2200: 1.6781}


def crop(img, z):
    """The centre 1/z x 1/z of `img`: exactly what a z-times-longer lens sees."""
    w, h = img.size
    cw, ch = w / z, h / z
    box = (round((w - cw) / 2), round((h - ch) / 2),
           round((w + cw) / 2), round((h + ch) / 2))
    return img.crop(box)


def gray(img, size):
    return np.asarray(img.convert("L").resize(size, Image.LANCZOS),
                      dtype=np.float64)


def corr(a, b):
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d else 0.0


def selftest():
    ok = True
    ref = (320, 180)                     # compare small; this is about framing
    for f, z in sorted(RENDERED.items()):
        before = Image.open(os.path.join(PEEP, f"r2581_before_{f}.png"))
        after = Image.open(os.path.join(PEEP, f"r2581_after_{f}.png"))
        mine = gray(crop(before, z), ref)
        theirs = gray(after, ref)
        same = corr(mine, theirs)
        other_f = 2170 if f != 2170 else 2050
        other = gray(Image.open(os.path.join(PEEP, f"r2581_after_{other_f}.png")),
                     ref)
        diff = corr(mine, other)
        good = same > 0.90 and abs(diff) < 0.60 and same - abs(diff) > 0.30
        ok &= good
        print(f"  {'PASS' if good else 'FAIL'}  f{f} z={z:.4f}  crop(before) vs "
              f"its OWN after {same:+.4f}   vs f{other_f}'s after {diff:+.4f}")

    # NEGATIVE: a cropper that does nothing must fail the same assertion.
    f, z = 2110, RENDERED[2110]
    before = Image.open(os.path.join(PEEP, f"r2581_before_{f}.png"))
    noop = corr(gray(before, ref), gray(Image.open(
        os.path.join(PEEP, f"r2581_after_{f}.png")), ref))
    good = noop < 0.90
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  negative/no-op  the UNCROPPED before "
          f"correlates {noop:+.4f} with the after; a cropper that silently did "
          f"nothing would have to score < 0.90 here and it does")

    print("SELFTEST " + ("PASS" if ok else "FAIL"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", type=int, default=2110)
    ap.add_argument("--zooms", default="1.3,1.5,1.7,1.94")
    ap.add_argument("--out", default="")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        okay = selftest()
        print(">> STAGE RESULT: "
              + ("CROPVIEW_SELFTEST_OK" if okay else "CROPVIEW_SELFTEST_FAILED"))
        return

    src = os.path.join(PEEP, f"r2581_before_{a.frame}.png")
    img = Image.open(src)
    out = a.out or os.path.join(R2, "tmp/r2581_retune")
    os.makedirs(out, exist_ok=True)
    for tok in a.zooms.split(","):
        z = float(tok)
        p = os.path.join(out, f"z{z:.2f}_{a.frame}.png")
        crop(img, z).resize(img.size, Image.LANCZOS).save(p)
        print(f"  z={z:.3f}  {p}")
    print(">> STAGE RESULT: CROPVIEW_OK")


if __name__ == "__main__":
    sys.exit(main())
