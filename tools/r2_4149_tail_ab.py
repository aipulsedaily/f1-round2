#!/usr/bin/env python
"""R2-4149 -- RENDER THE WHOLE FILM WITH A DIFFERENT `rt60_high`, WITHOUT
EDITING THE RENDER PATH TO DO IT.

`tools/r2_4149_room_hf.py` says the network's best fit to the physically
derived room is `rt60_high = 0.45 s` (log-RMS 0.1414) against the shipped
0.35 s (0.1841) -- a five-percentage-point improvement in a quantity whose own
estimator tolerance G-RING sets at 25 %. THAT IS NOT AN ARGUMENT FOR CHANGING
IT. It is a reason to render both and adjudicate both, because the room sits
under every beat and a fit is not a verdict.

THE PREDICTION, RECORDED BEFORE THE RENDER: 0.45 s makes the 4 kHz tail 22 %
longer (1.274 -> 1.560 s on the network's own IR), and R2-4148 measured that
beat 1's G-SUSTAIN note cover comes from partials IN THE ROOM TAIL rather than
from the assembly layer. So the physics-correct direction should make the gate
this whole rebuild exists to satisfy WORSE, and nothing should improve.

`layers.showroom_tail` is patched here rather than edited, so the render path
in git is the shipped one at all times and no A/B can be confused with a
delivery.

    .venv/bin/python -m tools.r2_4149_tail_ab --rt60-high 0.45 \
        --out audio/out/r2_4149/master_rt45.wav
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import layers                                         # noqa: E402
from audio import master                                         # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rt60-high", type=float, required=True)
    ap.add_argument("--rt60-low", type=float, default=2.4)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sr", type=int, default=96000)
    a = ap.parse_args()

    out = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    stems = os.path.join(os.path.dirname(out), "stems")
    report = os.path.splitext(out)[0] + ".json"

    orig = layers.showroom_tail

    def patched(excitation, spec, sr, rt60_low=a.rt60_low,
                rt60_high=a.rt60_high):
        return orig(excitation, spec, sr, rt60_low=rt60_low,
                    rt60_high=rt60_high)

    layers.showroom_tail = patched
    print(">> showroom_tail patched: rt60_low %.2f  rt60_high %.3f"
          % (a.rt60_low, a.rt60_high))
    rep = master.build(out, sr=a.sr, report_path=report, stems_dir=stems)
    print(">> STAGE RESULT: %s %.2f LUFS %.2f dBTP"
          % ("AUDIO_MASTER_OK" if rep.get("build_ok", True)
             else "AUDIO_MASTER_MIX_FAILURE",
             rep["master"]["integrated_lufs"],
             rep["master"]["true_peak_dbtp"]))
    return 0 if rep.get("build_ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
