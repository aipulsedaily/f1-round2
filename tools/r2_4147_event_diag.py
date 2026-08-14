#!/usr/bin/env python
"""R2-4147 -- IS G-EVENT INVERTED FOR THIS MATERIAL. THE DIAGNOSIS.

THE PRIOR EVIDENCE. R2-4144 measured a dense articulation train making G-EVENT
MONOTONICALLY WORSE (11.95 -> 8.35 dB) and explained it correctly: at 20-100 Hz
every 20 ms window already holds an articulation, so a dense train FILLS THE
TROUGHS. R2-4145 then measured a 10 dB cliff in the same quantity between
CELL_GAIN 0.008 and 0.012 and read it as a bracket. Both readings have the same
cause and this module measures it: **`local_dynamic_range` scores the DEPTH OF
THE SILENCE between the events, so the cheapest way to maximise it is to put
nothing between them.** The client's ear found that on the first listen.

The experiment is one signal with one thing varied: the film's own 777 part
impacts, plus a filler, at a matched level.

    python -m tools.r2_4147_event_diag

A filler that is a MACHINE (dense distinct articulations) and a filler that is a
BED (stationary noise) must land on opposite sides of any instrument that is
allowed to steer this build. The current one does not separate them; it ranks
BOTH below silence.
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                    # noqa: E402
from audio import layers                                          # noqa: E402
from tools.r2_4081_asm_bench import render_parts, _to_measure_sr   # noqa: E402
from tools.r2_4147_audible import event_mask                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def gap_dynamic_range(mono, sr, guard_s=0.35, win_s=2.0, st_ms=20.0):
    """THE SAME QUANTITY, ASKED OF THE GAPS INSTEAD OF THE BEAT.

    `local_dynamic_range` spans p95-p5 of the 20 ms level over the WHOLE
    window, so its p95 is an impact and its p5 is whatever is between them --
    which makes silence its best score. This asks the question that actually
    separates a machine from a bed: **inside the material that is left when the
    loud events are removed, is the level still fluctuating?**

    A dense train of distinct articulations fluctuates -- each pawl, latch and
    exhaust is an attack and a decay, and even at 100 articulations a second a
    20 ms window catches between one and two of them, not a smooth average.
    Stationary noise does not fluctuate: p95-p5 of its 20 ms level is 0.6 dB.
    SILENCE CANNOT ANSWER AT ALL, and returning nan for it is correct -- an
    empty gap is the defect, not a perfect score.
    """
    mono = np.asarray(mono, dtype=np.float64)
    gap = ~event_mask(mono, sr, guard_s=guard_s)
    w = max(int(st_ms * 1e-3 * sr), 8)
    hop = max(w // 2, 1)
    n = (len(mono) - w) // hop + 1
    if n < 8:
        return {"median_db": float("nan"), "n_windows": 0}
    idx = np.arange(w)[None, :] + hop * np.arange(n)[:, None]
    rms = np.sqrt((mono[idx] ** 2).mean(axis=1))
    isgap = gap[idx].all(axis=1)
    L = 20.0 * np.log10(np.maximum(rms, 1e-12))
    per = max(int(win_s * sr / hop), 8)
    vals = []
    for i in range(0, len(L) - per + 1, per // 2):
        sl = slice(i, i + per)
        g = isgap[sl]
        if g.mean() < 0.5:
            continue
        seg = L[sl][g]
        if len(seg) < 16:
            continue
        vals.append(float(np.percentile(seg, 95) - np.percentile(seg, 5)))
    if not vals:
        return {"median_db": float("nan"), "n_windows": 0}
    return {"median_db": float(np.median(vals)), "n_windows": len(vals),
            "p25_db": float(np.percentile(vals, 25))}


def match_rms(y, target_rms):
    r = float(np.sqrt(np.mean(y ** 2)))
    return y * (target_rms / r) if r > 0 else y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(
        ROOT, "audio", "out", "r2_4147", "event_diag.json"))
    a = ap.parse_args()

    imp, cell, sr, info = render_parts()
    rng = np.random.default_rng(4147)

    # THE MATCHED LEVEL. Every filler is presented at the same RMS, and that
    # RMS is the one the AUDIBILITY instrument says a listener can actually
    # hear -- 18 dB over the shipped cell, i.e. the level R2-4147 measured as
    # the shipped one being under.
    cell_rms = float(np.sqrt(np.mean(cell ** 2)))
    lvl = cell_rms * 10.0 ** (18.0 / 20.0)

    # a hair dryer, band-limited the way C1 makes one: white noise wearing the
    # impacts' own octave balance
    from audio.controls import synth as CS
    hair = CS.octave_matched_noise(imp, sr, seed=4147)
    hair = np.asarray(hair, dtype=np.float64)
    if hair.ndim > 1:
        hair = hair.mean(axis=1)
    hair = hair[:len(imp)] if len(hair) >= len(imp) else np.pad(hair, (0, len(imp) - len(hair)))

    # a drone: one servo comb, the C8b failure mode
    t = np.arange(len(imp)) / sr
    drone = sum(np.sin(2 * np.pi * f * t) / (1 + i)
                for i, f in enumerate((196.0, 392.0, 588.0, 784.0, 980.0)))

    arms = [
        ("impacts + NOTHING (what R2-4141 shipped)", imp),
        ("impacts + the cell at CELL_GAIN %.3f" % layers.CELL_GAIN, imp + cell),
        ("impacts + the cell, +18 dB (dominant)", imp + match_rms(cell, lvl)),
        ("impacts + a HAIR DRYER at the same level", imp + match_rms(hair, lvl)),
        ("impacts + a DRONE at the same level", imp + match_rms(drone, lvl)),
    ]

    from tools.r2_4147_sep import articulation_modulation_index as _AMI
    from tools.r2_4147_audible import audibility as _AUD
    from tools.r2_4147_gain_sweep import _place_at_bus, PROGRAMME_LUFS_I

    rows = []
    for label, y in arms:
        ym, msr = _to_measure_sr(np.asarray(y, dtype=np.float64), sr)
        n = min(len(ym), int(33.0 * msr))
        ym = ym[:n]
        ldr = P.local_dynamic_range(ym, msr)
        gdr = gap_dynamic_range(ym, msr)
        au = _AUD(_place_at_bus(ym, msr), msr, PROGRAMME_LUFS_I)
        rows.append({"label": label,
                     "G_EVENT_ldr_db": ldr["median_db"],
                     "gap_dynamic_range_db": gdr["median_db"],
                     "ami": _AMI(ym, msr)["ami"],
                     "audible_db": au.get("median_sensation_db", float("nan")),
                     "gap_windows": gdr["n_windows"],
                     "rms": float(np.sqrt(np.mean(ym ** 2)))})

    lim = P.V("G_EVENT.min_local_dynamic_range_db")
    print("")
    print("%-46s %11s %9s %8s %11s" % (
        "arm", "G-EVENT dB", "GAP-DR", "AMI", "AUDIBLE dB"))
    print("%-46s %11s %9s %8s %11s" % ("bar", "%.1f" % lim, "--", "--", "> 0"))
    print("-" * 90)
    for r in rows:
        print("%-46s %11.2f %9.2f %8.4f %11.2f" % (
            r["label"], r["G_EVENT_ldr_db"], r["gap_dynamic_range_db"],
            r["ami"], r["audible_db"]))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump({"rows": rows, "bar_g_event_db": lim}, open(a.out, "w"), indent=1)
    print("\n->", a.out)


if __name__ == "__main__":
    main()
