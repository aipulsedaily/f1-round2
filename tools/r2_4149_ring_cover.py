#!/usr/bin/env python
"""R2-4149 -- G-RING LOST ITS BEAT-1 MEASUREMENT. IS THERE A DECAY THERE AT ALL?

R2-4148 recorded the cost of making beat 1 audible honestly: G-RING's usable
decay regions went 4 -> 2 -> INAPPLICABLE, and its warning was that you cannot
measure ISO 3382 T20 in an operating factory. A GATE THAT HAS STOPPED
MEASURING IS NOT A GATE THAT PASSES, so this asks the question that decides
between the two possible findings:

  (a) THE DETECTOR is the limit -- the decays are there and `decay_regions`
      cannot see them -- in which case coverage can be restored; or
  (b) THE STANDARD is the limit -- the gaps do not contain the 12 dB fall
      ISO 3382 T20 needs -- in which case beat 1 genuinely has no measurable
      decay and that is the finding, recorded rather than papered over.

The discriminator is arithmetic and it is measured per band, because that is
where the answer differs from the broadband picture: `percept.decay_regions`
finds gaps in the BROADBAND envelope and `band_decay_t60` then reads every
1/6-octave band inside those same gaps. A room's ring-through is a PER-BAND
quantity and a band can be decaying through 20 dB while the broadband envelope
sits on a floor that another band is holding up. ISO 3382 measures the decay of
a band in that band; it does not borrow another band's gap.

    .venv/bin/python -m tools.r2_4149_ring_cover --wav <master.wav>
"""

import argparse
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal as sg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(wav):
    x, sr = sf.read(wav, always_2d=True)
    return P.to_mono(x), sr


def beat_seg(mono, sr, name):
    import json
    sheet = json.load(open(os.path.join(ROOT, "docs", "beat_sheet.json")))
    for b in P.beats_from_sheet(sheet, len(mono) / sr):
        if b.name == name:
            return P._slice(mono, sr, b), b
    raise SystemExit("no beat " + name)


