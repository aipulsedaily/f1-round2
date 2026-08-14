#!/usr/bin/env python
"""R2-4081 -- THE BEAT-1 VOICE BENCH.

Renders the `assembly` layer alone over beat 1's world window and measures it
with G-HNR's and G-FLAT's OWN instruments (`audio.percept.boersma_hnr`,
`percept.per_band_sfm` / `white_sfm_reference`), so a change to the voice can be
judged in ~20 s instead of a 28-minute film render.

IT IS A PROXY AND THE PROXY IS CALIBRATED, NOT ASSUMED: `--stem` measures the
rendered `assembly.wav` of an existing master with the identical estimators, so
the offset between "the layer as synthesised" and "the layer as it reaches the
mix" is a printed number rather than a hope.
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                    # noqa: E402
from audio import layers                                          # noqa: E402
from audio.clock import Clock, WorldGrid                          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def beat1_clusters():
    """EXACTLY what `master.build` hands `layers.assembly`, and it has to be
    exactly that or the bench is measuring a different film."""
    anim = json.load(open(os.path.join(ROOT, "world", "beat1_anim_anim.json")))
    explode = json.load(open(os.path.join(ROOT, "docs", "explode_plan.json")))
    sheet = json.load(open(os.path.join(ROOT, "docs", "beat_sheet.json")))
    present = {r["cluster"]: r for r in sheet.get("beat1", {}).get("schedule", [])}
    return {k: dict(explode["clusters"][k], **anim["clusters"][k],
                    **{f: present.get(k, {}).get(f)
                       for f in ("presented_t", "presented_until_t")})
            for k in anim["clusters"] if k in explode["clusters"]}


def render_parts(sr=96000, t_end=33.0):
    """The layer's two voices separately, so the balance between them can be
    swept without re-rendering the impacts every time (they are 80 % of the
    cost). `layers.assembly` returns drive+impacts summed, so the drive is
    rendered again on its own and subtracted -- identical arithmetic, and the
    subtraction is exact because the drive is added after the band-pass."""
    clock = Clock(os.path.join(ROOT, "docs", "beat_sheet.json"), sr=sr)
    grid = WorldGrid(clock)
    tw = grid.t
    m = (tw + clock.launch_film_t >= -0.5) & (tw + clock.launch_film_t <= t_end)
    i0, i1 = int(np.argmax(m)), int(len(m) - np.argmax(m[::-1]))
    cl = beat1_clusters()
    full, info = layers.assembly(tw[i0:i1], cl, sr, clock.launch_film_t)
    drive, dinfo = layers.cell_events(tw[i0:i1], cl, sr, clock.launch_film_t)
    imp = np.asarray(full, dtype=np.float64) - drive
    info["drive"] = dinfo
    return imp, drive, sr, info


def render_assembly(sr=96000, t_end=33.0):
    """The layer over beat 1 only. Beat 1 is entirely OUTSIDE the world/film
    ramp (the ramp is film t 36-44 s), so world time and film time are 1:1 here
    and no warp is needed for the window this measures."""
    clock = Clock(os.path.join(ROOT, "docs", "beat_sheet.json"), sr=sr)
    grid = WorldGrid(clock)
    tw = grid.t
    m = (tw + clock.launch_film_t >= -0.5) & (tw + clock.launch_film_t <= t_end)
    i0, i1 = int(np.argmax(m)), int(len(m) - np.argmax(m[::-1]))
    x, info = layers.assembly(tw[i0:i1], beat1_clusters(), sr,
                              clock.launch_film_t)
    return np.asarray(x, dtype=np.float64), sr, info


MEASURE_SR = 48000
# THE GATE JUDGES THE 48 kHz DELIVERY, AND THAT IS NOT A DETAIL HERE. G-FLAT's
# 2048-point window at 96 kHz is 46.9 Hz per bin, and a 1/3-octave band is
# 0.2316*f wide, so `per_band_sfm`'s own `min_bins=5` guard discards EVERY band
# under 1011 Hz and the estimator returns nan. Measuring the layer at the rate
# the gate will see it is the only way the two numbers are the same number.


def _to_measure_sr(x, sr):
    if sr == MEASURE_SR:
        return x, sr
    from math import gcd
    from scipy import signal as sg
    g = gcd(MEASURE_SR, sr)
    return sg.resample_poly(x, MEASURE_SR // g, sr // g), MEASURE_SR


def measure(x, sr, label):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    x, sr = _to_measure_sr(x, sr)
    h, live = P.boersma_hnr(x, sr)
    hv = h[live]
    W = P.white_sfm_reference(min(len(x), int(8 * sr)), sr)
    n = int(3.0 * sr)
    sl = [P.per_band_sfm(x[i:i + n], sr) / W
          for i in range(0, len(x) - n + 1, n)]
    return {
        "label": label,
        "seconds": round(len(x) / sr, 3),
        "hnr_median_db": float(np.median(hv)) if hv.size else float("nan"),
        "hnr_p25_db": float(np.percentile(hv, 25)) if hv.size else float("nan"),
        "hnr_fraction_below_0db": float((hv < 0).mean()) if hv.size else float("nan"),
        "hnr_windows": int(live.sum()),
        "sfm_median_ratio_of_white": float(np.median(sl)) if sl else float("nan"),
        "sfm_worst_ratio_of_white": float(np.max(sl)) if sl else float("nan"),
        "rms": float(np.sqrt(np.mean(x ** 2))),
        "BARS": {"hnr_median_db": 8.0, "hnr_fraction_below_0db": 0.10,
                 "sfm_median_ratio_of_white": 0.45,
                 "sfm_worst_ratio_of_white": 0.55},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stem", default=None,
                    help="also measure this rendered stem wav, with the same "
                         "estimators, to calibrate the proxy")
    ap.add_argument("--t-end", type=float, default=33.0)
    ap.add_argument("--sweep", default=None,
                    help="comma-separated CELL_GAIN multipliers to sweep the "
                         "drive-against-impacts balance")
    ap.add_argument("--out", default=os.path.join(ROOT, "audio", "out",
                                                  "r2_4081", "asm_bench.json"))
    a = ap.parse_args()
    rows = []
    if a.sweep:
        imp, drive, sr, info = render_parts(t_end=a.t_end)
        rows.append(measure(imp, sr, "impacts alone (CELL_GAIN = 0)"))
        rows.append(measure(drive, sr, "the line shaft alone"))
        for g in [float(v) for v in a.sweep.split(",")]:
            r = measure(imp + drive * g, sr,
                        "layers.assembly, CELL_GAIN x %.3g = %.4g"
                        % (g, layers.CELL_GAIN * g))
            r["cell_gain"] = layers.CELL_GAIN * g
            rows.append(r)
        rows.append({"label": "drive report",
                     "drive": {k: v for k, v in info["drive"].items()
                               if k != "per_cluster"}})
    else:
        x, sr, info = render_assembly(t_end=a.t_end)
        r = measure(x, sr, "layers.assembly() over beat 1, as synthesised")
        r["impacts"] = info["impacts"]
        r["servo_voices"] = info["servo"]["voices"]
        rows.append(r)
    if a.stem:
        import soundfile as sf
        y, ysr = sf.read(a.stem, always_2d=True)
        i1 = int(min(len(y), a.t_end * ysr))
        rows.append(measure(y[:i1], ysr, "rendered stem %s, beat 1" % a.stem))
    for r in [r for r in rows if "hnr_median_db" in r]:
        print("== %s" % r["label"])
        print("   HNR  median %+.2f dB   p25 %+.2f   below-0 %.3f   (bars +8.0 / 0.10)"
              % (r["hnr_median_db"], r["hnr_p25_db"], r["hnr_fraction_below_0db"]))
        print("   SFM  median %.3f*W     worst %.3f*W          (bars 0.45 / 0.55)"
              % (r["sfm_median_ratio_of_white"], r["sfm_worst_ratio_of_white"]))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(rows, fh, indent=1, default=float)
    print(">> wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
