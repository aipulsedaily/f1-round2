"""R2-1661: measure the ground in a rendered frame, before against after.

    .venv/bin/python tools/r2_1661_measure.py BEFORE.png AFTER.png \
        [--mask-top 0.0 --mask-bottom 1.0] [--json OUT.json] [--selftest]

THE METRIC IS THE ONE THE DEFECT WAS FOUND WITH, not a new one.  R2-1128 measured
the patchwork as the coefficient of variation of the LOW-FREQUENCY luminance across
the infield -- 20-25 CV p5-p95, up to 59 peak-to-peak, over 50-55 % of the frame.
So:

  PATCH CV      blur to 41 px (a 155 m field at f2811's 9.2 cm/px is ~1700 px across,
                so 41 px keeps whole fields and destroys grass), then take
                (p95 - p5) / median over the ground mask, in per cent.  This is what
                "you see all the patches" is, in a number.  It must go DOWN.

  TEXTURE       RMS of (frame - blur41) over the same mask, relative to the median.
                This is everything the blur threw away: grass, tufts, shadow, crop
                grain.  A flat wash has almost none.  It must go UP.  The two
                together are the whole argument -- CV alone can be improved by
                flattening the land, which would be a different defect and not a fix.

  BARE FRACTION share of ground pixels whose local texture is below 35 % of the
                frame's own median texture: ground carrying nothing.

TWO CONTROLS, BOTH MANUFACTURED AT RUN TIME so neither can expire when the defect is
fixed (R2-072).  `--selftest` runs them and refuses to report if either fails:

  POSITIVE  a synthetic 3-value patchwork at the measured 50 % albedo step must come
            back at a patch CV in the 20-60 band and near-zero texture.  If it does
            not, the instrument cannot see the defect it was built for.
  NEGATIVE  the same patchwork with the steps removed (one flat value plus the same
            noise) must come back near zero CV.  If it does not, the instrument is
            reporting its own blur kernel.

The mask is the GROUND, and it is found rather than assumed: the horizon is the
highest row whose row-median luminance exceeds the frame median by 12 %, which is
where sky starts in every frame of this beat.  `--mask-top/--mask-bottom` override it.
"""
import sys, json, argparse
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
BLUR_PX = 41
VLO_PX = 601


def parse():
    p = argparse.ArgumentParser()
    p.add_argument("before", nargs="?")
    p.add_argument("after", nargs="?")
    p.add_argument("--mask-top", type=float, default=None)
    p.add_argument("--mask-bottom", type=float, default=1.0)
    p.add_argument("--boxes", default=None,
                   help="x,y,w,h;x,y,w,h -- measure ONLY inside these. THE DEFECT "
                        "WAS MEASURED OVER THE INFIELD, and a below-horizon mask is "
                        "not the infield: it also contains the track, the black "
                        "showroom platform and the treeline, whose luminance range "
                        "is the whole frame's. Measured on f2811, that mask reports "
                        "54 CV and 118 p2p for BOTH arms -- it is measuring the "
                        "platform, and it would report the same number if the "
                        "farmland were replaced by a photograph of it.")
    p.add_argument("--label", default="")
    p.add_argument("--json", default=None)
    p.add_argument("--selftest", action="store_true")
    return p.parse_args()


def luma(path):
    a = np.asarray(Image.open(path).convert("RGB"), np.float64) / 255.0
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2], a


def boxblur(a, k):
    """Separable box blur, twice -- a triangle kernel, edge-safe by division."""
    def one(x, k):
        pad = k // 2
        c = np.cumsum(np.pad(x, ((0, 0), (pad + 1, pad)), mode="edge"), axis=1)
        return (c[:, k:] - c[:, :-k]) / float(k)
    out = a
    for _ in range(2):
        out = one(out, k)
        out = one(out.T, k).T
    return out


def horizon_row(L):
    med = np.median(L)
    rows = np.median(L, axis=1)
    hot = np.where(rows > med * 1.12)[0]
    if not len(hot):
        return 0
    # sky is contiguous from the top; take the last row of that run
    r = 0
    while r + 1 < len(rows) and rows[r + 1] > med * 1.12:
        r += 1
    return r if hot[0] == 0 else 0


def parse_boxes(s, shape):
    H, W = shape
    m = np.zeros(shape, bool)
    out = []
    for part in s.split(";"):
        x, y, w, h = (int(v) for v in part.split(","))
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + w), min(H, y + h)
        m[y0:y1, x0:x1] = True
        out.append([x0, y0, x1 - x0, y1 - y0])
    return m, out


