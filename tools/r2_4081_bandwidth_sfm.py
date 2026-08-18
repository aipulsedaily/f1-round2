#!/usr/bin/env python
"""R2-4081 -- G-BALANCE / G-FLAT: DOES A BAND-WIDTH-AWARE TERM ACTUALLY WORK?

R2-4079(4) established the limit as a MEASUREMENT: a 1/3-octave band at f is
w(f) = 0.2316*f wide, so a comb of spacing df has two lines in a band only
above 4.318*df, and B7's order-1.5 firing puts the engine's spacing at
275-360 Hz -- unresolvable over the lower 52-63 % of the 500-3000 Hz window.
It reported that per stem and gated nothing on it.

The open question left was: BAND-WIDTH-AWARE TERM, OR GENUINE LIMIT? This
bench answers it by building the term and measuring whether it works, rather
than by deciding which sentence to write.

WHY IT IS NOT SIMPLY "USE WIDER BANDS". `per_band_sfm` is 1/3-octave for a
reason: flatness INSIDE a narrow band is immune to broad tilt, which is what
makes C7 (the delivered master plus a tilt) unable to move G-FLAT. Widening
the band re-admits tilt: the geometric mean of a sloped spectrum falls below
its arithmetic mean, so a TILTED NOISE stem would start reading tonal. Any
band-width-aware term must therefore restore tilt-freeness explicitly.

So the candidate measured here is DETRENDED WIDE-BAND SFM:

  * bin spacing fine enough to resolve the stem's own comb (win chosen so that
    df spans >= 8 bins, instead of SFM_WIN = 2048, which at the stems' 96 kHz
    gives 46.9 Hz bins and SKIPS every 1/3-octave band below ~1 kHz for having
    fewer than 5 bins in it);
  * band width = max(1/3 octave, 4.318 * df) -- wide enough to hold two lines
    of the comb the stem itself declares;
  * inside each band the smooth shape is removed from the log spectrum before
    the flatness is taken, so tilt cannot enter at any bandwidth.

The test is not "does the engine's number go down". It is:

    (a) white noise must still read ~1.00 x W          (the reference)
    (b) genuinely noisy stems must stay >= 0.60 x W    (no false tonality)
    (c) a TILTED noise stem must stay >= 0.60 x W      (tilt-freeness kept)
    (d) the engine must fall clearly below 0.60 x W    (the thing at issue)

A term that does (d) but not (a)-(c) is a broken instrument that happens to
give the answer that was wanted, and is not shipped.

    .venv/bin/python -m tools.r2_4081_bandwidth_sfm
"""

import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal as sig

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEMS = os.path.join(ROOT, "audio", "out", "r2_4079", "stems")
OUT = os.path.join(ROOT, "audio", "out", "r2_4081", "bandwidth_sfm.json")
F_LO, F_HI = 500.0, 3000.0


