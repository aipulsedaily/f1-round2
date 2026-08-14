#!/usr/bin/env python
"""R2-4081 -- THE ACCEPTANCE TEST: three rejected masters, three reasons.

The client has rejected three audio masters and named a DIFFERENT defect each
time:

    audio/out/master.wav                    "a wind blower" / "hair blower"
    audio/out/ab/master_R2-2001_..._tubes   "banging on tubes", "over and over"
    watch/rejected_audio_R2-4079/...        "sounds like a shitty musical"

A suite that fails all three for the same reason has learned nothing. This
tool prints the per-master, per-gate matrix and, for the beat where the film
was judged, the numbers each gate read -- so "its own reason" is a row of
measurements and not an assertion.

    .venv/bin/python -m tools.r2_4081_acceptance
"""

import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                    # noqa: E402
from tools import percept_matrix as M                             # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio", "out", "r2_4081", "acceptance_R2-4081.json")

MASTERS = [
    ("M1 hair blower", os.path.join(ROOT, "audio", "out", "master.wav"),
     os.path.join(ROOT, "audio", "out", "stems"),
     "TOO NOISY -- 'a wind blower', 'hair blower'"),
    ("M2 tubes", os.path.join(ROOT, "audio", "out", "ab",
                              "master_R2-2001_REJECTED_tubes.wav"), None,
     "WRONG STRUCTURE -- 'banging on tubes', 'The Tubes over and over'"),
    ("M3 musical", os.path.join(ROOT, "audio", "out", "r2_4079",
                                "master_R2-4079.wav"),
     os.path.join(ROOT, "audio", "out", "r2_4079", "stems"),
     "TOO MUCH STRUCTURE -- 'ngl audio is worse, sounds like a shitty musical'"),
]


def main():
    sheet = M._film_sheet()
    tel = M._telemetry("film")
    rows, reports = {}, {}
    for label, wav, stems_dir, complaint in MASTERS:
        if not os.path.isfile(wav):
            print(f"!! missing {wav}")
            continue
        x, sr = sf.read(wav, always_2d=True)
        stems, prov = M._stems("film", stems_dir) if stems_dir else (None, {"used": False})
        rep = P.run_suite(x, sr, sheet, stems=stems, telemetry=tel)
        rows[label] = rep["quality_verdicts"]
        # PER-BEAT outcomes, for every gate, read off the rows rather than
        # parsed out of failure strings -- the uniqueness claim below is only
        # worth making if it is computed from the measurement.
        per_beat = {}
        for g, gr in rep["gates"].items():
            for bn, br in (gr.get("per_beat") or {}).items():
                per_beat[f"{g}@{bn}"] = br.get("outcome")
        reports[label] = {
            "wav": wav, "complaint": complaint,
            "verdicts": rep["quality_verdicts"],
            "failing": P.failing_gates(rep),
            "stems_used": prov.get("used", False),
            "per_beat_outcome": per_beat,
            "beat1": {
                g: rep["gates"][g]["per_beat"].get("1_assembly")
                for g in ("G-SUSTAIN", "G-EVENT", "G-NOVEL", "G-MOD",
                          "G-GESTURE", "G-ROOM", "G-BALANCE")
                if g in rep["gates"]},
            "failures": {g: rep["gates"][g]["failures"]
                         for g in P.failing_gates(rep)},
        }
        print(f"\n=== {label}: {complaint}")
        print(f"    {wav}")
        for g in sorted(P.failing_gates(rep)):
            for f in rep["gates"][g]["failures"][:3]:
                print(f"    {g:<11s} {f}")

    gates = sorted({g for r in rows.values() for g in r})
    w = max(len(g) for g in gates) + 1
    print("\n\nPER-MASTER, PER-GATE MATRIX")
    print(f"{'gate':<{w}s}" + "".join(f"{k:>16s}" for k in rows))
    short = {P.PASS: "pass", P.FAIL: "FAIL", P.INAPPLICABLE: "inapplicable"}
    for g in gates:
        print(f"{g:<{w}s}" + "".join(f"{short.get(rows[k].get(g), '-'):>16s}"
                                     for k in rows))

    # WHAT IS EACH MASTER'S OWN REASON. At GATE level all three fail nearly
    # everything, which is the correct answer to "is this shippable" and a
    # useless answer to "why was it rejected". The reason lives one level down,
    # at the (gate, beat) row.
    print("\nUNIQUE FAILURES -- the gate each master fails that the others pass:")
    for k in rows:
        uniq = [g for g in gates if rows[k].get(g) == P.FAIL
                and all(rows[o].get(g) != P.FAIL for o in rows if o != k)]
        print(f"   {k:<16s} {', '.join(uniq) or '(none -- it shares every failure)'}")
        reports[k]["unique_failures"] = uniq

    print("\nUNIQUE (gate, beat) ROWS -- computed from per-beat outcomes:")
    pb = {k: {r for r, o in reports[k]["per_beat_outcome"].items() if o == P.FAIL}
          for k in reports}
    for k in pb:
        others = set().union(*[pb[o] for o in pb if o != k]) if len(pb) > 1 else set()
        uniq = sorted(pb[k] - others)
        print(f"   {k:<16s} {', '.join(uniq) or '(none)'}")
        reports[k]["unique_rows"] = uniq

    print("\nBEAT 1 -- the beat every complaint is about, as numbers:")
    hdr = f"{'master':<16s} {'SUSTAIN cover':>13s} {'chord':>7s} {'pwr':>7s} " \
          f"{'':>4s} {'EVENT dB':>9s} {'':>4s} {'NOVEL r':>8s} {'':>4s} {'MOD dB':>7s}"
    print(hdr)
    for k in reports:
        b = reports[k]["beat1"]
        su, ev = b.get("G-SUSTAIN") or {}, b.get("G-EVENT") or {}
        nv, mo = b.get("G-NOVEL") or {}, b.get("G-MOD") or {}
        print(f"{k:<16s} {su.get('note_cover', float('nan')):13.3f} "
              f"{su.get('chord_cover', float('nan')):7.3f} "
              f"{su.get('held_power_share', float('nan')):7.4f} "
              f"{str(su.get('outcome'))[:4]:>4s} "
              f"{ev.get('median_db', float('nan')):9.2f} "
              f"{str(ev.get('outcome'))[:4]:>4s} "
              f"{nv.get('r_max', float('nan')):8.3f} "
              f"{str(nv.get('outcome'))[:4]:>4s} "
              f"{mo.get('peak_over_local_median_db', float('nan')):7.2f}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump(reports, fh, indent=1, default=float)
    print(f"\n>> wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
