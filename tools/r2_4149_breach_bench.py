#!/usr/bin/env python
"""R2-4149 -- THE BREACH POSITIVE, AND WHAT IT SAYS ABOUT G-PRESENCE's BAR.

R2-4148 reported G-PRESENCE FAIL at `3_breach` (AMI 0.1409) and deliberately
did not chase it, for a reason about the instrument: **the AMI bar is
control-derived from a corpus whose only positive is C9, and C9 is a BEAT-1
control.** A decaying tail has a smooth envelope by definition, so whether
0.1409 was a defect or the instrument reaching past its own validation could
not be decided without a breach-beat positive. That is what `synth.glass_breach`
is, and this is the bench that reads it.

WHAT MUST BE TRUE BEFORE THE ANSWER IS BELIEVED, and all of it is printed:

  1. THE POSITIVE MUST BE STABLE ACROSS SEEDS. A bar derived from one draw of
     a random process is a bar drawn through a point.
  2. THE POSITIVE MUST STILL FAIL WHEN IT IS SPOILED. The same breach with its
     own spectrum, stationary, must read like a hair dryer, or the statistic is
     measuring the material's spectrum rather than its articulation.
  3. THE STATISTIC'S OWN NULLS MUST BE MEASURED. They are, and one of them is
     ugly: a SINGLE IMPULSE in 8 s of digital silence reads 37.13.

    .venv/bin/python -m tools.r2_4149_breach_bench
"""

import argparse
import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                   # noqa: E402
from audio.controls import synth as C                            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ami(x, sr=C.SR):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = P.to_mono(x)
    return P.articulation_modulation_index(x, sr).get("ami", float("nan"))


