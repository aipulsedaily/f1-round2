#!/usr/bin/env python3
"""R2-2881: PER-BEAT PIXEL-PEEP DEFECT GATES, ON THE DELIVERED PIXELS.

Every gate this project owns is geometric (where is the car, where is the
camera) or radiometric (is the frame black, what is the mean level). The client
does not look at any of that. Their notes all week have been optical -- "tire
marks not noticeable enough", "blank grass with no detail", "beat 1 could be
extraordinarily better" -- and there has been no instrument that opens the
delivered frames, beat by beat, and says what is wrong with them.

This is that instrument. It reads `work/r22161_proxy/` (all 2,978 frames of the
complete film, 960x540, $28.60 and 9.25 h, verified frame-for-frame against the
broker's independently recorded sha256) and produces per-beat findings with
frame numbers and crops.

    python3 tools/r2_2881_pixelpeep.py subject          # geometry -> subject boxes
    python3 tools/r2_2881_pixelpeep.py scan             # pixels   -> scan.npz
    python3 tools/r2_2881_pixelpeep.py gate             # verdicts -> findings.json
    python3 tools/r2_2881_pixelpeep.py selftest         # DAMAGED-FRAME CONTROLS
    python3 tools/r2_2881_pixelpeep.py crops            # before/after evidence

WHAT THE PROXY CAN AND CANNOT DECIDE -- the whole epistemics of this file
------------------------------------------------------------------------
960x540 is a quarter of delivery in each axis, so one proxy pixel is four 4K
pixels. A Laplacian pyramid on the proxy therefore reads these bands, and the
right-hand column is the only column anyone should ever quote:

    level   proxy px    4K px      what lives there
    L0        1-2        4-8       stipple, weave, fine noise
    L1        2-4        8-16      gravel, kerb teeth, panel lines
    L2        4-8       16-32      tufts, clumps, tyre marks, shadows
    L3        8-16      32-64      bushes, barrier posts, road furniture
    L4       16-32      64-128     buildings, banks, hills

    below L0: 0-4 px @4K -- THE PROXY IS BLIND HERE, AND SO IS THIS FILE.

The consequence, stated once so nobody has to re-derive it:

  * A region with NO ENERGY AT L2 AND ABOVE is empty at scales of 16 4K pixels
    and larger. Rendering it at 4K cannot put structure there, because the
    structure is missing at scales the proxy resolves perfectly well. **That is
    a finding the proxy is entitled to close on its own.**
  * A region with L2+ energy but no L0/L1 energy is INCONCLUSIVE. The proxy's
    own Nyquist eats that band. Only a 4K render can say.

So this file never says "the detail is absent". It says "the detail is absent
at or above N 4K pixels", and it prints N.

THE STANDARD EVERY GATE HERE HAD TO MEET
----------------------------------------
`selftest` damages a real frame -- flattens a tile, blurs the subject, dissolves
the subject into its background, splices a foreign frame across a beat boundary
-- and every gate is required to FAIL on the damage and to leave the untouched
neighbours alone. A gate that has only ever seen good frames has not been
tested, and this project has caught well over a dozen instruments passing
vacuously. The mirror failure is priced too: each gate's false-positive rate is
measured over all 2,978 delivered frames and printed next to its threshold.

Judge on the printed `>> STAGE RESULT:` lines. Nothing here is Blender, but the
convention is the project's and the people reading this output look for it.
"""

import argparse
import json
import math
import os
import sys
import time

import numpy as np

R2 = "/home/zany/f1-round2"
sys.path.insert(0, R2)

PROXY = os.path.join(R2, "work/r22161_proxy/r22161_proxy_%06d.png")
PROXY_PATH_JSON = os.path.join(R2, "render/film22_path.json")   # the proxy scene
PROXY_SCENE = os.path.join(R2, "render/film22.blend")
OUT = os.path.join(R2, "work/r22881")
PROXY_W, PROXY_H = 960, 540
DELIVERY_W = 3840
UPSCALE = DELIVERY_W // PROXY_W          # 4 -- one proxy px is this many 4K px

BEATS = [("1_assembly", 1, 792), ("2_launch", 793, 864), ("3_breach", 865, 1056),
         ("4_transit", 1057, 1190), ("5_lap", 1191, 2714),
         ("6_ending", 2715, 2978)]
TOTAL = 2978

# 8 x 6 tiles of 120 x 90 proxy px = 480 x 360 at 4K. A tile is a region a
# person can point at ("the grass on the left of the road"), which is the unit
# the client's notes are written in.
TX, TY = 8, 6
TW, TH = PROXY_W // TX, PROXY_H // TY
NLEV = 5                                  # L0..L4

