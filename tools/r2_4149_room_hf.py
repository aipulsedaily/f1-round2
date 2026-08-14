#!/usr/bin/env python
"""R2-4149 -- WHAT RT60 DOES THIS ROOM ACTUALLY SUPPORT ABOVE 4 kHz?

R2-4147(5) established the half that matters: `rt60_high = 0.35 s at 4 kHz` is
not a target the showroom's materials can reach. Sabine on the room's own
4290 m3 / 1996 m2 demands a surface absorption of 0.967 to get there, which is
an anechoic chamber. THE DECLARATION IS THE DEFECT.

This tool derives the replacement rather than picking one, and it does it in
the shape the room is already declared in everywhere else in this package:

  * THE ROOM'S MATERIALS ARE ONE NUMBER, and it is already declared three times
    -- `layers.showroom_tail`'s own Sabine line (alpha 0.144), `percept.
    SHOWROOM_DECLARED_RT60_S` = 2.4 s, and G-RING's Sabine bar. A single
    frequency-independent surface absorption is what this design declares, and
    correcting a declaration is not licence to invent a materials schedule
    nobody measured.

  * AIR IS NOT A SURFACE and is accounted for separately, which is the whole
    reason a big room goes dark at the top without any treatment doing it.
    Sabine with the air term is RT60 = 0.161 V / (S*alpha + 4 m V), m in
    nepers/m from ISO 9613-1.

The air term is the ONLY frequency dependence in the target, and it is enough:
a 4290 m3 room is 800 m of travel per second of tail.

It then measures what `dsp.fdn_reverb` ACTUALLY delivers, on its own impulse
response, per 1/6 octave -- because the one trap already recorded in this file
is a first-order shelf that LENGTHENED the tail (0.805 -> 0.878 s) because it
only reached its target at Nyquist. No filter's declared corner is believed
here; only its measured decay.

    .venv/bin/python -m tools.r2_4149_room_hf
    .venv/bin/python -m tools.r2_4149_room_hf --sweep
"""

import argparse
import json
import math
import os
import sys

import numpy as np
from scipy import signal as sg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import dsp                                            # noqa: E402

SHOWROOM = (30.0, 22.0, 6.5)
# The temperature `layers.showroom_tail` already passes to `speed_of_sound`.
AIR_T_C = 20.0
# 50 % RH at 101.325 kPa is ISO 9613-1's own reference condition and the
# mid-point of a conditioned building. Declared, not fitted; the sensitivity to
# it is printed below so the reader can see what it is worth.
AIR_RH_PCT = 50.0
AIR_P_KPA = 101.325


def air_alpha_db_per_m(f_hz, t_c=AIR_T_C, rh_pct=AIR_RH_PCT, p_kpa=AIR_P_KPA):
    """ISO 9613-1 atmospheric absorption, dB/m. The closed form, not a table.

    alpha = 8.686 f^2 [ 1.84e-11 (pa/pr)^-1 (T/T0)^0.5
            + (T/T0)^-2.5 ( 0.01275 e^(-2239.1/T) / (frO + f^2/frO)
                          + 0.1068 e^(-3352.0/T) / (frN + f^2/frN) ) ]

    The first term is classical (viscous + thermal conduction); the two others
    are the vibrational relaxation of O2 and of N2, and it is the oxygen
    relaxation that puts the knee in the middle of the audio band.
    """
    f = np.asarray(f_hz, dtype=np.float64)
    T = t_c + 273.15
    T0 = 293.15
    T01 = 273.16
    pr = 101.325
    pa = p_kpa
    # molar concentration of water vapour, % -- ISO 9613-1 Annex B
    psat_over_pr = 10.0 ** (-6.8346 * (T01 / T) ** 1.261 + 4.6151)
    h = rh_pct * psat_over_pr / (pa / pr)
    frO = (pa / pr) * (24.0 + 4.04e4 * h * (0.02 + h) / (0.391 + h))
    frN = (pa / pr) * (T / T0) ** -0.5 * (
        9.0 + 280.0 * h * np.exp(-4.170 * ((T / T0) ** (-1.0 / 3.0) - 1.0)))
    a = 8.686 * f ** 2 * (
        1.84e-11 * (pa / pr) ** -1.0 * (T / T0) ** 0.5
        + (T / T0) ** -2.5 * (
            0.01275 * np.exp(-2239.1 / T) / (frO + f ** 2 / frO)
            + 0.1068 * np.exp(-3352.0 / T) / (frN + f ** 2 / frN)))
    return a


def air_m_nepers_per_m(f_hz, **kw):
    """The `m` that enters Sabine. 4*m*V is an ENERGY loss per second, and the
    dB/m figure is an energy decay too, so m = alpha_dB/m / (10 log10 e)."""
    return air_alpha_db_per_m(f_hz, **kw) / (10.0 * math.log10(math.e))


