"""THE GATES. Every claim in the report is produced here, or it is not claimed.

    .venv/bin/python -m audio.verify --wav audio/out/master.wav \
        --report audio/out/master_report.json --out audio/out

Written under this project's own rule: a gate that has never failed has never
been tested. Every gate below has a POSITIVE CONTROL -- an artefact constructed
to be bad in exactly the way the gate is supposed to catch -- and the control's
result is printed next to the real one. If a control passes, the gate is broken
and the run says so.

    seam gate         control: the same mix with a 1-sample splice at a beat
                      boundary, and with a 3 dB step
    pitch gate        control: the engine re-synthesised from a CONSTANT speed
    doppler gate      control: the same pass rendered with the source held still
    external-asset    control: a file containing `sf.read("engine.wav")`
    kerb classifier   control: a position track that deliberately runs wide
"""

from __future__ import annotations

import argparse
import json
import os
import ast
import re
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy import signal as _sig

from . import dsp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.dirname(os.path.abspath(__file__))
# A doppler window whose measured ratio is further than this from the prediction
# is a COMB-SEARCH FAILURE, not a Doppler error: the misses are exact simple
# ratios (0.75 = one tooth over, 0.485 = the sub-octave), 480 cents and up, while
# the worst genuine error either master shows is 30 cents. See `doppler_gate`.
TRACK_MAX_CENTS = 200.0

# THE FIRING ORDER, IN ONE PLACE, BECAUSE B7 MOVES IT.
# Today's engine fires evenly on a 120-degree crank, so the fundamental is
# engine order 3 (rpm/60*3). The spec's B7 adopts the FIA Art. 5.2.10 three-
# journal geometry, which forces uneven 90/150 firing and moves the fundamental
# to order 1.5 -- HALVING it. `doppler` is the only load-bearing gate the old
# suite had, and a comb search handed the wrong fundamental locks an octave out
# and reports a tracker failure fraction, not a Doppler failure. So the order
# lives here, both gates read it, and porting B7 is one edit rather than a hunt.
ENGINE_ORDER = 3.0
DOPPLER_MIN_CLOSING_MS = 15.0
# A pass worth measuring. Below ~15 m/s of closing speed the ratio moves by
# under 0.8 semitones over the window and the measurement is inside its own
# error bar, so the station is not manufactured -- it is skipped and said so.
# frame rate comes from the beat sheet, which is the film's own declaration
with open(os.path.join(ROOT, "docs", "beat_sheet.json")) as _fh:
    FPS = int(json.load(_fh)["fps"])


# ============================================================== f0 tracking ===
def track_f0(x, sr, t_centres, lo=120.0, hi=1400.0, win=8192, harmonics=5):
    """Harmonic-product-spectrum f0, one estimate per centre time.

    HPS rather than a plain spectral peak: the exhaust's strongest partial is
    often the 2nd or 3rd, and a peak-picker would report octave errors that look
    like a broken engine. HPS multiplies decimated copies of the magnitude
    spectrum so only the true fundamental survives, then the candidate is
    re-scored against its own 2x/3x/4x by harmonic summation to undo the
    sub-octave errors HPS makes when the fundamental is weak.

    VALIDATED against a synthetic four-harmonic chirp of known f0: see
    `main()`'s `f0_tracker_control`.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    w = np.hanning(win)
    out = np.full(t_centres.shape[0], np.nan)
    conf = np.zeros(t_centres.shape[0])
    for i, tc in enumerate(t_centres):
        a = int(tc * sr) - win // 2
        if a < 0 or a + win >= x.shape[0]:
            continue
        seg = x[a:a + win] * w
        if float(np.abs(seg).max()) < 1e-7:
            continue
        S = np.abs(np.fft.rfft(seg, n=win * 2))
        f = np.fft.rfftfreq(win * 2, 1.0 / sr)
        hps = S.copy()
        for k in range(2, harmonics + 1):
            d = S[::k]
            hps[:d.shape[0]] *= d
        m = (f >= lo) & (f <= hi)
        idx = np.flatnonzero(m)
        if idx.size == 0:
            continue
        j = idx[np.argmax(hps[idx])]
        # OCTAVE / SUB-OCTAVE CORRECTION. Harmonic-product spectra fall into a
        # sub-harmonic when the true fundamental is weak, and an engine on
        # OVERRUN -- injectors cut, no combustion, only pumping -- is exactly
        # that case. Measured on the dry engine, 18 % of windows came back at
        # f0/4 (169 Hz against a true 673 Hz). The candidate is therefore
        # re-scored against its own 2x, 3x and 4x by harmonic summation on the
        # RAW spectrum, which a sub-octave loses because it has no energy at its
        # own fundamental.
        best, best_sc = f[j], -1.0
        for mul in (1, 2, 3, 4):
            fc = f[j] * mul
            if fc > hi * 1.05:
                break
            sc = 0.0
            for k in range(1, 7):
                b = int(round(fc * k / (f[1] - f[0])))
                if b + 2 < S.shape[0]:
                    sc += float(S[max(b - 2, 0):b + 3].max()) / (k ** 0.5)
            if sc > best_sc * 1.02:
                best_sc, best = sc, fc
        j = int(np.clip(int(round(best / (f[1] - f[0]))), 1, S.shape[0] - 2))
        # parabolic refinement on the log magnitude of the RAW spectrum
        y0, y1, y2 = np.log(np.maximum(S[j - 1:j + 2], 1e-30))
        # A PEAK has a NEGATIVE second difference. Clamping the denominator with
        # max(.., 1e-12) -- the obvious-looking guard -- turned every peak into a
        # division by 1e-12 and reported f0 in the terahertz.
        den = y0 - 2.0 * y1 + y2
        d = 0.5 * (y0 - y2) / den if abs(den) > 1e-9 else 0.0
        out[i] = f[j] + float(np.clip(d, -0.5, 0.5)) * (f[1] - f[0])
        conf[i] = float(S[j] / max(np.median(S[idx]), 1e-30))
    return out, conf


def doppler_ratio(x, sr, t_centres, f_emit, win=16384, rmin=0.60, rmax=1.65,
                  n_harm=8, nres=1600):
    """Measure the received/emitted frequency RATIO directly.

    Tracking f0 and dividing is the wrong tool here: in the finished mix the
    engine sits under tyre roar, wind and crowd, its strongest partial moves
    between the 1st and the 3rd depending on the pipe resonances, and for part
    of the pass the car is on the brakes with the injectors cut and there is no
    firing tone at all. What IS known is the emitted fundamental, from the
    telemetry. So the measurement is a comb search: slide a harmonic comb built
    on `f_emit` across a log-frequency grid of ratios and take the ratio that
    best explains the observed spectrum. That measures the quantity the gate is
    actually about, and it degrades to "no answer" rather than to an octave
    error when the engine is quiet.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim > 1:
        x = x.mean(axis=1)
    w = np.hanning(win)
    nfft = win * 2
    f = np.fft.rfftfreq(nfft, 1.0 / sr)
    df = f[1] - f[0]
    ratios = np.exp(np.linspace(np.log(rmin), np.log(rmax), nres))
    out = np.full(t_centres.shape[0], np.nan)
    conf = np.zeros(t_centres.shape[0])
    for i, (tc, fe) in enumerate(zip(t_centres, np.atleast_1d(f_emit))):
        a = int(tc * sr) - win // 2
        if a < 0 or a + win >= x.shape[0] or not np.isfinite(fe) or fe <= 0:
            continue
        S = np.abs(np.fft.rfft(x[a:a + win] * w, n=nfft))
        sc = np.zeros(nres)
        for k in range(1, n_harm + 1):
            b = np.rint(ratios * k * fe / df).astype(np.int64)
            ok = (b > 1) & (b < S.shape[0] - 2)
            v = np.zeros(nres)
            bb = b[ok]
            v[ok] = np.maximum.reduce([S[bb - 1], S[bb], S[bb + 1]])
            sc += v / (k ** 0.5)
        j = int(np.argmax(sc))
        conf[i] = float(sc[j] / max(np.median(sc), 1e-30))
        if 0 < j < nres - 1:
            y0, y1, y2 = sc[j - 1], sc[j], sc[j + 1]
            den = y0 - 2.0 * y1 + y2
            d = 0.5 * (y0 - y2) / den if abs(den) > 1e-12 else 0.0
            lg = np.log(ratios)
            out[i] = float(np.exp(lg[j] + np.clip(d, -0.5, 0.5) * (lg[1] - lg[0])))
        else:
            out[i] = float(ratios[j])
    return out, conf


# ================================================================ seam gate ===
def _boundary_samples(sheet, sr):
    out = []
    for b in sheet["beats"][1:]:
        f = int(round(b["start_s"] * FPS)) + 1
        out.append((b["name"], f, int((f - 1) / FPS * sr)))
    return out