def detrended_band_sfm(mono, sr, spacing_hz=None, win=None, f_lo=F_LO,
                       f_hi=F_HI, min_bins=8):
    """Per-band SFM with the band width tied to the source's own comb spacing
    and the band's own tilt removed before the flatness is taken."""
    df_target = spacing_hz if (spacing_hz and np.isfinite(spacing_hz)) else 0.0
    if win is None:
        # 8 bins per comb period, rounded up to a power of two
        need = 8.0 * sr / max(df_target, 60.0)
        win = int(2 ** int(np.ceil(np.log2(max(need, 4096)))))
        win = min(win, 65536)
    Pw, f = P._stft_power(mono, sr, win=win)
    if Pw.shape[0] < 1:
        return float("nan"), win, 0
    bw_min = 4.318 * df_target * 0.2316 if df_target else 0.0
    vals, nb = [], 0
    fc = f_lo
    while fc <= f_hi:
        w13 = 0.2316 * fc
        w = max(w13, bw_min)
        lo, hi = fc - w / 2, fc + w / 2
        m = (f >= lo) & (f < hi)
        if m.sum() >= min_bins:
            Pb = np.maximum(Pw[:, m], 1e-30)
            e = Pb.mean(axis=1)
            live = e > max(float(np.percentile(e, 95)) * 10 ** (-5.0), 1e-28)
            if live.sum() >= 4:
                Pb = Pb[live]
                L = np.log(Pb)
                k = int(max(min(m.sum() // 2 * 2 - 1, 31), 5))
                if k < L.shape[1]:
                    L = L - sig.savgol_filter(L, k, 2, axis=1)
                sfm = np.exp(L.mean(axis=1)) / np.maximum(np.exp(L).mean(axis=1),
                                                          1e-30)
                vals.append(float(np.mean(sfm)))
                nb += 1
        fc *= 2 ** (1.0 / 3.0)
    return (float(np.mean(vals)) if vals else float("nan")), win, nb


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    sheet = json.load(open(os.path.join(ROOT, "docs", "beat_sheet.json")))
    names = [f[:-4] for f in sorted(os.listdir(STEMS)) if f.endswith(".wav")]
    y0, sr = sf.read(os.path.join(STEMS, "engine.wav"), dtype="float32",
                     always_2d=True)
    beats = P.beats_from_sheet(sheet, len(y0) / sr)
    rng = np.random.default_rng(90210)
    n = int(8.0 * sr)

    # ---- the reference and the tilt control -------------------------------
    w = rng.standard_normal(n)
    W_shipped = P.per_band_sfm(w, sr)
    W_new, win_w, nb_w = detrended_band_sfm(w, sr, 300.0)
    sos = sig.butter(2, 1200.0 / (sr / 2), btype="low", output="sos")
    tilt = sig.sosfilt(sos, w) + 0.2 * w
    t_shipped = P.per_band_sfm(tilt, sr) / W_shipped
    t_new = detrended_band_sfm(tilt, sr, 300.0)[0] / W_new

    print(f">> white reference: shipped W = {W_shipped:.4f} "
          f"(win {P.SFM_WIN});  detrended wide-band W = {W_new:.4f} "
          f"(win {win_w}, {nb_w} bands)")
    print(f">> (a) white through each pipeline reads 1.000 x its own W by "
          f"construction")
    print(f">> (c) TILTED noise: shipped {t_shipped:.3f} x W   "
          f"detrended wide-band {t_new:.3f} x W   "
          f"(both must stay >= 0.60)\n")

    rep = {"W_shipped": W_shipped, "W_new": W_new,
           "tilt_control": {"shipped": t_shipped, "new": t_new}, "stems": {}}

    print("    beat        stem            spacing   shipped SFM   "
          "detrended wide-band   near-white at 0.60?")
    for bname in ("2_launch", "4_transit", "5_lap"):
        b = [x for x in beats if x.name == bname][0]
        a, z = int(b.t0 * sr), int(b.t1 * sr)
        for nm in names:
            yy, _ = sf.read(os.path.join(STEMS, nm + ".wav"), dtype="float32",
                            always_2d=True)
            seg = yy[a:z].mean(axis=1)
            if float((seg ** 2).mean()) < 1e-14:
                continue
            cs = P.comb_spacing_of(seg, sr)
            s_old = P.per_band_sfm(seg, sr) / W_shipped
            s_new = detrended_band_sfm(seg, sr, cs["spacing_hz"])[0] / W_new
            rep["stems"].setdefault(bname, {})[nm] = {
                "spacing_hz": cs["spacing_hz"], "shipped": s_old, "new": s_new}
            if nm in ("engine", "wind", "bed", "crowd", "tyres",
                      "reflect_garage", "brakes"):
                mark = ("near-white" if s_new >= 0.60 else "TONAL")
                print(f"    {bname:11s} {nm:15s} {cs['spacing_hz']:6.1f} Hz   "
                      f"{s_old:8.3f}      {s_new:12.3f}          {mark}")
        print()

    json.dump(rep, open(OUT, "w"), indent=1, default=float)
    print(f">> wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
