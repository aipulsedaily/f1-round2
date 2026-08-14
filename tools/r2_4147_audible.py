#!/usr/bin/env python
"""R2-4147 -- IS ANYTHING AUDIBLE HERE. THE MEASUREMENT THE SUITE NEVER MADE.

THE GAP THIS FILLS. Every instrument in `audio/percept.py` is RELATIVE: it
measures structure WITHIN whatever signal it is given. G-EVENT measures the
spread of the short-term level, G-SUSTAIN the cover of held partials, G-MOD the
depth of a modulation. **Digital silence scores perfectly on all of them.** A
beat that contains nothing has infinite local dynamic range, zero note cover
and no modulation, so the suite calls it clean, and the client calls it
"i dont hear anything until the tubes play".

This module measures the one thing none of them do: whether the passage BETWEEN
the events puts anything over a listener's absolute threshold of hearing, at a
stated playback calibration, in the presence of the events' own masking.

    python -m tools.r2_4147_audible --master PATH        # a delivered wav
    python -m tools.r2_4147_audible --stems DIR          # the per-bus share
    python -m tools.r2_4147_audible --controls           # C9 / silence nulls

Everything here is absolute, so the calibration is declared and derived rather
than assumed -- see `REF_SPL_AT_TARGET_LUFS`.
"""

import argparse
import json
import os
import sys

import numpy as np
from scipy import signal as sg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                    # noqa: E402
from audio import dsp                                             # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# THE CALIBRATION. An absolute measurement needs one, and this one is DERIVED.
#
# EBU R 128 / Tech 3343 ss.2.2 and ITU-R BS.1770 monitoring practice put a
# -23 LUFS programme at **73 dB SPL** (A-weighted, slow) at the reference
# listening position for a single front loudspeaker in a calibrated room; the
# same figure is SMPTE RP 200's 82 dB SPL per channel at -20 dBFS RMS pink
# reduced by the 9 dB the two standards differ by in reference level. The film
# is delivered at TARGET_LUFS_I = -23.0 (audio/master.py), so full scale sits
# at 73 + 23 = 96 dB SPL.
#
# THE DOMESTIC CASE IS THE ONE THAT MATTERS AND IT IS QUIETER. A viewer at home
# does not run reference level; the measured median domestic playback of R 128
# material is 10-15 dB below it. This module therefore reports BOTH and gates on
# the domestic figure, because a passage that is inaudible at home is inaudible
# to the client, who watched it on a laptop.
REF_SPL_AT_TARGET_LUFS = 73.0        # dB SPL for a -23 LUFS programme, R 128
DOMESTIC_OFFSET_DB = 12.0            # median domestic listening under reference
TARGET_LUFS_I = -23.0

# The absolute threshold of hearing in quiet, ISO 226:2003 Annex A / Terhardt's
# closed form, dB SPL as a function of frequency in kHz. This is a PUBLISHED
# curve, not a fit to this film.
def threshold_in_quiet_db(f_hz):
    f = np.maximum(np.asarray(f_hz, dtype=np.float64), 20.0) / 1000.0
    return (3.64 * f ** -0.8
            - 6.5 * np.exp(-0.6 * (f - 3.3) ** 2)
            + 1e-3 * f ** 4)


