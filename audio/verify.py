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


# ============================================================== level gate ====
def level_gate(x, sr):
    L, st, st_t = dsp.loudness_lufs(x, sr)
    tp = dsp.true_peak_dbtp(x, sr)
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
        "PASS": bool(tp <= -1.0 and pk < 1.0 and abs(L + 14.0) <= 0.5 and quiet == 0),
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


# ============================================ harmonic-to-noise (R2-1401) =====
# THE GATE THAT SHOULD HAVE EXISTED FIRST.
#
# Every gate in this file passed a master the client described, in full, as
# "audio is shit sounds like a hair blower". They were all correct: the levels
# were legal, the seams were clean, the pitch tracked the telemetry to 1.3 cents
# and the Doppler solved. Not one of them asked whether the sound was an ENGINE
# rather than a fan, because that question is about the RATIO of line spectrum to
# broadband -- and nothing measured it.
#
# A hair dryer is broadband noise shaped by a resonant cavity. An engine is a
# line spectrum locked to a firing frequency. The difference is one number, and
# these thresholds are where it goes.
# THE THRESHOLDS ARE SET FROM BOTH MASTERS, MEASURED THE SAME WAY. Over the
# flying lap, above 2.6 kHz: the rejected master reads -0.73 dB, this metric's
# reading on PURE NOISE is -1.97 dB, and the rebuilt film reads about +6.7 dB.
# The artefact the client rejected therefore sat 1.2 dB above a literal noise
# generator. 3.0 dB is placed between them with margin on both sides.
#
# THE ABOVE-2.6 kHz NUMBER IS THE DISCRIMINATING ONE AND THE BROADBAND NUMBER IS
# NOT, WHICH IS WORTH STATING PLAINLY. Across the whole band the two masters read
# 3.49 dB and 3.89 dB -- barely separable -- because below 2.6 kHz the mix is
# legitimately full of low-frequency bed content doing real work (wind buffet,
# tyre cavity, the outdoor bed's weight). Gating hard on the broadband figure
# would be gating on how much air the film has in it. The broadband threshold is
# a floor against total collapse; it is not the test.
HNR_MIN_DB = 2.0            # a floor, over the beats the engine drives
HNR_HF_MIN_DB = 3.0         # THE test: above 2.6 kHz, where the defect lived

# ============ R2-2221: THIS GATE SCORED THREE BEATS OF SIX, AND ON A MEDIAN ====
# TWO DEFECTS, ONE STRUCTURAL AND ONE STATISTICAL, AND THE SECOND IS NOT THE ONE
# IT LOOKS LIKE.
#
# (1) COVERAGE. `driven = ["2_launch", "4_transit", "5_lap"]` meant the breach and
#     the ending were computed, printed into `per_beat`, and then not gated. The
#     client spent 63 % of their listening time on exactly those two beats. A gate
#     that scores half the film is not a gate on the film.
#
# (2) THE MEDIAN. A per-beat median says nothing whatever about the other half of
#     the beat: 33.1 % of the flying lap sat below this gate's own 3.0 dB and it
#     passed regardless.
#
# THE REPLACEMENT IS THE FRACTION BELOW THRESHOLD, WHICH IS THE PERCENTILE FLOOR
# READ FROM THE OTHER END, AND IT IS THE END THAT CAN ACTUALLY BE GATED. Both
# forms say the same thing -- "no more than F of this beat may sit below T" -- but
# only one of them is decidable here, and that was measured rather than assumed:
#
#   * A PERCENTILE OF THE VALUE IS NOT ESTIMABLE ON A SHORT BEAT. Beat 2 is 3.0 s,
#     which is 120 analysis windows at a 25 ms hop, and those windows overlap. A
#     block bootstrap (200 ms blocks, 3000 resamples) puts the standard error of
#     its 5th percentile at 2.69 dB and of its 20th at 1.51 dB. A floor placed on
#     a number with a 2.7 dB error bar is not a floor. The separation available
#     between this master and the one the client rejected, at those percentiles,
#     is 0.58 and 1.42 dB -- smaller than the error bar on either.
#   * THE FRACTION SEPARATES FAR BETTER, because the hair dryer's failure is that
#     ALMOST EVERY window is noise-like, not that its median is low. Over the
#     flying lap above 2.6 kHz: this master 0.331 of windows below 3.0 dB, the
#     rejected master 0.911. Over the transit, 0.379 against 0.964. Its error is
#     binomial on the effective sample count, so a short beat gets an honest error
#     bar instead of a percentile estimated from six windows.
#
# Measured margins, in standard errors, of this master against its limit: worst
# 3.52 (transit HF), best 29.5 (lap broadband). The value-percentile form could
# not reach 3 sigma anywhere below its median.
#
# WHAT FRACTION IS PERMITTED, AND WHY THAT ONE. One rule, applied to every beat
# and every limb and stated once: the limit is the midpoint between what THIS
# master reads and what the adversary reads, rounded to the nearest 0.05.
#   * On the above-2.6 kHz limb, THE TEST, the adversary is the tightest of the
#     octave-matched hair dryer and the two masters the client rejected as one.
#     That limb exists to catch a hair blower, so it is set against a hair blower.
#   * On the broadband limb, THE FLOOR, the adversary is the octave-matched hair
#     dryer alone. The rejected masters are not broadband failures and were never
#     claimed to be (see the note above: 3.49 against 3.89 dB, barely separable),
#     so setting the floor against them produces a limit tighter than the film
#     itself -- measured, it lands at 0.05 with a 0.00-sigma margin. A floor is
#     not the test and must not be set as though it were.
#
# THE LAP'S BOTTOM THIRD IS NOT A DEFECT, AND THAT WAS CHECKED RATHER THAN
# ASSUMED. Correlation between a window's above-2.6 kHz ratio and its own level,
# over the flying lap: +0.252. The low-scoring windows are the QUIET windows --
# the car far away, pointing away, between passes. Restricting the lap to the
# windows within 6 dB of its own 95th-percentile level (63.0 % of them) moves the
# median from 5.84 to 8.03 dB. A film whose subject drives away from the camera
# for part of a lap is required to have quiet windows; requiring 3 dB of
# harmonic-to-noise inside them is requiring the car to be somewhere it is not.
# That is why the permitted fraction is 0.60 on the lap and not 0.05.
HNR_NOISE_FLOOR_DB = -1.0
# One decibel above what this metric reads on something with no line spectrum at
# all. Measured, per beat, on white noise wearing the master's own octave balance:
# -1.95 to -2.10 dB above 2.6 kHz across all six beats, and on flat white noise
# -1.98 to -2.01. It is the threshold for the beats the engine does not drive,
# where 3.0 dB would be asking an empty showroom to sound like an engine.

