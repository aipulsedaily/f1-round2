"""THE BREACH SOURCE BENCH (R2-4039) -- measure the glass without a 27 min render.

    .venv/bin/python tools/r2_4030_breach_bench.py [--json out.json] [--wav out.wav]

Builds the impact + shard field exactly as `master.py` builds it, on whichever
grid `master.py` currently uses, and measures the 36-44 s window of the SOURCE.
The master chain cannot put high frequencies into a signal that has none, so
every §2 target can be watched moving here, in ~40 seconds, before spending a
render on it.

Reported at both the source's own scale and after a rough per-bus trim, because
the fractions are what matter and they are scale-free.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from scipy import signal as _sig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from audio import layers                       # noqa: E402
from audio.clock import Clock                  # noqa: E402
from tools.r2_4030_master_probe import band_fractions, crest_db, onset_density  # noqa: E402

SR = 96000
BREACH = (36.0, 44.0)


def build_breach_legacy(sr=SR):
    """THE DEGENERATE CONTROL FOR G3: synthesise on the world grid and warp,
    which is what `master.py` did before R2-4035. This must measure infrasonic."""
    from audio.clock import WorldGrid
    spec = json.load(open(os.path.join(ROOT, "docs", "circuit_spec.json")))
    clock = Clock(os.path.join(ROOT, "docs", "beat_sheet.json"), sr=sr)
    grid = WorldGrid(clock)
    from audio.scene import Telemetry
    tel = Telemetry(spec=spec)
    v_contact = float(np.interp(11.98, tel.col["s_m"], tel.v_world))
    ev, summ = layers.shard_ballistics(spec, v_contact)
    tw = grid.t
    imp_w, imp_info = layers.impact_event(tw, clock.glass_world_t, sr, v_contact)
    # the old world-grid schedule: onset index (t_impact + t - t0) * sr
    onset_w = clock.glass_world_t + np.array([e[0] for e in ev]) - float(tw[0])
    gw = layers.render_shards(ev, tw.shape[0], sr, onset_w, groups=4)
    sh_w = np.zeros(tw.shape[0], dtype=np.float32)
    for s, _c in gw:
        sh_w += s
    return {"clock": clock, "sr": sr,
            "impact": grid.to_film(imp_w), "shards": grid.to_film(sh_w),
            "events": ev, "summary": summ,
            "onset_film": clock.film_at_world(clock.glass_world_t
                                              + np.array([e[0] for e in ev])),
            "impact_info": imp_info, "contact_speed": v_contact}


def build_breach(sr=SR):
    spec = json.load(open(os.path.join(ROOT, "docs", "circuit_spec.json")))
    clock = Clock(os.path.join(ROOT, "docs", "beat_sheet.json"), sr=sr)
    # the same contact speed master.py uses
    from audio.scene import Telemetry
    tel = Telemetry(spec=spec)
    v_contact = float(np.interp(11.98, tel.col["s_m"], tel.v_world))
    ev, summ = layers.shard_ballistics(spec, v_contact)
    n = clock.n
    imp_film_t = float(clock.film_at_world(clock.glass_world_t))
    imp, imp_info = layers.impact_event(clock.film_t, imp_film_t, sr, v_contact)
    onset = clock.film_at_world(clock.glass_world_t
                                + np.array([e[0] for e in ev], dtype=np.float64))
    groups = layers.render_shards(ev, n, sr, onset, groups=4)
    shards = np.zeros(n, dtype=np.float32)
    for s, _c in groups:
        shards += s
    bed, bed_info = layers.debris_bed(
        n, sr, onset, np.array([e[5] for e in ev], dtype=np.float64))
    return {"clock": clock, "sr": sr, "impact": imp, "shards": shards,
            "debris": bed, "debris_info": bed_info,
            "events": ev, "summary": summ, "onset_film": onset,
            "impact_info": imp_info, "contact_speed": v_contact,
            "rendered": {"events": getattr(layers.render_shards, "last_events", 0),
                         "non_zero": getattr(layers.render_shards, "last_rendered", 0),
                         "fines_burst": getattr(layers.render_shards, "last_fines", 0)}}


def measure(x, sr, name):
    a, b = BREACH
    seg = np.asarray(x[int(a * sr):int(b * sr)], dtype=np.float64)
    if seg.ndim == 1:
        seg = seg[:, None]
    frac, cent, _ = band_fractions(seg, sr)
    c = crest_db(seg, sr)
    return {
        "bus": name,
        "peak": float(np.abs(seg).max()),
        "rms_dbfs": float(20 * np.log10(max(float(np.sqrt((seg ** 2).mean())), 1e-12))),
        "spectral_centroid_hz": cent,
        "pct_below_30": 100.0 * (frac["0_20"] + frac["20_30"]),
        "pct_below_100": 100.0 * (frac["0_20"] + frac["20_30"] + frac["30_60"] + frac["60_100"]),
        "pct_above_2k": 100.0 * (frac["2000_4000"] + frac["4000_6000"]
                                 + frac["6000_8000"] + frac["8000_24000"]),
        "pct_above_4k": 100.0 * (frac["4000_6000"] + frac["6000_8000"] + frac["8000_24000"]),
        "pct_above_6k": 100.0 * (frac["6000_8000"] + frac["8000_24000"]),
        "crest_50ms_p50_db": float(np.median(c)),
        "onsets_per_s_1k_4k": onset_density(seg, sr, 1000.0, 4000.0),
        "onsets_per_s_4k_12k": onset_density(seg, sr, 4000.0, 12000.0),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    ap.add_argument("--wav", default=None)
    ap.add_argument("--legacy", action="store_true",
                    help="the world-grid + warp path R2-4035 replaced -- G3's "
                         "degenerate control, which MUST measure infrasonic")
    a = ap.parse_args()
    b = build_breach_legacy() if a.legacy else build_breach()
    print("=== %s ===" % ("LEGACY world-grid + warp()" if a.legacy else "film-grid schedule"))
    sr = b["sr"]
    # the buses as they will be trimmed: the mix is dominated by whichever bus
    # is loudest, so measure them at the TARGET_LUFS_S ratios rather than raw
    from audio.master import TARGET_LUFS_S
    from audio import dsp as _dsp

    def at_target(x, key):
        s = np.asarray(x, dtype=np.float64)[:, None].repeat(2, axis=1)
        m = _dsp.max_short_term_lufs(s, sr)
        g = min(TARGET_LUFS_S[key] - m, 20.0 * np.log10(1.0 / max(float(np.abs(s).max()), 1e-12)))
        return np.asarray(x, dtype=np.float64) * 10.0 ** (g / 20.0), g

    parts, gains = {}, {}
    for key in ("impact", "shards", "debris"):
        parts[key], gains[key] = at_target(b[key], key)
    mix = parts["impact"] + parts["shards"] + parts["debris"]
    rep = {"contact_speed_ms": b["contact_speed"],
           "shard_summary": b["summary"],
           "impact_info": b["impact_info"],
           "debris_info": b.get("debris_info", {}),
           "rendered": b.get("rendered", {}),
           "bus_trims_db": gains,
           "shower_film_span_s": float(b["onset_film"].max() - b["onset_film"].min()),
           "shower_world_span_s": float(max(e[0] for e in b["events"])),
           "buses": [measure(b["impact"], sr, "impact raw"),
                     measure(b["shards"], sr, "shards raw"),
                     measure(b["debris"], sr, "debris raw"),
                     measure(parts["impact"], sr, "impact @tgt"),
                     measure(parts["shards"], sr, "shards @tgt"),
                     measure(parts["debris"], sr, "debris @tgt"),
                     measure(mix, sr, "BREACH SUM")]}
    print("rendered: %s" % rep["rendered"])
    # per-second onset density of the shower on the film grid
    hist, edges = np.histogram(b["onset_film"], bins=np.arange(35.0, 55.0, 0.25))
    rep["scheduled_events_per_s"] = {"t": edges[:-1].tolist(),
                                     "per_s": (hist / 0.25).tolist(),
                                     "peak_per_s": float((hist / 0.25).max())}
    print("shower: %.3f s world -> %.3f s film (x%.2f), peak scheduled density %.0f ev/s"
          % (rep["shower_world_span_s"], rep["shower_film_span_s"],
             rep["shower_film_span_s"] / rep["shower_world_span_s"],
             rep["scheduled_events_per_s"]["peak_per_s"]))
    print("%-14s %9s %9s %8s %8s %8s %8s %8s %7s %7s"
          % ("bus", "centroid", "rms dBFS", "<30Hz%", "<100Hz%", ">2k%", ">4k%", ">6k%",
             "crest", "ons1-4k"))
    for m in rep["buses"]:
        print("%-14s %9.1f %9.1f %8.2f %8.2f %8.4f %8.4f %8.4f %7.2f %7.1f"
              % (m["bus"], m["spectral_centroid_hz"], m["rms_dbfs"], m["pct_below_30"],
                 m["pct_below_100"], m["pct_above_2k"], m["pct_above_4k"],
                 m["pct_above_6k"], m["crest_50ms_p50_db"], m["onsets_per_s_1k_4k"]))
    if a.wav:
        import soundfile as sf
        seg = mix[int(BREACH[0] * sr):int(BREACH[1] * sr)]
        seg = seg / max(float(np.abs(seg).max()), 1e-9) * 0.7
        sf.write(a.wav, _sig.resample_poly(seg, 1, 2), sr // 2, subtype="PCM_24")
        print(">> %s" % a.wav)
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(rep, fh, indent=1, default=float)
        print(">> %s" % a.json)


if __name__ == "__main__":
    main()
