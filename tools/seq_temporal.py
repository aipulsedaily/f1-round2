#!/usr/bin/env python3
"""Temporal-defect scan over a rendered frame sequence.

Stills cannot show flicker, popping, sim jitter, camera-path kinks, speed-ramp
stutter or batch seams. This reads the frames in order and measures the things
that only exist BETWEEN frames.

WHAT IT MEASURES, per adjacent pair (n-1, n):

  d1        mean |I_n - I_{n-1}| over all pixels, in 0..1 luma.  Global motion
            energy.  A held frame reads ~0; a pop reads as a spike.
  p999      the 99.9th percentile of |delta|.  A firefly or a 3-frame shard
            interpenetration moves few pixels a long way, which d1 buries.
  hot       fraction of pixels with |delta| > 0.25.  Same idea, counted.
  mean/sd   per-frame luma mean and sd.  Exposure flicker and a dropped frame.
  dup       True when the frame is byte-identical to its predecessor.  Stepped
            time / a repeated frame in a speed ramp.

HOW IT FLAGS, and why not with a rolling median:

  R2-086: a local-median detector can only ever see the FIRST tooth of a
  periodic defect, because the window fills with the defect and the median
  rises to meet it.  So every threshold here is derived from a GLOBAL robust
  scale (median and MAD over the whole sequence, or over the named beat), never
  from the neighbourhood of the sample being judged.  Beat-local scales are
  offered because the film's own dynamics change by beat -- but a beat is
  hundreds of frames, far longer than any defect we are hunting.

  The second difference of d1 (jerk in image space) is what catches a camera
  kink and a speed-ramp stutter: a smooth move has a smooth d1; an easing
  discontinuity does not, even when d1 itself looks unremarkable.

Reads PNGs at their native size.  --stride N subsamples pixels for speed; the
metrics are means and percentiles, so subsampling changes them by less than the
noise floor at 720p and makes a 3,000-frame pass take minutes rather than an
hour.  Use --stride 1 to confirm anything it finds.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import median_filter

# Beat boundaries in FRAMES, 1-based inclusive, from docs/beat_sheet.md at 24 fps.
BEATS = [
    ("1_assembly", 1, 792),
    ("2_launch", 793, 864),
    ("3_breach", 865, 1056),
    ("4_transit", 1057, 1190),
    ("5_lap", 1191, 2714),
    ("6_ending", 2715, 2978),
]


# How far a pixel must jump, and come back, to count as a temporal impulse.
# In 0..1 display luma. Well above any denoised-noise residual and well below a
# real firefly, which lands at or near 1.0 on a mid-grey neighbour.
IMPULSE = 0.35

# Minimum impulse-pixel count to report. Set from the clean control, which
# measured 0. Anything above a handful is not noise.
IMPULSE_MIN_PX = 8


def beat_of(frame: int) -> str:
    for name, lo, hi in BEATS:
        if lo <= frame <= hi:
            return name
    return "?"


def frame_number(path: Path) -> int:
    m = re.findall(r"(\d+)", path.stem)
    if not m:
        raise ValueError(f"no frame number in {path.name}")
    return int(m[-1])


def load_luma(path: Path, stride: int) -> np.ndarray:
    with Image.open(path) as im:
        a = np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0
    if stride > 1:
        a = a[::stride, ::stride]
    # Rec.709 luma. The grade is AgX/SDR, so the PNG is display-referred and a
    # simple weighted sum is the right thing to difference.
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def mad(x: np.ndarray) -> float:
    m = float(np.median(x))
    return float(np.median(np.abs(x - m))) or 0.0


def robust_z(x: np.ndarray) -> np.ndarray:
    """Deviation in MADs from the GLOBAL median. Never a rolling window."""
    m = np.median(x)
    s = np.median(np.abs(x - m))
    if s <= 0:
        s = float(np.std(x)) or 1e-9
    return (x - m) / (1.4826 * s)


def selftest(tmp: Path) -> int:
    """Rebuild the controls this instrument was calibrated on, and assert them.

    The project's rule is that a gate is only trusted once it has been shown
    FAILING an artefact already known to be bad. Two of these controls are here
    because the first version of this tool got them wrong:

      * `firefly` — the temporal-impulse test originally fired on 267 px of
        EVERY frame of `clean`, the same reading with the defect present and
        absent, because a narrow feature panning across a pixel in one frame is
        also a temporal impulse. Spatial isolation is what separates them.
      * `flick2`  — a 1.5 % two-frame flicker was completely invisible, because
        it puts a CONSTANT offset into the difference series and so produces no
        period-2 line there at all. It lives in the `mean` series.

    `clean` is the control that makes the rest non-vacuous: it must flag NOTHING.
    It pans a window across one large aperiodic field, so any periodicity the
    tool reports on it is the tool's own.
    """
    from scipy.ndimage import gaussian_filter
    H, W, N = 180, 320, 240
    rng = np.random.default_rng(7)
    big = gaussian_filter(rng.random((H + 40, W + 900)), 1.4)
    big = (big - big.min()) / (big.max() - big.min())
    big = np.clip(big * 1.6 - 0.3, 0, 1)

    def base(t):
        x0 = int(round(t * 3.0))
        return big[0:H, x0:x0 + W]

    def firefly(t):
        a = base(t).copy()
        if t in (150, 151, 152):
            r = np.random.default_rng(t)
            a[r.integers(0, H, 40), r.integers(0, W, 40)] = 1.0
        return a

    cases = {
        "clean":    base,
        "firefly":  firefly,
        "held":     lambda t: base(100 if t == 101 else t),
        "flick2":   lambda t: base(t) * (1.0 + 0.015 * ((t % 2) * 2 - 1)),
        "period24": lambda t: base(t) * (1.03 if t % 24 == 0 else 1.0),
    }
    for name, fn in cases.items():
        d = tmp / name
        d.mkdir(parents=True, exist_ok=True)
        for i in range(1, N + 1):
            Image.fromarray((np.clip(fn(i), 0, 1) * 255).astype(np.uint8)) \
                 .convert("RGB").save(d / f"{name}_{i:06d}.png")

    import subprocess
    fails = []
    for name in cases:
        r = subprocess.run(
            [sys.executable, __file__, str(tmp / name), "--stride", "1",
             "--scale", "global", "--z", "8"],
            capture_output=True, text=True)
        out = r.stdout
        flagged = int(re.search(r"FLAGGED (\d+) frame", out).group(1))
        spec = "PERIODIC ENERGY" in out
        if name == "clean":
            ok = flagged == 0
            why = f"must flag nothing, flagged {flagged}"
        elif name == "firefly":
            ok = flagged == 3 and all(f"f  {n} " in out for n in (150, 151, 152))
            why = f"must flag exactly f150,151,152; flagged {flagged}"
        elif name == "held":
            ok = "IDENTICAL to the previous frame" in out
            why = "must report the duplicate frame"
        elif name == "flick2":
            # The point of this case: the OUTLIER test must miss it and the
            # SPECTRAL test must catch it. If outliers start firing here the
            # two instruments have stopped being independent.
            ok = flagged == 0 and spec and "period     2.0" in out
            why = f"outliers must miss it (got {flagged}) and a period-2 line must appear"
        else:
            ok = flagged > 0
            why = f"must flag something, flagged {flagged}"
        print(f"  {'PASS' if ok else 'FAIL'}  {name:9s} {why}")
        if not ok:
            fails.append(name)
    print(f"\nSELFTEST {'PASS' if not fails else 'FAIL: ' + ', '.join(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", nargs="?", help="directory of PNG frames")
    ap.add_argument("--selftest", action="store_true",
                    help="rebuild and assert the calibration controls")
    ap.add_argument("--stride", type=int, default=2)
    ap.add_argument("--csv", help="write the full per-frame table here")
    ap.add_argument("--json", help="write the flagged findings here")
    ap.add_argument("--scale", choices=["global", "beat"], default="beat",
                    help="robust scale computed over the whole sequence or per beat")
    ap.add_argument("--z", type=float, default=8.0, help="MADs to flag at")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--frames", help="restrict to lo-hi")
    # THE SPACING MUST BE DECLARED, because a sequence directory can hold two
    # different spacings at once. This pass fills a stride-6 pass across the
    # whole film first, then dense blocks at the hot spots, into ONE directory.
    # Differencing adjacent FILES there would compare a 6-frame gap against a
    # 1-frame gap and call the result motion energy. Only pairs exactly
    # `--spacing` apart are measured; everything else is dropped, and the count
    # of dropped pairs is printed so a wrong --spacing is loud rather than
    # silently halving the sample.
    ap.add_argument("--spacing", type=int, default=1,
                    help="frame step this scan is valid for (1 = adjacent). "
                         "Pairs not exactly this far apart are NOT measured.")
    a = ap.parse_args()

    if a.selftest:
        import tempfile
        with tempfile.TemporaryDirectory(
                dir=os.environ.get('TMPDIR')) as td:
            return selftest(Path(td))
    if not a.dir:
        ap.error('a directory is required unless --selftest')

    files = sorted(Path(a.dir).glob("*.png"), key=frame_number)
    if a.frames:
        lo, _, hi = a.frames.partition("-")
        lo, hi = int(lo), int(hi or lo)
        files = [f for f in files if lo <= frame_number(f) <= hi]
    if a.limit:
        files = files[: a.limit]
    if len(files) < 3:
        print(f"need at least 3 frames, found {len(files)}", file=sys.stderr)
        return 1

    rows = []
    prev = None
    prev2 = None
    prev_hash = None
    prev_step = None
    dropped = 0
    for i, f in enumerate(files):
        n = frame_number(f)
        h = hashlib.sha256(f.read_bytes()).hexdigest()
        L = load_luma(f, a.stride)
        row = {
            "frame": n,
            "beat": beat_of(n),
            "file": f.name,
            "mean": float(L.mean()),
            "sd": float(L.std()),
            "d1": float("nan"),
            "p999": float("nan"),
            "hot": float("nan"),
            "dup": 0,
            "gap": 0,
            "imp_hi": 0,
            "imp_lo": 0,
        }
        step = (n - rows[-1]["frame"]) if rows else None
        paired = prev is not None and step == a.spacing
        if prev is not None and not paired:
            dropped += 1
        if paired:
            d = np.abs(L - prev)
            row["d1"] = float(d.mean())
            row["p999"] = float(np.percentile(d, 99.9))
            row["hot"] = float((d > 0.25).mean())
            row["dup"] = int(h == prev_hash)
            row["gap"] = 0
        elif prev is not None:
            row["gap"] = 1
        # The impulse test needs three frames evenly spaced; `paired` only
        # covers the last pair, so require the one before it too.
        if prev2 is not None and paired and prev_step == a.spacing:
            # A FIREFLY IS BOTH A TEMPORAL AND A SPATIAL OUTLIER, and the
            # temporal half alone is not a measurement.
            #
            # "A pixel that jumps and comes straight back" sounds specific and
            # is not: a narrow bright feature panning across a pixel in one
            # frame does exactly that. Measured on a synthetic clean pan at
            # 3 px/frame it fired on 267 bright pixels of EVERY frame -- the
            # same reading with the defect present and absent.
            #
            # What separates them is that a firefly is ALONE. A passing edge is
            # spatially coherent with its neighbours; a stray sample is not. So
            # the pixel must also differ from the median of its own 3x3
            # neighbourhood, in the same direction, in the frame it appears.
            back = prev - prev2
            fwd = prev - L
            local = median_filter(prev, size=3)
            iso = prev - local
            rows[-1]["imp_hi"] = int(((back > IMPULSE) & (fwd > IMPULSE)
                                      & (iso > IMPULSE)).sum())
            rows[-1]["imp_lo"] = int(((back < -IMPULSE) & (fwd < -IMPULSE)
                                      & (iso < -IMPULSE)).sum())
        # Appended AFTER the impulse block, which attributes the impulse to the
        # middle frame of the three — i.e. to rows[-1], the previous one.
        rows.append(row)
        prev2 = prev
        prev_step = step
        prev, prev_hash = L, h
        if (i + 1) % 200 == 0:
            print(f"  ... {i + 1}/{len(files)}", file=sys.stderr, flush=True)

    # --- flagging, on a GLOBAL (or beat-global) robust scale ------------------
    findings = []
    groups = {}
    for r in rows[1:]:
        if not np.isnan(r["d1"]):
            groups.setdefault(r["beat"] if a.scale == "beat" else "all", []).append(r)

    for key, grp in groups.items():
        d1 = np.array([r["d1"] for r in grp])
        p999 = np.array([r["p999"] for r in grp])
        hot = np.array([r["hot"] for r in grp])
        mean = np.array([r["mean"] for r in grp])
        # jerk: second difference of the motion-energy series
        jerk = np.zeros_like(d1)
        if len(d1) > 2:
            jerk[1:-1] = d1[2:] - 2 * d1[1:-1] + d1[:-2]

        z_d1 = robust_z(d1)
        z_p999 = robust_z(p999)
        z_hot = robust_z(hot)
        z_mean = robust_z(mean)
        z_jerk = robust_z(jerk)

        for i, r in enumerate(grp):
            r["z_d1"] = float(z_d1[i])
            r["z_p999"] = float(z_p999[i])
            r["z_hot"] = float(z_hot[i])
            r["z_mean"] = float(z_mean[i])
            r["z_jerk"] = float(z_jerk[i])
            why = []
            if abs(z_d1[i]) > a.z:
                why.append(f"motion energy {z_d1[i]:+.1f} MADs (d1 {r['d1']:.4f})")
            if z_p999[i] > a.z:
                why.append(f"outlier pixels {z_p999[i]:+.1f} MADs (p99.9 {r['p999']:.3f})")
            if z_hot[i] > a.z:
                why.append(f"hot-pixel count {z_hot[i]:+.1f} MADs ({r['hot'] * 100:.3f} %)")
            if abs(z_mean[i]) > a.z:
                why.append(f"exposure {z_mean[i]:+.1f} MADs (mean {r['mean']:.4f})")
            if abs(z_jerk[i]) > a.z:
                why.append(f"jerk {z_jerk[i]:+.1f} MADs")
            # Impulses are judged on an ABSOLUTE count, not a z-score. A clean
            # sequence has a median of 0, and a MAD of 0 makes every z-score
            # infinite or undefined — a scale-free defect needs a scale-free
            # test. The floor was measured on a synthetic clean control.
            if r["imp_hi"] >= IMPULSE_MIN_PX:
                why.append(f"{r['imp_hi']} BRIGHT temporal impulse px "
                           f"(firefly / one-frame pop)")
            if r["imp_lo"] >= IMPULSE_MIN_PX:
                why.append(f"{r['imp_lo']} DARK temporal impulse px "
                           f"(one-frame dropout / interpenetration)")
            if r["dup"]:
                why.append("IDENTICAL to the previous frame")
            if r["d1"] < 1e-6 and not r["dup"]:
                why.append("no change from the previous frame")
            if why:
                findings.append({"frame": r["frame"], "beat": r["beat"],
                                 "scale": key, "why": why})

    # --- periodicity, which is a DIFFERENT instrument -------------------------
    #
    # R2-086: a defect that repeats at roughly a detector's window length becomes
    # its own baseline.  The outlier test above is global rather than local so it
    # does not have that exact failure, but a defect present on (say) every third
    # frame still contributes to the global median it is judged against, and a
    # low-amplitude one hides under it entirely.
    #
    # A periodogram cannot be fooled that way, because it does not ask "is this
    # sample unusual" at all.  It asks whether the series carries energy at a
    # fixed period, which a smooth camera move over a smooth world does not.  A
    # 24-frame sawtooth, a 2-frame flicker or an every-Nth-frame LOD swap all
    # appear as a spectral line even when no single frame is an outlier.
    #
    # The detrend is essential: the d1 series has real low-frequency structure
    # (the film accelerates), and without removing it the whole spectrum is one
    # DC-adjacent blob.
    # THE SERIES MATTERS, and getting this wrong made the check useless once.
    # A 2-frame brightness flicker puts a CONSTANT offset into d1 — every
    # adjacent pair differs by the same amount — so d1 is flat and carries no
    # period-2 line at all.  The flicker lives in the `mean` series.  Measured
    # on a synthetic 1.5 % 2-frame flicker: invisible in d1, 1e5x in mean.
    # So all three series are transformed, not just the difference one.
    spectral = []
    for key, grp in groups.items():
        for series in ("d1", "mean", "sd"):
            y = np.array([r[series] for r in grp], dtype=float)
            if len(y) < 32 or not np.all(np.isfinite(y)):
                continue
            # Remove the real low-frequency structure — the film genuinely
            # accelerates — so the spectrum is not one DC-adjacent blob.
            x = y - np.convolve(y, np.ones(9) / 9, mode="same")
            x = x[4:-4]
            if len(x) < 32 or np.allclose(x, 0):
                continue
            w = np.hanning(len(x))
            P = np.abs(np.fft.rfft(x * w)) ** 2
            freq = np.fft.rfftfreq(len(x), d=1.0)
            P[0] = 0.0
            # Compare each line to the MEDIAN of the spectrum, which a single
            # line cannot move. A broadband series has no line above a few x it.
            base = float(np.median(P[1:])) or 1e-30
            ratio = P / base
            order = np.argsort(ratio)[::-1][:3]
            for top in order:
                if ratio[top] > 50 and freq[top] > 0:
                    spectral.append({
                        "scale": key, "series": series,
                        "period_frames": round(1.0 / freq[top], 2),
                        "ratio": round(float(ratio[top]), 1),
                        "n": len(x),
                    })

    if a.csv:
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) +
                               ["z_d1", "z_p999", "z_hot", "z_mean", "z_jerk"])
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in w.fieldnames})

    if a.json:
        Path(a.json).write_text(json.dumps(
            {"outliers": findings, "spectral": spectral}, indent=1))

    # --- report ---------------------------------------------------------------
    print(f"frames read      {len(rows)}  ({rows[0]['frame']}..{rows[-1]['frame']})")
    measured = sum(1 for r in rows if not np.isnan(r["d1"]))
    print(f"spacing          {a.spacing} frame(s); {measured} pair(s) measured, "
          f"{dropped} pair(s) DROPPED for not being exactly {a.spacing} apart")
    if measured == 0:
        print("NOTHING MEASURED — --spacing does not match this directory")
        return 1
    miss = [r["frame"] for r in rows if r["gap"]]
    if miss:
        print(f"NON-CONTIGUOUS   before {miss[:20]}{' ...' if len(miss) > 20 else ''}")
    for name, lo, hi in BEATS:
        g = [r for r in rows[1:] if r["beat"] == name and not np.isnan(r["d1"])]
        if not g:
            continue
        d1 = np.array([r["d1"] for r in g])
        print(f"{name:12s} n={len(g):5d}  d1 median {np.median(d1):.4f}  "
              f"MAD {mad(d1):.4f}  max {d1.max():.4f} @ f"
              f"{g[int(np.argmax(d1))]['frame']}")
    if spectral:
        print("\nPERIODIC ENERGY — evidence, not a verdict. Real content can be")
        print("periodic (fence posts at constant speed); a period of 2-3 frames")
        print("at 24 fps almost never can be.")
        for s in spectral:
            print(f"  {s['scale']:12s} {s['series']:5s} period "
                  f"{s['period_frames']:8.2f} frames  {s['ratio']:10.1f}x the "
                  f"spectral median  (n={s['n']})")
    else:
        print("\nno periodic energy above 50x the spectral median in any series")

    print(f"\nFLAGGED {len(findings)} frame(s) at |z| > {a.z} on a {a.scale} scale")
    for f in findings[:200]:
        print(f"  f{f['frame']:5d} [{f['beat']}]  " + "; ".join(f["why"]))
    if len(findings) > 200:
        print(f"  ... {len(findings) - 200} more (see --json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