# THE APPLICABILITY TEST, AND WHY A GATE NEEDS ONE (R2-2221).
# Extending this gate to all six beats immediately raises the question the old
# `driven` list was silently answering: is this measurement MEANINGFUL in this
# beat? Two ways it can fail to be, both measured from the audio, neither
# declared by hand:
#
#   POWER -- can the metric tell this beat from a hair dryer at all? Measured as
#   the difference in the gated statistic itself between the film and the
#   octave-matched hair-dryer control. Below 0.20 there is nothing to gate.
#
#   AUDIBILITY -- would a change in the scored band be heard? The above-2.6 kHz
#   limb scores a band; if that band carries almost none of the beat's energy,
#   its harmonic-to-noise ratio is a ratio measured on nothing.
#
# These two numbers are what the old `driven` list was hiding, and they do not
# agree with it. Assembly and the ending, both excluded before, are measurable on
# both limbs and are gated here. The breach, also excluded before, fails BOTH
# tests -- and fails them by two orders of magnitude, not marginally. See
# `harmonic_gate` for the numbers and what covers the breach instead.
HNR_POWER_MIN = 0.20        # fraction, film against the hair-dryer control
HNR_HF_SHARE_MIN = 0.002    # of a beat's energy, above 2.6 kHz

# (threshold dB, fraction of the beat permitted below it), per beat, per limb.
# Produced by the one rule above; every endpoint and every margin is in the
# staging note for R2-2221 and reproduced by `tools/audio_hnr_evidence.py`.
BEAT_HNR_LIMITS = {
    "1_assembly": {"hf": (HNR_NOISE_FLOOR_DB, 0.85), "bb": (HNR_NOISE_FLOOR_DB, 0.30)},
    "2_launch":   {"hf": (HNR_HF_MIN_DB,      0.40), "bb": (HNR_MIN_DB,          0.50)},
    "3_breach":   {"hf": (HNR_NOISE_FLOOR_DB, 0.65), "bb": (HNR_NOISE_FLOOR_DB, 0.55)},
    "4_transit":  {"hf": (HNR_HF_MIN_DB,      0.65), "bb": (HNR_MIN_DB,          0.55)},
    "5_lap":      {"hf": (HNR_HF_MIN_DB,      0.60), "bb": (HNR_MIN_DB,          0.60)},
    "6_ending":   {"hf": (HNR_NOISE_FLOOR_DB, 0.65), "bb": (HNR_NOISE_FLOOR_DB, 0.30)},
}
# The beats whose threshold is the engine test rather than the noise floor. This
# list is no longer the gate's coverage -- every beat is gated -- it only chooses
# which of the two thresholds a beat is held to.
HNR_ENGINE_BEATS = ("2_launch", "4_transit", "5_lap")

