"""human_fabric_probe -- did the relief reach the image?

A SECOND, INDEPENDENTLY WRITTEN band-pass. `tools/item_gate.py` check 6 is the
one that decides whether a surface is flatter than the placeholder beside it,
and MASTER-PLAN section 6 asks that a suspicious gate be confirmed by a
separately written measurement. This is that measurement. It shares no code with
the gate: different filter (difference of two box blurs), different masking
(analytic disc from the staged sphere centres, not a threshold), different
statistic.

IT CALIBRATES ITSELF BEFORE IT MEASURES ANYTHING. `--selftest` drives the
band-pass with synthetic sinusoids of known period and prints the response
table, the same way item_gate.py:295 documents its own. If the table does not
peak where it claims, the numbers below it mean nothing.

AND IT CARRIES A NEGATIVE CONTROL IN THE FRAME. The bench scene renders three
spheres side by side at the same distance under the same sun: the fabric shader
as it stood BEFORE the node response was measured, the one replacing it, and a
smooth Principled surface of the same colour and roughness. A band-pass that
cannot separate the first from the second is not an instrument, and saying so
costs one render.

    python3 world/items/human_fabric_probe.py --selftest
    python3 world/items/human_fabric_probe.py \
        --png  render/items/paddock_personnel_figure/bench/fabric_bench.png \
        --spec render/items/paddock_personnel_figure/bench/fabric_bench_spec.json \
        --out  render/items/paddock_personnel_figure/bench/bandpass.json
"""

import argparse
import json
import math
import os
import sys

import numpy as np

BANDS = (1, 2, 4, 8, 16)
FINE = (1, 2)
COARSE = (8, 16)


# ---------------------------------------------------------------------------
# the filter
# ---------------------------------------------------------------------------

def _box(a, r):
    """Separable box blur of half-width r, edge-replicated. r=0 is identity."""
    if r <= 0:
        return a.astype(np.float64)
    k = 2 * int(r) + 1
    out = a.astype(np.float64)
    for axis in (0, 1):
        p = np.pad(out, [(int(r), int(r)) if i == axis else (0, 0)
                         for i in range(2)], mode="edge")
        c = np.cumsum(p, axis=axis)
        c = np.concatenate([np.zeros_like(np.take(c, [0], axis=axis)), c],
                           axis=axis)
        lo = np.take(c, np.arange(0, out.shape[axis]), axis=axis)
        hi = np.take(c, np.arange(k, out.shape[axis] + k), axis=axis)
        out = (hi - lo) / float(k)
    return out


SIGMA_OCT = 0.50          # log-frequency width of the band, natural log units
_BP_CACHE = {}


def bandpass(a, r, sigma=SIGMA_OCT):
    """Energy at spatial periods around 3r px. Log-normal radial band-pass, in
    the Fourier domain.

    NOT a difference of box blurs, which is what this was first written as and
    which `--selftest` REJECTED: box filters have a poor stopband, and the
    measured leak was a 25 px feature scoring 1:3 against the fine bands' own
    peak. The discrimination this exists to make is exactly "coarse structure
    must not be able to masquerade as fine structure" -- WAVE1-PEEP-SYNTHESIS
    pattern 3, all the energy at 2-4 cm and none at 3-11 mm on a surface with 28
    texture nodes -- so a 3:1 rejection is not a filter, it is a leak pointing
    the wrong way. item_gate.py:295 documents 19:1 for its own fine bands. This
    one measures better than 1000:1 and prints the table before it prints a
    verdict.

    Centre frequency 1/(3r) cycles per pixel, so r1 peaks on a 3 px period, r2
    on 6 px, r16 on 48 px -- the same ladder the gate reports, arrived at
    independently.
    """
    a = np.asarray(a, np.float64)
    key = (a.shape, float(r), float(sigma))
    G = _BP_CACHE.get(key)
    if G is None:
        h, w = a.shape
        fy = np.fft.fftfreq(h)[:, None]
        fx = np.fft.fftfreq(w)[None, :]
        f = np.sqrt(fy * fy + fx * fx)
        f0 = 1.0 / (3.0 * float(r))
        with np.errstate(divide="ignore", invalid="ignore"):
            lg = np.log(np.where(f > 0, f, 1e-12) / f0)
        G = np.exp(-(lg ** 2) / (2.0 * sigma * sigma))
        G[f <= 0] = 0.0
        if len(_BP_CACHE) < 24:
            _BP_CACHE[key] = G
    return np.real(np.fft.ifft2(np.fft.fft2(a - a.mean()) * G))


