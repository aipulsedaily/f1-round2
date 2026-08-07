"""PROVE THE FILM BEFORE THE LIFT IS THE SAME FILM, AT THE SOURCE.

    .venv/bin/python tools/audio_prefix_identity.py

`tools/audio_ending_ab.py` compares two finished masters, and it cannot return
zero: `audio/master.py` measures every bus's peak short-term loudness to set its
trim, normalises the whole film to -14 LUFS and iterates a limiter, so a change
confined to the last 11 s still moves ONE BROADBAND GAIN over all 2,978 frames.
That is a mix decision, not a rebuilt beat, and conflating the two is how "the
ending changed" becomes "the film changed".

So the claim is split, and this file proves the half that CAN be exact:

    every world-clock source the render is built from is bit-identical, sample
    for sample, for every world time up to the end of the telemetry.

It runs `audio/scene.py` and `audio/engine.py` twice over the whole world grid --
once with `F1_LAPDOWN=1` and once with `F1_LAPDOWN=0` -- in two subprocesses, so
the module-level `LAPDOWN_ENABLED` is read fresh each time, and compares:

  * every track `Telemetry.sample()` returns,
  * the dry engine signal, its rpm and its gear,
  * the dry tyre signal,

with `==`, not with a tolerance. Anything non-zero before `t_end` is a leak from
the ending into the film and is a defect regardless of how small it is.

The sample rate defaults to 48 kHz rather than the master's 96 kHz. That is a
weaker statement about ALIASING and an identical statement about LEAKAGE, which
is what is being tested; 96 kHz is available with `--sr` and costs about four
minutes and 6 GB.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHILD = r'''
import json, os, sys
import numpy as np
sys.path.insert(0, ROOT_)
from audio.scene import Telemetry
from audio.clock import Clock, WorldGrid
from audio import engine as E, layers as L, scene as S

spec = json.load(open(os.path.join(ROOT_, "docs", "circuit_spec.json")))
clock = Clock(os.path.join(ROOT_, "docs", "beat_sheet.json"), sr=SR_)
grid = WorldGrid(clock)
tel = Telemetry(spec=spec)
tw = grid.t
st = tel.sample(tw, "v_world")
lat, _ = S.lateral_offsets(spec, tel.sample(np.arange(tw[0], tw[-1], 1/240.), "v_world")["pos"])
wc = np.arange(tw[0], tw[-1], 1/240.)
stc = tel.sample(wc, "v_world")
surf_c = S.classify(spec, stc["pos"], stc["track_s"], lat, 20.0)
surf = {k: np.interp(tw, wc, surf_c[k]).astype(np.float32) for k in surf_c}
eng, rpm, gear, _i = E.synth(tw, st["speed"], st["accel_long"], st["slip"],
                             st["wheel_w"], spec, SR_)
tyre, _ti = L.tyres(tw, {k: st[k].astype(np.float32) for k in
                        ("speed", "accel_long", "accel_lat", "slip", "wheel_w")},
                    surf, spec, SR_)
out = {"t_end": float(tel.t_end), "t0": float(tw[0]), "sr": SR_,
       "lapdown": tel._lapdown is not None}
np.savez(OUT_, tw=tw, eng=eng, rpm=rpm.astype(np.float64), gear=gear.astype(np.int16),
         tyre=tyre, **{k: np.asarray(st[k], dtype=np.float64) for k in
                       ("speed", "accel_long", "accel_lat", "slip", "wheel_w",
                        "heading", "s_m", "track_s")},
         pos=st["pos"], meta=np.frombuffer(json.dumps(out).encode(), dtype=np.uint8))
'''


def run(lapdown, sr, path):
    env = dict(os.environ, F1_LAPDOWN="1" if lapdown else "0")
    src = (f"ROOT_ = {ROOT!r}\nSR_ = {sr}\nOUT_ = {path!r}\n" + CHILD)
    script = os.path.join(os.path.dirname(path), "child.py")
    with open(script, "w") as fh:
        fh.write(src)
    try:
        subprocess.run([sys.executable, script], check=True, env=env)
    finally:
        os.unlink(script)
    return np.load(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sr", type=int, default=48000)
    ap.add_argument("--out", default=os.path.join(ROOT, "audio", "out", "ab",
                                                  "prefix_identity.json"))
    args = ap.parse_args()

    # SCRATCH GOES ON DISK, NOT IN /tmp. /tmp here is a 5.9 GB tmpfs, i.e. RAM on
    # an 11 GB box, and each arm's dump is 1.3 GB; the first run of this tool
    # filled it, took 4 GB of memory away from the render running beside it, and
    # then failed with ENOSPC. `cache/` is on /dev/vda3.
    tmp = os.path.join(ROOT, "cache", "prefix_identity")
    os.makedirs(tmp, exist_ok=True)
    try:
        A = run(False, args.sr, os.path.join(tmp, "a.npz"))
        B = run(True, args.sr, os.path.join(tmp, "b.npz"))
    finally:
        pass
    meta = json.loads(bytes(A["meta"]).decode())
    t_end = meta["t_end"]
    tw = A["tw"]
    pre = tw <= t_end
    post = tw > t_end

    rows = {}
    for k in ("speed", "accel_long", "accel_lat", "slip", "wheel_w", "heading",
              "s_m", "track_s", "eng", "rpm", "gear", "tyre"):
        a, b = np.asarray(A[k], dtype=np.float64), np.asarray(B[k], dtype=np.float64)
        rows[k] = {
            "bit_identical_before_t_end": bool((a[pre] == b[pre]).all()),
            "worst_abs_delta_before_t_end": float(np.abs(a[pre] - b[pre]).max()),
            "worst_abs_delta_after_t_end": float(np.abs(a[post] - b[post]).max()),
        }
        # WHERE the leak starts is the whole diagnosis. A worst-case magnitude
        # says a leak exists; the first differing sample says which block, filter
        # or reduction produced it, and how far back it reaches.
        d = np.flatnonzero(a != b)
        if d.size:
            i = int(d[0])
            rows[k]["first_differing_index"] = i
            rows[k]["first_differing_world_t"] = float(tw[i])
            rows[k]["first_differing_s_before_t_end"] = float(t_end - tw[i])
            j = int(np.flatnonzero(np.abs(a[pre] - b[pre]) ==
                                   rows[k]["worst_abs_delta_before_t_end"])[0]) \
                if not rows[k]["bit_identical_before_t_end"] else -1
            rows[k]["worst_before_t_end_at_world_t"] = float(tw[j]) if j >= 0 else None
    a, b = A["pos"], B["pos"]
    rows["pos"] = {
        "bit_identical_before_t_end": bool((a[pre] == b[pre]).all()),
        "worst_abs_delta_before_t_end": float(np.abs(a[pre] - b[pre]).max()),
        "worst_abs_delta_after_t_end": float(np.abs(a[post] - b[post]).max()),
    }

    rep = {
        "sr": args.sr, "t_end_world_s": t_end,
        "world_samples_before_t_end": int(pre.sum()),
        "tracks": rows,
        "ALL_BIT_IDENTICAL_BEFORE_T_END": all(
            r["bit_identical_before_t_end"] for r in rows.values()),
        "note": ("A = F1_LAPDOWN=0 (the pre-R2-943 constant-speed extrapolation), "
                 "B = F1_LAPDOWN=1 (the lap-down). Compared with ==, not with a "
                 "tolerance. This is the claim the finished masters cannot make, "
                 "because master.py's bus trims, -14 LUFS normalisation and "
                 "limiter are all functions of the whole film including its "
                 "ending."),
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(rep, fh, indent=1)
    for k, r in rows.items():
        print(f"  {k:11s} before t_end: bit-identical={r['bit_identical_before_t_end']} "
              f"(worst {r['worst_abs_delta_before_t_end']:.3e})   "
              f"after: {r['worst_abs_delta_after_t_end']:.4g}")
    print(f">> ALL_BIT_IDENTICAL_BEFORE_T_END = {rep['ALL_BIT_IDENTICAL_BEFORE_T_END']}")
    print(f">> {args.out}")
    return 0 if rep["ALL_BIT_IDENTICAL_BEFORE_T_END"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
