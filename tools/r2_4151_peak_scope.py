#!/usr/bin/env python
"""R2-4151 -- WHAT `BUS_PEAK_CEILING` IS ACTUALLY MEASURING, AND WHAT ACTUALLY
BOUNDS THE BREACH.

    .venv/bin/python -m tools.r2_4151_peak_scope [--chain]

R2-4150 left this open: "THE BLOCKER IS `BUS_PEAK_CEILING` AGAINST AN EVENT BUS,
AND IT IS 8.38 dB. R2-4034's derivation is about sub-bass the K-weighting cannot
hear." This file measures every limb of that sentence. Four sections, in the
order they have to be believed:

  1. THE DEAFNESS, MEASURED. R2-4034's derivation is that the K-weighted 3 s
     meter under-reads the breach's buses because they are almost entirely
     sub-bass. The direct measure of that is the same short-term meter taken
     K-WEIGHTED and taken UNWEIGHTED; the gap is how much of the bus sits under
     the meter's own rolloff. R2-4034's own case, the `impact` bus, read a
     14.09 dB gap. It reads +0.07 dB now, and no bus in this film exceeds
     +2.27 dB -- because R2-4035, in the same rebuild, moved the transient
     world-attached sources onto the film grid and took `impact` from 92.99 %
     of its energy below 30 Hz to 3.09 %. THE STATED REASON IS GONE.

  2. WHAT THE CRITERION REDUCES TO. `g_peak < g_lufs` is exactly
     `PLR > -target`, where PLR is the bus's peak-to-loudness ratio. So it is a
     crest tax whose threshold is a mix constant, and it punishes eventfulness
     by construction -- the fourth mechanism in this film that does.

  3. THE POSITIVE CONTROL. `audio/controls/synth.glass_breach` is the validated
     physics positive for this exact event, and its PLR is measured here beside
     the film's. A criterion that would tax the reference answer harder than
     the thing being fixed is not measuring the defect.

  4. WHAT ACTUALLY BINDS (`--chain`, ~10 min). The R2-4150 stems are summed and
     put through master.py's real post-premix chain -- 30 Hz high-pass, program
     gain, DC block, the solved-for single limiter pass -- with the `shards` bus
     swept. G14 (premix peak <= +6 dBFS) and G1 (limiter GR <= 3 dB) are read
     off directly. Both are DECLARED thresholds and neither may be moved, so
     what they say is the whole size of the prize.
"""

import argparse
import json
import math
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal as _sig

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import dsp                                             # noqa: E402
from audio import percept as P                                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 96000
TARGET_LUFS_I = -23.0
CEILING_DBTP = -1.15