# THE ONE DECLARED HOLE, AND EVERY NUMBER BEHIND IT.
# `3_breach` is the only beat this metric cannot measure, and it fails both
# applicability tests independently, each by about two orders of magnitude:
#
#   AUDIBILITY. The band above 2.6 kHz carries 0.020 % of the breach's energy --
#   -47.7 dBFS, which is 31.5 dB below the flying lap's own RMS and 37 dB below
#   the breach's. The next darkest beat in the film is the assembly at 1.02 %, so
#   the breach is fifty times below anything else and the 0.20 % limit sits in a
#   two-order-of-magnitude gap where no choice of it changes the answer. The
#   +0.09 dB that this beat scores above 2.6 kHz is a ratio computed on one part
#   in five thousand of what anybody hears.
#
#   POWER. On the broadband limb, where the breach's energy actually is, this
#   metric scores the film 0.044 BELOW an octave-matched hair dryer -- the wrong
#   sign. That is not a bug: the breach is 995 shard contacts and a laminated
#   pane, and a median-filtered spectral floor cannot find a line spectrum in 995
#   randomly-timed inharmonic rings because there is not one there. Breaking
#   glass is broadband on purpose.
#
# WHAT COVERS THE BREACH INSTEAD, since "this gate cannot see it" is not the same
# as "nothing does": `level_gate` for distortion and clipping (it is the film's
# loudest event, -10.4 dBFS RMS), `seam_gate` at both its boundaries (it is also
# the film's largest legitimate spectral jump, which is why the seam gate scores
# a local percentile rather than an absolute step), and `edge_gate` on the master
# that contains it.
#
# THIS IS A DECLARATION, NOT A SKIP. If any OTHER beat ever becomes unmeasurable
# on both limbs it lands in `undeclared_unmeasurable` and the gate FAILS. And the
# declaration cannot rot in the beat's favour: the two numbers above are
# recomputed from the audio every run, so if a future edit puts high frequency
# back into the breach, its share rises past 0.20 %, the limb becomes applicable
# on its own, and the breach starts being gated with no edit to this file.
HNR_DECLARED_UNMEASURABLE = ("3_breach",)


def _hairdryer_like(x, sr, seed=1401):
    """White noise wearing `x`'s own octave balance: the adversary, in one place.

    This exact construction was already the strongest of `control_harmonic`'s
    three controls -- it has the film's tonal balance and no line spectrum
    anywhere, so anything it scores well on is being scored on brightness or
    level rather than on harmonicity. R2-2221 promotes it from a control to the
    reference the gate's own applicability and limits are measured against, so
    that "can this metric see anything here" is a number from this run rather
    than a judgement made once and written into a list.
    """
    rng = np.random.default_rng(seed)
    nz = rng.standard_normal(x.shape[0])
    out = np.zeros_like(nz)
    edges = [31.25 * 2.0 ** k for k in range(10)]
    for lo, hi in zip(edges[:-1], edges[1:]):
        if hi >= sr * 0.49:
            break
        sos = _sig.butter(4, [lo, min(hi, sr * 0.45)], btype="bandpass",
                          fs=sr, output="sos")
        bx = _sig.sosfilt(sos, x)
        bn = _sig.sosfilt(sos, nz)
        out += bn * (np.sqrt(np.mean(bx ** 2))
                     / max(np.sqrt(np.mean(bn ** 2)), 1e-12))
    return out


# ---------------------------------------------------------------- waveguide ---
# WHY THIS GATE EXISTS (R2-2004). Every gate above passed a master the client described as
# "a wind machine with someone banging on tubes", and the harmonic gate passed it
# most emphatically of all -- HNR above 2.6 kHz went 3.2 -> 23.7 dB in the
# rebuild that CAUSED the banging. That is not a bug in the harmonic gate. HNR
# asks "is this tonal rather than noisy", and a struck tube is extremely tonal.
# It scores well. Nothing we owned asked the other question: does the tone STOP
# between firing events, or does it ring on into the next one.
#
# So this gate measures decay, not spectrum, and it does it on the synthesiser's
# own constants rather than on the rendered wav -- the exhaust's mode structure is
# fully determined by PRIMARY_L_CYL, the loop gains and the damping corners, so
# solving it directly is exact, instant, and cannot be masked by the wind bed
# sitting on top of it in the mix.
#
# The measurement. Each pipe is y[n] = x[n] -/+ g*LP(y[n-D]), whose denominator
# is the polynomial (1 - c z^-1) -/+ g(1-c) z^-D. Its roots ARE the modes: the
# angle of each root gives the mode frequency, the magnitude gives its decay, and
# T60 = 60 / (-20 log10 |z|) samples. Compare that against the interval between
# firing events, 20/rpm seconds for a V6 (three firings per revolution).
#
# The threshold, and why it is not 1.0. At 11,000 rpm a V6 fires every 1.82 ms
# while one primary's acoustic round trip is 1.91 ms, so a real engine ALWAYS has
# a previous pulse still in the pipe and a ratio below 1 is not physically
# available. What separates an engine from a struck tube is the DEPTH of that
# overlap. Measured on the two masters the client rejected, the median mode rang
# for 7.5 firing intervals and the worst for 20.7; at 8.0 the gate would have
# failed both. The rebuilt values sit at 3.0 median / 6.9 worst.
WAVEGUIDE_RPM = 11000.0      # representative of the flying lap: rpm_at_vmax is 13,143
WAVEGUIDE_MEDIAN_MAX = 5.0   # median mode T60, in firing intervals
WAVEGUIDE_WORST_MAX = 9.0    # the longest-ringing mode below 9 kHz
WAVEGUIDE_HARMONIC_MAX_PCT = 4.0   # see below


