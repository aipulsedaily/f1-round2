#!/usr/bin/env python
"""THE FDN IMPULSE BENCH -- R2-4079(3).

R2-4075(3) reported a regression the previous agent had introduced itself:
G-ROOM(c)'s cepstral peak moved from 38.30x at 11.292 ms -- `master.py`'s
deleted self-delay, sample-exact -- to **11.45x at 1.062 ms**, and 1.062 ms is
`dsp.DIFFUSION_MS[0] = 0.94 ms` plus the network. Eight cascaded Schroeder
allpasses at g = 0.7 with the shortest at 0.94 ms is the textbook recipe for a
METALLIC diffuser: the magnitude is flat by construction, so it adds no ripple,
but the impulse response still has an echo at its own delay and the cepstrum
sees it. It was a 3.3x improvement and it was still a failure, and the cause
was one line.

R2-4076 item 1 named the fix and the number it must move: shortest stage
0.94 -> >= 4 ms, g 0.7 -> 0.55, re-measure THIS number.

THIS BENCH IS THE VERIFICATION, NOT THE ASSUMPTION. It measures, on the
reverberator's own impulse response and with G-ROOM's own estimators
(`percept.cepstral_ripple_of`, `percept.fractional_octave_ripple_of`), the
three quantities the change could move -- and the third one is the one that
matters, because a diffuser can always be made to look better in the cepstrum
by making it do less:

  1. cepstral peak over 1-30 ms  -- the defect, must fall
  2. 1/12-octave ripple 0.4-6 kHz -- must NOT rise: if lengthening the stages
     merely disables the diffusion, the network's own comb comes back
  3. T60 per band against Sabine -- must NOT move: G-RING passes today and a
     diffusion change that alters the decay has changed the room

    python -m tools.r2_4079_fdn_bench
    python -m tools.r2_4079_fdn_bench --sweep      # the candidates, measured
"""

import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import dsp                                          # noqa: E402
from audio import percept as P                                 # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def showroom_delays(spec):
    ix, iy, iz = spec["showroom"]["interior_m"]
    d = [iz, iy * 0.5, ix * 0.5,
         np.hypot(ix, iy) * 0.5, np.hypot(iy, iz), np.hypot(ix, iz) * 0.5,
         np.sqrt(ix * ix + iy * iy + iz * iz) * 0.5,
         np.sqrt(ix * ix + iy * iy + iz * iz)]
    return sorted(float(x) for x in d)


def band_t60(ir, sr, f_c, frac=1):
    """Backward-integrated (Schroeder) T60 of one octave band of an IR."""
    from scipy import signal as sg
    lo, hi = f_c / 2 ** (1 / (2 * frac)), f_c * 2 ** (1 / (2 * frac))
    hi = min(hi, sr * 0.45)
    sos = sg.butter(4, [lo, hi], btype="bandpass", fs=sr, output="sos")
    y = sg.sosfilt(sos, ir)
    e = np.cumsum(y[::-1] ** 2)[::-1]
    e = 10.0 * np.log10(np.maximum(e / max(e[0], 1e-30), 1e-30))
    i0 = int(np.argmax(e <= -5.0))
    i1 = int(np.argmax(e <= -25.0))
    if i1 <= i0:
        return float("nan")
    t = np.arange(i0, i1) / sr
    a = np.polyfit(t, e[i0:i1], 1)[0]
    return float(-60.0 / a) if a < 0 else float("nan")


def measure(sr, delays_m, diffusion_ms, g, rt60_low=2.4, rt60_high=0.35,
            dur_s=4.0):
    """One impulse response, measured with G-ROOM's and G-RING's own tools."""
    n = int(dur_s * sr)
    imp = np.zeros(n)
    imp[0] = 1.0
    ms_saved, g_saved = dsp.DIFFUSION_MS, dsp.DIFFUSION_G
    dsp.DIFFUSION_MS, dsp.DIFFUSION_G = tuple(diffusion_ms), float(g)
    try:
        t0 = time.time()
        ir = dsp.fdn_reverb(imp, sr, delays_m, rt60_low, rt60_high,
                            c=float(dsp.speed_of_sound(20.0)),
                            n_diffusion=len(diffusion_ms), extra_lines=8,
                            stereo=True)
        secs = time.time() - t0
    finally:
        dsp.DIFFUSION_MS, dsp.DIFFUSION_G = ms_saved, g_saved
    out = {"diffusion_ms": list(diffusion_ms), "g": float(g),
           "seconds": round(secs, 2), "channels": {}}
    for ch, label in ((0, "L"), (1, "R")):
        x = ir[:, ch].astype(np.float64)
        # (a) THE GATE'S OWN ESTIMATOR. G-ROOM(c) runs `cepstral_ripple_of` on
        #     `tail_spectrum`, which is a MEAN OF STFT FRAMES at win 16384. That
        #     averaging is not incidental -- it is what makes the statistic a
        #     property of the room rather than of one window -- so the bench
        #     runs it the same way or it is predicting a different number.
        S, f = P._stft_power(x, sr, win=16384, hop=8192)
        Sm = S.mean(axis=0)
        cep = P.cepstral_ripple_of(Sm, sr)
        rip = P.fractional_octave_ripple_of(Sm, f)
        # (b) THE STRUCTURAL VIEW: one long FFT of the whole impulse response,
        #     no frame averaging. This is the view R2-4067's table was taken in
        #     (it reports 40.4x / 59.6x undiffused against 15.4x / 21.2x
        #     rebuilt, numbers the averaged estimator does not produce), and it
        #     is far more sensitive to a single discrete echo. Both are
        #     reported, because a change that only improves one of them has not
        #     removed an echo, it has hidden one.
        nfft = 1 << int(np.ceil(np.log2(len(x))))
        S1 = np.abs(np.fft.rfft(x, n=nfft)) ** 2
        f1 = np.fft.rfftfreq(nfft, 1.0 / sr)
        cep1 = P.cepstral_ripple_of(S1, sr)
        rip1 = P.fractional_octave_ripple_of(S1, f1)
        out["channels"][label] = {
            "cepstral_peak_over_median": cep["peak_over_median"],
            "cepstral_quefrency_ms": cep["quefrency_ms"],
            "ripple_p95_p5_db": rip["ripple_db"],
            "occupancy": rip["occupancy"],
            "ir_fft_cepstral_peak_over_median": cep1["peak_over_median"],
            "ir_fft_cepstral_quefrency_ms": cep1["quefrency_ms"],
            "ir_fft_ripple_p95_p5_db": rip1["ripple_db"],
            "t60_125hz": band_t60(x, sr, 125.0),
            "t60_713hz": band_t60(x, sr, 713.0),
            "t60_2khz": band_t60(x, sr, 2000.0),
        }
    out["lr_correlation"] = float(np.corrcoef(ir[:, 0], ir[:, 1])[0, 1])
    return out


