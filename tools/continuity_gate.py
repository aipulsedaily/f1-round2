#!/usr/bin/env python3
"""Temporal continuity gate (#37) — defects that only exist ACROSS frames.

A 4K still can show a bevel, a decal edge, a material that reads as plastic. It
can never show a shard that interpenetrates for three frames, a shadow that pops,
a batch seam where two machines rendered adjacent ranges, or a beat that is two
seconds too long. Those live in the differences between frames, and this gate is
the instrument for them.

    python3 tools/continuity_gate.py --seq DIR [--frames A-B] [--report OUT.json]
    python3 tools/continuity_gate.py --selftest            # positive controls
    python3 tools/continuity_gate.py --selftest --source DIR   # ... on real frames

WHAT IT LOOKS FOR, and the detector that looks
----------------------------------------------
    D1  pop            a single frame that does not belong between its neighbours
    D2  flicker        a burst of 2-8 such frames, or a period-2 oscillation
    D3  fireflies      isolated blown pixels that resolve differently per frame
    D4  batch seam     a persistent STEP in level or noise at one frame boundary
    D5  camera kink    an acceleration spike in the frame-to-frame image motion
    D6  stepped time   a held/duplicated frame, or period-2 speed-ramp stutter
    D7  blur/motion    sharpness inconsistent with motion at the same speed
    D8  pacing         measurement, not a verdict: where the film sits still

THE CALIBRATION FLOOR
---------------------
A 4/255 peak per-pixel difference between two renders of the same frame is
renderer noise, not a seam (measured on this project, 2026-08-03). Every
per-pixel threshold here sits above PEAK_NOISE, and every per-frame threshold is
robust-z against the sequence's OWN rolling neighbourhood, so the floor is
re-measured from the data on every run and printed beside the assumed one.

WHY THE VACUITY GUARDS EXIST
----------------------------
On this project a harness once measured a four-day-old blend and returned mean
|diff| 7.69e-06 against a 7.70e-06 noise floor, 0.00 % of pixels, correlation
0.99994 -- a flawless, entirely convincing null. The real answer was 57.50 %.
A null must be PROVEN, not accepted. So this gate refuses (exit 3, VACUOUS)
rather than passing when it cannot see what it claims to check:

    * fewer than MIN_FRAMES frames
    * frame numbers that are not contiguous (a strided sequence has no adjacency,
      so every temporal residual is meaningless -- and would come back clean)
    * a sequence with no motion at all (nothing to be discontinuous)
    * mixed frame dimensions
    * a source directory whose frames it cannot all read

and it stamps every input with tools/provenance.py so a clean report can be
checked against the sequence it claims to describe.

WHERE THE CONTROLS STAND (R2-078)
---------------------------------
    substrate            gate 1.0.0                gate 1.1.0
    synthetic            14/14                     14/14
    real seam frames     13/13, 1 NOT MEASURABLE   14/14

The one that was not measurable was D7_blur_motion: on real frames it reported
"32 usable frames is below the 50 needed for a 15-neighbour speed-matched
baseline", because most frames had no usable motion figure to be matched on. It
now measures, and catches a blur kernel of 3 on the same substrate.

EXIT CODES via tools/gate_exit.py: 0 pass, 1 fail, 2 crash, 3 vacuous.
Never trust $? from a Blender run; this tool is plain CPython and does not
involve Blender at all.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import sys
import sqlite3
import tempfile
from collections import deque

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_exit                                              # noqa: E402
import image_motion                                           # noqa: E402
try:
    import provenance
except Exception:                                             # pragma: no cover
    provenance = None

# 1.1.0: the whole-frame phase-correlation image-motion estimate was replaced
# with tools/image_motion.py's block motion field (R2-068). D5 and D7 and the
# pacing translation figure were all computed from the old number; D1, D2, D3,
# D4 and D6 never touched it and are unchanged.
GATE_VERSION = "continuity_gate/1.1.0"

# ---------------------------------------------------------------------------
# Calibration constants. Every one of these is a measurement or a stated
# assumption, never a knob tuned until the answer looked right.
# ---------------------------------------------------------------------------

PEAK_NOISE = 4.0 / 255.0     # MEASURED on this project: two renders of one frame
                             # peak at 4/255. Anything at or below is the renderer.
HOT_PIXEL = 2.0 * PEAK_NOISE      # a pixel must beat the floor twice over to count
FIREFLY_TEMPORAL = 0.20           # brighter than BOTH temporal neighbours by this
FIREFLY_SPATIAL = 0.15            # ...and than its own 8 spatial neighbours
Z_FAIL = 8.0                      # robust-z for a hard finding
Z_BURST = 4.0                     # lower bar, but only inside a run (D2)
SEAM_SIGMA = 6.0                  # step must beat the flatter side's sigma by this
SEAM_FLATNESS = 0.35              # both sides flat vs the step -> not a fade.
                                  # A pure linear ramp scores exactly 0.50 here,
                                  # so 0.35 excludes fades by construction.
SEAM_WINDOW = 12                  # frames each side of a candidate boundary
ROLL_WINDOW = 12                  # +/- neighbours for every rolling robust-z
MIN_FRAMES = 8                    # below this nothing here has any power
KINK_MIN_ACCEL = 1.0              # px/frame^2 -- below this it is estimator noise
HELD_RATIO = 0.25                 # motion < this * local median  ->  held frame
STUTTER_RATIO = 2.0               # alternating high/low by this  ->  period-2
MOTION_NEIGHBOURS = 15            # k-NN in motion magnitude for the blur check
D7_MIN_FRAMES = 50                # below this the blur/motion baseline has no power
TILE_Y, TILE_X = 9, 16            # the frame is tracked as 144 regional levels, so a
                                  # shard that pops in one corner is not averaged away
TILE_AMP = 2.0 * PEAK_NOISE       # a tile's level must move this much to count
SEAM_COHERENCE = 0.50             # fraction of tiles that must step the SAME way
MAX_BURST = 8                     # a "burst" longer than this is a scene change

TILE_MIN_FRAMES = 48              # below this there is not enough history to
                                  # estimate 144 per-tile scales; the tile route
                                  # reports NOT MEASURED rather than guessing

# Severity is carried on each finding, not implied by the detector, because the
# SAME detector has different authority depending on scope. A whole-frame level
# pop cannot be anything but a defect. A one-tile excursion can equally well be
# a specular highlight sweeping across bodywork -- which is exactly what the
# first version of this gate reported as 25 defects on real footage before the
# frames were looked at. See LOCAL_IS_ADVISORY below.
LOCAL_IS_ADVISORY = True

BEATS_24FPS = [                   # from docs/beat_sheet.json, 24 fps, 1-based
    ("1_assembly", 1, 792),
    ("2_launch", 793, 864),
    ("3_breach", 865, 1056),
    ("4_transit", 1057, 1190),
    ("5_lap", 1191, 2714),
    ("6_ending", 2715, 2978),
]


# ---------------------------------------------------------------------------
# frame IO
# ---------------------------------------------------------------------------

FRAME_RE = re.compile(r"(\d{3,8})\.(?:png|PNG)$")


def find_frames(seq_dir):
    """[(frame_number, path), ...] sorted by frame number."""
    out = []
    for p in sorted(glob.glob(os.path.join(seq_dir, "*.png"))):
        m = FRAME_RE.search(os.path.basename(p))
        if m:
            out.append((int(m.group(1)), p))
    out.sort()
    return out


def load_luma(path):
    """(luma float32 0..1, per-channel means). RGBA and greyscale both fine."""
    from PIL import Image
    with Image.open(path) as im:
        im = im.convert("RGB")
        a = np.asarray(im, dtype=np.float32) / 255.0
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    return lum, (float(a[..., 0].mean()), float(a[..., 1].mean()), float(a[..., 2].mean()))


# ---------------------------------------------------------------------------
# small numerical helpers
# ---------------------------------------------------------------------------

def mad(x):
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return 0.0
    m = np.median(x)
    return float(np.median(np.abs(x - m)) * 1.4826)


def rolling_robust_z(x, window=ROLL_WINDOW, floor=0.0):
    """z of each sample against its own neighbourhood, ITSELF EXCLUDED.

    Excluding the sample is what lets a single huge outlier still score: if it
    contaminated its own baseline it would partly hide itself.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    z = np.zeros(n)
    med = np.zeros(n)
    sig = np.zeros(n)
    for i in range(n):
        lo, hi = max(0, i - window), min(n, i + window + 1)
        w = np.concatenate([x[lo:i], x[i + 1:hi]])
        if w.size < 3:
            continue
        m = float(np.median(w))
        s = max(mad(w), floor)
        med[i], sig[i] = m, s
        z[i] = (x[i] - m) / s if s > 0 else 0.0
    return z, med, sig


