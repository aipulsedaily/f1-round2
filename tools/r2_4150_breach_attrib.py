#!/usr/bin/env python
"""R2-4150 -- WHAT IS ACTUALLY IN THE FILM'S BREACH, BUS BY BUS, AND WHAT THE
BEST POSSIBLE GLASS LAYER COULD DO ABOUT IT.

R2-4149 named the breach as the film's largest un-actioned audio defect and
handed the next agent a model of it: *the film is almost entirely fine dice, a
uniform wash of tiny fragments with nothing large in it.* That model came from
a NUMBER MATCH -- the corpus positive's dice-only ablation reads 0.153 and the
film reads 0.141 -- and a number match is not an attribution. This is the
attribution, and it says something different.

    .venv/bin/python -m tools.r2_4150_breach_attrib

WHAT IT MEASURES, all on the shipped estimator and the shipped stems:

  1. AMI of every bus alone over 36-44 s, its share of the window's energy, and
     the sum's AMI with each bus removed. THE DRAG IS NOT WHERE THE MODEL SAID.
  2. THE FEASIBILITY BOUND. The corpus positive's own shower is substituted for
     the film's shards+debris at the same delivered energy -- an ORACLE glass
     layer, one that reads 0.79-1.31 on its own -- and the sum is read. If a
     perfect glass layer cannot clear the bar through the rest of this mix,
     then rebuilding the glass alone cannot be the whole answer, and that is
     worth knowing BEFORE anything is built rather than after.
  3. THE FILM'S OWN FRAGMENT POPULATION against the DELIVERED FRAMES'. The
     picture's fracture is published per shard in `sim/out/breach_sim.json`,
     which is tracked; the audio invents its own.

Nothing here changes a threshold, a level or a generator. It measures.
"""

import argparse
import json
import os
import sys

import numpy as np
import soundfile as sf
import scipy.signal as _sig

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                   # noqa: E402
from audio.controls import synth as C                            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEMS = os.path.join(ROOT, "audio", "out", "r2_4147", "stems")
BREACH = (36.0, 44.0)


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
    ap = argparse.ArgumentParser()
    ap.add_argument("--stems", default=STEMS)
    a = ap.parse_args()

    bar = P.V("G_PRESENCE.min_articulation_index")
    sig, sr, n = load_window(a.stems, *BREACH)
    tot = sum(float((v ** 2).sum()) for v in sig.values())
    total = sum(sig.values())

    print("G-PRESENCE's AMI bar is %.2f. `3_breach` = %.1f-%.1f s of "
          "%s\n" % (bar, BREACH[0], BREACH[1], os.path.relpath(a.stems, ROOT)))

    # -- 1. the buses -------------------------------------------------------
    print("1. EVERY BUS ALONE, ITS SHARE OF THE WINDOW, AND THE SUM WITHOUT IT")
    print("%-18s %10s %9s %12s" % ("bus", "AMI alone", "share %", "sum without"))
    order = sorted(sig, key=lambda k: -float((sig[k] ** 2).sum()))
    for nm in order:
        e = 100.0 * float((sig[nm] ** 2).sum()) / tot
        if e < 0.02:
            continue
        print("%-18s %10.4f %9.2f %12.4f"
              % (nm, ami(sig[nm], sr), e, ami(total - sig[nm], sr)))
    print("%-18s %10.4f %9.2f" % ("THE SUM", ami(total, sr), 100.0))
    print()

    # -- 2. the feasibility bound ------------------------------------------
    glass_e = float((sig["shards"] ** 2).sum() + (sig["debris"] ** 2).sum())
    print("2. THE BOUND. The corpus positive's own shower substituted for "
          "shards+debris\n   at the SAME delivered energy (%.1f %% of the "
          "window), against engine trim." % (100.0 * glass_e / tot))
    y, _ = C.glass_breach(include=("dice", "slabs", "mullions", "room"))
    y = _sig.resample_poly(P.to_mono(y), sr, C.SR)
    o = np.zeros(n)
    o[:min(len(y), n)] = y[:min(len(y), n)]
    oracle = np.stack([o, o], axis=1)
    oracle *= np.sqrt(glass_e / max(float((oracle ** 2).sum()), 1e-30))
    rest = {k: v for k, v in sig.items() if k not in ("shards", "debris")}
    no_eng = sum(v for k, v in rest.items() if k != "engine")
    cols = (1.0, 0.5, 0.25, 0.0)
    print("%-36s %s" % ("glass layer \\ engine",
                        "".join("%10s" % ("%+.0f dB" % (20 * np.log10(g))
                                          if g else "muted") for g in cols)))
    for tag, gl in (("the film's own shards+debris", sig["shards"] + sig["debris"]),
                    ("the ORACLE at the same energy", oracle),
                    ("the ORACLE, +6 dB", oracle * 2.0),
                    ("the ORACLE, +12 dB", oracle * 4.0)):
        print("%-36s %s" % (tag, "".join(
            "%10.4f" % ami(no_eng + rest["engine"] * g + gl, sr) for g in cols)))
    print()
    print("   the ORACLE alone reads %.4f; the film's glass alone reads %.4f."
          % (ami(oracle, sr), ami(sig["shards"] + sig["debris"], sr)))
    print()

    # -- 3. the population -------------------------------------------------
    print("3. THE FRAGMENT POPULATION: THE AUDIO'S AGAINST THE DELIVERED "
          "FRAMES'")
    meta = json.load(open(os.path.join(ROOT, "sim", "out",
                                       "breach_sim.json")))["shard_meta"]
    wall = json.load(open(os.path.join(ROOT, "sim", "out",
                                       "fracture_wall.json")))
    gone = {b["uid"] for b in wall["breach_state"] if b["beat3"] == "destroyed"}
    pic = [m for m in meta if m["bay"] in gone]
    Lp = np.array([np.sqrt(m["area"]) for m in pic])
    mp = np.array([m["mass"] for m in pic])
    print("   the picture: bays %s leave; %d shards, %.0f kg, "
          "sqrt(area) %.3f-%.3f m" % (sorted(gone), len(pic), mp.sum(),
                                      Lp.min(), Lp.max()))
    print("   glass makeup, from the section drawing: %s"
          % wall["section"]["glass_makeup"])

    from audio import layers                                     # noqa: PLC0415
    spec = json.load(open(os.path.join(ROOT, "docs", "circuit_spec.json")))
    rep = json.load(open(os.path.join(
        ROOT, "audio", "out", "r2_4147", "master_R2-4147.json")))
    ev, summ = layers.shard_ballistics(spec, rep["breach_sim"]["contact_speed_ms"])
    La = layers._shard_sizes(ev, max(e[2] for e in ev) + 1)
    print("   the audio:   %d shards, %.0f kg, sqrt(area) %.3f-%.3f m"
          % (len(La), (layers.GLASS_RHO * layers.GLASS_H * La ** 2).sum(),
             La.min(), La.max()))
    print()
    print("%14s %14s %14s" % ("equivalent side", "picture", "audio"))
    for lo, hi in ((0, .02), (.02, .05), (.05, .1), (.1, .2), (.2, .4), (.4, 9)):
        print("%6.3f-%6.3f m %14d %14d"
              % (lo, hi, ((Lp >= lo) & (Lp < hi)).sum(),
                 ((La >= lo) & (La < hi)).sum()))
    print()
    print("   median piece: picture %.3f m, audio %.3f m."
          % (np.median(Lp), np.median(La)))


if __name__ == "__main__":
    main()
