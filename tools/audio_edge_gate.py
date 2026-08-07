"""THE EDGE GATE, STANDALONE — run it on any wav in a couple of seconds.

    .venv/bin/python tools/audio_edge_gate.py audio/out/master.wav [more.wav ...]
    .venv/bin/python tools/audio_edge_gate.py --json out.json audio/out/*.wav

The gate itself lives in `audio.verify.edge_gate` and runs inside the full gate
suite; this is the same function behind a cheap entry point, because the full
suite takes minutes and this question -- does frame 1 belong to the film? -- is
the one that needs asking after every render, on every cut, and on every A/B.

WHY IT EXISTS: R2-960. `np.roll` is circular. Used as a delay on the showroom's
2.4 s reverb tail it wrapped the tail of a car at 323 km/h onto the first 11.3 ms
of a film that opens on an empty showroom -- a 0.8505 peak against a 0.0233
programme RMS, +31.2 dB, inside frame 1, in every master this project ever
produced. The seam gate visits beat BOUNDARIES; frame 1 is an EDGE. Nothing
looked there. Now something does.

`--controls` additionally runs the positive controls. Three must FAIL and two
must PASS -- if the gate cannot fail on the defect it was built for, it is not a
gate, and if it fails on things that are fine it is not usable. One of the
must-pass controls is a STATED NEGATIVE: circularly rolling the FINISHED master
does not fail, because this film ends quiet and the defect lived in the reverb
tail buffer, not in the master. That distinction is the whole point.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from audio.verify import edge_gate, control_edge          # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wav", nargs="+")
    ap.add_argument("--json", default=None, help="write the full result here")
    ap.add_argument("--controls", action="store_true",
                    help="also run the positive controls on the first wav")
    ap.add_argument("--headroom-db", type=float, default=3.0)
    a = ap.parse_args()

    out, ok = [], True
    for p in a.wav:
        x, sr = sf.read(p, always_2d=True)
        r = edge_gate(x, sr, os.path.basename(p), headroom_db=a.headroom_db)
        out.append(r)
        f, l = r["edges"]["first"], r["edges"]["last"]
        print(f"\n== {p}")
        print(f"   frames {r['frames']}   interior crest p99.9 {r['interior_crest_p99_9_db']:+.2f} dB"
              f"  (max {r['interior_crest_max_db']:+.2f} at f{r['interior_crest_max_frame']},"
              f" median {r['interior_crest_median_db']:+.2f})")
        print(f"   crest limit {r['crest_limit_db']:+.2f} dB   step limit {r['step_limit_db']:+.2f} dB")
        for nm, e in (("FIRST frame", f), ("LAST  frame", l)):
            print(f"   {nm} {e['frame']:>5}: peak {e['peak']:.4f} at {e['peak_at_ms']:.2f} ms"
                  f"   crest {e['crest_db']:+.2f} dB [{'ok' if e['PASS_crest'] else 'FAIL'}]"
                  f"   boundary sample {e['boundary_sample_abs']:.5f}"
                  f"   step {e['onset_step_db']:+.2f} dB [{'ok' if e['PASS_step'] else 'FAIL'}]")
        print(f"   PASS={r['PASS']}")
        ok = ok and r["PASS"]

    if a.controls:
        x, sr = sf.read(a.wav[0], always_2d=True)
        print(f"\n== positive controls, built from {a.wav[0]}")
        ctl = control_edge(x, sr)
        cok = True
        for i, c in enumerate(ctl):
            must_fail = i < 3
            good = (not c["PASS"]) if must_fail else bool(c["PASS"])
            cok = cok and good
            ce = c["edges"]
            print(f"   [{'MUST FAIL' if must_fail else 'MUST PASS '}] {c['label']}")
            print(f"       first crest {ce['first']['crest_db']:+.2f} step "
                  f"{ce['first']['onset_step_db']:+.2f} | last crest "
                  f"{ce['last']['crest_db']:+.2f} step {ce['last']['onset_step_db']:+.2f}"
                  f"  -> PASS={c['PASS']}  {'(correct)' if good else '(GATE IS BROKEN)'}")
        out.append({"controls": [c for c in ctl]})
        print(f"   CONTROLS_FAIL_AS_EXPECTED={cok}")
        ok = ok and cok

    if a.json:
        with open(a.json, "w") as fh:
            json.dump(out, fh, indent=1, default=float)
        print(f">> wrote {a.json}")
    print(">> STAGE RESULT:", "AUDIO_EDGE_OK" if ok else "AUDIO_EDGE_FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