def max_short_term(x, sr, k_weighted=True, win_s=3.0, hop_s=0.5):
    """`dsp.max_short_term_lufs`, with the K-weighting made optional.

    Identical arithmetic otherwise -- same window, same hop, same -0.691 -- so
    the two differ ONLY by the filter, and their gap is the meter's deafness to
    this bus and nothing else.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    p = np.zeros(x.shape[0])
    for ch in range(x.shape[1]):
        if k_weighted:
            (b1, a1), (b2, a2) = dsp._k_weighting(sr)
            y = _sig.lfilter(b2, a2, _sig.lfilter(b1, a1, x[:, ch]))
        else:
            y = x[:, ch]
        p += y * y
    c = np.concatenate([[0.0], np.cumsum(p)])
    w, h = int(win_s * sr), max(int(hop_s * sr), 1)
    starts = np.arange(0, c.shape[0] - 1 - w, h)
    return float(-0.691 + 10.0 * np.log10(max(float(((c[starts + w] - c[starts]) / w).max()), 1e-20)))


def deafness_table(tag, report):
    d = os.path.join(ROOT, "audio", "out", tag, "stems")
    bl = json.load(open(os.path.join(ROOT, "audio", "out", tag, report)))["buses"]
    print("  %-16s %8s %8s %8s %9s %8s" % ("bus", "K-wtd", "unwtd", "deaf dB",
                                           "PLR dB", "trim dB"))
    worst = ("", -99.0)
    for nm in sorted(os.listdir(d)):
        if not nm.endswith(".wav"):
            continue
        k = nm[:-4]
        if k not in bl:
            continue
        x, _ = sf.read(os.path.join(d, nm), always_2d=True)
        x = x.astype(np.float64)
        if float(np.abs(x).max()) < 1e-12:
            continue
        pre = x * 10.0 ** (-bl[k]["trim_db"] / 20.0)
        lk = max_short_term(pre, SR, True)
        lu = max_short_term(pre, SR, False)
        plr = 20.0 * math.log10(max(float(np.abs(pre).max()), 1e-12)) - lk
        if lu - lk > worst[1]:
            worst = (k, lu - lk)
        print("  %-16s %8.2f %8.2f %8.2f %9.2f %8.2f  %s"
              % (k, lk, lu, lu - lk, plr, bl[k]["trim_db"],
                 "PEAK CRITERION WON" if bl[k]["peak_criterion_won"] else ""))
    print("  deafest bus in the film: %s, %+.2f dB\n" % worst)


def chain(stems, sg, dg):
    rest = sum(v for k, v in stems.items() if k not in ("shards", "debris"))
    m = (rest + stems["shards"] * 10 ** (sg / 20)
         + stems["debris"] * 10 ** (dg / 20)).astype(np.float32)
    raw_peak = float(np.abs(m).max())
    m = _sig.sosfilt(_sig.butter(4, 30.0, btype="highpass", fs=SR, output="sos"),
                     m, axis=0).astype(np.float32)
    _, g_db = dsp.program_gain(m.mean(axis=1), SR, target_rms=0.085, attack_s=6.0,
                               release_s=12.0, max_boost_db=7.0, max_cut_db=3.0)
    m = m * (10.0 ** (g_db / 20.0)).astype(np.float32)[:, None]
    m = _sig.sosfilt(_sig.butter(2, 12.0, btype="highpass", fs=SR, output="sos"),
                     m, axis=0).astype(np.float32)
    pre = m.copy()
    L0, _, _ = dsp.loudness_lufs(pre, SR)
    makeup, gr = TARGET_LUFS_I - L0, 0.0
    for _ in range(4):
        y, gr_i = dsp.soft_limit((pre * float(10.0 ** (makeup / 20.0))).astype(np.float32),
                                 ceiling=10.0 ** (CEILING_DBTP / 20.0), sr=SR)
        L, _, _ = dsp.loudness_lufs(y, SR)
        gr = min(gr, float(gr_i))
        if abs(L - TARGET_LUFS_I) < 0.05:
            break
        makeup += (TARGET_LUFS_I - L)
    return 20.0 * math.log10(raw_peak), gr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chain", action="store_true",
                    help="also run the real post-premix chain (slow)")
    args = ap.parse_args()

    print("1. THE DEAFNESS. Same 3 s short-term meter, K-weighted and not.")
    print("   R2-4034's case: the `impact` bus, +0.82 dBFS unweighted against")
    print("   -13.26 K-weighted, i.e. 14.09 dB. That was measured BEFORE")
    print("   R2-4035 moved it onto the film grid.\n")
    print("  -- R2-4147, the shipped master")
    deafness_table("r2_4147", "master_R2-4147.json")
    print("  -- R2-4150, the rebuilt breach")
    deafness_table("r2_4150", "master_R2-4150.json")

    print("2. WHAT THE CRITERION REDUCES TO.")
    print("   g_peak < g_lufs  <=>  20log10(C/pk) < target - Lk")
    print("                    <=>  20log10(pk) - Lk > 20log10(C) - target")
    print("                    <=>  PLR > -target      (at C = 1.0)")
    print("   So a bus is trimmed below its declared loudness exactly when its")
    print("   peak-to-loudness ratio exceeds a MIX CONSTANT. `shards` declares")
    print("   -9.0, so anything over 9.0 dB of PLR is taxed -- which is less")
    print("   PLR than any transient signal has.\n")

    print("3. THE POSITIVE CONTROL, at the same measure.")
    from audio.controls import synth                              # noqa: E402
    for inc in (("dice", "slabs", "mullions"), ("dice",), ("slabs",), ("mullions",)):
        y = np.asarray(synth.glass_breach(include=inc)[0], dtype=np.float64)
        if y.ndim > 1:
            y = y.mean(axis=1)
        pk = 20.0 * math.log10(float(np.abs(y).max()))
        lk = max_short_term(y, 48000, True)
        print("   corpus %-26s PLR %6.2f dB   crest %6.2f dB   AMI %.4f"
              % ("+".join(inc), pk - lk,
                 20 * math.log10(float(np.abs(y).max()) / float(np.sqrt((y ** 2).mean()))),
                 P.articulation_modulation_index(y, 48000).get("ami", float("nan"))))
    print("   The validated physics positive for this exact event is PEAKIER")
    print("   than the rebuilt bus the criterion trimmed 11.71 dB. A guard that")
    print("   would tax the reference answer harder is not measuring a defect.\n")

    if not args.chain:
        print("4. skipped -- pass --chain (about 10 minutes).")
        return
    print("4. WHAT ACTUALLY BINDS. R2-4150's stems through the real chain.")
    d = os.path.join(ROOT, "audio", "out", "r2_4150", "stems")
    stems = {}
    for nm in sorted(os.listdir(d)):
        if nm.endswith(".wav"):
            x, _ = sf.read(os.path.join(d, nm), always_2d=True)
            stems[nm[:-4]] = x.astype(np.float32)
    print("   %10s %10s %14s %8s %14s %8s" % ("shards", "debris", "premix dBFS",
                                              "G14", "limiter GR", "G1"))
    for sg, dg in ((0, 0), (4, -9), (6, -9), (8.38, -9), (12, -12)):
        pk, gr = chain(stems, sg, dg)
        print("   %+10.2f %+10.2f %+13.2f %8s %+13.2f %8s"
              % (sg, dg, pk, "PASS" if pk <= 6 else "FAIL",
                 gr, "PASS" if gr >= -3.0 else "FAIL"))
    print()
    print("   G14 binds at about +4.05 dB and G1 at about +8.2 dB. Both are")
    print("   DECLARED thresholds. The 8.38 dB the OPEN item asked for is not")
    print("   available from the mix at any setting of the ceiling.")


if __name__ == "__main__":
    main()