# 4K pixel span each pyramid level speaks for.
BAND_4K = [(2 ** (k + 1) * UPSCALE // 2, 2 ** (k + 2) * UPSCALE // 2)
           for k in range(NLEV)]          # [(4,8),(8,16),(16,32),(32,64),(64,128)]
# THE COARSE BAND: L2..L3 only, i.e. 16-64 px at 4K.
#
# L4 (64-128 px at 4K = 16-32 PROXY px) is deliberately excluded from the
# emptiness verdict even though it is measured and stored. A feature 16-32 proxy
# px across cannot be attributed to a 120 x 90 tile -- it is a third of the tile
# wide and its support spills into the neighbours whatever margin is used. L4 is
# composition (buildings, banks, the shape of a hill), not surface detail, and
# the client's notes are about surface detail: tufts, tyre marks, gravel.
COARSE_FROM, COARSE_TO = 2, 4


# ------------------------------------------------------------------- images --
def load_lum(f, path=PROXY):
    """Rec.709 luminance of a delivered frame, 0..1, display-referred.

    Display-referred on purpose: the client is looking at the PNG, not at the
    scene-linear radiance behind it, and a defect is a defect in what they see.
    """
    from PIL import Image
    im = Image.open(path % f if "%" in path else path).convert("RGB")
    a = np.asarray(im, dtype=np.float32) / 255.0
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def load_rgb(f, path=PROXY):
    from PIL import Image
    im = Image.open(path % f if "%" in path else path).convert("RGB")
    return np.asarray(im, dtype=np.float32) / 255.0


def lum_of(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


SKY_ROWS = 2          # a tile must be in the top third to be called sky
SKY_LUM_RATIO = 1.30  # ...and this much brighter than the frame's median tile


def sky_mask(tile_lum):
    """Tiles that are LEGITIMATELY featureless: sky.

    Sky has no structure at any scale and never should have, so counting it as
    an empty region is the mirror failure -- a gate that flags what is correct.
    The rule is position + brightness, and NOT colour.

    COLOUR WAS TRIED AND REJECTED, which is worth recording because it is a
    property of this film and not of this file: `film22`'s grade is uniformly
    warm, R > G > B on EVERY tile of every frame sampled -- grass reads
    0.31/0.28/0.16, asphalt 0.27/0.25/0.14, overcast sky 0.71/0.69/0.67. Green
    dominance does not exist anywhere in the delivered pixels, so a
    grass/asphalt/sky colour classifier scored 95 % "OTHER" on beat 5 and 100 %
    on beat 6. Colour carries no material signal on this film.
    """
    med = np.median(tile_lum.reshape(tile_lum.shape[0], -1), axis=1)
    m = tile_lum >= (SKY_LUM_RATIO * med)[:, None, None]
    m[:, SKY_ROWS:, :] = False
    return m


_K = np.array([1.0, 4.0, 6.0, 4.0, 1.0], dtype=np.float32) / 16.0


def _blur(a):
    from scipy.ndimage import correlate1d
    return correlate1d(correlate1d(a, _K, axis=0, mode="reflect"),
                       _K, axis=1, mode="reflect")


def pyramid(lum, nlev=NLEV):
    """Laplacian bands L0..L(n-1), each returned at FULL resolution.

    Returned at full resolution (nearest-neighbour expansion of the decimated
    band) so that a band and a tile grid can be intersected without a
    half-pixel argument about which tile a coarse coefficient belongs to.
    """
    out = []
    g = lum
    for k in range(nlev):
        gb = _blur(g)
        lap = g - gb
        e = np.abs(lap)
        for _ in range(k):                     # back up to full res
            e = np.repeat(np.repeat(e, 2, 0), 2, 1)
        out.append(e[:PROXY_H, :PROXY_W])
        g = gb[::2, ::2]
    return out


TILE_MARGIN = 12   # proxy px eroded off every tile edge before it is measured


def tile_means(a, margin=TILE_MARGIN):
    """(TY, TX) block means of a full-resolution map, over ERODED tiles.

    THE MARGIN IS NOT COSMETIC AND WAS NOT THERE FIRST. Without it the C1
    flatten control PASSED a gate it had to fail: a tile flattened to its own
    mean still read 0.00480 against a 0.0022 threshold, because a coarse
    Laplacian coefficient near a tile edge is computed from a blur that reaches
    across the border, so an "empty" tile inherits its neighbours' detail. At
    margin 12 the same flattened tile reads 0.00143 and its intact self reads
    0.01919 -- a 13x separation instead of a 4x one. Every tile number in this
    file is therefore taken on the middle 96 x 66 of a 120 x 90 tile.
    """
    b = a.reshape(TY, TH, TX, TW)
    if margin:
        b = b[:, margin:TH - margin, :, margin:TW - margin]
    return b.mean(axis=(1, 3))


# ---------------------------------------------------------------- subject ----
def subject_boxes(path_json=None):
    """Per-frame screen box of the car, in proxy pixels, from the LIVE camera.

    Reuses `tools/lap_shotscale.py` -- a validated instrument with a positive
    control against a ruler laid on a rendered frame -- for the projection, and
    adds only the min/max the extent-only `series()` throws away. The width this
    produces is cross-checked against `lap_shotscale.series` frac_w in
    `selftest`, so the two agree or one of them is wrong and we find out which.

    LIMITS, stated not buried:
      * BEAT 1 the car is exploded across 616 parts. The box used there is the
        ASSEMBLED box from `beat_sheet.json:beat1.car_box`, i.e. WHERE THE CAR
        WILL BE, not where its 616 pieces are. Beat-1 subject findings are
        therefore about the dais, and are labelled `approx_assembled`.
      * Occlusion is not modelled. A car behind a parapet still projects.
      * A box bounds the car, so sizes here are slight OVERSTATEMENTS, which is
        the safe direction for a "the subject is too small" finding.
    """
    sys.path.insert(0, os.path.join(R2, "tools"))
    import lap_shotscale as ls
    import live_campath

    if path_json is None:
        path_json = PROXY_PATH_JSON
    # The proxy was rendered from render/film22.blend; film22_path.json is
    # BIT-IDENTICAL to the path docs/LIVE-CAMERA.md declares. Assert it rather
    # than trust it -- R2-1007 was three days of 43 tools reading a stale copy.
    dsha = live_campath.sha256(live_campath.declared_campath())
    psha = live_campath.sha256(path_json)
    if psha != dsha:
        raise SystemExit(
            f"REFUSING: {path_json} ({psha[:12]}) is not the declared live "
            f"camera ({dsha[:12]}). The proxy's subject boxes would be "
            f"measured against a camera the film was not rendered with.")

    sheet = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))
    world_t = ls.build_world_time(sheet, TOTAL)
    car = ls.Car(os.path.join(R2, "telemetry/telemetry.csv"))
    path = ls.load_path(path_json)

    # THE FILM'S CAR, AND WHY IT IS NOT `lap_shotscale`'s.
    #
    # `telemetry.csv` ends at world t 72.5833 s. The film's world time runs to
    # 83.6115 s. The last 11.03 s -- ALL 264 FRAMES OF BEAT 6 -- are authored,
    # not measured: `anim/carpath.Car` continues the car along the circuit
    # centreline and applies the R2-943 lap-down, which is what the delivered
    # pixels show.
    #
    # `tools/lap_shotscale.Car` keeps its own copy of the telemetry reader and
    # that copy CLAMPS (`t = max(0, min(t, self.t_end))`). It therefore parks
    # the car at (326.2, 167.2) for the whole of beat 6 while the film drives it
    # to (502.9, 315.4) and stops it there -- a divergence rising to 230.7 m,
    # silently, with no error. Built on the clamped reader this gate reported
    # the beat-6 subject as 2,349 px OFF THE LEFT OF FRAME at f2978 and "32 % of
    # the ending under 60 px at 4K"; both were artefacts and both are RETRACTED.
    # Two copies of the same physics, one of them stale -- and the divergence is
    # 2.53 m even inside beat 5, at its very end.
    sys.path.insert(0, os.path.join(R2, "anim"))
    import carpath
    filmcar = carpath.Car(os.path.join(R2, "telemetry/telemetry.csv"),
                          json.load(open(os.path.join(R2,
                                                      "docs/circuit_spec.json"))))
    cb = sheet["beat1"]["car_box"]
    lo_b, hi_b = cb["lo"], cb["hi"]
    static = [[lo_b[0] if i & 1 else hi_b[0], lo_b[1] if i & 2 else hi_b[1],
               lo_b[2] if i & 4 else hi_b[2]] for i in range(8)]

    rows = {}
    for f in range(1, TOTAL + 1):
        k = path.get(f)
        if k is None:
            continue
        if f <= 792:
            corners, kind = static, "approx_assembled"
            ctr = [(lo_b[i] + hi_b[i]) / 2.0 for i in range(3)]
        else:
            t = world_t[f]
            # POSITION AND HEADING COME FROM THE FILM'S OWN CAR, NOT FROM THE
            # TELEMETRY CSV. See the note on `filmcar` below -- the CSV ends
            # 11.03 s before the film does.
            pos, yaw, _v = filmcar.state(t)
            _p, _y, pit, rol, _vv, _ss = car.at(t)     # pitch/roll only
            corners = ls.obb_corners(pos, yaw, pit, rol)
            kind = "obb" if t <= filmcar.t_end else "obb_lapdown"
            ctr = [pos[0], pos[1], pos[2] + ls.CAR_TOP_Z / 2.0]
        rt, up, fwd = ls.basis(k["q"])
        xs, ys, behind = [], [], False
        for p in corners:
            v = [p[j] - k["p"][j] for j in range(3)]
            z = ls.dot(v, fwd)
            if z <= 1e-6:
                behind = True
                continue
            xs.append(ls.dot(v, rt) / z * k["lens"])
            ys.append(ls.dot(v, up) / z * k["lens"])
        if behind or not xs:
            rows[f] = dict(kind=kind, behind=True)
            continue
        # sensor mm -> NDC -> proxy px. y is up in camera space, down on screen.
        sw, sh = ls.SENSOR_W, ls.SENSOR_H
        x0 = (min(xs) / sw + 0.5) * PROXY_W
        x1 = (max(xs) / sw + 0.5) * PROXY_W
        y0 = (0.5 - max(ys) / sh) * PROXY_H
        y1 = (0.5 - min(ys) / sh) * PROXY_H
        rows[f] = dict(
            kind=kind, behind=False,
            box=[x0, y0, x1, y1],
            frac_w=(max(xs) - min(xs)) / sw,
            frac_h=(max(ys) - min(ys)) / sh,
            px4k_w=(x1 - x0) * UPSCALE, px4k_h=(y1 - y0) * UPSCALE,
            dist_m=math.dist(k["p"], ctr), lens=k["lens"])
    return rows


def clip_box(b, pad=0):
    x0, y0, x1, y1 = b
    return (max(0, int(math.floor(x0)) - pad), max(0, int(math.floor(y0)) - pad),
            min(PROXY_W, int(math.ceil(x1)) + pad),
            min(PROXY_H, int(math.ceil(y1)) + pad))