def room_geometry(interior_m=SHOWROOM):
    ix, iy, iz = interior_m
    v = ix * iy * iz
    s = 2.0 * (ix * iy + ix * iz + iy * iz)
    return v, s


def surface_alpha_from_declared(rt60_low_s, interior_m=SHOWROOM,
                                f_ref_hz=250.0, **kw):
    """The room's surface absorption, backed out of the DECLARED low-frequency
    RT60 with the air term of that same band removed.

    The air term at 250 Hz is 0.6 dB/km -- three parts in a thousand of the
    total loss -- so this is 0.1442 either way. It is done properly anyway,
    because the whole point of this pass is that air is not a surface.
    """
    v, s = room_geometry(interior_m)
    m = float(air_m_nepers_per_m(f_ref_hz, **kw))
    return (0.161 * v / rt60_low_s - 4.0 * m * v) / s


def target_rt60(f_hz, alpha_surface, interior_m=SHOWROOM, **kw):
    """Sabine WITH the air term, which is the whole target curve."""
    v, s = room_geometry(interior_m)
    m = air_m_nepers_per_m(f_hz, **kw)
    return 0.161 * v / (s * alpha_surface + 4.0 * m * v)


def implied_surface_alpha(f_hz, rt60_s, interior_m=SHOWROOM, **kw):
    """The inverse: what surface absorption would a measured RT60 demand, once
    the air of that band has been credited? This is the number that made 0.35 s
    indefensible (0.967) and it is how any replacement is checked."""
    v, s = room_geometry(interior_m)
    m = np.asarray(air_m_nepers_per_m(f_hz, **kw), dtype=np.float64)
    return (0.161 * v / np.asarray(rt60_s, dtype=np.float64) - 4.0 * m * v) / s


# ------------------------------------------------------------ the network ----
def paths(interior_m=SHOWROOM):
    ix, iy, iz = interior_m
    d = [iz, iy * 0.5, ix * 0.5,
         np.hypot(ix, iy) * 0.5, np.hypot(iy, iz), np.hypot(ix, iz) * 0.5,
         np.sqrt(ix * ix + iy * iy + iz * iz) * 0.5,
         np.sqrt(ix * ix + iy * iy + iz * iz)]
    return sorted(float(x) for x in d)


def _t60_of(band, sr):
    """ISO 3382 T20 by Schroeder backward integration, x3. Same estimator
    `percept.band_decay_t60` uses, so the numbers are comparable to the gate."""
    q = max(int(sr / 400.0), 1)
    ne = len(band) // q
    if ne < 12:
        return float("nan")
    p2 = (band[:ne * q] ** 2).reshape(ne, q).mean(axis=1)
    E = np.cumsum(p2[::-1])[::-1]
    le = 10.0 * np.log10(np.maximum(E / max(E[0], 1e-30), 1e-12))
    t = np.arange(ne) / (sr / q)
    m = (le <= -5.0) & (le >= -25.0)
    if m.sum() < 8:
        return float("nan")
    A = np.polyfit(t[m], le[m], 1)
    return -60.0 / A[0] if A[0] < 0 else float("nan")


def network_rt60(sr=48000, dur_s=8.0, rt60_low=2.4, rt60_high=0.35,
                 f_lo=125.0, f_hi=None, n_diffusion=8, extra_lines=8, **kw):
    """T60 per 1/6 octave of the reverberator's OWN impulse response."""
    n = int(dur_s * sr)
    x = np.zeros(n)
    x[0] = 1.0
    y = np.asarray(dsp.fdn_reverb(x, sr, paths(), rt60_low, rt60_high,
                                  c=float(dsp.speed_of_sound(AIR_T_C)),
                                  n_diffusion=n_diffusion,
                                  extra_lines=extra_lines, stereo=False,
                                  **kw), dtype=np.float64)
    if f_hi is None:
        f_hi = sr * 0.45
    rows, fc = [], float(f_lo)
    while fc < f_hi:
        lo, hi = fc / 2 ** (1 / 12.0), min(fc * 2 ** (1 / 12.0), sr * 0.49)
        sos = sg.butter(4, [lo, hi], btype="bandpass", fs=sr, output="sos")
        rows.append({"f_hz": fc, "t60_s": _t60_of(sg.sosfilt(sos, y), sr)})
        fc *= 2 ** (1 / 6.0)
    return rows


