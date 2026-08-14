"""WATCH EACH DEFECT FAIL BEFORE IT IS FIXED (R2-4031).

    .venv/bin/python tools/r2_4030_defect_witness.py [--json out.json]

Seven defects, each measured from the code as it stands rather than quoted from
a report. Re-running this after the fix is what shows the number moving. None of
these needs a 27-minute render: they are unit measurements on the generators and
on the chain's own filters.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from scipy import signal as _sig

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from audio import dsp, layers          # noqa: E402
from audio.clock import Clock, WorldGrid  # noqa: E402

SR = 96000


def w1_kweighting():
    """(B) The gain-staging meter is deaf to the frequencies the mix is made of."""
    (b1, a1), (b2, a2) = dsp._k_weighting(SR)
    out = {}
    for f in (5.0, 10.0, 13.0, 20.0, 30.0, 60.0, 1000.0):
        w = [2 * np.pi * f / SR]
        h = _sig.freqz(b1, a1, worN=w)[1] * _sig.freqz(b2, a2, worN=w)[1]
        out["%g_hz_db" % f] = float(20 * np.log10(abs(h[0]) + 1e-30))
    return out


def w2_limiter_loop():
    """(3) The 8-pass loop reassigns `gr`, so only the gentlest pass is reported."""
    rng = np.random.default_rng(4021)
    n = SR * 4
    x = rng.standard_normal((n, 2)) * 0.02
    # a bass-heavy transient bus, exactly the shape the impact bus arrives in
    t = np.arange(n) / SR
    for c in (0, 1):
        x[:, c] += 7.5 * np.sin(2 * np.pi * 22.0 * t) * np.exp(-((t - 1.0) / 0.25) ** 2)
    per_pass = []
    y = x.copy()
    gr = 0.0
    for _ in range(8):
        L, _s, _ = dsp.loudness_lufs(y, SR)
        if abs(L + 14.0) < 0.05:
            break
        y *= float(10.0 ** ((-14.0 - L) / 20.0))
        y, gr = dsp.soft_limit(y, ceiling=10.0 ** (-1.15 / 20.0), sr=SR)
        per_pass.append(float(gr))
    return {"per_pass_gr_db": per_pass,
            "reported_gr_db_last_pass": float(gr),
            "true_max_gr_db": float(min(per_pass)) if per_pass else 0.0,
            "hidden_by_db": float(gr - min(per_pass)) if per_pass else 0.0}


def w3_limiter_preduck():
    """(4.1.3) `soft_limit` ducks BEFORE the peak: minimum_filter1d + filtfilt."""
    n = SR
    # a steady 0.5 bed so the applied gain is recoverable at EVERY sample, with
    # one sample 8x over the ceiling sitting in the middle of it
    x = np.full(n, 0.5)
    x[n // 2] = 4.0
    y, gr = dsp.soft_limit(x, ceiling=0.891, sr=SR)
    gs = np.asarray(y, dtype=np.float64) / x
    dip = gs < 0.99
    idx = np.flatnonzero(dip)
    i0, i1 = int(idx[0]), int(idx[-1])
    return {"gain_dip_starts_ms_before_peak": float((n // 2 - i0) / SR * 1e3),
            "gain_dip_ends_ms_after_peak": float((i1 - n // 2) / SR * 1e3),
            "total_hole_ms": float((i1 - i0) / SR * 1e3),
            "min_gain_db": float(20 * np.log10(gs.min())),
            "reported_gr_db": float(gr)}


def w3b_click_crest():
    """(G4 control) a 0.2 ms click of known crest through the limiter: the crest
    loss must be <= 3 dB. This is the gate's own degenerate control."""
    n = SR
    rng = np.random.default_rng(4023)
    x = rng.standard_normal(n) * 0.02
    L = max(int(0.0002 * SR), 2)
    x[n // 2:n // 2 + L] += 3.0 * np.hanning(L)

    def crest(v):
        w = int(SR * 0.05)
        i = n // 2 - w // 2
        s = np.asarray(v, dtype=np.float64)[i:i + w]
        return 20 * np.log10(np.abs(s).max() / np.sqrt((s ** 2).mean()))
    y, gr = dsp.soft_limit(x, ceiling=0.891, sr=SR)
    return {"crest_in_db": float(crest(x)), "crest_out_db": float(crest(y)),
            "crest_loss_db": float(crest(x) - crest(y)), "gr_db": float(gr)}


def w4_plate_modes():
    """(2.1) The pane generates nothing above 4718 Hz whatever `fmax` says."""
    out = {}
    for fmax in (1600.0, 18000.0):
        m = layers.plate_modes(2.125, 5.600, layers.GLASS_H, fmax=fmax)
        fs = np.array([q[0] for q in m])
        out["fmax_%d" % int(fmax)] = {
            "n_modes": len(m), "f_min": float(fs.min()), "f_max": float(fs.max()),
            "n_above_4718": int((fs > 4718.0).sum()),
            "modes_per_hz_over_range": float(len(m) / max(fs.max() - fs.min(), 1e-9)),
        }
    # the analytic density the spec derives: dN/df = pi*a*b/(4k)
    D = layers.GLASS_E * layers.GLASS_H ** 3 / (12.0 * (1 - layers.GLASS_NU ** 2))
    k = (np.pi / 2.0) * np.sqrt(D / (layers.GLASS_RHO * layers.GLASS_H))
    out["analytic"] = {"D_Nm": float(D), "rho_h": float(layers.GLASS_RHO * layers.GLASS_H),
                       "k": float(k),
                       "modes_per_hz": float(np.pi * 2.125 * 5.600 / (4.0 * k)),
                       "modes_below_20k": float(np.pi * 2.125 * 5.600 / (4.0 * k) * 20000.0)}
    out["q_loss_factor_now"] = {"q": 45.0, "eta": 1.0 / 45.0,
                                "t60_at_3k_s": float(2.2 * 45.0 / (np.pi * 3000.0))}
    return out


def w5_shard_amplitude_law():
    """(2.2 A/C) amp ~ 1/f, the ten loudest contacts all ring at the size clamp,
    and every shard below 26.6 mm renders as digital silence."""
    ev, summ = layers.shard_ballistics(
        json.load(open(os.path.join(ROOT, "docs", "circuit_spec.json"))), 16.709)
    L_silent = float(np.sqrt(0.47 * layers.GLASS_H * layers.GLASS_CL / (SR * 0.45)))
    legacy = len(ev[0]) == 5 and np.ndim(ev[0][2]) == 1
    if legacy:                                   # (t, p, freqs, amp, decay)
        f1 = np.array([e[2][0] for e in ev])
        amp = np.array([e[3] for e in ev])
        energy = amp ** 2 * np.array([e[4] for e in ev])
        nmodes = int(len(ev[0][2]))
        sizes = np.full(f1.shape, np.nan)
    else:                                        # (t, p, sid, vz, bounce, L)
        # the AMPLITUDE LAW as it now stands: per-mode drive x contact-force
        # spectrum x radiation efficiency x the size high-pass, summed
        sizes = np.array([e[5] for e in ev])
        vz = np.array([e[3] for e in ev])
        sids = np.array([e[2] for e in ev])
        mrng = np.random.default_rng(31337 + 7)
        n_sh = int(sids.max()) + 1
        by_sid = {}
        for s in range(n_sh):
            m = np.flatnonzero(sids == s)
            by_sid[s] = float(sizes[m[0]]) if m.size else 0.05
        modes = [layers.shard_modes(by_sid[s], mrng) for s in range(n_sh)]
        f1, amp, nmodes = [], [], []
        for k, (_t, _p, sid, vzi, bounce, L) in enumerate(ev):
            f, a_mode, _tau, _q = modes[sid]
            t_contact = 8e-5 * (1.0 + 0.6 * bounce) * (1.0 + 2.0 * L)
            drive = layers.GLASS_RHO * layers.GLASS_H * L * L * max(vzi, 1e-4)
            a = (a_mode * layers.hertz_spectrum(f, t_contact)
                 * np.asarray(layers.rad_amp(f))
                 * layers._size_highpass(f, L)) * drive
            f1.append(float(f[0]))
            amp.append(float(np.abs(a).max()))
            nmodes.append(int(f.size))
        f1 = np.array(f1)
        amp = np.array(amp)
        energy = amp ** 2
        nmodes = float(np.mean(nmodes))
    order = np.argsort(energy)[::-1]
    top10 = order[:10]
    out = {
        "contacts": len(ev), "shards": summ["shards"], "legacy_event_tuple": legacy,
        "corr_log_amp_vs_log_f1": float(np.corrcoef(np.log(amp + 1e-30), np.log(f1))[0, 1]),
        "slope_log_amp_vs_log_f1": float(np.polyfit(np.log(f1), np.log(amp + 1e-30), 1)[0]),
        "top10_energy_share_pct": float(100.0 * energy[top10].sum() / energy.sum()),
        "top10_f1_hz": [float(v) for v in f1[top10]],
        "energy_share_below_500hz_pct": float(100.0 * energy[f1 < 500].sum() / energy.sum()),
        "energy_share_above_2k_pct": float(100.0 * energy[f1 > 2000].sum() / energy.sum()),
        "silent_below_L_m": L_silent,
        "contacts_fully_silent_pct": float(100.0 * (f1 >= SR * 0.45).mean()),
        "modes_per_contact": nmodes,
    }
    if not legacy:
        # G9: log f1 against log L must have slope -2.0 +- 0.1, which is the
        # signature of a size law rather than an authored frequency table
        out["G9_slope_logf1_vs_logL"] = float(np.polyfit(np.log(sizes), np.log(f1), 1)[0])
        # G10: per-mode Q of one rendered shard
        _f, _a, _tau, q = layers.shard_modes(0.15, np.random.default_rng(1))
        out["G10_shard_q"] = float(q)
        out["G10_q_from_tau"] = [float(t * np.pi * fq) for t, fq in zip(_tau[:4], _f[:4])]
    return out


def w6_warp_transposition():
    """(A) `warp()` is a varispeed resampler: the internal control is the same
    generator either side of the ramp boundary."""
    clock = Clock(os.path.join(ROOT, "docs", "beat_sheet.json"), sr=SR)
    grid = WorldGrid(clock)
    # a fixed 1 kHz tone on the world grid, warped -- pitch out is pitch in x scale
    tone = np.sin(2 * np.pi * 1000.0 * grid.t).astype(np.float32)
    f = grid.to_film(tone)

    def centroid(t0, t1):
        seg = f[int(t0 * SR):int(t1 * SR)].astype(np.float64)
        fr, p = _sig.welch(seg, SR, nperseg=1 << 14)
        return float(np.trapezoid(p * fr, fr) / max(float(np.trapezoid(p, fr)), 1e-30))
    return {"scale_min": float(clock.scale.min()),
            "transposition_x": float(1.0 / clock.scale.min()),
            "semitones_down": float(12 * np.log2(1.0 / clock.scale.min())),
            "1khz_tone_centroid_hz_41_43s": centroid(41.0, 43.0),
            "1khz_tone_centroid_hz_44_45s": centroid(44.0, 45.2),
            "glass_film_t": float(clock.film_at_world(clock.glass_world_t))}


def w7_stem_spectra():
    """The shipped stems, if they are on disk: the shard generator's centroid
    inside the ramp versus the instant it ends."""
    p = os.path.join(ROOT, "audio", "out", "stems", "shards.wav")
    if not os.path.exists(p):
        return {"note": "no stems on disk"}
    import soundfile as sf
    out = {}
    for a, b in ((41.0, 43.0), (43.0, 44.0), (44.0, 45.2)):
        x, sr = sf.read(p, start=int(a * 96000), frames=int((b - a) * 96000), always_2d=True)
        m = x.mean(axis=1)
        fr, pp = _sig.welch(m, sr, nperseg=1 << 14)
        out["centroid_%g_%g_s" % (a, b)] = float(
            np.trapezoid(pp * fr, fr) / max(float(np.trapezoid(pp, fr)), 1e-30))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    r = {}
    for name, fn in (("k_weighting", w1_kweighting),
                     ("limiter_loop", w2_limiter_loop),
                     ("limiter_preduck", w3_limiter_preduck),
                     ("limiter_click_crest", w3b_click_crest),
                     ("plate_modes", w4_plate_modes),
                     ("shard_amplitude_law", w5_shard_amplitude_law),
                     ("warp", w6_warp_transposition),
                     ("stems", w7_stem_spectra)):
        print("... %s" % name, flush=True)
        r[name] = fn()
    print(json.dumps(r, indent=1, default=float))
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(r, fh, indent=1, default=float)
        print(">> %s" % a.json)


if __name__ == "__main__":
    main()
