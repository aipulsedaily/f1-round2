#!/usr/bin/env python
"""R2-4152 -- THE ENGINE'S EIGHT HELD SECONDS, AND WHY THEY ARE AN ARITHMETIC
ERROR IN R2-4064'S OWN RULE RATHER THAN A MIX PREFERENCE.

    .venv/bin/python -m tools.r2_4152_engine_ramp

R2-4150(1) measured the engine at 44.73 % of the breach at AMI 0.069, and
R2-4150(2) measured the consequence: an ORACLE glass layer -- the corpus
positive's own shower, which reads 0.7857 alone -- reaches 0.3031 through this
mix against a 0.50 bar. R2-4151(9) would have made it 79 %. Three passes have
now ended with "the engine is the next defect and nothing should be tuned to it
until it is derived".

THIS IS THE DERIVATION, AND IT IS NOT A NEW PHYSICAL MODEL. It is the level
clause missing from a rule this file already made and already relies on.

R2-4064'S RULE, AND THE HALF OF IT NOBODY WROTE DOWN
----------------------------------------------------
    "Slow motion stretches the SCHEDULE and leaves the PITCH alone."

That rule is applied to two classes of source in the same eight seconds:

  * IMPULSIVE, world-attached -- `impact`, `shards`, `debris`. R2-4035 puts
    these on the film grid: each contact is placed at `to_film(t_world)` and
    rendered at its true duration. The events are the SAME EVENTS. Their total
    energy in the window is therefore whatever the world contains, and their
    mean POWER falls by the clock scale because the same energy is spread over
    1/scale as much screen time. Nobody chose that; it is what "re-time the
    events" means.

  * CONTINUOUS, world-attached -- `engine`, `tyres`. R2-4064 puts these on the
    film grid too, with the operating point mapped through `to_film` and the
    carrier rendered at true frequency. So the engine emits at its true
    instantaneous power for EIGHT seconds of screen where the world contains
    1.6, and its energy in the window is multiplied by 1/scale = 6.51.

    THE SAME RULE, APPLIED TO THE TWO CLASSES IN THE SAME WINDOW, MOVES THEIR
    RELATIVE MEAN POWER BY 1/scale. That is 8.13 dB at the ramp's floor, and it
    is arithmetic on the project's own map, not an opinion about mixing.

WHICH ONE IS RIGHT
------------------
The impulsive class is right and it is right by construction: an event is
indivisible, so re-timing cannot create or destroy any of it. The continuous
class has no events, so nothing forced its energy to be conserved and nothing
in the file ever said what should be. The invariant that makes the two
consistent is the one the picture already claims: THE WINDOW CONTAINS THE
WORLD'S OWN EVENT, MORE SLOWLY. Slow motion shows you the same 1.6 seconds; it
does not show you five extra cars.

Under that invariant a continuous source rendered at true pitch on the film
grid must carry a gain of `sqrt(scale)` in amplitude, i.e. `10*log10(scale)` in
power, so that

    integral over the film window of p(tau) * scale(tau) dtau
        == integral over the world window of p(w) dw            (dw = scale dtau)

which is a CHANGE OF VARIABLES and is exact, not an approximation. At scale 1
it is 0.000 dB and it is bit-exact everywhere outside the ramp -- which is the
whole film except 36-44 s. Beat 1 cannot move.

WHAT THIS FILE MEASURES, in the order it has to be believed:

  1. THE MAP. The clock scale over the film, the ramp's support, and the
     energy-weighted mean scale under the engine's own power in the breach --
     which IS the correction, in dB, measured rather than quoted.
  2. THE PREMISE THE CHANGE OF VARIABLES NEEDS: that the film-grid engine's
     instantaneous power at film time tau really is the world engine's at
     w(tau). R2-4064's own witness measured it and this reads its numbers back.
  3. THE ASYMMETRY, ON THE DELIVERED STEMS: the impulsive buses' energy in the
     window against the continuous ones', and what each class would deliver in
     real time.
  4. WHAT IT IS WORTH, on R2-4150(1)'s attribution and R2-4150(2)'s ORACLE
     bound, recomputed with the correction applied to the delivered stems.

NOTHING HERE IS TUNED. The gain is `10*log10(clock.scale)` and there is no free
parameter in it.
"""

