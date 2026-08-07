"""A/B THE FILM'S ENDING. Two masters in, one verdict out.

    .venv/bin/python tools/audio_ending_ab.py A.wav B.wav --out audio/out/ab

Three separate questions, answered separately, because conflating them is how an
ending gets signed off on a number that was never about the ending:

 1. IS THE FILM BEFORE THE CHANGE THE SAME FILM?  Worst absolute sample delta
    over frames 1..2714, reported RAW and again after removing a single best-fit
    broadband gain. The gap between those two numbers is the whole-film gain
    staging in `master.py` (per-bus short-term-LUFS trims, the -14 LUFS
    normalisation, the limiter), which is a function of the ENDING and therefore
    cannot be bit-identical when the ending changes. Reporting only the raw
    number would call that a regression; reporting only the de-gained number
    would hide it.

 2. WHAT DOES THE ENDING DO?  Per-frame band energies, spectral centroid, an
    autocorrelation f0 track, and a transient count over the closing window --
    all at the ear, i.e. after propagation, so they are what an audience gets and
    not what the synthesiser emitted.

 3. WHAT DOES IT LOOK LIKE?  A linear-frequency and a log-frequency spectrogram
    of the closing window for each master, and an excerpt WAV of each so a human
    can put headphones on. The excerpts are the deliverable; the numbers are the
    index.
"""

from __future__ import annotations

import argparse
import json
import os

import numpy as np
import soundfile as sf

FPS = 24


def load(path):
    x, sr = sf.read(path, always_2d=True, dtype="float64")
    return x, sr


def prefix_delta(a, b, sr, upto_frame=2714):
    """Worst |a-b| over [0, upto_frame), raw and after one best-fit gain."""
    n = min(a.shape[0], b.shape[0], int(round(upto_frame * sr / FPS)))
    A, B = a[:n], b[:n]
    d = np.abs(A - B)
    num = float((A * B).sum())
    den = float((A * A).sum())
    g = num / den if den > 0 else 1.0
    dg = np.abs(A * g - B)
    return {
        "samples_compared": int(n),
        "frames_compared": float(n * FPS / sr),
        "worst_abs_sample_delta": float(d.max()),
        "worst_abs_sample_delta_dbfs": float(20 * np.log10(max(d.max(), 1e-15))),
        "rms_delta_dbfs": float(20 * np.log10(max(np.sqrt((A - B) ** 2).mean(), 1e-15))),
        "best_fit_gain_db": float(20 * np.log10(g)) if g > 0 else None,
        "worst_abs_sample_delta_after_gain": float(dg.max()),
        "worst_abs_sample_delta_after_gain_dbfs": float(20 * np.log10(max(dg.max(), 1e-15))),
        "first_differing_frame": (int(np.argmax(d.max(axis=1) > 0) * FPS / sr) + 1
                                  if bool((d > 0).any()) else None),
    }


def _bands(x, sr, f0, f1):
    n = x.shape[0]
    X = np.fft.rfft(x * np.hanning(n))
    f = np.fft.rfftfreq(n, 1.0 / sr)
    m = (f >= f0) & (f < f1)
    return float(np.sqrt((np.abs(X[m]) ** 2).sum()) / max(n, 1))


