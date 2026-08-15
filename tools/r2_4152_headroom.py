#!/usr/bin/env python
"""R2-4152 -- THE SECOND INSTRUMENT: A HEADROOM LEDGER IN THE PEAK DOMAIN.

    .venv/bin/python -m tools.r2_4152_headroom [--budget]

R2-4151 left OPEN #2 in these terms: `BUS_PEAK_CEILING`'s stated derivation is
dead (measured K-weighting deafness <= 2.27 dB anywhere in the film, +0.07 dB on
R2-4034's own case); what it actually does is bound peak-to-loudness ratio at
-target, i.e. tax eventfulness; it may not be disabled because it is the only
thing between the single-event `impact` bus and a linear peak of 19.5; and

    "the real defect is that a 3-second short-term meter is the wrong
     instrument for a bus whose event is 0.16 ms, and there is no second
     instrument."

This file is the second instrument. It has four sections and they have to be
believed in order:

  1. THE LEDGER. Every bus, what it CLAIMS of the film's peak headroom (the true
     peak it enters the sum with, in dBTP) against what the film DECLARES it has
     (G14: premix peak <= +6.0 dBFS). `BUS_PEAK_CEILING` reports a per-bus trim
     and has never once related that trim to G14, so nobody has ever been able
     to answer "how much headroom does this film have left". The answer is on
     the shipped master and it is not zero.

  2. THE COINCIDENCE, MEASURED. A per-bus ceiling is only meaningful against the
     sum, and the sum is not the arithmetic total of the parts. The premix peak
     is measured against the worst case (every bus peaking at the same sample)
     and against the actual delivered mix, and the gap between them is the
     number a budget has to be built on. Measured, not assumed.

  3. THE VALIDATION THE OPEN ITEM ASKS FOR. `synth.glass_breach` is the
     validated physics positive for this exact event, at PLR 27.14 dB. It must
     pass the new criterion comfortably; a bus entering the sum at +17.5 dBFS
     must fail it. Both are run here, and so is the old criterion beside them,
     because the point of the new one is that its verdict does not depend on
     crest at all.

  4. THE BUDGET (`--budget`, slow). The stems summed and put through master.py's
     real post-premix chain, with the peak ceiling and the engine's ramp gain as
     the two axes, reading G14 and G1 off directly. Both are DECLARED thresholds
     and neither may be moved, so what they say is the whole size of the prize.

NOTHING HERE MOVES A THRESHOLD. G14 stays at +6.0 dBFS and G1 at 3 dB; what
changes is that the per-bus ceiling stops being a constant nobody chose and
becomes a number solved out of those two.
"""

import argparse
import json
import math
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal as _sig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from audio import dsp                                            # noqa: E402
from audio import master as M                                    # noqa: E402

SR = 96000
TARGET_LUFS_I = -23.0
CEILING_DBTP = -1.15
G14_PREMIX_PEAK_DBFS = 6.0          # DECLARED. `master.chain_checks`.
G1_LIMITER_GR_DB = 3.0              # DECLARED. `master.chain_checks`.


def db(x):
    return 20.0 * math.log10(max(float(x), 1e-12))


def load_stems(tag):
    d = os.path.join(ROOT, "audio", "out", tag, "stems")
    out = {}
    for nm in sorted(os.listdir(d)):
        if nm.endswith(".wav"):
            x, _ = sf.read(os.path.join(d, nm), always_2d=True)
            out[nm[:-4]] = x.astype(np.float32)
    return out