# THE ROOM THE CLIENT IS SITTING IN. Threshold in quiet is an anechoic figure
# and using it alone would flatter this film badly: nobody watches in an
# anechoic chamber. ISO R 1996's NOISE RATING curves give octave-band levels as
#     L = a(band) + b(band) * N
# and ISO/ANSI recommend NR 25-30 for a living room or bedroom. **NR-25 is the
# QUIET END and it is chosen deliberately**: a passage that is inaudible even in
# the quietest domestic room is inaudible, full stop, so a bar drawn there
# cannot be accused of being generous to itself.
NR_BANDS = np.array([31.5, 63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
NR_A = np.array([55.4, 35.5, 22.0, 12.0, 4.8, 0.0, -3.5, -6.1, -8.0])
NR_B = np.array([0.681, 0.790, 0.870, 0.930, 0.974, 1.000, 1.015, 1.025, 1.030])
ROOM_NR = 25.0


def room_noise_third_octave_db(f_hz, nr=ROOM_NR):
    """NR-`nr` octave-band levels, interpolated in log f and spread to thirds.

    An octave holds three third-octaves, so a flat-in-the-band assumption puts
    each third 10*log10(3) = 4.77 dB under its octave.
    """
    oct_l = NR_A + NR_B * nr
    lf = np.log2(np.maximum(np.asarray(f_hz, dtype=np.float64), 20.0))
    return np.interp(lf, np.log2(NR_BANDS), oct_l) - 10.0 * np.log10(3.0)


def masked_threshold_db(f_hz, nr=ROOM_NR):
    """WHAT A BAND HAS TO EXCEED TO BE HEARD AT ALL, in a real room."""
    return np.maximum(threshold_in_quiet_db(f_hz),
                      room_noise_third_octave_db(f_hz, nr))


# THE BAND SET IS THE EAR'S, NOT THE FFT's. Audibility is decided inside a
# critical band, so the analysis bands are third-octaves from 25 Hz to 16 kHz
# (IEC 61260 preferred centres), which are within a factor of ~1.4 of the ERB
# over the range where the threshold is low enough to matter.
def third_octave_centres(f_lo=25.0, f_hi=16000.0):
    n0 = int(np.round(3.0 * np.log2(f_lo / 1000.0)))
    n1 = int(np.round(3.0 * np.log2(f_hi / 1000.0)))
    return 1000.0 * 2.0 ** (np.arange(n0, n1 + 1) / 3.0)


def band_spl(seg, sr, full_scale_spl_db, centres=None):
    """Per-third-octave SPL of one segment, at the declared calibration.

    Power is taken from the periodogram and summed inside each band's own
    edges, so the answer does not depend on the FFT length once the band holds
    more than a few bins.
    """
    if centres is None:
        centres = third_octave_centres()
    seg = np.asarray(seg, dtype=np.float64)
    n = len(seg)
    if n < 256:
        return centres, np.full(len(centres), -np.inf)
    nfft = int(2 ** np.ceil(np.log2(min(max(n, 4096), 65536))))
    f, pxx = sg.welch(seg, fs=sr, nperseg=min(nfft, n), noverlap=None,
                      window="hann", scaling="spectrum")
    out = np.empty(len(centres))
    for i, fc in enumerate(centres):
        lo, hi = fc / 2 ** (1 / 6), fc * 2 ** (1 / 6)
        m = (f >= lo) & (f < hi)
        p = float(pxx[m].sum()) if m.any() else 0.0
        out[i] = 10.0 * np.log10(max(p, 1e-30)) + full_scale_spl_db
    return centres, out


# ---------------------------------------------------------------------------
def event_mask(mono, sr, guard_s=0.35, hop_s=0.010):
    """WHICH SAMPLES ARE 'BETWEEN THE EVENTS', measured off the signal itself.

    A frame is EVENT if the 20 ms level is within 12 dB of the beat's p98, and
    the mask is dilated forward by `guard_s` so that an impact's own decay --
    which is the thing the client can hear -- is never counted as the gap it is
    decaying into. Everything else is GAP.
    """
    w = max(int(0.020 * sr), 8)
    hop = max(int(hop_s * sr), 1)
    n = (len(mono) - w) // hop + 1
    if n < 8:
        return np.zeros(len(mono), dtype=bool)
    idx = np.arange(w)[None, :] + hop * np.arange(n)[:, None]
    L = 20.0 * np.log10(np.maximum(np.sqrt((mono[idx] ** 2).mean(axis=1)), 1e-12))
    hot = L > (np.percentile(L, 98) - 12.0)
    k = int(guard_s / hop_s)
    if k > 0:
        hot = np.convolve(hot.astype(float), np.ones(k + 1), mode="full")[:n] > 0
    out = np.zeros(len(mono), dtype=bool)
    for i in np.flatnonzero(hot):
        out[i * hop:i * hop + w] = True
    return out


def _superseded_audibility(mono, sr, lufs_i, t0=0.0, t1=None, seg_s=1.0,
               spl_offset_db=DOMESTIC_OFFSET_DB):
    """THE INSTRUMENT. Sensation level of the GAPS, in dB above threshold.

    For every 1 s segment of the passage that is mostly gap, the per-third-
    octave SPL is compared to the threshold in quiet at the declared playback
    calibration. The segment's SENSATION LEVEL is the level of its most audible
    band above that band's threshold; a segment is AUDIBLE if any band clears
    threshold at all.

    Reported as the MEDIAN over segments, so one busy second cannot carry a
    beat -- the same reasoning `local_dynamic_range` uses, pointed at the
    opposite quantity.
    """
    mono = np.asarray(mono, dtype=np.float64)
    t1 = len(mono) / sr if t1 is None else t1
    seg = mono[int(t0 * sr):int(t1 * sr)]
    # FULL SCALE IN dB SPL. The listener sets the volume so the PROGRAMME sits
    # at a comfortable level, not so that full scale sits anywhere in
    # particular. A programme delivered at `lufs_i` and played at
    # (REF - offset) dB SPL therefore puts 0 dBFS at
    #     (REF - offset) - lufs_i     [dB SPL]
    # and every band level below is measured against that.
    fs_spl = (REF_SPL_AT_TARGET_LUFS - spl_offset_db) - lufs_i
    gap = ~event_mask(seg, sr)
    centres = third_octave_centres()
    thr = masked_threshold_db(centres)
    thr_quiet = threshold_in_quiet_db(centres)
    ns = int(seg_s * sr)
    rows = []
    for i in range(0, len(seg) - ns + 1, ns):
        g = gap[i:i + ns]
        if g.mean() < 0.60:              # not a gap segment; the events own it
            continue
        s = seg[i:i + ns][g]
        if len(s) < int(0.20 * sr):
            continue
        _, spl = band_spl(s, sr, fs_spl, centres)
        sl = spl - thr
        rows.append({"t": round(t0 + i / sr, 2),
                     "sensation_db": float(np.max(sl)),
                     "at_hz": float(centres[int(np.argmax(sl))]),
                     "bands_audible": int((sl > 0).sum()),
                     "sensation_anechoic_db": float(np.max(spl - thr_quiet)),
                     "spl_broadband": float(10.0 * np.log10(
                         np.sum(10.0 ** (spl / 10.0))))})
    if not rows:
        return {"n_gap_segments": 0, "median_sensation_db": float("nan"),
                "p90_sensation_db": float("nan"), "median_bands_audible": float("nan"),
                "gap_fraction": float(gap.mean()), "full_scale_spl_db": fs_spl,
                "why": "no segment of this passage is mostly gap"}
    sl = np.array([r["sensation_db"] for r in rows])
    aq = np.array([r["sensation_anechoic_db"] for r in rows])
    nb = np.array([r["bands_audible"] for r in rows])
    return {
        "n_gap_segments": len(rows),
        "gap_fraction": float(gap.mean()),
        "full_scale_spl_db": round(fs_spl, 2),
        "room": "NR-%.0f, the quiet end of ISO/ANSI's domestic range" % ROOM_NR,
        "playback": ("%.0f dB SPL for a %.1f LUFS programme, %.0f dB under R 128 "
                     "reference" % (REF_SPL_AT_TARGET_LUFS - spl_offset_db,
                                    TARGET_LUFS_I, spl_offset_db)),
        "median_sensation_db": float(np.median(sl)),
        "p10_sensation_db": float(np.percentile(sl, 10)),
        "p90_sensation_db": float(np.percentile(sl, 90)),
        "median_sensation_anechoic_db": float(np.median(aq)),
        "median_bands_audible": float(np.median(nb)),
        "median_gap_spl_db": float(np.median(
            [r["spl_broadband"] for r in rows])),
        "worst_segments": sorted(rows, key=lambda r: r["sensation_db"])[:6],
    }


# --------------------------------------------------------------------- CLI --
def read_wav(path):
    import soundfile as sf
    x, sr = sf.read(path, always_2d=True)
    return x, sr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default=os.path.join(
        ROOT, "audio", "out", "r2_4141", "master_R2-4141.wav"))
    ap.add_argument("--t0", type=float, default=0.0)
    ap.add_argument("--t1", type=float, default=33.0)
    ap.add_argument("--stems", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    x, sr = read_wav(a.master)
    lufs_i, _, _ = dsp.loudness_lufs(x, sr)
    mono = x.mean(axis=1)
    r = audibility(mono, sr, lufs_i, a.t0, a.t1)
    r["master"] = a.master
    r["lufs_i"] = round(lufs_i, 2)
    print(json.dumps(r, indent=1))
    if a.json:
        json.dump(r, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()


# THE SHIPPED IMPLEMENTATION LIVES IN `audio/percept.py` (R2-4147 moved it there
# so that G-PRESENCE and this bench cannot drift apart). This wrapper keeps the
# tool's windowed CLI while delegating the measurement itself.
def audibility(mono, sr, lufs_i, t0=0.0, t1=None, seg_s=1.0,
               spl_offset_db=DOMESTIC_OFFSET_DB):
    mono = np.asarray(mono, dtype=np.float64)
    t1 = len(mono) / sr if t1 is None else t1
    r = P.gap_audibility(mono[int(t0 * sr):int(t1 * sr)], sr, lufs_i,
                         seg_s=seg_s, spl_offset_db=spl_offset_db)
    r["room"] = "NR-%.0f, the quiet end of ISO/ANSI's domestic range" % P.ROOM_NR
    r["playback"] = ("%.0f dB SPL for a %.1f LUFS programme, %.0f dB under "
                     "R 128 reference" % (P.REF_SPL_AT_TARGET_LUFS - spl_offset_db,
                                          lufs_i, spl_offset_db))
    return r