def frame_profile(x, sr, f_lo, f_hi):
    """Per-film-frame level, band split, centroid and an f0 estimate at the ear."""
    mono = x.mean(axis=1)
    hop = int(round(sr / FPS))
    rows = []
    for fr in range(f_lo, f_hi + 1):
        a = (fr - 1) * hop
        b = min(a + hop, mono.shape[0])
        if b - a < 64:
            break
        seg = mono[a:b]
        rms = float(np.sqrt((seg ** 2).mean()))
        w = seg * np.hanning(seg.shape[0])
        X = np.abs(np.fft.rfft(w))
        f = np.fft.rfftfreq(seg.shape[0], 1.0 / sr)
        p = X ** 2
        cen = float((f * p).sum() / max(p.sum(), 1e-30))
        # f0 by autocorrelation of the 40-1200 Hz part, 60..600 Hz search
        lo, hi = int(60 * seg.shape[0] / sr), int(1200 * seg.shape[0] / sr)
        Xb = np.zeros_like(X, dtype=complex)
        Xb[lo:hi] = np.fft.rfft(w)[lo:hi]
        band = np.fft.irfft(Xb, n=seg.shape[0])
        ac = np.correlate(band, band, mode="full")[seg.shape[0] - 1:]
        k0, k1 = int(sr / 600.0), min(int(sr / 60.0), ac.shape[0] - 1)
        f0 = float(sr / (k0 + int(np.argmax(ac[k0:k1])))) if k1 > k0 else 0.0
        clarity = float(ac[k0 + int(np.argmax(ac[k0:k1]))] / max(ac[0], 1e-30)) if k1 > k0 else 0.0
        rows.append({
            "frame": fr,
            "rms_dbfs": 20 * np.log10(max(rms, 1e-12)),
            "peak": float(np.abs(seg).max()),
            "centroid_hz": cen,
            "f0_hz": f0, "f0_clarity": clarity,
            "e_sub_dbfs": 20 * np.log10(max(_bands(seg, sr, 20, 120), 1e-12)),
            "e_low_dbfs": 20 * np.log10(max(_bands(seg, sr, 120, 500), 1e-12)),
            "e_mid_dbfs": 20 * np.log10(max(_bands(seg, sr, 500, 2000), 1e-12)),
            "e_hi_dbfs": 20 * np.log10(max(_bands(seg, sr, 2000, 8000), 1e-12)),
            "e_air_dbfs": 20 * np.log10(max(_bands(seg, sr, 8000, 20000), 1e-12)),
            "lr_balance_db": float(
                20 * np.log10(max(np.sqrt((x[a:b, 1] ** 2).mean()), 1e-12)
                              / max(np.sqrt((x[a:b, 0] ** 2).mean()), 1e-12))),
        })
    return rows


