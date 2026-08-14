#!/usr/bin/env python
"""R2-4149 -- A KNOWN-T60 POSITIVE CONTROL FOR G-RING'S ESTIMATOR.

G-RING went INAPPLICABLE at beat 1 (4 -> 2 -> 0 usable decay regions) and
R2-4148 filed that as a real loss of coverage. Before any detector is changed
to get the regions back, ONE QUESTION HAS TO BE ANSWERED AND IT HAS NEVER BEEN
ASKED IN THIS PROJECT: **when G-RING did report a number at beat 1, was that
number the room's T60?**

Nothing in the suite has ever fed this estimator a decay whose T60 IS KNOWN.
Every G-RING figure in every staging entry is an estimate on a film, checked
against nothing. So this builds the missing control: impacts convolved with an
exponential IR of DECLARED T60, on a DECLARED inter-onset interval, over a
DECLARED stationary floor -- and asks `percept.decay_regions` and
`percept.band_decay_t60` what they make of it.

The three knobs are the three things that changed between R2-4141 and R2-4147:

  * T60           -- the truth the estimator has to return
  * IOI           -- how much gap there is between events. The delivered
                     master's beat 1 has 54 prominent peaks in 33 s, a MEDIAN
                     GAP OF 0.420 s, and a 2.4 s room needs 1.00 s just to
                     traverse ISO 3382 T20's -5 to -25 dB window.
  * floor         -- the machine between the events, which is what made beat 1
                     audible and what raised the p5 the decay has to fall to.

    .venv/bin/python -m tools.r2_4149_ring_control
"""

import argparse
import os
import sys

import numpy as np
from scipy import signal as sg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                   # noqa: E402

SR = 48000


def known_room(n, sr, t60_s, seed=7):
    """An exponentially-decaying noise impulse response. Frequency-independent
    by construction, so EVERY 1/6-octave band has the same true T60 and any
    spread the estimator reports is the estimator's own."""
    rng = np.random.default_rng(seed)
    t = np.arange(n) / sr
    return rng.standard_normal(n) * 10.0 ** (-3.0 * t / t60_s)


def impacts(dur_s, sr, ioi_s, seed=11, jitter=0.15):
    """Short broadband bursts on a jittered grid -- the dry excitation."""
    rng = np.random.default_rng(seed)
    x = np.zeros(int(dur_s * sr))
    t = 0.5
    while t < dur_s - 0.5:
        a = int(t * sr)
        L = int(0.004 * sr)
        env = np.exp(-np.arange(L) / (0.0008 * sr))
        x[a:a + L] += rng.standard_normal(L) * env * rng.uniform(0.6, 1.0)
        t += ioi_s * (1.0 + jitter * rng.uniform(-1.0, 1.0))
    return x


def envelope_range_db(x, sr):
    """The same p95-p5 of the broadband envelope the diagnostic reports for a
    real beat, so a control can be matched to a beat rather than guessed at."""
    e, _ = P.broadband_envelope(np.asarray(x, dtype=np.float64), sr,
                                env_hz=200.0)
    le = 20.0 * np.log10(np.maximum(e, 1e-12))
    return float(np.percentile(le, 95) - np.percentile(le, 5))


def case(t60_s, ioi_s, floor_db, dur_s=33.0, sr=SR, seed=11):
    ir = known_room(int(min(3.0 * t60_s, 6.0) * sr), sr, t60_s, seed=seed + 1)
    dry = impacts(dur_s, sr, ioi_s, seed=seed)
    wet = sg.fftconvolve(dry, ir)[:len(dry)]
    wet = wet / max(np.abs(wet).max(), 1e-12)
    if np.isfinite(floor_db):
        rng = np.random.default_rng(seed + 3)
        f = sg.sosfilt(sg.butter(2, [200.0, 6000.0], btype="bandpass",
                                 fs=sr, output="sos"),
                       rng.standard_normal(len(wet)))
        f = f / max(np.sqrt(np.mean(f ** 2)), 1e-12)
        wet = wet + f * 10.0 ** (floor_db / 20.0)
    regs = P.decay_regions(wet, sr)
    row = {"t60_true": t60_s, "ioi_s": ioi_s, "floor_db": floor_db,
           "env_range_db": envelope_range_db(wet, sr),
           "n_regions": len(regs), "n_bands": 0,
           "median_t60": float("nan"), "worst_t60": float("nan"),
           "broadband_t60": float("nan")}
    if len(regs) >= 3:
        d = P.band_decay_t60(wet, sr, regs)
        t = [r["t60_s"] for r in d["bands"] if np.isfinite(r["t60_s"])]
        row["n_bands"] = len(t)
        row["broadband_t60"] = d["broadband_t60_s"]
        if t:
            row["median_t60"] = float(np.median(t))
            row["worst_t60"] = float(np.max(t))
    return row