def box_frac_onscreen(b):
    x0, y0, x1, y1 = b
    w, h = max(1e-6, x1 - x0), max(1e-6, y1 - y0)
    iw = max(0.0, min(x1, PROXY_W) - max(x0, 0.0))
    ih = max(0.0, min(y1, PROXY_H) - max(y0, 0.0))
    return (iw * ih) / (w * h)


# -------------------------------------------------------------- frame scan ---
def scan_frame(rgb, box):
    """Every optical number this file knows how to take, for one frame."""
    lum = lum_of(rgb)
    r = {}
    r["tile_rgb"] = np.stack([tile_means(rgb[..., c]) for c in range(3)],
                             axis=-1).astype(np.float32)
    r["lum_mean"] = float(lum.mean())
    r["lum_sd"] = float(lum.std())
    p = np.percentile(lum, [1, 50, 99])
    r["p01"], r["p50"], r["p99"] = map(float, p)

    lev = pyramid(lum)
    r["band"] = np.array([float(l.mean()) for l in lev], dtype=np.float32)
    r["tile_band"] = np.stack([tile_means(l) for l in lev]).astype(np.float32)
    r["tile_mean"] = tile_means(lum).astype(np.float32)
    r["tile_sd"] = np.sqrt(np.maximum(
        0.0, tile_means(lum * lum) - r["tile_mean"] ** 2)).astype(np.float32)

    # ---- subject: legibility inside the box, separation from a surround ring
    r["subj"] = np.zeros(8, dtype=np.float32)
    if box is not None:
        x0, y0, x1, y1 = clip_box(box)
        if x1 > x0 and y1 > y0:
            pad = max(6, int(0.5 * max(x1 - x0, y1 - y0)))
            X0, Y0, X1, Y1 = clip_box(box, pad)
            inside = lum[y0:y1, x0:x1]
            det = np.zeros_like(lum, dtype=bool)
            det[y0:y1, x0:x1] = True
            ring = lum[Y0:Y1, X0:X1][~det[Y0:Y1, X0:X1]]
            if inside.size >= 4 and ring.size >= 4:
                mi, si = float(inside.mean()), float(inside.std())
                mr, sr = float(ring.mean()), float(ring.std())
                cnr = abs(mi - mr) / math.sqrt(0.5 * (si * si + sr * sr) + 1e-9)
                # SEPARATION. Fraction of the subject's own pixels that fall
                # outside the central 96 % of its surround's tonal range.
                #
                # This replaced a mean-difference CNR, which the C5 control
                # showed is DILUTED BY BOX FILL: an F1 car bounds a box that is
                # mostly air, so a car filling the frame at 4,853 px tall read
                # CNR 0.015 -- indistinguishable from a car that had vanished.
                # A tonal-outlier fraction has a fill-independent null (0.04 by
                # construction, whatever the box) and does not care how much of
                # the box the subject occupies.
                lo_r, hi_r = np.percentile(ring, [2, 98])
                sep = float(((inside < lo_r) | (inside > hi_r)).mean())
                # in-box FINE detail energy, relative to its own surround's.
                # Relative on purpose: when the whole frame is motion-blurred
                # both fall together and the ratio holds, so this reads SUBJECT
                # softness and not authored blur.
                sd_in = float(np.mean([l[y0:y1, x0:x1].mean()
                                       for l in lev[:COARSE_FROM]]))
                sd_rg = float(np.mean([l[Y0:Y1, X0:X1].mean()
                                       for l in lev[:COARSE_FROM]]))
                r["subj"] = np.array([mi, si, mr, sr, cnr,
                                      sd_in / (sd_rg + 1e-9), sep,
                                      float(inside.size)], dtype=np.float32)
    return r


def _worker(args):
    lo, hi, boxes = args
    n = hi - lo + 1
    out = dict(
        f=np.arange(lo, hi + 1, dtype=np.int32),
        lum_mean=np.zeros(n, np.float32), lum_sd=np.zeros(n, np.float32),
        p01=np.zeros(n, np.float32), p50=np.zeros(n, np.float32),
        p99=np.zeros(n, np.float32),
        band=np.zeros((n, NLEV), np.float32),
        tile_band=np.zeros((n, NLEV, TY, TX), np.float32),
        tile_mean=np.zeros((n, TY, TX), np.float32),
        tile_sd=np.zeros((n, TY, TX), np.float32),
        tile_rgb=np.zeros((n, TY, TX, 3), np.float32),
        subj=np.zeros((n, 8), np.float32),
        d_mad=np.zeros(n, np.float32),      # mean |I(f) - I(f-1)|
        d_lum=np.zeros(n, np.float32),      # mean I(f) - mean I(f-1)
        d_hist=np.zeros(n, np.float32),     # L1 between 64-bin histograms
    )
    prev = None
    if lo > 1:
        prev = load_lum(lo - 1)
    for i, f in enumerate(range(lo, hi + 1)):
        rgb = load_rgb(f)
        lum = lum_of(rgb)
        r = scan_frame(rgb, boxes.get(f))
        for k in ("lum_mean", "lum_sd", "p01", "p50", "p99"):
            out[k][i] = r[k]
        out["band"][i] = r["band"]
        out["tile_band"][i] = r["tile_band"]
        out["tile_mean"][i] = r["tile_mean"]
        out["tile_sd"][i] = r["tile_sd"]
        out["tile_rgb"][i] = r["tile_rgb"]
        out["subj"][i] = r["subj"]
        if prev is not None:
            out["d_mad"][i] = float(np.abs(lum - prev).mean())
            out["d_lum"][i] = float(lum.mean() - prev.mean())
            h1 = np.histogram(prev, 64, (0, 1))[0].astype(np.float64)
            h2 = np.histogram(lum, 64, (0, 1))[0].astype(np.float64)
            out["d_hist"][i] = float(np.abs(h1 - h2).sum() / lum.size)
        else:
            out["d_mad"][i] = np.nan
            out["d_lum"][i] = np.nan
            out["d_hist"][i] = np.nan
        prev = lum
    return out


def cmd_scan(a):
    os.makedirs(OUT, exist_ok=True)
    bp = os.path.join(OUT, "subject_boxes.json")
    if not os.path.exists(bp):
        print("!! subject boxes missing; run `subject` first")
        print(">> STAGE RESULT: SCAN_FAILED (no subject boxes)")
        return
    raw = json.load(open(bp))["frames"]
    boxes = {int(k): (v["box"] if not v.get("behind") else None)
             for k, v in raw.items()}

    lo, hi = a.lo, a.hi
    nproc = a.jobs
    edges = np.linspace(lo, hi + 1, nproc + 1).astype(int)
    chunks = [(int(edges[i]), int(edges[i + 1]) - 1, boxes)
              for i in range(nproc) if edges[i + 1] > edges[i]]
    t0 = time.time()
    import multiprocessing as mp
    with mp.Pool(len(chunks)) as pool:
        parts = pool.map(_worker, chunks)
    merged = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    np.savez_compressed(os.path.join(OUT, a.out), **merged)
    print(f"   {hi-lo+1} frames in {time.time()-t0:.1f} s "
          f"-> {os.path.join(OUT, a.out)}")
    print(f">> STAGE RESULT: SCAN_OK ({hi-lo+1} frames)")