def diff_events(x, window=ROLL_WINDOW, z_thr=Z_FAIL, max_span=MAX_BURST,
                amp_floor=0.0):
    """Classify every anomaly in a level series by the SHAPE of its first
    difference. This is the core of the gate, and the reason it can tell a pop
    from a seam from a fade at all.

        pop at i        d[i] = +x  and  d[i+1] = -x        (goes out, comes back)
        burst [i..j]    d[i-1] = +x and d[j] = -x          (span 2..MAX_BURST)
        step at i       d[i] = +x, nothing returns it      (a batch seam)
        fade            no outlier in d anywhere           (the whole ramp is d)

    A fade needs no special case: its first difference is smooth and constant,
    so it produces no outlier and cannot be mistaken for a step. That is why the
    discriminator lives here and not in a threshold.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.size < MIN_FRAMES:
        return []
    d = np.diff(x)
    z, _, _ = rolling_robust_z(d, window=window, floor=1e-12)
    outs = [i for i in range(d.size)
            if abs(z[i]) >= z_thr and abs(d[i]) >= amp_floor]
    used, events = set(), []
    for i in outs:
        if i in used:
            continue
        partner = None
        for j in outs:
            if j <= i or j in used:
                continue
            if j - i > max_span:
                break
            ratio = abs(d[j]) / max(abs(d[i]), 1e-12)
            if np.sign(d[j]) != np.sign(d[i]) and 0.35 <= ratio <= 3.0:
                partner = j
                break
        if partner is not None:
            used.add(i)
            used.add(partner)
            events.append({"kind": "burst", "first": i + 1, "last": partner,
                           "span": partner - i, "amp": float(d[i]),
                           "z": float(abs(z[i]))})
        else:
            used.add(i)
            lo = max(0, i + 1 - window)
            before = float(np.median(x[lo:i + 1]))
            after = float(np.median(x[i + 1:i + 1 + window]))
            events.append({"kind": "step", "first": i + 1, "last": i + 1,
                           "span": 1, "amp": float(d[i]), "z": float(abs(z[i])),
                           "persists": float(after - before)})
    return events


def tile_means(a, ty=TILE_Y, tx=TILE_X):
    h, w = a.shape
    hh, ww = (h // ty) * ty, (w // tx) * tx
    return a[:hh, :ww].reshape(ty, hh // ty, tx, ww // tx).mean(axis=(1, 3)).ravel()


def spatial_neighbour_max(a):
    """Max over the 8 neighbours of each pixel, centre excluded. Streaming
    maximum so only two full-size arrays are alive at once."""
    p = np.pad(a, 1, mode="edge")
    out = None
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            if dy == 1 and dx == 1:
                continue
            sl = p[dy:dy + a.shape[0], dx:dx + a.shape[1]]
            out = sl.copy() if out is None else np.maximum(out, sl, out=out)
    return out


def sharpness(a):
    """Mean |Laplacian| -- falls when a frame is motion-blurred."""
    lap = np.abs(4.0 * a[1:-1, 1:-1] - a[:-2, 1:-1] - a[2:, 1:-1]
                 - a[1:-1, :-2] - a[1:-1, 2:])
    return float(lap.mean())


def phase_shift(a, b):
    """DEPRECATED, R2-068. The whole-frame translation, which is the motion of
    nothing on a tracking shot -- and this implementation returned the NEGATIVE
    of the shift its own docstring claimed, and its callers printed it at the
    downsampled analysis scale rather than in frame pixels.

    Kept only so the defect stays reproducible: tools/image_motion.py's
    --selftest checks its replica against this function. Nothing in this gate
    consumes it any more.
    """
    h, w = a.shape
    wy = np.hanning(h).astype(np.float32)[:, None]
    wx = np.hanning(w).astype(np.float32)[None, :]
    A = np.fft.rfft2((a - a.mean()) * wy * wx)
    B = np.fft.rfft2((b - b.mean()) * wy * wx)
    R = A * np.conj(B)
    mag = np.abs(R)
    R = np.divide(R, mag, out=np.zeros_like(R), where=mag > 1e-12)
    r = np.fft.irfft2(R, s=a.shape)
    iy, ix = np.unravel_index(int(np.argmax(r)), r.shape)

    def sub(c, i, n):                       # parabolic refinement, one axis
        im1, ip1 = c[(i - 1) % n], c[(i + 1) % n]
        d = im1 - 2 * c[i] + ip1
        return 0.0 if abs(d) < 1e-12 else 0.5 * (im1 - ip1) / d

    dy = iy + sub(r[:, ix], iy, h)
    dx = ix + sub(r[iy, :], ix, w)
    if dy > h / 2:
        dy -= h
    if dx > w / 2:
        dx -= w
    return float(dx), float(dy)


def downsample_to(a, target_w=256):
    """DEPRECATED with phase_shift, R2-068/R2-078. Integer box-downsample by
    FLOOR division, so 960 became 320 and every motion figure this gate printed
    was at that scale rather than in frame pixels. Kept only for the replica in
    tools/image_motion.py to be checked against."""
    h, w = a.shape
    if w <= target_w:
        return a
    k = max(1, w // target_w)
    hh, ww = (h // k) * k, (w // k) * k
    return a[:hh, :ww].reshape(hh // k, k, ww // k, k).mean(axis=(1, 3))


def parse_frames_arg(s):
    out = []
    for part in str(s).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part.lstrip("-"):
            a, _, b = part.partition("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return sorted(set(out))


# ---------------------------------------------------------------------------
# measurement pass
# ---------------------------------------------------------------------------

def measure(frames, progress=True):
    """One streaming pass. Returns a dict of per-frame series.

    Only three full-resolution frames are alive at any moment, so a 2,978-frame
    4K sequence costs the same memory as a 3-frame one.
    """
    n = len(frames)
    nums = np.array([f for f, _ in frames])
    s = {k: np.full(n, np.nan) for k in
         ("mean", "sd", "r", "g", "b", "res_mean", "res_p999", "res_hot",
          "firefly", "d_prev", "sharp",
          # --- the image-motion series, from tools/image_motion.py's block
          # field. There is no single "mx"/"my" any more, because a tracking
          # shot does not have one: see R2-068.
          "mmag",        # median |block motion|, FULL-RESOLUTION px/frame
          "mp90",        # 90th percentile of the same
          "mspread",     # p90-p10 of block dx: how much the frame disagrees
                         # with itself. Near 0 = one motion; large = tracking.
          "mcov",        # fraction of blocks that produced an estimate
          "maccel",      # median over blocks of |v_i - v_{i-1}|  (D5)
          "maccel_max",  # max over blocks of the same             (D5, local)
          "mshear")}     # |secondary cluster - dominant cluster|
    s["_motion_refused"] = np.zeros(n, dtype=bool)
    shapes = set()
    tiles = np.full((n, TILE_Y * TILE_X), np.nan)
    win = deque()        # (idx, luma)
    prev_lum = None
    prev_field = None

    for i, (fnum, path) in enumerate(frames):
        lum, (mr, mg, mb) = load_luma(path)
        shapes.add(lum.shape)
        s["mean"][i] = float(lum.mean())
        s["sd"][i] = float(lum.std())
        s["r"][i], s["g"][i], s["b"][i] = mr, mg, mb
        s["sharp"][i] = sharpness(lum)
        tiles[i] = tile_means(lum)

        field = None
        if prev_lum is not None and prev_lum.shape == lum.shape:
            field = image_motion.motion_field(prev_lum, lum)
            if field["refused"]:
                s["_motion_refused"][i] = True
                field = None
            else:
                s["mmag"][i] = field["speed_med"]
                s["mp90"][i] = field["speed_p90"]
                s["mspread"][i] = field["spread_dx"]
                s["mcov"][i] = field["coverage"]
                s["mshear"][i] = field["shear"]
                acc = image_motion.block_accel(prev_field, field)
                if acc is not None:
                    s["maccel"][i] = acc["med"]
                    s["maccel_max"][i] = acc["max"]
        prev_lum = lum
        prev_field = field

        win.append((i, lum))
        if len(win) == 3:
            (ia, a), (ib, b), (ic, c) = win
            s["d_prev"][ib] = float(np.abs(b - a).mean())
            # temporal second difference: real motion is locally linear in time,
            # so a frame that does not belong between its neighbours stands out
            # even when the whole frame is moving fast.
            res = np.abs(b - 0.5 * (a + c))
            s["res_mean"][ib] = float(res.mean())
            s["res_p999"][ib] = float(np.percentile(res, 99.9))
            s["res_hot"][ib] = float((res > HOT_PIXEL).mean())
            excess = b - np.maximum(a, c)
            cand = excess > FIREFLY_TEMPORAL
            if cand.any():
                nb = spatial_neighbour_max(b)
                s["firefly"][ib] = float(np.count_nonzero(cand & ((b - nb) > FIREFLY_SPATIAL)))
            else:
                s["firefly"][ib] = 0.0
            win.popleft()
        if progress and n > 200 and i % 100 == 0:
            print(f"    measured {i}/{n}", file=sys.stderr, flush=True)

    # d_prev for the last frame (the window never centres on it)
    if n >= 2:
        a, _ = load_luma(frames[-2][1])
        b, _ = load_luma(frames[-1][1])
        s["d_prev"][n - 1] = float(np.abs(b - a).mean())
    s["_nums"] = nums
    s["_shapes"] = shapes
    s["_tiles"] = tiles
    return s


# ---------------------------------------------------------------------------
# detectors
# ---------------------------------------------------------------------------

def _finding(det, frames, severity, detail, **kw):
    d = {"detector": det, "frames": [int(f) for f in frames],
         "severity": severity, "detail": detail}
    d.update(kw)
    return d


def _events_all(s):
    """Every level event, globally and per tile, computed once and shared by
    D1, D2 and D4 so the three cannot disagree about what happened."""
    ev = {"global": diff_events(np.nan_to_num(s["mean"], nan=0.0)),
          "tiles": {}, "tiles_measured": True}
    T = s["_tiles"]
    if T.shape[0] < TILE_MIN_FRAMES:
        # Not enough history to estimate 144 per-tile scales. Saying NOT
        # MEASURED is a result; firing anyway would be guessing, and passing
        # anyway would be the convincing null this project has been burned by.
        ev["tiles_measured"] = False
        return ev
    for t in range(T.shape[1]):
        col = T[:, t]
        if not np.isfinite(col).all():
            continue
        e = diff_events(col, amp_floor=TILE_AMP)
        if e:
            ev["tiles"][t] = e
    return ev


def _tile_xy(t):
    return (t // TILE_X, t % TILE_X)


def _group_tile_events(ev, kind, span_lo, span_hi):
    """Collect tile events of a kind that start on the same frame."""
    by_frame = {}
    for t, evs in ev["tiles"].items():
        for e in evs:
            if e["kind"] != kind or not (span_lo <= e["span"] <= span_hi):
                continue
            by_frame.setdefault(e["first"], []).append((t, e))
    return by_frame


def d1_pop(s, nums):
    """A single frame that does not belong between its neighbours.

    Two independent routes, because a pop can be global (the whole frame lifts)
    or local (one shard, one shadow, one corner of the image). The local route
    is what makes a 144-tile decomposition worth the arithmetic: a shard popping
    in one tile moves the whole-frame mean by under a percent of its own size.
    """
    ev = s["_events"]
    out = []
    seen = set()
    for e in ev["global"]:
        if e["kind"] == "burst" and e["span"] == 1:
            i = e["first"]
            seen.add(i)
            hot = s["res_hot"][i] if np.isfinite(s["res_hot"][i]) else float("nan")
            out.append(_finding(
                "D1_pop", [nums[i]], "FAIL",
                f"frame {nums[i]}: whole-frame level jumps {e['amp']:+.5f} "
                f"(z={e['z']:.1f}) and comes straight back the next frame -- a "
                f"popped frame. {hot*100:.3f}% of its pixels move more than the "
                f"{HOT_PIXEL:.4f} renderer floor.",
                z=round(e["z"], 2), amp=e["amp"], scope="global",
                hot_frac=None if not np.isfinite(hot) else float(hot)))
    for i, group in _group_tile_events(ev, "burst", 1, 1).items():
        if i in seen:
            continue
        amps = [e["amp"] for _, e in group]
        xy = [_tile_xy(t) for t, _ in group]
        out.append(_finding(
            "D1_pop", [nums[i]], "WARN" if LOCAL_IS_ADVISORY else "FAIL",
            f"frame {nums[i]}: {len(group)} of {TILE_Y*TILE_X} image tiles jump "
            f"{np.mean(amps):+.4f} and return the next frame, while the frame as a "
            f"whole does not -- a LOCAL pop (tiles row,col {xy[:6]}"
            f"{' ...' if len(xy) > 6 else ''}). A shard, a shadow or an LOD swap "
            f"behaves like this -- and SO DOES A SPECULAR HIGHLIGHT sweeping across "
            f"bodywork, which is why this is advisory. Confirm by re-rendering "
            f"frames {nums[max(0,i-1)]}-{nums[min(i+1,len(nums)-1)]} with a different "
            f"seed: geometry reproduces, sampling artefacts do not.",
            z=round(max(e["z"] for _, e in group), 2), scope="local",
            n_tiles=len(group), tiles=[list(map(int, p)) for p in xy[:20]]))
    return out


def d2_flicker(s, nums):
    """A burst of 2-8 frames, and period-2 oscillation.

    The 2nd-difference statistic that finds a single pop is BLIND to the middle
    of a plateau -- three frames lifted together give a residual of zero at the
    centre frame -- which is why flicker is found on the level series instead.
    """
    ev = s["_events"]
    out, seen = [], set()
    for e in ev["global"]:
        if e["kind"] == "burst" and 2 <= e["span"] <= MAX_BURST:
            a, b = e["first"], e["last"]
            seen.add(a)
            out.append(_finding(
                "D2_flicker", [int(x) for x in nums[a:b + 1]], "FAIL",
                f"frames {nums[a]}-{nums[b]}: whole-frame level steps "
                f"{e['amp']:+.5f} (z={e['z']:.1f}), holds for {e['span']} frames, "
                f"then steps back. A {e['span']}-frame excursion that returns is "
                f"flicker, not a scene change.",
                span=e["span"], amp=e["amp"], z=round(e["z"], 2), scope="global"))
    for i, group in _group_tile_events(ev, "burst", 2, MAX_BURST).items():
        if i in seen:
            continue
        span = max(e["span"] for _, e in group)
        xy = [_tile_xy(t) for t, _ in group]
        out.append(_finding(
            "D2_flicker", [int(nums[i]), int(nums[min(i + span, len(nums) - 1)])],
            "WARN" if LOCAL_IS_ADVISORY else "FAIL",
            f"frames {nums[i]}-{nums[min(i+span, len(nums)-1)]}: {len(group)} image "
            f"tiles step and return after {span} frames while the whole frame does "
            f"not -- a LOCAL {span}-frame flicker (tiles row,col {xy[:6]}"
            f"{' ...' if len(xy) > 6 else ''}). This is the signature of geometry "
            f"that interpenetrates for a few frames -- and also of a specular "
            f"highlight tracking along a curved surface, so it is advisory until "
            f"a re-render with a different seed reproduces it.",
            span=int(span), n_tiles=len(group), scope="local",
            tiles=[list(map(int, p)) for p in xy[:20]]))

    # period-2 oscillation in frame level: alternating sign after detrending
    m = np.nan_to_num(s["mean"], nan=0.0)
    if len(m) >= 8:
        trend = np.convolve(m, np.ones(5) / 5.0, mode="same")
        r = m - trend
        sgn = np.sign(r)
        for i in range(2, len(r) - 8):
            w = sgn[i:i + 8]
            alt = int(np.count_nonzero(w[1:] * w[:-1] < 0))
            amp = float(np.abs(r[i:i + 8]).mean())
            if alt >= 6 and amp > PEAK_NOISE / 2:
                out.append(_finding(
                    "D2_flicker", [int(x) for x in nums[i:i + 8]], "FAIL",
                    f"frames {nums[i]}-{nums[i+7]}: frame level alternates sign "
                    f"{alt}/7 times with mean amplitude {amp:.5f} -- period-2 flicker",
                    alternations=alt, amplitude=amp, scope="global"))
                break
    return out


def d3_firefly(s, nums):
    v = np.nan_to_num(s["firefly"], nan=0.0)
    z, med, _ = rolling_robust_z(v, floor=1.0)
    out = []
    for i in range(len(v)):
        if not np.isfinite(s["firefly"][i]):
            continue
        if v[i] >= 20 and z[i] >= Z_FAIL:
            out.append(_finding(
                "D3_firefly", [nums[i]], "FAIL",
                f"frame {nums[i]}: {int(v[i])} isolated pixels are more than "
                f"{FIREFLY_TEMPORAL} brighter than both temporal neighbours and "
                f"{FIREFLY_SPATIAL} brighter than their own 8 spatial neighbours "
                f"(neighbourhood median {med[i]:.0f}, z={z[i]:.1f})",
                count=int(v[i]), z=round(float(z[i]), 2)))
    return out


def d4_seam(s, nums, boundaries=None, window=SEAM_WINDOW):
    """A step that does not come back, coherent across most of the frame.

    A batch seam is a build/machine/settings difference between two adjacent
    ranges, so it moves the WHOLE image the same way at exactly one frame and
    stays moved. Three things must all hold, and each rejects a different
    impostor:

        the step does not revert        rejects a pop
        no outlier in a smooth ramp     rejects a fade (handled in diff_events)
        >= SEAM_COHERENCE of tiles
          step the same direction       rejects content -- a camera whipping past
                                        a bright object moves tiles both ways

    A LOCAL persistent step is deliberately NOT reported here: in a film things
    legitimately appear and stay. Only a whole-frame one is a seam.
    """
    out = []
    n = len(nums)
    ntiles = s["_tiles"].shape[1]
    ev = s["_events"]

    # Candidate frames: EVERY interior frame, tested directly on tile coherence.
    #
    # An earlier version only tested frames where the whole-frame level series
    # already had an outlier. On 33 real frames of the car launch that found
    # nothing at all -- a 32%-of-level seam went undetected -- because the frame
    # mean swings so hard during the launch that no seam can be an outlier in
    # it. Conditioning a detector on another detector firing first is how a gate
    # acquires a blind spot it cannot see.
    cand = {e["first"]: e for e in ev["global"] if e["kind"] == "step"}
    bset = set(boundaries or [])
    for i in range(n):
        if i not in cand and (SEAM_WINDOW <= i <= n - SEAM_WINDOW or nums[i] in bset):
            cand[i] = None

    T = s["_tiles"]
    if T.shape[0] < 2 * window + 2:
        return out
    # Each tile's own FIRST DIFFERENCE, with its local median removed.
    #
    # This detrending is what makes the test ramp-immune by construction: under
    # any smooth change -- a fade, a sunset, a car launching out of a dark
    # showroom -- a tile's first difference is locally constant, so subtracting
    # the local median leaves zero. Only a change that is concentrated at ONE
    # frame survives. An earlier version compared before/after medians instead
    # and fired on every ramp in the real launch footage.
    D = np.diff(T, axis=0)
    detr = np.empty_like(D)
    for i in range(D.shape[0]):
        lo, hi = max(0, i - window), min(D.shape[0], i + window + 1)
        detr[i] = D[i] - np.median(D[lo:hi], axis=0)

    for i in sorted(cand):
        j = i - 1                          # diff index for the boundary at frame i
        if j < 1 or j >= detr.shape[0] - 1:
            continue
        e_ = detr[j]
        pos = e_ > TILE_AMP / 2
        neg = e_ < -TILE_AMP / 2
        coh = max(pos.mean(), neg.mean())
        if coh < SEAM_COHERENCE:
            continue
        mask = pos if pos.mean() >= neg.mean() else neg
        step = float(np.median(e_[mask]))
        # not a pop: the very next frame must not undo it
        undo = float(np.median(detr[j + 1][mask]))
        if np.sign(undo) != np.sign(step) and abs(undo) > 0.4 * abs(step):
            continue
        # and it must still be gone-and-stayed a dozen frames later
        fwd = float(np.median(detr[j + 1:j + 1 + window][:, mask].sum(axis=0)))
        if np.sign(fwd) != np.sign(step) and abs(fwd) > 0.6 * abs(step):
            continue
        lo, hi = max(0, i - window), min(n, i + window)
        chan = {}
        for key in ("r", "g", "b"):
            x = np.asarray(s[key], dtype=np.float64)
            chan[key.upper()] = float(np.median(x[i:hi]) - np.median(x[lo:i]))
        nz = np.nan_to_num(s["res_mean"], nan=0.0)
        dnoise = float(np.median(nz[i:hi]) - np.median(nz[lo:i]))
        told = nums[i] in bset
        out.append(_finding(
            "D4_seam", [int(nums[i])], "FAIL",
            f"frame {nums[i]}: {coh*100:.0f}% of the {ntiles} image tiles step "
            f"{step:+.5f} in the SAME direction at this one frame, after each "
            f"tile's own local trend is removed, and do not come back "
            f"(R{chan['R']:+.5f} G{chan['G']:+.5f} B{chan['B']:+.5f}, "
            f"noise {dnoise:+.6f})"
            + (" -- and this is a known job boundary, where two machines met."
               if told else
               " -- no pop, no ramp: two ranges rendered differently."),
            coherence=round(float(coh), 3), step=step, channels=chan,
            noise_step=dnoise, at_job_boundary=bool(told)))
    return out


def _kink_z(x, window=ROLL_WINDOW, floor=0.0, leading=False):
    """Robust z against a neighbourhood, IGNORING frames that were not measured.

    `leading=True` compares each sample only to the window BEFORE it. A kink is
    a discontinuity, so what it must stand out from is what came before, not a
    window that also contains its aftermath. MEASURED on this project: the
    pre-fix beat-2 seam steps the median block acceleration from 0.54 to 8.57
    px/frame^2 at f794 and then settles at 3.2 for the rest of the beat. Against
    a centred +/-12 window that step is invisible; against the 12 frames before
    it, z=77. The centred window was using the defect's own aftermath as its
    baseline.

    Frames whose motion field was refused are NaN, and they are dropped from
    every baseline rather than counted as zero. Counting them as zero is what
    put a "z=95 against a median of 0.00" finding on frame 841 of carlaunch,
    three frames into a sequence that had not started moving yet.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    z, med = np.zeros(n), np.full(n, np.nan)
    for i in range(n):
        if not np.isfinite(x[i]):
            continue
        w = x[max(0, i - window):i] if leading else np.concatenate(
            [x[max(0, i - window):i], x[i + 1:min(n, i + window + 1)]])
        w = w[np.isfinite(w)]
        if w.size < 3:
            continue
        m = float(np.median(w))
        sg = max(mad(w), floor)
        med[i] = m
        z[i] = (x[i] - m) / sg if sg > 0 else 0.0
    return z, med