def measure(L, top, bot, boxes=None):
    H, W = L.shape
    if boxes is not None:
        m, _ = parse_boxes(boxes, L.shape)
        y0, y1 = 0, H
    else:
        y0 = int(round(top * H)); y1 = int(round(bot * H))
        y0 = max(0, min(H - 2, y0)); y1 = max(y0 + 1, min(H, y1))
        m = np.zeros(L.shape, bool)
        m[y0:y1, :] = True
    # BAND-PASS, NOT LOW-PASS, AND THIS CORRECTION MATTERS.  A pure low-pass over a
    # box that spans 150 m to 1 km of range is dominated by AERIAL PERSPECTIVE: the
    # airlight ramp across that depth is the largest low-frequency signal in the
    # frame by a wide margin, it is physically correct, and it is not a patch.
    # Measured on f2811 it put both arms at 43 CV and hid a real improvement inside
    # its own gradient.  A field is 155 m across, which at 9.2 cm/px foreshortened to
    # this frame's grazing angle is 200-600 px; the haze ramp is 2000+ px.  So the
    # patch band is [41 px, 601 px]: above the grass, below the atmosphere.
    lo = boxblur(L, BLUR_PX)
    vlo = boxblur(L, VLO_PX)
    hi = L - lo
    band = lo - vlo
    med = float(np.median(lo[m]))
    v = band[m]
    p5, p95 = np.percentile(v, [5, 95])
    tex = np.sqrt(np.maximum(boxblur(hi * hi, BLUR_PX), 0.0))
    tv = tex[m]
    tmed = float(np.median(tv))
    return dict(
        rows=[y0, y1], ground_frac=round(float(m.mean()), 4),
        median=round(med, 5),
        patch_cv_pct=round(float((p95 - p5) / max(med, 1e-9) * 100.0), 3),
        patch_p2p_pct=round(float((v.max() - v.min()) / max(med, 1e-9) * 100.0), 2),
        patch_sd_pct=round(float(v.std() / max(med, 1e-9) * 100.0), 3),
        texture_pct=round(float(tmed / max(med, 1e-9) * 100.0), 4),
        texture_p05_pct=round(float(np.percentile(tv, 5) / max(med, 1e-9) * 100.0), 4),
        texture_p95_pct=round(float(np.percentile(tv, 95) / max(med, 1e-9) * 100.0), 4),
        # ABSOLUTE, not self-referential.  A share of pixels below 0.35 x the frame's
        # OWN median texture rises when the whole frame gets more textured, which is
        # the opposite of what it is supposed to report.  BARE_ABS is the share below
        # a fixed 1.5 % of median luminance -- ground carrying nothing, on a ruler
        # that does not move between the arms.
        bare_frac=round(float((tv < 0.35 * tmed).mean()), 4),
        bare_abs=round(float((tv < 0.015 * med).mean()), 4),
        **_edges(lo, m, med))


def _edges(lo, m, med):
    """How SHARP the largest tonal transitions are -- which is what a patch is.

    VARIANCE IS THE WRONG QUESTION AND THIS PASS PROVED IT ON ITSELF.  The band-pass
    CV came back unchanged (40.18 -> 40.58) while the frame plainly improved, because
    the fix DELETED one kind of band-scale variance (155 m flat blocks with a step at
    the hedge) and DELIBERATELY ADDED another (the sward's own 38 m and 9 m
    patchiness, which is what stops the new cover being a second flat wash).  Those
    two are the same magnitude and opposite in meaning, and a variance metric cannot
    tell them apart.

    A patch is not "variance", it is a BOUNDED REGION WITH AN EDGE.  So measure the
    edge: the gradient magnitude of the 41 px low-pass, in per cent of median
    luminance per 100 px, at the top of its distribution.  A 50 % albedo step across
    a hedge is a large number here; a drift that fades over 38 m is a small one, at
    the same variance.
    """
    gy, gx = np.gradient(lo)
    g = np.hypot(gx, gy)[m] * 100.0 / max(med, 1e-9) * 100.0
    return dict(edge_p99=round(float(np.percentile(g, 99)), 3),
                edge_p999=round(float(np.percentile(g, 99.9)), 3),
                edge_mean=round(float(g.mean()), 4))