def pipe_modes(length_m, loop_gain, damp_hz, c_gas, sr, invert):
    """Exact mode frequencies and T60 of one `dsp.comb_pipe`, by root-solving.

    Not an impulse-response estimate. A Schroeder decay on a band-filtered
    impulse response measures the ANALYSIS FILTER's ringing as much as the
    pipe's -- at 125 Hz a third-octave Butterworth has a T60 of 179 ms on its
    own, which is longer than anything the pipe does. Root-solving has no such
    floor and no such ambiguity.
    """
    D = max(int(round(2.0 * length_m / c_gas * sr)), 4)
    c = float(np.exp(-2.0 * np.pi * min(damp_hz, sr * 0.45) / sr))
    s = -1.0 if invert else 1.0
    a = np.zeros(D + 1)
    a[0], a[1] = 1.0, -c
    a[D] -= s * loop_gain * (1.0 - c)
    r = np.roots(a)
    f = np.angle(r) / (2.0 * np.pi) * sr
    keep = (f > 1.0) & (np.abs(r) < 1.0)
    f, mag = f[keep], np.abs(r[keep])
    t60 = 60.0 / np.maximum(-20.0 * np.log10(np.maximum(mag, 1e-12)), 1e-12) / sr
    o = np.argsort(f)
    return f[o], t60[o]


def waveguide_gate(sr=96000):
    """Does the exhaust get DRIVEN by the firing series, or STRUCK by it?"""
    from audio import engine as _E
    fire = 20.0 / WAVEGUIDE_RPM                     # V6: three firings per rev
    out = {"rpm": WAVEGUIDE_RPM, "firing_interval_s": fire, "elements": []}
    worst_ratio, medians = 0.0, []
    worst_harm = 0.0
    elems = [("primary_cyl%d" % i, L, _E.PIPE_LOOP_GAIN, _E.PIPE_DAMP_HZ, True)
             for i, L in enumerate(_E.PRIMARY_L_CYL)]
    elems += [("collector", _E.COLLECTOR_L, _E.COLLECTOR_LOOP_GAIN,
               _E.COLLECTOR_DAMP_HZ, False),
              ("tailpipe", _E.TAILPIPE_L, _E.PIPE_LOOP_GAIN * 0.8,
               _E.PIPE_DAMP_HZ, False)]
    for name, L, g, dh, inv in elems:
        f, t = pipe_modes(L, g, dh, _E.C_EXHAUST, sr, inv)
        sel = f < 9000.0
        if sel.sum() < 3:
            continue
        f, t = f[sel], t[sel]
        ratio = t / fire
        # Harmonicity: an in-loop lowpass is dispersive, so damping the ring
        # harder detunes the upper modes and turns the pipe INTO a bell. Whatever
        # a future edit does to shorten the ring, it may not do it this way.
        n = np.arange(1, len(f) + 1) * (2 if inv else 1) - (1 if inv else 0)
        harm_pct = float(np.abs(f - f[0] * n).max() / (f[0] * n.max()) * 100.0)
        medians.append(float(np.median(ratio)))
        worst_ratio = max(worst_ratio, float(ratio.max()))
        worst_harm = max(worst_harm, harm_pct)
        out["elements"].append({
            "name": name, "length_m": float(L), "loop_gain": float(g),
            "f0_hz": float(f[0]), "modes_below_9k": int(len(f)),
            "t60_at_f0_ms": float(t[0] * 1e3),
            "q_at_f0": float(np.pi * f[0] * t[0] / 6.91),
            "median_ring_through": float(np.median(ratio)),
            "worst_ring_through": float(ratio.max()),
            "max_harmonic_error_pct": harm_pct,
        })
    out["median_ring_through"] = float(np.max(medians)) if medians else float("inf")
    out["worst_ring_through"] = worst_ratio
    out["max_harmonic_error_pct"] = worst_harm
    out["threshold_median"] = WAVEGUIDE_MEDIAN_MAX
    out["threshold_worst"] = WAVEGUIDE_WORST_MAX
    out["threshold_harmonic_pct"] = WAVEGUIDE_HARMONIC_MAX_PCT
    out["PASS"] = bool(out["median_ring_through"] <= WAVEGUIDE_MEDIAN_MAX
                       and worst_ratio <= WAVEGUIDE_WORST_MAX
                       and worst_harm <= WAVEGUIDE_HARMONIC_MAX_PCT)
    return out


