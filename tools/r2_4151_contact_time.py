#!/usr/bin/env python
"""R2-4151 -- THE CONTACT-TIME LAW, CHECKED BEFORE THE MIX WAS TOUCHED, AND IT
IS NOT THE DEFECT.

    .venv/bin/python -m tools.r2_4151_contact_time

R2-4150(8) left two candidate explanations for the 8.38 dB the mix took off the
rebuilt shard bus, and put arithmetic on both. This file adjudicates the SECOND
one first, because the standing rule is that a guard which fires on a signal
that is genuinely too peaky is RIGHT and the signal is wrong:

    `render_shards` sets t_contact = 8e-5 (1 + 0.6 b)(1 + 2 L), which over the
    picture's 21 mm -> 495 mm size range is a factor of 1.99. Hertzian impact
    of geometrically similar bodies gives t_c ~ (m^2/(R E*^2 v))^(1/5), and for
    a plate (m ~ L^2, R ~ L) that is L^0.6, i.e. 6.7x over the same range. The
    largest fragments' contacts are about 3.4x too short and therefore about
    10.6 dB too peaky -- the same order as the 8.38 dB.

THE FIRST HALF OF THAT IS RIGHT AND THE CONCLUSION IS WRONG, and the reason is
one line of the synthesiser that the arithmetic did not look at.

  * The exponent really is wrong: the shipped law's effective exponent over the
    picture's size range is 0.20 against Hertz's 0.60, and the biggest
    fragments' contacts really are 3.4x too short.
  * BUT `hertz_spectrum` is FLAT BELOW 1/T, and a 433 mm fragment's whole mode
    set sits at 174-2049 Hz while 1/T is 6.7 kHz on the shipped law and 1.7 kHz
    on the Hertz law. Lengthening the contact does not attenuate the peak; it
    attenuates the UPPER MODES, which carry energy and not peak.
  * MEASURED over all 8401 contacts of the picture population: correcting the
    law drops the peak proxy 2.2 dB and the ENERGY proxy 3.7 dB. It makes the
    bus 1.5 dB PEAKIER, not less. The guard would fire HARDER.

So the contact-time law is a real (small) physics error and it is NOT the
mechanism, and it was not implemented in R2-4151 for exactly the reason
R2-4150(8) declined to implement it: deriving a contact-time law while needing
8.4 dB is the situation this project has been wrong in four times.

THE COEFFICIENT IS CHECKED RATHER THAN QUOTED. t_c = 2.9432 delta_max / v is a
textbook result and this project has been burned by a free-plate constant that
was wrong by 13.5x (R2-4149). It is verified here by integrating the Hertz ODE
m d'' = -k d^(3/2) directly, which shares no assumption with the closed form.
"""

import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import layers                                          # noqa: E402

# glass on a concrete floor. 1/E* = (1-nu1^2)/E1 + (1-nu2^2)/E2.
E_CONCRETE, NU_CONCRETE = 30.0e9, 0.20
ESTAR = 1.0 / ((1.0 - layers.GLASS_NU ** 2) / layers.GLASS_E
               + (1.0 - NU_CONCRETE ** 2) / E_CONCRETE)
HERTZ_C = 2.9432
# the contact feature's radius of curvature as a fraction of the piece. It
# enters as alpha^(-1/5), so the whole plausible range 0.01-0.5 -- from a
# fracture-roughness edge to a corner as round as the piece is wide -- spans
# 2.19x, and the SIZE EXPONENT does not depend on it at all.
ALPHA = 0.05


def t_hertz(L, v, alpha=ALPHA):
    """Hertz contact duration for a plate of side L landing at speed v."""
    m = layers.GLASS_RHO * layers.GLASS_H * np.asarray(L, dtype=np.float64) ** 2
    k = (4.0 / 3.0) * ESTAR * np.sqrt(alpha * np.asarray(L, dtype=np.float64))
    return HERTZ_C * (5.0 * m * v ** 2 / (4.0 * k)) ** 0.4 / v


def t_shipped(L, bounce=0):
    return 8.0e-5 * (1.0 + 0.6 * bounce) * (1.0 + 2.0 * np.asarray(L, dtype=np.float64))


def _ode_coefficient(m=0.5, k=2.4e10, v=1.0, n=400000):
    """Integrate m d'' = -k d^1.5 and return t_c / (delta_max / v)."""
    dmax = (5.0 * m * v * v / (4 * k)) ** 0.4
    dt = 4.0 * dmax / v / n
    d, dv, t = 0.0, v, 0.0
    while True:
        dv += (-k * max(d, 0.0) ** 1.5 / m) * dt
        d += dv * dt
        t += dt
        if d <= 0.0:
            return t / (dmax / v)