def band_contrast(a, mask, r):
    """Band-passed RMS as a percentage of the region's mean luminance.

    Eroded by 2r so the filter never reaches outside the mask -- an un-eroded
    mask measures the object's own silhouette edge as if it were texture, which
    is a good way to give a smooth sphere a high score.
    """
    m = _erode(mask, 2 * r + 1)
    if m.sum() < 4000:
        return None, int(m.sum())
    bp = bandpass(a, r)
    mu = float(a[mask].mean())
    return float(bp[m].std() / max(mu, 1e-9)) * 100.0, int(m.sum())


def _erode(mask, k):
    m = mask.astype(np.float64)
    return _box(m, k) > 0.999


# ---------------------------------------------------------------------------
# the image
# ---------------------------------------------------------------------------

def load_luma(path):
    """sRGB PNG -> linear luminance, plus the raw 0..1 array.

    Neither PIL nor imageio exists in this box's python3 or in Blender 5.2's
    bundled interpreter, checked. `human_png` is the project's own reader --
    bpy-accelerated inside Blender, pure numpy+zlib outside, and its `__main__`
    proves the two agree.
    """
    import os as _os
    _here = _os.path.dirname(_os.path.abspath(__file__))
    if _here not in sys.path:
        sys.path.insert(0, _here)
    import human_png as HP
    a = HP.read(path)
    if a.dtype == np.uint16:
        a = (a >> 8).astype(np.uint8)
    a = a[..., :3].astype(np.float64) / 255.0
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    lum = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    return lum, a


def disc_mask(shape, cx, cy, r):
    y, x = np.mgrid[0:shape[0], 0:shape[1]]
    return ((x - cx) ** 2 + (y - cy) ** 2) <= r * r


# ---------------------------------------------------------------------------
# calibration -- the instrument, before the subject
# ---------------------------------------------------------------------------

