#!/usr/bin/env python3
"""EVERY NUMBER IN THE R2-2221 HARMONIC GATE, REPRODUCED FROM THE WAVS ON DISK.

    .venv/bin/python tools/audio_hnr_evidence.py

WHY THIS EXISTS. `audio/verify.py` now carries a threshold and a permitted
fraction for each of six beats and two limbs -- twenty-four numbers -- plus two
applicability limits. Numbers that large in count rot silently, and this project
has already shipped three staging notes whose figures no longer reproduce. This
regenerates all of them from the four masters on disk, prints the rule that
produced each, and exits non-zero if any constant in `verify.py` disagrees with
what the audio now says.

WHAT IT MEASURES, IN THE ORDER THE ARGUMENT IS MADE

  1. THE NOISE FLOOR. What this metric reads on things with no line spectrum, per
     beat, so "1 dB above a noise generator" is a measurement.
  2. WHY THE FRACTION AND NOT THE PERCENTILE. Block-bootstrap standard errors of
     both statistics, per beat, against the separation each one buys.
  3. THE LIMITS, by the one stated rule, with both endpoints and both margins.
  4. APPLICABILITY, per beat per limb: power against a hair dryer, and the share
     of the beat's energy in the band being scored.
  5. INVARIANCE. The same beat scored on four masters spanning two complete
     engine rebuilds. A beat whose number does not move is a beat this metric is
     not measuring the engine in, and that is the whole argument about the breach
     and the ending.
  6. THE VERDICT TABLE. Every master and every constructed control against the
     limits, so "the film passes and the artefacts the client rejected fail" is a
     table rather than a claim.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal as _sig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from audio.verify import (  # noqa: E402
    BEAT_HNR_LIMITS, HNR_DECLARED_UNMEASURABLE, HNR_ENGINE_BEATS,
    HNR_HF_SHARE_MIN, HNR_POWER_MIN, _hairdryer_like, hnr_profile,
)

AB = os.path.join(ROOT, "audio", "out", "ab")
MASTER = os.path.join(ROOT, "audio", "out", "master.wav")
# The two artefacts the client rejected as a hair blower. R2-1400 is the one they
# heard; the 2 Aug shipped master is the same defect one build earlier, kept
# because two independent instances of a failure make a better adversary than one.
HAIRDRYER_MASTERS = [
    ("REJECTED R2-1400 (hair blower)",
     os.path.join(AB, "master_R2-1400_REJECTED_hairblower.wav")),
    ("SHIPPED 2 Aug (same defect, one build earlier)",
     os.path.join(AB, "master_SHIPPED_aug2.wav")),
]
# NOT an adversary for this gate, and that is the point: the client called this
# one "someone banging on tubes", which is a DECAY defect. It is extremely tonal
# and scores well here. `waveguide_gate` is what catches it.
OTHER_MASTERS = [
    ("REJECTED R2-2001 (tubular bells)",
     os.path.join(AB, "master_R2-2001_REJECTED_tubes.wav")),
]

BLK = 8          # 200 ms of hops: past the 43 ms window's own overlap
BOOT = 3000
SEED = 2221


def load_mono(path):
    x, sr = sf.read(path, dtype="float64")
    return (x.mean(axis=1) if x.ndim > 1 else x), sr


def beat_profiles(x, sr, sheet):
    """Per-beat window profiles, plus the beat's share of energy above 2.6 kHz."""
    t, h, hf = hnr_profile(x, sr)
    xh = _sig.sosfilt(_sig.butter(6, 2600.0, btype="highpass", fs=sr,
                                  output="sos"), x)
    out = {}
    for b in sheet["beats"]:
        m = (t >= b["start_s"]) & (t < b["start_s"] + b["duration_s"])
        if not m.any():
            continue
        s0 = int(round(b["start_s"] * sr))
        s1 = int(round((b["start_s"] + b["duration_s"]) * sr))
        out[b["name"]] = {
            "bb": h[m], "hf": hf[m],
            "share": float(np.mean(xh[s0:s1] ** 2)
                           / max(np.mean(x[s0:s1] ** 2), 1e-30)),
            "band_dbfs": float(10.0 * np.log10(max(np.mean(xh[s0:s1] ** 2), 1e-30))),
            "rms_dbfs": float(10.0 * np.log10(max(np.mean(x[s0:s1] ** 2), 1e-30))),
        }
    return out


