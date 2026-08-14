#!/usr/bin/env python
"""R2-4141 -- WHICH VOICE OWNS EACH BEAT-1 FAILURE.

`--gates` on the cell bench says the layer fails G-MOD, G-NOVEL, G-RING and
G-ROOM(c). It does not say whether the cell put them there or whether they were
already in the part impacts, and those are different repairs: one is audio and
one is picture-locked. This runs each gate on the impacts alone, the cell alone
and the sum, so the answer is a table instead of a guess.
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                    # noqa: E402
from tools.r2_4081_asm_bench import render_parts, _to_measure_sr  # noqa: E402

BEAT1_S = 33.0
GATES = ("G-MOD", "G-NOVEL", "G-RING", "G-ROOM", "G-GESTURE", "G-EVENT",
         "G-SUSTAIN")


def one(x, sr, label):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    x, sr = _to_measure_sr(x, sr)
    b = [P.Beat("1_assembly", 0.0, min(len(x) / sr, BEAT1_S))]
    out = {"label": label}
    for fn in (P.g_mod, P.g_novel, P.g_ring, P.g_room, P.g_gesture,
               P.g_event, P.g_sustain):
        r = fn(x, sr, b)
        row = r["per_beat"].get("1_assembly", {})
        out[r["gate"]] = {
            "verdict": r["verdict"],
            "n": {k: (round(v, 4) if isinstance(v, float) else v)
                  for k, v in row.items()
                  if isinstance(v, (int, float)) and not isinstance(v, bool)},
            "failures": r["failures"],
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sr", type=int, default=96000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    imp, cell, sr, _info = render_parts(sr=a.sr, t_end=BEAT1_S)
    rows = [one(imp, sr, "impacts alone"),
            one(cell, sr, "cell alone"),
            one(imp + cell, sr, "sum (the layer)")]
    print("%-18s %s" % ("", "  ".join("%-11s" % g for g in GATES)))
    for r in rows:
        print("%-18s %s" % (r["label"],
                            "  ".join("%-11s" % r[g]["verdict"] for g in GATES)))
    for r in rows:
        print("\n== %s" % r["label"])
        for g in GATES:
            if r[g]["failures"]:
                for f in r[g]["failures"]:
                    print("   %-10s %s" % (g, f[:150]))
    if a.out:
        json.dump(rows, open(a.out, "w"), indent=1)
        print("\n>> " + a.out)


if __name__ == "__main__":
    main()
