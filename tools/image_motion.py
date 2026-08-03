#!/usr/bin/env python3
"""BLOCK MOTION FIELD -- what the picture does, when the picture does two things.

    .venv/bin/python tools/image_motion.py --selftest
    .venv/bin/python tools/image_motion.py --seq DIR --prefix P --lo N --hi N
    .venv/bin/python tools/image_motion.py --calibrate DIR --prefix P --lo N --hi N

WHY THIS EXISTS (R2-068)
========================
A whole-frame phase correlation returns ONE translation for the whole picture.
A tracking shot does not have one. Measured on frames 804->805 of the fixed
beat-2 seam, 960x540, block by block: image motion runs smoothly from +8 px at
the left of frame to +40 px at the right, with one block at -28 px top left,
because the camera dollies past a room whose contents sit at every depth from
about 4 m to about 22 m. It is not two halves. It is a depth gradient with a
moving car in it.

What the old estimator did with that:

    tools/frame_motion.py --regions, hand-drawn boxes
        background strip           -23.98 px
        subject box                +36.03 px
        floor strip                +41.23 px
    whole frame, full resolution   +12.98 px      the motion of nothing
    whole frame, 320-wide          -13.50 px      same frames, same estimator
    whole frame, 240-wide          +15.99 px      ...and the answer changes sign
                                                  with the downsample factor

and the 0.29 px/frame in the defect log is the MEDIAN of |whole-frame motion|
over the 84 pairs of seam_after, printed at the 320-wide analysis scale without
rescaling. Rescaled to the 960 px the frames actually are, it is 0.86. The block
field over the same 84 pairs gives a median image speed of 4.33 px and a median
block-to-block spread of 11.81 px. So the old headline figure is low by 3x from
the missing rescale and by another 5x from averaging a gradient down to a peak.

WHAT THIS MEASURES INSTEAD
==========================
The frame is covered with overlapping blocks on a fixed grid. Each block is
phase-correlated on its own, so a block that sees only background reports the
background and a block that sees only the car reports the car. Per frame pair:

    field       (dx, dy, valid) for every block, in FULL-RESOLUTION pixels
    dominant    the motion of the largest coherent cluster of blocks
    secondary   the motion of the next cluster, if one exists at all
    shear       |secondary - dominant| -- 0 on a locked-off shot, large on a
                tracking shot, and THE number that says which one you have
    coverage    fraction of blocks that produced a usable estimate

READ `dominant` WITH `dominant_frac`. On the opposed-motion control it holds
80% of the blocks and means what it says. On real frames 804->805 of the seam it
holds 19%, and secondary another 19%, because the picture there is a CONTINUUM
of depths rather than two rigid things -- the two clusters are then just two
samples of a gradient, and `spread_dx` (35.3 px on that frame) is the honest
summary. An instrument that reported only `dominant` would have replaced one
confident wrong number with another.

`dominant` and `secondary` are named by BLOCK COUNT, not by position in frame.
Calling the top strip "background" and a centre box "the subject" -- which is
what tools/frame_motion.py --regions does -- is a fixed idiom that is true of
one beat and false of the rest of the film: the car does not stay in the middle
of the frame for 2,978 frames.

A MEASURED LIMIT
================
On the beat-5 720p frames in work/seq_b5_1900 the field splits into blocks at
about 0 px and blocks at about +48 px. Brute-force minimum-|diff| search over
+/-30 analysis px was run on eight of those blocks as a check that shares no
code with the phase correlation: six agreed with it, including four of the
zeros, which are genuinely static. Two did not -- blocks reporting -0.19 and
-0.33 px whose true shifts are +51 and +9 px. So on heavily motion-blurred
720p content roughly a quarter of blocks can lose a large motion to a competing
zero peak, and the median speed of such a frame (0.66 px) should be read
together with its spread (51.9 px), which is what says the frame does not have
one motion in it. NOT FIXED; measured and stated.

REFUSAL
=======
A block with no texture, or whose correlation peak is not distinct, or whose
measured shift does not reduce the block's own frame-to-frame difference, is
INVALID and contributes nothing. If fewer than MIN_VALID_FRAC of blocks are
valid the whole pair is REFUSED and reports NaN. An instrument that always
returns a number is how R2-068 survived: every consumer must be able to see
"not measured" and say so.

The residual is not "did the shift reduce the difference" but "did the measured
shift beat a WRONG shift with the same interpolation". Two earlier versions of
that test were wrong in opposite directions -- one refused all slow motion, the
other accepted pure noise -- and both are written up in block_residual, because
each of them would have switched the instrument off somewhere without saying so.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys

import numpy as np

# --- geometry of the analysis -------------------------------------------------
ANALYSIS_W = 480      # frames are box-downsampled by an INTEGER factor to about
                      # this width before blocks are cut, so 960, 1280, 1920 and
                      # 3840 all land on a comparable block-to-content scale.
BLOCK = 96            # px at the analysis scale. Wraparound in the correlation
                      # aliases shifts beyond BLOCK/2, so one block measures
                      # +/-48 analysis px = +/-96 px at 960 wide and +/-192 px
                      # at 1920. The largest per-region motion measured anywhere
                      # in this film so far is 70.7 px at 960 (seam f810 floor).
GRID_Y, GRID_X = 6, 10   # 60 blocks, overlapping. Overlap makes neighbouring
                         # estimates correlated, which costs nothing here: the
                         # summaries are medians and cluster counts, not sums.

# --- validity thresholds ------------------------------------------------------
# Each is set from a distribution measured on this project's own frames; run
# --calibrate to reprint them. Figures below are over 5,040 blocks of
# seam_after f748-832 (960x540) and 120 blocks of render/breach_f9 (1920x1080).
TEX_MIN_STD = 0.010   # block luma std. MEASURED: the flattest real block on the
                      # seam is 0.079 and on breach_f9 0.027, so this rejects
                      # nothing real; it exists for a genuinely blank block,
                      # which has no structure to correlate at all.
PSR_MIN = 4.0         # correlation peak height in sigmas of its own surface.
                      # MEASURED: real p05 = 8.8 (seam) / 8.0 (breach), min 4.4.
RESID_MAX = 0.90      # the measured shift must beat a wrong shift by 10%; see
                      # block_residual for what the ratio is against. MEASURED
                      # distributions of that ratio:
                      #   two independent noise fields   p05 0.980  p50 0.989
                      #   real seam frames, 5,040 blocks p50 0.221  p95 0.667
                      #   render/breach_f9 at 1920       p50 0.847  p95 1.264
                      #   the opposed-motion control     p50 0.077
                      # 0.90 sits below every noise block and above 95% of real
                      # seam blocks. The breach stills sit high because an
                      # explosion is genuinely not a translation, and losing a
                      # fifth of those blocks is the correct outcome.
MIN_VALID_FRAC = 0.30 # below this the pair is refused outright.

# --- clustering ---------------------------------------------------------------
CLUSTER_R = 1.5       # analysis px: vectors within this of each other are one
                      # motion. Sub-pixel scatter inside one rigid region is
                      # smaller than this; two rigid regions are further apart.
MODE_SEP = 3.0        # analysis px: a second cluster must be at least this far
                      # from the first to be a DIFFERENT motion rather than the
                      # tail of the first.
MIN_MODE_FRAC = 0.12  # ...and must hold this fraction of the valid blocks.

NOISE_SIGMA = (4.0 / 255.0) / 4.0   # peak ~= the measured 4/255 renderer floor


# ---------------------------------------------------------------------------
# frame IO and the analysis pyramid
# ---------------------------------------------------------------------------

def load_luma(path):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    a = np.asarray(im, dtype=np.float32) / 255.0
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def downsample_int(a, target_w=ANALYSIS_W):
    """Integer box-downsample. Returns (image, factor)."""
    h, w = a.shape
    k = max(1, int(round(w / float(target_w))))
    if k == 1:
        return a, 1
    hh, ww = (h // k) * k, (w // k) * k
    return a[:hh, :ww].reshape(hh // k, k, ww // k, k).mean(axis=(1, 3)), k


def block_centres(h, w, block=BLOCK, gy=GRID_Y, gx=GRID_X):
    """Top-left corners of the block grid, clamped to the frame."""
    bh, bw = min(block, h), min(block, w)
    ys = (np.linspace(0, h - bh, gy) if gy > 1 else np.array([(h - bh) / 2.0]))
    xs = (np.linspace(0, w - bw, gx) if gx > 1 else np.array([(w - bw) / 2.0]))
    return [(int(round(y)), int(round(x)), bh, bw)
            for y in ys for x in xs]


_HANN = {}


def _hann(bh, bw):
    key = (bh, bw)
    if key not in _HANN:
        _HANN[key] = np.outer(np.hanning(bh), np.hanning(bw)).astype(np.float32)
    return _HANN[key]


def _stack(img, cells):
    return np.stack([img[y:y + bh, x:x + bw] for (y, x, bh, bw) in cells])


def block_shifts(A_blocks, B_blocks):
    """Phase correlation on a STACK of blocks at once.

    Returns (dx, dy, psr) arrays, in ANALYSIS pixels, for the motion FROM the
    A block TO the B block. The sign is verified against a known synthetic
    shift by --selftest, because continuity_gate's phase_shift() shipped with a
    docstring claiming one sign and code returning the other.

    psr is the peak height in standard deviations of the rest of the
    correlation surface: a single rigid motion gives one tall spike, a block
    straddling two motions gives two shorter ones and psr falls.
    """
    n, bh, bw = A_blocks.shape
    win = _hann(bh, bw)
    a = (A_blocks - A_blocks.mean(axis=(1, 2), keepdims=True)) * win
    b = (B_blocks - B_blocks.mean(axis=(1, 2), keepdims=True)) * win
    A = np.fft.rfft2(a, axes=(1, 2))
    B = np.fft.rfft2(b, axes=(1, 2))
    R = A * np.conj(B)
    m = np.abs(R)
    R = np.divide(R, m, out=np.zeros_like(R), where=m > 1e-12)
    c = np.fft.irfft2(R, s=(bh, bw), axes=(1, 2))

    flat = c.reshape(n, -1)
    pk = np.argmax(flat, axis=1)
    iy, ix = np.divmod(pk, bw)
    peak = flat[np.arange(n), pk]
    mu, sd = flat.mean(axis=1), flat.std(axis=1)
    psr = np.where(sd > 1e-12, (peak - mu) / np.maximum(sd, 1e-12), 0.0)

    def sub(vals_m1, vals_0, vals_p1):
        d = vals_m1 - 2 * vals_0 + vals_p1
        num = 0.5 * (vals_m1 - vals_p1)
        return np.divide(num, d, out=np.zeros_like(num),
                         where=np.abs(d) > 1e-12)

    ar = np.arange(n)
    dy = iy + sub(c[ar, (iy - 1) % bh, ix], c[ar, iy, ix], c[ar, (iy + 1) % bh, ix])
    dx = ix + sub(c[ar, iy, (ix - 1) % bw], c[ar, iy, ix], c[ar, iy, (ix + 1) % bw])
    dy = np.where(dy > bh / 2, dy - bh, dy)
    dx = np.where(dx > bw / 2, dx - bw, dx)
    return -dx, -dy, psr


def _shift_bilinear(a, dy, dx):
    iy, ix = int(math.floor(dy)), int(math.floor(dx))
    ry, rx = dy - iy, dx - ix
    r00 = np.roll(np.roll(a, iy, axis=0), ix, axis=1)
    r01 = np.roll(r00, 1, axis=1)
    r10 = np.roll(r00, 1, axis=0)
    r11 = np.roll(r10, 1, axis=1)
    return ((1 - ry) * (1 - rx) * r00 + (1 - ry) * rx * r01
            + ry * (1 - rx) * r10 + ry * rx * r11)


DECOY = 4.0           # analysis px: how far the null-hypothesis shift sits
                      # from the measured one. See block_residual.


def block_residual(a, b, dx, dy):
    """How much better the MEASURED shift explains b than a WRONG shift does.

    Two earlier versions of this were wrong in opposite directions and both are
    worth recording, because each would have disabled the instrument somewhere:

      1. Rounding the shift to whole pixels and dividing by the unshifted
         difference. A block moving 0.4 px/frame was shifted by zero, the ratio
         came back at exactly 1.000, and the block was discarded -- so the
         estimator refused every slow pan, including the 45-frame approach at
         the head of the beat-2 seam and the whole synthetic control substrate.

      2. Shifting at sub-pixel precision but still dividing by the UNSHIFTED
         difference. Bilinear interpolation smooths, and smoothing lowers the
         difference against anything -- so two independent noise fields, which
         have no motion at all, scored 0.6 and were accepted. Measured: the
         refusal control returned a confident (+10.3, +30.1) px.

    So the denominator is now the same shift displaced by DECOY pixels, keeping
    the identical fractional part and therefore the identical amount of
    interpolation smoothing. What is left in the ratio is only whether THIS
    displacement is better than a neighbouring one, which is the question.
    """
    h = int(math.ceil(abs(dy) + DECOY)) + 1
    w = int(math.ceil(abs(dx) + DECOY)) + 1
    if 2 * h >= a.shape[0] or 2 * w >= a.shape[1]:
        return float("inf")
    core = (slice(h, -h), slice(w, -w))
    after = float(np.abs(b[core] - _shift_bilinear(a, dy, dx)[core]).mean())
    null = min(float(np.abs(b[core] - _shift_bilinear(a, dy + DECOY, dx + DECOY)[core]).mean()),
               float(np.abs(b[core] - _shift_bilinear(a, dy - DECOY, dx - DECOY)[core]).mean()))
    return after / null if null > 1e-12 else float("inf")


# ---------------------------------------------------------------------------
# the field
# ---------------------------------------------------------------------------

def motion_field(a_full, b_full, target_w=ANALYSIS_W, diag=False):
    """The block motion field between two full-resolution luma frames.

    Every pixel figure returned is in FULL-RESOLUTION pixels of the input
    frames, not of the internal analysis scale.
    """
    a, k = downsample_int(a_full, target_w)
    b, _ = downsample_int(b_full, target_w)
    cells = block_centres(*a.shape)
    n = len(cells)
    AB, BB = _stack(a, cells), _stack(b, cells)

    std = np.maximum(AB.std(axis=(1, 2)), BB.std(axis=(1, 2)))
    ddx, ddy, psr = block_shifts(AB, BB)

    dx = np.full(n, np.nan)
    dy = np.full(n, np.nan)
    res = np.full(n, np.nan)
    for j in range(n):
        if std[j] < TEX_MIN_STD:
            continue
        if psr[j] < PSR_MIN:
            continue
        r = block_residual(AB[j], BB[j], ddx[j], ddy[j])
        res[j] = r
        if not (r < RESID_MAX):
            continue
        dx[j], dy[j] = ddx[j], ddy[j]

    valid = np.isfinite(dx)
    out = {"scale": int(k), "n_blocks": n, "n_valid": int(valid.sum()),
           "coverage": float(valid.mean()),
           "refused": False, "why": None,
           "speed_med": float("nan"), "speed_p90": float("nan"),
           "spread_dx": float("nan"), "spread_dy": float("nan"),
           "dominant": (float("nan"), float("nan")), "dominant_frac": 0.0,
           "secondary": None, "secondary_frac": 0.0, "shear": float("nan"),
           "block_dx": dx * k, "block_dy": dy * k, "block_valid": valid,
           "block_xy": cells}
    if diag:
        out.update({"block_psr": psr, "block_resid": res, "block_std": std})

    if valid.sum() < MIN_VALID_FRAC * n:
        out["refused"] = True
        out["why"] = (f"only {int(valid.sum())} of {n} blocks produced a usable "
                      f"estimate ({valid.mean()*100:.0f}% < "
                      f"{MIN_VALID_FRAC*100:.0f}%): too little texture, or no "
                      f"distinct correlation peak, or the shift did not reduce "
                      f"the block's own difference")
        return out

    v = np.stack([dx[valid], dy[valid]], axis=1)

    # The headline scalars. MEASURED on this film's own frames (seam f804->805,
    # dumped block by block): the picture is NOT two rigid halves. Block motion
    # runs smoothly from +8 px on the left of frame to +39 px on the right with
    # one -28 px block at top left, because the camera dollies past a room whose
    # contents are at every depth from ~4 m to ~22 m. So the honest per-frame
    # summary is a robust CENTRE and a SPREAD of the block distribution, not a
    # single translation -- and `spread_dx` is the number that says whether the
    # frame has one motion in it or several.
    mag = np.hypot(v[:, 0], v[:, 1])
    out["speed_med"] = float(np.median(mag)) * k
    out["speed_p90"] = float(np.percentile(mag, 90)) * k
    out["spread_dx"] = float(np.percentile(v[:, 0], 90) - np.percentile(v[:, 0], 10)) * k
    out["spread_dy"] = float(np.percentile(v[:, 1], 90) - np.percentile(v[:, 1], 10)) * k

    d1, f1 = _mode(v, CLUSTER_R)
    rest = v[np.linalg.norm(v - d1, axis=1) > MODE_SEP]
    sec, f2 = None, 0.0
    if len(rest) >= MIN_MODE_FRAC * len(v):
        d2, f2r = _mode(rest, CLUSTER_R)
        f2 = f2r * len(rest) / len(v)
        if f2 >= MIN_MODE_FRAC and np.linalg.norm(d2 - d1) >= MODE_SEP:
            sec = d2
    out["dominant"] = (float(d1[0]) * k, float(d1[1]) * k)
    out["dominant_frac"] = float(f1)
    if sec is not None:
        out["secondary"] = (float(sec[0]) * k, float(sec[1]) * k)
        out["secondary_frac"] = float(f2)
        out["shear"] = float(np.linalg.norm(sec - d1)) * k
    else:
        out["shear"] = 0.0
    return out


def _mode(v, radius):
    """The densest cluster of 2-D vectors: the vector with the most neighbours
    within `radius`, refined to the mean of those neighbours."""
    d = np.linalg.norm(v[:, None, :] - v[None, :, :], axis=2)
    i = int(np.argmax((d <= radius).sum(axis=1)))
    members = d[i] <= radius
    return v[members].mean(axis=0), float(members.mean())


def field_summary(r):
    """The scalars a consumer keeps: never one number where the picture has
    several. `speed_med` is the typical image speed and is the only one of
    these that is a fair replacement for the old single translation."""
    dom = r["dominant"]
    return {
        "refused": bool(r["refused"]),
        "coverage": r["coverage"],
        "speed_med": r["speed_med"], "speed_p90": r["speed_p90"],
        "spread_dx": r["spread_dx"], "spread_dy": r["spread_dy"],
        "dom_dx": dom[0], "dom_dy": dom[1],
        "dom_mag": math.hypot(dom[0], dom[1]) if np.isfinite(dom[0]) else float("nan"),
        "dom_frac": r["dominant_frac"],
        "sec_dx": r["secondary"][0] if r["secondary"] else float("nan"),
        "sec_dy": r["secondary"][1] if r["secondary"] else float("nan"),
        "sec_mag": (math.hypot(*r["secondary"]) if r["secondary"] else float("nan")),
        "sec_frac": r["secondary_frac"],
        "shear": r["shear"],
    }


def block_accel(prev_field, cur_field):
    """|v_i - v_{i-1}| per block, over blocks valid in BOTH frames.

    This is the quantity a camera kink actually moves. A kink in the camera
    path changes every block's velocity at once whatever depth it is at, so the
    MEDIAN of this over blocks is a camera-path statistic; a kink in one
    object's animation moves only the blocks that object covers, so the MAX is
    a local statistic. Neither needs the field to be clustered, which matters
    because on this film the field is a depth gradient, not two rigid halves.
    """
    if prev_field is None or cur_field is None:
        return None
    if prev_field["block_dx"].shape != cur_field["block_dx"].shape:
        return None
    if prev_field["refused"] or cur_field["refused"]:
        return None
    both = prev_field["block_valid"] & cur_field["block_valid"]
    if both.sum() < MIN_VALID_FRAC * prev_field["n_blocks"]:
        return None
    a = np.hypot(cur_field["block_dx"][both] - prev_field["block_dx"][both],
                 cur_field["block_dy"][both] - prev_field["block_dy"][both])
    return {"n": int(both.sum()), "med": float(np.median(a)),
            "max": float(a.max()),
            "n_over_med3": int((a > 3.0 * max(np.median(a), 1e-6)).sum())}


# ---------------------------------------------------------------------------
# sequences
# ---------------------------------------------------------------------------

def find_pair_paths(d, prefix, lo, hi):
    out = []
    for f in range(lo, hi + 1):
        hits = glob.glob(os.path.join(d, f"{prefix}*{f:06d}.png"))
        if hits:
            out.append((f, sorted(hits)[0]))
    return out


def sequence_field(d, prefix, lo, hi, diag=False):
    rows, prev, prevf = {}, None, None
    for f, p in find_pair_paths(d, prefix, lo, hi):
        cur = load_luma(p)
        if prev is not None and f == prevf + 1:
            rows[f] = motion_field(prev, cur, diag=diag)
        prev, prevf = cur, f
    return rows


# ---------------------------------------------------------------------------
# CONTROLS -- everything here is synthesised procedurally or read from this
# project's own renders. Nothing is downloaded.
# ---------------------------------------------------------------------------

def _fractal(h, w, seed=7,
             octaves=((4, .5), (8, .28), (16, .15), (32, .09), (64, .05))):
    rng = np.random.default_rng(seed)
    tex = np.zeros((h, w), dtype=np.float32)
    for octv, amp in octaves:
        small = rng.random((octv, octv)).astype(np.float32)
        ys = np.clip(np.linspace(0, octv - 1, h).astype(int), 0, octv - 1)
        xs = np.clip(np.linspace(0, octv - 1, w).astype(int), 0, octv - 1)
        big = small[ys][:, xs]
        k = np.ones((3, 3), np.float32) / 9.0
        for _ in range(2):
            p = np.pad(big, 1, mode="edge")
            big = sum(p[i:i + h, j:j + w] * k[i, j] for i in range(3) for j in range(3))
        tex += amp * big
    return (tex - tex.min()) / (tex.max() - tex.min())


def _sample(tex, h, w, oy, ox):
    """Bilinear crop of `tex` at a sub-pixel offset. Sampling FURTHER ALONG the
    texture makes content appear to move BACKWARDS, so a caller that wants
    content to move +d asks for offset -d."""
    iy, ix = int(math.floor(oy)), int(math.floor(ox))
    ry, rx = oy - iy, ox - ix
    return ((1 - ry) * (1 - rx) * tex[iy:iy + h, ix:ix + w]
            + (1 - ry) * rx * tex[iy:iy + h, ix + 1:ix + 1 + w]
            + ry * (1 - rx) * tex[iy + 1:iy + 1 + h, ix:ix + w]
            + ry * rx * tex[iy + 1:iy + 1 + h, ix + 1:ix + 1 + w])


def control_opposed(bg_dx=-24.0, fg_dx=+36.0, h=540, w=960, seed=11,
                    box=(0.37, 0.71, 0.31, 0.73)):
    """The input that fooled the old estimator: background one way, subject the
    other, at the amplitudes measured on frames 804->805 of the real seam.

    Returns (frame_a, frame_b, subject_area_fraction).
    """
    rng = np.random.default_rng(seed)
    pad = 200
    bg = _fractal(h + 2 * pad, w + 2 * pad, seed=seed)
    fg = _fractal(h + 2 * pad, w + 2 * pad, seed=seed + 1,
                  octaves=((6, .5), (12, .3), (24, .2), (48, .12)))
    y0, y1, x0, x1 = box
    ys, ye, xs, xe = int(y0 * h), int(y1 * h), int(x0 * w), int(x1 * w)

    def frame(t):
        a = _sample(bg, h, w, pad, pad - bg_dx * t).copy()
        sub = _sample(fg, ye - ys, xe - xs, pad, pad - fg_dx * t)
        a[ys:ye, xs:xe] = 0.25 + 0.6 * sub
        return np.clip(a + rng.normal(0, NOISE_SIGMA, a.shape), 0, 1).astype(np.float32)

    return frame(0.0), frame(1.0), (ye - ys) * (xe - xs) / float(h * w)


def control_static(h=540, w=960, seed=13):
    """A genuinely static pair: the same picture twice, with INDEPENDENT
    renderer noise on each. The correct answer is zero and the estimator must
    not manufacture motion out of the noise."""
    rng = np.random.default_rng(seed)
    base = _fractal(h, w, seed=seed)
    a = np.clip(base + rng.normal(0, NOISE_SIGMA, base.shape), 0, 1).astype(np.float32)
    b = np.clip(base + rng.normal(0, NOISE_SIGMA, base.shape), 0, 1).astype(np.float32)
    return a, b


def old_whole_frame(a, b, target_w=256):
    """The estimator R2-068 is about, reproduced so its failure stays checkable.

    continuity_gate's downsample used FLOOR division (960 // 256 = 3, giving a
    320-wide analysis image), not rounding, and that detail is load-bearing: on
    frames 804->805 of the seam this function returns -13.50 px at k=3 and
    +15.99 px at k=4. Same estimator, same two frames, answer flips sign with
    the downsample factor -- which is what "the peak of a correlation that never
    fitted" looks like when you vary an implementation detail.

    Returned in FULL-RESOLUTION px, with the sign convention this file uses --
    continuity_gate returned the negative of this and printed it WITHOUT the
    factor k, i.e. at the analysis scale.
    """
    if target_w is None:
        aa, k, bb = a, 1, b
    else:
        k = max(1, a.shape[1] // target_w)          # floor, as shipped
        hh, ww = (a.shape[0] // k) * k, (a.shape[1] // k) * k
        aa = a[:hh, :ww].reshape(hh // k, k, ww // k, k).mean(axis=(1, 3))
        bb = b[:hh, :ww].reshape(hh // k, k, ww // k, k).mean(axis=(1, 3))
    h, w = aa.shape
    wy = np.hanning(h).astype(np.float32)[:, None]
    wx = np.hanning(w).astype(np.float32)[None, :]
    A = np.fft.rfft2((aa - aa.mean()) * wy * wx)
    B = np.fft.rfft2((bb - bb.mean()) * wy * wx)
    R = A * np.conj(B)
    m = np.abs(R)
    R = np.divide(R, m, out=np.zeros_like(R), where=m > 1e-12)
    r = np.fft.irfft2(R, s=aa.shape)
    iy, ix = np.unravel_index(int(np.argmax(r)), r.shape)

    def sub(line, i, n):                    # the shipped parabolic refinement
        im1, ip1 = line[(i - 1) % n], line[(i + 1) % n]
        d = im1 - 2 * line[i] + ip1
        return 0.0 if abs(d) < 1e-12 else 0.5 * (im1 - ip1) / d

    dy = iy + sub(r[:, ix], iy, h)
    dx = ix + sub(r[iy, :], ix, w)
    if dy > h / 2:
        dy -= h
    if dx > w / 2:
        dx -= w
    return -dx * k, -dy * k, k


def _dsn(x):
    return "-" if x is None else f"{x:+8.2f}"


# ---------------------------------------------------------------------------
# SELFTEST -- three controls, plus a sign control, plus the old estimator's
# answer printed beside the new one on every synthetic case.
# ---------------------------------------------------------------------------

IDIOM_SEQ = "/home/zany/vast-render/out/seq/seam_after"
IDIOM_PREFIX = "seam_after"
IDIOM_PATH = "/home/zany/f1-round2/work/seam/prev_after_path.json"
IDIOM_LO, IDIOM_HI = 748, 832
BREACH_DIR = "/home/zany/f1-round2/render/breach_f9"


def _quat_matrix(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def geometry_prediction(path_rows, f_prev, f_cur, width, sensor=36.0):
    """From the camera path alone: the image shift a point at infinity gets from
    the camera's ROTATION, and the parallax coefficient f*|T_x| that divides by
    depth. Shares no code with the estimator, so it is an independent check.

    Sign convention is NOT asserted here; both branches are returned and the
    caller picks the one that yields positive depths. That is a measurement.
    """
    p1, p2 = path_rows[f_prev], path_rows[f_cur]
    R1, R2 = _quat_matrix(p1["q"]), _quat_matrix(p2["q"])
    fpx = width * p1["lens"] / sensor
    dR = R1.T @ R2
    ang = math.acos(max(-1.0, min(1.0, (np.trace(dR) - 1) / 2)))
    if ang > 1e-9:
        ax = np.array([dR[2, 1] - dR[1, 2], dR[0, 2] - dR[2, 0],
                       dR[1, 0] - dR[0, 1]]) / (2 * math.sin(ang))
    else:
        ax = np.zeros(3)
    theta = ax * ang
    T = R1.T @ (np.array(p2["p"]) - np.array(p1["p"]))
    # Which of the four sign combinations is physical was decided by MEASUREMENT
    # on f805, not by algebra: only rot_dx = +f*theta_y with par_coeff = -f*T_x
    # puts every block at a positive depth (4.1-22.2 m, a showroom). The other
    # three put most or all of the picture behind the camera.
    return {"fpx": fpx, "rot_dx": fpx * theta[1], "par_coeff": -fpx * float(T[0]),
            "theta_y": float(theta[1]), "T_x": float(T[0])}


def selftest(verbose=False):
    rows = []

    def add(name, ok, why, detail):
        rows.append({"control": name, "ok": bool(ok), "why": why, "detail": detail})
        print(f"  {name:<22} {'OK  ' if ok else 'MISS <-- '}{detail}")
        if not ok:
            print(f"  {'':<22} expected: {why}")

    print("\n=== SIGN CONTROL — every phase-correlation sign here is measured, "
          "not assumed")
    tex = _fractal(400, 700, seed=3)
    for S, axis in ((7, "x"), (5, "y")):
        if axis == "x":
            A = np.stack([tex[100:300, 100:300].astype(np.float32)])
            B = np.stack([tex[100:300, 100 - S:300 - S].astype(np.float32)])
        else:
            A = np.stack([tex[100:300, 100:300].astype(np.float32)])
            B = np.stack([tex[100 - S:300 - S, 100:300].astype(np.float32)])
        dx, dy, _ = block_shifts(A, B)
        got = dx[0] if axis == "x" else dy[0]
        add(f"sign_{axis}", abs(got - S) < 0.05,
            f"a known +{S} px move of the content must read +{S}",
            f"content moved +{S} px, estimator says {got:+.3f} px")

    print("\n=== POSITIVE CONTROL — opposed foreground/background, the input "
          "that fooled the old estimator")
    a, b, frac = control_opposed(bg_dx=-24.0, fg_dx=+36.0)
    odx256, ody256, k256 = old_whole_frame(a, b, 256)
    odxf, odyf, _ = old_whole_frame(a, b, None)
    r = motion_field(a, b)
    print(f"    truth:  background -24.00 px over {100*(1-frac):.0f}% of frame, "
          f"subject +36.00 px over {100*frac:.0f}%")
    print(f"    OLD whole-frame, continuity_gate's 256-wide scale: "
          f"dx={odx256:+.2f} px  (reported unscaled as {odx256/k256:+.2f})")
    print(f"    OLD whole-frame, full resolution:                  dx={odxf:+.2f} px")
    print(f"    NEW dominant  {r['dominant'][0]:+.2f} px over "
          f"{r['dominant_frac']*100:.0f}% of blocks;  secondary "
          f"{r['secondary'][0] if r['secondary'] else float('nan'):+.2f} px over "
          f"{r['secondary_frac']*100:.0f}%;  shear {r['shear']:.2f} px; "
          f"coverage {r['coverage']*100:.0f}%")
    # What the old estimator gets WRONG here is not its accuracy -- it locks
    # cleanly onto one of the two peaks -- but that it reports the motion of the
    # minority of the picture as the motion of all of it, with no second number
    # and no signal that a second motion exists. The sweep printed below shows
    # the answer JUMPING between the two truths as the subject grows.
    old_ok = abs(odx256 - (-24.0)) > 5.0
    add("positive_old_fails", old_ok,
        "the OLD estimator must fail to report the motion of the 86% of the "
        "frame that is background",
        f"background is -24.00 over 86% of the frame; old says {odx256:+.2f} "
        f"(and offers no second number at all)")
    print("    the old estimator's answer against subject area, same two "
          "motions throughout:")
    print("      subject%   old whole-frame     new dominant / secondary")
    for wf in (0.05, 0.10, 0.12, 0.20, 0.40, 0.75):
        sd = math.sqrt(wf)
        bx = (0.5 - sd / 2, 0.5 + sd / 2, 0.5 - sd / 2, 0.5 + sd / 2)
        aa, bb, fr = control_opposed(box=bx)
        oo, _, _ = old_whole_frame(aa, bb, 256)
        rr = motion_field(aa, bb)
        ss = rr["secondary"][0] if rr["secondary"] else float("nan")
        print(f"      {fr*100:6.0f}     {oo:+12.2f}     {rr['dominant'][0]:+8.2f} "
              f"/ {ss:+8.2f}")
    got = sorted([r["dominant"][0], r["secondary"][0] if r["secondary"] else float("nan")])
    ok = (r["secondary"] is not None
          and abs(got[0] - (-24.0)) < 1.0 and abs(got[1] - 36.0) < 1.0)
    add("positive_new_recovers", ok,
        "the NEW estimator must recover BOTH motions to within 1 px",
        f"new is {got[0]:+.2f} and {got[1]:+.2f} px against -24.00 and +36.00")

    print("\n=== NEGATIVE CONTROL — a genuinely static pair, correct answer ~0")
    a, b = control_static()
    r = motion_field(a, b)
    odx, _, _ = old_whole_frame(a, b, 256)
    print(f"    OLD whole-frame dx={odx:+.3f} px;  NEW dominant "
          f"{r['dominant'][0]:+.3f},{r['dominant'][1]:+.3f} px, secondary "
          f"{r['secondary']}, spread_dx {r['spread_dx']:.3f}, "
          f"coverage {r['coverage']*100:.0f}%")
    ok = (not r["refused"] and abs(r["dominant"][0]) < 0.25
          and abs(r["dominant"][1]) < 0.25 and r["secondary"] is None
          and r["speed_med"] < 0.25)
    add("negative_static", ok,
        "must return ~0 with no second mode, and must NOT refuse",
        f"dominant ({r['dominant'][0]:+.3f},{r['dominant'][1]:+.3f}), "
        f"speed_med {r['speed_med']:.3f}, secondary "
        f"{'none' if r['secondary'] is None else 'INVENTED'}")

    print("\n=== IDIOM CONTROL — real frames from this film, which are known good")
    if not os.path.isdir(IDIOM_SEQ):
        add("idiom_seam", False, "the real seam frames must be present",
            f"{IDIOM_SEQ} is missing")
    else:
        R = sequence_field(IDIOM_SEQ, IDIOM_PREFIX, IDIOM_LO, IDIOM_HI)
        ref = [f for f, x in R.items() if x["refused"]]
        cov = np.array([x["coverage"] for x in R.values()])
        print(f"    {len(R)} real pairs, coverage min {cov.min():.2f} "
              f"median {np.median(cov):.2f} max {cov.max():.2f}")
        add("idiom_seam_measurable", len(ref) == 0,
            "the estimator must MEASURE known-good film frames, not refuse them",
            f"{len(ref)} of {len(R)} real pairs refused"
            + (f" ({ref[:8]})" if ref else ""))

        if os.path.exists(IDIOM_PATH):
            path = {p["f"]: p for p in json.load(open(IDIOM_PATH))["path"]}
            width = 960
            bad, tot, depths = 0, 0, []
            for f in range(802, 812):
                if f not in R or R[f]["refused"]:
                    continue
                g = geometry_prediction(path, f - 1, f, width)
                bdx = R[f]["block_dx"][R[f]["block_valid"]]
                # The camera's rotation is one constant offset for every block,
                # whatever depth it is at; the rest is parallax, and parallax
                # must divide by a POSITIVE depth. Nothing in the estimator
                # knows the camera path, so this is an independent check.
                d = g["par_coeff"] / (bdx - g["rot_dx"])
                depths.extend(d.tolist())
                tot += len(d)
                bad += int((d <= 0).sum())
            depths = np.array(depths)
            inr = float(((depths > 1.0) & (depths < 40.0)).mean())
            print(f"    camera-path cross-check on {tot} block estimates, f802-811: "
                  f"implied depth min {depths.min():.1f} m, "
                  f"median {np.median(depths):.1f} m, max {depths.max():.1f} m")
            # Not 100%: there is a CAR in the frame and it moves in the world,
            # so blocks covering it are not static scenery and cannot be
            # required to fit a static-parallax model. 1% is the allowance for
            # that and for blocks straddling the car's edge.
            add("idiom_geometry_agrees", bad <= 0.01 * tot and inr > 0.95,
                "at least 99% of blocks must be explained by the camera's own "
                "rotation plus parallax at a POSITIVE, room-sized depth",
                f"{bad}/{tot} blocks need a negative depth; "
                f"{inr*100:.1f}% land in 1-40 m")
        else:
            print(f"    (no camera path at {IDIOM_PATH}; geometry check skipped)")

    fs = {int(x.split("_f")[-1][:4]): x
          for x in glob.glob(os.path.join(BREACH_DIR, "f9_1920_*.png"))}
    pairs = [(f - 1, f) for f in sorted(fs) if f - 1 in fs]
    if pairs:
        cov, ref = [], 0
        for p, c in pairs:
            r = motion_field(load_luma(fs[p]), load_luma(fs[c]))
            cov.append(r["coverage"])
            ref += int(r["refused"])
            print(f"    breach_f9 {p}->{c} @1920: speed_med {r['speed_med']:.1f} px, "
                  f"spread_dx {r['spread_dx']:.1f}, coverage {r['coverage']:.2f}"
                  + ("  REFUSED" if r["refused"] else ""))
        add("idiom_breach_measurable", ref == 0,
            "the breach stills at 1920 are real delivery pixels and must measure",
            f"{ref} of {len(pairs)} refused, coverage min {min(cov):.2f}")

    print("\n=== REFUSAL CONTROL — an input nothing can measure")
    rng = np.random.default_rng(5)
    a = rng.random((540, 960)).astype(np.float32)
    b = rng.random((540, 960)).astype(np.float32)
    r = motion_field(a, b)
    add("refusal_on_noise", r["refused"],
        "two independent noise fields have no motion between them and the "
        "estimator must say so rather than return a number",
        (r["why"] or "")[:88] if r["refused"] else
        f"returned dominant {r['dominant']} instead of refusing")
    flat = np.full((540, 960), 0.5, np.float32)
    r = motion_field(flat, flat + 0.0001)
    add("refusal_on_flat", r["refused"],
        "a textureless pair must be refused, not reported as static",
        (r["why"] or "")[:88] if r["refused"] else "returned a number")

    n_ok = sum(1 for r in rows if r["ok"])
    print(f"\n  {n_ok}/{len(rows)} controls behaved as specified")
    return n_ok == len(rows), rows


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report")
    ap.add_argument("--seq")
    ap.add_argument("--prefix", default="")
    ap.add_argument("--lo", type=int, default=1)
    ap.add_argument("--hi", type=int, default=10 ** 9)
    ap.add_argument("--calibrate", action="store_true",
                    help="print the distributions the validity thresholds are "
                         "set from, on whatever --seq is given")
    a = ap.parse_args()

    if a.selftest:
        ok, rows = selftest()
        if a.report:
            with open(a.report, "w") as fh:
                json.dump({"tool": "image_motion", "controls": rows}, fh, indent=1)
        print(">> STAGE RESULT: " + ("IMAGE_MOTION_CONTROLS_OK" if ok
                                     else "IMAGE_MOTION_CONTROLS_FAIL"))
        sys.exit(0 if ok else 1)

    if not a.seq:
        ap.error("need --seq or --selftest")
    R = sequence_field(a.seq, a.prefix, a.lo, a.hi, diag=a.calibrate)
    if not R:
        print(f">> FAIL: no consecutive frame pairs in {a.seq}")
        sys.exit(2)

    if a.calibrate:
        for key in ("block_std", "block_psr", "block_resid"):
            x = np.concatenate([r[key][np.isfinite(r[key])] for r in R.values()])
            print(f"  {key:12s} n={len(x):6d} min {x.min():9.5f} "
                  f"p05 {np.percentile(x,5):9.5f} p50 {np.percentile(x,50):9.5f} "
                  f"p95 {np.percentile(x,95):9.5f} max {x.max():9.5f}")
        cov = np.array([r["coverage"] for r in R.values()])
        print(f"  coverage     n={len(cov):6d} min {cov.min():9.3f} "
              f"p05 {np.percentile(cov,5):9.3f} p50 {np.median(cov):9.3f} "
              f"p95 {np.percentile(cov,95):9.3f} max {cov.max():9.3f}")
        print(">> STAGE RESULT: IMAGE_MOTION_CALIBRATED")
        return

    print(f"=== BLOCK MOTION FIELD, {len(R)} pairs from {a.seq}")
    print("      f   speed_med  speed_p90   spread_dx   dominant dx,dy   "
          "secondary dx,dy    shear   cov")
    prev = None
    nref = 0
    for f in sorted(R):
        r = R[f]
        if r["refused"]:
            nref += 1
            print(f"  {f:5d}   REFUSED: {r['why']}")
            prev = r
            continue
        s = r["secondary"]
        print(f"  {f:5d} {r['speed_med']:10.2f} {r['speed_p90']:10.2f} "
              f"{r['spread_dx']:11.2f}   {r['dominant'][0]:+7.2f},{r['dominant'][1]:+6.2f}   "
              + (f"{s[0]:+8.2f},{s[1]:+6.2f}" if s else f"{'-':>16}")
              + f" {r['shear']:8.2f} {r['coverage']:5.2f}")
        prev = r
    print(f"  {nref} of {len(R)} pairs refused")
    print(">> STAGE RESULT: " + ("IMAGE_MOTION_OK" if nref < 0.5 * len(R)
                                 else "IMAGE_MOTION_MOSTLY_REFUSED"))


if __name__ == "__main__":
    main()
