#!/usr/bin/env python
"""R2-4081 -- G-ROOM(b): WHAT DOES THIS LIMB READ ON A SIGNAL WITH NO ROOM IN IT?

The mobility bench disconfirmed the obvious explanation: correcting the
single-linkage chaining moves R2-4079 from 0.600 to 0.592 and R2-4069 from
0.525 to 0.508, so the 0.075 regression is REAL and survives a correct
clusterer. Its author's account of it stands.

It also turned up something larger, so this bench asks the two questions that
follow, both of which have a known answer by construction:

  (1) WHAT IS CHANCE? Limb (a) computes an explicit `chance_level` and gates on
      the EXCESS over it, because a comb score means nothing without one. Limb
      (b) gates a raw fraction. With N observations pooled over 200-6000 Hz at
      1 % tolerance there are only ln(30)/ln(1.01) ~ 342 resolvable slots, so
      collisions are the null expectation, not evidence of a fixed room. The
      null is measured here by re-drawing the SAME NUMBER of peaks per burst
      uniformly in log frequency and running the identical clusterer.

  (2) CAN THIS LIMB SEE ITS OWN DEFECT? `M-ROOMb fixed inharmonic resonator
      bank` is limb (b)'s defect by name and reads 0.047 -- it PASSES. The
      suspect is `peak_recurrence`'s pre-onset reference: a bank of fixed
      resonators is ALREADY SOUNDING before every onset, so subtracting the
      pre-onset spectrum removes precisely the lines the limb exists to find.
      Measured here with the reference on and off.

    .venv/bin/python -m tools.r2_4081_mobility_null
"""

import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                     # noqa: E402
from audio.controls import synth as C                              # noqa: E402
from tools import percept_matrix as M                              # noqa: E402
from tools.r2_4081_mobility_bench import (cluster_single, cluster_centroid,
                                          _score)                  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio", "out", "r2_4081", "mobility_null.json")
F_LO, F_HI, TOL = 200.0, 6000.0, 1.0


def observations(mono, sr, bursts, top_k=8, pre_onset=True):
    obs = []
    for s, n in bursts:
        seg = mono[s:s + n]
        if len(seg) < 2048:
            continue
        win = min(8192, 1 << int(np.log2(len(seg))))
        Pw, f = P._stft_power(seg, sr, win=win)
        if Pw.shape[0] == 0:
            continue
        S = Pw.mean(axis=0)
        if pre_onset:
            pre = P._pre_onset(mono, sr, s)
            if len(pre) >= win:
                Pp, _ = P._stft_power(pre, sr, win=win)
                if Pp.shape[0]:
                    S = np.maximum(S - Pp.mean(axis=0), S * 1e-6)
        m = (f >= F_LO) & (f <= F_HI)
        Sb, fb = S[m], f[m]
        k = max(int(len(Sb) / 60) | 1, 5)
        ldb = 10 * np.log10(np.maximum(Sb, 1e-20))
        rel = ldb - P._sig.savgol_filter(ldb, k, 2)
        pk, _ = P._sig.find_peaks(rel, distance=max(int(len(Sb) / 200), 2))
        if len(pk) == 0:
            continue
        pk = pk[np.argsort(-rel[pk])][:top_k]
        obs.append([float(fb[p]) for p in pk])
    return obs


def rec(obs, clus=cluster_single):
    flat = sorted(x for row in obs for x in row)
    return _score(obs, clus(flat, TOL), TOL)["recurrence"]


def null_level(obs, n_trials=40, seed=4081, clus=cluster_single):
    """The same peak COUNTS, drawn uniformly in log frequency. Anything a
    position-independent random spectrum scores is not evidence of a room."""
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_trials):
        fake = [list(np.exp(rng.uniform(np.log(F_LO), np.log(F_HI), len(row))))
                for row in obs]
        vals.append(rec(fake, clus))
    return float(np.mean(vals)), float(np.std(vals))


def load_beat1(path_or_arr, sr=None, sheet=None):
    if isinstance(path_or_arr, str):
        x, sr = sf.read(path_or_arr, dtype="float32", always_2d=True)
        mono = x.mean(axis=1)
        sheet = json.load(open(os.path.join(ROOT, "docs", "beat_sheet.json")))
    else:
        mono = P.to_mono(path_or_arr)
    beats = P.beats_from_sheet(sheet, len(mono) / sr)
    b = [x for x in beats if x.name == "1_assembly"][0]
    seg = P._slice(mono, sr, b)
    return seg, sr


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    rep = {}
    print(">> (1) THE NULL. bar 0.35, single-linkage (shipped) and centroid.\n")
    print("    signal                          measured   CHANCE (uniform "
          "log-f draw, same counts)   excess")
    items = [("R2-4079 (this master)",
              os.path.join(ROOT, "audio/out/r2_4079/master_R2-4079.wav")),
             ("R2-4069 (before per-part timbre)",
              os.path.join(ROOT, "audio/out/r2_4064/master_R2-4069.wav")),
             ("C4 delivered master",
              os.path.join(ROOT, "audio/out/master.wav"))]
    for tag, p in items:
        if not os.path.exists(p):
            continue
        seg, sr = load_beat1(p)
        obs = observations(seg, sr, P.find_bursts(seg, sr))
        for cname, clus in (("single", cluster_single), ("centroid", cluster_centroid)):
            r = rec(obs, clus)
            mu, sd = null_level(obs, clus=clus)
            rep.setdefault(tag, {})[cname] = {"recurrence": r, "chance": mu,
                                              "chance_sd": sd, "excess": r - mu}
            print(f"    {tag:31s} {cname:8s} {r:.3f}     {mu:.3f} +- {sd:.3f}"
                  f"          {r - mu:+.3f}")

    print("\n>> (2) CAN LIMB (b) SEE ITS OWN DEFECT? pre-onset reference on/off\n")
    base = C.physical_showroom_beat()
    sr = C.SR
    cases = [("C8b physical showroom  (must PASS)", base),
             ("M-ROOMb fixed resonator bank (must FAIL)",
              M._fixed_resonators(base.copy(), sr)),
             ("M-ROOMa 8-tap FDN no diffusion (must FAIL)",
              M._fdn_comb_tail(base.copy(), sr))]
    print("    signal                                    pre-onset ON      "
          "pre-onset OFF     chance(OFF)")
    for tag, y in cases:
        seg, _ = load_beat1(y, sr, C.BEAT1_SHEET)
        bursts = P.find_bursts(seg, sr)
        row = {}
        for pon in (True, False):
            obs = observations(seg, sr, bursts, pre_onset=pon)
            if len(obs) < 4:
                row["ON" if pon else "OFF"] = None
                continue
            row["ON" if pon else "OFF"] = {"recurrence": rec(obs),
                                           "n_bursts": len(obs)}
            if not pon:
                mu, sd = null_level(obs)
                row["chance_OFF"] = mu
        rep[tag] = row
        f = lambda k: ("n/a  " if row.get(k) is None
                       else f"{row[k]['recurrence']:.3f} ({row[k]['n_bursts']}b)")
        print(f"    {tag:42s} {f('ON'):15s} {f('OFF'):15s} "
              f"{row.get('chance_OFF', float('nan')):.3f}")

    json.dump(rep, open(OUT, "w"), indent=1, default=float)
    print(f"\n>> wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