def broadband_headroom(seg, sr, prominence_db=6.0):
    """WHAT FALL IS ACTUALLY AVAILABLE after each broadband peak. ISO 3382 T20
    needs 25 dB of usable range (-5 to -25); `band_decay_t60` demands 12 dB of
    fall in the backward integral. This reports the raw material."""
    e, fs = P.broadband_envelope(seg, sr, env_hz=200.0)
    le = 20.0 * np.log10(np.maximum(e, 1e-12))
    k = min(int(0.05 * fs) | 1, (len(le) // 2) * 2 - 1)
    if k >= 5:
        le = sg.savgol_filter(le, k, 2)
    pk, _ = sg.find_peaks(le, prominence=prominence_db,
                          distance=max(int(0.30 * fs), 1))
    drops, gaps = [], []
    for i, p in enumerate(pk):
        a = p + int(0.05 * fs)
        stop = pk[i + 1] if i + 1 < len(pk) else len(le)
        if stop - a < 4:
            continue
        drops.append(float(le[a] - le[a:stop].min()))
        gaps.append(float((stop - a) / fs))
    # HOW LONG THE ENVELOPE ACTUALLY FALLS. `decay_regions` ends a region at
    # the first point 3 dB above the running minimum since the peak, and then
    # discards it if what is left is under 0.30 s. That single number is the
    # difference between 4 regions and INAPPLICABLE, so it is measured here.
    falls = []
    for i, p in enumerate(pk):
        a = p + int(0.05 * fs)
        stop = min(pk[i + 1] if i + 1 < len(pk) else len(le),
                   a + int(1.5 * fs), len(le))
        if stop - a < 4:
            continue
        s = le[a:stop]
        rmin = np.minimum.accumulate(s)
        rise = np.nonzero(s > rmin + 3.0)[0]
        falls.append(float((int(rise[0]) if rise.size else len(s)) / fs))
    return {"n_peaks": int(len(pk)), "drop_db": np.array(drops),
            "gap_s": np.array(gaps), "fall_s": np.array(falls),
            "p5_le": float(np.percentile(le, 5)),
            "p95_le": float(np.percentile(le, 95))}


def band_envelope(band, sr, env_hz=200.0):
    """The band's OWN envelope. `percept.broadband_envelope` band-passes
    150-8000 Hz before it looks, which is right for a broadband envelope and
    wrong for a 1/6-octave one -- it would filter a 200 Hz band twice and let a
    5.7 kHz band's neighbours in. Everything after the bandpass is identical:
    Hilbert magnitude, anti-alias, decimate to `env_hz`."""
    e = np.abs(sg.hilbert(np.asarray(band, dtype=np.float64)))
    q = max(int(round(sr / env_hz)), 1)
    ne = len(e) // q
    if ne < 8:
        return np.zeros(0), env_hz
    e = sg.sosfiltfilt(sg.butter(6, 0.4 * env_hz, btype="low", fs=sr,
                                 output="sos"), e)
    return e[:ne * q].reshape(ne, q).mean(axis=1), sr / q


def band_regions(band, sr, min_s=0.30, max_s=1.5, prominence_db=6.0,
                 env_hz=200.0):
    """The same region rule as `percept.decay_regions`, run ON ONE BAND rather
    than on the broadband envelope. Nothing here is loosened: the same 6 dB
    peak prominence, the same 0.30 s minimum, the same 3 dB stop rule."""
    e, fs = band_envelope(band, sr, env_hz=env_hz)
    if len(e) < 64:
        return []
    le = 20.0 * np.log10(np.maximum(e, 1e-12))
    k = min(int(0.05 * fs) | 1, (len(le) // 2) * 2 - 1)
    if k >= 5:
        le = sg.savgol_filter(le, k, 2)
    pk, _ = sg.find_peaks(le, prominence=prominence_db,
                          distance=max(int(0.30 * fs), 1))
    out = []
    for i, p in enumerate(pk):
        a = p + int(0.05 * fs)
        stop = pk[i + 1] if i + 1 < len(pk) else len(le)
        b = min(a + int(max_s * fs), stop, len(le))
        if b - a < int(min_s * fs):
            continue
        seg = le[a:b]
        rmin = np.minimum.accumulate(seg)
        rise = np.nonzero(seg > rmin + 3.0)[0]
        if rise.size:
            b = a + int(rise[0])
        if (b - a) / fs >= min_s:
            out.append((int(a / fs * sr), int(b / fs * sr)))
    return out


def per_band_t60(seg, sr, f_lo=200.0, f_hi=6000.0, max_regions=14):
    """T20 x 3 per 1/6 octave, measured in EACH BAND'S OWN gaps."""
    rows = []
    fc = f_lo
    while fc <= f_hi:
        lo, hi = fc / 2 ** (1 / 12.0), fc * 2 ** (1 / 12.0)
        if hi >= sr * 0.45:
            break
        sos = sg.butter(4, [lo, hi], btype="bandpass", fs=sr, output="sos")
        b = sg.sosfilt(sos, seg)
        regs = band_regions(b, sr)[:max_regions]
        sl, drops = [], []
        for a0, b0 in regs:
            s = np.asarray(b[a0:b0], dtype=np.float64)
            if len(s) < int(0.20 * sr):
                continue
            q = max(int(sr / 400.0), 1)
            ne = len(s) // q
            if ne < 12:
                continue
            p2 = (s[:ne * q] ** 2).reshape(ne, q).mean(axis=1)
            E = np.cumsum(p2[::-1])[::-1]
            le = 10.0 * np.log10(np.maximum(E / max(E[0], 1e-30), 1e-12))
            t = np.arange(ne) / (sr / q)
            m = (le <= -5.0) & (le >= -25.0)
            if m.sum() < 8:
                continue
            A = np.polyfit(t[m], le[m], 1)
            span = float(t[m].max() - t[m].min())
            drop = -A[0] * span
            resid = le[m] - np.polyval(A, t[m])
            var = float(np.var(le[m]))
            r2 = 1.0 - float(np.var(resid)) / var if var > 1e-12 else 0.0
            drops.append(drop)
            if A[0] < -3.0 and drop >= 12.0 and r2 >= 0.90:
                sl.append(-60.0 / A[0])
        rows.append({"f_hz": fc, "n_regions": len(regs),
                     "n_usable": len(sl),
                     "t60_s": float(np.median(sl)) if sl else float("nan"),
                     "best_drop_db": float(max(drops)) if drops else 0.0})
        fc *= 2 ** (1 / 6.0)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav", default=os.path.join(
        ROOT, "audio", "out", "r2_4147", "master_R2-4147.wav"))
    ap.add_argument("--beat", default="1_assembly")
    a = ap.parse_args()

    mono, sr = load(a.wav)
    seg, b = beat_seg(mono, sr, a.beat)
    print("%s  %s  %.1f-%.1f s" % (os.path.relpath(a.wav, ROOT), b.name,
                                   b.t0, b.t1))
    print()

    h = broadband_headroom(seg, sr)
    print("WHAT THE BROADBAND ENVELOPE OFFERS")
    print("  peaks at 6 dB prominence, 0.30 s apart: %d" % h["n_peaks"])
    if h["drop_db"].size:
        d = np.sort(h["drop_db"])[::-1]
        print("  fall available after each peak, dB: max %.1f  median %.1f  "
              "min %.1f" % (d[0], float(np.median(d)), d[-1]))
        print("  peaks whose gap holds the 12 dB ISO 3382 needs: %d of %d"
              % (int((h["drop_db"] >= 12.0).sum()), h["drop_db"].size))
        print("  gap length, s: median %.3f" % float(np.median(h["gap_s"])))
        f = h["fall_s"]
        print("  the envelope keeps FALLING for, s: max %.3f  median %.3f"
              % (float(f.max()), float(np.median(f))))
        print("  peaks whose fall lasts the 0.30 s a region needs: %d of %d"
              % (int((f >= 0.30).sum()), f.size))
    print("  broadband envelope p95 - p5: %.1f dB"
          % (h["p95_le"] - h["p5_le"]))
    print()

    regs = P.decay_regions(seg, sr)
    print("G-RING AS IT STANDS -- regions from the BROADBAND envelope: %d "
          "(needs 3)" % len(regs))
    if regs:
        d = P.band_decay_t60(seg, sr, regs)
        t = [r["t60_s"] for r in d["bands"] if np.isfinite(r["t60_s"])]
        print("  bands with a measurable decay inside them: %d (needs 6)"
              % len(t))
    print()

    rows = per_band_t60(seg, sr)
    ok = [r for r in rows if np.isfinite(r["t60_s"])]
    print("PER-BAND REGIONS -- each band's decay measured in ITS OWN gaps, "
          "same rules")
    print("%9s %9s %9s %10s %11s" % ("f Hz", "regions", "usable", "T60 s",
                                     "best drop"))
    for r in rows:
        print("%9.0f %9d %9d %10s %11.1f"
              % (r["f_hz"], r["n_regions"], r["n_usable"],
                 "%.3f" % r["t60_s"] if np.isfinite(r["t60_s"]) else "-",
                 r["best_drop_db"]))
    print()
    print("bands with a measurable T60: %d of %d" % (len(ok), len(rows)))
    if ok:
        t = np.array([r["t60_s"] for r in ok])
        print("  median %.3f s   worst %.3f s at %.0f Hz"
              % (float(np.median(t)), float(t.max()),
                 ok[int(np.argmax(t))]["f_hz"]))
        sab = P.sabine_rt60(P.SHOWROOM_INTERIOR_M, P.SHOWROOM_DECLARED_RT60_S)
        print("  Sabine %.2f s; worst/median = %.3f"
              % (sab["rt60_s"], float(t.max() / np.median(t))))


if __name__ == "__main__":
    main()