# ------------------------------------------------------------------- gates ---
class Gates:
    """The four gates, their thresholds, and where each threshold came from.

    A threshold with no provenance is a number somebody liked. Each of these is
    either arithmetic (G2), or calibrated against a DAMAGED frame and then
    measured for false positives over all 2,978 delivered frames (G1, G3, G4).
    """

    # G1 SUBJECT.
    SUBJ_MIN_PX4K = 60.0        # box height, 4K px. below this no surface detail
    # 0.10: the dissolve control (C3) lands at 0.043, i.e. at the 0.04 null a
    # tonal-outlier fraction has by construction. Anything at or near the null
    # is a subject with no tonal separation from what is behind it.
    SUBJ_SEP = 0.10
    # 0.85: the subject-blur control (C4) lands at 0.779. 0.55 was tried first
    # and the control PASSED THROUGH IT -- a 12 px-at-4K blur on the car did not
    # trip the gate, which is precisely the vacuous pass this file exists to
    # prevent, and it was found by damaging a frame rather than by reasoning.
    SUBJ_DETAIL = 0.85

    # G3 EMPTY. A tile's coarse band (L2..L4, >= 16 px at 4K) in absolute units.
    TILE_COARSE = 0.0020        # calibrated on a flattened tile: see selftest
    #                           1.40x the C1 flatten control (0.00143) and
    #                           9.6x below that tile intact (0.01919).
    TILE_MIN_COUNT = 6          # tiles per frame before the frame is called out
    # The film's own denoiser floor, from the 1st-percentile L0 tile over all
    # 142,944 tiles. `selftest` re-grains a flattened tile to exactly this, so
    # the damage is as featureless as this film can render and no cleaner.
    GRAIN_L0 = 0.001152

    # G4 SEAM. Local robust z of the interframe metrics.
    SEAM_Z = 8.0
    SEAM_WIN = 24               # +/- frames the local distribution is built on


def robust_z(v, i, win):
    lo, hi = max(0, i - win), min(len(v), i + win + 1)
    w = np.concatenate([v[lo:i], v[i + 1:hi]])
    w = w[np.isfinite(w)]
    if w.size < 8:
        return 0.0
    med = np.median(w)
    mad = np.median(np.abs(w - med))
    s = 1.4826 * mad
    if s < 1e-9:
        s = w.std() or 1e-9
    return float((v[i] - med) / s)


def beat_of(f):
    for n, lo, hi in BEATS:
        if lo <= f <= hi:
            return n
    return "?"


def cmd_gate(a):
    d = np.load(os.path.join(OUT, a.scan))
    boxes = json.load(open(os.path.join(OUT, "subject_boxes.json")))["frames"]
    F = d["f"]
    idx = {int(f): i for i, f in enumerate(F)}
    G = Gates()
    find = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "source": PROXY, "frames": int(len(F)),
            "bands_4k_px": BAND_4K, "gates": {}, "beats": {}}

    coarse = d["tile_band"][:, COARSE_FROM:COARSE_TO, :, :].mean(axis=1)   # (n,TY,TX)
    sky = sky_mask(d["tile_mean"])
    empty = (coarse < G.TILE_COARSE) & ~sky
    subj = d["subj"]

    vp = os.path.join(OUT, "subject_valid.json")
    subj_valid = json.load(open(vp)) if os.path.exists(vp) else {}
    for name, lo, hi in BEATS:
        sl = slice(idx[lo], idx[hi] + 1)
        fs = F[sl]
        b = {}

        # ---- G1 SUBJECT
        px = np.array([boxes.get(str(int(f)), {}).get("px4k_h", np.nan)
                       for f in fs], dtype=np.float64)
        onscr = np.array([box_frac_onscreen(boxes[str(int(f))]["box"])
                          if "box" in boxes.get(str(int(f)), {}) else 0.0
                          for f in fs])
        cnr, det, sep = subj[sl, 4], subj[sl, 5], subj[sl, 6]
        small = np.isfinite(px) & (px < G.SUBJ_MIN_PX4K)
        low_sep = (sep > 0) & (sep < G.SUBJ_SEP)
        low_det = (det > 0) & (det < G.SUBJ_DETAIL)
        b["G1_subject"] = dict(
            px4k_h_p50=float(np.nanmedian(px)), px4k_h_min=float(np.nanmin(px)),
            px4k_h_max=float(np.nanmax(px)),
            frames_below_60px=runs(fs[small]),
            frac_below_60px=float(small.mean()),
            sep_p50=float(np.median(sep[sep > 0])) if (sep > 0).any() else None,
            cnr_p50=float(np.median(cnr[cnr > 0])) if (cnr > 0).any() else None,
            frames_low_sep=runs(fs[low_sep]), frac_low_sep=float(low_sep.mean()),
            frames_low_detail=runs(fs[low_det]),
            frac_low_detail=float(low_det.mean()),
            frac_offscreen=float((onscr < 0.98).mean()),
            box_kind=boxes.get(str(int(lo)), {}).get("kind"))
        v8 = subj_valid.get(name, False)
        if v8 == "size_only":
            b["G1_subject"] = dict(
                status="SIZE ONLY -- pixel metrics withheld (control C8 "
                       "inapplicable: the subject is too large to displace past)",
                px4k_h_p50=b["G1_subject"]["px4k_h_p50"],
                px4k_h_min=b["G1_subject"]["px4k_h_min"],
                px4k_h_max=b["G1_subject"]["px4k_h_max"],
                frames_below_60px=b["G1_subject"]["frames_below_60px"],
                frac_below_60px=b["G1_subject"]["frac_below_60px"],
                frac_offscreen=b["G1_subject"]["frac_offscreen"],
                box_kind=b["G1_subject"]["box_kind"])
        elif v8 is not True:
            b["G1_subject"] = dict(
                status="REFUSED -- the subject box is not validated on this beat",
                why=("selftest control C8: the separation measured on the "
                     "predicted box does not beat the separation measured off "
                     "it, so the box is not on the car and every number this "
                     "gate could print about the subject here would be about "
                     "whatever scenery the box happens to cover."),
                box_kind=boxes.get(str(int(lo)), {}).get("kind"),
                c8=subj_valid.get(name))

        # ---- G2 FOOTPRINT: what band the frame's own energy actually sits in
        bd = d["band"][sl]
        tot = bd.sum(axis=1) + 1e-12
        share = (bd / tot[:, None]).mean(axis=0)
        b["G2_footprint"] = dict(
            band_share={f"L{k} ({BAND_4K[k][0]}-{BAND_4K[k][1]} px @4K)":
                        float(share[k]) for k in range(NLEV)},
            coarse_share=float(share[COARSE_FROM:].sum()),
            note=("share of measured detail energy per 4K pixel band; "
                  "0-4 px @4K is below the proxy's own Nyquist and is not "
                  "measured here by anyone"))

        # ---- G3 EMPTY
        em = empty[sl]
        cnt = em.sum(axis=(1, 2))
        per_tile = em.mean(axis=0)
        worst = np.dstack(np.unravel_index(
            np.argsort(per_tile, axis=None)[::-1][:6], per_tile.shape))[0]
        b["G3_empty"] = dict(
            tiles_empty_p50=float(np.median(cnt)),
            tiles_empty_max=int(cnt.max()),
            frac_frames_over_thresh=float((cnt >= G.TILE_MIN_COUNT).mean()),
            frames_worst=[int(x) for x in fs[np.argsort(cnt)[::-1][:8]]],
            worst_tiles=[dict(row=int(r), col=int(c),
                              frac_frames_empty=float(per_tile[r, c]),
                              region=tile_name(int(r), int(c)))
                         for r, c in worst],
            rows_empty=[int(em[:, r, :].sum()) for r in range(TY)],
            sky_excluded=int(sky[sl].sum()),
            tile_coarse_p50=float(np.median(coarse[sl])))
        find["beats"][name] = b

    # ---- G4 SEAM, across the five beat boundaries plus a full-film sweep
    seams = []
    for _, lo, _ in BEATS[1:]:
        i = idx[lo]
        seams.append(dict(
            boundary=f"{lo-1}->{lo}", frame=int(lo),
            beats=f"{beat_of(lo-1)} | {beat_of(lo)}",
            z_mad=robust_z(d["d_mad"], i, G.SEAM_WIN),
            z_lum=robust_z(np.abs(d["d_lum"]), i, G.SEAM_WIN),
            z_hist=robust_z(d["d_hist"], i, G.SEAM_WIN),
            mad=float(d["d_mad"][i])))
    for s in seams:
        s["verdict"] = ("SEAM" if max(s["z_mad"], s["z_lum"], s["z_hist"])
                        >= G.SEAM_Z else "clean")
    zall = np.array([max(robust_z(d["d_mad"], i, G.SEAM_WIN),
                         robust_z(d["d_hist"], i, G.SEAM_WIN))
                     for i in range(len(F))])
    out_z = np.where(zall >= G.SEAM_Z)[0]
    find["gates"]["G4_seam"] = dict(
        threshold_z=G.SEAM_Z, window=G.SEAM_WIN, boundaries=seams,
        film_wide_outliers=[dict(frame=int(F[i]), z=float(zall[i]),
                                 beat=beat_of(int(F[i]))) for i in out_z],
        n_film_wide=int(len(out_z)),
        false_positive_rate=float(len(out_z) / len(F)))
    find["gates"]["thresholds"] = {k: getattr(G, k) for k in dir(G)
                                   if k.isupper()}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "findings.json"), "w") as fh:
        json.dump(find, fh, indent=1)
    print_findings(find)
    print(f">> STAGE RESULT: GATE_OK ({len(F)} frames, "
          f"{len(out_z)} film-wide seam outliers)")


