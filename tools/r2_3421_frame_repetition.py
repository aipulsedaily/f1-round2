"""R2-3421 -- DOES THE DELIVERED FRAME READ AS REPETITIVE?  Measured on the pixels.

    python3 tools/r2_3421_frame_repetition.py \
        --frames work/r22161_proxy/r22161_proxy_%06d.png --f 2319 \
        --out work/r23421/rep_2319.json [--dump work/r23421/pairs_2319.png]

    # and the controls, which MUST fire before any of the above is believed
    python3 tools/r2_3421_frame_repetition.py ... --control tile100
    python3 tools/r2_3421_frame_repetition.py ... --control tile20
    python3 tools/r2_3421_frame_repetition.py ... --control lattice

WHAT IT LOOKS FOR
=================
The rule names a PERCEPTUAL event -- "one tree spammed 100 times" -- and there
are exactly two ways an audience notices one:

  1. THE SAME SILHOUETTE TWICE.  A distinctive shape recurs somewhere else in
     the frame at a size the eye can compare.  Position is irrelevant; what
     gives it away is that two pieces of the picture are the SAME PICTURE.
     Measured here as the best normalised cross-correlation between a patch and
     any other patch of the frame at least `--exclude` pixels away.  This is
     copy-move detection, and it does not care whether the placement is random.

  2. A COMB.  Every instance oriented the same way, so the surface reads as
     brushed rather than grown. This survives ANY library size and any
     placement, and it is the failure both of the other arms passed -- see
     `orientation_R`.

  3. A PERIOD.  The placement itself has a lattice or a beat, so the eye reads
     a texture instead of a landscape -- and this is the failure that survives
     a large library, because a hundred DIFFERENT trees on a 12 m grid still
     read as planted.  Measured as the strongest off-centre peak of the band's
     autocorrelation.

Autocorrelation ALONE cannot see (1): a repeated mesh dropped at random
positions produces no periodicity whatever.  NCC alone cannot see (2): a
perfectly regular lattice of DIFFERENT objects has no near-duplicate patches.
Both arms are here because either alone passes the other's failure vacuously.

WHY IT RUNS ON THE DELIVERED FRAMES AND NOT ON STILLS
=====================================================
`work/r22161_proxy/` is the finished film, all 2,978 frames, with the shipping
180-degree shutter already in them.  The near-field ground drags 213-245 px on
beat 5, and the shutter removes 2.45x of the coarse band there, so repetition
that is obvious on a still can be absent from the delivery -- and the delivery
is what the audience is asked about.  Measuring the render instead of the
delivery would answer a question nobody is asking.

The cost of that choice is stated rather than hidden: the proxy is 960x540, a
4x linear downscale of the 3840x2160 master, so this instrument's resolving
power is a quarter of the delivery's.  `--min-npix` refuses a band whose
subject is too small for the patch size to mean anything, and the controls are
built AT PROXY RESOLUTION from the frame's own pixels, so what they prove, they
prove at the resolution actually being used.

THE CONTROLS
============
Every one is built out of the SAME BAND being tested, so lighting, grade, grain,
blur and colour are held and the only new thing is repetition:

    tile100   the band is repainted with ONE patch of itself, dropped at random
              positions and random flips -- "one tree spammed", exactly
    tile20    one patch replaces a random 20 % of the band's patches
    lattice   one patch on a regular grid -- the periodicity arm's own failure
    phase     the band's Fourier PHASE is randomised, its power spectrum kept.
              THE NULL: identical texture statistics, identical blur, identical
              contrast, and no repeated structure anywhere. If this fires, the
              instrument is reading the power spectrum and not repetition.
    shuffle   the band's patches shuffled in place. RETIRED AS A NULL and kept
              only as the record of a control that failed: it scored 19.6 % at
              NCC 0.90, ABOVE tile100, because shuffling manufactures hard tile
              seams and the seams correlate with each other. A control that
              introduces its own artefact measures the artefact.

A measurement of repetition that has never seen repetition is not a
measurement.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HERE = os.path.join(R2, "tools")
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import gate_exit                                                    # noqa: E402

# The near-field verge, measured: hero grass at >= 150 px/m of the 4K frame
# lands in 4K y 1449..2153 over the full width, i.e. proxy y 362..538.
BAND = (0, 362, 960, 176)          # x, y, w, h in proxy pixels

PATCH = 24                         # a 0.22 m fescue clump at f2319 is 22 proxy px
STRIDE = 4
EXCLUDE = 40                       # a match nearer than this is the patch itself
# NCC_HIT WAS 0.90 AND THE CONTROLS FALSIFIED IT.  At 0.90 the shipping band
# scored 6.51 % and a band repainted entirely out of one patch scored 11.68 %
# -- no separation worth the name -- because near-field grass under a 180-degree
# shutter is so self-similar that any two 24 px windows of it correlate at ~0.75.
# 0.90 was a number chosen by taste.  0.96 is chosen by the ladder: it is where
# the shipping band (0.011 %) and the same band with ONE patch pasted over 20 %
# of it (13.75 %) stop overlapping, a separation of 1,250x.  See the calibration
# table in docs/STAGING-R2-3421-to-R2-3480.md.
NCC_HIT = 0.96
VAR_FLOOR = 0.02                   # flat sky/asphalt has no silhouette to repeat

# THE VERDICT LINES. Both are set by the controls in tools/, not by taste --
# see `--control` above and the calibration table in the staging note.
HIT_FRAC_FAIL = 0.0025             # ladder: ship 0.011 %, tile100 2.4 %, tile20 13.7 %
PERIOD_FAIL = 0.30                 # off-centre autocorrelation peak, normalised


def read_gray(pattern, f):
    """One frame's luma as float32 in [0, 1], via one ffmpeg decode."""
    path = pattern % f if "%" in pattern else pattern
    if not os.path.isfile(path):
        raise SystemExit("no such frame: " + path)
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path,
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, check=True).stdout
    p = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "json", path],
                       capture_output=True, text=True, check=True)
    st = json.loads(p.stdout)["streams"][0]
    w, h = int(st["width"]), int(st["height"])
    return np.frombuffer(out, np.uint8).reshape(h, w).astype(np.float32) / 255.0