def control_waveguide(sr=96000):
    """Positive controls: the gate must FAIL the values that produced the
    complaint, and must FAIL the tempting wrong fix.

    [0] the shipped 0.70/0.62 -- what the client called banging on tubes.
    [1] 0.85: a nearly lossless pipe, worse still.
    [2] a 3rd-order in-loop lowpass at 1200 Hz with the delay compensated back to
        pitch. It shortens the ring beautifully (T60 at 3 kHz 18.5 -> 2.8 ms) and
        it is the WRONG ANSWER: it stretches the mode series 20.5 % off the odd
        c/4L harmonics, which is 323 cents, which is a tubular bell. If the
        harmonicity limb of this gate ever gets deleted, this control passes.
    [3] STATED NEGATIVE: the values actually shipped must PASS.
    """
    from audio import engine as _E
    fire = 20.0 / WAVEGUIDE_RPM
    L = _E.PRIMARY_L_CYL[0]
    out = []
    for label, g, dh, order in [
            ("R2-1401 shipped: loop_gain 0.70, damp 3200 (the rejected master)",
             0.70, 3200.0, 1),
            ("near-lossless pipe: loop_gain 0.85", 0.85, 3200.0, 1),
            ("3rd-order in-loop lowpass at 1200 Hz (short ring, INHARMONIC)",
             0.44, 1200.0, 3),
            ("STATED NEGATIVE: the shipped values", _E.PIPE_LOOP_GAIN,
             _E.PIPE_DAMP_HZ, 1)]:
        if order == 1:
            f, t = pipe_modes(L, g, dh, _E.C_EXHAUST, sr, True)
        else:
            c = float(np.exp(-2.0 * np.pi * dh / sr))
            f0 = _E.C_EXHAUST / (4.0 * L)
            w = 2.0 * np.pi * f0 / sr
            pd = -np.angle(((1 - c) / (1 - c * np.exp(-1j * w))) ** order) / w
            D = max(int(round(2.0 * L / _E.C_EXHAUST * sr - pd)), 4)
            num, den = np.array([1.0]), np.array([1.0])
            for _ in range(order):
                num = np.convolve(num, [1.0 - c])
                den = np.convolve(den, [1.0, -c])
            a = np.zeros(max(len(den), D + len(num)))
            a[:len(den)] = den
            a[D:D + len(num)] += g * num
            r = np.roots(a)
            f = np.angle(r) / (2.0 * np.pi) * sr
            k = (f > 1.0) & (np.abs(r) < 1.0)
            f, mag = f[k], np.abs(r[k])
            t = 60.0 / np.maximum(-20.0 * np.log10(np.maximum(mag, 1e-12)),
                                  1e-12) / sr
            o = np.argsort(f)
            f, t = f[o], t[o]
        sel = f < 9000.0
        f, t = f[sel], t[sel]
        ratio = t / fire
        n = np.arange(1, len(f) + 1) * 2 - 1
        harm = float(np.abs(f - f[0] * n).max() / (f[0] * n.max()) * 100.0)
        out.append({
            "label": label,
            "median_ring_through": float(np.median(ratio)),
            "worst_ring_through": float(ratio.max()),
            "max_harmonic_error_pct": harm,
            "PASS": bool(np.median(ratio) <= WAVEGUIDE_MEDIAN_MAX
                         and ratio.max() <= WAVEGUIDE_WORST_MAX
                         and harm <= WAVEGUIDE_HARMONIC_MAX_PCT),
        })
    return out


# 43 ms, NOT 93 ms. The source is a car whose pitch moves under both rpm and
# Doppler: at the doppler station the ratio spans 1.29 to 0.81 over 7 s, so inside
# a 93 ms window an 8 kHz partial sweeps ~48 Hz -- four analysis bins -- and
# smears itself into the very noise floor it is being compared against. Measured
# on the rebuilt engine bus alone over the lap, above 2.6 kHz:
#     21 ms   4.52 dB   (too short: 46 Hz bins cannot resolve the series at all)
#     43 ms  14.35 dB
#     93 ms  10.38 dB
#    186 ms   5.84 dB
# 43 ms is long enough to resolve a 600 Hz firing series (23 Hz bins) and short
# enough that the lines stay put inside it. THE REJECTED MASTER WAS RE-MEASURED AT
# THE SAME WINDOW BEFORE THE THRESHOLDS ABOVE WERE CHOSEN, so the comparison is
# like for like and the window was not picked to flatter the fix.
def hnr_profile(x, sr, win_s=0.043, hop_s=0.025, fmin=60.0, fmax=16000.0,
                hf_from=2600.0):
    """Tonal-to-broadband ratio in dB, per window, with NO f0 estimate.

    Taking a running median of the power spectrum over a 1/3-octave-wide span
    gives the BROADBAND floor: a median is insensitive to the sparse narrow peaks
    a harmonic series puts in a spectrum, and tracks the noise underneath them.
    Energy above that floor is therefore the line spectrum, and the floor's own
    energy is the noise. Their ratio is the measurement.

    Why not track f0 and sum its harmonics: by the time the signal reaches the
    master it has been through a moving Doppler shift, two facade reflections and
    a 2.4 s room tail, so the lines are neither stationary nor exactly harmonic.
    The median floor does not care -- it finds structure wherever the structure
    is, which is what "does this sound like an engine" actually asks.
    """
    from scipy.ndimage import median_filter
    n = 1 << int(np.ceil(np.log2(win_s * sr)))
    hop = int(hop_s * sr)
    w = np.hanning(n)
    f = np.fft.rfftfreq(n, 1.0 / sr)
    band = (f >= fmin) & (f <= fmax)
    hb = band & (f >= hf_from)
    med = max(int(round(0.26 * 1000.0 / (sr / n))), 5)
    med += 1 - med % 2
    starts = np.arange(0, x.shape[0] - n, hop)
    hnr = np.empty(starts.shape[0])
    hnr_hf = np.empty(starts.shape[0])
    for i, a0 in enumerate(starts):
        P = np.abs(np.fft.rfft(x[a0:a0 + n] * w)) ** 2
        floor = median_filter(P, size=med, mode="nearest")
        tonal = np.maximum(P - floor, 0.0)
        hnr[i] = 10.0 * np.log10(max(tonal[band].sum(), 1e-30)
                                 / max(floor[band].sum(), 1e-30))
        hnr_hf[i] = 10.0 * np.log10(max(tonal[hb].sum(), 1e-30)
                                    / max(floor[hb].sum(), 1e-30))
    return starts / sr, hnr, hnr_hf