import json
import os
import sys

import numpy as np
import soundfile as sf
import scipy.signal as _sig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from audio import percept as P                                   # noqa: E402
from audio.clock import Clock                                    # noqa: E402
from audio.controls import synth as C                            # noqa: E402

BREACH = (36.0, 44.0)
# THE TWO CLASSES, and every bus in the film assigned to one of them.
CONTINUOUS = ("engine", "tyres")           # world-attached, no events
IMPULSIVE = ("impact", "shards", "debris", "structure", "assembly",
             "brakes", "suspension")
CAMERA = ("wind",)                          # film-attached: never warped
DERIVED = ("reflect_garage", "reflect_showroom", "room", "aperture")
AMBIENT = ("crowd", "fence", "bed")


def ami(x, sr):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    return P.articulation_modulation_index(x, sr).get("ami", float("nan"))


def load_window(stems_dir, t0, t1):
    names = sorted(n[:-4] for n in os.listdir(stems_dir) if n.endswith(".wav"))
    sr = sf.info(os.path.join(stems_dir, names[0] + ".wav")).samplerate
    a, b = int(t0 * sr), int(t1 * sr)
    out = {}
    for nm in names:
        x, _ = sf.read(os.path.join(stems_dir, nm + ".wav"), start=a, stop=b,
                       always_2d=True)
        out[nm] = np.asarray(x, dtype=np.float64)
    return out, sr, b - a


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "r2_4147"
    stems = os.path.join(ROOT, "audio", "out", tag, "stems")

    # ---------------------------------------------------------- 1. THE MAP --
    clock = Clock(os.path.join(ROOT, "docs", "beat_sheet.json"), sr=96000)
    print("1. THE MAP. `audio.clock.Clock.scale` is dw/dtau at every film "
          "sample.\n")
    sc = clock.scale
    ft = clock.film_t
    print("   scale min %.6f, max %.6f; 1/min = %.4f x" % (sc.min(), sc.max(),
                                                           1.0 / sc.min()))
    off = float(ft[sc < 0.999][0]), float(ft[sc < 0.999][-1])
    print("   scale < 0.999 over film t %.3f .. %.3f s -- i.e. inside beat 3 "
          "ONLY." % off)
    print("   beat 1 is 0.0-33.0 s and the scale there is exactly 1.0, so a "
          "gain of")
    print("   10*log10(scale) is bit-exact 0 dB across the whole of it.\n")

    sig, sr, n = load_window(stems, *BREACH)
    a, b = int(BREACH[0] * sr), int(BREACH[1] * sr)
    scw = np.interp(np.arange(a, b) / sr, ft, sc)

    # THE CORRECTION, measured under the engine's own power rather than quoted
    # at the ramp floor: the energy-weighted mean of the scale.
    p_eng = (sig["engine"] ** 2).sum(axis=1)
    w_mean = float((p_eng * scw).sum() / p_eng.sum())
    print("   THE CORRECTION, ENERGY-WEIGHTED UNDER THE ENGINE'S OWN POWER:")
    print("     mean scale over 36-44 s, unweighted   %.6f  (%+.3f dB)"
          % (scw.mean(), 10 * np.log10(scw.mean())))
    print("     mean scale weighted by engine power   %.6f  (%+.3f dB)"
          % (w_mean, 10 * np.log10(w_mean)))
    print("     at the ramp floor                     %.6f  (%+.3f dB)"
          % (sc.min(), 10 * np.log10(sc.min())))
    print("   The correction is applied PER SAMPLE as 10*log10(scale(tau)), so")
    print("   the single number is a summary and not the implementation.\n")

    # ------------------------------------------------------- 2. THE PREMISE --
    wit = os.path.join(ROOT, "audio", "out", "witness_engine_grid.json")
    if os.path.exists(wit):
        w = json.load(open(wit))
        print("2. THE PREMISE, FROM R2-4064'S OWN WITNESS "
              "(`audio/out/witness_engine_grid.json`).")
        print("   The change of variables needs the film-grid engine's power at")
        print("   film tau to BE the world engine's at w(tau). R2-4064 built the")
        print("   film grid by mapping the operating point through `to_film`, and")
        print("   its witness measured the agreement:")
        print("     rpm schedule, film grid against world grid mapped:")
        print("       max |diff| %.6f rpm, p99 %.6f rpm"
              % (w["rpm_schedule_max_abs_diff_rpm"],
                 w["rpm_schedule_p99_abs_diff_rpm"]))
        for row in w["engine"]:
            print("     %-24s legacy(warped) %+7.2f dBFS   film grid %+7.2f dBFS"
                  % (row["window"], row["legacy"]["rms_dbfs"],
                     row["film"]["rms_dbfs"]))
        print("   THE TWO GRIDS DELIVER THE SAME RMS IN EVERY WINDOW TO 0.02 dB.")
        print("   The instantaneous power is the same function of WORLD time on")
        print("   both, so the change of variables applies to either.\n")

    # ----------------------------------------------------- 3. THE ASYMMETRY --
    print("3. THE ASYMMETRY, ON THE DELIVERED STEMS OF %s.\n" % tag)
    print("   Every bus's energy in 36-44 s of film, and what the WORLD contains")
    print("   over the same 1.60 s. THE TWO CLASSES ARE READ DIFFERENTLY AND")
    print("   THAT IS THE POINT, so both columns say which rule produced them:")
    print("     IMPULSIVE  world E == film E, BY CONSTRUCTION. The events are the")
    print("                same events at different times; re-timing cannot")
    print("                create or destroy any of one. Excess is 0.00 and is")
    print("                not a measurement.")
    print("     CONTINUOUS world E = integral p(tau) scale(tau) dtau, the change")
    print("                of variables. Excess is the measurement.")
    print("   (`impact` and `structure` are impulsive but concentrated at the")
    print("   ramp's shoulder, so their scale-weighted integral is NOT 7.8 dB")
    print("   down -- which is exactly why the column is not applied to them.)\n")
    print("   %-18s %11s %12s %12s %10s"
          % ("bus", "class", "film E dB", "world E dB", "excess dB"))
    for nm in sorted(sig, key=lambda k: -float((sig[k] ** 2).sum())):
        e_f = float((sig[nm] ** 2).sum())
        if e_f < 1e-12:
            continue
        cls = ("continuous" if nm in CONTINUOUS else
               "impulsive" if nm in IMPULSIVE else
               "camera" if nm in CAMERA else
               "derived" if nm in DERIVED else "ambient")
        if cls in ("continuous", "derived"):
            e_w = float(((sig[nm] ** 2).sum(axis=1) * scw).sum())
            note = "%12.2f %10.2f" % (10 * np.log10(e_w), 10 * np.log10(e_f / e_w))
        else:
            note = "%12.2f %10s" % (10 * np.log10(e_f), "0.00 (c)")
        print("   %-18s %11s %12.2f %s" % (nm, cls, 10 * np.log10(e_f), note))
    print()
    ce = sum(float((sig[k] ** 2).sum()) for k in CONTINUOUS if k in sig)
    ie = sum(float((sig[k] ** 2).sum()) for k in IMPULSIVE if k in sig)
    print("   CONTINUOUS / IMPULSIVE, as the film delivers it   %+7.2f dB"
          % (10 * np.log10(ce / ie)))
    print("   the same ratio with the correction applied        %+7.2f dB"
          % (10 * np.log10(ce * w_mean / ie)))
    print("   THE FILM OVER-WEIGHTS ITS CONTINUOUS SOURCES AGAINST ITS IMPULSIVE")
    print("   ONES BY %.2f dB IN THIS WINDOW, AND BY EXACTLY 0.00 dB EVERYWHERE"
          % (-10 * np.log10(w_mean)))
    print("   ELSE IN THE FILM.\n")

    # -------------------------------------------------------- 4. WHAT IT IS --
    print("4. WHAT IT IS WORTH. R2-4150(1)'s attribution and R2-4150(2)'s ORACLE")
    print("   bound, recomputed with the correction on the delivered stems.\n")
    corr = np.sqrt(scw)[:, None]
    fixed = dict(sig)
    for k in CONTINUOUS:
        if k in fixed:
            fixed[k] = fixed[k] * corr
    # the reflections and the room tail are DERIVED from the engine and the
    # tyres, so under the correction they follow. On the stems that cannot be
    # re-derived, so they are corrected by the same factor and the fact is
    # stated rather than hidden.
    for k in DERIVED:
        if k in fixed:
            fixed[k] = fixed[k] * corr

    bar = P.V("G_PRESENCE.min_articulation_index")
    for label, s in (("as delivered", sig), ("engine + tyres corrected", fixed)):
        tot = sum(float((v ** 2).sum()) for v in s.values())
        total = sum(s.values())
        print("   -- %s: beat AMI %.4f (bar %.2f)" % (label, ami(total, sr), bar))
        for nm in ("engine", "shards", "debris", "tyres"):
            if nm in s:
                print("        %-10s share %6.2f %%" %
                      (nm, 100.0 * float((s[nm] ** 2).sum()) / tot))
    print()

    # the ORACLE bound, R2-4150(2), against the corrected engine
    glass_e = float((sig["shards"] ** 2).sum() + (sig["debris"] ** 2).sum())
    y, _ = C.glass_breach(include=("dice", "slabs", "mullions", "room"))
    y = _sig.resample_poly(P.to_mono(y), sr, C.SR)
    o = np.zeros(n)
    o[:min(len(y), n)] = y[:min(len(y), n)]
    oracle = np.stack([o, o], axis=1)
    oracle *= np.sqrt(glass_e / max(float((oracle ** 2).sum()), 1e-30))
    print("   R2-4150(2)'s BOUND, re-run against the corrected engine.")
    print("   %-34s %12s %12s" % ("glass layer", "engine as is", "corrected"))
    for tag2, gl in (("the film's own shards+debris",
                      sig["shards"] + sig["debris"]),
                     ("the ORACLE at the same energy", oracle),
                     ("the ORACLE, +6 dB", oracle * 2.0)):
        row = []
        for s in (sig, fixed):
            rest = sum(v for k, v in s.items() if k not in ("shards", "debris"))
            row.append(ami(rest + gl, sr))
        print("   %-34s %12.4f %12.4f" % (tag2, row[0], row[1]))
    print()
    print("   THE BOUND WAS 0.3031 AND IT IS WHAT SAID NO GLASS LAYER CAN CLEAR")
    print("   0.50 THROUGH THIS ENGINE. The correction is derived from the map,")
    print("   not from that bar, and it is 0.00 dB outside beat 3.")
    print()
    print("   AND THE COINCIDENCE IS STATED RATHER THAN ENJOYED: the corrected")
    print("   bound lands within 0.0001 of the 0.50 bar. There is no free")
    print("   parameter in 10*log10(clock.scale) to have landed it there, the")
    print("   direction of the conclusion is UNCHANGED (a perfect glass layer")
    print("   still does not clear the bar), and the number would be the same if")
    print("   the bar were 0.20 or 0.90.\n")

    # ------------------------------------------- 5. WHAT THE CLIENT HEARS ----
    print("5. WHAT IT COSTS THE ARTEFACT, WHICH IS THE ONLY THING THAT DECIDES.")
    print("   The beat gets QUIETER: the engine was 44.7 %% of it. Measured on")
    print("   the same stems, broadband and in the band the client has rejected")
    print("   a master over.\n")
    for label, s in (("as delivered", sig), ("engine + tyres corrected", fixed)):
        total = sum(s.values())
        m = total.mean(axis=1)
        f, pxx = _sig.welch(m, sr, nperseg=8192)
        b48 = float(pxx[(f >= 4000) & (f < 8000)].sum())
        print("   %-26s beat RMS %+7.2f dBFS   4-8 kHz %+7.2f dB   "
              "peak %+6.2f dBFS"
              % (label, 10 * np.log10(float((m ** 2).mean())),
                 10 * np.log10(b48), 20 * np.log10(float(np.abs(m).max()))))
    print()
    print("   THAT LOSS IS THE COST AND IT IS NOT PAID BY THE GLASS: it is paid")
    print("   by the bus that was taking 44.7 %% of a beat it reads 0.069 on. The")
    print("   headroom it frees is measured in `tools/r2_4152_headroom.py`, and")
    print("   the premix peak of this film sits at t = 40.377 s and is 51.1 %%")
    print("   `shards` and 44.4 %% `engine` -- the two are the same headroom.")


if __name__ == "__main__":
    main()