def show(rows, title):
    """`worst / broadband` IS G-RING's OWN STATISTIC and its bar is 1.5. This
    room is FREQUENCY-INDEPENDENT by construction -- every band has the same
    true T60 -- so the truthful answer is 1.0 and anything the column shows
    above the bar is the gate's NULL, not a mode."""
    print(title)
    print("%9s %8s %9s %8s %7s %9s %9s %11s %9s"
          % ("T60 true", "IOI s", "floor dB", "regions", "bands", "median",
             "med/true", "broadband", "worst/bb"))
    for r in rows:
        med, bb, wo = r["median_t60"], r["broadband_t60"], r["worst_t60"]
        rat = wo / bb if np.isfinite(bb) and np.isfinite(wo) and bb > 0.05 \
            else float("nan")
        flag = ""
        if np.isfinite(rat) and rat > 1.5:
            flag = "  <-- FAILS G-RING's 1.5x bar on a UNIFORM room"
        print("%9.2f %8.2f %9s %8d %7d %9s %9s %11s %9s%s"
              % (r["t60_true"], r["ioi_s"],
                 "-inf" if not np.isfinite(r["floor_db"])
                 else "%.0f" % r["floor_db"],
                 r["n_regions"], r["n_bands"],
                 "-" if not np.isfinite(med) else "%.3f" % med,
                 "-" if not np.isfinite(med) else "%.3f" % (med / r["t60_true"]),
                 "-" if not np.isfinite(bb) else "%.3f" % bb,
                 "-" if not np.isfinite(rat) else "%.3f" % rat, flag))
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.parse_args()

    print("A ROOM WHOSE T60 IS KNOWN, MEASURED BY G-RING'S OWN ESTIMATOR")
    print("(the estimator is `percept.decay_regions` + `percept.band_decay_t60`,")
    print(" unchanged, and the truth is the exponent the IR was built with)")
    print()

    show([case(2.4, ioi, float("-inf")) for ioi in
          (4.0, 3.0, 2.0, 1.5, 1.0, 0.60, 0.42)],
         "1. HOW MUCH GAP DOES A 2.4 s ROOM NEED? (no floor at all)")

    show([case(0.8, ioi, float("-inf")) for ioi in
          (2.0, 1.5, 1.0, 0.60, 0.42)],
         "2. THE SAME, FOR A 0.8 s ROOM -- a shorter decay needs a shorter gap")

    show([case(2.4, 1.5, fl) for fl in
          (float("-inf"), -60.0, -50.0, -40.0, -30.0, -20.0)],
         "3. WHAT A MACHINE BETWEEN THE EVENTS COSTS (2.4 s room, 1.5 s gap)")

    show([case(2.4, 0.42, fl) for fl in (float("-inf"), -40.0, -30.0)],
         "4. BEAT 1's OWN GEOMETRY: 0.42 s median gap between prominent peaks")

    # 5_lap IS THE ONLY BEAT G-RING STILL MEASURES ON THE DELIVERED MASTER, and
    # it is the one that FAILS it (worst band 4.450 s, broadband 2.938 s, ratio
    # 1.515). Its own geometry, measured off the master by
    # `tools/r2_4149_ring_cover.py`: 2.42 s median gap and a broadband envelope
    # whose p95-p5 is 13.4 dB -- an engine is running through the whole of it.
    # So the control is matched to THAT, and the question is what this
    # estimator returns for a room that is 2.4 s and uniform when it is
    # measured through an engine.
    rows = [case(2.4, 2.42, fl, dur_s=63.5)
            for fl in (float("-inf"), -50.0, -40.0, -35.0, -30.0, -25.0)]
    show(rows, "5. 5_lap's OWN GEOMETRY: 2.42 s median gap, engine underneath\n"
               "   (the master's 5_lap measures env p95-p5 = 13.4 dB, worst "
               "4.450 s,\n    broadband 2.938 s, ratio 1.515 -- match the "
               "env range column to it)")
    print("%9s %12s" % ("floor dB", "env p95-p5"))
    for r in rows:
        print("%9s %12.1f"
              % ("-inf" if not np.isfinite(r["floor_db"])
                 else "%.0f" % r["floor_db"], r["env_range_db"]))
    print()
    lim = P.V("G_RING.t60_vs_sabine_max_ratio") * 2.4
    print("G-RING's Sabine limb would also fire on these: the bar is "
          "%.2f s and a UNIFORM 2.4 s room reads" % lim)
    print("  " + "  ".join(
        "-" if not np.isfinite(r["worst_t60"]) else "%.2f" % r["worst_t60"]
        for r in rows))


if __name__ == "__main__":
    main()
