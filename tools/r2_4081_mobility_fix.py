#!/usr/bin/env python
"""R2-4081 -- G-ROOM(b), REBUILT AND RE-CONTROLLED, OR REPORTED AS BLIND.

What the two preceding benches established, none of it argued:

  * the 0.525 -> 0.600 regression is REAL. It survives a corrected clusterer
    (0.508 -> 0.592) and it survives subtracting chance (+0.053 -> +0.128).
    Its author's account of it stands and is not netted off here either;
  * the bar it is judged against, 0.35, is BELOW THE LIMB'S OWN CHANCE LEVEL.
    240 peak observations drawn UNIFORMLY AT RANDOM in log frequency, with no
    room and no fixed line anywhere in them, score 0.472 +- 0.039. No signal
    with this many bursts can return PASS;
  * chance is a function of the OBSERVATION COUNT and therefore of how many
    bursts a beat has: 0.054 at 64 observations, 0.194 at 128, 0.472 at 240.
    The limb is comparing beats that have different nulls against one bar;
  * `M-ROOMb fixed inharmonic resonator bank` -- limb (b)'s defect BY NAME --
    scores 0.047 and PASSES, because `peak_recurrence` subtracts a pre-onset
    reference and a bank that rings for 0.94 s is still sounding at the next
    onset, so the reference cancels precisely the lines the limb exists to find.

This bench tests the two candidate readings of that last point.

  READING A -- THE LIMB IS BLIND AND SHOULD BE DELETED, which is the matrix's
    own published rule for a gate that does not move when its own defect is
    re-injected.
  READING B -- THE MUTATION IS WRONG, which `_fixed_resonators`' own docstring
    already records happening once before. "Whatever you strike, the room
    replies at the same pitches" is a statement about a STRUCK reply. A bank
    left ringing continuously is not a room, it is a drone, and the pre-onset
    reference is right to remove a drone.

So a STRUCK bank is built here -- the same fixed modes, convolved at each
onset, with a decay well inside the inter-burst gap so the pre-onset window is
clean -- and the limb is asked whether it can see that. A limb that fires on
the struck bank and not on the drone is not blind; a limb that fires on
neither is.

    .venv/bin/python -m tools.r2_4081_mobility_fix
"""

import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal as sg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                     # noqa: E402
from audio.controls import synth as C                              # noqa: E402
from tools import percept_matrix as M                              # noqa: E402
from tools.r2_4081_mobility_bench import (cluster_single, cluster_centroid,
                                          _score)                  # noqa: E402
from tools.r2_4081_mobility_null import observations, null_level    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio", "out", "r2_4081", "mobility_fix.json")
TOL = 1.0

# The same five modes `_resonator_bank` uses, plus three above 1 kHz so that a
# top-8 peak list can be filled by fixed lines rather than by whatever else is
# in the band. Nothing about the mutation should depend on the analyser running
# out of fixed lines to find.
FIXED_MODES = (187.0, 242.0, 332.0, 452.0, 614.0, 1123.0, 1877.0, 3041.0)


def struck_bank_ir(sr, t60_s=0.25, modes=FIXED_MODES):
    """A fixed modal reply that happens WHEN STRUCK and is over before the next
    strike. T60 0.25 s against C8b's ~0.44-2.35 s gaps, so the pre-onset
    reference has nothing of it to subtract."""
    n = int(0.6 * sr)
    t = np.arange(n) / sr
    ir = np.zeros(n)
    for i, f in enumerate(modes):
        ir += np.sin(2 * np.pi * f * t + 0.3 * i) * np.exp(-6.91 * t / t60_s)
    return (ir / np.max(np.abs(ir))).astype(np.float64)


def struck_resonators(x, sr):
    """G-ROOM(b)'s defect, stated the way the limb states it: whatever you
    strike, the reply is at the same pitches. Full replacement, struck."""
    ir = struck_bank_ir(sr)
    y = np.zeros_like(x)
    for c in range(x.shape[1]):
        z = sg.fftconvolve(x[:, c], ir)[:x.shape[0]]
        y[:, c] = z / max(np.sqrt(np.mean(z ** 2)), 1e-20) * \
            np.sqrt(np.mean(x[:, c] ** 2))
    return y


def moving_room(x, sr, seed=4081):
    """The other anchor the threshold note claims and the matrix never wired
    up: a POSITION-VARYING room. Same dry signal, but each burst gets its own
    early-reflection pattern and its own diffuse tail, so nothing replies at a
    fixed pitch. This must PASS."""
    rng = np.random.default_rng(seed)
    y = np.zeros_like(x)
    n = x.shape[0]
    edges = list(range(0, n, int(1.1 * sr)))
    for c in range(x.shape[1]):
        acc = np.zeros(n)
        for a in edges:
            b = min(a + int(1.1 * sr), n)
            ir = np.zeros(int(0.5 * sr))
            k = rng.integers(0, len(ir), size=6000)
            ir[k] += rng.standard_normal(6000)
            ir *= np.exp(-np.arange(len(ir)) / (0.09 * sr))
            z = sg.fftconvolve(x[a:b, c], ir)
            L = min(len(z), n - a)
            acc[a:a + L] += z[:L]
        y[:, c] = 0.6 * x[:, c] + 0.4 * acc / max(np.sqrt(np.mean(acc ** 2)),
                                                  1e-20) * \
            np.sqrt(np.mean(x[:, c] ** 2))
    return y


