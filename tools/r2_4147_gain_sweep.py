#!/usr/bin/env python
"""R2-4147 -- THE BRACKET, RE-RUN AGAINST THE INSTRUMENTS THAT ARE NOT INVERTED.

`tools/r2_4141_gain_sweep.py` swept CELL_GAIN against G-EVENT and G-RING and
concluded 0.008. G-EVENT's best score is SILENCE (`tools/r2_4147_event_diag.py`),
so that sweep was walking downhill toward an empty beat and it arrived. The
client heard the arrival.

This one sweeps the same two knobs against three quantities that cannot be
bought with silence:

  AUDIBLE   `r2_4147_audible.audibility` -- the sensation level of the material
            BETWEEN the events, in dB over the masked threshold of an NR-25
            domestic room at domestic playback. Silence scores -inf. MUST BE > 0.
  AMI       `r2_4147_sep.articulation_modulation_index` -- the envelope's
            4-100 Hz RMS over its mean. A bed scores low however loud it is.
  ringT60   G-RING's own broadband decay. It goes to `nan` when the floor is too
            high for ISO 3382's 12 dB fall, and a limb that has gone blind is
            NOT a pass. This is the real ceiling and it is the only one.

    python -m tools.r2_4147_gain_sweep --cell 0.03,0.05,0.075,0.10,0.15
    python -m tools.r2_4147_gain_sweep --staging 0,0.25,0.55,1.0,2.0
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
from tools.r2_4147_audible import audibility                      # noqa: E402
from tools.r2_4147_sep import articulation_modulation_index       # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEAT1_S = 33.0

# THE LEVEL THE LAYER REACHES THE MIX AT, so an absolute measurement made on the
# bench means the same thing as one made on the master. `audio/master.py` trims
# the assembly bus to TARGET_LUFS_S['assembly'] = -27.0 LUFS-S and the delivered
# programme is TARGET_LUFS_I = -23.0, so a bench signal is placed at the bus's
# own target before its audibility is measured. The calibration is CHECKED
# against the rendered master in `--check`, not assumed.
BUS_LUFS_S = -27.0
PROGRAMME_LUFS_I = -23.0


def _place_at_bus(x, sr):
    """Put a bench signal at the level the assembly bus enters the mix at."""
    from audio import dsp
    st = np.stack([x, x], axis=1)
    _, stt, _ = dsp.loudness_lufs(st, sr)
    live = stt[np.isfinite(stt) & (stt > -70.0)]
    if not live.size:
        return x
    return x * 10.0 ** ((BUS_LUFS_S - float(np.percentile(live, 95))) / 20.0)


def render(sr=96000, t_end=BEAT1_S):
    clock = Clock(os.path.join(ROOT, "docs", "beat_sheet.json"), sr=sr)
    tw = WorldGrid(clock).t
    m = (tw + clock.launch_film_t >= -0.5) & (tw + clock.launch_film_t <= t_end)
    i0, i1 = int(np.argmax(m)), int(len(m) - np.argmax(m[::-1]))
    cl = beat1_clusters()
    full, _ = layers.assembly(tw[i0:i1], cl, sr, clock.launch_film_t)
    cell, _ = layers.cell_events(tw[i0:i1], cl, sr, clock.launch_film_t)
    return np.asarray(full, dtype=np.float64) - cell, cell, sr


def row(imp, cell, sr, label):
    x = imp + cell
    x, msr = _to_measure_sr(x, sr)
    x = x[:int(BEAT1_S * msr)]
    xb = _place_at_bus(x, msr)
    # THE PROGRAMME'S loudness anchors the SPL calibration, not the bus's: a
    # listener sets the volume by the film, and the layer is then whatever it is
    # under that setting. -23.0 LUFS-I is `master.TARGET_LUFS_I`.
    au = audibility(xb, msr, PROGRAMME_LUFS_I)
    ami = articulation_modulation_index(x, msr)["ami"]
    ldr = P.local_dynamic_range(x, msr)["median_db"]
    b = [P.Beat("1_assembly", 0.0, BEAT1_S)]
    ring = P.g_ring(x, msr, b)
    pb = ring.get("per_beat", {}).get("1_assembly", {})
    return {"label": label,
            "audible_db": au.get("median_sensation_db", float("nan")),
            "bands": au.get("median_bands_audible", float("nan")),
            "ami": ami, "ldr_db": ldr,
            "gap_frac": au.get("gap_fraction", float("nan")),
            "ring_t60": pb.get("broadband_t60_s", float("nan")),
            "ring_verdict": ring["verdict"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", default="")
    ap.add_argument("--staging", default="")
    ap.add_argument("--out", default=os.path.join(
        ROOT, "audio", "out", "r2_4147", "gain_sweep.json"))
    a = ap.parse_args()

    keep_c, keep_s = layers.CELL_GAIN, layers.STAGING_RATIO
    rows = []
    try:
        if a.cell:
            for g in [float(v) for v in a.cell.split(",")]:
                layers.CELL_GAIN = g
                imp, cell, sr = render()
                rows.append(row(imp, cell, sr, "CELL_GAIN %.4f" % g))
            layers.CELL_GAIN = keep_c
        if a.staging:
            for g in [float(v) for v in a.staging.split(",")]:
                layers.STAGING_RATIO = g
                imp, cell, sr = render()
                rows.append(row(imp, cell, sr, "STAGING_RATIO %.3f" % g))
            layers.STAGING_RATIO = keep_s
        if not rows:
            imp, cell, sr = render()
            rows.append(row(imp, cell, sr, "as shipped"))
    finally:
        layers.CELL_GAIN, layers.STAGING_RATIO = keep_c, keep_s

    print("")
    print("%-24s %11s %7s %8s %9s %9s %10s" % (
        "arm", "AUDIBLE dB", "bands", "AMI", "gapfrac", "LDR dB", "ringT60"))
    print("%-24s %11s %7s %8s %9s %9s %10s" % (
        "want", "> 0", ">= 1", ">= 0.80", "", "(inverted)", "a number"))
    print("-" * 88)
    for r in rows:
        print("%-24s %11.2f %7.1f %8.4f %9.3f %9.2f %10s" % (
            r["label"], r["audible_db"], r["bands"], r["ami"], r["gap_frac"],
            r["ldr_db"],
            "nan" if not np.isfinite(r["ring_t60"] or float("nan"))
            else "%.4f" % r["ring_t60"]))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(rows, open(a.out, "w"), indent=1)
    print("\n->", a.out)


if __name__ == "__main__":
    main()