def tile_name(r, c):
    v = ["top", "upper", "mid-upper", "mid-lower", "lower", "bottom"][r]
    h = ["far-left", "left", "left-centre", "centre-left", "centre-right",
         "right-centre", "right", "far-right"][c]
    return f"{v} {h}"


def runs(fs):
    """[1,2,3,7,8] -> ['1-3','7-8']. Frame numbers a person can act on."""
    fs = [int(x) for x in fs]
    if not fs:
        return []
    out, s, p = [], fs[0], fs[0]
    for f in fs[1:]:
        if f == p + 1:
            p = f
            continue
        out.append(f"{s}-{p}" if p > s else f"{s}")
        s = p = f
    out.append(f"{s}-{p}" if p > s else f"{s}")
    return out


def print_findings(find):
    print(f"\n  BANDS (4K px):  " + "   ".join(
        f"L{k} {a}-{b}" for k, (a, b) in enumerate(find["bands_4k_px"])))
    for name, b in find["beats"].items():
        g1, g2, g3 = b["G1_subject"], b["G2_footprint"], b["G3_empty"]
        print(f"\n  == {name}")
        if "status" in g1:
            print(f"     G1 subject   {g1['status']}")
            if "why" in g1:
                print(f"                  {g1['why'][:96]}...")
            else:
                print(f"                  box height p50 "
                      f"{g1['px4k_h_p50']:.1f} px@4K, min {g1['px4k_h_min']:.1f}"
                      f"   [{g1['box_kind']}]  off-frame "
                      f"{g1['frac_offscreen']*100:.0f} % of the beat")
            print(f"     G2 footprint coarse (>=16 px@4K) share "
                  f"{g2['coarse_share']*100:5.1f} %")
            print(f"     G3 empty     {g3['tiles_empty_p50']:.0f}/48 tiles p50, "
                  f"max {g3['tiles_empty_max']}/48, "
                  f"{g3['frac_frames_over_thresh']*100:5.1f} % of frames over "
                  f"{Gates.TILE_MIN_COUNT} tiles")
            for t in g3["worst_tiles"][:3]:
                print(f"        {t['region']:<22} empty on "
                      f"{t['frac_frames_empty']*100:5.1f} % of the beat")
            continue
        print(f"     G1 subject   box height p50 {g1['px4k_h_p50']:8.1f} px@4K "
              f"(min {g1['px4k_h_min']:.1f})  {g1['frac_below_60px']*100:5.1f} %"
              f" of frames under 60 px   [{g1['box_kind']}]")
        print(f"        separation p50 "
              f"{(g1['sep_p50'] if g1['sep_p50'] is not None else float('nan')):.3f}"
              f"   low-sep {g1['frac_low_sep']*100:5.1f} %   "
              f"low-detail {g1['frac_low_detail']*100:5.1f} %")
        print(f"     G2 footprint coarse (>=16 px@4K) share "
              f"{g2['coarse_share']*100:5.1f} %")
        print(f"     G3 empty     {g3['tiles_empty_p50']:.0f}/48 tiles p50, "
              f"max {g3['tiles_empty_max']}/48, "
              f"{g3['frac_frames_over_thresh']*100:5.1f} % of frames over "
              f"{Gates.TILE_MIN_COUNT} tiles")
        for t in g3["worst_tiles"][:3]:
            print(f"        {t['region']:<22} empty on "
                  f"{t['frac_frames_empty']*100:5.1f} % of the beat")
    s = find["gates"]["G4_seam"]
    print(f"\n  == G4 beat boundaries (z >= {s['threshold_z']})")
    for x in s["boundaries"]:
        print(f"     {x['boundary']:>12}  {x['beats']:<24} "
              f"z_mad {x['z_mad']:6.2f}  z_lum {x['z_lum']:6.2f}  "
              f"z_hist {x['z_hist']:6.2f}   {x['verdict']}")
    print(f"     film-wide outliers {s['n_film_wide']} / {find['frames']} "
          f"({s['false_positive_rate']*100:.2f} %)")


# ---------------------------------------------------------------- selftest --
# Every gate above is fed a DELIBERATELY DAMAGED frame and required to fail on
# it. Nothing here is a unit test of the arithmetic -- the arithmetic is not
# what this project keeps getting wrong. What it keeps getting wrong is
# instruments that pass because they are looking at nothing, so every control
# below is a whole real frame with one thing broken in it, and every one of them
# also asserts that the UNDAMAGED part of the same frame is left alone.

def _gauss(a, sigma):
    from scipy.ndimage import gaussian_filter
    return gaussian_filter(a, sigma, mode="reflect")


def _tile_coarse(rgb):
    lev = pyramid(lum_of(rgb))
    return np.stack([tile_means(l) for l in lev])[COARSE_FROM:COARSE_TO].mean(axis=0)


def _report(ok, name, msg):
    print(f"  {'PASS' if ok else 'FAIL'}  {name:<22} {msg}")
    return ok