def seam_gate(x, sr, sheet, label="", half_ref_s=0.5):
    """Is the waveform continuous across every beat boundary?

    THE STATISTIC IS THE THIRD DIFFERENCE, taken at the boundary sample and
    referenced to the LOCAL half-second around it. A cut -- a splice, a jump to
    other material, an instantaneous gain change -- is a step in a signal that
    is otherwise band-limited to 20 kHz at 48 kHz, and a step is what a third
    difference is built to find. The local reference matters: the film's own
    loudest transient is the glass, one frame into beat 3, so a global reference
    would call the breach a cut.

    Reported alongside, NOT as pass/fail:
      * hp20k -- energy above 20 kHz at the boundary sample, a second and
        independently-derived view of the same question.
      * spectral_jump_db -- how much the third-octave spectrum changes across
        the boundary. Beat 3's boundary IS the largest spectral change in the
        film, by design: it is the frame the car reaches the glass. A gate that
        failed on that would be a gate demanding the film not have a breach.

    MEASURED SENSITIVITY, from the controls in `control_seam`:
        977-sample splice          p99.998   caught
        3 dB instantaneous step    p99.950   caught
        0.5 dB instantaneous step  p91.19    NOT caught (below the master's own
                                             worst boundary, p90.2, by 1 point)
        40 ms crossfade            see below -- a crossfade is smooth and has no
                                             step; it is caught by the spectral
                                             jump, which is why that number is
                                             reported even though it does not
                                             gate.
    So: this gate proves the absence of a discontinuity down to about a 1 dB
    instantaneous level change. It cannot prove the absence of a slow fade, and
    it is not asked to -- the render applies exactly two time-varying gains, the
    program gain and the limiter, and `master_report.json` states the maximum
    per-sample change of both.

    WHAT WAS THROWN AWAY. Version 1 compared |x[i+1]-x[i]| at the boundary to
    the local 99.99th percentile of |x[i+1]-x[i]|; a real splice scored 2.0
    against a threshold of 4.0 and BOTH controls passed. Version 2 used a
    third-octave spectral distance and failed the MASTER at every boundary,
    because the master legitimately changes spectrum at every beat.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    n = x.shape[0]
    mono = x.mean(axis=1)

    d3 = np.abs(np.diff(mono, n=3, prepend=[0.0, 0.0, 0.0]))
    hp = np.abs(_sig.sosfilt(_sig.butter(6, min(20000.0, sr * 0.47),
                                         btype="highpass", fs=sr, output="sos"), mono))
    half = int(half_ref_s * sr)

    wlen = int(0.021 * sr)
    win = np.hanning(wlen)
    nf = 1 << int(np.ceil(np.log2(wlen)))
    fr = np.fft.rfftfreq(nf, 1.0 / sr)
    edges = 1000.0 * 2.0 ** (np.arange(-30, 15) / 3.0)
    bidx = [b for b in (np.flatnonzero((fr >= a) & (fr < c))
                        for a, c in zip(edges[:-1], edges[1:])) if b.size]

    def spectral_at(i):
        if i - wlen < 0 or i + wlen >= n:
            return 0.0
        A = np.abs(np.fft.rfft(mono[i - wlen:i] * win, n=nf))
        B = np.abs(np.fft.rfft(mono[i:i + wlen] * win, n=nf))
        da = np.array([20.0 * np.log10(max(float(A[b].mean()), 1e-12)) for b in bidx])
        db = np.array([20.0 * np.log10(max(float(B[b].mean()), 1e-12)) for b in bidx])
        return float(np.abs(da - db).mean())

    rows = []
    for name, frame, i in _boundary_samples(sheet, sr):
        a0, b0 = max(i - half, 0), min(i + half, n)
        v3 = float(d3[i:i + 4].max())
        vh = float(hp[i:i + 4].max())
        rows.append({
            "beat": name, "frame": frame, "sample": i,
            "d3": v3,
            "d3_local_percentile": float((d3[a0:b0] < v3).mean() * 100.0),
            "d3_local_p99_9": float(np.percentile(d3[a0:b0], 99.9)),
            "hp20k": vh,
            "hp20k_local_percentile": float((hp[a0:b0] < vh).mean() * 100.0),
            "spectral_jump_db": spectral_at(i),
            "max_sample_delta_pm2ms": float(np.abs(np.diff(
                x[max(i - int(0.002 * sr), 0):i + int(0.002 * sr)], axis=0)).max()),
        })
    worst = max(r["d3_local_percentile"] for r in rows)
    return {
        "label": label, "statistic": "|3rd difference| at the boundary sample, "
                                     "percentile against the local +/-0.5 s",
        "boundaries": rows,
        "worst_d3_local_percentile": worst,
        "worst_hp20k_local_percentile": max(r["hp20k_local_percentile"] for r in rows),
        "max_spectral_jump_db": max(r["spectral_jump_db"] for r in rows),
        "threshold_percentile": 99.9,
        "PASS": bool(worst < 99.9),
    }


def _d3_score_at(mono, sr, t, win_s=0.5):
    """|3rd difference| peak in a +-25 ms window at `t`, over the local median
    of the surrounding +-`win_s`."""
    n = mono.shape[0]
    i = int(t * sr)
    a0, b0 = max(i - int(win_s * sr), 0), min(i + int(win_s * sr), n)
    if b0 - a0 < 256:
        return float("nan")
    d3 = np.abs(np.diff(mono[a0:b0], n=3, prepend=[0.0, 0.0, 0.0]))
    j = i - a0
    lo, hi = max(j - int(0.025 * sr), 0), min(j + int(0.025 * sr), d3.shape[0])
    med = float(np.median(d3))
    if med <= 0 or hi <= lo:
        return float("nan")
    return float(d3[lo:hi].max() / med)


def splice_scan(x, sr, win_s=0.5, top=12):
    """THE SAME STATISTIC, FILM-WIDE, not only at the five beat boundaries.

    `seam_gate` adjudicates 20 samples of 5,956,000 -- 0.0003 % of the film --
    and that is measured, not estimated. It is why `swap_b1_loop.wav`, whose
    beat 1 is a 2 s block tiled 16.5 times with sixteen splices inside it,
    reported a seam percentile BIT-IDENTICAL to the delivered master's: every
    one of its splices was inside a beat, and the gate only visits boundaries.

    This walks the whole file and RANKS candidates. It deliberately does NOT
    carry an absolute threshold: the breach is a real 562x local-median event
    at 36.0 s and any global bar that failed it would be a bar demanding the
    film not have a breach. What is gated is the gate's own SENSITIVITY, in
    `main`, by injecting a splice mid-beat and measuring how far it stands out
    from that location's own floor.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    mono = x.mean(axis=1)
    n = mono.shape[0]
    d3 = np.abs(np.diff(mono, n=3, prepend=[0.0, 0.0, 0.0]))
    half = int(win_s * sr)
    step = max(half // 2, 1)
    hits = []
    for a0 in range(0, n - 1, step):
        b0 = min(a0 + 2 * half, n)
        seg = d3[a0:b0]
        if seg.size < 64:
            continue
        # THE REFERENCE IS THE LOCAL MEDIAN, NOT A HIGH PERCENTILE. A 99.99th
        # percentile of a 48,000-sample window is itself five samples from the
        # top, so a real splice can only ever score 2x it -- the statistic
        # saturates on exactly the event it exists to find.
        med = float(np.median(seg))
        j = int(np.argmax(seg))
        if med <= 0:
            continue
        hits.append({"t_s": float((a0 + j) / sr), "d3": float(seg[j]),
                     "local_median": med, "score": float(seg[j] / med)})
    hits.sort(key=lambda h: -h["score"])
    merged = []                      # one splice, one report
    for h in hits:
        if all(abs(h["t_s"] - m["t_s"]) > 0.05 for m in merged):
            merged.append(h)
    return {"statistic": ("|3rd difference| peak over the rolling local MEDIAN, "
                          "over the WHOLE film"),
            "windows_scanned": int((n - 1) // step + 1),
            "coverage_fraction": 1.0,
            "candidates": merged[:top],
            "worst_score": merged[0]["score"] if merged else 0.0,
            "no_absolute_threshold": (
                "by design: the breach is a legitimate 562x event and a global "
                "bar that failed it would be a bar demanding the film not have "
                "a breach. Sensitivity is gated by injection instead.")}


# ============================================================== level gate ====
def _pyloudnorm_lufs(x, sr):
    """ITU-R BS.1770-4 through `pyloudnorm` (MIT), the reference implementation.

    The spec asks `levels` to swap its hand-rolled meter for this one. Both are
    reported and their difference is gated: an in-repo K-weighting that
    disagrees with the reference by more than 0.3 LU is a bug in the meter, and
    a meter nobody cross-checks is how a level error ships.
    """
    try:
        import pyloudnorm                                     # noqa: PLC0415
    except ImportError:
        return {"available": False}
    m = pyloudnorm.Meter(sr)
    return {"available": True, "integrated_lufs": float(m.integrated_loudness(x)),
            "implementation": "pyloudnorm %s, ITU-R BS.1770-4" %
                              getattr(pyloudnorm, "__version__", "?")}


def level_gate(x, sr):
    L, st, st_t = dsp.loudness_lufs(x, sr)
    tp = dsp.true_peak_dbtp(x, sr)
    pln = _pyloudnorm_lufs(x, sr)
    pk = float(np.abs(x).max())
    n1 = x.shape[0] // sr
    seg = x[:n1 * sr].reshape(n1, sr, -1)
    rms = np.sqrt((seg.astype(np.float64) ** 2).mean(axis=(1, 2)))
    quiet = int((20 * np.log10(np.maximum(rms, 1e-12)) < -80.0).sum())
    return {
        "integrated_lufs": float(L), "true_peak_dbtp": float(tp),
        "sample_peak": pk, "sample_peak_dbfs": float(20 * np.log10(max(pk, 1e-12))),
        "clipped_samples": int((np.abs(x) >= 1.0).sum()),
        "dc_offset": [float(x[:, 0].mean()), float(x[:, 1].mean())],
        "short_term_lufs_min": float(st.min()), "short_term_lufs_max": float(st.max()),
        "short_term_range_db": float(st.max() - st.min()),
        "silent_1s_windows_below_-80dB": quiet,
        "channel_correlation": float(np.corrcoef(x[:, 0], x[:, 1])[0, 1]),
        "reference_meter": pln,
        "reference_meter_delta_lu": (
            float(L - pln["integrated_lufs"]) if pln.get("available") else None),
        "PASS": bool(tp <= -1.0 and pk < 1.0 and abs(L + 14.0) <= 0.5 and quiet == 0
                     and (not pln.get("available")
                          or abs(L - pln["integrated_lufs"]) <= 0.3)),
    }


# =============================================================== edge gate ====
def _frame_crest_profile(mono, peak_per_frame, sr, spf, ref_s):
    """Per-frame peak referenced to the LOUDER of the two adjacent `ref_s` windows."""
    c = np.concatenate([[0.0], np.cumsum(mono.astype(np.float64) ** 2)])
    n = mono.shape[0]
    ref = int(ref_s * sr)

    def _rms(a, b):
        a, b = max(int(a), 0), min(int(b), n)
        if b <= a:
            return 1e-12
        return float(np.sqrt(max((c[b] - c[a]) / (b - a), 1e-24)))

    nf = peak_per_frame.shape[0]
    out = np.empty(nf)
    for i in range(nf):
        a0, b0 = i * spf, (i + 1) * spf
        r = max(_rms(b0, b0 + ref), _rms(a0 - ref, a0), 1e-12)
        out[i] = 20.0 * np.log10(max(peak_per_frame[i], 1e-12) / r)
    return out


def edge_gate(x, sr, label="", ref_s=1.0, headroom_db=3.0):
    """DOES THE FILM'S FIRST FRAME, AND ITS LAST, BELONG TO THE FILM?

    THIS IS THE GATE THE PROJECT DID NOT HAVE, and R2-960 is why it exists. A
    circular `np.roll` used as a delay wrapped the last 11.3 ms of a 2.4 s reverb
    tail -- the tail of a car at 323 km/h -- onto the first 11.3 ms of a film
    that opens on an empty showroom. It sat in EVERY master this project
    produced, and every gate passed it:

      * `seam_gate` walks `sheet["beats"][1:]`, so it visits beat BOUNDARIES.
        Frame 1 is not a boundary between two beats, it is the outer EDGE of the
        first one, and the last frame is the outer edge of the last. The two
        places the film touches silence were the two places nothing looked.
      * `level_gate` is global: an 0.8505 sample peak is under 1.0, the true peak
        still made -1.10 dBTP, the integrated loudness still made -14 LUFS, and
        one frame in 2,978 cannot move any of them. Its `silent_1s_windows` test
        asks whether a window is TOO QUIET; nothing asked whether the opening was
        too LOUD for what surrounds it.

    TWO INDEPENDENT STATISTICS, both of which must pass, at BOTH edges.

    1. `crest_db` -- the peak inside the edge frame, referenced to the RMS of the
       adjacent `ref_s` of programme, judged against THE FILM'S OWN interior
       frames. The film is its own control: the same number is computed for all
       2,976 interior frames and the edge must not exceed their 99.9th percentile
       by more than `headroom_db`. This is `seam_gate`'s idiom -- a local
       reference, because the film's own loudest transient is the breach and a
       global threshold would call the breach a defect.

    2. `onset_step_db` -- |x[0]| for the head and |x[-1]| for the tail, against
       the same adjacent RMS. Outside the file is digital silence, so these two
       samples ARE the step across the film's outer boundary. A master that is
       topped and tailed cannot begin louder than the second it begins with, so
       the threshold is 0 dB + `headroom_db`. This statistic shares no arithmetic
       with the first and catches the same defect independently.

    THE THRESHOLDS ARE NOT TUNED TO THE TWO MASTERS. Measured:

        statistic 1   pre-fix frame 1  +31.62 dB   interior p99.9  +19.27 dB
                      post-fix frame 1  +8.53 dB   interior p99.9  +18.11 dB
        statistic 2   pre-fix          +23.45 dB   post-fix        -12.28 dB

    Any headroom between 0 and +12.3 dB gives the same verdict on statistic 1,
    and anything between -12.3 and +23.4 dB gives the same verdict on statistic
    2. The chosen values sit in the middle of gaps of 22 dB and 36 dB. The gate
    is not measuring a fine distinction; it is measuring the difference between
    programme and a splice.

    Every number above is what `tools/audio_edge_gate.py` prints for those two
    files; they are quoted here so the docstring can be checked against the tool
    rather than believed. R2-953 and R2-954 both shipped correct fixes with wrong
    numbers in the prose, and that is a cheap mistake to keep making.

    SCOPE: THIS GATES MASTERS, AND IT IS USEFUL ON CUTS FOR A DIFFERENT REASON.
    Run on an extract, statistic 2 reports the EXTRACT's in-point, not the film's.
    That is not a false positive, it is a second job worth having: the ending
    extracts cut for the human listening pass were hard cuts at their in-point,
    because they were extracted without a fade. A listener would hear that as a
    click on the clip's first frame and could easily charge it to the film. The
    copies in `watch/audio/` are faded 5 ms and score -212 dB or better. A gate
    that stops the listening pass from manufacturing the very artefact it is
    convened to look for is earning its place twice.

    THE NUMBERS THAT USED TO BE IN THIS PARAGRAPH DID NOT REPRODUCE (R2-2225).
    It cited `audio/out/ab/ending_A_nolapdown.wav` and `ending_B_lapdown.wav` at
    "a hard cut at 0.542 with a +9.67 dB step". Those files still exist, under
    `audio/out/ab/brake/`, orphaned since 7 Aug 10:50 and read by no code path;
    re-measured now they open at 0.258 / +5.08 dB and 0.259 / +5.13 dB. The
    defect was real and is fixed -- the point of the paragraph stands -- but
    quoting a specific number for a file nothing writes is exactly the "numbers
    in the prose" failure the paragraph above this one warns about, committed by
    the docstring that warns about it. Live tools name live files.

    WHAT THIS CANNOT PROVE. Statistic 2 asserts the master is topped and tailed,
    which is true of this film by construction -- it opens on a silent showroom
    and ends on a stopped car -- but a film that legitimately hard-cut to loud
    material on frame 1 would fail it, correctly for a master and incorrectly for
    a reel. Statistic 1 carries no such assumption. Neither statistic can see a
    defect that is quieter than the film's own transients; for that, listen --
    which is R2-1090, and is why `watch/` exists.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    n = x.shape[0]
    spf = int(round(sr / FPS))
    mono = x.mean(axis=1)
    absmax = np.abs(x).max(axis=1)
    nf = n // spf
    pk = absmax[:nf * spf].reshape(nf, spf).max(axis=1)

    # THE FILM IS ITS OWN REFERENCE, SO IT MUST HAVE ENOUGH OF ITSELF TO BE ONE.
    # Below a handful of frames there are no interior frames to take a percentile
    # over and the statistic is undefined. It fails LOUDLY rather than raising or,
    # worse, passing: a gate that cannot judge must not report that it did. The
    # master is 2,978 frames and the shortest clip in watch/ is 54, so this is a
    # guard against a wrong file being handed to the tool, not a real limit.
    MIN_FRAMES = 8
    if nf < MIN_FRAMES:
        return {
            "label": label, "frames": int(nf), "APPLICABLE": False, "PASS": False,
            "reason": (f"{nf} frames is too short to be its own reference; "
                       f"edge_gate needs at least {MIN_FRAMES}"),
        }

    crest = _frame_crest_profile(mono, pk, sr, spf, ref_s)
    interior = crest[1:-1]
    p999 = float(np.percentile(interior, 99.9))
    limit = p999 + headroom_db

    ref = int(ref_s * sr)
    head_rms = float(np.sqrt(max((mono[spf:spf + ref] ** 2).mean(), 1e-24)))
    tail_rms = float(np.sqrt(max((mono[-spf - ref:-spf] ** 2).mean(), 1e-24)))
    step_head = 20.0 * np.log10(max(float(absmax[0]), 1e-12) / max(head_rms, 1e-12))
    step_tail = 20.0 * np.log10(max(float(absmax[-1]), 1e-12) / max(tail_rms, 1e-12))

    edges = {
        "first": {
            "frame": 1, "crest_db": float(crest[0]),
            "peak": float(pk[0]),
            "peak_at_sample": int(absmax[:spf].argmax()),
            "peak_at_ms": float(absmax[:spf].argmax() / sr * 1000.0),
            "ref_rms": head_rms,
            "boundary_sample_abs": float(absmax[0]),
            "onset_step_db": float(step_head),
            "PASS_crest": bool(crest[0] <= limit),
            "PASS_step": bool(step_head <= headroom_db),
        },
        "last": {
            "frame": int(nf), "crest_db": float(crest[-1]),
            "peak": float(pk[-1]),
            "peak_at_sample": int(n - spf + absmax[-spf:].argmax()),
            "peak_at_ms": float(absmax[-spf:].argmax() / sr * 1000.0),
            "ref_rms": tail_rms,
            "boundary_sample_abs": float(absmax[-1]),
            "onset_step_db": float(step_tail),
            "PASS_crest": bool(crest[-1] <= limit),
            "PASS_step": bool(step_tail <= headroom_db),
        },
    }
    ok = all(e["PASS_crest"] and e["PASS_step"] for e in edges.values())
    return {
        "label": label, "APPLICABLE": True,
        "statistic": ("edge-frame peak vs adjacent-1s RMS, against the film's own "
                      "interior p99.9 + headroom; and the outer boundary sample "
                      "vs the same RMS"),
        "frames": int(nf),
        "interior_crest_p99_9_db": p999,
        "interior_crest_max_db": float(interior.max()),
        "interior_crest_max_frame": int(interior.argmax()) + 2,
        "interior_crest_median_db": float(np.median(interior)),
        "crest_limit_db": float(limit),
        "step_limit_db": float(headroom_db),
        "headroom_db": float(headroom_db),
        "edges": edges,
        "PASS": bool(ok),
    }


def control_edge(x, sr):
    """Artefacts that are bad at the film's EDGES, in the ways the edges go bad.

    WHAT THE FIRST TWO CONTROLS MUST INJECT, AND WHY IT IS NOT `np.roll(master)`.
    The obvious control -- circularly roll the finished master by the same
    0.0113 s the showroom decorrelation used -- DOES NOT FAIL THIS GATE, and that
    is correct, not a hole. R2-960's roll was applied to an INTERMEDIATE buffer,
    the showroom's 2.4 s reverb tail, whose last samples are the decay of a car
    at 323 km/h. The FINISHED film ends on a car that has stopped: its last
    11.3 ms peak 0.111, so wrapping them onto the head raises frame 1 to +15.0 dB
    crest, under the +21.1 dB limit. Measured, not assumed.

    The defect is therefore not "a wrap" but "LOUD MATERIAL ARRIVING AT A QUIET
    EDGE", and a faithful control has to inject what actually wrapped. These take
    the film's own loudest 11.3 ms -- the nearest thing the master contains to the
    tail of a 323 km/h car -- and place it at each edge through the SAME 0.35 mix
    coefficient `master.py` applied to the delayed tail. No gain is tuned to hit
    a target number.

    Validated against the real thing as well as the constructed one:
    `audio/out/ab/master_SHIPPED_aug2.wav`, the actual pre-fix artefact, scores
    +31.62 dB crest and a +23.45 dB onset step and FAILS.
    """
    d = int(0.0113 * sr)
    mono = np.abs(np.asarray(x, dtype=np.float64)).max(axis=1)
    # the loudest 11.3 ms the film contains, by windowed energy
    k = np.convolve(mono ** 2, np.ones(d), mode="valid")
    j = int(k.argmax())
    loud = np.asarray(x, dtype=np.float64)[j:j + d] * 0.35   # master.py's own coefficient

    y = np.asarray(x, dtype=np.float64).copy()
    y[:d] += loud
    a = edge_gate(y, sr, "CONTROL: R2-960's signature -- the film's loudest 11.3 ms "
                         "arriving on frame 1 through the mix's own 0.35 coefficient")

    z = np.asarray(x, dtype=np.float64).copy()
    z[-d:] += loud
    b = edge_gate(z, sr, "CONTROL: the same energy arriving on the LAST 11.3 ms "
                         "(proves the gate looks at BOTH edges)")

    w = np.asarray(x, dtype=np.float64).copy()
    w[0] = 0.33204                                     # the pre-fix first sample, measured
    c = edge_gate(w, sr, "CONTROL: a single -9.6 dBFS sample at index 0, the step the "
                         "shipped master actually opened with")

    v = np.asarray(x, dtype=np.float64).copy()         # a quiet edge tick: the limit
    v[0] = 10.0 ** (-40.0 / 20.0)
    d4 = edge_gate(v, sr, "CONTROL: a -40 dBFS sample at index 0 (below the gate's "
                          "sensitivity, stated)")

    # THIS CONTROL FLIPPED, AND THE GATE IS NOT WHAT CHANGED (R2-2007).
    #
    # It used to be a stated negative: "rolling the finished master does NOT fail,
    # because this film ends quiet." That was measured, and it was true of the
    # master it was measured on -- `master_R2-1400_REJECTED_hairblower.wav` still
    # scores +15.00 dB crest and a -1.57 dB step here, exactly the numbers the old
    # docstring quoted, and still passes.
    #
    # What changed is the FILM. R2-954 replaced the ending's motored coast with a
    # running idle, and an idling engine is both louder and impulsive where a
    # dying coast was neither. The premise "this film ends quiet" is simply no
    # longer a fact about this film, so wrapping its last 11.3 ms onto frame 1
    # now really does put audible material on the first frame -- which is the
    # defect this gate exists to catch. Failing it is the gate WORKING.
    #
    # Measured across every master on disk, onset step of the rolled copy:
    #     master_SHIPPED_aug2                 -6.63 dB   (fails on crest instead)
    #     master_R2-1400_REJECTED_hairblower  -1.57 dB   PASS  <- the old premise
    #     master_B_lapdown (rejected #2)      +5.63 dB   FAIL  <- already flipped
    #     current master                      +3.96 dB   FAIL
    # It had ALREADY flipped on the master the client was given, and nobody saw
    # it because the suite never reached its own aggregation (R2-2006).
    #
    # So this is now a MUST-FAIL, and it is content-dependent by nature: if the
    # ending is ever made quiet again, this control will start passing and should
    # be re-stated rather than forced.
    e = edge_gate(np.roll(np.asarray(x, dtype=np.float64), d, axis=0), sr,
                  "CONTROL: circularly rolling the FINISHED master wraps its own "
                  "ending onto frame 1. Since R2-954 this film ends on a running "
                  "idle rather than a motored coast, so that IS audible material "
                  "on frame 1 and it MUST fail")
    return a, b, c, d4, e


def ffmpeg_ebur128(path):
    """Independent second opinion on loudness and true peak."""
    try:
        p = subprocess.run(
            ["ffmpeg", "-nostats", "-hide_banner", "-i", path,
             "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
            capture_output=True, text=True, timeout=600)
    except Exception as e:                                    # noqa: BLE001
        return {"error": str(e)}
    txt = p.stderr
    out = {}
    for key, pat in (("integrated_lufs", r"I:\s*(-?\d+\.\d+) LUFS"),
                     ("loudness_range_lu", r"LRA:\s*(-?\d+\.\d+) LU"),
                     ("true_peak_dbfs", r"Peak:\s*(-?\d+\.\d+) dBFS")):
        m = re.findall(pat, txt)
        if m:
            out[key] = float(m[-1])
    return out


# ============================================================ external check ==
# Reads that would bring a recorded sound into the render, by DOTTED CALL NAME
# rather than by regex. An AST walk cannot be fooled by a comment, cannot fire
# on a docstring that mentions the thing it is looking for, and cannot miss a
# call because it was spelled with different whitespace. The first version of
# this check was a regex list and it flagged eleven lines, of which ELEVEN were
# its own pattern table and its own docstring.
FORBIDDEN_CALLS = {
    "sf.read", "soundfile.read", "sf.blocks", "soundfile.blocks",
    "wavfile.read", "scipy.io.wavfile.read", "librosa.load", "librosa.core.load",
    "wave.open", "aifc.open", "sunau.open", "audioread.audio_open",
    "AudioSegment.from_file", "AudioSegment.from_wav", "AudioSegment.from_mp3",
    "torchaudio.load", "torchaudio.info", "ffmpeg.input",
    "urllib.request.urlopen", "urlopen", "requests.get", "requests.post",
    "hf_hub_download", "snapshot_download",
}
FORBIDDEN_IMPORTS = {"librosa", "pydub", "audioread", "torchaudio",
                     "urllib", "requests", "huggingface_hub", "datasets"}
AUDIO_EXT = (".wav", ".aif", ".aiff", ".flac", ".mp3", ".ogg", ".m4a", ".opus",
             ".sf2", ".sfz")

# The one permitted read in the package, stated rather than hidden: verify.py
# opens the FINISHED MASTER to measure it. It contributes nothing to the render.
ALLOW = {("verify.py", "sf.read")}

# THE ONLY THIRD-PARTY LIBRARIES THIS PACKAGE MAY IMPORT, BY NAME.
# Code libraries only. Every one of them is an ALGORITHM: pyroomacoustics
# generates an impulse response from room dimensions, pyloudnorm implements
# ITU-R BS.1770-4, parselmouth is a dev-only cross-check of the in-repo Boersma
# HNR and is deliberately NOT in requirements.txt because it is GPL-3 and must
# not enter the shipped package. NONE OF THEM SHIPS CONTENT. The ban on
# recorded material is absolute and it is on CONTENT, not on code.
ALLOWED_THIRD_PARTY = {"pyroomacoustics", "pyloudnorm", "parselmouth"}
DEV_ONLY_THIRD_PARTY = {"parselmouth"}          # GPL-3: tools/ only, never audio/
STDLIB_AND_CORE_OK = {"numpy", "scipy", "soundfile", "matplotlib", "json", "os",
                      "sys", "math", "ast", "argparse", "dataclasses",
                      "subprocess", "hashlib", "time", "collections",
                      "itertools", "functools", "warnings", "typing", "re",
                      "__future__", "audio", "tools"}


def _dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def scan_external(paths, render_only=False):
    """AST scan for anything that could read a recorded sound.

    `render_only` restricts the scan to the modules that actually build the
    master, i.e. everything except this file.
    """
    hits = []
    files = []
    for path in paths:
        if os.path.isdir(path):
            for root, _d, fs in os.walk(path):
                files += [os.path.join(root, f) for f in fs if f.endswith(".py")]
        elif path.endswith(".py"):
            files.append(path)
    for fp in sorted(files):
        base = os.path.basename(fp)
        if render_only and base == "verify.py":
            continue
        # DECLARED EXCEPTION, CHECKED RATHER THAN ASSERTED: `audio/controls/`
        # is the permanent control corpus. It reads the DELIVERED MASTER, on
        # purpose -- C4 is "the rejected master, retained permanently" and C1
        # and C7 are built from it -- and it contributes nothing to the render.
        # `percept.g_construct` fails if any render-path module ever imports it,
        # and `main` re-checks the same thing here, so "not on the render path"
        # cannot quietly stop being true.
        if os.path.basename(os.path.dirname(fp)) == "controls":
            continue
        src = open(fp, encoding="utf-8", errors="ignore").read()
        try:
            tree = ast.parse(src)
        except SyntaxError as e:                       # noqa: PERF203
            hits.append({"file": fp, "line": 0, "what": f"unparseable: {e}"})
            continue
        docstrings = set()
        for nd in ast.walk(tree):
            if isinstance(nd, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                               ast.ClassDef)):
                d = ast.get_docstring(nd, clean=False)
                if d is not None and nd.body and isinstance(nd.body[0], ast.Expr):
                    docstrings.add(id(nd.body[0].value))
        for nd in ast.walk(tree):
            if isinstance(nd, ast.Call):
                name = _dotted(nd.func)
                if name in FORBIDDEN_CALLS and (base, name) not in ALLOW:
                    hits.append({"file": fp, "line": nd.lineno, "what": f"call {name}()"})
            elif isinstance(nd, ast.Import):
                for al in nd.names:
                    if al.name.split(".")[0] in FORBIDDEN_IMPORTS:
                        hits.append({"file": fp, "line": nd.lineno,
                                     "what": f"import {al.name}"})
            elif isinstance(nd, ast.ImportFrom):
                if (nd.module or "").split(".")[0] in FORBIDDEN_IMPORTS:
                    hits.append({"file": fp, "line": nd.lineno,
                                 "what": f"from {nd.module} import"})
            elif isinstance(nd, ast.Constant) and isinstance(nd.value, str):
                if id(nd) in docstrings:
                    continue
                v = nd.value.lower()
                if v.endswith(AUDIO_EXT) and base not in ("master.py", "verify.py"):
                    hits.append({"file": fp, "line": nd.lineno,
                                 "what": f"audio-file literal {nd.value!r}"})
        # NO AUDIO FILE MAY BE OPENED FOR READING ANYWHERE IN THIS PACKAGE.
        # `sf.read` is already forbidden by name; this closes the plain
        # `open(path, "rb")` route, which the call list could not see because
        # `open` is legitimate for JSON and for logs.
        for nd in ast.walk(tree):
            if not (isinstance(nd, ast.Call) and _dotted(nd.func) == "open"):
                continue
            arg = nd.args[0] if nd.args else None
            mode = nd.args[1].value if (len(nd.args) > 1
                                        and isinstance(nd.args[1], ast.Constant)
                                        and isinstance(nd.args[1].value, str)) else "r"
            for kw in nd.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            looks_audio = (isinstance(arg, ast.Constant)
                           and isinstance(arg.value, str)
                           and arg.value.lower().endswith(AUDIO_EXT))
            if looks_audio and "w" not in mode and "a" not in mode:
                hits.append({"file": fp, "line": nd.lineno,
                             "what": f"open({arg.value!r}, {mode!r}) -- an audio "
                                     f"file opened for READING"})
        # THE GPL FENCE. parselmouth is GPL-3 and is a dev-only cross-check; if
        # it ever appears under audio/ the shipped package inherits GPL-3.
        if os.path.basename(os.path.dirname(fp)) == "audio" or "audio/" in fp:
            for nd in ast.walk(tree):
                mods = []
                if isinstance(nd, ast.Import):
                    mods = [al.name.split(".")[0] for al in nd.names]
                elif isinstance(nd, ast.ImportFrom):
                    mods = [(nd.module or "").split(".")[0]]
                for m in mods:
                    if m in DEV_ONLY_THIRD_PARTY:
                        hits.append({"file": fp, "line": nd.lineno,
                                     "what": f"GPL-3 dev-only dependency {m!r} "
                                             f"imported inside the shipped package"})
    return hits


# ============================================================ positive tests ==
def control_external(tmpdir):
    """Three artefacts that are bad in three different ways, all must be caught."""
    cases = {
        "sf_read": "import soundfile as _s\nx, r = _s.read('engine_loop.wav')\n",
        "librosa": "import librosa\ny, sr = librosa.load('v6.flac')\n",
        "download": "import requests\nrequests.get('http://x/y.wav')\n",
    }
    res = {}
    for name, src in cases.items():
        bad = os.path.join(tmpdir, f"_control_{name}.py")
        with open(bad, "w") as fh:
            fh.write(src)
        res[name] = len(scan_external([bad]))
        os.remove(bad)
    return {"control_hits_per_case": res,
            "CONTROL_FAILS_AS_EXPECTED": all(v > 0 for v in res.values())}


def control_seam(x, sr, sheet):
    """Three artefacts that are bad in three different ways at a beat boundary."""
    f = int(round(sheet["beats"][3]["start_s"] * FPS)) + 1
    i = int((f - 1) / FPS * sr)

    y = x.copy()
    y[i:] = np.roll(y[i:], 977, axis=0)                # a hard splice
    a = seam_gate(y, sr, sheet, "CONTROL: 977-sample splice at beat 4")

    z = x.copy()
    z[i:] *= 10.0 ** (3.0 / 20.0)                      # a 3 dB level step
    b = seam_gate(z, sr, sheet, "CONTROL: 3 dB level step at beat 4")

    v = x.copy()
    v[i:] *= 10.0 ** (0.5 / 20.0)                      # a 0.5 dB step: the limit
    d = seam_gate(v, sr, sheet, "CONTROL: 0.5 dB level step at beat 4 "
                                "(below the gate's sensitivity, stated)")

    w = x.copy()                                       # a 40 ms crossfade
    L = int(0.040 * sr)
    ramp = np.linspace(0.0, 1.0, L)[:, None]
    other = np.roll(x, 191111, axis=0)
    w[i:i + L] = w[i:i + L] * (1.0 - ramp) + other[i:i + L] * ramp
    w[i + L:] = other[i + L:]
    c = seam_gate(w, sr, sheet, "CONTROL: 40 ms crossfade to elsewhere at beat 4")
    return a, b, c, d


def control_kerb(spec):
    """A position track that deliberately runs 8 m wide must classify as kerb.

    Proves the kerb layer is not dead code that would stay silent whatever the
    car did -- which is what "it never triggers on this telemetry" would
    otherwise be indistinguishable from.
    """
    sys.path.insert(0, os.path.join(ROOT, "anim"))
    import carpath
    from .scene import classify, half_width_at
    tab = np.array(carpath.centreline_table(spec, 1.0))
    S, CX, CY, CZ, H = tab.T
    m = (S > 500.0) & (S < 700.0)
    s = S[m]
    hw = half_width_at(spec, s)
    off = hw + 0.75                                    # mid-kerb
    pos = np.stack([CX[m] - off * np.sin(H[m]), CY[m] + off * np.cos(H[m]), CZ[m]], axis=1)
    f = classify(spec, pos, s, off, 20.0)
    return {"kerb_fraction_on_control_track": float((f["kerb"] > 0.5).mean()),
            "CONTROL_TRIGGERS_AS_EXPECTED": bool((f["kerb"] > 0.5).mean() > 0.8)}


# ============================ WHAT USED TO BE HERE, AND WHY IT IS GONE ========
# DELETED, 629 lines: `hnr_profile`, `harmonic_gate`, `control_harmonic`,
# `_hairdryer_like`, the whole `BEAT_HNR_LIMITS` table and every HNR_* constant,
# plus `pipe_modes`, `waveguide_gate`, `control_waveguide` and the WAVEGUIDE_*
# constants. Per docs/audio-rebuild3/SPEC-ENGINE-AND-GATES.md section 2 these
# were REPLACED, not recalibrated, and the reasons are numbers rather than
# opinions:
#
#   `harmonic` / `hnr_profile`. Its own docstring said it worked "with NO f0
#   estimate": it subtracted a 269.5 Hz running median and called whatever poked
#   above it tonal. It never checked that the peaks fell on integer multiples of
#   anything, and noise through any resonator makes peaks. Measured: a literal
#   wind blower pointed into a rack of inharmonic tubes PASSED beat 1's limit
#   with MORE margin than the delivered master (fraction-below 0.481 against the
#   master's 0.708, limit 0.85), and at Q = 80 it scored +4.04 dB -- above this
#   gate's own 2.0 dB ENGINE bar. The only signal it could fail was flat white
#   noise, which is precisely the single adversary its thresholds were tuned
#   against. And it is a per-window statistic aggregated by a fraction, so it is
#   mathematically invariant to repetition: it scored a 2 s block tiled 63x at
#   +43.8 dB, 5.4x the delivered film's best beat.
#
#   `BEAT_HNR_LIMITS`. Beat 1's bar was HNR_NOISE_FLOOR_DB = -1.0 dB, which this
#   file's own comment defined as "one decibel above what this metric reads on
#   something with no line spectrum at all", with 0.85 of windows permitted
#   below even that. 76.5 % of the film (94.9 s of 124.1 s) was held to that
#   noise floor or explicitly excused from the engine bar. Worse, the rule that
#   produced every number in the table -- "the limit is the midpoint between
#   what THIS master reads and what the adversary reads" -- derives the pass
#   mark from the artefact under test, so a film can only fail by being worse
#   than the film the limits were calibrated on. That rule is now BANNED IN
#   WRITING: `audio/percept.py` requires every threshold to carry a
#   machine-checked `source` in {physics, published, control-derived}, and
#   `audit_thresholds()` rejects `source=artefact` by name.
#
#   `waveguide`. An algebraic root-solve of engine.py's constants at a
#   hand-picked WAVEGUIDE_RPM = 11000, passing at median 4.852 against a limit
#   of 5.0 -- a 3.0 % margin -- while the same gate FAILS at the film's own
#   rpm_at_vmax of 13,143 (5.798). It never opened the wav, and it inspected
#   only the three exhaust elements, so it could not see layers.assembly's 616
#   inharmonic impacts or the showroom FDN, which is where the tube ringing
#   actually was.
#
# THE REPLACEMENTS ARE IN `audio/percept.py`, and they are three instruments
# where there was one number, because collapsing them was the original mistake:
#   G-FLAT   tilt-free per-band spectral flatness against white
#   G-HNR    calibrated Boersma autocorrelation HNR, re-validated every run
#   G-ORDER  comb tracking against TELEMETRY rpm, not against the audio
#   G-RING   ring-through and modal decay on the RENDERED STEREO WAV, over all
#            layers and the whole film, against the declared room's Sabine RT60
# and the six with no predecessor at all: G-NOVEL, G-MOD, G-GESTURE, G-ROOM,
# G-BALANCE, G-CONSTRUCT. `tools/percept_matrix.py` runs the permanent control
# corpus FIRST and refuses to adjudicate any master if a control returns the
# wrong verdict.
#
# WHAT THIS FILE IS NOW: the things it was genuinely good at -- loudness, true
# peak, the two frames no other gate visits, splice detection, the provenance
# scan, and the Doppler solve, which was the only load-bearing gate in the old
# suite. It no longer claims to judge whether the film sounds like an engine.

# ================================================================== plots =====
def spectrogram_png(x, sr, path, title, nfft=4096, fmax=20000, beats=None,
                    marks=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    mono = x.mean(axis=1) if x.ndim > 1 else x
    f, t, S = _sig.spectrogram(mono, fs=sr, nperseg=nfft, noverlap=nfft * 3 // 4,
                               window="hann", scaling="spectrum", mode="magnitude")
    db = 20.0 * np.log10(np.maximum(S, 1e-10))
    fig, ax = plt.subplots(2, 1, figsize=(22, 11), height_ratios=[3, 1],
                           constrained_layout=True)
    m = f <= fmax
    im = ax[0].pcolormesh(t, f[m], db[m], shading="auto", cmap="magma",
                          vmin=db[m].max() - 96, vmax=db[m].max())
    ax[0].set_yscale("symlog", linthresh=200.0)
    ax[0].set_ylabel("Hz")
    ax[0].set_title(title)
    fig.colorbar(im, ax=ax[0], label="dB")
    if beats:
        for b in beats:
            ax[0].axvline(b["start_s"], color="cyan", lw=0.9, alpha=0.8)
            ax[0].text(b["start_s"] + 0.4, fmax * 0.55, b["name"], color="cyan",
                       fontsize=8, rotation=90, va="top")
    for mk in (marks or []):
        ax[0].axvline(mk[0], color="lime", lw=1.1, ls="--", alpha=0.9)
        ax[0].text(mk[0] + 0.3, 30, mk[1], color="lime", fontsize=8, rotation=90)
    tt = np.arange(mono.shape[0]) / sr
    step = max(mono.shape[0] // 400000, 1)
    ax[1].plot(tt[::step], (x[::step, 0] if x.ndim > 1 else mono[::step]), lw=0.3, color="#4488ff")
    if x.ndim > 1:
        ax[1].plot(tt[::step], -np.abs(x[::step, 1]), lw=0.3, color="#ff8844")
    ax[1].set_xlim(0, tt[-1]); ax[1].set_ylim(-1.05, 1.05)
    ax[1].axhline(1.0, color="r", lw=0.5); ax[1].axhline(-1.0, color="r", lw=0.5)
    ax[1].set_xlabel("film time (s)"); ax[1].set_ylabel("L / -|R|")
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def plot_pitch(t, f_meas, f_pred, path, title, xlabel="film time (s)"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(16, 6), constrained_layout=True)
    ax.plot(t, f_pred, color="#22aa44", lw=1.6, label="predicted")
    ax.plot(t, f_meas, ".", color="#cc3355", ms=3, label="measured from the audio")
    ax.set_xlabel(xlabel); ax.set_ylabel("exhaust f0 (Hz)"); ax.set_title(title)
    ax.legend(); ax.grid(alpha=0.25)
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


# =================================================================== main =====
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav", default=os.path.join(ROOT, "audio", "out", "master.wav"))
    ap.add_argument("--report", default=os.path.join(ROOT, "audio", "out", "master_report.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "audio", "out"))
    ap.add_argument("--sr-engine", type=int, default=48000,
                    help="sample rate for the dry-engine re-synthesis used by the pitch gate")
    ap.add_argument("--skip-plots", action="store_true")
    a = ap.parse_args()

    os.makedirs(a.out, exist_ok=True)
    spec = json.load(open(os.path.join(ROOT, "docs", "circuit_spec.json")))
    sheet = json.load(open(os.path.join(ROOT, "docs", "beat_sheet.json")))
    x, sr = sf.read(a.wav, always_2d=True)               # the ARTEFACT under test
    V = {"wav": a.wav, "sr": sr, "samples": int(x.shape[0]),
         "duration_s": x.shape[0] / sr,
         "frames_at_24fps": x.shape[0] / sr * FPS}
    print(f">> {a.wav}: {x.shape[0]} samples, {x.shape[0]/sr:.4f} s, "
          f"{x.shape[0]/sr*FPS:.2f} frames")

    # ---------------------------------------------------------------- levels --
    V["levels"] = level_gate(x, sr)
    V["levels_ffmpeg_ebur128"] = ffmpeg_ebur128(a.wav)
    print(">> levels:", json.dumps(V["levels"], indent=1))
    print(">> ffmpeg:", V["levels_ffmpeg_ebur128"])

    # ------------------------------------------------------------------ edges --
    # THE TWO FRAMES NO OTHER GATE VISITS. The seam gate walks beat boundaries;
    # frame 1 and frame 2978 are edges, not boundaries. See `edge_gate`.
    V["edges"] = edge_gate(x, sr, "master")
    ectl = control_edge(x, sr)
    V["edge_controls"] = list(ectl)
    # the first three controls MUST fail; the fourth states the sensitivity limit.
    V["edges"]["CONTROLS_FAIL_AS_EXPECTED"] = bool(
        (not ectl[0]["PASS"]) and (not ectl[1]["PASS"]) and (not ectl[2]["PASS"]))
    _ef, _el = V["edges"]["edges"]["first"], V["edges"]["edges"]["last"]
    print(f">> edges: frame 1 crest {_ef['crest_db']:+.2f} dB step "
          f"{_ef['onset_step_db']:+.2f} dB | last frame crest {_el['crest_db']:+.2f} dB "
          f"step {_el['onset_step_db']:+.2f} dB | limits crest "
          f"{V['edges']['crest_limit_db']:+.2f} step {V['edges']['step_limit_db']:+.2f} "
          f"PASS={V['edges']['PASS']}")
    for c in ectl:
        print(f"   control {c['label'][:60]}: PASS={c['PASS']}")

    # ------------------------------------------------------------------ seam --
    V["seam"] = seam_gate(x, sr, sheet, "master")
    V["seam"]["CLASS"] = "advisory"
    V["seam"]["ADVISORY_NOTE"] = (
        "A PASS here proves almost nothing and that is measured, not modest: "
        "this gate adjudicates 20 samples of 5,956,000 (0.0003 % of the film) "
        "and its own 3 dB-step positive control PASSES on broadband material. "
        "`swap_b1_loop.wav`, whose beat 1 is a 2 s block tiled 16.5 times, "
        "reported a seam percentile BIT-IDENTICAL to the delivered master's, "
        "because every one of its sixteen splices is inside a beat. A FAIL is "
        "still informative and still stops the build; a PASS is advisory. "
        "`splice_film_wide` below is the coverage fix.")
    V["splice_film_wide"] = splice_scan(x, sr)
    # POSITIVE CONTROL for the film-wide scan, inside a beat where the boundary
    # gate cannot look: a 977-sample splice at 20 s, i.e. mid-beat-1.
    _y = x.copy()
    _i = int(20.0 * sr)
    _y[_i:] = np.roll(_y[_i:], 977, axis=0)
    _mono_o = x.mean(axis=1) if x.ndim > 1 else x
    _mono_s = _y.mean(axis=1) if _y.ndim > 1 else _y
    _base = _d3_score_at(_mono_o, sr, 20.0)
    _ctlv = _d3_score_at(_mono_s, sr, 20.0)
    V["splice_film_wide"]["CONTROL_mid_beat_splice_at_20s"] = {
        "score_before_splice": _base, "score_after_splice": _ctlv,
        "lift": float(_ctlv / _base) if _base and _base == _base else None,
        "required_lift": 5.0,
        "note": ("the boundary gate cannot see this splice at all -- it is "
                 "13 s from the nearest beat boundary. This is the gate's own "
                 "sensitivity, measured by injection, and it is what is gated "
                 "-- not a number chosen by hand.")}
    V["splice_film_wide"]["PASS"] = bool(
        _base == _base and _ctlv == _ctlv and _ctlv >= 5.0 * _base)
    del _y, _mono_s
    print(f">> splice scan (film-wide): {V['splice_film_wide']['windows_scanned']} "
          f"windows, 100 % coverage; worst candidate "
          f"{V['splice_film_wide']['worst_score']:.0f}x local median at "
          f"{V['splice_film_wide']['candidates'][0]['t_s']:.2f} s | SENSITIVITY "
          f"control: a mid-beat splice lifts its own location from {_base:.1f}x "
          f"to {_ctlv:.1f}x, PASS={V['splice_film_wide']['PASS']}")
    ctl = control_seam(x, sr, sheet)
    V["seam_controls"] = list(ctl)
    # the first two controls (splice, 3 dB step) MUST fail; the 0.5 dB step and
    # the crossfade are reported to state the gate's sensitivity limit honestly.
    V["seam"]["CONTROLS_FAIL_AS_EXPECTED"] = bool(
        (not ctl[0]["PASS"]) and (not ctl[1]["PASS"]))
    print(f">> seam: worst d3 local percentile "
          f"{V['seam']['worst_d3_local_percentile']:.3f} PASS={V['seam']['PASS']}")
    for c in ctl:
        print(f"   control {c['label']}: d3 p{c['worst_d3_local_percentile']:.3f} "
              f"PASS={c['PASS']}")

    # -------------------------------------------------------- external assets --
    hits_render = scan_external([PKG], render_only=True)
    hits_all = scan_external([PKG], render_only=False)
    V["external_assets"] = {
        "render_path_hits": hits_render, "whole_package_hits": hits_all,
        "scanned": sorted(os.path.basename(f) for f in os.listdir(PKG)
                          if f.endswith(".py")),
        "declared_exception": ("verify.py calls sf.read once, on the FINISHED "
                               "MASTER, to measure it. It contributes nothing to "
                               "the render; `render_path_hits` excludes verify.py "
                               "and must be empty."),
        "CLASS": "provenance",
        "PROVENANCE_NOTE": (
            "This gate never opens the wav. It is an AST scan of the source "
            "tree, so it cannot distinguish any two audio files and it passed "
            "100 % white noise. It is excluded from the quality verdict -- not "
            "because it is unimportant, but because it answers a different "
            "question."),
        "controls_exclusion": {
            "path": "audio/controls/",
            "why": ("the permanent control corpus; it reads the delivered "
                    "master because C4 IS the delivered master and C1/C7 are "
                    "built from it, and it is not on the render path"),
            "render_path_imports_it": sorted(
                os.path.basename(f) for f in os.listdir(PKG)
                if f.endswith(".py") and f not in ("verify.py", "percept.py")
                and ("from .controls" in open(os.path.join(PKG, f),
                                              encoding="utf-8",
                                              errors="ignore").read()
                     or "import controls" in open(os.path.join(PKG, f),
                                                  encoding="utf-8",
                                                  errors="ignore").read()))},
        "allowed_third_party": sorted(ALLOWED_THIRD_PARTY),
        "dev_only_third_party": sorted(DEV_ONLY_THIRD_PARTY),
        "PASS": len(hits_render) == 0 and len(hits_all) == 0}
    V["external_assets"].update(control_external(a.out))
    if V["external_assets"]["controls_exclusion"]["render_path_imports_it"]:
        V["external_assets"]["PASS"] = False
        V["external_assets"]["EXCLUSION_NO_LONGER_TRUE"] = True
    # the advisory/quality/provenance split needs seam's own splice coverage in
    # the same place the seam gate is judged
    V["seam"]["film_wide_PASS"] = V["splice_film_wide"]["PASS"]
    print(f">> external assets: {len(hits_render)} render-path hits, "
          f"{len(hits_all)} package hits; controls "
          f"{V['external_assets']['control_hits_per_case']}")

    # ------------------------------------------------------------- bandsplit --
    tst = dsp.pink(sr * 2, 5, sr)
    err = float(np.abs(sum(dsp.split_bands(tst, sr)) - tst).max())
    V["bandsplit_reconstruction_max_abs_err"] = err
    V["bandsplit_PASS"] = bool(err < 1e-5)

    # -------------------------------------------------------------- controls --
    V["kerb_classifier_control"] = control_kerb(spec)
    print(">> kerb control:", V["kerb_classifier_control"])

    # ---------------------------------------------------- pitch tracks speed --
    from .clock import Clock, WorldGrid
    from .scene import Telemetry
    from . import engine as eng_mod
    se = a.sr_engine
    clock = Clock(os.path.join(ROOT, "docs", "beat_sheet.json"), sr=se)
    grid = WorldGrid(clock)
    tel = Telemetry(spec=spec)
    tw = grid.t
    st = tel.sample(tw, "v_world")
    dry, rpm, gear, einfo = eng_mod.synth(tw, st["speed"], st["accel_long"],
                                          st["slip"], st["wheel_w"], spec, se)
    # measure f0 on the dry world-clock engine, once every 0.25 s of world time
    tc = np.arange(1.0, float(tw[-1]) - 1.0, 0.25) - float(tw[0])
    f_meas, conf = track_f0(dry, se, tc)
    wt = tc + float(tw[0])
    f_pred = np.interp(wt, tw, rpm) / 60.0 * ENGINE_ORDER
    v_at = np.interp(wt, tw, st["speed"])
    thr, _brake = eng_mod.throttle_from_spec(st["speed"], st["accel_long"], spec)
    th_at = np.interp(wt, tw, thr)
    v_at = np.interp(wt, tw, st["speed"])
    ok = np.isfinite(f_meas) & (wt > 0.5) & (wt < float(tel.t_end))
    firing = ok & (th_at > 0.10)
    overrun = ok & (th_at <= 0.10)

    def _stats(mask):
        if mask.sum() < 5:
            return {}
        e = 1200.0 * np.log2(np.maximum(f_meas[mask], 1e-6)
                             / np.maximum(f_pred[mask], 1e-6))
        return {
            "n_windows": int(mask.sum()),
            "corr_measured_f0_vs_predicted_f0": float(
                np.corrcoef(f_meas[mask], f_pred[mask])[0, 1]),
            "corr_measured_f0_vs_v_world": float(
                np.corrcoef(f_meas[mask], v_at[mask])[0, 1]),
            "median_abs_error_cents": float(np.median(np.abs(e))),
            "p95_abs_error_cents": float(np.percentile(np.abs(e), 95)),
            "within_50_cents_fraction": float((np.abs(e) < 50.0).mean()),
        }

    V["pitch"] = {
        "CLASS": "provenance",
        "PROVENANCE_NOTE": (
            "RECLASSIFIED. This gate re-synthesises the dry engine from the "
            "telemetry and measures THAT, so it never takes the delivered "
            "master as an input and it passed 100 % white noise. It proves the "
            "SOURCE tracks the telemetry, which is worth proving and is kept. "
            "It does not and cannot say anything about the artefact, so it is "
            "excluded from the quality verdict. What replaces it as a quality "
            "test is G-ORDER in audio/percept.py, which tracks the firing comb "
            "ON THE DELIVERED MASTER against the same telemetry."),
        "method": ("f0 measured from the DRY world-clock engine every 0.25 s of "
                   "world time and compared with rpm/60*3, where rpm is the "
                   "gearbox solution from the telemetry's v_world. Measured on "
                   "the dry voice because 'the engine pitch tracks the telemetry' "
                   "is a claim about the SOURCE; what the ears hear is that "
                   "times the Doppler ratio, which the doppler gate tests "
                   "separately."),
        "firing": _stats(firing),
        "overrun": _stats(overrun),
        "all": _stats(ok),
        "overrun_note": ("with the injectors cut there is no combustion and "
                         "therefore no firing fundamental to find; the tracker "
                         "reports the pumping and turbo content instead. The "
                         "overrun rows are listed, not hidden, and they are NOT "
                         "part of the pass criterion."),
    }

    # CONTROL 1: the TRACKER, against a synthetic chirp whose f0 is known
    # exactly. If this fails, nothing else the tracker says means anything.
    tt = np.arange(se * 6) / se
    pch = np.cumsum(2.0 * np.pi * (200.0 + 80.0 * tt) / se)
    chirp = sum(amp * np.sin(k * pch)
                for k, amp in ((1, 1.0), (2, 0.8), (3, 0.6), (4, 0.3)))
    tcc = np.arange(0.5, 5.5, 0.25)
    fcc, _cc = track_f0(chirp, se, tcc)
    V["pitch"]["CONTROL_tracker_on_known_chirp_max_err_cents"] = float(
        np.nanmax(np.abs(1200.0 * np.log2(fcc / (200.0 + 80.0 * tcc)))))

    # CONTROL 2: the same synthesis driven by a CONSTANT speed must not track.
    dryc, _rpmc, _gc, _ic = eng_mod.synth(
        tw, np.full_like(st["speed"], 60.0), np.zeros_like(st["accel_long"]),
        np.zeros_like(st["slip"]), st["wheel_w"], spec, se)
    fmc, _c2 = track_f0(dryc, se, tc)
    okc = np.isfinite(fmc) & firing
    V["pitch"]["CONTROL_constant_speed_corr_vs_v_world"] = float(
        np.corrcoef(fmc[okc], v_at[okc])[0, 1]) if okc.sum() > 10 else 0.0
    del dryc

    fs = V["pitch"]["firing"]
    V["pitch"]["PASS"] = bool(
        fs.get("corr_measured_f0_vs_predicted_f0", 0.0) > 0.97
        and fs.get("within_50_cents_fraction", 0.0) > 0.85
        and V["pitch"]["CONTROL_tracker_on_known_chirp_max_err_cents"] < 25.0)
    V["pitch"]["CONTROL_FAILS_AS_EXPECTED"] = bool(
        abs(V["pitch"]["CONTROL_constant_speed_corr_vs_v_world"]) < 0.3)
    print(">> pitch:", json.dumps(V["pitch"], indent=1))

    if not a.skip_plots:
        plot_pitch(wt[firing], f_meas[firing], f_pred[firing],
                   os.path.join(a.out, "pitch_vs_telemetry.png"),
                   "dry engine f0 measured from the audio vs rpm/60*3 from the telemetry "
                   "(world clock)", xlabel="world time (s)")

    # ------------------------------------------------------------- doppler ----
    V["doppler"] = doppler_gate(x, sr, spec, sheet, clock, tel, a.out,
                                skip_plot=a.skip_plots)
    print(">> doppler:", json.dumps(V["doppler"], indent=1))

    # ----------------------------------------------------------- spectrograms --
    if not a.skip_plots:
        rep = json.load(open(a.report)) if os.path.exists(a.report) else {}
        marks = [(sheet["beats"][2]["start_s"], "nose at the glass")]
        V["spectrogram"] = spectrogram_png(
            x, sr, os.path.join(a.out, "master_spectrogram.png"),
            f"CIRCUIT VITRINE master -- {x.shape[0]/sr:.2f} s, {sr} Hz, "
            f"{V['levels']['integrated_lufs']:.2f} LUFS, "
            f"{V['levels']['true_peak_dbtp']:.2f} dBTP",
            beats=sheet["beats"], marks=marks)
        b3 = sheet["beats"][2]
        i0 = int((b3["start_s"] - 3.0) * sr); i1 = int((b3["start_s"] + 11.0) * sr)
        spectrogram_png(x[i0:i1], sr, os.path.join(a.out, "breach_spectrogram.png"),
                        "beat 3, the breach: world time 1.000 -> 0.1537 -> 1.000 "
                        "(film t 33.0 - 47.0 s)", nfft=2048, fmax=16000)
        i0 = int(2245 / FPS * sr) - int(4.0 * sr); i1 = int(2245 / FPS * sr) + int(6.0 * sr)
        spectrogram_png(x[i0:i1], sr, os.path.join(a.out, "doppler_spectrogram.png"),
                        "beat 5, the doppler station: camera hovering 26.26 m off the "
                        "line, car at 313.2 km/h", nfft=4096, fmax=8000)
        _ = rep

    # ================================================= THE VERDICT SPLIT ====
    # TWO STRUCTURAL RULES, from the spec's section 2. Both fix a CLASS of
    # defect rather than one gate:
    #
    # (1) Any gate that does not take the rendered stereo master as an input is
    #     PROVENANCE and is excluded from the quality verdict. That alone
    #     removes three of the old eight. `external_assets` is an AST scan of
    #     the source tree. `pitch` re-synthesises the dry engine from telemetry
    #     and measures THAT -- it passed 100 % white noise, and so did the other
    #     two, on 5 of 5 degenerate inputs. They are still run, still reported,
    #     still required to pass; they simply no longer answer the question
    #     "does this master sound right", because they never could.
    #
    # (2) INAPPLICABLE is a distinct outcome from PASS and never counts toward
    #     ALL_PASS. The old harmonic gate on pure noise reported `failures: []`
    #     and tripped `undeclared_unmeasurable`: it said "I cannot measure
    #     this", never "this is noise", and that read as green.
    #
    # And one more, stated plainly because the audit measured it: `seam`
    # adjudicates 20 samples of 5,956,000 -- 0.0003 % of the film -- and its own
    # 3 dB-step positive control PASSES on broadband material. Its PASS is
    # ADVISORY. It can still fail the build on a real splice, because a failure
    # there is informative even though a pass is not.
    QUALITY_GATES = ("levels", "edges", "doppler")
    PROVENANCE_GATES = ("external_assets", "pitch")
    ADVISORY_GATES = ("seam",)

    quality = {k: V[k].get("PASS") for k in QUALITY_GATES if isinstance(V.get(k), dict)}
    provenance = {k: V[k].get("PASS") for k in PROVENANCE_GATES
                  if isinstance(V.get(k), dict)}
    advisory = {k: V[k].get("PASS") for k in ADVISORY_GATES if isinstance(V.get(k), dict)}

    V["gate_classes"] = {"quality": list(quality), "provenance": list(provenance),
                         "advisory": list(advisory)}
    V["gate_summary"] = {**quality, **provenance, **advisory}
    V["quality_pass"] = all(bool(v) for v in quality.values())
    V["provenance_pass"] = all(bool(v) for v in provenance.values())
    # An advisory FAIL still stops the build. An advisory PASS proves nothing.
    V["advisory_fail"] = any(v is False for v in advisory.values())
    V["ALL_PASS"] = bool(V["quality_pass"] and V["provenance_pass"]
                         and not V["advisory_fail"])
    V["NOT_A_QUALITY_VERDICT"] = (
        "This file no longer judges whether the film sounds like an engine. "
        "Three masters passed all eight of its predecessors and all three were "
        "rejected. The percept gates -- G-FLAT, G-HNR, G-ORDER, G-RING, "
        "G-NOVEL, G-MOD, G-GESTURE, G-ROOM, G-BALANCE, G-CONSTRUCT -- live in "
        "audio/percept.py and are adjudicated by tools/percept_matrix.py, "
        "which runs a permanent control corpus FIRST and refuses to report a "
        "verdict on any master if a control comes back wrong. AUDIO_VERIFY_OK "
        "means the levels are legal, the edges are clean, no recorded asset "
        "entered the render and the Doppler solves. It does not mean the "
        "master is good.")

    with open(os.path.join(a.out, "verify_report.json"), "w") as fh:
        json.dump(V, fh, indent=1, default=float)
    print(">> quality   :", json.dumps(quality))
    print(">> provenance:", json.dumps(provenance), "(excluded from the quality verdict)")
    print(">> advisory  :", json.dumps(advisory), "(a PASS here proves nothing)")
    print(">> NOTE:", V["NOT_A_QUALITY_VERDICT"])
    print(">> STAGE RESULT:", "AUDIO_VERIFY_OK" if V["ALL_PASS"] else "AUDIO_VERIFY_FAIL")
    return 0 if V["ALL_PASS"] else 1


def doppler_gate(x, sr, spec, sheet, clock, tel, outdir, skip_plot=False):
    """The declared station: measure the sweep, predict it, compare.

    Prediction is not a formula pulled from the brief. It is this project's own
    geometry: the car's position from the telemetry through the film clock, the
    camera's ears from the rig path, and the SAME retarded-time solve the mix was
    rendered with. The received-to-emitted frequency ratio is dt_e/dt_a, which is
    read straight off that solve.
    """
    from .scene import CameraPath
    from . import spatial as sp
    cam = CameraPath()
    d = sheet["doppler"]
    lap = spec["headline"]["length_m"]

    t_ctrl = np.arange(0.0, clock.duration_s, 1.0 / sp.CTRL_HZ)
    w_ctrl = clock.world_at_film(t_ctrl)
    car = tel.sample(w_ctrl, "v_world")
    campos, _R, _l = cam.at(t_ctrl)
    r = np.linalg.norm(campos - car["pos"], axis=1)

    # the film time at which the car is at the declared station
    ts = car["track_s"]
    j = int(np.argmin(np.abs(ts - d["station_s"])))
    t_pass = float(t_ctrl[j])
    # local minimum of the range around it -- the actual closest approach
    lo, hi = max(j - int(3 * sp.CTRL_HZ), 0), min(j + int(3 * sp.CTRL_HZ), r.shape[0])
    jm = lo + int(np.argmin(r[lo:hi]))
    t_min = float(t_ctrl[jm])

    # ---- retarded-time solve, exactly as the mix used --------------------
    earL, earR, centre, _RR = cam.ears(t_ctrl)
    hdg = car["heading"]
    fwd = np.stack([np.cos(hdg), np.sin(hdg), np.zeros_like(hdg)], axis=1)
    src = car["pos"] - fwd * 1.60 + np.array([0.0, 0.0, 0.42])
    t_a, rr, _e, _u = sp.retarded(t_ctrl, src, centre, sp.C_AIR)
    ratio = 1.0 / np.gradient(t_a, t_ctrl)                  # f_recv / f_emit

    # ---- radial closing speed, measured -----------------------------------
    dr = np.gradient(rr, t_ctrl)
    win = int(3.0 * sp.CTRL_HZ)
    v_app = float(-np.min(dr[max(jm - win, 0):jm]))
    v_rec = float(np.max(dr[jm:jm + win]))
    st_closed = 1200.0 * np.log2(((sp.C_AIR + v_rec) / (sp.C_AIR - v_app)))

    # ---- measured, off the actual master ----------------------------------
    # window: from 3.0 s before closest approach to 1.2 s after. The car brakes
    # for T12 (R=50 m) 145 m past the station, i.e. 1.7 s later, and on the
    # brakes the injectors are cut and there is no firing tone to measure. The
    # window is stated rather than tuned, and the throttle that sets it is the
    # circuit spec's own vehicle model.
    from . import engine as eng_mod
    tc = np.arange(t_min - 3.0, t_min + 1.2, 0.05)

    # THE EMITTED FUNDAMENTAL MUST BE RECONSTRUCTED THE WAY THE RENDER BUILT IT.
    # `gear_and_rpm` carries a 120 ms gear hold and a 90 ms driveline lag, both
    # in SAMPLES. Calling it on the 20 Hz analysis grid ran the lag over 1.8
    # samples from an initial value of zero and the hold over 2, which made the
    # first windows report 5,579 rpm at 300 km/h and made the gear hunt between
    # 7th and 8th. It is therefore evaluated on a fine world grid and sampled.
    srf = 4800
    w0 = float(clock.world_at_film(max(tc[0] - 6.0, 0.0)))
    w1 = float(clock.world_at_film(min(tc[-1] + 1.0, clock.duration_s)))
    wf = np.arange(w0, w1, 1.0 / srf)
    vf = np.interp(wf, tel.t, tel.v_world)
    af = np.interp(wf, tel.t, tel.col["accel_long_ms2"])
    rpm_f, _gf, _lf = eng_mod.gear_and_rpm(
        vf, np.zeros_like(vf), np.zeros_like(vf), srf, wf, -2.30, -0.05)
    thr_f, _brf = eng_mod.throttle_from_spec(vf, af, spec)
    # EVALUATE THE EMITTED FUNDAMENTAL AT THE EMISSION TIME, NOT THE ARRIVAL
    # TIME. The wave that arrives at the ears at film time t was emitted
    # r/c seconds earlier -- 76 ms at closest approach but 614 ms at the start of
    # the window, where the car is 210 m away and accelerating out of T11. Using
    # the arrival time put the reconstruction a whole gear out over part of the
    # approach (a 19.6 % ratio step), which showed up as a 22 % disagreement
    # between the measured ridge in the spectrogram and the prediction. This is
    # the same retarded-time correction the renderer applies; the gate has to
    # apply it too or it is testing a different film.
    t_emit = np.interp(tc, t_a, t_ctrl)
    w_emit = clock.world_at_film(np.clip(t_emit, 0.0, clock.duration_s))
    f_emit = np.interp(w_emit, wf, rpm_f) / 60.0 * ENGINE_ORDER
    thr_e = np.interp(w_emit, wf, thr_f)

    ratio_at = np.interp(tc, t_a, ratio)            # predicted, indexed by ARRIVAL

    # WHICH TONAL SOURCE IS ON THE CAR AT THIS INSTANT?
    # Through T11's exit the car pulls 4.5 lateral g and the TYRE SCRUB SQUEAL
    # (layers.tyres: 780 + 90*tanh(lat_g/3) Hz, gated on lat_g > 1.6) is louder
    # than the engine at 170 m, where air absorption has already thinned the
    # exhaust's upper partials. Measured with an engine comb, those windows come
    # back at ratio 1.49 against a predicted 1.13 -- not an error in the mix, a
    # measurement pointed at the wrong source.
    #
    # The Doppler ratio is a property of the GEOMETRY, not of the source, so both
    # sources must measure the same ratio. Each window is measured with the comb
    # belonging to whichever source the tyre layer's own activation condition
    # says is present. That the two agree is itself the check that the
    # spatialiser applies one geometry to everything riding on the car.
    lat_g = np.abs(np.interp(w_emit, tel.t, tel.col["accel_lat_ms2"])) / 9.81
    f_scrub = 780.0 + 90.0 * np.tanh(lat_g / 3.0)
    use_scrub = lat_g > 2.0

    r_eng, conf_eng = doppler_ratio(x, sr, tc, f_emit)
    r_scr, conf_scr = doppler_ratio(x, sr, tc, f_scrub)
    r_meas = np.where(use_scrub, r_scr, r_eng)
    conf = np.where(use_scrub, conf_scr, conf_eng)
    f_src = np.where(use_scrub, f_scrub, f_emit)

    # NO THROTTLE MASK, unlike the pitch gate: the comb search is handed the
    # emitted fundamental, so it still locks on overrun where a blind f0 tracker
    # cannot. `thr_e` is reported so the overrun part of the pass is visible.
    good = np.isfinite(r_meas) & (conf > 2.0)
    if good.sum() > 8:
        st_meas = 1200.0 * np.log2(np.percentile(r_meas[good] * f_src[good], 97)
                                   / max(np.percentile(r_meas[good] * f_src[good], 3), 1e-6))
        err_c = 1200.0 * np.log2(np.maximum(r_meas[good], 1e-6)
                                 / np.maximum(ratio_at[good], 1e-6))
        med_err = float(np.median(np.abs(err_c)))
        p90_err = float(np.percentile(np.abs(err_c), 90))
        ratio_corr = float(np.corrcoef(r_meas[good], ratio_at[good])[0, 1])
        st_ratio_meas = 1200.0 * np.log2(r_meas[good].max() / r_meas[good].min())

        # A COMB SEARCH SOMETIMES LOCKS ONE TOOTH OVER, AND PEARSON'S r CANNOT
        # SURVIVE IT.  R2-045.  The failures are not near misses, they are exact
        # simple ratios: measured/predicted 0.4853 (the sub-octave) and
        # 0.7536-0.7595 (the 4th harmonic read as the 3rd).  Five of 83 windows
        # landed there on the R2-045 master and four of 85 on the master before
        # it, and that ONE window is the whole difference between r = 0.93149 and
        # r = 0.83669 — while the median error was unchanged (5.13 -> 5.12 cents)
        # and the p90 HALVED (61.12 -> 30.27).  A statistic that swings 0.09 on
        # one tracker slip, in a window where the car's position, the camera's
        # position and the predicted ratio are all bit-identical, is measuring the
        # tracker's luck and not the film.
        #
        # So the correlation is taken over the windows where the tracker LOCKED,
        # and the ones where it did not are COUNTED AND GATED instead of being
        # quietly dropped: nothing is hidden, `corr_measured_ratio_vs_predicted_
        # ratio` is still reported raw, and a master that genuinely lost its
        # Doppler would show it as a rising failure FRACTION, a rising median and
        # a rising p90, all three of which are gated.  200 cents is a whole tone —
        # eight times the worst real error either master shows (30 c) and a third
        # of the smallest comb slip possible (480 c), so the split is not a
        # borderline judgement.
        tracked = np.abs(err_c) < TRACK_MAX_CENTS
        fail_frac = float(1.0 - tracked.mean())
        if tracked.sum() > 8:
            robust_corr = float(np.corrcoef(r_meas[good][tracked],
                                            ratio_at[good][tracked])[0, 1])
            # CONTROL: the same windows, same values, correspondence destroyed.
            # A statistic that cannot tell the film from a shuffle of itself is
            # not a gate.  Seeded, so it is the same shuffle on every run.
            _perm = np.random.default_rng(7).permutation(r_meas[good][tracked])
            perm_corr = float(np.corrcoef(_perm, ratio_at[good][tracked])[0, 1])
        else:
            robust_corr = perm_corr = float("nan")
    else:
        st_meas = med_err = ratio_corr = st_ratio_meas = p90_err = float("nan")
        robust_corr = perm_corr = float("nan")
        fail_frac = float("nan")
        tracked = np.zeros(0, bool)

    # CONTROL for the estimator: the same windows measured against a comb built
    # on a DELIBERATELY WRONG emitted frequency must not return ratio 1.
    r_bad, _cb = doppler_ratio(x, sr, tc, np.where(use_scrub, f_scrub, f_emit) * 1.35)
    bad_med = float(np.nanmedian(r_bad[np.isfinite(r_bad)])) if np.isfinite(r_bad).any() else float("nan")

    # ---- CONTROLS ---------------------------------------------------------
    # (a) source held still, camera still flying. This is NOT a null: the
    #     camera decelerates from 76 m/s into the hover and leaves at 48 m/s, so
    #     the listener's own motion contributes a real sweep. Reported because
    #     it is the size of the effect the CAMERA is responsible for.
    src_static = np.repeat(src[jm][None, :], t_ctrl.shape[0], axis=0)
    t_a2, _r2, _e2, _u2 = sp.retarded(t_ctrl, src_static, centre, sp.C_AIR)
    ratio2 = 1.0 / np.gradient(t_a2, t_ctrl)
    st_listener = 1200.0 * np.log2(np.max(ratio2[lo:hi]) / np.min(ratio2[lo:hi]))
    # (b) THE TRUE NULL: source still AND ears still. Must come out at zero, or
    #     the retarded-time solve is manufacturing Doppler out of nothing.
    ear_static = np.repeat(centre[jm][None, :], t_ctrl.shape[0], axis=0)
    t_a3, _r3, _e3, _u3 = sp.retarded(t_ctrl, src_static, ear_static, sp.C_AIR)
    ratio3 = 1.0 / np.gradient(t_a3, t_ctrl)
    st_control = 1200.0 * np.log2(np.max(ratio3[lo:hi]) / np.min(ratio3[lo:hi]))

    out = {
        "declared": {k: d[k] for k in ("station_s", "peak_kph", "slant_range_m",
                                       "dwell_s", "semitone_sweep",
                                       "offset_from_centreline_m")},
        "measured_frame_of_closest_approach": int(t_min * FPS) + 1,
        "measured_film_t_closest_approach_s": t_min,
        "measured_slant_range_m": float(r[jm]),
        "measured_car_speed_kph": float(np.interp(w_ctrl[jm], tel.t, tel.v_world) * 3.6),
        "measured_camera_speed_ms": float(np.linalg.norm(
            np.gradient(campos, axis=0)[jm] * sp.CTRL_HZ)),
        "speed_of_sound_ms": sp.C_AIR,
        "measured_approach_closing_speed_ms": v_app,
        "measured_recession_speed_ms": v_rec,
        "predicted_sweep_semitones_from_closing_speeds": float(st_closed / 100.0),
        "ratio_max_from_retarded_solve": float(np.max(ratio[lo:hi])),
        "ratio_min_from_retarded_solve": float(np.min(ratio[lo:hi])),
        "predicted_sweep_semitones_from_retarded_solve": float(
            12.0 * np.log2(np.max(ratio[lo:hi]) / np.min(ratio[lo:hi]))),
        "measured_sweep_semitones_in_master": float(st_meas / 100.0) if st_meas == st_meas else None,
        "measured_ratio_span_semitones_in_master": float(st_ratio_meas / 100.0)
        if st_ratio_meas == st_ratio_meas else None,
        "measured_ratio_max": float(np.nanmax(r_meas[good])) if good.sum() else None,
        "measured_ratio_min": float(np.nanmin(r_meas[good])) if good.sum() else None,
        "corr_measured_ratio_vs_predicted_ratio": ratio_corr,
        "corr_on_tracked_windows": robust_corr,
        "tracked_windows": int(tracked.sum()),
        "tracker_failure_windows": int(good.sum()) - int(tracked.sum()),
        "tracker_failure_fraction": fail_frac,
        "tracker_failure_definition_cents": TRACK_MAX_CENTS,
        "median_abs_error_vs_prediction_cents": med_err,
        "p90_abs_error_vs_prediction_cents": p90_err,
        "usable_windows": int(good.sum()),
        "window_film_t_s": [float(tc[0]), float(tc[-1])],
        "emission_lead_at_window_start_s": float(tc[0] - t_emit[0]),
        "emission_lead_at_closest_approach_s": float(
            tc[int(np.argmin(np.abs(tc - t_min)))]
            - t_emit[int(np.argmin(np.abs(tc - t_min)))]),
        "windows_on_throttle": int((thr_e[good] > 0.10).sum()) if good.sum() else 0,
        "windows_on_overrun": int((thr_e[good] <= 0.10).sum()) if good.sum() else 0,
        "windows_measured_on_engine_comb": int((~use_scrub)[good].sum()) if good.sum() else 0,
        "windows_measured_on_tyre_scrub_comb": int(use_scrub[good].sum()) if good.sum() else 0,
        "max_lateral_g_in_window": float(lat_g.max()),
        "CONTROL_estimator_on_wrong_f_emit_median_ratio": bad_med,
        "CONTROL_permuted_windows_corr": perm_corr,
        "CONTROL_null_static_source_and_static_ears_semitones": float(st_control / 100.0),
        "listener_motion_only_sweep_semitones": float(st_listener / 100.0),
    }
    # ================= COVERAGE: EVERY BEAT WITH CAMERA-RELATIVE MOTION ====
    # THE OLD GATE SAW 85 WINDOWS IN ONE 4.2 s SPAN, 3.38 % of the film, all of
    # it inside beat 5. It was still the only load-bearing gate the suite had --
    # it failed all three whole-file degenerates -- and it passed BOTH beat-1
    # swaps with numbers bit-identical to the delivered master's, because its
    # window lives somewhere else entirely.
    #
    # So the same measurement now runs at EVERY pass: every local maximum of
    # closing speed in the retarded-time solve above DOPPLER_MIN_CLOSING_MS,
    # anywhere in the film. Stations where the engine is not sounding, or where
    # the tracker cannot lock, are reported INAPPLICABLE -- which is not a PASS
    # and does not count toward the verdict.
    def _station(t0):
        tcs = np.arange(t0 - 3.0, t0 + 1.2, 0.05)
        tcs = tcs[(tcs > 0.2) & (tcs < clock.duration_s - 0.2)]
        if tcs.size < 20:
            return None
        te = np.interp(tcs, t_a, t_ctrl)
        we = clock.world_at_film(np.clip(te, 0.0, clock.duration_s))
        fe = np.interp(we, wf, rpm_f) / 60.0 * ENGINE_ORDER
        rat = np.interp(tcs, t_a, ratio)
        lg = np.abs(np.interp(we, tel.t, tel.col["accel_lat_ms2"])) / 9.81
        fs_ = 780.0 + 90.0 * np.tanh(lg / 3.0)
        us = lg > 2.0
        re_, ce_ = doppler_ratio(x, sr, tcs, fe)
        rs_, cs_ = doppler_ratio(x, sr, tcs, fs_)
        rm = np.where(us, rs_, re_)
        cf = np.where(us, cs_, ce_)
        gd = np.isfinite(rm) & (cf > 2.0)
        if gd.sum() < 8:
            return {"film_t_s": float(t0), "usable_windows": int(gd.sum()),
                    "OUTCOME": "INAPPLICABLE",
                    "why": "fewer than 8 windows where the tracker locked -- "
                           "no engine sounding here, or no tonal source to "
                           "measure. INAPPLICABLE is not PASS."}
        ec = 1200.0 * np.log2(np.maximum(rm[gd], 1e-6)
                              / np.maximum(rat[gd], 1e-6))
        trk = np.abs(ec) < TRACK_MAX_CENTS
        ff = float(1.0 - trk.mean())
        if trk.sum() <= 8:
            # NOT A FAIL: the comb search never locked on a single window here,
            # so there is no measured Doppler ratio to disagree with anything.
            # Calling that a Doppler failure would be asserting a defect from a
            # measurement that did not happen -- which is the same error as
            # calling an unmeasurable beat a pass, pointed the other way.
            return {"film_t_s": float(t0), "usable_windows": int(gd.sum()),
                    "tracked_windows": int(trk.sum()),
                    "tracker_failure_fraction": ff,
                    "median_abs_error_cents": float(np.median(np.abs(ec))),
                    "OUTCOME": "INAPPLICABLE",
                    "why": ("the tracker locked on %d of %d windows; with no "
                            "locked window there is no measured ratio. Most "
                            "likely the engine is not the loudest tonal source "
                            "at this range. INAPPLICABLE is not PASS."
                            % (int(trk.sum()), int(gd.sum())))}
        rc = float(np.corrcoef(rm[gd][trk], rat[gd][trk])[0, 1])
        med = float(np.median(np.abs(ec)))
        p90 = float(np.percentile(np.abs(ec), 90))
        ok = bool(med < 100.0 and p90 < 150.0 and rc == rc and rc > 0.90
                  and ff <= 0.15)
        return {"film_t_s": float(t0), "usable_windows": int(gd.sum()),
                "tracked_windows": int(trk.sum()),
                "tracker_failure_fraction": ff,
                "median_abs_error_cents": med, "p90_abs_error_cents": p90,
                "corr_on_tracked_windows": rc,
                "predicted_ratio_span_semitones": float(
                    12.0 * np.log2(rat.max() / max(rat.min(), 1e-9))),
                "OUTCOME": "PASS" if ok else "FAIL"}

    drdt = np.gradient(rr, t_ctrl)
    closing = -drdt
    cand, _cp = _sig.find_peaks(closing, height=DOPPLER_MIN_CLOSING_MS,
                                distance=int(5.0 * sp.CTRL_HZ))
    stations = []
    for ci in cand:
        # the closest approach just after this closing peak
        lo2 = int(ci)
        hi2 = min(int(ci) + int(6.0 * sp.CTRL_HZ), rr.shape[0])
        if hi2 - lo2 < 4:
            continue
        tst = float(t_ctrl[lo2 + int(np.argmin(rr[lo2:hi2]))])
        if any(abs(tst - r["film_t_s"]) < 4.0 for r in stations):
            continue
        r = _station(tst)
        if r is not None:
            r["beat"] = next((b["name"] for b in reversed(sheet["beats"])
                              if tst >= b["start_s"]), "?")
            r["peak_closing_speed_ms"] = float(closing[ci])
            stations.append(r)
    out["coverage"] = {
        "declared_station_only_time_fraction": 4.2 / clock.duration_s,
        "stations": stations,
        "beats_covered": sorted({r["beat"] for r in stations}),
        "n_pass": sum(1 for r in stations if r["OUTCOME"] == "PASS"),
        "n_fail": sum(1 for r in stations if r["OUTCOME"] == "FAIL"),
        "n_inapplicable": sum(1 for r in stations
                              if r["OUTCOME"] == "INAPPLICABLE"),
        "min_closing_speed_ms": DOPPLER_MIN_CLOSING_MS,
        "engine_order": ENGINE_ORDER,
        "PORTING_NOTE": (
            "B7 halves the firing fundamental to engine order 1.5. Change "
            "ENGINE_ORDER at the top of this file BEFORE that render, or every "
            "station here reports a tracker failure fraction that looks like a "
            "broken Doppler and is not."),
    }

    out["PASS"] = bool(
        abs(out["predicted_sweep_semitones_from_retarded_solve"]
            - out["predicted_sweep_semitones_from_closing_speeds"]) < 0.6
        and med_err == med_err and med_err < 100.0
        and p90_err == p90_err and p90_err < 150.0
        and robust_corr == robust_corr and robust_corr > 0.90
        # THE CAP IS WHERE THE GATE'S TEETH ARE.  Both real masters sit at
        # 4.7 % and 6.0 %; a master with the pass window time-reversed reads
        # 79.8 % and one with the window lifted from elsewhere in the film
        # reads 62.5 %.  0.15 is 2.5x the worst real run and 4x under the
        # mildest broken one.  Note that `robust_corr` ALONE passes both of
        # those broken files (+0.953, +0.972) — it is this line and the two
        # error percentiles that fail them.
        and fail_frac == fail_frac and fail_frac <= 0.15
        and out["usable_windows"] > 8
        # AND EVERY OTHER PASS IN THE FILM. An INAPPLICABLE station does not
        # contribute either way; a FAIL anywhere fails the gate.
        and out["coverage"]["n_fail"] == 0)
    out["CONTROL_FAILS_AS_EXPECTED"] = bool(
        out["CONTROL_null_static_source_and_static_ears_semitones"] < 0.01
        and perm_corr == perm_corr and perm_corr < 0.5)

    if not skip_plot:
        plot_pitch(tc[good], r_meas[good] * f_src[good], ratio_at[good] * f_src[good],
                   os.path.join(outdir, "doppler_pitch.png"),
                   f"doppler station: measured f0 in the master vs the retarded-time "
                   f"prediction (closest approach {out['measured_slant_range_m']:.2f} m, "
                   f"{out['measured_car_speed_kph']:.1f} km/h)")
    return out


if __name__ == "__main__":
    sys.exit(main())
