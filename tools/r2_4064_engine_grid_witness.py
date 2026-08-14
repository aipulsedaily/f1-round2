"""R2-4064: WATCH THE ENGINE'S VARISPEED FAIL, THEN WATCH IT MOVE.

The delivered breach is 55 % engine by energy at a 217.7 Hz spectral centroid
(R2-4056), and the reason is one call site: `master.py` synthesises the engine on
the WORLD grid and then runs it through `WorldGrid.to_film`, which is
`catmull_rom` -- a VARISPEED RESAMPLER. Beat 3 runs world time down to a floor of
0.153719, so every partial the engine produces during the breach is transposed
6.5051x down: 31.4 semitones, two and a half octaves.

R2-4035 fixed exactly this for the transient breach sources (impact, shards,
debris) by synthesising on the FILM grid, and deliberately left the sustained
ones alone because they belong to the engine workflow. This is that workflow.

WHAT THIS TOOL DOES. It renders the engine (and the tyres) BOTH WAYS from the
same telemetry and the same clock, over the same film-time window, and measures:

    legacy   engine.synth on the world grid, then grid.to_film()
    film     telemetry resampled to world_at_film(film_t), engine.synth on the
             FILM grid -- the rpm SCHEDULE stretches, the firing frequency at
             each instant is the true frequency for that rpm

It never writes a master and never touches `audio/`. Run it before and after the
change; the numbers it prints are the ones quoted in the staging note.

    .venv/bin/python -m tools.r2_4064_engine_grid_witness --sr 96000
"""

from __future__ import annotations

import argparse
import json
import os
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from audio import dsp, engine, layers          # noqa: E402
from audio.clock import Clock, WorldGrid       # noqa: E402
from audio.scene import Telemetry, classify, lateral_offsets  # noqa: E402