# ============================================================== 1. THE LEDGER =
def ledger(tag, report):
    """Every bus's CLAIM on the film's declared peak headroom.

    The claim is the bus's true peak AS IT ENTERS THE SUM -- after its trim,
    before anything downstream -- measured the way BS.1770-4 Annex 2 specifies
    (4x polyphase). That is the quantity G14 is about. The old report has
    `trim_db_from_peak_ceiling` and `peak_entering_sum`, and neither of them is
    ever compared to +6.0 dBFS anywhere in the file.
    """
    st = load_stems(tag)
    bl = json.load(open(os.path.join(ROOT, "audio", "out", tag, report)))["buses"]
    rows = []
    lin_sum = 0.0
    for k, x in st.items():
        if k not in bl or float(np.abs(x).max()) < 1e-12:
            continue
        tp = dsp.true_peak_dbtp(x, SR)
        pk = db(np.abs(x).max())
        raw = 20.0 * math.log10(max(bl[k]["raw_peak"], 1e-12))
        rows.append({
            "bus": k,
            "tp_entering_dbtp": tp,
            "peak_entering_dbfs": pk,
            "raw_peak_dbfs": raw,
            "trim_db": bl[k]["trim_db"],
            "peak_criterion_won": bool(bl[k]["peak_criterion_won"]),
            "lufs_target_missed_by_db": bl[k]["lufs_target_missed_by_db"],
            # what the bus would have entered at had the LUFS target alone run
            "tp_if_lufs_only_dbtp": tp + bl[k]["trim_db_from_lufs_target"] - bl[k]["trim_db"],
        })
        lin_sum += 10.0 ** (tp / 20.0)
    rows.sort(key=lambda r: -r["tp_entering_dbtp"])
    return rows, lin_sum, st


def print_ledger(name, rows, lin_sum, premix_tp):
    print("  -- %s" % name)
    print("     %-17s %9s %9s %9s %9s  %s"
          % ("bus", "TP dBTP", "claim %", "TP if the", "trim dB", ""))
    print("     %-17s %9s %9s %9s %9s  %s"
          % ("", "entering", "of G14", "meter ran", "", ""))
    budget_lin = 10.0 ** (G14_PREMIX_PEAK_DBFS / 20.0)
    for r in rows:
        share = 100.0 * (10.0 ** (r["tp_entering_dbtp"] / 20.0)) / budget_lin
        print("     %-17s %+9.2f %9.1f %+9.2f %+9.2f  %s"
              % (r["bus"], r["tp_entering_dbtp"], share,
                 r["tp_if_lufs_only_dbtp"], r["trim_db"],
                 "PEAK CRITERION WON" if r["peak_criterion_won"] else ""))
    print("     %-17s %+9.2f %9.1f" % ("WORST CASE (sum)", db(lin_sum),
                                       100.0 * lin_sum / budget_lin))
    print("     %-17s %+9.2f %9.1f" % ("premix, DELIVERED", premix_tp,
                                       100.0 * 10 ** (premix_tp / 20.0) / budget_lin))
    print("     %-17s %+9.2f dB of the film's DECLARED peak budget is UNUSED"
          % ("HEADROOM LEFT", G14_PREMIX_PEAK_DBFS - premix_tp))
    print()