def d5_camera_kink(s, nums):
    """A kink in the camera path, seen in the picture rather than in metres.

    WHAT THIS ASKS, and why it cannot be one number (R2-068)
    -------------------------------------------------------
    The question is "did the image motion change abruptly in one frame". The
    old version answered it from a whole-frame translation, which on a tracking
    shot is the peak of a correlation between two regions moving opposite ways
    -- the motion of nothing. On this film's own frames the picture is not even
    two motions but a depth gradient, +8 px on one side of frame to +40 on the
    other, so there is no single translation to difference.

    What IS a single number, and is the right one, is how much every block's
    velocity changed at once. A kink in the CAMERA path changes the velocity of
    every block, whatever depth it sits at; a kink in one object's animation
    changes only the blocks that object covers. So:

        maccel      median over blocks of |v_i - v_(i-1)|   -> the camera
        maccel_max  max over blocks of the same             -> one object

    Both are computed from the block field, and both are absent (NaN) on any
    frame the field refused, which is reported rather than passed over.
    """
    out = []
    a = s["maccel"]
    finite = np.isfinite(a)
    if finite.sum() < MIN_FRAMES:
        s.setdefault("_not_measured", []).append({
            "detector": "D5_camera_kink",
            "why": f"only {int(finite.sum())} frames have a usable block motion "
                   f"field; {MIN_FRAMES} is the minimum for a rolling baseline"})
        return out
    az = np.nan_to_num(a, nan=0.0)
    z, med = _kink_z(a, floor=KINK_MIN_ACCEL / 20.0)
    zl, medl = _kink_z(a, floor=KINK_MIN_ACCEL / 20.0, leading=True)
    for i in range(2, len(az) - 1):
        if not finite[i]:
            continue
        if az[i] < KINK_MIN_ACCEL:
            continue
        lead = zl[i] > z[i]
        zz, mm_, src = ((zl[i], medl[i], "the 12 frames BEFORE it") if lead
                        else (z[i], med[i], "its own neighbourhood"))
        if zz < Z_FAIL:
            continue
        out.append(_finding(
            "D5_camera_kink", [nums[i]], "WARN",
            f"frame {nums[i]}: the WHOLE picture changes velocity "
            f"{az[i]:.2f} px/frame^2 in one frame (median over "
            f"{int(s['mcov'][i]*100)}% of blocks), z={zz:.1f} against "
            f"{src}, median {mm_:.2f}. Every block at every depth turning "
            f"together is the camera, not an object. A smooth ease does not "
            f"do this; a keyframe with the wrong handle does.",
            accel=round(float(az[i]), 3), z=round(float(zz), 2),
            scope="global", baseline="leading" if lead else "centred"))
    # the local route: one object's animation kinks while the camera does not
    am = np.nan_to_num(s["maccel_max"], nan=0.0)
    zlo, _ = _kink_z(s["maccel_max"], floor=KINK_MIN_ACCEL / 20.0)
    zle, _ = _kink_z(s["maccel_max"], floor=KINK_MIN_ACCEL / 20.0, leading=True)
    zl = np.maximum(zlo, zle)
    fired = {f["frames"][0] for f in out}
    for i in range(2, len(am) - 1):
        if not np.isfinite(s["maccel_max"][i]) or nums[i] in fired:
            continue
        if am[i] >= KINK_MIN_ACCEL and zl[i] >= Z_FAIL and az[i] < KINK_MIN_ACCEL:
            out.append(_finding(
                "D5_camera_kink", [nums[i]], "WARN" if LOCAL_IS_ADVISORY else "FAIL",
                f"frame {nums[i]}: ONE region of the picture changes velocity "
                f"{am[i]:.2f} px/frame^2 (z={zl[i]:.1f}) while the frame as a "
                f"whole changes {az[i]:.2f} -- a LOCAL kink. An animated object "
                f"with a bad handle does this; so does a specular highlight "
                f"crossing a block, which is why it is advisory.",
                accel=round(float(am[i]), 3), z=round(float(zl[i]), 2),
                scope="local"))
    return out