def main():
    print("0. THE COEFFICIENT, CHECKED RATHER THAN QUOTED")
    print("   Hertz ODE m d'' = -k d^1.5 integrated directly:")
    print("     t_c / (delta_max/v) = %.4f    textbook 2.9432\n" % _ode_coefficient())

    print("1. THE EXPONENT. shipped (1 + 2L) against Hertz L^0.6")
    lo, hi = 0.0213, 0.4950                      # picture median and largest
    e_ship = np.log(t_shipped(hi) / t_shipped(lo)) / np.log(hi / lo)
    print("   E* (glass on concrete) = %.4g Pa, alpha = %.2f" % (ESTAR, ALPHA))
    print("   %-14s %12s %12s %10s" % ("L", "shipped", "Hertz @2 m/s", "ratio"))
    for L in (0.008, 0.0213, 0.05, 0.10, 0.20, 0.4326, 0.4950):
        ts, th = float(t_shipped(L)), float(t_hertz(L, 2.0))
        print("   %10.1f mm %10.3f ms %10.3f ms %10.2fx" % (L * 1e3, ts * 1e3,
                                                            th * 1e3, th / ts))
    print("   effective exponent over %.1f-%.1f mm: shipped %.2f, Hertz 0.60"
          % (lo * 1e3, hi * 1e3, e_ship))
    print("   alpha sweep at L = 433 mm, v = 9.05 m/s: "
          + "  ".join("%.2f->%.3f ms" % (a, t_hertz(0.4326, 9.05, a) * 1e3)
                      for a in (0.01, 0.02, 0.05, 0.10, 0.20, 0.50)))
    print("   -- the exponent is wrong by a factor of 3.4 over the range, and")
    print("      the absolute level is robust: alpha over its whole plausible")
    print("      range moves t_c by 2.19x and the exponent not at all.\n")

    print("2. WHAT CORRECTING IT DOES TO THE BUS, over all 8401 contacts")
    print("   (the peak proxy is max amp.sum(), the energy proxy sum(amp^2))")
    import json
    from tools import r2_4150_breach_rebuild as RB                 # noqa: E402
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = json.load(open(os.path.join(root, "docs", "circuit_spec.json")))
    # the PICTURE's population and the laminate's damping, via R2-4150's patch,
    # because `audio/layers.py` at HEAD still renders the delivered master and
    # therefore still draws its own size law. Nothing here depends on the
    # damping; the population does matter, because the whole question is about
    # the largest fragments.
    with RB.patched(RB.LAMINATE_ETA):
        ev, _summ = RB.rebuilt_ballistics(spec, 16.70928590302728,
                                          RB.picture_fragments())
        n_sh = max((e[2] for e in ev), default=-1) + 1
        mrng = np.random.default_rng(31337 + 7)
        modes = [layers.shard_modes(float(L), mrng)
                 for L in layers._shard_sizes(ev, n_sh)]

    def sums(law, alpha=ALPHA):
        out = np.empty(len(ev))
        for k, (_t, _p, sid, vz_in, bounce, L) in enumerate(ev):
            f, a_mode, _tau, _q = modes[sid]
            vz = max(float(vz_in), 1e-4)
            drive = layers.GLASS_RHO * layers.GLASS_H * L * L * vz
            tc = (t_shipped(L, bounce) if law == "shipped"
                  else t_hertz(L, vz, alpha) * (1.0 + 0.6 * bounce))
            amp = (a_mode * layers.hertz_spectrum(f, tc)
                   * np.asarray(layers.rad_amp(f))
                   * layers._size_highpass(f, L)) * drive
            amax = float(amp.max()) if amp.size else 0.0
            keep = ((f < 96000 * 0.45) & (amp > amax * 1e-4)) if amax > 0 \
                else np.zeros(f.shape, bool)
            out[k] = float(amp[keep].sum())
        return out

    o = sums("shipped")
    print("   %8s %14s %14s %12s" % ("alpha", "peak proxy", "energy proxy", "crest"))
    for alpha in (0.02, 0.05, 0.10, 0.20):
        h = sums("hertz", alpha)
        dp = 20 * np.log10(h.max() / o.max())
        de = 10 * np.log10((h ** 2).sum() / (o ** 2).sum())
        print("   %8.2f %+13.2f dB %+13.2f dB %+11.2f dB" % (alpha, dp, de, dp - de))
    print()
    print("   THE CREST GOES UP. Correcting the contact-time law makes the bus")
    print("   PEAKIER relative to its own loudness, across the whole plausible")
    print("   alpha range, so the peak criterion would take MORE away and not")
    print("   less. R2-4150(8)'s '10.6 dB too peaky' assumed peak ~ 1/T; it is")
    print("   not, because `hertz_spectrum` is flat below 1/T and a large")
    print("   fragment's entire mode set is below 1/T under BOTH laws.")
    print()
    print("   NOT IMPLEMENTED. It is a real error of about 3.4x on the largest")
    print("   fragments' contact hardness and it belongs to whoever next opens")
    print("   the shard synthesiser on its own merits, with nothing riding on")
    print("   the answer.")


if __name__ == "__main__":
    main()