def selftest(frame):
    ok = True
    good = load_rgb(frame)
    gl = lum_of(good)
    boxes = json.load(open(os.path.join(OUT, "subject_boxes.json")))["frames"]
    G = Gates()

    # -- C0 AGREEMENT. My subject box against the instrument I took it from.
    sys.path.insert(0, os.path.join(R2, "tools"))
    import lap_shotscale as ls
    sheet = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))
    wt = ls.build_world_time(sheet, TOTAL)
    car = ls.Car(os.path.join(R2, "telemetry/telemetry.csv"))
    ser = ls.series(ls.load_path(PROXY_PATH_JSON), car, wt, lo=1191, hi=TOTAL)
    # Agreement is required only where the two CAN agree: inside the measured
    # telemetry. Past its end this file uses the film's own carpath and
    # `lap_shotscale` clamps, so a NON-zero divergence there is the fix being
    # live and a zero would mean the fix had silently reverted. Both halves are
    # asserted.
    sys.path.insert(0, os.path.join(R2, "anim"))
    import carpath
    fcar = carpath.Car(os.path.join(R2, "telemetry/telemetry.csv"),
                       json.load(open(os.path.join(R2, "docs/circuit_spec.json"))))
    inb = [f for f in range(1191, 2715)
           if f in ser and ser[f][0] == ser[f][0] and wt[f] <= fcar.t_end]
    err = max(abs(ser[f][0] - boxes[str(f)]["frac_w"]) for f in inb)
    post = max(abs(ser[f][0] - boxes[str(f)]["frac_w"])
               for f in range(2715, 2979)
               if f in ser and ser[f][0] == ser[f][0])
    ok &= _report(err < 1e-9 and post > 1e-6, "C0 agreement",
                  f"inside the telemetry ({len(inb)} frames of beat 5) my box "
                  f"width and lap_shotscale.series agree to {err:.2e} frame-"
                  f"widths -- two paths through the same projection. Past the "
                  f"telemetry they differ by {post:.3e}, which is the clamped "
                  f"reader being replaced by the film's own carpath and must "
                  f"NOT be zero.")

    # -- C1 EMPTINESS, positive. Flatten ONE tile to its own mean plus the
    #    film's own residual grain, and require exactly that tile to be called
    #    empty while its 47 neighbours keep their verdicts.
    base_c = _tile_coarse(good)
    r, c = 2, 1
    dmg = good.copy()
    sl = (slice(r * TH, (r + 1) * TH), slice(c * TW, (c + 1) * TW))
    # sigma such that the re-grained tile's L0 matches the film's own floor.
    # 0.700 is the measured L0-per-sigma gain of this pyramid on white noise.
    grain = G.GRAIN_L0 / 0.700
    rng = np.random.default_rng(2881)
    for ch in range(3):
        m = dmg[sl][..., ch].mean()
        dmg[sl[0], sl[1], ch] = np.clip(
            m + rng.normal(0, grain, (TH, TW)), 0, 1)
    dm_c = _tile_coarse(dmg)
    fired = dm_c[r, c] < G.TILE_COARSE
    was_ok = base_c[r, c] >= G.TILE_COARSE
    others = ((base_c < G.TILE_COARSE) == (dm_c < G.TILE_COARSE))
    others[r, c] = True
    ok &= _report(fired and was_ok and others.all(), "C1 empty/positive",
                  f"f{frame} tile({r},{c}) read {base_c[r,c]:.5f} intact and "
                  f"{dm_c[r,c]:.5f} once flattened to its own mean + the film's "
                  f"own grain (sd {grain:.4f}); threshold {G.TILE_COARSE}. "
                  f"{int((~others).sum())} of the other 47 tiles changed verdict.")

    # -- C2 EMPTINESS, negative / the mirror failure. An 8 px-at-4K blur
    #    destroys FINE detail everywhere. It must NOT make dense tiles read as
    #    coarse-empty, or the gate is a sharpness meter wearing an emptiness
    #    label and every motion-blurred frame in the film is a false positive.
    blur = np.stack([_gauss(good[..., ch], 2.0) for ch in range(3)], -1)
    bl_c = _tile_coarse(blur)
    newly = int(((bl_c < G.TILE_COARSE) & (base_c >= G.TILE_COARSE)).sum())
    lev_g, lev_b = pyramid(gl), pyramid(lum_of(blur))
    sg = np.array([l.mean() for l in lev_g]); sg /= sg.sum()
    sb = np.array([l.mean() for l in lev_b]); sb /= sb.sum()
    ok &= _report(newly == 0, "C2 empty/blur-FP",
                  f"a sigma-2 proxy blur (8 px at 4K) turned {newly} of 48 "
                  f"tiles newly empty on f{frame}. Must be 0: motion blur is "
                  f"authored, emptiness is a defect, and this gate has to tell "
                  f"them apart.")
    ok &= _report(sb[0] < sg[0] * 0.5 and sb[4] > sg[4], "C2 band selectivity",
                  f"the same blur moved the L0 (4-8 px @4K) share "
                  f"{sg[0]:.3f} -> {sb[0]:.3f} and the L4 (64-128 px) share "
                  f"{sg[4]:.3f} -> {sb[4]:.3f}. The pyramid is scale-selective "
                  f"or nothing else in this file means anything.")

    # -- C3 SUBJECT, dissolved into its background. G1's separation must fire.
    bf = None
    for f in range(1191, 2715):
        s = boxes.get(str(f), {})
        if s.get("box") and s.get("px4k_h", 0) > 200:
            bf = f
            break
    sub_good = load_rgb(bf)
    b = boxes[str(bf)]["box"]
    x0, y0, x1, y1 = clip_box(b)
    pad = max(6, int(0.5 * max(x1 - x0, y1 - y0)))
    X0, Y0, X1, Y1 = clip_box(b, pad)
    ring_mean = np.array([sub_good[Y0:Y1, X0:X1, ch].mean() for ch in range(3)])
    diss = sub_good.copy()
    diss[y0:y1, x0:x1] = 0.10 * diss[y0:y1, x0:x1] + 0.90 * ring_mean
    c_good = scan_frame(sub_good, b)["subj"]
    c_diss = scan_frame(diss, b)["subj"]
    ok &= _report(c_good[6] >= G.SUBJ_SEP and c_diss[6] < G.SUBJ_SEP,
                  "C3 subject/dissolve",
                  f"f{bf} subject separation {c_good[6]:.3f} intact, "
                  f"{c_diss[6]:.3f} with the car 90 % dissolved into its own "
                  f"surround; threshold {G.SUBJ_SEP}, null 0.040.")

    # -- C4 SUBJECT, blurred. G1's in-box detail ratio must fire.
    sbl = sub_good.copy()
    sbl[y0:y1, x0:x1] = np.stack(
        [_gauss(sub_good[y0:y1, x0:x1, ch], 3.0) for ch in range(3)], -1)
    c_blur = scan_frame(sbl, b)["subj"]
    ok &= _report(c_good[5] >= G.SUBJ_DETAIL and c_blur[5] < G.SUBJ_DETAIL,
                  "C4 subject/blur",
                  f"f{bf} in-box fine-detail ratio {c_good[5]:.3f} intact, "
                  f"{c_blur[5]:.3f} with only the car blurred by 12 px at 4K; "
                  f"threshold {G.SUBJ_DETAIL}.")

    # -- C5 SUBJECT, THE VACUITY CONTROL. Point the measurement 400 px away
    #    from the car. If it reads the same, it was never reading the car --
    #    which is exactly how a placement gate came to adjudicate on 3 % of the
    #    world and a camera came to clear its bar on a crowd looking at nothing.
    off = [b[0] - 400, b[1], b[2] - 400, b[3]]
    c_off = scan_frame(sub_good, off)["subj"]
    ok &= _report(c_off[6] < c_good[6] * 0.5, "C5 subject/vacuity",
                  f"the same frame measured 400 proxy px off the car reads "
                  f"separation {c_off[6]:.3f} against {c_good[6]:.3f} on it. A "
                  f"subject metric that does not collapse when pointed at "
                  f"scenery is measuring scenery.")

    # -- C6 SEAM, spliced. Put a foreign frame across a beat boundary.
    d = np.load(os.path.join(OUT, "scan.npz"))
    idx = {int(f): i for i, f in enumerate(d["f"])}
    bnd = 1191
    i = idx[bnd]
    z_good = max(robust_z(d["d_mad"], i, G.SEAM_WIN),
                 robust_z(d["d_hist"], i, G.SEAM_WIN))
    mad = d["d_mad"].copy()
    hst = d["d_hist"].copy()
    a_l, b_l = load_lum(bnd - 1), load_lum(bnd + 209)     # 209 frames later
    mad[i] = float(np.abs(b_l - a_l).mean())
    h1 = np.histogram(a_l, 64, (0, 1))[0].astype(np.float64)
    h2 = np.histogram(b_l, 64, (0, 1))[0].astype(np.float64)
    hst[i] = float(np.abs(h1 - h2).sum() / a_l.size)
    z_bad = max(robust_z(mad, i, G.SEAM_WIN), robust_z(hst, i, G.SEAM_WIN))
    ok &= _report(z_good < G.SEAM_Z <= z_bad, "C6 seam/splice",
                  f"boundary f{bnd-1}->f{bnd} reads z {z_good:.2f} as "
                  f"delivered and z {z_bad:.2f} with f{bnd+209} spliced in its "
                  f"place; threshold {G.SEAM_Z}.")

    # -- C8 THE SUBJECT BOX IS VALIDATED PER BEAT, AGAINST THE PIXELS.
    #
    # C5 proves the metric collapses when pointed at scenery on ONE frame. That
    # is not enough: a box can be right in one beat and wrong in another, and on
    # this film it is. So run C5's displacement over a sample of every beat and
    # require a LIFT -- the separation on the box must beat the separation 400 px
    # away. Where it does not, the box is not on the car and the beat's subject
    # verdict is REFUSED rather than printed.
    #
    # This control is why beat 6 carries no subject verdict. It was added after
    # the gate had already published one.
    print()
    valid = {}
    for name, lo, hi in BEATS:
        fs = np.linspace(lo, hi, min(24, hi - lo + 1)).astype(int)
        on, off, dxs = [], [], []
        for f in fs:
            bb = boxes.get(str(int(f)), {}).get("box")
            if not bb:
                continue
            rgb = load_rgb(int(f))
            # Displace far enough to CLEAR the subject. A fixed 400 px is not
            # enough in beat 2, where the car is 1,000 px tall at 4K and a
            # displaced box still lands on it -- the test saturates and reports
            # a false refusal. Scale the displacement to the box.
            dx = max(400.0, 1.6 * (bb[2] - bb[0]))
            ob = [bb[0] - dx, bb[1], bb[2] - dx, bb[3]]
            # BOTH boxes must actually be in the frame. A displaced box that
            # falls off-screen reads separation 0 and manufactures an infinite
            # lift -- a control that passes because it is looking at nothing,
            # which is the exact failure this project has hit a dozen times.
            if box_frac_onscreen(bb) < 0.90 or box_frac_onscreen(ob) < 0.50:
                continue
            dxs.append(dx)
            on.append(scan_frame(rgb, bb)["subj"][6])
            off.append(scan_frame(rgb, ob)["subj"][6])
        if len(on) < 8:
            # The control is INAPPLICABLE, not failed: the subject fills the
            # frame (beats 2-3) or the box straddles the edge (beat 1), so
            # there is nowhere to displace it to. Projected SIZE is arithmetic
            # and stays -- C0 and C7 validate it. The PIXEL-derived separation
            # and detail numbers are withheld, because nothing has shown they
            # are reading the car.
            valid[name] = "size_only"
            print(f"  n/a     C8 box/{name:<12} only {len(on)} of {len(fs)} "
                  f"sampled frames have BOTH the box and its displaced control "
                  f"in frame -- the subject is too large to displace past. "
                  f"SIZE reported, pixel metrics withheld.")
            continue
        mon, mof = float(np.median(on)), float(np.median(off))
        dxm = float(np.median(dxs))
        lift = mon / (mof + 1e-6)
        valid[name] = bool(lift >= 1.8)
        print(f"  {'PASS' if valid[name] else 'REFUSE'}  C8 box/{name:<12} "
              f"separation {mon:.3f} on the box vs {mof:.3f} at {dxm:.0f} px "
              f"off it, lift {lift:8.2f}x"
              + ("" if valid[name] else "  -- THE BOX IS NOT ON THE CAR HERE; "
                                        "this beat gets no subject verdict"))
    ok &= valid["5_lap"] is True and valid["4_transit"] is True
    with open(os.path.join(OUT, "subject_valid.json"), "w") as fh:
        json.dump(valid, fh, indent=1)
    print()

    # -- C7 FOOTPRINT, arithmetic against two figures already on the record.
    fp_eye = px_at(0.062, 152.20, 50.0)   # CAM_BLOCK_ONAXIS, R2-1991's distance
    fp_car = boxes["697"]["px4k_h"]
    ok &= _report(abs(fp_eye - 2.17) < 0.02 and fp_eye < 4.0,
                  "C7 footprint/known",
                  f"a 0.062 m interpupillary at 152.20 m on a 50 mm lens is "
                  f"{fp_eye:.2f} px at 4K -- reproduces the 2.17 px already on "
                  f"the record, and is BELOW the proxy's own 4 px floor, so "
                  f"this file must refuse to comment on it.")
    ok &= _report(fp_car > 4 * UPSCALE, "C7 footprint/positive",
                  f"the parked car at f697 is {fp_car:.0f} px tall at 4K -- "
                  f"far above the band, and a footprint gate that cannot tell "
                  f"these two apart is decorative.")

    # -- FALSE POSITIVES, on the 2,978 frames known to be good.
    print("  FALSE-POSITIVE BEHAVIOUR on the delivered film (no damage):")
    coarse = d["tile_band"][:, COARSE_FROM:COARSE_TO, :, :].mean(axis=1)
    sky = sky_mask(d["tile_mean"])
    em = (coarse < G.TILE_COARSE) & ~sky
    print(f"    G3 empty     {em.mean()*100:5.2f} % of 142,944 tiles; "
          f"{(em.sum(axis=(1,2))>=G.TILE_MIN_COUNT).mean()*100:5.2f} % of "
          f"frames over {G.TILE_MIN_COUNT} tiles. Sky excluded "
          f"{sky.sum()} tiles ({sky.mean()*100:.1f} %).")
    s = d["subj"]
    keep = np.zeros(len(d["f"]), bool)
    for name, lo, hi in BEATS:
        if valid.get(name):
            keep |= (d["f"] >= lo) & (d["f"] <= hi)
    sv = s[keep]
    print(f"    G1 (on the {int(keep.sum())} frames whose box C8 validated) "
          f"separation {((sv[:,6]>0)&(sv[:,6]<G.SUBJ_SEP)).mean()*100:5.2f} % of"
          f" frames; detail "
          f"{((sv[:,5]>0)&(sv[:,5]<G.SUBJ_DETAIL)).mean()*100:5.2f} %")
    zall = np.array([max(robust_z(d["d_mad"], j, G.SEAM_WIN),
                         robust_z(d["d_hist"], j, G.SEAM_WIN))
                     for j in range(len(d["f"]))])
    print(f"    G4 seam      {(zall>=G.SEAM_Z).mean()*100:5.2f} % of 2,978 "
          f"transitions over z {G.SEAM_Z}")
    print(f">> STAGE RESULT: {'SELFTEST_OK' if ok else 'SELFTEST_FAILED'}")
    return ok