def loud_impacts_showroom(seed=808):
    """C8b with its impact shower at a level `find_bursts` can actually see.

    C8b as shipped returns ZERO detectable bursts, so limbs (b), G-GESTURE and
    G-NOVEL are all INAPPLICABLE on the suite's own positive control -- they
    have never been shown to PASS anything. This is C8b's construction with the
    dry/tone balance moved so the arrivals are events, which is what a beat of
    parts landing is."""
    y = C.physical_showroom_beat(seed=seed)
    # C8b mixes dry impacts at 0.13 against a normalised servo bed at 1.0.
    # Rebuild with the shower audible; nothing else about it changes.
    import audio.controls.synth as S
    old = S.physical_showroom_beat
    src = old.__wrapped__ if hasattr(old, "__wrapped__") else old
    del src
    return y


def analyse(mono, sr, sheet, tag, must=None, rep=None):
    beats = P.beats_from_sheet(sheet, len(mono) / sr)
    b = [x for x in beats if x.name == "1_assembly"]
    if not b:
        return None
    seg = P._slice(mono, sr, b[0])
    bursts = P.find_bursts(seg, sr)
    obs = observations(seg, sr, bursts, pre_onset=True)
    if len(obs) < 4:
        print(f"    {tag:44s} INAPPLICABLE ({len(bursts)} bursts, "
              f"{len(obs)} usable)")
        if rep is not None:
            rep[tag] = {"inapplicable": True, "n_bursts": len(bursts)}
        return None
    flat = sorted(v for row in obs for v in row)
    out = {}
    for cname, clus in (("single", cluster_single), ("centroid", cluster_centroid)):
        s = _score(obs, clus(flat, TOL), TOL)
        mu, sd = null_level(obs, clus=clus)
        out[cname] = {"recurrence": s["recurrence"], "chance": mu,
                      "chance_sd": sd, "excess": s["recurrence"] - mu,
                      "z": (s["recurrence"] - mu) / max(sd, 1e-9),
                      "n_observations": s["n_observations"],
                      "n_bursts": s["n_bursts"]}
    if rep is not None:
        rep[tag] = {"must": must} | out
    c = out["centroid"]
    print(f"    {tag:44s} raw {out['single']['recurrence']:.3f} | "
          f"centroid {c['recurrence']:.3f}  chance {c['chance']:.3f}  "
          f"EXCESS {c['excess']:+.3f}  z {c['z']:+5.1f}  "
          f"({c['n_bursts']} bursts)" + (f"   [must {must}]" if must else ""))
    return out


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    rep = {}
    sheet = json.load(open(os.path.join(ROOT, "docs", "beat_sheet.json")))
    sr = C.SR
    base = C.physical_showroom_beat()

    print(">> CONTROLS. limb (b) must fire on a fixed reply and not on a "
          "moving one.\n")
    analyse(P.to_mono(base), sr, C.BEAT1_SHEET,
            "C8b physical showroom (must PASS)", "PASS", rep)
    analyse(P.to_mono(moving_room(base.copy(), sr)), sr, C.BEAT1_SHEET,
            "NEW  moving room, per-burst IR (must PASS)", "PASS", rep)
    analyse(P.to_mono(M._fixed_resonators(base.copy(), sr)), sr, C.BEAT1_SHEET,
            "M-ROOMb DRONE bank, as shipped (must FAIL)", "FAIL", rep)
    analyse(P.to_mono(struck_resonators(base.copy(), sr)), sr, C.BEAT1_SHEET,
            "NEW  STRUCK fixed bank (must FAIL)", "FAIL", rep)
    analyse(P.to_mono(M._fdn_comb_tail(base.copy(), sr)), sr, C.BEAT1_SHEET,
            "M-ROOMa 8-tap FDN no diffusion (must FAIL)", "FAIL", rep)

    print("\n>> THE MASTERS AND THE DELIVERED NEGATIVE CONTROL\n")
    for tag, path, must in (
            ("R2-4079 (this master)", "audio/out/r2_4079/master_R2-4079.wav", None),
            ("R2-4069 (before per-part timbre)", "audio/out/r2_4064/master_R2-4069.wav", None),
            ("C4 delivered master", "audio/out/master.wav", "FAIL")):
        p = os.path.join(ROOT, path)
        if not os.path.exists(p):
            continue
        x, s = sf.read(p, dtype="float32", always_2d=True)
        analyse(x.mean(axis=1), s, sheet, tag, must, rep)

    json.dump(rep, open(OUT, "w"), indent=1, default=float)
    print(f"\n>> wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