def d6_stepped_time(s, nums):
    """A held/duplicated frame, or period-2 stutter in a speed ramp."""
    d = np.nan_to_num(s["d_prev"], nan=np.nan)
    out = []
    finite = np.isfinite(d)
    if finite.sum() < MIN_FRAMES:
        return out
    for i in range(1, len(d)):
        if not finite[i]:
            continue
        lo, hi = max(0, i - ROLL_WINDOW), min(len(d), i + ROLL_WINDOW + 1)
        w = d[lo:hi][np.isfinite(d[lo:hi])]
        w = w[w != d[i]] if w.size > 3 else w
        if w.size < 3:
            continue
        m = float(np.median(w))
        if m <= PEAK_NOISE / 8:            # the sequence itself is static here
            continue
        if d[i] < 1e-7:
            out.append(_finding(
                "D6_stepped_time", [nums[i]], "FAIL",
                f"frame {nums[i]} is pixel-identical to frame {nums[i-1]} while the "
                f"sequence around it moves {m:.5f}/frame -- a duplicated frame",
                d_prev=float(d[i]), local_median=m))
        elif d[i] < HELD_RATIO * m:
            out.append(_finding(
                "D6_stepped_time", [nums[i]], "FAIL",
                f"frame {nums[i]} moved {d[i]:.5f} against a local median of {m:.5f} "
                f"({d[i]/m*100:.0f}%) -- the frame is held while time keeps running",
                d_prev=float(d[i]), local_median=m))

    # period-2 stutter: alternating long/short steps over >= 6 frames
    for i in range(1, len(d) - 7):
        w = d[i:i + 8]
        if not np.isfinite(w).all():
            continue
        even, odd = w[0::2], w[1::2]
        hi_, lo_ = max(even.mean(), odd.mean()), min(even.mean(), odd.mean())
        if lo_ > 1e-9 and hi_ / lo_ >= STUTTER_RATIO and hi_ > PEAK_NOISE / 4:
            out.append(_finding(
                "D6_stepped_time", list(nums[i:i + 8]), "FAIL",
                f"frames {nums[i]}-{nums[i+7]}: inter-frame motion alternates "
                f"{hi_:.5f} / {lo_:.5f} ({hi_/lo_:.1f}x) -- stepped time, the ramp "
                f"is quantised instead of smooth",
                ratio=round(float(hi_ / lo_), 2)))
            break
    return out


def d7_blur_motion(s, nums):
    """Sharpness inconsistent with the motion at that speed.

    Compares each frame to the MOTION_NEIGHBOURS frames whose image motion is
    most similar -- not to its temporal neighbours. During a speed ramp that is
    the whole question: at this speed, is this frame as blurred as the rest of
    the sequence says it should be?

    R2-068: the speed variable used to be the whole-frame translation, which on
    this footage is a number near zero with no relation to how fast the picture
    is moving -- so "the 15 frames nearest it in speed" were not nearest it in
    speed at all and the baseline was a global sharpness baseline wearing a
    speed-matched costume. It is now the MEDIAN BLOCK SPEED from the motion
    field, which is a real image speed in real frame pixels. Frames whose field
    was refused have no speed and are excluded rather than defaulted to zero.
    """
    mm = s["mmag"]
    sh = s["sharp"]
    ok = np.isfinite(mm) & np.isfinite(sh) & (sh > 0)
    idx = np.flatnonzero(ok)
    if idx.size < D7_MIN_FRAMES:
        # The baseline for "how sharp should a frame moving this fast be" is the
        # sequence itself. With too few frames the defective frames ARE a large
        # share of their own baseline and hide inside it. Measured: on 33 frames
        # of the launch this detector could not see a 25-pixel box blur.
        s.setdefault("_not_measured", []).append({
            "detector": "D7_blur_motion",
            "why": f"{idx.size} usable frames is below the {D7_MIN_FRAMES} needed "
                   f"for a {MOTION_NEIGHBOURS}-neighbour speed-matched baseline"})
        return []
    lsh = np.log(sh[idx])
    mmv = mm[idx]
    out = []
    for j, i in enumerate(idx):
        dist = np.abs(mmv - mmv[j])
        dist[j] = np.inf
        knn = np.argpartition(dist, MOTION_NEIGHBOURS)[:MOTION_NEIGHBOURS]
        base = lsh[knn]
        m, sg = float(np.median(base)), max(mad(base), 1e-6)
        z = (lsh[j] - m) / sg
        if abs(z) >= Z_FAIL:
            out.append(_finding(
                "D7_blur_motion", [nums[i]], "WARN",
                f"frame {nums[i]}: moves {mmv[j]:.2f} px/frame but its sharpness "
                f"{sh[i]:.5f} is z={z:+.1f} against the {MOTION_NEIGHBOURS} frames "
                f"nearest it in speed "
                f"({'too sharp -- shutter not scaled with the ramp' if z > 0 else 'too soft -- over-blurred'})",
                z=round(float(z), 2), mmag=float(mmv[j]), sharp=float(sh[i])))
    return out