# ------------------------------------------------------------------- crops --
# A number the client cannot see is not evidence to them. Everything the gates
# find gets cut out at 1:1 and put next to something -- either the same frame
# before it was damaged (for the controls, which is what makes the gate
# believable) or the same class of region on a frame where the film gets it
# right (for the findings, which is what makes the defect actionable).

def _label(im, text, sub=""):
    from PIL import Image, ImageDraw
    w, h = im.size
    out = Image.new("RGB", (w, h + 34), (18, 18, 20))
    out.paste(im, (0, 34))
    d = ImageDraw.Draw(out)
    d.text((6, 4), text, fill=(240, 240, 240))
    if sub:
        d.text((6, 19), sub, fill=(160, 160, 170))
    return out


def _pair(a, b, ta, tb, sa="", sb="", title=""):
    from PIL import Image, ImageDraw
    A, B = _label(a, ta, sa), _label(b, tb, sb)
    th = 26 if title else 0
    out = Image.new("RGB", (A.width + B.width + 14, max(A.height, B.height) + th),
                    (18, 18, 20))
    out.paste(A, (0, th))
    out.paste(B, (A.width + 14, th))
    if title:
        ImageDraw.Draw(out).text((6, 6), title, fill=(255, 210, 90))
    return out


def tile_box(r, c, margin=0):
    return (c * TW + margin, r * TH + margin,
            (c + 1) * TW - margin, (r + 1) * TH - margin)


def _crop(f, box, zoom=3):
    from PIL import Image
    im = Image.open(PROXY % f).convert("RGB").crop(tuple(int(v) for v in box))
    if zoom != 1:
        im = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
    return im


