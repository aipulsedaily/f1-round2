#!/usr/bin/env python3
"""r2881_seat_measure.py -- the seat A/B, measured, with its null and its control.

    .venv/bin/python tools/r2881_seat_measure.py \
        --before render/r2881/seat_f2635_BEFORE.png \
        --after  render/r2881_seat/seat_f2635_AFTER.png \
        --null   render/r2881_seat/seat_f2635_NULL.png \
        --mask   work/r2881_seat/windows_mask.npz \
        --out    work/r2881_seat/seat_ab.json

WHAT IS MEASURED, AND WHY EACH ONE
----------------------------------
1.  BAND-PASSED p-p OF LOG LUMINANCE, PER OCTAVE.  A difference of Gaussians,
    p-p taken between the 1st and 99th percentile so one specular hit cannot set
    a band.  LOG, not linear: R2-060 measured paint-on-curvature leaking 40.9x
    more into a linear band-pass than into a log one, and this surface is a
    curved bowl in a dark cockpit, which is exactly that case.  Directly
    comparable to `itemkit.RELIEF_BANDS`, whose numbers are peak-to-peak
    radiance modulation.

    THE FINE BAND IS THE HEADLINE: sigma 1-2 px and 2-4 px are the octaves a
    5.0 mm weave (7.1 px) and a 2.2 mm nap (3.1 px) live in.  A material that is
    flat has power in the coarse octaves — that is form, the shape of the seat —
    and nothing in the fine ones.

2.  THE NULL.  The AFTER scene rendered a second time.  Cycles is stochastic and
    OpenImageDenoise is not idempotent, so two renders of one scene do not match.
    A difference is only evidence if it is bigger than that floor.

3.  THE NEGATIVE CONTROL.  `LiveryPaint`, 33.7 % of this crop, which R2-881 does
    not touch.  If the control moves by more than the null then the difference on
    the seat is not the change.

THE MASK IS ERODED BEFORE IT IS READ.  `tools/r2881_seat_window.py` rasterises
which material owns each pixel by raycasting the camera, on a 4 px lattice.  The
DoG ladder's widest kernel here is sigma 8, so the mask is eroded by 24 px — 3
sigma — and every band value reported is therefore a function of same-material
pixels only.  Nothing is measured across a silhouette.
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

#: DoG ladder.  sigma 1->2 px is where the nap sits, 2->4 px the weave.
SIGMAS = (1.0, 2.0, 4.0, 8.0, 16.0)
ERODE_PX = 24


def read_lum(path):
    """Linear-light luminance.  Undoes the sRGB EOTF only — NOT AgX.

    Every arm carries the identical transform, so a monotone curve common to all
    three cancels in every comparison made here.  Inverting AgX badly would not
    cancel and would import its own error.
    """
    a = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64) / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722


def octave_pp(lg, mask):
    """Band-passed p-p of log luminance per octave, over `mask` only."""
    out = []
    prev = ndimage.gaussian_filter(lg, SIGMAS[0])
    for k in range(len(SIGMAS) - 1):
        nxt = ndimage.gaussian_filter(lg, SIGMAS[k + 1])
        band = (prev - nxt)[mask]
        lo, hi = np.percentile(band, [1.0, 99.0])
        out.append(dict(band="%.0f-%.0f px" % (SIGMAS[k], SIGMAS[k + 1]),
                        sigma_lo=SIGMAS[k], sigma_hi=SIGMAS[k + 1],
                        pp=float(hi - lo), rms=float(band.std())))
        prev = nxt
    return out


def peakiness(g):
    """How much of the structure sits in DISCRETE spectral peaks — i.e. is this
    a REPEAT (a weave) or just broadband noise?  Hann-windowed, DC and the two
    lowest rings blocked so a shadow gradient is not counted as the biggest
    'peak' in the picture."""
    g = g - g.mean()
    wy = np.hanning(g.shape[0])[:, None]
    wx = np.hanning(g.shape[1])[None, :]
    P = np.abs(np.fft.fftshift(np.fft.fft2(g * wy * wx))) ** 2
    cy, cx = P.shape[0] // 2, P.shape[1] // 2
    Y, X = np.mgrid[:P.shape[0], :P.shape[1]]
    fy = (Y - cy) / P.shape[0]
    fx = (X - cx) / P.shape[1]
    rad = np.sqrt(fy ** 2 + fx ** 2)
    keep = (rad > 0.010) & (rad < 0.45)
    Pk = np.where(keep, P, 0.0)
    i = int(np.argmax(Pk))
    py, px = np.unravel_index(i, P.shape)
    return dict(peakiness=float(Pk.flat[i] / max(np.median(P[keep]), 1e-30)),
                period_px=float(1.0 / max(rad[py, px], 1e-9)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--null", required=True)
    ap.add_argument("--mask", required=True)
    ap.add_argument("--px-per-m", type=float, default=1416.4)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    ims = {}
    for nm, p in (("before", a.before), ("after", a.after), ("null", a.null)):
        ims[nm] = read_lum(p)
    shp = {nm: im.shape for nm, im in ims.items()}
    if len(set(shp.values())) != 1:
        raise SystemExit("arms are different sizes: %s" % shp)
    H, W = ims["before"].shape

    z = np.load(a.mask, allow_pickle=True)
    lab, step = z["labels"], int(z["step"])
    names = [str(x) for x in z["names"]]
    full = np.kron(lab, np.ones((step, step), dtype=lab.dtype))[:H, :W]
    if full.shape != (H, W):
        pad = np.zeros((H, W), dtype=lab.dtype)
        pad[:full.shape[0], :full.shape[1]] = full
        full = pad

    logs = {nm: np.log(np.maximum(im, 1e-6)) for nm, im in ims.items()}
    res = {"px_per_m": a.px_per_m, "shape": [H, W], "sigmas": list(SIGMAS),
           "erode_px": ERODE_PX, "regions": {}}

    print("seat A/B at frame 2635, %dx%d crop, %.1f px/m" % (W, H, a.px_per_m))
    print("mask eroded by %d px (3 sigma of the widest DoG kernel)" % ERODE_PX)
    for k, nm in enumerate(names):
        m = (full == k + 1)
        me = ndimage.binary_erosion(m, np.ones((3, 3), bool), iterations=ERODE_PX // 2)
        n = int(me.sum())
        if n < 4000:
            print("  %-14s only %d px survive erosion — SKIPPED" % (nm, n))
            continue
        row = {"px": n, "raw_px": int(m.sum())}
        for arm in ("before", "after", "null"):
            row[arm] = dict(mean=float(ims[arm][me].mean()),
                            std=float(ims[arm][me].std()),
                            octaves=octave_pp(logs[arm], me))
        ys, xs = np.where(me)
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        for arm in ("before", "after"):
            row[arm]["peak"] = peakiness(logs[arm][y0:y1 + 1, x0:x1 + 1])
        res["regions"][nm] = row

        print("\n  %s  (%d px after erosion, %d before)" % (nm.upper(), n, m.sum()))
        print("    %-10s %10s %10s %10s %10s %10s"
              % ("band", "BEFORE", "AFTER", "NULL", "A-B", "A/B"))
        for i in range(len(SIGMAS) - 1):
            b = row["before"]["octaves"][i]["pp"]
            af = row["after"]["octaves"][i]["pp"]
            nu = row["null"]["octaves"][i]["pp"]
            print("    %-10s %10.4f %10.4f %10.4f %10.4f %9.2fx"
                  % (row["before"]["octaves"][i]["band"], b, af, nu,
                     af - b, af / max(b, 1e-9)))
        print("    mean lum   %10.5f %10.5f %10.5f"
              % (row["before"]["mean"], row["after"]["mean"], row["null"]["mean"]))

    # the null floor and the control, stated as one line each
    print("\nNULL FLOOR (after vs a second render of after) and CONTROL:")
    for nm, row in res["regions"].items():
        d_null = [abs(row["null"]["octaves"][i]["pp"] - row["after"]["octaves"][i]["pp"])
                  for i in range(len(SIGMAS) - 1)]
        d_ab = [abs(row["after"]["octaves"][i]["pp"] - row["before"]["octaves"][i]["pp"])
                for i in range(len(SIGMAS) - 1)]
        ratio = [d_ab[i] / max(d_null[i], 1e-9) for i in range(len(d_ab))]
        row["null_floor_pp"] = d_null
        row["ab_delta_pp"] = d_ab
        row["signal_over_null"] = ratio
        print("  %-14s fine band |A-B| %.4f vs null %.4f  = %6.1fx the floor"
              % (nm, d_ab[0], d_null[0], ratio[0]))

    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        json.dump(res, open(a.out, "w"), indent=1)
        print("\nwrote %s" % a.out)
    print(">> STAGE RESULT: R2881_MEASURE_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