def harmonic_gate(x, sr, sheet, label="", power_ref=None, applicability=None):
    """Is the film's dominant voice a line spectrum or a noise band?

    EVERY BEAT IS SCORED AND EVERY MEASURABLE BEAT IS GATED (R2-2221). The old
    docstring said beat 1 is an empty showroom, beat 3 a breaking window and
    beat 6 a distant idle, that none of them is supposed to be harmonic, and that
    scoring them would measure the wrong thing. Two thirds of that was wrong, and
    the wrong two thirds were the two beats the client spent most of their
    listening time on.

    The assembly and the ending ARE measurable -- against an octave-matched hair
    dryer they separate by 0.245 and 0.661 in the gated statistic -- they are
    simply not ENGINE beats, so they are held to a floor one decibel above a
    noise generator instead of to the engine's 3.0 dB. Only the breach is
    genuinely unmeasurable, and it is declared, with both of its numbers, at
    `HNR_DECLARED_UNMEASURABLE`.

    Which threshold a beat is held to is `HNR_ENGINE_BEATS`; that tuple is no
    longer the gate's coverage.

    MONO-SAFE, AND IT WAS NOT (R2-2006). `hnr_profile` windows with a 1-D Hann,
    so a stereo argument raised `operands could not be broadcast (4096,2)
    (4096,)`. `main()` passes the master, which is stereo, so **this gate threw
    every time the suite ran it** -- and because the throw happened after the
    six gates before it had already printed, the run looked healthy right up to
    the point it died, and `verify_report.json` was simply never rewritten.
    That is why the report on disk carries six gates and no `harmonic`: the
    gate written to catch the hair dryer had never once run inside the suite.
    It was only ever exercised standalone, on mono, which is why nobody saw it.
    `control_harmonic` reduces its own control files to mono explicitly, so the
    requirement was known -- it was just never applied to the master itself.
    """
    x = np.asarray(x)
    if x.ndim > 1:
        x = x.mean(axis=1)
    t, h, hf = hnr_profile(x, sr)
    if power_ref is None:
        # the octave-matched hair dryer, built from THIS signal, is the adversary
        # every applicability and limit number in this gate is measured against.
        power_ref = _hairdryer_like(x, sr)
    tr, hr, hfr = hnr_profile(power_ref, sr)
    sos_hi = _sig.butter(6, 2600.0, btype="highpass", fs=sr, output="sos")
    x_hf = _sig.sosfilt(sos_hi, x)

    per_beat, fails, not_applicable = {}, [], []
    for b in sheet["beats"]:
        name = b["name"]
        m = (t >= b["start_s"]) & (t < b["start_s"] + b["duration_s"])
        mr = (tr >= b["start_s"]) & (tr < b["start_s"] + b["duration_s"])
        if not m.any():
            continue
        s0 = int(round(b["start_s"] * sr))
        s1 = int(round((b["start_s"] + b["duration_s"]) * sr))
        e_all = float(np.mean(x[s0:s1] ** 2))
        share = float(np.mean(x_hf[s0:s1] ** 2) / max(e_all, 1e-30))
        lim = BEAT_HNR_LIMITS.get(name)
        rec = {"hnr_db": float(np.median(h[m])),
               "hnr_above_2k6_db": float(np.median(hf[m])),
               "windows": int(m.sum()),
               "engine_driven": name in HNR_ENGINE_BEATS,
               "energy_share_above_2k6": share,
               "band_level_above_2k6_dbfs":
                   float(10.0 * np.log10(max(np.mean(x_hf[s0:s1] ** 2), 1e-30))),
               "limbs": {}}
        for limb, prof, prof_ref in (("hf", hf, hfr), ("bb", h, hr)):
            thr, permitted = lim[limb]
            frac = float((prof[m] < thr).mean())
            frac_ref = float((prof_ref[mr] < thr).mean()) if mr.any() else 1.0
            power = frac_ref - frac
            why = None
            if power < HNR_POWER_MIN:
                why = ("no power: this metric scores the beat %+.3f against an "
                       "octave-matched hair dryer on this limb, so there is "
                       "nothing here to gate" % power)
            elif limb == "hf" and share < HNR_HF_SHARE_MIN:
                why = ("not audible: the band above 2.6 kHz carries %.4f%% of "
                       "this beat's energy (limit %.2f%%), so its harmonic-to-"
                       "noise ratio is a ratio measured on nothing"
                       % (100.0 * share, 100.0 * HNR_HF_SHARE_MIN))
            ok = why is None
            # APPLICABILITY IS A PROPERTY OF THE FILM, NOT OF THE SIGNAL UNDER
            # TEST, and conflating the two is a hole big enough to drive the
            # whole gate through (R2-2221). Both applicability tests compare the
            # signal against a hair dryer -- so when the signal IS a hair dryer,
            # every limb reads zero power, every limb goes NOT APPLICABLE, and
            # the control passes by having nothing left to fail. Measured on the
            # first build of this gate: control (2) PASS=True with no failures,
            # and the master the client rejected failed only one beat of three
            # because the other two had "no power" against a copy of the defect
            # they contain. A control is scored against the FILM's applicability,
            # which `main` computes once from the master and hands down.
            if applicability is not None:
                ok = bool(applicability.get(name, {}).get(limb, False))
                if not ok and why is None:
                    why = ("not applicable on the master, and applicability is "
                           "the master's property, not this signal's")
            rec["limbs"][limb] = {
                "threshold_db": thr,
                "fraction_below": frac,
                "fraction_permitted_below": permitted,
                "fraction_below_on_hairdryer_control": frac_ref,
                "power_vs_hairdryer": power,
                "APPLICABLE": ok,
                "not_applicable_because": why,
                "PASS": bool(frac <= permitted) if ok else None,
            }
            if ok and frac > permitted:
                fails.append("%s.%s %.3f > %.2f below %.1f dB"
                             % (name, limb, frac, permitted, thr))
            if not ok:
                not_applicable.append("%s.%s: %s" % (name, limb, why))
        per_beat[name] = rec

    # A beat with no applicable limb is a hole, and it must be a DECLARED hole.
    # `3_breach` is the only one and it is declared below; anything else that
    # becomes unmeasurable fails the gate rather than falling quietly out of it.
    uncovered = [n for n, r in per_beat.items()
                 if not any(l["APPLICABLE"] for l in r["limbs"].values())]
    undeclared = [n for n in uncovered if n not in HNR_DECLARED_UNMEASURABLE]
    eng = [per_beat[k] for k in HNR_ENGINE_BEATS if k in per_beat]
    return {
        "label": label,
        "method": ("median-filtered spectral floor; tonal energy above the floor "
                   "against the floor's own energy, 60 Hz - 16 kHz, and again "
                   "restricted to above 2.6 kHz. GATED ON THE FRACTION OF EACH "
                   "BEAT BELOW ITS THRESHOLD, not on the beat's median, and on "
                   "every beat rather than on the three the engine drives."),
        "per_beat": per_beat,
        "beats_scored": sorted(per_beat),
        "beats_gated": sorted(n for n in per_beat if n not in uncovered),
        "beats_unmeasurable": sorted(uncovered),
        "declared_unmeasurable": sorted(HNR_DECLARED_UNMEASURABLE),
        "undeclared_unmeasurable": sorted(undeclared),
        "not_applicable": sorted(not_applicable),
        "failures": sorted(fails),
        "applicability": {n: {k: v["APPLICABLE"] for k, v in r["limbs"].items()}
                          for n, r in per_beat.items()},
        "applicability_source": "this signal" if applicability is None else "the master",
        "engine_driven_beats": list(HNR_ENGINE_BEATS),
        # kept so the numbers in every earlier report stay comparable
        "worst_engine_beat_hnr_db": float(min(g["hnr_db"] for g in eng)),
        "worst_engine_beat_hnr_above_2k6_db":
            float(min(g["hnr_above_2k6_db"] for g in eng)),
        "threshold_hnr_db": HNR_MIN_DB,
        "threshold_hnr_above_2k6_db": HNR_HF_MIN_DB,
        "PASS": bool(not fails and not undeclared),
    }