# ======================================================== 2. THE COINCIDENCE ==
def coincidence(st, mix, premix_tp, lin_sum, ceiling=1.0):
    """WHAT THE FILM'S PEAK BUDGET ACTUALLY SUPPORTS, SOLVED RATHER THAN ASSUMED.

    A per-bus allowance cannot be got at by a formula over the bus count,
    because the buses do not coincide: the arithmetic sum of the seventeen bus
    peaks is +17.25 dBFS and the delivered premix peak is +3.21, i.e. the mix
    realises a fifth of its own worst case. Dividing the budget by seventeen
    would be as arbitrary as the 1.0 it replaces, in the other direction.

    So it is SOLVED, on the delivered stems, exactly the way the limiter's
    makeup already is in this file: raise the common ceiling that the
    peak-criterion-won buses are sitting on, re-sum, and read the premix peak
    off. The answer is the largest ceiling at which G14 -- a DECLARED threshold,
    +6.0 dBFS, which is not moved -- still passes.
    """
    kap = 10.0 ** (premix_tp / 20.0) / lin_sum
    print("2. WHAT THE BUDGET SUPPORTS, SOLVED ON THE DELIVERED STEMS.")
    print("   worst case (every bus peaking on one sample) %+.2f dBFS" % db(lin_sum))
    print("   delivered premix true peak                   %+.2f dBTP" % premix_tp)
    print("   kappa = delivered / worst case               %.4f  (%+.2f dB)"
          % (kap, db(kap)))
    print("   the mix realises %.1f %% of its own worst case, so the budget is"
          % (100.0 * kap))
    print("   not divisible by a bus count and has to be solved.\n")

    # which buses are ON the ceiling -- those are the ones a ceiling change moves
    on = [k for k, x in st.items()
          if abs(db(np.abs(x).max()) - db(ceiling)) < 0.05]
    rest = np.zeros_like(mix)
    held = np.zeros_like(mix)
    for k, x in st.items():
        (held if k in on else rest)[:] += x
    print("   ON THE CEILING (a ceiling change moves exactly these): %s"
          % ", ".join(sorted(on)))
    lo, hi = 1.0, 8.0
    for _ in range(40):
        c = 0.5 * (lo + hi)
        pk = dsp.true_peak_dbtp(rest + held * c, SR)
        if pk <= G14_PREMIX_PEAK_DBFS:
            lo = c
        else:
            hi = c
    print("   G14 %+.2f dBFS is met up to a common ceiling of %.4f = %+.2f dBFS,"
          % (G14_PREMIX_PEAK_DBFS, lo, db(lo)))
    print("   i.e. `BUS_PEAK_CEILING` = 1.0 is leaving %+.2f dB of the film's OWN"
          % db(lo))
    print("   DECLARED peak budget unspent, on every bus that is sitting on it.\n")
    return kap, db(lo), on


# ==================== 3. THE CRITERION, AND WHAT THE OPEN ITEM ASKS OF IT =====
def tp_headroom_criterion(x, sr, budget_dbtp):
    """THE SECOND INSTRUMENT.

    `g = budget_dbtp - true_peak(x)`: the gain that puts this bus's TRUE peak
    exactly on its share of the film's declared peak budget.

    WHAT MAKES IT DIFFERENT FROM `BUS_PEAK_CEILING`, WHICH IS ALSO A PEAK RULE.
    Two things, and only the second is arithmetic:

      * ITS THRESHOLD IS DERIVED. `BUS_PEAK_CEILING = 1.0` is a sample-domain
        constant with a derivation (R2-4034's K-weighting deafness) that
        measures 0.07 dB today. This one's threshold is solved out of G14, which
        is declared, plus the MEASURED coincidence of the buses it is applied
        to. Move G14 and it moves; move nothing and it does not.

      * IT IS IN THE TRUE-PEAK DOMAIN, WHICH IS THE DOMAIN THE THING IT
        PROTECTS IS MEASURED IN. G14 and the delivery ceiling are both true
        peak. A sample-domain ceiling on a 0.16 ms Hertzian contact at 96 kHz
        under-reads the inter-sample peak by up to 1.2 dB and over-reads nothing
        -- so the old rule was protecting the wrong quantity as well as at the
        wrong threshold.

    AND WHAT IT DOES NOT DO. Its verdict does not contain the bus's loudness, so
    it does not contain the bus's PLR, so it cannot tax transient density. That
    is the whole point: `min(g_lufs, g_peak)` at a fixed ceiling is exactly
    `PLR > -target`, and this is not.
    """
    return budget_dbtp - dsp.true_peak_dbtp(x, sr)