def _med_or_none(x):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    return None if x.size == 0 else round(float(np.median(x)), 3)


def d8_pacing(s, nums, fps=24.0, beats=BEATS_24FPS):
    """Measurement, not a verdict. Where does the film sit still?

    Pacing is measured on the actual per-pixel change rate, NOT on an image
    translation. Measured on beat 5: a stretch where phase correlation reported
    0.05 px/frame of translation -- apparently frozen -- was in fact changing 3%
    of full scale per frame, with 93.8% of pixels different one second later.

    That reasoning was right and the VERDICT here was never downstream of the
    broken estimator (R2-068); only the reported translation column was, and it
    has been replaced by the block-field image speed and its spread.
    """
    mm = np.nan_to_num(s["d_prev"], nan=0.0)
    gmed = float(np.median(mm[mm > 0])) if (mm > 0).any() else 0.0
    trans = s["mmag"]
    spread = s["mspread"]
    rows, out = [], []
    for name, a, b in beats:
        sel = (nums >= a) & (nums <= b)
        if sel.sum() < 3:
            continue
        v = mm[sel]
        static = v < 0.30 * gmed
        best = run = 0
        for x in static:
            run = run + 1 if x else 0
            best = max(best, run)
        rows.append({"beat": name, "frames_present": int(sel.sum()),
                     "span": [int(a), int(b)], "seconds": round((b - a + 1) / fps, 2),
                     "change_median": round(float(np.median(v)), 5),
                     "change_p90": round(float(np.percentile(v, 90)), 5),
                     # R2-068: this used to be `translation_median_px`, a
                     # whole-frame translation at the downsampled analysis
                     # scale. It is now the median block speed in FRAME pixels,
                     # beside the spread that says whether the frame holds one
                     # motion or several. The key was renamed rather than
                     # reused: same name, different quantity is how a stale
                     # figure survives a fix.
                     "image_speed_median_px": _med_or_none(trans[sel]),
                     "image_speed_spread_px": _med_or_none(spread[sel]),
                     "frames_motion_not_measured":
                         int(np.count_nonzero(~np.isfinite(trans[sel]))),
                     "motion_median": round(float(np.median(v)), 5),
                     "motion_p90": round(float(np.percentile(v, 90)), 5),
                     "longest_static_run_frames": int(best),
                     "longest_static_run_s": round(best / fps, 2)})
        if best / fps > 1.5:
            out.append(_finding(
                "D8_pacing", [int(a), int(b)], "WARN",
                f"beat {name}: {best} consecutive frames ({best/fps:.1f} s) below "
                f"30% of the sequence's median per-pixel change rate. On a "
                f"one-shot film with no cuts to hide behind, that reads as a drag.",
                beat=name, static_s=round(best / fps, 2)))
    return out, rows


# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------

def campath_gate(path_json, fps=24.0, sensor=36.0, report_path=None):
    """Render-free camera continuity, straight from the animated path.

    This is the cheapest instrument in the ladder and the most sensitive: it
    sees the CAUSE (a keyframe handle, a rotation rate) rather than the effect,
    it covers all 2,978 frames without renting a GPU, and it can be run before a
    single frame exists.

    Rotation is reported in SCREEN WIDTHS PER FRAME rather than degrees, because
    degrees are not legible on their own -- 5 deg/frame on an 18mm lens and on a
    58mm lens are entirely different pictures. A camera that sweeps more than a
    quarter of its own frame width in one frame cannot be read by a viewer at
    24 fps, however smooth the curve is.
    """
    with open(path_json) as fh:
        doc = json.load(fh)
    path = doc["path"]
    n = len(path)
    f = np.array([p["f"] for p in path])
    P = np.array([p["p"] for p in path], dtype=np.float64)
    Q = np.array([p["q"] for p in path], dtype=np.float64)
    L = np.array([p.get("lens", 35.0) for p in path], dtype=np.float64)

    v = np.linalg.norm(np.diff(P, axis=0), axis=1)            # m/frame
    a = np.abs(np.diff(v))                                    # m/frame^2
    jerk = np.abs(np.diff(a))
    dot = np.abs(np.sum(Q[:-1] * Q[1:], axis=1)).clip(0, 1)
    dtheta = np.degrees(2 * np.arccos(dot))                   # deg/frame
    hfov = np.degrees(2 * np.arctan(sensor / (2 * L)))
    screen_per_frame = dtheta / hfov[:-1]                     # frame widths/frame
    dlens = np.abs(np.diff(L))

    rep = {"gate": GATE_VERSION + "/campath", "path": os.path.abspath(path_json),
           "frames": n, "fps": fps, "findings": []}

    def add(det, frames, sev, detail, **kw):
        rep["findings"].append(_finding(det, frames, sev, detail, **kw))

    # --- rotation legibility. The threshold is stated, not tuned.
    WHIP, FAST = 0.25, 0.12
    idx = np.flatnonzero(screen_per_frame > WHIP)
    for grp in _runs(idx):
        i0, i1 = grp[0], grp[-1]
        pk = int(grp[int(np.argmax(screen_per_frame[grp]))])
        add("C1_rotation_smear", [int(f[i0]), int(f[i1])], "FAIL",
            f"frames {f[i0]}-{f[i1]}: the camera sweeps up to "
            f"{screen_per_frame[pk]*100:.0f}% of its own frame width per frame "
            f"({dtheta[pk]:.1f} deg/frame on a {L[pk]:.0f}mm lens, hFOV "
            f"{hfov[pk]:.0f} deg), peaking at frame {f[pk]}. Above {WHIP*100:.0f}% "
            f"a viewer cannot read the image at {fps:.0f} fps -- it smears.",
            peak_frame=int(f[pk]), peak_screen_widths=float(screen_per_frame[pk]),
            peak_deg_per_frame=float(dtheta[pk]), lens_mm=float(L[pk]))
    fast = np.flatnonzero((screen_per_frame > FAST) & (screen_per_frame <= WHIP))
    for grp in _runs(fast):
        i0, i1 = grp[0], grp[-1]
        if i1 - i0 < 2:
            continue
        add("C1_rotation_smear", [int(f[i0]), int(f[i1])], "WARN",
            f"frames {f[i0]}-{f[i1]}: {screen_per_frame[grp].max()*100:.0f}% of "
            f"frame width per frame -- fast, readable, but detail will be lost",
            peak_screen_widths=float(screen_per_frame[grp].max()))

    # --- easing / path kinks
    z, med, _ = rolling_robust_z(a, window=ROLL_WINDOW, floor=1e-6)
    for i in np.flatnonzero(z >= Z_FAIL):
        if a[i] < 1e-4:
            continue
        add("C2_path_kink", [int(f[i + 1])], "WARN",
            f"frame {f[i+1]}: camera speed changes {a[i]:.4f} m/frame in one "
            f"frame, z={z[i]:.1f} against a local median of {med[i]:.5f} "
            f"({v[i]*fps:.1f} -> {v[min(i+1,len(v)-1)]*fps:.1f} m/s). An eased "
            f"curve does not do this; a keyframe with a linear handle does.",
            accel=float(a[i]), z=round(float(z[i]), 2))

    zj, _, _ = rolling_robust_z(jerk, window=ROLL_WINDOW, floor=1e-6)
    kinks = [int(f[i + 2]) for i in np.flatnonzero(zj >= Z_FAIL) if jerk[i] > 1e-4]
    if kinks:
        rep["jerk_outliers"] = kinks[:80]

    # --- lens. A zoom RAMP is legitimate and this film has one; only a
    # discontinuity in the zoom is a defect. Using the raw first difference
    # reported 300 consecutive "steps" across a perfectly smooth 37->53mm pull.
    for e in diff_events(L, amp_floor=0.25):
        i = e["first"]
        add("C3_lens_step", [int(f[i])], "WARN",
            f"frame {f[i]}: the zoom rate changes discontinuously, focal length "
            f"{L[i-1]:.1f} -> {L[i]:.1f} mm (z={e['z']:.1f} against the "
            f"surrounding zoom rate). A smooth pull does not do this.",
            lens_from=float(L[i - 1]), lens_to=float(L[i]), kind=e["kind"])

    # --- per-beat summary a human can read
    rows = []
    for name, lo, hi in BEATS_24FPS:
        sel = (f[:-1] >= lo) & (f[:-1] <= hi)
        if sel.sum() < 3:
            continue
        rows.append({
            "beat": name, "frames": [lo, hi],
            "speed_med_ms": round(float(np.median(v[sel])) * fps, 2),
            "speed_max_ms": round(float(v[sel].max()) * fps, 2),
            "rot_med_pct_width": round(float(np.median(screen_per_frame[sel])) * 100, 2),
            "rot_max_pct_width": round(float(screen_per_frame[sel].max()) * 100, 2),
            "rot_max_frame": int(f[np.flatnonzero(sel)[int(np.argmax(screen_per_frame[sel]))]]),
            "lens_mm": [round(float(L[:-1][sel].min()), 1),
                        round(float(L[:-1][sel].max()), 1)],
        })
    rep["per_beat"] = rows
    rep["verdict"] = "FAIL" if any(x["severity"] == "FAIL" for x in rep["findings"]) else "PASS"
    if provenance is not None:
        try:
            rep["provenance"] = provenance.stamp(
                __file__, inputs=[("campath", path_json)], tool_version=GATE_VERSION)
        except Exception as e:
            rep["provenance_error"] = repr(e)
    if report_path:
        with open(report_path, "w") as fh:
            json.dump(rep, fh, indent=1)
    return rep


