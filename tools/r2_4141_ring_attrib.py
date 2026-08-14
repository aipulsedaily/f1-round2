#!/usr/bin/env python
"""R2-4141 -- WHICH CELL VOICE PUTS THE 5.7 kHz RING IN THE SUM.

G-RING PASSES on the part impacts alone and PASSES on the cell alone, and the
SUM fails it: a 1/6-octave band at 5702 Hz decaying 1.71x slower than the
broadband. A failure that exists in neither part is an interaction, and the only
way to find which voice owns it is to take the voices out one at a time.

The part impacts are 80 % of the render cost and they do not change between
variants, so they are rendered ONCE and cached. Each variant then re-renders
the cell alone with one voice suppressed and re-measures the sum.
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
from tools.r2_4081_asm_bench import (beat1_clusters, render_parts,  # noqa: E402
                                     _to_measure_sr)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEAT1_S = 33.0
CACHE = os.path.join(ROOT, "audio", "out", "r2_4141", "impacts_96k.npy")


def impacts(sr):
    if os.path.exists(CACHE):
        return np.load(CACHE)
    imp, _cell, _sr, _i = render_parts(sr=sr, t_end=BEAT1_S)
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    np.save(CACHE, imp.astype(np.float32))
    return imp


def cell(sr, suppress=()):
    """The cell with one voice suppressed, by patching the voice's builder to
    return silence. Nothing in `layers` is edited: a variant that needed an
    edit would not be a measurement of the shipped layer."""
    clock = Clock(os.path.join(ROOT, "docs", "beat_sheet.json"), sr=sr)
    tw = WorldGrid(clock).t
    m = (tw + clock.launch_film_t >= -0.5) & (tw + clock.launch_film_t <= BEAT1_S)
    i0, i1 = int(np.argmax(m)), int(len(m) - np.argmax(m[::-1]))
    saved = {}
    for name in suppress:
        saved[name] = getattr(layers, name)
    try:
        if "valve_exhaust" in suppress:
            layers.valve_exhaust = lambda sr_, *a, **k: np.zeros(64)
        if "latch_strike" in suppress:
            layers.latch_strike = lambda sr_, *a, **k: np.zeros(64)
        if "servo_traverse" in suppress:
            layers.servo_traverse = lambda sr_, dur_s, *a, **k: np.zeros(
                max(int(dur_s * sr_), 16))
        if "nut_runner" in suppress:
            layers.nut_runner = lambda sr_, dur_s, *a, **k: (
                np.zeros(max(int(dur_s * sr_), 16)), 0)
        if "rolling_bed" in suppress:
            layers.rolling_bed = lambda n, *a, **k: np.zeros(n)
        return layers.cell_events(tw[i0:i1], beat1_clusters(), sr,
                                  clock.launch_film_t)[0]
    finally:
        for k2, v in saved.items():
            setattr(layers, k2, v)


def ring_row(x, sr, label):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    x, sr = _to_measure_sr(x, sr)
    b = [P.Beat("1_assembly", 0.0, min(len(x) / sr, BEAT1_S))]
    r = P.g_ring(x, sr, b)
    row = r["per_beat"].get("1_assembly", {})
    return {"label": label, "verdict": r["verdict"],
            "worst_ratio": row.get("narrowband_over_broadband"),
            "worst_hz": row.get("worst_band_hz"),
            "worst_band_t60_s": row.get("worst_band_t60_s"),
            "broadband_t60_s": row.get("broadband_t60_s"),
            "limit": row.get("limit_narrowband_ratio"),
            "failures": r["failures"]}


VARIANTS = [(), ("valve_exhaust",), ("latch_strike",), ("servo_traverse",),
            ("nut_runner",), ("rolling_bed",)]


def _p(r):
    print("%-28s %-6s %9.3f %9.0f %9.4f %9.4f" % (
        r["label"], r["verdict"], r["worst_ratio"] or 0.0, r["worst_hz"] or 0.0,
        r["worst_band_t60_s"] or 0.0, r["broadband_t60_s"] or 0.0), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sr", type=int, default=96000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    imp = impacts(a.sr).astype(np.float64)
    rows = [ring_row(imp, a.sr, "impacts alone")]
    print("%-28s %-6s %9s %9s %9s %9s" % ("", "", "worst x", "at Hz",
                                          "bandT60", "bbT60"), flush=True)
    _p(rows[0])
    for sup in VARIANTS:
        c = cell(a.sr, suppress=sup)
        lab = "sum, no " + "+".join(sup) if sup else "sum, everything"
        n = min(len(imp), len(c))
        r = ring_row(imp[:n] + c[:n], a.sr, lab)
        rows.append(r)
        _p(r)
    if a.out:
        json.dump(rows, open(a.out, "w"), indent=1)
        print(">> " + a.out)


if __name__ == "__main__":
    main()
