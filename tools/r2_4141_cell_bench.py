#!/usr/bin/env python
"""R2-4141 -- THE BEAT-1 BENCH, POINTED AT THE GATES THAT STILL APPLY.

`tools/r2_4081_asm_bench.py` measures beat 1 with `boersma_hnr` and
`per_band_sfm`. R2-4084 RETIRED both of those at beat 1 -- on the measurement
that every negative in the corpus outscores every positive on both at once --
so a bench that reports them as BARS is a bench that will steer the next build
into the fourth rejection. This one reports the instruments that survived:

    G-SUSTAIN   note_cover <= 0.20, chord_cover <= 0.05, held_power_share <= 0.15
    G-EVENT     local_dynamic_range >= 13.7 dB (median, p95-p5 of the 20 ms
                level inside 2 s windows)

and it prints the retired pair as CONTEXT ONLY, unbarred, so the numbers stay
visible and cannot be chased.

The reference row is `audio/controls/synth.assembly_cell` -- C9, the positive
control -- rendered through the same estimators at the same rate. A build is
finished when its numbers are on C9's side of the corpus, not when they clear a
bar by a hair.

    python -m tools.r2_4141_cell_bench --parts        # impacts vs drive vs sum
    python -m tools.r2_4141_cell_bench --control      # C9 reference row
    python -m tools.r2_4141_cell_bench --stem PATH    # a rendered assembly.wav
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                    # noqa: E402
from tools.r2_4081_asm_bench import (beat1_clusters, render_parts,  # noqa: E402
                                     render_assembly, _to_measure_sr,
                                     MEASURE_SR)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BEAT1_S = 33.0


def measure(x, sr, label, total_s=BEAT1_S):
    """Every number the beat-1 verdict is made of, on one signal."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    x, sr = _to_measure_sr(x, sr)
    n = min(len(x), int(total_s * sr))
    seg = x[:n]
    total = n / sr

    ns = P.note_statistics(seg, sr, total)
    ldr = P.local_dynamic_range(seg, sr)
    h, live = P.boersma_hnr(seg, sr)
    W = P.white_sfm_reference(min(len(seg), int(8 * sr)), sr)
    sfm = P.per_band_sfm(seg, sr) / W if W else float("nan")

    return {
        "label": label,
        "seconds": round(total, 3),
        "rms": float(np.sqrt(np.mean(seg ** 2))),
        # ---- LIVE at beat 1 ------------------------------------------------
        "note_cover": ns["note_cover"],
        "chord_cover": ns["chord_cover"],
        "held_power_share": ns["held_power_share"],
        "n_notes": ns["n_notes"],
        "longest_note_s": ns["longest_note_s"],
        "ldr_median_db": ldr["median_db"],
        "ldr_p25_db": ldr["p25_db"],
        "BARS": {"note_cover": P.V("G_SUSTAIN.max_note_cover"),
                 "chord_cover": P.V("G_SUSTAIN.max_chord_cover"),
                 "held_power_share": P.V("G_SUSTAIN.max_held_power_share"),
                 "ldr_median_db": P.V("G_EVENT.min_local_dynamic_range_db")},
        # ---- RETIRED at beat 1 (R2-4084). CONTEXT, NOT BARS. ---------------
        "context_retired": {
            "hnr_median_db": float(np.median(h[live])) if live.any() else float("nan"),
            "sfm_ratio_of_white": float(sfm),
            "note": ("both retired at beat 1: every corpus negative outscores "
                     "every positive on both at once. Printed so the numbers "
                     "stay visible; NOT a target."),
        },
        "loudest_notes": ns["loudest_notes"][:4],
    }