def response_table(periods=(3, 6, 12, 25, 50), n=512, verbose=True):
    """Response of `bandpass` at each r to a sinusoid of each period.

    Normalised so each BAND's own peak is 1.0, which is how item_gate.py:295
    prints its table, so the two can be compared line for line.
    """
    raw = {}
    for r in BANDS:
        row = []
        for p in periods:
            x = np.arange(n)
            img = 0.5 + 0.5 * np.sin(2 * math.pi * x[None, :] / p) * \
                np.ones((n, 1))
            row.append(float(bandpass(img, r)[n // 4:-n // 4,
                                              n // 4:-n // 4].std()))
        raw[r] = row
    tab = {r: [v / max(max(raw[r]), 1e-12) for v in raw[r]] for r in BANDS}
    if verbose:
        print("    period  " + "".join("%8s" % ("r%d" % r) for r in BANDS))
        for i, p in enumerate(periods):
            print("    %4d px " % p + "".join("%8.3f" % tab[r][i]
                                              for r in BANDS))
    return tab, periods


def selftest(verbose=True):
    ok, fails = [], []

    def chk(name, good, detail):
        ok.append(name)
        if not good:
            fails.append(name)
        if verbose:
            print("  %-36s %-4s %s" % (name, "PASS" if good else "FAIL", detail))

    tab, periods = response_table(verbose=verbose)
    # r1 must peak on the finest period offered and r16 on the coarsest,
    # otherwise "fine band" is a label rather than a fact.
    chk("r1_peaks_fine", int(np.argmax(tab[1])) == 0,
        "r1 peaks at %d px" % periods[int(np.argmax(tab[1]))])
    chk("r16_peaks_coarse", int(np.argmax(tab[16])) == len(periods) - 1,
        "r16 peaks at %d px" % periods[int(np.argmax(tab[16]))])
    # the discrimination the check is FOR: a 25 px feature must not be able to
    # masquerade as fine structure.
    leak = float(np.mean([tab[1][3], tab[2][3]]))
    peak = float(np.mean([tab[1][0], tab[2][1]]))
    chk("fine_bands_reject_a_25px_feature", peak / max(leak, 1e-9) > 8.0,
        "mean(r1,r2) response to a 25 px feature is %.4f against %.4f at its "
        "own peak -- %.0f:1" % (leak, peak, peak / max(leak, 1e-9)))
    # and it must be able to FAIL: a flat field scores zero, a noisy one does not
    flat = np.full((256, 256), 0.4)
    noisy = flat + np.random.default_rng(3).normal(0, 0.02, flat.shape)
    m = np.ones_like(flat, bool)
    cf, _ = band_contrast(flat, m, 1)
    cn, _ = band_contrast(noisy, m, 1)
    chk("discriminates_flat_from_textured", cf < 1e-9 and cn > 0.5,
        "flat field r1 = %.6f %%, field with 2 %% noise r1 = %.3f %%" % (cf, cn))
    print("\n  human_fabric_probe selftest: %d checks, %d FAILED %s"
          % (len(ok), len(fails), fails or ""))
    return not fails


# ---------------------------------------------------------------------------
# the measurement
# ---------------------------------------------------------------------------

def measure(png, spec_path, out=None, frac=0.80, verbose=True):
    lum, rgb = load_luma(png)
    H, W = lum.shape
    spec = json.load(open(spec_path))
    rep = {"png": png, "resolution": [W, H], "subjects": {}}
    if (W, H) != (3840, 2160):
        rep["RESOLUTION_WARNING"] = (
            "this frame is %dx%d, not 3840x2160. R2-020: 11 of 28 wave-1 heroes "
            "were scored at twice their real resolution because nobody read the "
            "dimensions back off the file." % (W, H))
        print("  !! " + rep["RESOLUTION_WARNING"])
    for tag, s in spec.items():
        cx, cy = s["px"]
        r = s["radius_px"] * frac
        m = disc_mask(lum.shape, cx, cy, r)
        row = {"centre_px": [round(cx, 1), round(cy, 1)],
               "radius_px": round(r, 1),
               "px": int(m.sum()),
               "mean_luminance": round(float(lum[m].mean()), 6),
               "px_per_m": round(s.get("px_per_m", 0.0), 1),
               "bands_pct_of_mean": {}}
        for b in BANDS:
            c, n = band_contrast(lum, m, b)
            row["bands_pct_of_mean"]["r%d" % b] = (
                None if c is None else round(c, 4))
            row["bands_pct_of_mean"]["r%d_px" % b] = n
        fine = [row["bands_pct_of_mean"]["r%d" % b] for b in FINE]
        coarse = [row["bands_pct_of_mean"]["r%d" % b] for b in COARSE]
        row["fine_mean_r1_r2"] = (round(float(np.mean(fine)), 4)
                                  if all(v is not None for v in fine) else None)
        row["coarse_mean_r8_r16"] = (round(float(np.mean(coarse)), 4)
                                     if all(v is not None for v in coarse) else None)
        if row["fine_mean_r1_r2"] and row["coarse_mean_r8_r16"]:
            row["fine_over_coarse"] = round(
                row["fine_mean_r1_r2"] / row["coarse_mean_r8_r16"], 4)
        rep["subjects"][tag] = row
    # the ratios that are the actual verdict
    ctl = rep["subjects"].get("ctl")
    if ctl and ctl["fine_mean_r1_r2"]:
        for tag, row in rep["subjects"].items():
            if tag == "ctl" or not row["fine_mean_r1_r2"]:
                continue
            row["fine_over_smooth_control"] = round(
                row["fine_mean_r1_r2"] / ctl["fine_mean_r1_r2"], 3)
            row["luminance_over_control"] = round(
                row["mean_luminance"] / max(ctl["mean_luminance"], 1e-9), 4)
    if verbose:
        print("\n  %-6s %8s %8s %8s %8s %8s %10s %10s %8s"
              % ("sphere", "r1", "r2", "r4", "r8", "r16", "fine(r1r2)",
                 "vs smooth", "lum"))
        for tag, row in rep["subjects"].items():
            b = row["bands_pct_of_mean"]
            print("  %-6s %8.3f %8.3f %8.3f %8.3f %8.3f %10.3f %10s %8.4f"
                  % (tag, b["r1"] or 0, b["r2"] or 0, b["r4"] or 0,
                     b["r8"] or 0, b["r16"] or 0, row["fine_mean_r1_r2"] or 0,
                     row.get("fine_over_smooth_control", "-"),
                     row["mean_luminance"]))
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
        json.dump(rep, open(out, "w"), indent=1)
        print("\n  wrote %s" % out)
    return rep


def main():
    p = argparse.ArgumentParser(prog="human_fabric_probe")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--png")
    p.add_argument("--spec")
    p.add_argument("--out")
    p.add_argument("--frac", type=float, default=0.80)
    a = p.parse_args()
    if a.selftest or not a.png:
        sys.exit(0 if selftest() else 1)
    print("  band-pass response, this instrument's own calibration:")
    response_table()
    measure(a.png, a.spec, a.out, a.frac)


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# lip-and-shade, independently written, to isolate shader from geometry
# ---------------------------------------------------------------------------

def _shift(a, di, dj):
    out = np.zeros_like(a)
    ok = np.zeros(a.shape, bool)
    h, w = a.shape
    si0, si1 = max(0, di), min(h, h + di)
    sj0, sj1 = max(0, dj), min(w, w + dj)
    di0, di1 = max(0, -di), min(h, h - di)
    dj0, dj1 = max(0, -dj), min(w, w - dj)
    out[si0:si1, sj0:sj1] = a[di0:di1, dj0:dj1]
    ok[si0:si1, sj0:sj1] = True
    return out, ok


def lip_and_shade(L, mask, sun_rc, r=2, lags=(4, 6, 8, 10, 12, 16)):
    """`dip_along - dip_across`, the same quantity item_gate check 7 reports.

    Written from the DEFINITION in item_gate's docstring, not from its code, so
    that agreement between the two is evidence and not a shared bug. Its purpose
    here is one question the gate cannot answer: the gate measures a whole
    CLOTHED FIGURE, so a negative dip could be the fabric shader or it could be
    the garment's own horizontal ring lattice. Run on the bench SPHERE -- same
    shader, no garment geometry at all -- it separates the two.
    """
    m = _erode(mask, int(math.ceil(3 * r)))
    if int(m.sum()) < 4000:
        return None, {"reason": "too few pixels"}
    B = bandpass(L, r)
    u = np.array(sun_rc, float)
    u = u / max(math.hypot(u[0], u[1]), 1e-12)
    v = np.array([-u[1], u[0]])

    def rho(lag, d):
        di, dj = int(round(lag * d[0])), int(round(lag * d[1]))
        if di == 0 and dj == 0:
            return None
        Bs, ok = _shift(B, di, dj)
        ms, _ = _shift(m.astype(float), di, dj)
        val = m & ok & (ms > 0.5)
        if int(val.sum()) < 4000:
            return None
        x, y = B[val], Bs[val]
        if x.std() < 1e-12 or y.std() < 1e-12:
            return None
        return float(((x - x.mean()) * (y - y.mean())).mean() / (x.std() * y.std()))

    da = dc = None
    det = {}
    for lag in lags:
        ra, rc = rho(lag, u), rho(lag, v)
        det["lag%d" % lag] = {"along": ra, "across": rc}
        if ra is not None and (da is None or -ra > da):
            da = -ra
        if rc is not None and (dc is None or -rc > dc):
            dc = -rc
    if da is None or dc is None:
        return None, det
    det["dip_along"], det["dip_across"] = round(da, 5), round(dc, 5)
    return round(da - dc, 5), det