def _runs(idx):
    """Consecutive integers grouped into runs."""
    out, cur = [], []
    for i in np.atleast_1d(idx):
        if cur and i == cur[-1] + 1:
            cur.append(int(i))
        else:
            if cur:
                out.append(cur)
            cur = [int(i)]
    if cur:
        out.append(cur)
    return out


def auto_boundaries(seq_name, db=os.path.expanduser("~/vast-render/state/broker.db")):
    """Frames where the rendering JOB changed -- the exact places a batch seam
    can exist. Testing those specifically is far more powerful than scanning."""
    if not os.path.exists(db):
        return []
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        rows = con.execute(
            "select frame, job_id from frames where seq=? and state='done' "
            "order by frame", (seq_name,)).fetchall()
        con.close()
    except Exception:
        return []
    out, prev = [], None
    for f, j in rows:
        if prev is not None and j != prev:
            out.append(f)
        prev = j
    return out


def run_gate(seq_dir, frames_filter=None, fps=24.0, boundaries=None,
             seq_name=None, report_path=None, label=None, quiet=False):
    """Measure a sequence and return (verdict, report)."""
    report = {"gate": GATE_VERSION, "sequence_dir": os.path.abspath(seq_dir),
              "label": label, "findings": [], "guards": []}

    frames = find_frames(seq_dir)
    if frames_filter:
        keep = set(frames_filter)
        frames = [f for f in frames if f[0] in keep]

    # ---- vacuity guards. Refusing is a result; a clean pass on nothing is not.
    nums = [f for f, _ in frames]
    if len(frames) < MIN_FRAMES:
        report["guards"].append(
            f"only {len(frames)} frame(s) found in {seq_dir}; {MIN_FRAMES} is the "
            f"minimum at which any detector here has power")
        return "VACUOUS", report
    gaps = np.diff(nums)
    if not (gaps == 1).all():
        bad = sorted(set(int(g) for g in gaps if g != 1))
        report["guards"].append(
            f"frame numbers are NOT contiguous (steps present: {bad}). Every "
            f"detector here is built on adjacency; on a strided sequence they "
            f"would all return clean and mean nothing. "
            f"Range {nums[0]}-{nums[-1]}, {len(nums)} frames present of "
            f"{nums[-1]-nums[0]+1}.")
        return "VACUOUS", report

    if not quiet:
        print(f"  measuring {len(frames)} frames {nums[0]}-{nums[-1]} "
              f"from {seq_dir}", file=sys.stderr)
    s = measure(frames, progress=not quiet)
    nums = s["_nums"]

    if len(s["_shapes"]) != 1:
        report["guards"].append(f"mixed frame dimensions {sorted(s['_shapes'])}")
        return "VACUOUS", report
    h, w = next(iter(s["_shapes"]))
    report["resolution"] = [int(w), int(h)]
    report["frame_span"] = [int(nums[0]), int(nums[-1])]
    report["frame_count"] = len(nums)

    mm = s["mmag"]
    d = np.nan_to_num(s["d_prev"], nan=0.0)
    if float(np.median(d)) <= PEAK_NOISE / 8:
        report["guards"].append(
            f"the sequence does not move: median inter-frame |diff| "
            f"{np.median(d):.6f} is at or below an eighth of the {PEAK_NOISE:.4f} "
            f"renderer noise floor. A static sequence passes every temporal test "
            f"trivially, which is not the same as being continuous.")
        return "VACUOUS", report

    # ---- measured floor, printed beside the assumed one
    res = np.nan_to_num(s["res_mean"], nan=np.nan)
    res_f = res[np.isfinite(res)]
    report["floor"] = {
        "assumed_peak_pixel_noise": PEAK_NOISE,
        "measured_residual_median": float(np.median(res_f)),
        "measured_residual_mad": mad(res_f),
        "median_interframe_diff": float(np.median(d)),
        # R2-068: in FRAME pixels from the block motion field, not the peak of
        # a whole-frame correlation at the downsampled analysis scale. On
        # seam_after the old key printed 0.29 for a sequence whose median image
        # speed is 4.33 px/frame at 960 -- 3x from the missing rescale and 5x
        # from averaging a depth gradient down to one peak.
        "median_image_speed_px": _med_or_none(mm),
        "median_image_spread_px": _med_or_none(s["mspread"]),
        "motion_frames_not_measured": int(np.count_nonzero(s["_motion_refused"])),
        "motion_coverage_median": _med_or_none(s["mcov"]),
    }
    if int(np.count_nonzero(s["_motion_refused"])):
        report.setdefault("not_measured", []).append(
            f"the block motion field refused "
            f"{int(np.count_nonzero(s['_motion_refused']))} of {len(nums)} frame "
            f"pairs: too few blocks produced a usable estimate. D5 and D7 skip "
            f"those frames rather than treating them as motionless.")

    if boundaries is None and seq_name:
        boundaries = auto_boundaries(seq_name)
    report["job_boundaries_tested"] = [int(b) for b in (boundaries or [])]

    s["_events"] = _events_all(s)
    report["level_events"] = {
        "global": s["_events"]["global"],
        "tiles_with_events": len(s["_events"]["tiles"]),
        "tile_route_measured": s["_events"]["tiles_measured"]}
    if not s["_events"]["tiles_measured"]:
        report.setdefault("not_measured", []).append(
            f"the local (per-tile) route: {len(nums)} frames is below the "
            f"{TILE_MIN_FRAMES} needed to estimate {TILE_Y*TILE_X} per-tile "
            f"scales. Local pops and local flicker are NOT MEASURED in this run "
            f"-- not absent.")

    findings = []
    findings += d1_pop(s, nums)
    findings += d2_flicker(s, nums)
    findings += d3_firefly(s, nums)
    findings += d4_seam(s, nums)                    # scan every interior frame
    if boundaries:                                  # plus the known job seams
        findings += d4_seam(s, nums, boundaries=boundaries, window=SEAM_WINDOW)
    findings += d5_camera_kink(s, nums)
    findings += d6_stepped_time(s, nums)
    findings += d7_blur_motion(s, nums)
    for nm in s.get("_not_measured", []):
        report.setdefault("not_measured", []).append(
            f"{nm['detector']}: {nm['why']}")
    report["not_measured_detectors"] = [nm["detector"]
                                        for nm in s.get("_not_measured", [])]
    pac, rows = d8_pacing(s, nums, fps=fps)
    findings += pac
    report["pacing"] = rows

    # de-duplicate identical (detector, frames) pairs from the double seam scan
    seen, uniq = set(), []
    for f in findings:
        k = (f["detector"], tuple(f["frames"]), f["detail"][:60])
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    report["findings"] = uniq
    report["per_frame"] = {
        "frame": [int(x) for x in nums],
        **{k: [None if not np.isfinite(v) else round(float(v), 6)
               for v in s[k]] for k in
           ("mean", "sd", "res_mean", "res_hot", "firefly", "d_prev",
            "sharp", "mmag", "mspread", "mcov", "maccel", "maccel_max")}}

    hard = [f for f in uniq if f["severity"] == "FAIL"]
    verdict = "FAIL" if hard else "PASS"
    report["verdict"] = verdict
    report["counts"] = {}
    for f in uniq:
        report["counts"][f["detector"]] = report["counts"].get(f["detector"], 0) + 1

    if provenance is not None:
        try:
            ins = [("frame_%06d" % n, p) for n, p in frames[:3]]
            if len(frames) > 3:
                ins.append(("frame_%06d" % frames[-1][0], frames[-1][1]))
            report["provenance"] = provenance.stamp(
                __file__, inputs=ins, tool_version=GATE_VERSION,
                # R2-078: half of what this gate measures now comes out of
                # image_motion.py, which never appears on a command line. A
                # report that hashes only continuity_gate.py would claim a
                # provenance it does not have -- the exact failure that
                # `also_hash` exists for.
                also_hash=[("image_motion",
                            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "image_motion.py"))],
                extra={"frames_measured": len(frames),
                       "sequence_dir": os.path.abspath(seq_dir),
                       "note": "first three and last frame hashed; the full "
                               "per-frame table below is the rest of the evidence"})
        except Exception as e:
            report["provenance_error"] = repr(e)

    if report_path:
        os.makedirs(os.path.dirname(os.path.abspath(report_path)) or ".", exist_ok=True)
        with open(report_path, "w") as fh:
            json.dump(report, fh, indent=1)
    return verdict, report


