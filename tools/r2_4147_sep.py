#!/usr/bin/env python
"""R2-4147 -- WHICH MEASURE ACTUALLY SEPARATES A DENSE MACHINE FROM A SMOOTH BED.

The corpus decides, not an argument. Three candidate quantities are run over
the beat-1 controls and over the film's own voices:

  LDR    `percept.local_dynamic_range` -- G-EVENT's shipped instrument, the
         p95-p5 spread of the 20 ms level. IT MEASURES TROUGH DEPTH, so its
         best score is silence and its worst is anything dense.

  GDR    the same spread asked of the GAP MATERIAL ONLY (the samples left when
         the loud events and their 0.35 s of decay are removed). Answers "is
         what is BETWEEN the events still fluctuating".

  AMI    ARTICULATION MODULATION INDEX -- the RMS of the broadband envelope's
         4-100 Hz band over the envelope's mean. A train of distinct contacts
         at 20-100 Hz puts its energy exactly there; stationary noise and a
         held tone do not, whatever their density. THIS IS THE QUANTITY
         R2-4144's drag-chain sweep was reaching for and measured with the
         wrong tool.

Contract: C9 (the positive) must be on the machine side; C1 (the hair dryer)
and C8b (the drone) must be on the bed side, with a gap wide enough to put a
bar in.

    python -m tools.r2_4147_sep
"""

import argparse
import json
import os
import sys

import numpy as np
from scipy import signal as sg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                    # noqa: E402
from audio.controls import synth as CS                            # noqa: E402
from tools.r2_4081_asm_bench import render_parts, _to_measure_sr   # noqa: E402
from tools.r2_4147_event_diag import gap_dynamic_range            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# THE IMPLEMENTATION LIVES IN `audio/percept.py` -- the gate and the bench must
# be the same estimator or the bench is measuring a different film.
articulation_modulation_index = P.articulation_modulation_index


def _superseded_articulation_modulation_index(mono, sr, f_lo=4.0, f_hi=100.0):
    """RMS OF THE ENVELOPE'S ARTICULATION BAND, OVER THE ENVELOPE'S MEAN.

    THE ONE THING IT MUST NOT BE IS TROUGH DEPTH. A dense machine and an empty
    gap both make `local_dynamic_range` large -- the machine because its
    contacts are loud, the gap because its floor is low -- and that is the
    degeneracy that steered this build into silence. A MODULATION INDEX cannot
    be bought with silence: a passage with no signal has no envelope, so it
    returns nan rather than a perfect score, and a passage with a SMOOTH
    envelope returns a small number no matter how loud it is.

    4-100 Hz is not chosen: 4 Hz is under the slowest gesture rate a hand or an
    actuator produces and 100 Hz is the roughness boundary above which the ear
    stops hearing separate events and starts hearing timbre (Terhardt; the
    fluctuation-strength / roughness split). ABOVE 100 Hz a train IS a tone,
    which is exactly the failure this project has shipped four times.

    Stationary noise is not zero here and must not be: the envelope of a
    band-limited noise fluctuates by its own Rayleigh statistics. The null is
    therefore MEASURED (`--null`) rather than assumed to be zero.
    """
    mono = np.asarray(mono, dtype=np.float64)
    if mono.ndim > 1:
        mono = mono.mean(axis=1)
    # envelope: full-wave rectify, then a linear-phase low-pass at ENV_HZ, so
    # the 4-100 Hz band is inside the envelope's own passband with room to spare
    dec = max(int(sr // (4 * ENV_HZ)), 1)
    sos = sg.butter(4, ENV_HZ, btype="lowpass", fs=sr, output="sos")
    e = sg.sosfiltfilt(sos, np.abs(mono))[::dec]
    fs = sr / dec
    mu = float(np.mean(e))
    if mu <= 1e-12 or len(e) < int(4 * fs):
        return {"ami": float("nan"), "why": "no envelope: nothing is here"}
    # DETREND at 2 Hz so a macro fade or a beat-long swell cannot enter the band
    hp = sg.butter(2, f_lo * 0.5, btype="highpass", fs=fs, output="sos")
    band = sg.sosfiltfilt(sg.butter(4, [f_lo, f_hi], btype="bandpass",
                                    fs=fs, output="sos"),
                          sg.sosfiltfilt(hp, e))
    return {"ami": float(np.sqrt(np.mean(band ** 2)) / mu),
            "ami_db": float(20.0 * np.log10(max(np.sqrt(np.mean(band ** 2)) / mu, 1e-9))),
            "env_mean": mu, "env_fs": fs}


def measure(x, sr, label):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    x, sr = _to_measure_sr(x, sr)
    n = min(len(x), int(33.0 * sr))
    x = x[:n]
    return {"label": label,
            "LDR": P.local_dynamic_range(x, sr)["median_db"],
            "GDR": gap_dynamic_range(x, sr)["median_db"],
            "AMI": articulation_modulation_index(x, sr)["ami"],
            "rms": float(np.sqrt(np.mean(x ** 2)))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(
        ROOT, "audio", "out", "r2_4147", "separation.json"))
    a = ap.parse_args()

    rows = []
    # ---- the corpus -------------------------------------------------------
    for name, side in (("C9_assembly_cell", "POSITIVE -- a machine"),
                       ("C1_octave_matched_noise", "NEGATIVE -- the hair dryer"),
                       ("C8b_tonal_showroom_drone", "NEGATIVE -- the drone"),
                       ("C3_blower_plus_tubes", "NEGATIVE -- blower into tubes")):
        c = CS.build(name)
        rows.append(measure(c["x"], c["sr"], "%-26s %s" % (name, side)))
    # ---- a measured null: white noise, which is the smoothest bed there is -
    rng = np.random.default_rng(4147)
    rows.append(measure(rng.standard_normal(33 * 48000) * 0.05, 48000,
                        "%-26s %s" % ("NULL white noise", "the smooth-bed null")))
    # ---- the film ---------------------------------------------------------
    imp, cell, sr, _ = render_parts()
    rows.append(measure(imp, sr, "%-26s %s" % ("film part impacts alone", "")))
    rows.append(measure(cell, sr, "%-26s %s" % ("film cell alone (0.008)", "")))
    rows.append(measure(imp + cell, sr, "%-26s %s" % ("SHIPPED beat-1 layer", "")))

    print("")
    print("%-56s %9s %9s %9s" % ("signal", "LDR dB", "GDR dB", "AMI"))
    print("-" * 88)
    for r in rows:
        print("%-56s %9.2f %9.2f %9.4f" % (r["label"], r["LDR"], r["GDR"], r["AMI"]))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(rows, open(a.out, "w"), indent=1)
    print("\n->", a.out)


if __name__ == "__main__":
    main()
