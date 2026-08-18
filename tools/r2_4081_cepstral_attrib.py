#!/usr/bin/env python
"""R2-4081 -- WHERE THE BREACH'S 1.000 ms CEPSTRAL PEAK COMES FROM.

The quefrency ladder (r2_4081_quefrency_bench) showed the beat-3 maximum is a
LOCATED feature at 1.000 ms and not a rail: it stays at 1.000 ms for every
lower bound from 0.20 ms down. So the next question is what is at 1.000 ms.

Two candidates, and they have different owners:

  * THE AUDIO. Some bus in the breach is summed with a ~1 ms delayed copy of
    itself, or carries a 1 kHz-spaced comb for a physical reason.
  * THE INSTRUMENT. G-ROOM runs on `to_mono(x)` = (L+R)/2. If a source arrives
    at the two channels with a ~1 ms relative delay -- which is what a stereo
    pair of receivers 0.18 m apart DOES, and what the retarded-time solve puts
    there on purpose -- then the mono FOLD-DOWN combs at 1 kHz and the cepstrum
    prints a peak at the inter-channel delay that is not in either channel.

The discriminator is direct: measure L alone, R alone and (L+R)/2. A feature
present in mono and absent from both channels is made by the summing.

Then attribute per stem, on the same 36-44 s window, using each stem's own
tails, so the answer names a bus rather than a beat.

    .venv/bin/python -m tools.r2_4081_cepstral_attrib
"""

import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WAV = os.path.join(ROOT, "audio", "out", "r2_4079", "master_R2-4079.wav")
STEMS = os.path.join(ROOT, "audio", "out", "r2_4079", "stems")
OUT = os.path.join(ROOT, "audio", "out", "r2_4081", "cepstral_attrib.json")


def cep_scan(S, sr, q_lo_ms=1.0, q_hi_ms=30.0):
    if S is None:
        return {"peak_over_median": float("nan"), "quefrency_ms": float("nan")}
    L = 0.5 * np.log(np.maximum(S, 1e-20))
    c = np.abs(np.fft.irfft(L))
    q0, q1 = int(q_lo_ms * 1e-3 * sr), min(int(q_hi_ms * 1e-3 * sr), len(c) - 1)
    band = c[q0:q1]
    j = int(np.argmax(band))
    return {"peak_over_median": float(band[j] / max(float(np.median(band)), 1e-20)),
            "quefrency_ms": float((q0 + j) / sr * 1e3)}


def tails_of(seg, sr):
    regions = P.decay_regions(seg, sr)
    S, f, n = P.tail_spectrum(seg, sr, regions)
    return S, n


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    sheet = json.load(open(os.path.join(ROOT, "docs", "beat_sheet.json")))
    x, sr = sf.read(WAV, dtype="float32", always_2d=True)
    beats = P.beats_from_sheet(sheet, len(x) / sr)
    rep = {"channels": {}, "stems": {}}

    print(">> (1) IS IT IN THE CHANNELS, OR IN THE MONO SUM?\n")
    print("    beat            L             R            (L+R)/2")
    for b in beats:
        if b.name not in ("1_assembly", "3_breach", "5_lap", "6_ending"):
            continue
        a, z = int(b.t0 * sr), int(b.t1 * sr)
        rows = {}
        for tag, ch in (("L", x[a:z, 0]), ("R", x[a:z, 1]),
                        ("mono", x[a:z].mean(axis=1))):
            S, n = tails_of(np.ascontiguousarray(ch), sr)
            rows[tag] = cep_scan(S, sr) | {"n_tail_regions": n}
        rep["channels"][b.name] = rows
        print(f"    {b.name:12s} "
              + "  ".join(f"{rows[t]['peak_over_median']:6.2f}x@"
                          f"{rows[t]['quefrency_ms']:6.3f}ms" for t in
                          ("L", "R", "mono")))

    print("\n>> (2) WHICH BUS CARRIES IT? beat 3, each stem's own tails, mono\n")
    b3 = [b for b in beats if b.name == "3_breach"][0]
    tot = None
    for fn in sorted(os.listdir(STEMS)):
        if not fn.endswith(".wav"):
            continue
        name = fn[:-4]
        y, sr2 = sf.read(os.path.join(STEMS, fn), dtype="float32", always_2d=True)
        a, z = int(b3.t0 * sr2), int(b3.t1 * sr2)
        seg = y[a:z]
        pw = float((seg ** 2).mean())
        m = np.ascontiguousarray(seg.mean(axis=1))
        S, n = tails_of(m, sr2)
        r = cep_scan(S, sr2) | {"n_tail_regions": n, "power": pw}
        # and the same stem, one channel only, to separate fold-down again
        SL, _ = tails_of(np.ascontiguousarray(seg[:, 0]), sr2)
        rl = cep_scan(SL, sr2)
        r["L_peak_over_median"] = rl["peak_over_median"]
        r["L_quefrency_ms"] = rl["quefrency_ms"]
        rep["stems"][name] = r
        tot = pw if tot is None else tot + pw
    share = {k: v["power"] / sum(s["power"] for s in rep["stems"].values())
             for k, v in rep["stems"].items()}
    print("    stem                share    mono peak            L peak")
    for k in sorted(rep["stems"], key=lambda k: -share[k]):
        v = rep["stems"][k]
        rep["stems"][k]["share_of_beat3"] = share[k]
        print(f"    {k:20s} {share[k]*100:5.1f}%  "
              f"{v['peak_over_median']:7.2f}x@{v['quefrency_ms']:6.3f}ms  "
              f"{v['L_peak_over_median']:7.2f}x@{v['L_quefrency_ms']:6.3f}ms")

    json.dump(rep, open(OUT, "w"), indent=1)
    print(f"\n>> wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
