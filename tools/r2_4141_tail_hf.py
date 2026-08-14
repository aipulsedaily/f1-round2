#!/usr/bin/env python
"""R2-4141 -- DOES THE SHOWROOM TAIL ACTUALLY DELIVER ITS DECLARED rt60_high?

SUPERSEDED BY `tools/r2_4149_room_hf.py`, AND ITS CONCLUSION IS WITHDRAWN.
Two things below are wrong. (1) It runs at 48 kHz and the FDN runs at the
render's 96 kHz, and `rt60_high` is a NYQUIST target, so this measures a
sample rate the film is not rendered at -- 4 kHz reads 0.90 s here and 1.27 s
at 96 kHz. (2) It compares the measurement against a DECLARED 0.35 s at 4 kHz
that R2-4147(5) showed demands an anechoic surface absorption of 0.967 and
R2-4149 showed does not exist as a target at all: a room's high-frequency
decay is Sabine with the ISO 9613 air term and has no crossover anywhere in
it. Kept because its measurement of the network was sound and it is what
started the question.

`layers.showroom_tail` declares rt60_low 2.4 s and rt60_high 0.35 s, and
R2-4045 moved the high number from 0.85 to 0.35 on the argument that "the FDN's
per-line damping already implements this exactly; the number was simply set too
high". THIS TOOL CHECKS THAT SENTENCE, on the network's own impulse response,
with no film in the way.

WHY IT WAS SUSPECTED. Three beat-1 measurements point at one place:

    G-SUSTAIN   note cover 0.208 (bar 0.20) from ten partials at 2.5-3.8 kHz,
                each holding 0.68-0.90 s -- while the ASSEMBLY STEM that
                produced them reads note cover 0.000
    G-RING      worst 1/6-octave band 1.89 s against a 1.24 s broadband
    G-EVENT     23.40 dB on the layer, 14.69 dB on the master

and the `room` stem measures T60 = 1.0-1.6 s at EVERY band up to 5.7 kHz. A
0.35 s high-frequency tail cannot sustain a 0.9 s partial. Either the number is
not being delivered or the number is not the cause, and this says which.

    .venv/bin/python -m tools.r2_4141_tail_hf
"""

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import dsp                                            # noqa: E402
from audio import percept as P                                   # noqa: E402

SHOWROOM = (30.0, 22.0, 6.5)


def paths(interior_m):
    ix, iy, iz = interior_m
    d = [iz, iy * 0.5, ix * 0.5,
         np.hypot(ix, iy) * 0.5, np.hypot(iy, iz), np.hypot(ix, iz) * 0.5,
         np.sqrt(ix * ix + iy * iy + iz * iz) * 0.5,
         np.sqrt(ix * ix + iy * iy + iz * iz)]
    return sorted(float(x) for x in d)


def ir_t60(sr=48000, dur_s=6.0, rt60_low=2.4, rt60_high=0.35, **kw):
    """T60 per 1/6 octave of the network's own impulse response, by Schroeder
    backward integration over the whole tail -- no gaps, no film, no gates."""
    n = int(dur_s * sr)
    x = np.zeros(n)
    x[0] = 1.0
    y = dsp.fdn_reverb(x, sr, paths(SHOWROOM), rt60_low, rt60_high,
                       c=float(dsp.speed_of_sound(20.0)),
                       n_diffusion=8, extra_lines=8, stereo=False, **kw)
    y = np.asarray(y, dtype=np.float64)
    from scipy import signal as sg
    rows = []
    fc = 250.0
    while fc < sr * 0.4:
        lo, hi = fc / 2 ** (1 / 12.0), fc * 2 ** (1 / 12.0)
        sos = sg.butter(4, [lo, min(hi, sr * 0.45)], btype="bandpass",
                        fs=sr, output="sos")
        b = sg.sosfilt(sos, y)
        q = max(int(sr / 400.0), 1)
        ne = len(b) // q
        p2 = (b[:ne * q] ** 2).reshape(ne, q).mean(axis=1)
        E = np.cumsum(p2[::-1])[::-1]
        le = 10.0 * np.log10(np.maximum(E / max(E[0], 1e-30), 1e-12))
        t = np.arange(ne) / (sr / q)
        m = (le <= -5.0) & (le >= -25.0)
        t60 = float("nan")
        if m.sum() >= 8:
            A = np.polyfit(t[m], le[m], 1)
            if A[0] < 0:
                t60 = -60.0 / A[0]
        rows.append({"f_hz": fc, "t60_s": t60})
        fc *= 2 ** (1 / 6.0)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rows = ir_t60()
    print("THE SHOWROOM FDN'S OWN IMPULSE RESPONSE")
    print("declared: rt60_low 2.40 s, rt60_high 0.35 s above `wet_hf_hz` 4000 Hz")
    print()
    print("%9s %10s %10s" % ("band Hz", "T60 s", "declared"))
    for r in rows:
        want = 2.4 if r["f_hz"] < 4000.0 else 0.35
        print("%9.0f %10.3f %10.2f" % (r["f_hz"], r["t60_s"], want))
    hf = [r["t60_s"] for r in rows if r["f_hz"] >= 4000.0
          and np.isfinite(r["t60_s"])]
    lo = [r["t60_s"] for r in rows if r["f_hz"] < 4000.0
          and np.isfinite(r["t60_s"])]
    print()
    print("median T60 below 4 kHz: %.3f s (declared 2.40)" % np.median(lo))
    print("median T60 above 4 kHz: %.3f s (declared 0.35)" % np.median(hf))
    print()
    print("`wet_hf_hz` is in `dsp.fdn_reverb`'s signature and appears NOWHERE "
          "in its body.\nThe per-line damping is a one-pole whose coefficient "
          "is the gain RATIO gh/g and\nwhose corner therefore falls out of that "
          "ratio instead of being placed at a\nfrequency. For the showroom's "
          "shortest path that corner lands near 10 kHz, so\n`rt60_high` only "
          "applies in the top octave and the whole midrange decays at\n"
          "`rt60_low`.")
    if a.out:
        json.dump(rows, open(a.out, "w"), indent=1)
        print(">> " + a.out)


if __name__ == "__main__":
    main()