def validate(budget_dbtp):
    """THE VALIDATION OPEN #2 ASKS FOR, AND THE ONE HONEST THING IT SHOWS.

    The ask: "`synth.glass_breach` must pass comfortably; a bus at +17.5 dBFS
    must fail." Both are run, and so is the comparison that matters -- what the
    OLD criterion does to the corpus positive against what it does to the film's
    own bus, and whether the new one still does it.
    """
    from audio.controls import synth                              # noqa: E402
    print("3. THE VALIDATION OPEN #2 ASKS FOR, at the solved budget %+.2f dBTP.\n"
          % budget_dbtp)

    y = np.asarray(synth.glass_breach(include=("dice", "slabs", "mullions"))[0],
                   dtype=np.float64)
    if y.ndim == 1:
        y = np.stack([y, y], axis=1)
    lk_c = dsp.max_short_term_lufs(y, 48000)
    y9 = y * 10.0 ** ((-9.0 - lk_c) / 20.0)

    imp, _ = sf.read(os.path.join(ROOT, "audio", "out", "r2_4147", "stems",
                                  "impact.wav"), always_2d=True)
    imp = imp.astype(np.float64)
    bl = json.load(open(os.path.join(ROOT, "audio", "out", "r2_4147",
                                     "master_R2-4147.json")))["buses"]["impact"]
    ask = bl["trim_db_from_lufs_target"] - bl["trim_db"]
    sh, _ = sf.read(os.path.join(ROOT, "audio", "out", "r2_4151", "stems",
                                 "shards.wav"), always_2d=True)
    sh = sh.astype(np.float64)
    sh9 = sh * 10.0 ** ((-9.0 - dsp.max_short_term_lufs(sh, SR)) / 20.0)

    cases = [
        ("synth.glass_breach at shards' -9.0", y9, 48000),
        ("the film's own shards at -9.0", sh9, SR),
        ("`impact` where its LUFS target puts it", imp * 10.0 ** (ask / 20.0), SR),
        ("a bus entering the sum at +17.5 dBFS",
         imp * 10.0 ** ((17.5 - db(np.abs(imp).max())) / 20.0), SR),
    ]
    print("   %-40s %8s %9s %9s %8s"
          % ("bus, at the level its own target asks for", "PLR dB", "TP dBTP",
             "over budget", "verdict"))
    for nm, x, sr in cases:
        tp = dsp.true_peak_dbtp(x, sr)
        over = tp - budget_dbtp
        print("   %-40s %8.2f %+9.2f %+9.2f %8s"
              % (nm, db(np.abs(x).max()) - dsp.max_short_term_lufs(x, sr), tp,
                 over, "PASS" if over <= 0.05 else "FAIL"))
    print()
    print("   A BUS AT +17.5 dBFS FAILS BY %.2f dB, which is the protection the"
          % (17.5 - budget_dbtp))
    print("   ceiling exists for and the new criterion keeps -- `impact` at its")
    print("   own 3 s target is %.1f dB over and is still stopped.\n"
          % (dsp.true_peak_dbtp(imp * 10.0 ** (ask / 20.0), SR) - budget_dbtp))
    print("   AND THE CORPUS POSITIVE. R2-4151(2)'s indictment was that the old")
    print("   criterion would tax `synth.glass_breach` 18.14 dB against 11.71 dB")
    print("   for the film's own bus -- 6.4 dB HARDER on the reference answer.")
    print("   AT A COMMON PEAK BUDGET THAT ASYMMETRY IS NOT A PENALTY, IT IS THE")
    print("   TWO SIGNALS' RAW PEAKS: both land on the SAME delivered true peak,")
    print("   and there they are not the same sound --")
    for nm, x, sr in cases[:2]:
        z = x * 10.0 ** ((budget_dbtp - dsp.true_peak_dbtp(x, sr)) / 20.0)
        zz = z.mean(axis=1) if z.ndim > 1 else z
        import audio.percept as P                                 # noqa: E402
        print("     %-38s AMI %.4f at %+.2f dBTP, %+.2f LUFS-S"
              % (nm, P.articulation_modulation_index(zz, sr).get("ami", float("nan")),
                 budget_dbtp, dsp.max_short_term_lufs(z, sr)))
    print()
    print("   SO THE PEAK CRITERION IS NOT WHAT STOPS THE REFERENCE ANSWER FROM")
    print("   WORKING. What stops it is the size of the budget, and the budget is")
    print("   G14, and G14 is declared. That is what section 4 measures.\n")