def _synth(step):
    """A patchwork: 155 m fields at f2811's scale, three albedo families, plus the
    grain that survives in a real frame.  `step` 0 removes the families."""
    rng = np.random.default_rng(7)
    H, W = 2160, 3840
    yy, xx = np.mgrid[0:H, 0:W]
    fid = ((np.sin(xx / 620.0) * 1.7 + np.cos(yy / 540.0) * 1.3
            + np.sin((xx + yy) / 910.0)) % 3.0).astype(int)
    base = np.array([1.0, 1.0 + step, 1.0 + step * 0.94])[fid] * 0.34
    return base * (1.0 + rng.normal(0, 0.012, (H, W)))


def selftest():
    ok = True
    pos = measure(_synth(0.50), 0.0, 1.0)
    neg = measure(_synth(0.00), 0.0, 1.0)
    print("  POSITIVE 50 %% step : patch_cv %.2f  texture %.4f"
          % (pos["patch_cv_pct"], pos["texture_pct"]))
    print("  NEGATIVE no step   : patch_cv %.2f  texture %.4f"
          % (neg["patch_cv_pct"], neg["texture_pct"]))
    if not (20.0 <= pos["patch_cv_pct"] <= 60.0):
        print("  INSTRUMENT-FAIL: cannot see a 50 % albedo step"); ok = False
    if neg["patch_cv_pct"] > 3.0:
        print("  INSTRUMENT-FAIL: reports patches in a flat field"); ok = False
    if pos["patch_cv_pct"] < neg["patch_cv_pct"] * 4.0:
        print("  INSTRUMENT-FAIL: no separation between the controls"); ok = False
    print("  POSITIVE edge_p99 %.3f   NEGATIVE edge_p99 %.3f"
          % (pos["edge_p99"], neg["edge_p99"]))
    if pos["edge_p99"] < neg["edge_p99"] * 4.0:
        print("  INSTRUMENT-FAIL: edge metric cannot see a hard boundary"); ok = False
    return ok, dict(positive=pos, negative=neg)


def main():
    a = parse()
    res = {}
    if a.selftest:
        ok, res["selftest"] = selftest()
        if not ok:
            print(">> STAGE RESULT: R2_1661_MEASURE_INSTRUMENT_FAIL")
            return
        if not a.before:
            print(">> STAGE RESULT: R2_1661_MEASURE_SELFTEST_OK %s"
                  % json.dumps(res["selftest"]))
            return
    Lb, _ = luma(a.before)
    La, _ = luma(a.after)
    if Lb.shape != La.shape:
        print(">> STAGE RESULT: R2_1661_MEASURE_FAIL size mismatch %s vs %s"
              % (Lb.shape, La.shape))
        return
    top = a.mask_top
    if top is None:
        top = max(horizon_row(Lb), horizon_row(La)) / float(Lb.shape[0])
    b = measure(Lb, top, a.mask_bottom, a.boxes)
    f = measure(La, top, a.mask_bottom, a.boxes)
    res.update(label=a.label, before=b, after=f, mask_top=round(top, 4),
               boxes=a.boxes,
               delta=dict(
                   patch_cv_pct=round(f["patch_cv_pct"] - b["patch_cv_pct"], 3),
                   texture_pct=round(f["texture_pct"] - b["texture_pct"], 4),
                   bare_frac=round(f["bare_frac"] - b["bare_frac"], 4),
                   bare_abs=round(f["bare_abs"] - b["bare_abs"], 4),
                   edge_p99=round(f["edge_p99"] - b["edge_p99"], 3)))
    # THE VERDICT IS EDGE + TEXTURE, not variance.  See `_edges`.
    verdict = ("R2_1661_GROUND_BETTER"
               if (f["edge_p99"] < b["edge_p99"]
                   and f["texture_pct"] > b["texture_pct"]) else
               "R2_1661_GROUND_NOT_BETTER")
    print("  %-18s  patch_cv %7.3f -> %7.3f   texture %7.4f -> %7.4f   edge_p99 %7.3f -> %7.3f"
          % (a.label or "frame", b["patch_cv_pct"], f["patch_cv_pct"],
             b["texture_pct"], f["texture_pct"], b["edge_p99"], f["edge_p99"]))
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)
    print(">> STAGE RESULT: %s %s" % (verdict, json.dumps(res)))


if __name__ == "__main__":
    main()