def band_stats(x, sr, t0, t1, label):
    """Spectral centroid and band shares of `x` over film seconds [t0, t1)."""
    a, b = int(t0 * sr), int(t1 * sr)
    seg = np.asarray(x[a:b], dtype=np.float64)
    if seg.ndim > 1:
        seg = seg.mean(axis=1)
    if seg.size < 1024 or not np.any(seg):
        return {"label": label, "empty": True}
    w = np.hanning(seg.size)
    X = np.abs(np.fft.rfft(seg * w)) ** 2
    f = np.fft.rfftfreq(seg.size, 1.0 / sr)
    tot = float(X.sum()) + 1e-30
    return {
        "label": label,
        "rms_dbfs": float(20.0 * np.log10(max(float(np.sqrt((seg ** 2).mean())), 1e-12))),
        "centroid_hz": float((f * X).sum() / tot),
        "pct_lt_100": float(100.0 * X[f < 100.0].sum() / tot),
        "pct_gt_1k": float(100.0 * X[f > 1000.0].sum() / tot),
        "pct_gt_4k": float(100.0 * X[f > 4000.0].sum() / tot),
        "peak_hz": float(f[int(np.argmax(X))]),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sr", type=int, default=96000)
    ap.add_argument("--out", default=os.path.join(ROOT, "audio", "out", "witness_engine_grid.json"))
    a = ap.parse_args()
    sr = a.sr
    t0 = time.time()

    spec = json.load(open(os.path.join(ROOT, "docs", "circuit_spec.json")))
    sheet_p = os.path.join(ROOT, "docs", "beat_sheet.json")
    clock = Clock(sheet_p, sr=sr)
    grid = WorldGrid(clock)
    tel = Telemetry(spec=spec)

    def tel_on(t_world):
        st = tel.sample(t_world, "v_world")
        return {k: st[k].astype(np.float32) for k in
                ("speed", "accel_long", "accel_lat", "slip", "wheel_w")}, st["pos"], st["track_s"]

    # ---- the two grids -----------------------------------------------------
    tw = grid.t                                   # uniform WORLD grid
    tau = clock.film_t                            # uniform FILM grid
    w_of_tau = clock.world_at_film(tau)           # world time at each film sample

    print(f"world grid {tw.shape[0]} samples {tw[0]:.2f}..{tw[-1]:.2f} s world")
    print(f"film  grid {tau.shape[0]} samples {tau[0]:.2f}..{tau[-1]:.2f} s film")
    print(f"clock scale min {clock.scale.min():.6f} max {clock.scale.max():.6f} "
          f"-> transposition during the ramp {1.0 / clock.scale.min():.4f}x DOWN")

    res = {"sr": sr, "scale_min": float(clock.scale.min()),
           "transposition_x": float(1.0 / clock.scale.min())}

    # ---- LEGACY: synth on the world grid, then varispeed onto the film grid --
    st_w, pos_w, ts_w = tel_on(tw)
    eng_w, rpm_w, gear_w, info_w = engine.synth(
        tw, st_w["speed"], st_w["accel_long"], st_w["slip"], st_w["wheel_w"], spec, sr)
    print(f"[{time.time()-t0:6.1f}s] legacy engine synthesised on the world grid")
    eng_legacy = grid.to_film(eng_w)
    del eng_w

    # ---- FILM: the SCHEDULE mapped through the clock, the VOICE on the film
    # ---- grid. Same call, same telemetry, one extra pair of arguments.
    eng_film, rpm_f, gear_f, info_f = engine.synth(
        tw, st_w["speed"], st_w["accel_long"], st_w["slip"], st_w["wheel_w"], spec, sr,
        to_film=grid.to_film, t_world_film=w_of_tau)
    print(f"[{time.time()-t0:6.1f}s] film-grid engine synthesised "
          f"(half_order_weight {info_f['half_order_weight']}, firing order "
          f"{info_f['firing_fundamental_order']})")
    res["engine_info_film"] = {k: info_f[k] for k in
                               ("half_order_weight", "firing_angles_deg",
                                "firing_intervals_deg", "firing_fundamental_order",
                                "harmonic_over_broadband_db", "rendered_on")}
    res["engine_info_legacy_hb_db"] = info_w["harmonic_over_broadband_db"]

    # the rpm SCHEDULE must be the same curve in film time -- that is the whole
    # claim: the schedule stretches, the pitch does not.
    rpm_legacy_on_film = grid.to_film(rpm_w.astype(np.float32))
    res["rpm_schedule_max_abs_diff_rpm"] = float(
        np.abs(rpm_legacy_on_film[:tau.shape[0]] - rpm_f[:tau.shape[0]]).max())
    res["rpm_schedule_p99_abs_diff_rpm"] = float(np.percentile(
        np.abs(rpm_legacy_on_film[:tau.shape[0]] - rpm_f[:tau.shape[0]]), 99.0))

    windows = [("breach 36-44 s", 36.0, 44.0),
               ("ramp core 39-43 s", 39.0, 43.0),
               ("after the ramp 45-49 s", 45.0, 49.0),
               ("lap 60-64 s", 60.0, 64.0)]
    rows = []
    for lab, wa, wb in windows:
        rows.append({"window": lab,
                     "legacy": band_stats(eng_legacy, sr, wa, wb, "legacy"),
                     "film": band_stats(eng_film, sr, wa, wb, "film")})
    res["engine"] = rows

    print("\nENGINE, spectral centroid over each window")
    print("%-24s %12s %12s %10s" % ("window", "legacy Hz", "film Hz", "ratio"))
    for r in rows:
        lg, fl = r["legacy"], r["film"]
        if lg.get("empty") or fl.get("empty"):
            print("%-24s %12s %12s" % (r["window"], "-", "-"))
            continue
        print("%-24s %12.1f %12.1f %10.3f"
              % (r["window"], lg["centroid_hz"], fl["centroid_hz"],
                 fl["centroid_hz"] / max(lg["centroid_hz"], 1e-9)))
    print("\nENGINE, energy below 100 Hz / above 1 kHz (%)")
    for r in rows:
        lg, fl = r["legacy"], r["film"]
        if lg.get("empty") or fl.get("empty"):
            continue
        print("%-24s  <100 Hz %6.2f -> %6.2f    >1 kHz %6.3f -> %6.3f    "
              "peak %7.1f -> %7.1f Hz"
              % (r["window"], lg["pct_lt_100"], fl["pct_lt_100"],
                 lg["pct_gt_1k"], fl["pct_gt_1k"], lg["peak_hz"], fl["peak_hz"]))
    print("\nrpm schedule agreement (legacy warped to film vs film-grid): "
          "max %.2f rpm, p99 %.2f rpm"
          % (res["rpm_schedule_max_abs_diff_rpm"], res["rpm_schedule_p99_abs_diff_rpm"]))

    del eng_legacy, eng_film

    # ---- the tyres, the other varispeeded sustained bus --------------------
    wc = np.arange(tw[0], tw[-1], 1.0 / 240.0)
    stc = tel.sample(wc, "v_world")
    lat_c, _ = lateral_offsets(spec, stc["pos"])
    ev, shard_sum = layers.shard_ballistics(
        spec, float(np.interp(11.98, tel.col["s_m"], tel.v_world)))
    debris_end_x = float(np.clip(shard_sum["debris_p80_x_m"], 16.0, 45.0))
    surf_c = classify(spec, stc["pos"], stc["track_s"], lat_c, debris_end_x)

    surf_w = {k: np.interp(tw, wc, surf_c[k]).astype(np.float32) for k in surf_c}
    surf_f = {k: np.interp(w_of_tau, wc, surf_c[k]).astype(np.float32) for k in surf_c}

    tyre_w, _ = layers.tyres(tw, st_w, surf_w, spec, sr)
    tyre_legacy = grid.to_film(tyre_w)
    del tyre_w
    st_f = {k: grid.to_film(st_w[k]) for k in st_w}
    tyre_film, _ = layers.tyres(w_of_tau, st_f, surf_f, spec, sr)
    print(f"[{time.time()-t0:6.1f}s] tyres both ways")

    trows = []
    for lab, wa, wb in windows:
        trows.append({"window": lab,
                      "legacy": band_stats(tyre_legacy, sr, wa, wb, "legacy"),
                      "film": band_stats(tyre_film, sr, wa, wb, "film")})
    res["tyres"] = trows
    print("\nTYRES, spectral centroid over each window")
    print("%-24s %12s %12s %10s" % ("window", "legacy Hz", "film Hz", "ratio"))
    for r in trows:
        lg, fl = r["legacy"], r["film"]
        if lg.get("empty") or fl.get("empty"):
            print("%-24s %12s %12s" % (r["window"], "-", "-"))
            continue
        print("%-24s %12.1f %12.1f %10.3f"
              % (r["window"], lg["centroid_hz"], fl["centroid_hz"],
                 fl["centroid_hz"] / max(lg["centroid_hz"], 1e-9)))

    res["wall_clock_s"] = time.time() - t0
    with open(a.out, "w") as fh:
        json.dump(res, fh, indent=1, default=float)
    print(f"\n>> {a.out}  ({res['wall_clock_s']:.1f} s)")
    _ = dsp
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