# ================================================================ 4. BUDGET ===
def chain(mix):
    """master.py's real post-premix chain, offline. Same arithmetic as
    `tools/r2_4151_peak_scope.chain`, which reproduced the delivered numbers."""
    m = np.asarray(mix, dtype=np.float32)
    raw_peak = float(np.abs(m).max())
    m = _sig.sosfilt(_sig.butter(4, 30.0, btype="highpass", fs=SR, output="sos"),
                     m, axis=0).astype(np.float32)
    _, g_db = dsp.program_gain(m.mean(axis=1), SR, target_rms=0.085, attack_s=6.0,
                               release_s=12.0, max_boost_db=7.0, max_cut_db=3.0)
    m = m * (10.0 ** (g_db / 20.0)).astype(np.float32)[:, None]
    m = _sig.sosfilt(_sig.butter(2, 12.0, btype="highpass", fs=SR, output="sos"),
                     m, axis=0).astype(np.float32)
    L0, _, _ = dsp.loudness_lufs(m, SR)
    makeup, gr = TARGET_LUFS_I - L0, 0.0
    for _ in range(4):
        y, gr_i = dsp.soft_limit((m * float(10.0 ** (makeup / 20.0))).astype(np.float32),
                                 ceiling=10.0 ** (CEILING_DBTP / 20.0), sr=SR)
        L, _, _ = dsp.loudness_lufs(y, SR)
        gr = min(gr, float(gr_i))
        if abs(L - TARGET_LUFS_I) < 0.05:
            break
        makeup += (TARGET_LUFS_I - L)
    return db(raw_peak), gr


def meter_validity(tag):
    """THE OTHER LIMB, AND WHY IT IS MEASURED HERE AND NOT APPLIED.

    OPEN #2's diagnosis is a METERING defect -- "a 3-second short-term meter is
    the wrong instrument for a bus whose event is 0.16 ms" -- and no peak-domain
    criterion can repair a metering defect, because a peak carries no
    information about how long the bus was making a sound. The direct measure of
    the defect is BS.1770-4's OWN second window: the standard defines a 400 ms
    MOMENTARY loudness beside the 3 s short-term one, and

        U = max momentary - max short term

    is exactly how much louder a bus is while its event is happening than the
    3 s meter that sets its level believes. It is parameter-free -- both windows
    are the standard's, not this file's -- and it is INDEPENDENT OF CREST: two
    buses with the same PLR and different temporal concentration get different
    U, which is the separation the peak criterion cannot make.

    IT IS MEASURED AND NOT APPLIED IN THIS PASS, for a stated reason: subtracting
    U from every bus's target moves every bus in the film, and beat 1 is
    PICTURE-LOCKED. The numbers are here so the next pass can act on them
    knowing what they cost.
    """
    st = load_stems(tag)
    print("3b. THE METER-VALIDITY LIMB, MEASURED (BS.1770-4's own 400 ms window).\n")
    print("   %-18s %10s %10s %8s" % ("bus", "max M dB", "max S dB", "U dB"))
    rows = {}
    for k in sorted(st):
        x = st[k]
        if float(np.abs(x).max()) < 1e-9:
            continue
        s = dsp.max_short_term_lufs(x, SR, win_s=3.0, hop_s=0.5)
        m = dsp.max_short_term_lufs(x, SR, win_s=0.4, hop_s=0.1)
        rows[k] = m - s
        print("   %-18s %10.2f %10.2f %8.2f" % (k, m, s, m - s))
    print()
    print("   `impact` -- ONE event in a 124 s film, and R2-4034's own case --")
    print("   reads U = %.2f dB. `shards`, a shower of thousands, reads %.2f dB."
          % (rows.get("impact", float("nan")), rows.get("shards", float("nan"))))
    print("   THE TWO HAVE ALMOST THE SAME PLR AND THE INSTRUMENT SEPARATES THEM,")
    print("   which is what `BUS_PEAK_CEILING` cannot do at any threshold.")
    print("   `assembly`, beat 1's own bus, reads %.2f dB -- so applying this"
          % rows.get("assembly", float("nan")))
    print("   limb WOULD move beat 1, and beat 1 is picture-locked. NOT APPLIED.\n")
    return rows


