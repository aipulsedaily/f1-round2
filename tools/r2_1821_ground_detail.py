"""R2-1821: FINE-DETAIL SD on a rendered frame — the metric the client's complaint
was measured with (R2-1156), made reproducible and pointed at named regions.

    .venv/bin/python tools/r2_1821_ground_detail.py FRAME.png \
        [--regions REGIONS.json] [--vs OTHER.png] [--map OUT.png]
        [--profile x0,y0,x1,y1,w] [--json OUT.json] [--selftest]

THE METRIC
----------
R2-1156 measured the client's "blank grass no detail nothing" as the standard
deviation of FINE detail in 32 px tiles, in 8-bit levels.  Restated exactly:

    high pass   L - boxblur(L, 9)     everything finer than ~9 px survives.  9 px is
                chosen against the frame, not by habit: at f2760 the ground runs
                4-12 cm per delivered pixel, so 9 px is 0.4-1.1 m -- a tuft, a clump,
                a shadow.  Blur wider and the metric starts reading field boundaries;
                blur narrower and it reads the renderer's sampling noise.
    tile sd     sd of the high-passed luma inside each 32 x 32 tile, x 255.
    region      the MEDIAN tile sd over the region.  Median, not mean, because one
                fence post or one white line inside a grass box doubles a mean and
                the question is what the GROUND is doing.

WHY A SECOND NUMBER IS PUBLISHED WITH IT.  Fine-detail sd cannot tell "no vegetation"
from "vegetation smeared by motion blur", and this frame is a moving crane shot whose
foreground smears hard.  So every region also reports ANISOTROPY -- the ratio of
high-pass energy across the smear direction to along it.  Motion blur destroys detail
ALONG the smear and leaves it across; absent geometry destroys both.  A region that
is blank because nothing is there reads low sd at anisotropy ~1; a region that is
blank because it is smeared reads low sd at anisotropy well above 1.  Reporting the
first without the second is how a camera-speed problem gets fixed as a ground problem.

TWO CONTROLS, MANUFACTURED AT RUN TIME (R2-072), so neither expires when the defect
is fixed.  `--selftest` refuses to report if either fails:

  POSITIVE  a synthetic sward -- Poisson tufts at the measured screen cover on a flat
            olive ground -- must come back ABOVE the pit-building reference, or the
            metric cannot see cover it was built to see.
  NEGATIVE  the same ground with the tufts removed must come back near the renderer's
            own noise floor.  If it does not, the metric is reporting its blur kernel.
"""
import sys, json, argparse
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
HP_PX = 9
TILE = 32


def parse():
    p = argparse.ArgumentParser()
    p.add_argument("frame", nargs="?")
    p.add_argument("--vs", default=None, help="second frame, same camera, for A/B")
    p.add_argument("--regions", default=None, help="json {name: [x,y,w,h]}")
    p.add_argument("--map", default=None, help="write a tile-sd heat map here")
    p.add_argument("--profile", default=None,
                   help="x0,y0,x1,y1,width -- sample the tile map along a line, so a "
                        "density CLIFF and a density GRADIENT can be told apart")
    p.add_argument("--label", default="")
    p.add_argument("--json", default=None)
    p.add_argument("--selftest", action="store_true")
    return p.parse_args()


def luma(path):
    a = np.asarray(Image.open(path).convert("RGB"), np.float64) / 255.0
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def boxblur(a, k):
    def one(x, k):
        pad = k // 2
        c = np.cumsum(np.pad(x, ((0, 0), (pad + 1, pad)), mode="edge"), axis=1)
        return (c[:, k:] - c[:, :-k]) / float(k)
    out = a
    for _ in range(2):
        out = one(out, k)
        out = one(out.T, k).T
    return out


def tile_sd(L, hp=HP_PX, tile=TILE):
    """-> (ny, nx) map of fine-detail sd in 8-bit levels."""
    hi = L - boxblur(L, hp)
    ny, nx = L.shape[0] // tile, L.shape[1] // tile
    t = hi[:ny * tile, :nx * tile].reshape(ny, tile, nx, tile)
    return t.std(axis=(1, 3)) * 255.0


def anisotropy(L, box, hp=HP_PX):
    """|d/dx| vs |d/dy| of the high pass inside a box.  The smear at f2760 runs
    roughly horizontally in the lower frame, so ax/ay > 1 means detail survives
    ACROSS the smear -- i.e. the region is blurred, not empty."""
    x, y, w, h = box
    hi = (L - boxblur(L, hp))[y:y + h, x:x + w]
    ax = np.abs(np.diff(hi, axis=1)).mean()
    ay = np.abs(np.diff(hi, axis=0)).mean()
    return float(ay / max(ax, 1e-9))


def region_stat(L, S, box, tile=TILE):
    x, y, w, h = box
    j0, j1 = y // tile, max(y // tile + 1, (y + h) // tile)
    i0, i1 = x // tile, max(x // tile + 1, (x + w) // tile)
    sub = S[j0:j1, i0:i1].ravel()
    return dict(sd=float(np.median(sub)), sd_mean=float(sub.mean()),
                sd_p90=float(np.percentile(sub, 90)),
                tiles=int(sub.size), aniso=round(anisotropy(L, box), 3),
                box=[int(v) for v in box])