def print_report(report, verbose=True):
    v = report.get("verdict") or "VACUOUS"
    print(f"\n  {report.get('label') or report['sequence_dir']}")
    for g in report.get("guards", []):
        print(f"    VACUOUS: {g}")
    if "frame_count" in report:
        fl = report.get("floor", {})
        print(f"    {report['frame_count']} frames "
              f"{report['frame_span'][0]}-{report['frame_span'][1]} at "
              f"{report['resolution'][0]}x{report['resolution'][1]}")
        print(f"    floor: assumed peak pixel noise {fl.get('assumed_peak_pixel_noise'):.4f}, "
              f"measured residual median {fl.get('measured_residual_median',0):.6f} "
              f"(mad {fl.get('measured_residual_mad',0):.6f}), "
              f"median image speed {fl.get('median_image_speed_px') or 0:.2f} px/frame "
              f"(spread {fl.get('median_image_spread_px') or 0:.2f}, "
              f"block coverage {fl.get('motion_coverage_median') or 0:.2f}, "
              f"{fl.get('motion_frames_not_measured',0)} pairs not measured)")
        if report.get("job_boundaries_tested"):
            print(f"    job boundaries tested for seams: "
                  f"{report['job_boundaries_tested']}")
    for f in report.get("findings", []):
        if verbose or f["severity"] == "FAIL":
            print(f"    [{f['severity']}] {f['detector']}: {f['detail']}")
    if report.get("pacing"):
        print("    pacing:")
        for r in report["pacing"]:
            print(f"      {r['beat']:<12} {r['frames_present']:>5} fr  "
                  f"change/frame med {r['change_median']:>8.5f} p90 {r['change_p90']:>8.5f}  "
                  f"image speed {(r['image_speed_median_px'] or 0):>6.2f}px "
                  f"spread {(r['image_speed_spread_px'] or 0):>6.2f}px  "
                  f"longest still {r['longest_static_run_s']:>5.2f}s")
    print(f"    -> {v}")


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS
#
# A gate that has never failed has not been shown to work. Every defect class
# this tool claims to detect is synthesised here and the gate must catch it; and
# for each detector there is a NEGATIVE control -- a legitimate thing that looks
# similar -- which it must not catch.
# ---------------------------------------------------------------------------

def synth_base(n=64, w=320, h=180, seed=7):
    """A moving, textured, renderer-noise-carrying sequence.

    Panned fractal noise with an eased velocity, a slow global brightness drift,
    and per-frame gaussian noise scaled so its PEAK sits at the measured
    4/255 -- i.e. the same floor the real renderer has.
    """
    rng = np.random.default_rng(seed)
    tex = np.zeros((h * 3, w * 3), dtype=np.float32)
    for octv, amp in ((4, 0.5), (8, 0.28), (16, 0.15), (32, 0.09), (64, 0.05)):
        small = rng.random((octv, octv)).astype(np.float32)
        ys = np.linspace(0, octv - 1, h * 3)
        xs = np.linspace(0, octv - 1, w * 3)
        big = small[np.clip(ys.astype(int), 0, octv - 1)][:, np.clip(xs.astype(int), 0, octv - 1)]
        big = np.asarray(big, dtype=np.float32)
        k = np.ones((3, 3), np.float32) / 9.0
        for _ in range(2):                       # cheap smooth
            p = np.pad(big, 1, mode="edge")
            big = sum(p[i:i + big.shape[0], j:j + big.shape[1]] * k[i, j]
                      for i in range(3) for j in range(3))
        tex += amp * big
    tex = (tex - tex.min()) / (tex.max() - tex.min())

    t = np.arange(n) / max(n - 1, 1)
    ease = t * t * (3 - 2 * t)                    # smoothstep: C1, no kinks
    px = 2.0 + 24.0 * ease                        # cumulative pan, px
    py = 1.0 + 6.0 * ease
    sigma = PEAK_NOISE / 4.0                      # 4 sigma peaks ~= 4/255
    frames = []
    for i in range(n):
        # SUB-PIXEL pan. An integer-rounded pan is itself stepped motion, and
        # the first version of this generator produced a "clean" control that
        # the gate correctly failed -- the substrate was the defect.
        fy, fx = py[i] + h // 2, px[i] + w // 2
        iy, ix = int(math.floor(fy)), int(math.floor(fx))
        ry, rx = fy - iy, fx - ix
        a = ((1 - ry) * (1 - rx) * tex[iy:iy + h, ix:ix + w]
             + (1 - ry) * rx * tex[iy:iy + h, ix + 1:ix + 1 + w]
             + ry * (1 - rx) * tex[iy + 1:iy + 1 + h, ix:ix + w]
             + ry * rx * tex[iy + 1:iy + 1 + h, ix + 1:ix + 1 + w])
        a = a * (0.85 + 0.10 * t[i])              # slow legitimate drift
        a = a + rng.normal(0, sigma, a.shape).astype(np.float32)
        frames.append(np.clip(a, 0, 1))
    return frames


def real_base(source_dir, want=64):
    """Real rendered frames as the substrate, so the controls run against real
    renderer noise rather than a gaussian stand-in."""
    fr = find_frames(source_dir)
    nums = [f for f, _ in fr]
    if len(fr) < MIN_FRAMES or not (np.diff(nums) == 1).all():
        return None, None
    fr = fr[:want]
    out = []
    for _, p in fr:
        lum, _ = load_luma(p)
        out.append(lum)
    return out, [f for f, _ in fr]


def write_seq(frames, d, first=1, step=1):
    from PIL import Image
    os.makedirs(d, exist_ok=True)
    for i, a in enumerate(frames):
        u8 = np.clip(np.rint(a * 255.0), 0, 255).astype(np.uint8)
        Image.fromarray(np.dstack([u8, u8, u8])).save(
            os.path.join(d, "ctl_%06d.png" % (first + i * step)))