def _blocks(m, rng):
    nb = int(np.ceil(m / BLK))
    st = rng.integers(0, max(m - BLK, 1), size=(BOOT, nb))
    return (st[:, :, None] + np.arange(BLK)[None, None, :]).reshape(BOOT, -1)[:, :m]


def frac_se(v, thr, rng):
    """Fraction below threshold, and its block-bootstrap standard error."""
    idx = _blocks(v.shape[0], rng)
    return float((v < thr).mean()), float(np.std((v[idx] < thr).mean(axis=1)))


def pct_se(v, q, rng):
    """The q-th percentile of the value, and ITS block-bootstrap standard error."""
    idx = _blocks(v.shape[0], rng)
    return float(np.percentile(v, q)), float(np.std(np.percentile(v[idx], q, axis=1)))


def rule_limit(film, adversary):
    """The one rule: midpoint, rounded to the nearest 0.05."""
    return round((film + adversary) / 2.0 / 0.05) * 0.05


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--wav", default=MASTER)
    ap.add_argument("--json", default=os.path.join(ROOT, "audio", "out",
                                                   "hnr_evidence.json"))
    a = ap.parse_args()

    sheet = json.load(open(os.path.join(ROOT, "docs", "beat_sheet.json")))
    beats = [b["name"] for b in sheet["beats"]]
    rng = np.random.default_rng(SEED)

    x, sr = load_mono(a.wav)
    cases = {"THE FILM  %s" % os.path.basename(a.wav): beat_profiles(x, sr, sheet)}

    # the adversary, and the two other controls, built exactly as the gate builds
    # them so this file cannot drift from `verify.py`'s own construction
    hd = _hairdryer_like(x, sr)
    cases["ADVERSARY octave-matched hair dryer"] = beat_profiles(hd, sr, sheet)
    r2 = np.random.default_rng(1402)
    sos_hi = _sig.butter(4, 2600.0, btype="highpass", fs=sr, output="sos")
    sos_lo = _sig.butter(4, 2600.0, btype="lowpass", fs=sr, output="sos")
    hib = _sig.sosfilt(sos_hi, x)
    nz2 = _sig.sosfilt(sos_hi, r2.standard_normal(x.shape[0]))
    nz2 *= np.sqrt(np.mean(hib ** 2)) / max(np.sqrt(np.mean(nz2 ** 2)), 1e-12)
    cases["CONTROL top four octaves -> noise"] = beat_profiles(
        _sig.sosfilt(sos_lo, x) + nz2, sr, sheet)
    nz3 = r2.standard_normal(x.shape[0])
    cases["CONTROL flat white noise"] = beat_profiles(nz3, sr, sheet)
    for lab, p in HAIRDRYER_MASTERS + OTHER_MASTERS:
        if os.path.exists(p):
            y, ysr = load_mono(p)
            cases[lab] = beat_profiles(y, ysr, sheet)
        else:
            print("!! MISSING, skipped: %s" % p)

    film = next(iter(cases))
    hdk = "ADVERSARY octave-matched hair dryer"
    rep = {"wav": a.wav, "beats": {}}

    # ---------------------------------------------------------------- (1) ----
    print("=" * 92)
    print("1. THE NOISE FLOOR.  What this metric reads with no line spectrum at "
          "all, median dB.")
    print("   The -1.0 dB threshold for the beats the engine does not drive is "
          "one dB above this.")
    print("   %-12s %14s %14s %14s %14s" % ("beat", "hairdryer HF", "flat-noise HF",
                                            "hairdryer BB", "flat-noise BB"))
    for b in beats:
        print("   %-12s %14.2f %14.2f %14.2f %14.2f"
              % (b, np.median(cases[hdk][b]["hf"]),
                 np.median(cases["CONTROL flat white noise"][b]["hf"]),
                 np.median(cases[hdk][b]["bb"]),
                 np.median(cases["CONTROL flat white noise"][b]["bb"])))

    # ---------------------------------------------------------------- (2) ----
    print("\n" + "=" * 92)
    print("2. WHY THE FRACTION BELOW A THRESHOLD AND NOT A PERCENTILE OF THE "
          "VALUE.")
    print("   Both are the same statement. Only one is estimable on a 3-second "
          "beat.")
    print("   %-12s %6s | %-26s | %-26s"
          % ("beat", "wins", "p20 of the value (dB)", "fraction below 3.0 dB"))
    print("   %-12s %6s | %11s %13s | %11s %13s"
          % ("", "", "film+-SE", "hairdryer+-SE", "film+-SE", "hairdryer+-SE"))
    for b in beats:
        pf, pfe = pct_se(cases[film][b]["hf"], 20, rng)
        ph, phe = pct_se(cases[hdk][b]["hf"], 20, rng)
        ff, ffe = frac_se(cases[film][b]["hf"], 3.0, rng)
        fh, fhe = frac_se(cases[hdk][b]["hf"], 3.0, rng)
        print("   %-12s %6d | %6.2f+-%.2f %6.2f+-%.2f | %6.3f+-%.3f %6.3f+-%.3f"
              % (b, cases[film][b]["hf"].shape[0], pf, pfe, ph, phe,
                 ff, ffe, fh, fhe))
    print("   The value-percentile columns are in dB and the fraction columns "
          "are dimensionless;")
    print("   compare each against its own separation, not against each other.")

    # ------------------------------------------------------------ (3)+(4) ----
    print("\n" + "=" * 92)
    print("3+4. THE LIMITS AND THE APPLICABILITY, by the rule stated in "
          "verify.py.")
    print("   HF limb  adversary = tightest of {hair dryer, the rejected "
          "masters}   (THE TEST)")
    print("   BB limb  adversary = the hair dryer alone                       "
          "        (A FLOOR)")
    print("   %-12s %4s %6s %8s %9s | %6s %6s | %7s %8s %7s  %s"
          % ("beat", "limb", "thr", "film", "adversary", "LIMIT", "in use",
             "power", "share%", "margin", "applicable"))
    bad = []
    for b in beats:
        eng = b in HNR_ENGINE_BEATS
        rep["beats"][b] = {"share": cases[film][b]["share"],
                           "band_dbfs": cases[film][b]["band_dbfs"],
                           "rms_dbfs": cases[film][b]["rms_dbfs"], "limbs": {}}
        for limb in ("hf", "bb"):
            thr, in_use = BEAT_HNR_LIMITS[b][limb]
            ff, ffe = frac_se(cases[film][b][limb], thr, rng)
            fh, _ = frac_se(cases[hdk][b][limb], thr, rng)
            pool = [fh]
            if eng and limb == "hf":
                pool += [frac_se(cases[k][b][limb], thr, rng)[0]
                         for k, _p in HAIRDRYER_MASTERS if k in cases]
            adv = min(pool)
            lim = rule_limit(ff, adv)
            power = fh - ff
            share = cases[film][b]["share"]
            app = power >= HNR_POWER_MIN and (limb == "bb"
                                              or share >= HNR_HF_SHARE_MIN)
            why = ("YES" if app else
                   ("no: power %+.3f < %.2f" % (power, HNR_POWER_MIN)
                    if power < HNR_POWER_MIN else
                    "no: share %.4f%% < %.2f%%" % (100 * share,
                                                  100 * HNR_HF_SHARE_MIN)))
            rep["beats"][b]["limbs"][limb] = {
                "threshold_db": thr, "fraction_below": ff, "se": ffe,
                "adversary_fraction": adv, "limit_by_rule": lim,
                "limit_in_verify_py": in_use, "power": power,
                "APPLICABLE": app, "margin_sigma": (in_use - ff) / max(ffe, 1e-9)}
            print("   %-12s %4s %6.1f %8.3f %9.3f | %6.2f %6.2f | %+7.3f %8.4f "
                  "%6.1fs  %s"
                  % (b, limb, thr, ff, adv, lim, in_use, power, 100 * share,
                     (in_use - ff) / max(ffe, 1e-9), why))
            if app and abs(lim - in_use) > 1e-9:
                bad.append("%s.%s: the rule now gives %.2f, verify.py carries "
                           "%.2f" % (b, limb, lim, in_use))
            if app and ff > in_use:
                bad.append("%s.%s: the film reads %.3f against a limit of %.2f"
                           % (b, limb, ff, in_use))

    uncovered = [b for b in beats
                 if not any(rep["beats"][b]["limbs"][k]["APPLICABLE"]
                            for k in ("hf", "bb"))]
    print("\n   gated: %s" % ", ".join(b for b in beats if b not in uncovered))
    print("   unmeasurable: %s   declared: %s"
          % (", ".join(uncovered) or "(none)",
             ", ".join(HNR_DECLARED_UNMEASURABLE)))
    for b in uncovered:
        if b not in HNR_DECLARED_UNMEASURABLE:
            bad.append("%s is unmeasurable on both limbs and is NOT declared" % b)
    for b in HNR_DECLARED_UNMEASURABLE:
        if b not in uncovered:
            bad.append("%s is declared unmeasurable but is now measurable -- "
                       "delete the declaration and let the gate score it" % b)

    # ---------------------------------------------------------------- (5) ----
    print("\n" + "=" * 92)
    print("5. INVARIANCE ACROSS TWO COMPLETE ENGINE REBUILDS, median dB above "
          "2.6 kHz.")
    print("   A beat whose number does not move when the engine is rebuilt is a "
          "beat this")
    print("   metric is not measuring the engine in. THIS IS THE WHOLE ARGUMENT "
          "ABOUT THE")
    print("   BREACH AND THE ENDING, and it is the column on the right.")
    order = [k for k in ["SHIPPED 2 Aug (same defect, one build earlier)",
                         "REJECTED R2-1400 (hair blower)",
                         "REJECTED R2-2001 (tubular bells)", film] if k in cases]
    print("   %-12s" % "beat" + "".join("%20s" % k[:19] for k in order) + "   spread")
    for b in beats:
        v = [float(np.median(cases[k][b]["hf"])) for k in order]
        rep["beats"][b]["invariance_spread_db"] = max(v) - min(v)
        print("   %-12s" % b + "".join("%20.2f" % z for z in v)
              + "  %8.2f" % (max(v) - min(v)))

    # ---------------------------------------------------------------- (6) ----
    print("\n" + "=" * 92)
    print("6. THE VERDICT TABLE. Applicability is the FILM's, as in the gate.")
    for k in cases:
        f = []
        for b in beats:
            for limb in ("hf", "bb"):
                if not rep["beats"][b]["limbs"][limb]["APPLICABLE"]:
                    continue
                thr, lim = BEAT_HNR_LIMITS[b][limb]
                fr = float((cases[k][b][limb] < thr).mean())
                if fr > lim:
                    f.append("%s.%s %.2f>%.2f" % (b.split("_")[1][:5], limb,
                                                  fr, lim))
        print("   %-46s %s" % (k[:46], "PASS" if not f else "FAIL  " + ", ".join(f)))
        rep.setdefault("verdicts", {})[k] = {"PASS": not f, "failures": f}
    for lab, _p in HAIRDRYER_MASTERS:
        if lab in cases and rep["verdicts"][lab]["PASS"]:
            bad.append("%s PASSES -- the adversary this gate exists to catch is "
                       "no longer caught" % lab)
    if rep["verdicts"][film]["PASS"] is False:
        bad.append("the film itself FAILS")

    with open(a.json, "w") as fh:
        json.dump(rep, fh, indent=1, default=float)
    print("\n>> wrote %s" % a.json)
    for m in bad:
        print("!! %s" % m)
    print(">> STAGE RESULT:", "HNR_EVIDENCE_OK" if not bad else "HNR_EVIDENCE_STALE")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