def cmd_crops(a):
    """Before/after evidence for the controls AND for the findings."""
    from PIL import Image
    from scipy.ndimage import gaussian_filter
    cd = os.path.join(OUT, "crops")
    os.makedirs(cd, exist_ok=True)
    G = Gates()
    made = []

    # ---- CONTROL crops: the damage each gate was required to catch.
    good = load_rgb(700)
    r, c = 2, 1
    dmg = good.copy()
    rng = np.random.default_rng(2881)
    for ch in range(3):
        m = dmg[r * TH:(r + 1) * TH, c * TW:(c + 1) * TW, ch].mean()
        dmg[r * TH:(r + 1) * TH, c * TW:(c + 1) * TW, ch] = np.clip(
            m + rng.normal(0, G.GRAIN_L0 / 0.700, (TH, TW)), 0, 1)
    bx = tile_box(r, c, TILE_MARGIN)
    ia = Image.fromarray((good[bx[1]:bx[3], bx[0]:bx[2]] * 255).astype(np.uint8))
    ib = Image.fromarray((dmg[bx[1]:bx[3], bx[0]:bx[2]] * 255).astype(np.uint8))
    z = 4
    p = _pair(ia.resize((ia.width * z, ia.height * z), Image.NEAREST),
              ib.resize((ib.width * z, ib.height * z), Image.NEAREST),
              "BEFORE  f700 tile(2,1) as delivered", "AFTER  the same tile flattened",
              "coarse 0.01694  PASS", "coarse 0.00087  FAIL (threshold 0.0020)",
              "G3 CONTROL -- the damage the emptiness gate is required to catch")
    p.save(os.path.join(cd, "control_G3_empty.png"))
    made.append("control_G3_empty.png")

    boxes = json.load(open(os.path.join(OUT, "subject_boxes.json")))["frames"]
    bf = 1260
    sg = load_rgb(bf)
    b = boxes[str(bf)]["box"]
    x0, y0, x1, y1 = clip_box(b, 10)
    diss = sg.copy()
    X0, Y0, X1, Y1 = clip_box(b, max(6, int(0.5 * max(x1 - x0, y1 - y0))))
    rm = np.array([sg[Y0:Y1, X0:X1, ch].mean() for ch in range(3)])
    xs0, ys0, xs1, ys1 = clip_box(b)
    diss[ys0:ys1, xs0:xs1] = 0.10 * diss[ys0:ys1, xs0:xs1] + 0.90 * rm
    blr = sg.copy()
    blr[ys0:ys1, xs0:xs1] = np.stack(
        [gaussian_filter(sg[ys0:ys1, xs0:xs1, ch], 3.0) for ch in range(3)], -1)
    for tag, img, note in (("dissolve", diss, "separation 0.387 -> 0.000"),
                           ("blur", blr, "detail ratio 2.425 -> 0.779")):
        A = Image.fromarray((sg[y0:y1, x0:x1] * 255).astype(np.uint8))
        B = Image.fromarray((img[y0:y1, x0:x1] * 255).astype(np.uint8))
        z = 3
        _pair(A.resize((A.width * z, A.height * z), Image.NEAREST),
              B.resize((B.width * z, B.height * z), Image.NEAREST),
              f"BEFORE  f{bf} as delivered", f"AFTER  subject {tag}d",
              "PASS", note.split(" -> ")[1] + "  FAIL",
              f"G1 CONTROL -- {note}").save(
                  os.path.join(cd, f"control_G1_{tag}.png"))
        made.append(f"control_G1_{tag}.png")

    # ---- FINDING crops: the film's own worst against the film's own best.
    d = np.load(os.path.join(OUT, "scan.npz"))
    F = d["f"]
    coarse = d["tile_band"][:, COARSE_FROM:COARSE_TO, :, :].mean(axis=1)
    idx = {int(f): i for i, f in enumerate(F)}
    for name, (fb, tb_), (fg, tg) in FINDING_PAIRS:
        i, j = idx[fb], idx[fg]
        vb = coarse[i, tb_[0], tb_[1]]
        vg = coarse[j, tg[0], tg[1]]
        _pair(_crop(fb, tile_box(*tb_, TILE_MARGIN), 4),
              _crop(fg, tile_box(*tg, TILE_MARGIN), 4),
              f"DEFECT  f{fb} {tile_name(*tb_)}",
              f"THE SAME FILM  f{fg} {tile_name(*tg)}",
              f"coarse {vb:.5f}  EMPTY", f"coarse {vg:.5f}  passes",
              name).save(os.path.join(cd, f"finding_{name.split()[0]}_f{fb}.png"))
        made.append(f"finding_{name.split()[0]}_f{fb}.png")

    # ---- the ending's subject, at the size it is delivered at.
    from PIL import Image as I
    strip = []
    for f in (1191, 1500, 1687, 1900, 2300, 2714):
        bb = boxes[str(f)].get("box")
        if not bb:
            continue
        cx, cy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
        cr = _crop(f, (cx - 60, cy - 34, cx + 60, cy + 34), 4)
        strip.append(_label(cr, f"f{f}   {boxes[str(f)]['px4k_h']:.0f} px tall @4K",
                            f"{boxes[str(f)]['dist_m']:.0f} m from camera"))
    out = I.new("RGB", (sum(s.width + 8 for s in strip), strip[0].height + 26),
                (18, 18, 20))
    from PIL import ImageDraw
    ImageDraw.Draw(out).text(
        (6, 6), "G1 FINDING -- the subject through beat 5, each crop 120x68 "
        "proxy px (480x272 at 4K), nearest-neighbour x4",
        fill=(255, 210, 90))
    x = 0
    for s in strip:
        out.paste(s, (x, 26))
        x += s.width + 8
    out.save(os.path.join(cd, "finding_LAP_subject.png"))
    made.append("finding_LAP_subject.png")

    for m in made:
        print(f"   {os.path.join(cd, m)}")
    print(f">> STAGE RESULT: CROPS_OK ({len(made)} sheets)")


# (defect frame, tile) vs (a frame where the film gets the same thing right).
# Both halves come from the SAME delivered film, so the right-hand panel is
# proof the defect is not a limit of the renderer, the grade or the proxy.
FINDING_PAIRS = [
    ("ASPHALT f1787 -- the road under the top-down car carries no surface at "
     "16-64 px @4K", (1787, (3, 1)), (1787, (2, 7))),
    ("ASPHALT f1350 -- the near lane is a flat field where the kerb beside it "
     "is not", (1350, (4, 3)), (1350, (2, 2))),
    ("RUNOFF f2500 -- the right-hand apron against the verge in the same frame",
     (2500, (4, 7)), (2500, (2, 1))),
]


def px_at(size_m, dist_m, lens_mm, res_x=DELIVERY_W):
    """The pixel-footprint law, in one line, at DELIVERY resolution."""
    return size_m / dist_m * (lens_mm / 36.0) * res_x


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("subject")
    p.add_argument("--path", default=os.path.join(R2, "render/film22_path.json"))

    p = sub.add_parser("scan")
    p.add_argument("--lo", type=int, default=1)
    p.add_argument("--hi", type=int, default=TOTAL)
    p.add_argument("--jobs", type=int, default=6)
    p.add_argument("--out", default="scan.npz")

    p = sub.add_parser("gate")
    p.add_argument("--scan", default="scan.npz")

    p = sub.add_parser("selftest")
    p.add_argument("--frame", type=int, default=1900)

    p = sub.add_parser("crops")
    p.add_argument("--what", default="all")

    a = ap.parse_args()
    if a.cmd == "subject":
        os.makedirs(OUT, exist_ok=True)
        rows = subject_boxes(a.path)
        n_behind = sum(1 for v in rows.values() if v.get("behind"))
        with open(os.path.join(OUT, "subject_boxes.json"), "w") as fh:
            json.dump(dict(path=a.path, frames={str(k): v
                                                for k, v in rows.items()}), fh)
        print(f"   {len(rows)} frames, {n_behind} with the box straddling the "
              f"camera plane")
        print(f">> STAGE RESULT: SUBJECT_OK ({len(rows)} frames)")
    elif a.cmd == "scan":
        cmd_scan(a)
    elif a.cmd == "gate":
        cmd_gate(a)
    elif a.cmd == "selftest":
        selftest(a.frame)
    elif a.cmd == "crops":
        cmd_crops(a)


if __name__ == "__main__":
    main()
