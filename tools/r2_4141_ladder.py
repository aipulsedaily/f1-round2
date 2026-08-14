#!/usr/bin/env python
"""R2-4141 -- WHAT PUTS THE PICTURE'S 1.0417 s LADDER INTO THE ENVELOPE.

Beat 1's twelve seat times are a perfect ladder: 9.900, 10.945, 11.990 ... at
1.045 s, picture-locked (R2-4080) and ruled on by the client. THE PART IMPACTS
ARE ON THAT LADDER AND DO NOT SOUND LIKE IT -- measured, envelope
autocorrelation r = 0.000, "no prominent local maximum: no period, only trend"
-- because 777 arrivals with their own geometries, materials and fall times do
not form a repeated gesture.

Anything the cell puts ON the ladder does not have that protection. A single
synthesised gesture repeated twelve times at 1.045 s is a metronome, which is
the second thing the client rejected ("The Tubes over and over"), and it is
what control C6 is built to catch.

This measures the sum with the cell's release events (a) off, (b) as scheduled,
and (c) scattered by each gripper's own blow-off time, so the choice is made on
the number rather than on the argument.
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
from tools.r2_4081_asm_bench import beat1_clusters, _to_measure_sr  # noqa: E402
from tools.r2_4141_ring_attrib import impacts                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEAT1_S = 33.0


def cell_with(sr, drop_release=False, scatter_s=0.0):
    clock = Clock(os.path.join(ROOT, "docs", "beat_sheet.json"), sr=sr)
    tw = WorldGrid(clock).t
    m = (tw + clock.launch_film_t >= -0.5) & (tw + clock.launch_film_t <= BEAT1_S)
    i0, i1 = int(np.argmax(m)), int(len(m) - np.argmax(m[::-1]))
    real = layers.cell_moves

    def patched(clusters, fps=24):
        rows, sched = real(clusters, fps=fps)
        out = []
        for r in rows:
            if r["phase"] != "release":
                out.append(r)
                continue
            if drop_release:
                continue
            if scatter_s:
                r = dict(r, t0=r["t0"] + scatter_s
                         * layers._stable_unit(r["cluster"], 23))
            out.append(r)
        return out, sched

    layers.cell_moves = patched
    try:
        return layers.cell_events(tw[i0:i1], beat1_clusters(), sr,
                                  clock.launch_film_t)[0]
    finally:
        layers.cell_moves = real


def row(x, sr, label):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    x, sr = _to_measure_sr(x, sr)
    n = min(len(x), int(BEAT1_S * sr))
    x = x[:n]
    b = [P.Beat("1_assembly", 0.0, n / sr)]
    nv = P.g_novel(x, sr, b)["per_beat"].get("1_assembly", {})
    md = P.g_mod(x, sr, b)["per_beat"].get("1_assembly", {})
    ldr = P.local_dynamic_range(x, sr)
    ns = P.note_statistics(x, sr, n / sr)
    return {"label": label, "novel_r": nv.get("r_max"),
            "novel_lag_s": nv.get("lag_s"),
            "mod_db": md.get("peak_over_local_median_db"),
            "mod_hz": md.get("peak_hz"),
            "ldr_median_db": ldr["median_db"],
            "note_cover": ns["note_cover"], "chord_cover": ns["chord_cover"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sr", type=int, default=96000)
    ap.add_argument("--gain", type=float, default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.gain is not None:
        layers.CELL_GAIN = a.gain
    imp = impacts(a.sr).astype(np.float64)
    rows = [row(imp, a.sr, "impacts alone (the ladder, unheard)")]
    for lab, kw in (("cell: release as scheduled", {}),
                    ("cell: release dropped", {"drop_release": True}),
                    ("cell: release scattered 0.45 s",
                     {"scatter_s": 0.45}),
                    ("cell: release scattered 0.90 s",
                     {"scatter_s": 0.90})):
        c = cell_with(a.sr, **kw)
        n = min(len(imp), len(c))
        rows.append(row(imp[:n] + c[:n], a.sr, lab))
    print("%-36s %8s %8s %9s %8s %8s" % ("", "novel r", "lag s", "G-MOD dB",
                                         "mod Hz", "LDR dB"))
    print("%-36s %8s %8s %9s %8s %8s" % ("bar", "<=0.15", "-", "<=6.0", "-",
                                         ">=13.7"))
    for r in rows:
        print("%-36s %8.3f %8.3f %9.2f %8.3f %8.2f" % (
            r["label"], r["novel_r"], r["novel_lag_s"], r["mod_db"],
            r["mod_hz"], r["ldr_median_db"]))
    if a.out:
        json.dump(rows, open(a.out, "w"), indent=1)
        print(">> " + a.out)


if __name__ == "__main__":
    main()