def transients(x, sr, f_lo, f_hi, thresh_db=6.0):
    """Onsets in the window: spectral flux peaks, reported as film frames."""
    mono = x.mean(axis=1)
    a, b = (f_lo - 1) * sr // FPS, f_hi * sr // FPS
    seg = mono[a:min(b, mono.shape[0])]
    win, hop = 2048, 512
    frames = 1 + (seg.shape[0] - win) // hop
    S = np.empty((frames, win // 2 + 1))
    w = np.hanning(win)
    for i in range(frames):
        S[i] = np.abs(np.fft.rfft(seg[i * hop:i * hop + win] * w))
    flux = np.maximum(np.diff(S, axis=0), 0).sum(axis=1)
    flux = flux / max(flux.max(), 1e-30)
    med = np.convolve(flux, np.ones(21) / 21, mode="same")
    hit = (flux > med * 10 ** (thresh_db / 20.0) + 0.02)
    out = []
    for i in np.flatnonzero(hit):
        if out and i - out[-1][0] < 8:
            continue
        out.append((int(i), float(flux[i])))
    return [{"frame": f_lo + int(i * hop / sr * FPS), "strength": s} for i, s in out]


def spectrograms(paths, labels, sr, f_lo, f_hi, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy import signal as sg

    # THE SCALE IS SET FROM THE WINDOW, NOT FROM THE FILM, AND IS SHARED BY BOTH
    # PANELS. The closing 11 s sits 20-30 dB under the breach, so the whole-film
    # -130..-40 dB scale renders every panel as one saturated slab -- which is
    # exactly what the first pass of this plot did, and it hid the thing the plot
    # exists to show. Top of scale = the 99.7th percentile ACROSS BOTH masters,
    # 78 dB of range under it, so A and B stay directly comparable.
    grams = []
    for x in paths:
        mono = x.mean(axis=1)
        a, b = (f_lo - 1) * sr // FPS, min(f_hi * sr // FPS, mono.shape[0])
        f, t, S = sg.spectrogram(mono[a:b], sr, nperseg=4096, noverlap=3584,
                                 scaling="spectrum")
        grams.append((f, t, 10 * np.log10(np.maximum(S, 1e-16))))
    top = float(max(np.percentile(g[2], 99.7) for g in grams))
    # ROW 2 IS FLATTENED, and it has to be. A mix spectrum tilts ~60 dB from the
    # bed at 40 Hz to the air at 16 kHz, so ONE absolute colour scale is either
    # saturated across the mids or black across the top -- the first two passes of
    # this plot were both, and neither showed the thing being judged. Row 2
    # subtracts each bin's own median OVER THE WINDOW, so it answers "what
    # CHANGES", which is where a downshift staircase and a car coming to rest
    # live. Absolute level is not lost: it is the `rms_dbfs` column of
    # `frame_profile`, measured on the same frames.
    ref = [np.median(g[2], axis=1, keepdims=True) for g in grams]
    ref0 = np.maximum.reduce(ref) if len(ref) > 1 else ref[0]
    t0 = (f_lo - 1) / FPS

    fig, axes = plt.subplots(2, len(paths), figsize=(9 * len(paths), 9), squeeze=False)
    for c, ((f, t, db), lab) in enumerate(zip(grams, labels)):
        for r, (fmax, ylab, ysc, flat) in enumerate((
                (2500, "Hz (linear, 0-2.5 kHz) -- absolute dB", "linear", False),
                (20000, "Hz (log) -- dB re window median per bin", "log", True))):
            ax = axes[r][c]
            m = f <= fmax
            z = (db - ref0)[m] if flat else db[m]
            kw = dict(vmin=-16.0, vmax=16.0, cmap="RdBu_r") if flat else \
                dict(vmin=top - 45.0, vmax=top, cmap="magma")
            ax.pcolormesh(t + t0, f[m], z, shading="auto", **kw)
            if ysc == "log":
                ax.set_yscale("log"); ax.set_ylim(40, fmax)
            ax.set_title(f"{lab}  frames {f_lo}-{f_hi}")
            ax.set_ylabel(ylab); ax.set_xlabel("film t (s)")
            for fr in (2715, 2936):
                ax.axvline((fr - 1) / FPS, color="lime", lw=1.0, ls="--")
    fig.tight_layout()
    fig.savefig(out_png, dpi=110)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--labels", default="A,B")
    ap.add_argument("--out", default="audio/out/ab")
    ap.add_argument("--first-frame", type=int, default=2690)
    ap.add_argument("--last-frame", type=int, default=2978)
    ap.add_argument("--prefix-frame", type=int, default=2714)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    A, sr = load(args.a)
    B, srb = load(args.b)
    assert sr == srb, (sr, srb)
    la, lb = args.labels.split(",")

    rep = {"a": args.a, "b": args.b, "sr": sr,
           "duration_a_s": A.shape[0] / sr, "duration_b_s": B.shape[0] / sr,
           "frames_a": A.shape[0] * FPS / sr, "frames_b": B.shape[0] * FPS / sr,
           "prefix": prefix_delta(A, B, sr, args.prefix_frame)}

    for x, lab in ((A, la), (B, lb)):
        a = (args.first_frame - 1) * sr // FPS
        sf.write(os.path.join(args.out, f"ending_{lab}.wav"), x[a:], sr, subtype="PCM_24")
        rep[f"profile_{lab}"] = frame_profile(x, sr, args.first_frame, args.last_frame)
        rep[f"transients_{lab}"] = transients(x, sr, args.first_frame, args.last_frame)

    spectrograms([A, B], [la, lb], sr, args.first_frame, args.last_frame,
                 os.path.join(args.out, "ending_spectrograms.png"))

    with open(os.path.join(args.out, "ending_ab.json"), "w") as fh:
        json.dump(rep, fh, indent=1)
    p = rep["prefix"]
    print(f"prefix frames 1-{args.prefix_frame}: worst |d| {p['worst_abs_sample_delta']:.3e} "
          f"({p['worst_abs_sample_delta_dbfs']:.1f} dBFS); after {p['best_fit_gain_db']:+.4f} dB "
          f"best-fit gain {p['worst_abs_sample_delta_after_gain']:.3e} "
          f"({p['worst_abs_sample_delta_after_gain_dbfs']:.1f} dBFS)")
    print(f">> {args.out}/ending_ab.json  ending_{la}.wav  ending_{lb}.wav  "
          f"ending_spectrograms.png")


if __name__ == "__main__":
    main()