def beat1_gates(x, sr):
    """Every MASTER-LEVEL gate that applies at beat 1, run on the layer.

    A PROXY, AND THE PROXY'S SIZE IS KNOWN: `assembly` carries 0.9345 of beat
    1's stem power on R2-4079's own stems (`stem_beat_power_R2-4079.json`), the
    room tail 0.0480 and everything else 0.0175 together, so the layer is what
    beat 1 IS to within a quarter of a dB. G-BALANCE is not here -- it needs
    stems, and INAPPLICABLE is not PASS. G-MOD is here and it is expected to
    FAIL: beat 1's 1.0417 s seat ladder is picture-locked (R2-4080) and no
    audio change moves it.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    x, sr = _to_measure_sr(x, sr)
    b = [P.Beat("1_assembly", 0.0, min(len(x) / sr, BEAT1_S))]
    out = {}
    for fn in (P.g_novel, P.g_mod, P.g_gesture, P.g_room, P.g_ring,
               P.g_sustain, P.g_event):
        r = fn(x, sr, b)
        out[r["gate"]] = {"verdict": r["verdict"], "failures": r["failures"]}
    return out


HDR = ("label", "note_cover", "chord_cover", "held_power_share",
       "longest_note_s", "ldr_median_db")


def table(rows):
    b = rows[0]["BARS"]
    out = ["", "%-30s %10s %10s %10s %10s %10s   %s" % (
        "signal", "note", "chord", "heldpow", "longest", "LDR dB", "verdict"),
        "%-30s %10.2f %10.2f %10.2f %10s %10.1f   %s" % (
            "BAR", b["note_cover"], b["chord_cover"], b["held_power_share"],
            "-", b["ldr_median_db"], "<=  <=  <=   -   >=")]
    for r in rows:
        bad = []
        if r["note_cover"] > b["note_cover"]:
            bad.append("SUST:note")
        if r["chord_cover"] > b["chord_cover"]:
            bad.append("SUST:chord")
        if r["held_power_share"] > b["held_power_share"]:
            bad.append("SUST:power")
        if not (r["ldr_median_db"] >= b["ldr_median_db"]):
            bad.append("EVENT")
        out.append("%-30s %10.3f %10.3f %10.4f %10.2f %10.2f   %s" % (
            r["label"], r["note_cover"], r["chord_cover"],
            r["held_power_share"], r["longest_note_s"], r["ldr_median_db"],
            ",".join(bad) if bad else "pass"))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", action="store_true",
                    help="render the layer and measure impacts, drive and sum")
    ap.add_argument("--control", action="store_true",
                    help="add the C9 assembly-cell reference row")
    ap.add_argument("--stem", action="append", default=[],
                    help="measure a rendered stem wav instead")
    ap.add_argument("--sr", type=int, default=96000)
    ap.add_argument("--gates", action="store_true",
                    help="also run every master-level gate that applies at "
                         "beat 1 on the summed layer")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    rows = []
    if a.control:
        from audio.controls import synth as C
        y, nc = C.assembly_cell(sr=MEASURE_SR, total_s=BEAT1_S)
        r = measure(y, MEASURE_SR, "C9_assembly_cell (POSITIVE)")
        r["contacts"] = nc
        rows.append(r)
        print(json.dumps(r, indent=1)[:400], flush=True)

    gate_on = None
    if a.parts:
        imp, drive, sr, info = render_parts(sr=a.sr, t_end=BEAT1_S)
        rows.append(measure(imp, sr, "impacts alone"))
        rows.append(measure(drive, sr, "cell alone"))
        rows.append(measure(imp + drive, sr, "assembly layer (sum)"))
        rows[-1]["layer_info"] = {k: v for k, v in info.items()
                                  if k not in ("cluster_modes", "per_part_voices")}
        gate_on = (imp + drive, sr)
    elif not a.stem and not a.control:
        x, sr, info = render_assembly(sr=a.sr, t_end=BEAT1_S)
        rows.append(measure(x, sr, "assembly layer"))
        gate_on = (x, sr)

    for p in a.stem:
        import soundfile as sf
        y, sr = sf.read(p, always_2d=True)
        rows.append(measure(np.asarray(y, dtype=np.float64), int(sr),
                            os.path.basename(p)))

    print(table(rows))
    if a.gates and gate_on is not None:
        g = beat1_gates(*gate_on)
        print("\nEVERY MASTER-LEVEL GATE THAT APPLIES AT BEAT 1, ON THE LAYER")
        print("(proxy: `assembly` is 0.9345 of beat 1's stem power. G-BALANCE "
              "needs stems and is not here.)")
        for k in sorted(g):
            print("  %-11s %-4s  %s" % (k, g[k]["verdict"],
                                        "; ".join(g[k]["failures"])[:120]))
        rows.append({"label": "beat1_gates_on_layer", "gates": g})
    if a.out:
        json.dump(rows, open(a.out, "w"), indent=1)
        print("\n>> " + a.out)


if __name__ == "__main__":
    main()