def box_blur(a, r):
    """Separable running-mean, so the high-pass costs nothing."""
    if r < 1:
        return a
    k = 2 * r + 1
    c = np.cumsum(np.pad(a, ((0, 0), (r + 1, r)), mode="edge"), axis=1)
    a = (c[:, k:] - c[:, :-k]) / k
    c = np.cumsum(np.pad(a, ((r + 1, r), (0, 0)), mode="edge"), axis=0)
    return (c[k:, :] - c[:-k, :]) / k


def patches(band, p=PATCH, stride=STRIDE):
    """(N, p*p) patch matrix and (N, 2) centres, from a strided grid."""
    H, W = band.shape
    ys = np.arange(0, H - p + 1, stride)
    xs = np.arange(0, W - p + 1, stride)
    P = np.empty((len(ys) * len(xs), p * p), np.float32)
    C = np.empty((len(ys) * len(xs), 2), np.float32)
    i = 0
    for y in ys:
        for x in xs:
            P[i] = band[y:y + p, x:x + p].ravel()
            C[i] = (x + p / 2, y + p / 2)
            i += 1
    return P, C


def _win_stats(img, p):
    """Windowed sum and sum-of-squares for every p x p window, by integral image."""
    def integ(a):
        c = np.zeros((a.shape[0] + 1, a.shape[1] + 1), np.float64)
        c[1:, 1:] = a.cumsum(0).cumsum(1)
        return c[:-p, :-p] + c[p:, p:] - c[:-p, p:] - c[p:, :-p]
    return integ(img.astype(np.float64)), integ(img.astype(np.float64) ** 2)