def control_harmonic(x, sr, sheet, applicability=None):
    """Positive controls: things that ARE hair dryers must fail this gate.

    1. The shipped R2-1400 master itself, if it is still on disk. This is the
       strongest control available -- the artefact the client actually rejected,
       scored by the gate written to catch it. Skipped, and said so, if absent.
    2. A synthesised hair dryer: white noise through the SAME octave-band
       envelope as the master, so it has the film's exact tonal balance and no
       line spectrum at all. If the gate were secretly measuring brightness or
       level rather than harmonicity, this would pass.
    3. STATED NEGATIVE: the master with its top four octaves replaced by noise of
       the same band energy. This is the R2-1401 defect reconstructed on top of a
       fixed master, and it must fail on the HF threshold while still passing the
       broadband one -- which is what makes those two thresholds separate numbers.

    THE CONTROLS ARE SCORED AGAINST THE MASTER'S OWN APPLICABILITY (R2-2221).
    Every call below is handed the SAME `power_ref` the real gate used -- the
    hair dryer built from the master. If each control were allowed to build its
    own reference, control (2) would be measured against a copy of itself, every
    limb would read zero power, every limb would go NOT APPLICABLE, and a literal
    hair dryer would pass this gate by having nothing left to fail. A control
    must be held to the film's thresholds, not to its own.
    """
    # Same stereo trap as `harmonic_gate` (R2-2006), one step further in: controls
    # 2 and 3 BUILD their signal out of `x`, so a stereo master produced a stereo
    # band-split added to mono noise. Reduce once, here, and every control below
    # is built from the same mono the gate itself scores.
    x = np.asarray(x)
    if x.ndim > 1:
        x = x.mean(axis=1)
    ref = _hairdryer_like(x, sr)
    out = []
    # kept deliberately: this exact file is the artefact the client rejected, and
    # it is the only control here that was not constructed to fail.
    old = os.path.join(ROOT, "audio", "out", "ab",
                       "master_R2-1400_REJECTED_hairblower.wav")
    if os.path.exists(old):
        y, ysr = sf.read(old, dtype="float64")
        if y.ndim > 1:
            y = y.mean(axis=1)
        out.append(harmonic_gate(y, ysr, sheet, power_ref=ref, applicability=applicability,
                                 label="CONTROL: the R2-1400 master the client "
                                       "rejected as a hair blower"))

    # (2) noise with the master's own octave balance
    out.append(harmonic_gate(ref, sr, sheet, power_ref=ref, applicability=applicability,
                             label="CONTROL: white noise wearing the master's own "
                                   "octave balance -- a literal hair dryer"))

    # (3) the R2-1401 defect rebuilt on top of whatever `x` is
    rng = np.random.default_rng(1402)
    sos_hi = _sig.butter(4, 2600.0, btype="highpass", fs=sr, output="sos")
    sos_lo = _sig.butter(4, 2600.0, btype="lowpass", fs=sr, output="sos")
    hi = _sig.sosfilt(sos_hi, x)
    nz2 = _sig.sosfilt(sos_hi, rng.standard_normal(x.shape[0]))
    nz2 *= np.sqrt(np.mean(hi ** 2)) / max(np.sqrt(np.mean(nz2 ** 2)), 1e-12)
    out.append(harmonic_gate(_sig.sosfilt(sos_lo, x) + nz2, sr, sheet, power_ref=ref, applicability=applicability,
                             label="CONTROL, STATED NEGATIVE: the master's top four "
                                   "octaves replaced by noise of equal band energy"))
    return out


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
        "PASS": len(hits_render) == 0 and len(hits_all) == 0}
    V["external_assets"].update(control_external(a.out))
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
    f_pred = np.interp(wt, tw, rpm) / 60.0 * 3.0
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

    # ------------------------------------------------------------ harmonic ----
    V["harmonic"] = harmonic_gate(x, sr, sheet, label=os.path.basename(a.wav))
    hctl = control_harmonic(x, sr, sheet,
                            applicability=V["harmonic"]["applicability"])
    V["harmonic_controls"] = hctl
    V["harmonic"]["CONTROL_FAILS_AS_EXPECTED"] = bool(all(not c["PASS"] for c in hctl))
    print(">> harmonic:", json.dumps(
        {k: V["harmonic"][k] for k in
         ("beats_scored", "beats_gated", "beats_unmeasurable",
          "declared_unmeasurable", "undeclared_unmeasurable", "failures",
          "PASS", "CONTROL_FAILS_AS_EXPECTED")}, indent=1))
    print("   %-12s %5s %8s | %-28s | %-28s"
          % ("beat", "wins", "HF share", "above 2.6 kHz", "broadband"))
    for name, r in V["harmonic"]["per_beat"].items():
        cells = []
        for limb in ("hf", "bb"):
            L = r["limbs"][limb]
            cells.append("n/a %+.3f power" % L["power_vs_hairdryer"]
                         if not L["APPLICABLE"] else
                         "%.3f of %.2f below %+.1f dB %s"
                         % (L["fraction_below"], L["fraction_permitted_below"],
                            L["threshold_db"], "ok" if L["PASS"] else "FAIL"))
        print("   %-12s %5d %7.3f%% | %-28s | %-28s"
              % (name, r["windows"], 100.0 * r["energy_share_above_2k6"], *cells))
    for w in V["harmonic"]["not_applicable"]:
        print("   NOT APPLICABLE %s" % w)
    for c in hctl:
        print(f"   control {c['label'][:64]}: HNR {c['worst_engine_beat_hnr_db']:5.1f} "
              f"/ HF {c['worst_engine_beat_hnr_above_2k6_db']:5.1f} PASS={c['PASS']} "
              f"{'; '.join(c['failures'][:3])}")

    # ----------------------------------------------------------- waveguide ----
    V["waveguide"] = waveguide_gate()
    wctl = control_waveguide()
    V["waveguide_controls"] = wctl
    # [0..2] must FAIL, [3] -- the shipped values -- must PASS
    V["waveguide"]["CONTROL_FAILS_AS_EXPECTED"] = bool(
        all(not c["PASS"] for c in wctl[:3]) and wctl[3]["PASS"])
    print(">> waveguide:", json.dumps(
        {k: V["waveguide"][k] for k in
         ("rpm", "median_ring_through", "worst_ring_through",
          "max_harmonic_error_pct", "threshold_median", "threshold_worst",
          "threshold_harmonic_pct", "PASS", "CONTROL_FAILS_AS_EXPECTED")}, indent=1))
    for e in V["waveguide"]["elements"]:
        print(f"   {e['name']:14s} f0 {e['f0_hz']:6.1f} Hz  Q {e['q_at_f0']:5.2f}  "
              f"T60 {e['t60_at_f0_ms']:6.2f} ms  ring-through med "
              f"{e['median_ring_through']:5.2f}x worst {e['worst_ring_through']:5.2f}x")
    for c in wctl:
        print(f"   control {c['label'][:62]:62s}: med {c['median_ring_through']:6.2f}x "
              f"worst {c['worst_ring_through']:6.2f}x harm {c['max_harmonic_error_pct']:5.2f}% "
              f"PASS={c['PASS']}")

    passes = {k: V[k].get("PASS") for k in ("levels", "edges", "seam", "external_assets",
                                            "pitch", "doppler", "harmonic", "waveguide")
              if isinstance(V.get(k), dict)}
    V["ALL_PASS"] = all(bool(v) for v in passes.values())
    V["gate_summary"] = passes
    with open(os.path.join(a.out, "verify_report.json"), "w") as fh:
        json.dump(V, fh, indent=1, default=float)
    print(">> gates:", json.dumps(passes))
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
    f_emit = np.interp(w_emit, wf, rpm_f) / 60.0 * 3.0
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
        and out["usable_windows"] > 8)
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