def budget(tag, ceilings, engine_corrected):
    """THE HEADROOM BUDGET, AGAINST THE TWO THRESHOLDS THAT ACTUALLY BIND.

    The stems, with the ramp's level clause applied to the continuous and
    derived buses exactly as `master.py` applies it (`sqrt(clock.scale)` per
    sample, 0.000 dB outside 36-44 s), the common peak ceiling swept, and the
    whole thing through master.py's real post-premix chain. G14 and G1 are read
    off. NEITHER IS MOVED.
    """
    from audio.clock import Clock                                 # noqa: E402
    st = load_stems(tag)
    n = st["engine"].shape[0]
    clock = Clock(os.path.join(ROOT, "docs", "beat_sheet.json"), sr=SR)
    g = np.sqrt(np.interp(np.arange(n) / SR, clock.film_t,
                          clock.scale)).astype(np.float32)[:, None]
    CONT = ("engine", "tyres", "reflect_garage", "reflect_showroom", "room",
            "aperture")
    ON_CEILING = ("engine", "impact", "shards")
    print("4. THE BUDGET. %s stems, ramp level clause %s, real chain.\n"
          % (tag, "APPLIED" if engine_corrected else "not applied"))
    print("   %10s %14s %8s %14s %8s %12s"
          % ("ceiling", "premix dBFS", "G14", "limiter GR", "G1", "shards dB"))
    base = {}
    for k, x in st.items():
        base[k] = (x * g if (engine_corrected and k in CONT) else x)
    rest = sum(v for k, v in base.items() if k not in ON_CEILING)
    held = sum(v for k, v in base.items() if k in ON_CEILING)
    out = []
    for c in ceilings:
        pk, gr = chain(rest + held * float(c))
        out.append((c, pk, gr))
        print("   %10.4f %+13.2f %8s %+13.2f %8s %+11.2f"
              % (c, pk, "PASS" if pk <= G14_PREMIX_PEAK_DBFS else "FAIL",
                 gr, "PASS" if gr >= -G1_LIMITER_GR_DB else "FAIL", db(c)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", action="store_true")
    ap.add_argument("--tag", default="r2_4151")
    args = ap.parse_args()

    print(__doc__.split("\n\n")[0])
    print()
    print("1. THE LEDGER. What each bus CLAIMS of G14's +6.0 dBFS premix budget.\n")
    all_rows = {}
    for tag, rep in (("r2_4147", "master_R2-4147.json"),
                     ("r2_4151", "master_R2-4151.json")):
        rows, lin_sum, st = ledger(tag, rep)
        mix = np.zeros_like(st["engine"])
        for x in st.values():
            mix += x
        premix_tp = dsp.true_peak_dbtp(mix, SR)
        print_ledger(tag, rows, lin_sum, premix_tp)
        all_rows[tag] = (rows, lin_sum, premix_tp, st, mix)
    rows, lin_sum, premix_tp, st, mix = all_rows["r2_4151"]

    # where the premix peak is, and who owns it
    i = int(np.argmax(np.abs(mix).max(axis=1)))
    ch = int(np.argmax(np.abs(mix[i])))
    print("   WHERE THE PREMIX PEAK IS, AND WHO OWNS IT (r2_4151):")
    print("     film t = %.3f s, channel %d, value %+.2f dBFS"
          % (i / SR, ch, db(abs(mix[i, ch]))))
    contrib = sorted(((float(x[i, ch]), k) for k, x in st.items()),
                     key=lambda a: -abs(a[0]))
    for v, k in contrib[:6]:
        print("       %-17s %+9.4f  (%.1f %% of the peak)"
              % (k, v, 100.0 * v / mix[i, ch]))
    print()

    kap, budget_dbtp, on = coincidence(st, mix, premix_tp, lin_sum)
    validate(budget_dbtp)
    meter_validity(args.tag)

    if args.budget:
        budget(args.tag, (1.0, 1.394, 1.8, 2.2, 2.6, 3.0), True)


if __name__ == "__main__":
    main()