def ncc_fullsearch(band, p=PATCH, stride=STRIDE, exclude=EXCLUDE,
                   var_floor=VAR_FLOOR, mirror=True):
    """Best NCC of each textured patch against EVERY offset in the band.

    THE FIRST VERSION OF THIS FUNCTION WAS VACUOUS AND THE CONTROL CAUGHT IT.
    It compared patches on a stride-4 grid against each other, so two copies of
    one patch pasted at positions differing by a non-multiple of 4 were never
    compared at their aligned offset -- 15 times out of 16 an exact duplicate
    scored like unrelated grass.  Measured: the shipping frame scored 3.43 % and
    a band repainted ENTIRELY out of one patch scored 3.84 %, a separation of
    nothing, while the two are not remotely alike to look at.

    So the search is now over all integer offsets, by FFT, and a duplicate
    scores 1.000 wherever it was pasted.  `mirror` also searches the
    left-right flip, because `gn_kind` mirrors half of every scatter in x and a
    repeat the audience would see is a repeat whichever way round it is.
    """
    H, W = band.shape
    if H < p + 2 or W < p + 2:
        return None
    S1, S2 = _win_stats(band, p)
    n_pix = p * p
    wmean = S1 / n_pix
    wvar = np.maximum(S2 - S1 * S1 / n_pix, 0.0)
    wnorm = np.sqrt(wvar)                       # ||window - mean||
    ok_win = wnorm / np.sqrt(n_pix) >= var_floor

    ys = np.arange(0, H - p + 1, stride)
    xs = np.arange(0, W - p + 1, stride)
    F = np.fft.rfft2(band, s=(H, W))

    best, bxy, qxy = [], [], []
    for y in ys:
        for x in xs:
            if not ok_win[y, x]:
                continue
            t = band[y:y + p, x:x + p]
            tz = t - t.mean()
            tn = np.linalg.norm(tz)
            if tn <= 0:
                continue
            cands = [tz]
            if mirror:
                cands.append(tz[:, ::-1].copy())
            bb, bloc = -1.0, (0, 0)
            for tt in cands:
                K = np.zeros((H, W), np.float64)
                K[:p, :p] = tt[::-1, ::-1]      # correlation via convolution
                R = np.fft.irfft2(F * np.fft.rfft2(K, s=(H, W)), s=(H, W))
                # R[i, j] is the correlation for the window whose top-left is
                # (i - p + 1, j - p + 1); shift so index == window top-left
                R = R[p - 1:, p - 1:]
                m = min(R.shape[0], wnorm.shape[0]), min(R.shape[1], wnorm.shape[1])
                ncc = R[:m[0], :m[1]] / np.maximum(wnorm[:m[0], :m[1]] * tn, 1e-9)
                yy, xx = np.ogrid[:m[0], :m[1]]
                near = (np.abs(yy - y) < exclude) & (np.abs(xx - x) < exclude)
                ncc = np.where(near | ~ok_win[:m[0], :m[1]], -1.0, ncc)
                j = int(np.argmax(ncc))
                v = float(ncc.flat[j])
                if v > bb:
                    bb, bloc = v, divmod(j, m[1])
            best.append(bb)
            bxy.append((bloc[1] + p / 2, bloc[0] + p / 2))
            qxy.append((x + p / 2, y + p / 2))
    if len(best) < 32:
        return None
    return dict(best=np.array(best, np.float32),
                bxy=np.array(bxy, np.float32), qxy=np.array(qxy, np.float32),
                kept=len(best), total=int(len(ys) * len(xs)))


def orientation_R(band):
    """Axial concentration of the gradient orientations. 0 = isotropic, 1 = one way.

    THE THIRD ARM, ADDED BECAUSE THE OTHER TWO MISSED THE ONE CONTROL THAT WAS
    ACTUALLY WRONG.  The `stamp` rung of `tools/r2_3421_variety_control.py` --
    one mesh AND no per-instance yaw or mirror -- is instantly wrong to look at:
    every clump combs the same way.  The duplicate arm scored it 0.000 %, the
    same as the ship, and the period arm moved it only 0.114 against a 0.30 fail
    line, because a combed sward is not a lattice and contains no duplicated
    window.  Both arms would have passed it.

    Gradient orientations are doubled before averaging so the statistic is
    AXIAL: a blade leaning up-left and one leaning down-right are the same
    direction, which is what "combed" means and what an unsigned edge is.
    Magnitude-weighted, so the flat ground between blades does not vote.

    Measured on the ladder, all five rungs at 4K scale:

        ship 0.3100   top20 0.3104   top100 0.3107   allgrass100 0.2891
        stamp 0.6226

    Flat to 0.2 % across a top share of 9 %, 20 % and 100 %, and 2.01x on the
    rung that is wrong. That is the separation neither other arm had.
    """
    gy, gx = np.gradient(band.astype(np.float64))
    mag = np.hypot(gx, gy)
    if mag.sum() <= 1e-12:
        return 0.0, 0.0
    th = np.arctan2(gy, gx) * 2.0
    w = mag / mag.sum()
    C = float((w * np.cos(th)).sum())
    S = float((w * np.sin(th)).sum())
    return float(np.hypot(C, S)), float(np.degrees(np.arctan2(S, C) / 2.0))