def _blur(a, k=5):
    p = np.pad(a, k // 2, mode="edge")
    out = np.zeros_like(a)
    for i in range(k):
        for j in range(k):
            out += p[i:i + a.shape[0], j:j + a.shape[1]]
    return out / (k * k)


def selftest(source_dir=None, keep=None, verbose=False):
    """Synthesise one defect of each class and prove the gate catches it."""
    base = None
    substrate = "synthetic (panned fractal noise + gaussian at the 4/255 floor)"
    if source_dir:
        base, _ = real_base(source_dir)
        if base is None:
            print(f"  --source {source_dir} is not a usable contiguous sequence; "
                  f"falling back to synthetic", file=sys.stderr)
        else:
            substrate = f"REAL rendered frames from {source_dir}"
    if base is None:
        base = synth_base()
    n = len(base)
    first = 1

    def cp():
        return [a.copy() for a in base]

    # The level of the substrate, so an injection amplitude means the same thing
    # on synthetic noise and on a dark, violently-changing real launch shot.
    base_level = float(np.median([a.mean() for a in base]))

    cases = []      # (name, frames_or_maker, detector, expect_frames, why, ladder)

    cases.append(("clean", cp(), None, [],
                  "negative control: the untouched sequence must PASS", None))

    # D1 -- a single popped frame. SWEPT: the report records the smallest lift
    # this substrate allows the gate to see, rather than asserting one size.
    k1 = n // 2

    def mk_pop(amp):
        f = cp()
        f[k1] = np.clip(f[k1] + amp * base_level, 0, 1)
        return f
    cases.append(("pop_1frame", mk_pop, "D1_pop", [first + k1],
                  "one frame lifted by a fraction of the average frame level: "
                  "the classic popped frame", [0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28]))

    # D2 -- a 3-frame flicker
    k2 = n // 2 - 6

    def mk_flicker(amp):
        f = cp()
        for j in (k2, k2 + 1, k2 + 2):
            f[j] = np.clip(f[j] + amp * base_level, 0, 1)
        return f
    cases.append(("flicker_3frame", mk_flicker, "D2_flicker",
                  [first + k2, first + k2 + 1, first + k2 + 2],
                  "three consecutive frames lifted together, then back: a flicker "
                  "burst, not a scene change", [0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 1.28]))

    # D3 -- fireflies
    k3 = n // 2 + 7

    def mk_firefly(cnt):
        f = cp()
        rng = np.random.default_rng(11)
        hh, ww = f[k3].shape
        ys = rng.integers(2, hh - 2, int(cnt))
        xs = rng.integers(2, ww - 2, int(cnt))
        for y, x in zip(ys, xs):
            f[k3][y, x] = 1.0
        return f
    cases.append(("firefly", mk_firefly, "D3_firefly", [first + k3],
                  "isolated blown pixels in one frame: fireflies resolving "
                  "differently per frame", [10, 20, 40, 80, 160, 320]))

    # D4 -- a batch seam: everything from k on rendered by another machine
    k4 = n // 2

    def mk_seam(amp):
        f = cp()
        for j in range(k4, n):
            f[j] = np.clip(f[j] + amp * base_level, 0, 1)
        return f
    cases.append(("batch_seam", mk_seam, "D4_seam", [first + k4],
                  "a persistent level step from one frame on and never returning: "
                  "two machines, different build, adjacent ranges",
                  [0.005, 0.01, 0.02, 0.04, 0.08, 0.16, 0.32]))

    # D1/D2 negative -- a specular highlight sweeping across bodywork.
    # THIS CONTROL EXISTS BECAUSE THE GATE FAILED IT. On 33 real frames of the
    # car launch the first version reported 25 defects; the frames showed three
    # bright glints tracking along curved panels, entirely correct rendering.
    # A one-tile, one-frame brightening is simply not diagnostic on its own.
    f = cp()
    hh, ww = f[0].shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    for j in range(n):
        cx = ww * (0.15 + 0.7 * j / (n - 1))         # glint tracks across frame
        cy = hh * (0.45 + 0.10 * math.sin(j / 6.0))
        g = np.exp(-(((xx - cx) / 9.0) ** 2 + ((yy - cy) / 6.0) ** 2))
        f[j] = np.clip(f[j] + 0.85 * g, 0, 1)
    cases.append(("moving_specular", f, None, [],
                  "negative control: a bright specular glint tracking across the "
                  "frame brightens each tile it crosses for a frame or two and "
                  "must NOT be reported as a defect", None))

    # D4 negative -- a fade must NOT read as a seam
    f = cp()
    for j in range(n):
        f[j] = np.clip(f[j] * (1.0 - 0.55 * (j / (n - 1))), 0, 1)
    cases.append(("fade_not_seam", f, None, [],
                  "negative control: a 55% fade to black walks the whole "
                  "neighbourhood down together and must NOT read as a seam", None))

    # D6 -- a duplicated (held) frame
    k = n // 2 + 3
    f = cp(); f[k] = f[k - 1].copy()
    cases.append(("held_frame", f, "D6_stepped_time", [first + k],
                  "one frame is a pixel copy of its predecessor: stepped time", None))

    # D6 -- period-2 stutter across a stretch (a 2:1 pulldown: every frame held
    # for two, which is what a speed ramp quantised to 12 fps actually looks like)
    f = cp()
    for j in range(11, 27, 2):
        f[j] = f[j - 1].copy()
    cases.append(("stutter_period2", f, "D6_stepped_time", [],
                  "every other frame held: a speed ramp quantised to 12 fps", None))

    # D5 -- a camera-path kink: pan velocity jumps mid-sequence
    kink = synth_base(n=n)
    k = n // 2
    shifted = []
    for j, a in enumerate(kink):
        sh = 0 if j < k else 9 * (j - k)          # velocity 0 -> 9 px/frame at k
        shifted.append(np.roll(a, -sh, axis=1))
    cases.append(("camera_kink", shifted, "D5_camera_kink", [first + k],
                  "image pan velocity steps from 0 to 9 px/frame in one frame: "
                  "a keyframe with the wrong handle", None))

    # D7 -- blur inconsistent with motion
    k7 = n // 2

    def mk_blur(kern):
        f = cp()
        for j in range(k7, k7 + 5):
            f[j] = _blur(f[j], int(kern))
        return f
    cases.append(("blur_mismatch", mk_blur, "D7_blur_motion", [],
                  "five frames blurred while their motion is unchanged: motion "
                  "blur reading wrong through a ramp", [3, 5, 7, 11, 17, 25]))

    # vacuity controls -- these must return VACUOUS, never PASS
    vac = [("vacuous_strided", cp()[::2], "strided: adjacency destroyed"),
           ("vacuous_short", cp()[:4], "4 frames: below the floor of any power"),
           ("vacuous_static", [base[0].copy() for _ in range(n)],
            "a frozen sequence passes every temporal test trivially")]

    tmp = keep or tempfile.mkdtemp(prefix="contgate_ctl_")
    os.makedirs(tmp, exist_ok=True)
    print(f"\n  POSITIVE CONTROLS for {GATE_VERSION}")
    print(f"  substrate: {substrate}  ({n} frames, "
          f"{base[0].shape[1]}x{base[0].shape[0]})")
    print(f"  workdir:   {tmp}\n")
    hdr = f"  {'control':<20} {'expect':<18} {'verdict':<8} {'fired':<28} {'result'}"
    print(hdr)
    print("  " + "-" * (len(hdr) + 4))

    def _try(frames, name, want_det, want_frames):
        d = os.path.join(tmp, name)
        write_seq(frames, d, first=first)
        verdict, rep = run_gate(d, label=name, quiet=True)
        fired = sorted({f["detector"] for f in rep.get("findings", [])})
        fired_fail = sorted({f["detector"] for f in rep.get("findings", [])
                             if f["severity"] == "FAIL"})
        hit = sorted({fr for f in rep.get("findings", [])
                      if f["detector"] == want_det for fr in f["frames"]})
        if want_det is None:
            ok = (verdict == "PASS") and not fired_fail
        else:
            ok = want_det in fired
            if ok and want_frames:
                ok = bool(hit) and any(
                    min(abs(h - w) for h in hit) <= 1 for w in want_frames)
        return ok, verdict, fired, fired_fail, hit, rep

    rows, failures = [], []
    for name, frames, want_det, want_frames, why, ladder in cases:
        floor_at = None
        skipped = False
        if ladder is not None:
            # SENSITIVITY SWEEP. The question a gate must answer about itself is
            # not "did it catch my one arbitrary injection" but "how small a
            # defect can it catch on THIS footage". Everything below the floor
            # reported here is NOT MEASURED by this gate on this substrate.
            ok = False
            for amp in ladder:
                ok, verdict, fired, fired_fail, hit_frames, rep = _try(
                    frames(amp), f"{name}_a{amp}", want_det, want_frames)
                if ok:
                    floor_at = amp
                    break
            if not ok and want_det in rep.get("not_measured_detectors", []):
                skipped = True
                detail = "NOT MEASURABLE on this substrate: " + next(
                    (x for x in rep.get("not_measured", []) if x.startswith(want_det)),
                    "")[len(want_det) + 2:]
            else:
                detail = (f"detected from {floor_at} (swept {ladder[0]}..{ladder[-1]})"
                          if ok else f"NOT detected at any of {ladder}")
        else:
            ok, verdict, fired, fired_fail, hit_frames, rep = _try(
                frames, name, want_det, want_frames)
            if want_det is None:
                detail = ("no FAIL-class finding" if ok
                          else f"unexpected {fired_fail}")
            else:
                detail = ("fired at %s" % hit_frames[:6] if ok
                          else "detector did not fire")
        rows.append({"control": name, "detected_from": floor_at,
                     "ladder": ladder, "skipped": bool(skipped),
                     "expect": want_det or "PASS (negative)",
                     "verdict": verdict, "fired": fired, "ok": bool(ok),
                     "why": why, "detail": detail})
        if not ok and not skipped:
            failures.append(name)
        print(f"  {name:<20} {(want_det or 'PASS'):<18} {verdict:<8} "
              f"{','.join(x.split('_')[0] for x in fired) or '-':<20} "
              f"{('OK  ' + detail) if ok else (('SKIP  ' if skipped else 'MISS  <-- ') + detail)}")

    for name, frames, why in vac:
        d = os.path.join(tmp, name)
        # the strided control must be WRITTEN strided -- renumbering it 1..n
        # would hand the gate a contiguous sequence and it would rightly pass
        write_seq(frames, d, first=first, step=2 if name == "vacuous_strided" else 1)
        verdict, rep = run_gate(d, label=name, quiet=True)
        ok = verdict == "VACUOUS"
        rows.append({"control": name, "expect": "VACUOUS", "verdict": verdict,
                     "fired": [], "ok": bool(ok), "why": why,
                     "detail": (rep.get("guards") or ["-"])[0][:70]})
        if not ok:
            failures.append(name)
        print(f"  {name:<20} {'VACUOUS':<18} {verdict:<8} {'-':<28} "
              f"{'OK' if ok else 'MISS -- a null was ACCEPTED'}")

    print()
    for r in rows:
        print(f"  {r['control']:<20} {r['why']}")
    n_skip = sum(1 for r in rows if r.get("skipped"))
    n_ok = sum(1 for r in rows if r["ok"])
    print(f"\n  {n_ok}/{len(rows) - n_skip} controls behaved as specified"
          + (f"; {n_skip} not measurable on this substrate" if n_skip else ""))
    return (not failures), rows, tmp


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seq", help="directory of PNG frames")
    ap.add_argument("--name", help="broker sequence name, for automatic job-boundary "
                                   "seam tests and for resolving --seq")
    ap.add_argument("--frames", help="restrict to a range/list, e.g. 1-864")
    ap.add_argument("--boundaries", help="frame numbers to test for batch seams "
                                         "(default: taken from the broker's job table)")
    ap.add_argument("--fps", type=float, default=24.0)
    ap.add_argument("--report", help="write the JSON report here")
    ap.add_argument("--campath", help="render-free camera continuity from a "
                                      "path JSON (frames/p/q/lens)")
    ap.add_argument("--selftest", action="store_true",
                    help="synthesise one defect of each class and prove the gate "
                         "catches it, plus the negative and vacuity controls")
    ap.add_argument("--source", help="with --selftest: a real contiguous sequence "
                                     "to use as the control substrate")
    ap.add_argument("--keep", help="with --selftest: keep the control frames here")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()

    if a.campath:
        rep = campath_gate(a.campath, fps=a.fps, report_path=a.report)
        print(f"\n  camera path: {a.campath}  ({rep['frames']} frames)")
        print(f"  {'beat':<12} {'speed m/s':>18}  {'rotation % of frame width/frame':>34}  lens")
        for r in rep["per_beat"]:
            print(f"  {r['beat']:<12} med {r['speed_med_ms']:>6.1f} max {r['speed_max_ms']:>6.1f}"
                  f"   med {r['rot_med_pct_width']:>6.2f} max {r['rot_max_pct_width']:>7.2f}"
                  f" @f{r['rot_max_frame']:<5}  {r['lens_mm'][0]}-{r['lens_mm'][1]}mm")
        print()
        for x in rep["findings"]:
            print(f"    [{x['severity']}] {x['detector']}: {x['detail']}")
        return gate_exit.verdict(
            rep["verdict"],
            f" — {sum(1 for x in rep['findings'] if x['severity']=='FAIL')} FAIL, "
            f"{sum(1 for x in rep['findings'] if x['severity']=='WARN')} advisory")

    if a.selftest:
        ok, rows, tmp = selftest(a.source, keep=a.keep, verbose=a.verbose)
        if a.report:
            with open(a.report, "w") as fh:
                json.dump({"gate": GATE_VERSION, "controls": rows,
                           "workdir": tmp}, fh, indent=1)
        return gate_exit.verdict(
            "PASS" if ok else "FAIL",
            f" — {sum(1 for r in rows if r['ok'])}/"
            f"{len(rows) - sum(1 for r in rows if r.get('skipped'))} controls "
            f"behaved as specified"
            + ("" if ok else "; the gate is NOT trustworthy"))

    seq = a.seq
    if not seq and a.name:
        seq = os.path.expanduser(f"~/vast-render/out/seq/{a.name}")
    if not seq:
        ap.error("need --seq or --name")

    bounds = parse_frames_arg(a.boundaries) if a.boundaries else None
    verdict, rep = run_gate(
        seq, frames_filter=parse_frames_arg(a.frames) if a.frames else None,
        fps=a.fps, boundaries=bounds, seq_name=a.name,
        report_path=a.report, label=a.name or seq)
    print_report(rep, verbose=True)
    hard = [f for f in rep.get("findings", []) if f["severity"] == "FAIL"]
    return gate_exit.verdict(
        verdict, f" — {len(hard)} FAIL-class finding(s), "
                 f"{len(rep.get('findings', [])) - len(hard)} advisory")


if __name__ == "__main__":
    gate_exit.guard(main, tool="continuity_gate")