def fit_error(rows, alpha_surface, f_lo=250.0, f_hi=16000.0):
    """RMS error in LOG RT60 against the physical target, over the band the
    gates actually read (G-RING runs 200 Hz - 6 kHz; this goes to 16 k so the
    top octave cannot hide)."""
    e = []
    for r in rows:
        if not (f_lo <= r["f_hz"] <= f_hi) or not np.isfinite(r["t60_s"]):
            continue
        tgt = float(target_rt60(r["f_hz"], alpha_surface))
        e.append(math.log(r["t60_s"] / tgt))
    if not e:
        return float("nan"), 0
    return float(np.sqrt(np.mean(np.square(e)))), len(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sr", type=int, default=48000)
    ap.add_argument("--rt60-low", type=float, default=2.4)
    ap.add_argument("--rt60-high", type=float, default=0.35)
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    v, s = room_geometry()
    alpha = surface_alpha_from_declared(a.rt60_low)
    print("THE ROOM, AS DECLARED")
    print("  V = %.0f m3   S = %.0f m2   declared low-frequency RT60 = %.2f s"
          % (v, s, a.rt60_low))
    print("  surface absorption implied, air credited separately: alpha = %.4f"
          % alpha)
    print("  air: ISO 9613-1 at %.0f C, %.0f %% RH, %.3f kPa"
          % (AIR_T_C, AIR_RH_PCT, AIR_P_KPA))
    print()

    print("THE TARGET CURVE -- Sabine with the air term, nothing else")
    print("%9s %12s %12s %10s" % ("f Hz", "air dB/m", "4mV", "target T60 s"))
    for f in (125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0, 16000.0,
              a.sr / 2.0):
        m = float(air_m_nepers_per_m(f))
        print("%9.0f %12.5f %12.1f %10.3f"
              % (f, float(air_alpha_db_per_m(f)), 4.0 * m * v,
                 float(target_rt60(f, alpha))))
    print("  (S*alpha = %.1f, so the air term overtakes the surfaces at the "
          "frequency where 4mV crosses it)" % (s * alpha))
    print()

    rows = network_rt60(sr=a.sr, rt60_low=a.rt60_low, rt60_high=a.rt60_high)
    print("WHAT THE NETWORK DELIVERS, ON ITS OWN IMPULSE RESPONSE "
          "(rt60_low %.2f, rt60_high %.3f)" % (a.rt60_low, a.rt60_high))
    print("%9s %10s %10s %9s %11s"
          % ("f Hz", "measured", "target", "ratio", "alpha it"))
    print("%9s %10s %10s %9s %11s" % ("", "T60 s", "T60 s", "", "implies"))
    for r in rows:
        if not np.isfinite(r["t60_s"]):
            print("%9.0f %10s" % (r["f_hz"], "nan"))
            continue
        tgt = float(target_rt60(r["f_hz"], alpha))
        ia = float(implied_surface_alpha(r["f_hz"], r["t60_s"]))
        print("%9.0f %10.3f %10.3f %9.3f %11.4f"
              % (r["f_hz"], r["t60_s"], tgt, r["t60_s"] / tgt, ia))
    err, n = fit_error(rows, alpha)
    print()
    print("log-RMS error against the physical room, 250 Hz - 16 kHz: "
          "%.4f over %d bands (%.1f %% in T60)"
          % (err, n, 100.0 * (math.exp(err) - 1.0)))

    if a.sweep:
        print()
        print("THE SWEEP. `rt60_high` is the network's NYQUIST target, not its "
              "4 kHz one --")
        print("the per-line damper is a one-pole whose corner falls out of the "
              "gain ratio.")
        print("%10s %9s %9s %9s %9s %9s %9s"
              % ("rt60_high", "250 Hz", "1 kHz", "4 kHz", "8 kHz", "16 kHz",
                 "logRMS"))
        best = None
        for rh in (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.45, 0.60, 0.80, 1.10,
                   1.50, 2.00):
            rr = network_rt60(sr=a.sr, rt60_low=a.rt60_low, rt60_high=rh)
            e, _ = fit_error(rr, alpha)
            pick = {}
            for f in (250.0, 1000.0, 4000.0, 8000.0, 16000.0):
                c = min(rr, key=lambda r: abs(math.log(r["f_hz"] / f)))
                pick[f] = c["t60_s"]
            print("%10.2f %9.3f %9.3f %9.3f %9.3f %9.3f %9.4f"
                  % (rh, pick[250.0], pick[1000.0], pick[4000.0],
                     pick[8000.0], pick[16000.0], e))
            if best is None or e < best[1]:
                best = (rh, e)
        print()
        print(">> best `rt60_high` on this grid: %.2f s (logRMS %.4f)" % best)

    if a.out:
        json.dump({"volume_m3": v, "surface_m2": s,
                   "surface_alpha": alpha,
                   "air": {"t_c": AIR_T_C, "rh_pct": AIR_RH_PCT,
                           "p_kpa": AIR_P_KPA},
                   "target": [{"f_hz": r["f_hz"],
                               "target_t60_s": float(target_rt60(r["f_hz"],
                                                                 alpha))}
                              for r in rows],
                   "network": rows,
                   "log_rms_error": err},
                  open(a.out, "w"), indent=1)
        print(">> " + a.out)


if __name__ == "__main__":
    main()