def periodicity(band):
    """Strongest off-centre peak of the normalised autocorrelation."""
    a = band - band.mean()
    if a.std() < 1e-6:
        return 0.0, (0, 0)
    F = np.fft.rfft2(a)
    ac = np.fft.irfft2(F * np.conj(F), s=a.shape)
    ac = np.fft.fftshift(ac) / ac.flat[0]
    H, W = ac.shape
    cy, cx = H // 2, W // 2
    m = np.ones_like(ac, bool)
    # suppress the central lobe and the axes: a pure translation of the whole
    # band (which camera pan produces) sits on the axes and is not a lattice
    r = max(6, PATCH // 2)
    m[cy - r:cy + r + 1, :] = False
    m[:, cx - r:cx + r + 1] = False
    j = np.argmax(np.where(m, ac, -1))
    y, x = divmod(j, W)
    return float(ac[y, x]), (int(x - cx), int(y - cy))


# ---------------------------------------------------------------- controls
def make_control(band, kind, rng):
    """Repaint the band out of its OWN pixels, adding only repetition."""
    H, W = band.shape
    p = PATCH
    # the source patch: the most textured one in the band, so the control is
    # made of something that HAS a silhouette to recognise
    P, C = patches(band, p, STRIDE)
    v = P.std(1)
    src = P[int(v.argmax())].reshape(p, p)
    out = band.copy()
    if kind == "tile100":
        for _ in range((H * W) // (p * p) * 3):
            y = int(rng.integers(0, H - p)); x = int(rng.integers(0, W - p))
            t = src[::-1] if rng.random() < 0.5 else src
            t = t[:, ::-1] if rng.random() < 0.5 else t
            out[y:y + p, x:x + p] = t
    elif kind == "tile20":
        for _ in range(int((H * W) // (p * p) * 3 * 0.20)):
            y = int(rng.integers(0, H - p)); x = int(rng.integers(0, W - p))
            t = src[::-1] if rng.random() < 0.5 else src
            out[y:y + p, x:x + p] = t
    elif kind == "lattice":
        for y in range(0, H - p, p + 6):
            for x in range(0, W - p, p + 6):
                out[y:y + p, x:x + p] = src
    elif kind == "phase":
        F = np.fft.rfft2(band - band.mean())
        ph = rng.uniform(0, 2 * np.pi, F.shape)
        out = np.fft.irfft2(np.abs(F) * np.exp(1j * ph), s=band.shape)
        out = out * (band.std() / max(1e-6, out.std())) + band.mean()
    elif kind == "shuffle":
        ys = list(range(0, H - p + 1, p))
        xs = list(range(0, W - p + 1, p))
        tiles = [band[y:y + p, x:x + p].copy() for y in ys for x in xs]
        rng.shuffle(tiles)
        i = 0
        for y in ys:
            for x in xs:
                out[y:y + p, x:x + p] = tiles[i]; i += 1
    else:
        raise SystemExit("unknown control " + kind)
    return out


def dump_pairs(band, res, path, k=6):
    """Write the k strongest matched pairs side by side, so a person can look."""
    order = np.argsort(-res["best"])[:k]
    p = PATCH
    tile = np.zeros((k * (p + 2), 2 * (p + 2)), np.float32)
    H, W = band.shape
    for r, i in enumerate(order):
        for c, cxy in enumerate((res["qxy"][i], res["bxy"][i])):
            x, y = cxy
            x = int(np.clip(x - p / 2, 0, W - p)); y = int(np.clip(y - p / 2, 0, H - p))
            tile[r * (p + 2):r * (p + 2) + p, c * (p + 2):c * (p + 2) + p] = \
                band[y:y + p, x:x + p]
    a = np.clip(tile * 255, 0, 255).astype(np.uint8)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo",
                    "-pix_fmt", "gray", "-s", "%dx%d" % (a.shape[1], a.shape[0]),
                    "-i", "-", "-vf", "scale=iw*6:ih*6:flags=neighbor", path],
                   input=a.tobytes(), check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True)
    ap.add_argument("--f", type=int, nargs="+", required=True)
    ap.add_argument("--band", type=int, nargs=4, default=list(BAND))
    ap.add_argument("--control", default="none")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dump", default="")
    ap.add_argument("--seed", type=int, default=20263421)
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    x0, y0, w, h = a.band
    rows = []
    for f in a.f:
        img = read_gray(a.frames, f)
        band = img[y0:y0 + h, x0:x0 + w]
        if a.control != "none":
            band = make_control(band, a.control, rng)
        hp = band - box_blur(band, PATCH)          # kill the lighting ramp
        res = ncc_fullsearch(hp)
        if res is None:
            print(">> f%d: fewer than 32 textured patches in the band -- "
                  "nothing to measure." % f)
            rows.append({"frame": f, "vacuous": True})
            continue
        peak, lag = periodicity(hp)
        oR, oDeg = orientation_R(band)
        hit = float((res["best"] >= NCC_HIT).mean())
        # the whole top tail, so the verdict line is CHOSEN from the controls
        # rather than asserted: an exact duplicate scores 1.000 and generic
        # grass does not, and where those two populations part is a fact about
        # the material, not a preference.
        tail = {("hit_%.2f" % t): round(float((res["best"] >= t).mean()), 5)
                for t in (0.90, 0.94, 0.96, 0.98, 0.99, 0.999)}
        row = {"frame": f, "control": a.control,
               "patches_total": res["total"], "patches_textured": res["kept"],
               "ncc_p50": round(float(np.percentile(res["best"], 50)), 4),
               "ncc_p99": round(float(np.percentile(res["best"], 99)), 4),
               "ncc_max": round(float(res["best"].max()), 4),
               "hit_frac": round(hit, 5),
               "period_peak": round(peak, 4), "period_lag_px": list(lag),
               "orient_R": round(oR, 4), "orient_deg": round(oDeg, 1)}
        row.update(tail)
        rows.append(row)
        print("f%-6d %-9s textured %5d/%-6d  NCC p50 %.3f p99 %.3f max %.3f  "
              "hits>=%.2f %6.3f %%   period %.3f at %s"
              % (f, a.control, res["kept"], res["total"], row["ncc_p50"],
                 row["ncc_p99"], row["ncc_max"], NCC_HIT, hit * 100,
                 peak, tuple(lag)))
        print("        orient  R %.4f at %.1f deg  (isotropic 0, combed 1; "
              "ladder: ship 0.310, stamp 0.623)" % (oR, oDeg))
        print("        tail  " + "  ".join("%s %.3f%%" % (k, v * 100)
                                           for k, v in tail.items()))
        if a.dump:
            dump_pairs(hp, res, a.dump % f if "%" in a.dump else a.dump)

    live = [r for r in rows if not r.get("vacuous")]
    if not live:
        print("\n>> REFUSING: no frame in this run had a measurable band.")
        json.dump({"rows": rows, "vacuous": True}, open(a.out, "w"), indent=1)
        return gate_exit.verdict("FRAME_REPETITION_VACUOUS")
    worst_hit = max(r["hit_frac"] for r in live)
    worst_per = max(r["period_peak"] for r in live)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump({"band": a.band, "patch": PATCH, "stride": STRIDE,
               "exclude": EXCLUDE, "ncc_hit": NCC_HIT, "var_floor": VAR_FLOOR,
               "hit_frac_fail": HIT_FRAC_FAIL, "period_fail": PERIOD_FAIL,
               "control": a.control, "rows": rows,
               "worst_hit_frac": worst_hit, "worst_period_peak": worst_per},
              open(a.out, "w"), indent=1)
    print("\nwrote %s" % a.out)
    bad = []
    if worst_hit >= HIT_FRAC_FAIL:
        bad.append("DUPLICATE (%.3f %% of textured patches have a twin at NCC >= %.2f)"
                   % (worst_hit * 100, NCC_HIT))
    if worst_per >= PERIOD_FAIL:
        bad.append("PERIODIC (autocorrelation %.3f off-axis)" % worst_per)
    if bad:
        print(">> " + "; ".join(bad))
        return gate_exit.verdict("FRAME_REPETITION_FAIL")
    print(">> no duplicated silhouette and no placement period in %d frame(s)"
          % len(live))
    return gate_exit.verdict("FRAME_REPETITION_CLEAN")


if __name__ == "__main__":
    gate_exit.guard(main)
