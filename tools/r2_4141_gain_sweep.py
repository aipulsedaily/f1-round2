#!/usr/bin/env python
"""R2-4141 -- CELL_GAIN, SWEPT AGAINST THE TWO INSTRUMENTS THAT BRACKET IT.

The cell's level is not a taste knob and it is not a bar being chased. It is
bracketed on BOTH SIDES by measurements, and the bracket is the derivation:

  TOO QUIET -- the 9.9 s before the first part lands and the 11.6 s after the
    last one go back to being empty, which is what the old sustained bed
    existed to prevent and what the client heard as "The Tubes over and over":
    isolated hits with nothing between them.

  TOO LOUD -- the machine fills the gaps, and then TWO things fail at once and
    both of them are the same physical fact. G-EVENT's local dynamic range
    falls, because a filled gap is a raised p5. And G-RING's broadband decay
    stops being measurable at all: ISO 3382's T20 needs the level to fall 12 dB
    inside the gap, and it cannot fall 12 dB into a floor that is 10 dB down.
    A gate limb that goes from a number to `nan` is not a pass, and this sweep
    exists because R2-4141 made exactly that mistake once -- the mass-law fix
    to `servo_traverse` moved G-RING from 1.71x FAIL to a PASS whose broadband
    T60 was `nan`, i.e. to a limb that had gone blind.

So the shipped value is the one where the gap still DECAYS and the beat is
still EVENTFUL, with the cell as loud as those two allow. Both numbers are
printed for every level tried.

The part impacts are cached (`tools/r2_4141_ring_attrib`), so a level costs
about a minute instead of eight.
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                    # noqa: E402
from audio import layers                                          # noqa: E402
from tools.r2_4081_asm_bench import _to_measure_sr                # noqa: E402
from tools.r2_4141_ring_attrib import impacts, cell               # noqa: E402

BEAT1_S = 33.0


def row(x, sr, label):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    x, sr = _to_measure_sr(x, sr)
    n = min(len(x), int(BEAT1_S * sr))
    x = x[:n]
    b = [P.Beat("1_assembly", 0.0, n / sr)]
    ns = P.note_statistics(x, sr, n / sr)
    ldr = P.local_dynamic_range(x, sr)
    rg = P.g_ring(x, sr, b)["per_beat"].get("1_assembly", {})
    nv = P.g_novel(x, sr, b)["per_beat"].get("1_assembly", {})
    return {
        "label": label,
        "ldr_median_db": ldr["median_db"],
        "note_cover": ns["note_cover"], "chord_cover": ns["chord_cover"],
        "held_power_share": ns["held_power_share"],
        "ring_broadband_t60_s": rg.get("broadband_t60_s"),
        "ring_worst_band_t60_s": rg.get("worst_band_t60_s"),
        "ring_ratio": rg.get("narrowband_over_broadband"),
        "ring_worst_hz": rg.get("worst_band_hz"),
        "ring_n_regions": rg.get("n_decay_regions"),
        "novel_r": nv.get("r_max"), "novel_lag_s": nv.get("lag_s"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gains", default="0,0.010,0.015,0.022,0.030,0.045")
    ap.add_argument("--sr", type=int, default=96000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    imp = impacts(a.sr).astype(np.float64)
    keep = layers.CELL_GAIN
    rows = []
    print("%-14s %8s %8s %8s %9s %8s %8s %8s" % (
        "CELL_GAIN", "LDR dB", "note", "chord", "ringT60", "ring x", "at Hz",
        "novel r"), flush=True)
    print("%-14s %8s %8s %8s %9s %8s %8s %8s" % (
        "bar", ">=13.7", "<=0.20", "<=0.05", "finite", "<=1.50", "-",
        "<=0.15"), flush=True)
    try:
        for g in [float(v) for v in a.gains.split(",")]:
            layers.CELL_GAIN = g
            c = cell(a.sr)
            n = min(len(imp), len(c))
            r = row(imp[:n] + c[:n], a.sr, "%.4g" % g)
            r["cell_gain"] = g
            rows.append(r)
            def _f(v):
                # `x or nan` turns a real 0.0 into nan, and r_max = 0.0 is the
                # BEST possible G-NOVEL reading ("no period, only trend").
                return float("nan") if v is None else float(v)
            print("%-14s %8.2f %8.3f %8.3f %9.4f %8.3f %8.0f %8.3f" % (
                r["label"], r["ldr_median_db"], r["note_cover"],
                r["chord_cover"], _f(r["ring_broadband_t60_s"]),
                _f(r["ring_ratio"]), _f(r["ring_worst_hz"]),
                _f(r["novel_r"])), flush=True)
    finally:
        layers.CELL_GAIN = keep
    if a.out:
        json.dump(rows, open(a.out, "w"), indent=1)
        print(">> " + a.out)


if __name__ == "__main__":
    main()
