#!/usr/bin/env python
"""R2-4081 -- IS G-ROOM(c)'s BREACH NUMBER A MEASUREMENT OR A RAIL?

R2-4080 reported beat 3 at `cepstral peak 23.26x median at 1.000 ms`.
1.000 ms is `cepstral_ripple_of`'s own `q_lo_ms` default. A maximum that lands
ON the first sample of the search window is a LOWER BOUND on something the
search cannot see, not a located echo -- so the first move is to widen the
window and find out what the real figure is, before any audio is changed to
chase it.

This bench does three things and nothing else:

  1. re-measures every beat's tail cepstrum over a LADDER of lower bounds,
     0.02 -> 1.0 ms, and reports where the maximum actually sits;
  2. runs the identical estimator on SYNTHESISED controls whose answer is known
     by construction -- white (flat envelope, no echo), a tilted/coloured tail
     (envelope, no echo), a diffuse tail (no echo), and each of those plus a
     PLANTED echo at a known sub-millisecond delay -- so that the low-quefrency
     region can be attributed to the spectral ENVELOPE or to a real delay
     rather than argued about;
  3. reports the quefrency at which the envelope's own contribution has decayed
     into the noise, which is the only defensible place for a lower bound.

Nothing here changes a gate. It produces the number the decision needs.

    .venv/bin/python -m tools.r2_4081_quefrency_bench
"""

import json
import math
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WAV = os.path.join(ROOT, "audio", "out", "r2_4079", "master_R2-4079.wav")
OUT = os.path.join(ROOT, "audio", "out", "r2_4081", "quefrency_bench.json")

# The ladder of lower bounds, in ms. 1.0 is the shipped value.
Q_LO_LADDER = (0.02, 0.05, 0.10, 0.20, 0.30, 0.50, 0.75, 1.00)
Q_HI_MS = 30.0


def cep_of(S, sr):
    """The gate's own cepstrum, returned whole so the window can be varied."""
    L = 0.5 * np.log(np.maximum(S, 1e-20))
    return np.abs(np.fft.irfft(L))


def scan(c, sr, q_lo_ms, q_hi_ms=Q_HI_MS):
    q0, q1 = int(q_lo_ms * 1e-3 * sr), int(q_hi_ms * 1e-3 * sr)
    q1 = min(q1, len(c) - 1)
    if q1 <= q0:
        return None
    band = c[q0:q1]
    med = float(np.median(band))
    j = int(np.argmax(band))
    return {"q_lo_ms": q_lo_ms, "peak_over_median": float(band[j] / max(med, 1e-20)),
            "quefrency_ms": float((q0 + j) / sr * 1e3),
            "on_rail": bool(j == 0)}


def profile(c, sr, hi_ms=5.0):
    """The cepstrum itself, decimated, so the shape near zero is visible."""
    n = int(hi_ms * 1e-3 * sr)
    med = float(np.median(c[int(1e-3 * sr):int(30e-3 * sr)]))
    out = []
    for q_ms in (0.02, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50,
                 0.70, 0.90, 1.00, 1.10, 1.30, 1.60, 2.00, 3.00, 4.00, 5.00):
        j = int(q_ms * 1e-3 * sr)
        if j < len(c):
            out.append((q_ms, float(c[j] / max(med, 1e-20))))
    return out


# ----------------------------------------------------------------- controls --
def _tail_S(x, sr, win=16384):
    Pw, f = P._stft_power(x, sr, win=win, hop=win // 2)
    return Pw.mean(axis=0), f


def control_signals(sr, n, seed=4081):
    """Signals whose cepstral answer is known by construction."""
    rng = np.random.default_rng(seed)
    out = {}
    w = rng.standard_normal(n)
    out["white_no_echo"] = w
    # a coloured tail: strong spectral ENVELOPE, no delay anywhere.
    b, a = [1.0], [1.0]
    from scipy import signal as sig
    sos = sig.butter(2, 2000.0 / (sr / 2), btype="low", output="sos")
    tilt = sig.sosfilt(sos, w)
    tilt = tilt + 0.25 * w                       # shelf, not a brick wall
    out["tilted_no_echo"] = tilt
    # a diffuse tail: dense random arrivals, exponential decay, no repeat
    ir = np.zeros(int(0.6 * sr))
    k = rng.integers(0, len(ir), size=40000)
    ir[k] += rng.standard_normal(40000)
    ir *= np.exp(-np.arange(len(ir)) / (0.12 * sr))
    diff = sig.fftconvolve(w, ir)[:n]
    out["diffuse_no_echo"] = diff
    # the same three with a PLANTED echo at a known sub-ms delay
    for name, base in (("white", w), ("tilted", tilt), ("diffuse", diff)):
        for d_ms in (0.30, 0.60, 2.50):
            d = int(d_ms * 1e-3 * sr)
            y = base.copy()
            y[d:] += 0.7 * base[:-d]
            out[f"{name}_echo_{d_ms:.2f}ms"] = y
    return out


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    x, sr = sf.read(WAV, dtype="float32", always_2d=True)
    mono = x.mean(axis=1)
    sheet = json.load(open(os.path.join(ROOT, "docs", "beat_sheet.json")))
    beats = P.beats_from_sheet(sheet, len(mono) / sr)

    rep = {"wav": os.path.relpath(WAV, ROOT), "sr": sr,
           "shipped_window_ms": [1.0, Q_HI_MS], "beats": {}, "controls": {}}

    print(f">> {os.path.relpath(WAV, ROOT)}  sr {sr}")
    print(f">> shipped search window {1.0}-{Q_HI_MS} ms; "
          f"cepstral resolution {1e3/sr:.4f} ms/bin\n")

    for b in beats:
        seg = P._slice(mono, sr, b)
        if len(seg) < int(6.0 * sr):
            continue
        regions = P.decay_regions(seg, sr)
        S, f, n_reg = P.tail_spectrum(seg, sr, regions)
        if S is None:
            continue
        c = cep_of(S, sr)
        rows = [scan(c, sr, q) for q in Q_LO_LADDER]
        rep["beats"][b.name] = {"n_tail_regions": n_reg, "ladder": rows,
                                "profile": profile(c, sr)}
        print(f"--- {b.name}   ({n_reg} tail region(s))")
        print("    q_lo    peak/median      at        on the rail?")
        for r in rows:
            print(f"    {r['q_lo_ms']:5.2f}   {r['peak_over_median']:9.2f}x   "
                  f"{r['quefrency_ms']:7.3f} ms   {'YES' if r['on_rail'] else ''}")
        print()

    # ---- controls -----------------------------------------------------------
    n = int(4.0 * sr)
    print("--- CONTROLS (identical estimator; the answer is known by "
          "construction)")
    print("    signal                     q_lo 0.02      q_lo 0.20      "
          "q_lo 1.00 (shipped)")
    for name, y in control_signals(sr, n).items():
        S, f = _tail_S(y, sr)
        c = cep_of(S, sr)
        r02, r20, r100 = scan(c, sr, 0.02), scan(c, sr, 0.20), scan(c, sr, 1.00)
        rep["controls"][name] = {"q002": r02, "q020": r20, "q100": r100,
                                 "profile": profile(c, sr)}
        print(f"    {name:26s} {r02['peak_over_median']:7.2f}x@"
              f"{r02['quefrency_ms']:6.3f}  {r20['peak_over_median']:7.2f}x@"
              f"{r20['quefrency_ms']:6.3f}  {r100['peak_over_median']:7.2f}x@"
              f"{r100['quefrency_ms']:6.3f}")

    json.dump(rep, open(OUT, "w"), indent=1)
    print(f"\n>> wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