def _row(label, m):
    c = m["channels"]
    print("   %-40s gate-cep %6.2fx @ %6.2f ms | %6.2fx @ %6.2f ms   "
          "IR-fft-cep %7.2fx @ %6.2f ms | %7.2fx @ %6.2f ms   "
          "ripple %5.2f/%5.2f (IR %5.2f/%5.2f) dB   T60 %.2f/%.2f s"
          % (label,
             c["L"]["cepstral_peak_over_median"], c["L"]["cepstral_quefrency_ms"],
             c["R"]["cepstral_peak_over_median"], c["R"]["cepstral_quefrency_ms"],
             c["L"]["ir_fft_cepstral_peak_over_median"],
             c["L"]["ir_fft_cepstral_quefrency_ms"],
             c["R"]["ir_fft_cepstral_peak_over_median"],
             c["R"]["ir_fft_cepstral_quefrency_ms"],
             c["L"]["ripple_p95_p5_db"], c["R"]["ripple_p95_p5_db"],
             c["L"]["ir_fft_ripple_p95_p5_db"], c["R"]["ir_fft_ripple_p95_p5_db"],
             c["L"]["t60_125hz"], c["L"]["t60_713hz"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sr", type=int, default=48000)
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "audio", "out",
                                                  "r2_4079", "fdn_bench.json"))
    a = ap.parse_args()

    spec = json.load(open(os.path.join(ROOT, "docs", "circuit_spec.json")))
    d = showroom_delays(spec)
    print(">> showroom delays (m):", [round(v, 2) for v in d])
    print(">> G-ROOM(c) bar: cepstral peak <= %.1fx; G-ROOM ripple bar %.1f dB; "
          "Sabine RT60 2.40 s"
          % (P.V("G_ROOM.max_cepstral_peak_over_median"),
             P.V("G_ROOM.max_ripple_p95_minus_p5_db")))

    cases = [("SHIPPED R2-4067  0.94 ms, g 0.70",
              (0.94, 1.51, 2.42, 3.87, 6.19, 9.91, 12.7, 16.3), 0.70)]
    if a.sweep:
        cases += [
            ("no diffusion at all (the R2-4067 defect)", (), 0.0),
            ("shortest 4.0 ms, g 0.70",
             (4.03, 5.51, 7.53, 10.3, 14.07, 19.23, 26.29, 35.93), 0.70),
            ("shortest 4.0 ms, g 0.55",
             (4.03, 5.51, 7.53, 10.3, 14.07, 19.23, 26.29, 35.93), 0.55),
            ("shortest 4.0 ms, g 0.45",
             (4.03, 5.51, 7.53, 10.3, 14.07, 19.23, 26.29, 35.93), 0.45),
            ("shortest 5.0 ms, g 0.55",
             (5.01, 6.71, 8.99, 12.05, 16.15, 21.63, 28.99, 38.83), 0.55),
        ]
    cases.append(("PROPOSED  %s ms, g %.2f" % (dsp.DIFFUSION_MS[0],
                                               dsp.DIFFUSION_G),
                  dsp.DIFFUSION_MS, dsp.DIFFUSION_G))

    rows = []
    for label, ms, g in cases:
        m = measure(a.sr, d, ms, g)
        m["label"] = label
        rows.append(m)
        _row(label, m)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump({"sr": a.sr, "delays_m": d, "rows": rows,
                   "bars": {"cepstral": P.V("G_ROOM.max_cepstral_peak_over_median"),
                            "ripple_db": P.V("G_ROOM.max_ripple_p95_minus_p5_db")}},
                  fh, indent=1, default=float)
    print(">> wrote", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