def presence(x, sr, name="3_breach"):
    """G-PRESENCE on one 8 s signal, calibrated on its own loudness -- which is
    what the corpus does for every other control."""
    from audio import dsp                                        # noqa: PLC0415
    mono = P.to_mono(x) if np.ndim(x) > 1 else np.asarray(x, dtype=np.float64)
    st = x if np.ndim(x) > 1 else np.stack([mono, mono], axis=1)
    li, _, _ = dsp.loudness_lufs(st, sr)
    beats = [P.Beat(name, 0.0, len(mono) / sr)]
    return P.g_presence(mono, sr, beats, lufs_i=li)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav", default=os.path.join(
        ROOT, "audio", "out", "r2_4147", "master_R2-4147.wav"))
    ap.parse_args()

    bar = P.V("G_PRESENCE.min_articulation_index")
    print("G-PRESENCE's AMI bar is %.2f, control-derived, and every number "
          "below is\nmeasured with the SHIPPED estimator, unchanged.\n" % bar)

    # -- 1. the positive, over seeds --------------------------------------
    print("1. C10 GLASS BREACH -- the positive this corpus did not have")
    print("%42s %10s %10s" % ("", "AMI", "fragments"))
    vals = []
    for s in (6031, 111, 999, 2024, 7):
        x, nf = C.glass_breach(seed=s)
        a = ami(x)
        vals.append(a)
        print("%42s %10.4f %10d" % ("seed %d" % s, a, nf))
    print("%42s %10.4f" % ("median over five seeds", float(np.median(vals))))
    print()

    # -- 2. what it is made of --------------------------------------------
    print("2. THE ABLATIONS -- which part of a breach carries its "
          "articulation")
    for inc, what in (
            (("shatter", "dice", "slabs", "mullions", "room"),
             "everything: the car goes through the pane"),
            (("dice", "slabs", "mullions", "room"),
             "the SHOWER ALONE, no car impact  <- the conservative positive"),
            (("shatter", "room"), "the impact alone, nothing falling"),
            (("dice", "room"), "the fine dice alone -- a wash by the physics"),
            (("slabs", "mullions", "room"),
             "the large pieces alone -- what a listener can count"),
            (("dice", "slabs", "mullions"), "the shower with no room at all")):
        x, _ = C.glass_breach(include=inc)
        print("%42s %10.4f" % (what, ami(x)))
    print()

    # -- 3. the anti-cheat -------------------------------------------------
    print("3. THE SAME BREACH, SPOILED -- these must NOT pass")
    x, _ = C.glass_breach()
    print("%42s %10.4f" % ("C10, its own spectrum, stationary",
                           ami(C.octave_matched_noise(x, C.SR))))
    print()

    # -- 4. the statistic's own nulls -------------------------------------
    print("4. AMI's OWN NULLS, and one of them is a hole")
    sr, n = C.SR, int(8.0 * C.SR)
    z = np.zeros(n)
    z[sr] = 1.0
    rows = [("one impulse in 8 s of digital silence", z)]
    for db, lbl in ((-80.0, "80 dB"), (-40.0, "40 dB")):
        y = z + np.random.default_rng(1).standard_normal(n) * 10.0 ** (db / 20.0)
        rows.append(("the same impulse %s over a noise floor" % lbl, y))
    rows.append(("white noise",
                 np.random.default_rng(2).standard_normal(n)))
    for lbl, y in rows:
        print("%42s %10.4f" % (lbl, ami(y, sr)))
    print()
    print("   A SINGLE CLICK IN SILENCE IS THE BEST AMI THERE IS, and it is")
    print("   the same shape as the hole G-EVENT already has -- a relative")
    print("   statistic normalised by a mean that silence drives to zero.")
    print("   It is reported, NOT used: the conservative positive above")
    print("   contains no such transient and still clears the bar.")
    print()

    # -- 5. the film ------------------------------------------------------
    x, srm = sf.read(os.path.expanduser(sys.argv[0]) if False else
                     os.path.join(ROOT, "audio", "out", "r2_4147",
                                  "master_R2-4147.wav"), always_2d=True)
    mono = P.to_mono(x)
    sheet = json.load(open(os.path.join(ROOT, "docs", "beat_sheet.json")))
    print("5. THE FILM, beat by beat, with the envelope statistic that "
          "explains it")
    print("%12s %8s %10s %14s %14s"
          % ("beat", "s", "AMI", "env p95-p5 dB", "peak-median dB"))
    for b in P.beats_from_sheet(sheet, len(mono) / srm):
        s = P._slice(mono, srm, b)
        e, _ = P.broadband_envelope(s, srm, env_hz=200.0)
        le = 20.0 * np.log10(np.maximum(e, 1e-12))
        print("%12s %8.1f %10.4f %14.1f %14.1f"
              % (b.name, b.t1 - b.t0, ami(s, srm),
                 float(np.percentile(le, 95) - np.percentile(le, 5)),
                 float(le.max() - np.median(le))))
    print()

    # -- 6. the verdict ----------------------------------------------------
    xs, _ = C.glass_breach(include=("dice", "slabs", "mullions", "room"))
    a_cons = ami(xs)
    print("6. THE ANSWER")
    print("   the conservative breach positive reads %.4f against a %.2f bar."
          % (a_cons, bar))
    if a_cons >= bar:
        print("   A GOOD BREACH CLEARS THE CURRENT BAR, so the bar is NOT "
              "wrong for this")
        print("   beat and it is NOT MOVED. The film's 0.1409 is the audio.")
    else:
        print("   A GOOD BREACH CANNOT CLEAR THE CURRENT BAR: the bar is "
              "outside its own")
        print("   validation at this beat and moving it is legitimate, as "
              "source=control-derived.")
    print()
    print("   G-PRESENCE on the conservative positive, calibrated on its own "
          "loudness:")
    r = presence(xs, C.SR)
    for k, v in r["per_beat"].items():
        print("     %s: %s  sens %.2f dB, %.0f bands, AMI %.4f"
              % (k, v["outcome"], v["gap_sensation_db"],
                 v["gap_bands_audible"], v["articulation_index"]))
    for f in r["failures"]:
        print("     FAIL: " + f)
    for f in r["inapplicable"]:
        print("     INAPPLICABLE: " + f)


if __name__ == "__main__":
    main()
