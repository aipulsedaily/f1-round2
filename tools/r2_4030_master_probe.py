"""MEASURE A MASTER AGAINST THE CHAIN+GLASS SPEC'S GATES (R2-4030).

    .venv/bin/python tools/r2_4030_master_probe.py audio/out/master.wav [--json out.json]

Every number this prints is one the spec named a target for, so a fix can be
watched failing before it is applied and watched moving after. Nothing here
duplicates `audio/verify.py` -- that file belongs to the gate-rebuild workflow
and is not touched by this one.

THE WINDOW IS BEAT 3, 36.0-44.0 s. The brief said beat 4; `docs/beat_sheet.json`
says `3_breach` = 36.0-44.0 s and `4_transit` = 44.0-49.6 s. Anyone auditioning
beat 4 has been listening to the transit.
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

BREACH = (36.0, 44.0)
BEATS = {
    "1_assembly": (0.0, 33.0), "2_launch": (33.0, 36.0), "3_breach": (36.0, 44.0),
    "4_transit": (44.0, 49.6), "5_lap": (49.6, 113.1), "6_ending": (113.1, 124.1),
}


def _mono(x):
    return x.mean(axis=1) if x.ndim > 1 else x


def band_fractions(x, sr, edges=(0, 20, 30, 60, 100, 500, 2000, 4000, 6000, 8000, 24000)):
    """Fraction of energy in each band, from one Welch PSD of the window."""
    f, p = _sig.welch(_mono(x), sr, nperseg=min(1 << 15, len(x)), noverlap=None)
    tot = float(np.trapezoid(p, f))
    out = {}
    for a, b in zip(edges[:-1], edges[1:]):
        m = (f >= a) & (f < b)
        out["%d_%d" % (a, b)] = float(np.trapezoid(p[m], f[m]) / max(tot, 1e-30))
    cent = float(np.trapezoid(p * f, f) / max(tot, 1e-30))
    return out, cent, (f, p)


def crest_db(x, sr, win_ms=50.0):
    """Per-window crest factor (peak/RMS), in dB. The spec's most diagnostic
    statistic: Gaussian white noise scores ~10.9 dB, so anything below that is
    statistically noise."""
    m = _mono(x)
    w = int(sr * win_ms / 1000.0)
    k = len(m) // w
    if k == 0:
        return np.array([0.0])
    seg = m[:k * w].reshape(k, w).astype(np.float64)
    pk = np.abs(seg).max(axis=1)
    rms = np.sqrt((seg ** 2).mean(axis=1))
    ok = rms > 1e-7
    return 20.0 * np.log10(pk[ok] / rms[ok])


def onset_density(x, sr, lo, hi, hop_ms=1.0, refractory_ms=5.0):
    """Onsets per second in a band: spectral-flux peaks on the band-passed
    envelope. This is what 'the shower is 25-60x too sparse' was measured with.

    THE REFRACTORY PERIOD IS A CEILING ON THE MEASUREMENT, so it is stated. At
    the 20 ms this started with, no signal on earth could score above 50/s and
    G6's 150/s threshold was unreachable by construction. 5 ms caps it at 200/s,
    which is above the gate and still longer than the ~2 ms it takes two
    transients to stop being one.
    """
    m = _mono(x).astype(np.float64)
    sos = _sig.butter(4, [lo, min(hi, sr * 0.49)], btype="bandpass", fs=sr, output="sos")
    b = _sig.sosfilt(sos, m)
    hop = max(int(sr * hop_ms / 1000.0), 1)
    k = len(b) // hop
    env = np.abs(b[:k * hop].reshape(k, hop)).max(axis=1)
    env = np.maximum(env, 1e-9)
    d = np.diff(20.0 * np.log10(env), prepend=20.0 * np.log10(env[0]))
    # an onset is a >6 dB jump that is a local maximum of the rise
    cand = d > 6.0
    pk = cand & (d >= np.maximum(np.roll(d, 1), np.roll(d, -1)))
    idx = np.flatnonzero(pk)
    keep, last = [], -10 ** 9
    for i in idx:
        if (i - last) * hop_ms >= refractory_ms:
            keep.append(i)
            last = i
    return len(keep) / (len(b) / sr)


def onset_rise_ms(x, sr, lo=1000.0, hi=8000.0, n_top=15):
    """10-90% rise time of the strongest attacks in a band."""
    m = _mono(x).astype(np.float64)
    sos = _sig.butter(4, [lo, min(hi, sr * 0.49)], btype="bandpass", fs=sr, output="sos")
    b = np.abs(_sig.sosfilt(sos, m))
    e = _sig.sosfilt(_sig.butter(2, 400.0, btype="lowpass", fs=sr, output="sos"), b)
    pk_i = np.argsort(e)[::-1]
    rises, used = [], []
    for i in pk_i:
        if len(rises) >= n_top:
            break
        if any(abs(int(i) - u) < int(0.05 * sr) for u in used):
            continue
        used.append(int(i))
        p = e[i]
        a0 = max(int(i) - int(0.20 * sr), 0)
        seg = e[a0:i + 1]
        if seg.size < 4 or p <= 0:
            continue
        lo_i = np.flatnonzero(seg <= 0.1 * p)
        hi_i = np.flatnonzero(seg >= 0.9 * p)
        if lo_i.size and hi_i.size and hi_i[-1] > lo_i[-1]:
            rises.append((hi_i[-1] - lo_i[-1]) / sr * 1e3)
    return float(np.median(rises)) if rises else float("nan")


GLASS_FILM_T = 36.00010          # clock.film_at_world(filmtime.GLASS_WORLD_T)


def impact_rise_ms(x, sr, t_impact=GLASS_FILM_T, lo=1000.0, hi=8000.0):
    """10-90 % rise at the ONE onset whose time is known independently.

    `onset_rise_ms` above takes the strongest attacks it can find, which is the
    right measurement on a sparse signal and the wrong one on a dense shower:
    once the 1-8 kHz band is full of shards, "the loudest envelope points" are
    in the middle of the texture and the 10-90 % window measures the texture's
    build-up rather than an attack. Densifying the shower therefore made that
    number go UP (6.9 -> 57.0 ms) while the event it is supposed to describe got
    sharper. G5 is about the impact, and the impact's time is not in dispute:
    the nose meets the pane at world t = GLASS_WORLD_T, which the clock maps to
    film t = 36.00010 s, frame 864.
    """
    m = _mono(x).astype(np.float64)
    sos = _sig.butter(4, [lo, min(hi, sr * 0.49)], btype="bandpass", fs=sr, output="sos")
    i0 = int((t_impact - 0.030) * sr)
    i1 = int((t_impact + 0.060) * sr)
    b = np.abs(_sig.sosfilt(sos, m[i0:i1]))
    e = _sig.sosfilt(_sig.butter(2, 2000.0, btype="lowpass", fs=sr, output="sos"), b)
    if e.size < 8 or e.max() <= 0:
        return float("nan")
    pk = int(np.argmax(e))
    p = e[pk]
    seg = e[:pk + 1]
    lo_i = np.flatnonzero(seg <= 0.1 * p)
    hi_i = np.flatnonzero(seg >= 0.9 * p)
    if not (lo_i.size and hi_i.size and hi_i[-1] > lo_i[-1]):
        return float("nan")
    return float((hi_i[-1] - lo_i[-1]) / sr * 1e3)


def probe(path):
    x, sr = sf.read(path, always_2d=True)
    dur = x.shape[0] / sr
    rep = {"file": path, "sr": sr, "duration_s": dur,
           "sample_peak_dbfs": float(20 * np.log10(max(float(np.abs(x).max()), 1e-12)))}

    a, b = BREACH
    br = x[int(a * sr):int(b * sr)]
    frac, cent, _ = band_fractions(br, sr)
    c50 = crest_db(br, sr)
    rep["breach"] = {
        "window_s": list(BREACH),
        "band_fractions": frac,
        "pct_above_4k": 100.0 * (frac["4000_6000"] + frac["6000_8000"] + frac["8000_24000"]),
        "pct_above_6k": 100.0 * (frac["6000_8000"] + frac["8000_24000"]),
        "pct_below_100": 100.0 * (frac["0_20"] + frac["20_30"] + frac["30_60"] + frac["60_100"]),
        "pct_below_30": 100.0 * (frac["0_20"] + frac["20_30"]),
        "spectral_centroid_hz": cent,
        "crest_50ms_p50_db": float(np.median(c50)),
        "crest_50ms_max_db": float(c50.max()),
        "onset_rise_10_90_ms": onset_rise_ms(br, sr),
        "impact_rise_10_90_ms": impact_rise_ms(x, sr),
        "onsets_per_s_1k_4k": onset_density(br, sr, 1000.0, 4000.0),
        "onsets_per_s_4k_12k": onset_density(br, sr, 4000.0, 12000.0),
        "lr_correlation": float(np.corrcoef(br[:, 0], br[:, 1])[0, 1]) if br.shape[1] > 1 else 1.0,
    }
    # peak of the shower: the densest 1 s inside the breach
    dens = [onset_density(x[int(t * sr):int((t + 1.0) * sr)], sr, 1000.0, 4000.0)
            for t in np.arange(a, b - 1.0, 0.5)]
    rep["breach"]["onsets_per_s_1k_4k_peak_1s"] = float(max(dens)) if dens else 0.0

    cw = crest_db(x, sr)
    rep["whole_film"] = {
        "crest_50ms_p50_db": float(np.median(cw)),
        "crest_50ms_p90_db": float(np.percentile(cw, 90)),
        "gaussian_white_reference_db": 10.9,
    }
    fr_all, cent_all, (f, p) = band_fractions(x, sr)
    rep["whole_film"]["band_fractions"] = fr_all
    rep["whole_film"]["spectral_centroid_hz"] = cent_all
    rep["whole_film"]["pct_below_30"] = 100.0 * (fr_all["0_20"] + fr_all["20_30"])

    def brms(lo, hi):
        m = (f >= lo) & (f < hi)
        return float(10 * np.log10(max(float(np.trapezoid(p[m], f[m])), 1e-30)))
    rep["whole_film"]["band_rms_dbfs"] = {
        "1k_2k": brms(1000, 2000), "2k_4k": brms(2000, 4000), "4k_8k": brms(4000, 8000),
        "8k_12k": brms(8000, 12000), "12k_16k": brms(12000, 16000)}

    rep["beats"] = {}
    for name, (s0, s1) in BEATS.items():
        seg = x[int(s0 * sr):int(min(s1, dur) * sr)]
        if seg.shape[0] < sr // 2:
            continue
        fb, cb, _ = band_fractions(seg, sr)
        cb50 = crest_db(seg, sr)
        rep["beats"][name] = {
            "spectral_centroid_hz": cb,
            "pct_above_4k": 100.0 * (fb["4000_6000"] + fb["6000_8000"] + fb["8000_24000"]),
            "pct_below_30": 100.0 * (fb["0_20"] + fb["20_30"]),
            "crest_50ms_p50_db": float(np.median(cb50)),
        }
    return rep


GATES = [
    ("G2  breach energy >4 kHz", lambda r: r["breach"]["pct_above_4k"], ">=", 8.0, "%"),
    ("G3  breach spectral centroid", lambda r: r["breach"]["spectral_centroid_hz"], ">=", 1200.0, "Hz"),
    ("G4  breach 50 ms crest (p50)", lambda r: r["breach"]["crest_50ms_p50_db"], ">=", 18.0, "dB"),
    ("G5  impact rise 10-90% @36.0001s", lambda r: r["breach"]["impact_rise_10_90_ms"], "<=", 2.0, "ms"),
    ("G6  shard onsets 1-4 kHz, peak 1 s", lambda r: r["breach"]["onsets_per_s_1k_4k_peak_1s"], ">=", 150.0, "/s"),
    ("G13 median 50 ms crest, whole film", lambda r: r["whole_film"]["crest_50ms_p50_db"], ">", 11.0, "dB"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    r = probe(a.wav)
    print("=" * 78)
    print("MASTER PROBE  %s   %.3f s @ %d Hz" % (os.path.basename(a.wav), r["duration_s"], r["sr"]))
    print("=" * 78)
    b = r["breach"]
    print("BREACH 36.0-44.0 s (beat 3, `3_breach` -- NOT beat 4)")
    print("  spectral centroid      %10.1f Hz" % b["spectral_centroid_hz"])
    print("  energy <30 Hz          %10.2f %%" % b["pct_below_30"])
    print("  energy <100 Hz         %10.2f %%" % b["pct_below_100"])
    print("  energy >4 kHz          %10.4f %%" % b["pct_above_4k"])
    print("  energy >6 kHz          %10.4f %%" % b["pct_above_6k"])
    print("  50 ms crest p50/max    %6.2f / %6.2f dB" % (b["crest_50ms_p50_db"], b["crest_50ms_max_db"]))
    print("  onset rise 10-90%%      %10.2f ms  (loudest-attack estimator)"
          % b["onset_rise_10_90_ms"])
    print("  IMPACT rise 10-90%%     %10.2f ms  (at t=36.00010 s, frame 864)"
          % b["impact_rise_10_90_ms"])
    print("  onsets/s 1-4 kHz       %10.1f  (peak 1 s %.1f)"
          % (b["onsets_per_s_1k_4k"], b["onsets_per_s_1k_4k_peak_1s"]))
    print("  onsets/s 4-12 kHz      %10.1f" % b["onsets_per_s_4k_12k"])
    print("  L/R correlation        %10.3f" % b["lr_correlation"])
    w = r["whole_film"]
    print("WHOLE FILM")
    print("  median 50 ms crest     %10.2f dB   (Gaussian white = 10.9)" % w["crest_50ms_p50_db"])
    print("  energy <30 Hz          %10.2f %%" % w["pct_below_30"])
    print("  band RMS dB: " + "  ".join("%s %.1f" % (k, v) for k, v in w["band_rms_dbfs"].items()))
    print("PER BEAT   centroid   >4kHz%%   <30Hz%%   crest50")
    for k in sorted(r["beats"]):
        v = r["beats"][k]
        print("  %-12s %8.1f %8.3f %8.2f %8.2f"
              % (k, v["spectral_centroid_hz"], v["pct_above_4k"], v["pct_below_30"],
                 v["crest_50ms_p50_db"]))
    print("-" * 78)
    npass = 0
    for name, fn, op, thr, unit in GATES:
        val = fn(r)
        ok = (val >= thr) if op == ">=" else (val > thr) if op == ">" else (val <= thr)
        npass += bool(ok)
        print("  %-36s %10.3f %s %s %-4s  %s"
              % (name, val, op, thr, unit, "PASS" if ok else "FAIL"))
    print("  %d/%d gates pass" % (npass, len(GATES)))
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(r, fh, indent=1, default=float)
        print(">> %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