def synth(cover, seed=17, n=768):
    """A flat olive ground with Poisson tufts at `cover` screen fraction, rendered
    the way the sun renders them: a dark elongated shadow with a lit crown."""
    rng = np.random.default_rng(seed)
    L = np.full((n, n), 0.42) + rng.normal(0, 0.0025, (n, n))
    if cover > 0:
        r = 3.0
        k = int(cover * n * n / (np.pi * r * r * 4.5))
        ys = rng.integers(6, n - 6, k); xs = rng.integers(10, n - 10, k)
        yy, xx = np.mgrid[-6:7, -10:11]
        d = ((xx + 4) / 9.0) ** 2 + (yy / 3.0) ** 2           # the 4.5x shadow
        sh = np.clip(1.0 - d, 0, 1) * 0.16
        cr = np.clip(1.0 - (xx / 2.6) ** 2 - (yy / 2.6) ** 2, 0, 1) * 0.10
        for i in range(k):
            sl = (slice(ys[i] - 6, ys[i] + 7), slice(xs[i] - 10, xs[i] + 11))
            L[sl] -= sh
            L[sl] += cr
    return np.clip(L, 0, 1)


def selftest(ref):
    pos = tile_sd(synth(0.55))
    neg = tile_sd(synth(0.0))
    p, n = float(np.median(pos)), float(np.median(neg))
    ok_p = p > ref
    ok_n = n < 1.0
    print("  selftest POSITIVE synthetic sward @55%% cover: sd %.2f  (must exceed the"
          " %.2f reference)  %s" % (p, ref, "OK" if ok_p else "FAIL"))
    print("  selftest NEGATIVE same ground, tufts removed: sd %.2f  (must be < 1.00)"
          "  %s" % (n, "OK" if ok_n else "FAIL"))
    return ok_p and ok_n, dict(positive=round(p, 3), negative=round(n, 3),
                               ref=round(ref, 3), ok=bool(ok_p and ok_n))


DEFAULT_REGIONS = {
    # f2760, 3840 x 2160.  Every box is ground or reference; none straddles a boundary.
    "grass beside the pit building": [2600, 1500, 1150, 600],
    "grass, first 5 m off the road": [2180, 1180, 620, 210],
    "LEFT infield": [90, 570, 830, 190],
    "verge beside the track": [2180, 700, 620, 150],
    "treeline / scrub band": [1000, 300, 1900, 190],
    "pit buildings (reference)": [1750, 1180, 900, 330],
}


def main():
    a = parse()
    regions = json.load(open(a.regions)) if a.regions else DEFAULT_REGIONS
    frames = [("A", a.frame)] + ([("B", a.vs)] if a.vs else [])
    res = {}
    ref = None
    for tag, path in frames:
        L = luma(path)
        S = tile_sd(L)
        res[tag] = dict(path=path, shape=list(L.shape),
                        regions={k: region_stat(L, S, b) for k, b in regions.items()})
        if a.map:
            m = np.clip(S / 16.0, 0, 1)
            Image.fromarray((m * 255).astype(np.uint8)).resize(
                (S.shape[1] * 4, S.shape[0] * 4), Image.NEAREST).save(
                a.map if tag == "A" else a.map.replace(".png", "_B.png"))
        if a.profile:
            x0, y0, x1, y1, w = [float(v) for v in a.profile.split(",")]
            n = 40
            prof = []
            for i in range(n + 1):
                f = i / n
                px, py = x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
                b = [int(px - w / 2), int(py - w / 2), int(w), int(w)]
                b[0] = max(0, b[0]); b[1] = max(0, b[1])
                prof.append(round(region_stat(L, S, b)["sd"], 3))
            res[tag]["profile"] = prof
        ref = res[tag]["regions"].get("pit buildings (reference)", {}).get("sd", 10.0)

    print("== fine-detail sd, %d px tiles, 8-bit levels %s ==" % (TILE, a.label))
    hdr = "%-34s" % "region"
    for tag, path in frames:
        hdr += " %8s %7s" % (tag + " sd", "aniso")
    if len(frames) == 2:
        hdr += " %9s" % "delta"
    print(hdr)
    for k in regions:
        line = "%-34s" % k[:34]
        vals = []
        for tag, _ in frames:
            r = res[tag]["regions"][k]
            vals.append(r["sd"])
            line += " %8.2f %7.2f" % (r["sd"], r["aniso"])
        if len(vals) == 2:
            line += " %+8.1f%%" % (100.0 * (vals[1] / max(vals[0], 1e-9) - 1.0))
        print(line)
    if a.profile:
        for tag, _ in frames:
            print("profile %s: %s" % (tag, " ".join("%.1f" % v for v in res[tag]["profile"])))

    st_ok = True
    if a.selftest:
        st_ok, res["selftest"] = selftest(ref if ref else 10.0)
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)
    print(">> STAGE RESULT: %s" % ("R2_1821_DETAIL_OK" if st_ok else
                                   "R2_1821_DETAIL_INSTRUMENT_FAIL"))


if __name__ == "__main__":
    main()
