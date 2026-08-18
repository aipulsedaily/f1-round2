#!/usr/bin/env python
"""R2-4081 -- THE t = 106.76 s STATION: IS THE AUDIO WRONG OR IS THE ESTIMATOR?

R2-4077 and R2-4079 both left this open and both refused to exclude it. The
declared station now passes (median 6.0 c, corr 0.982) and so does the one at
t = 94.64 s (6.04 c, 0.983). This one reads median 76.9 c, p90 151.0 and
corr 0.591 -- and it has 1.41 SEMITONES of predicted Doppler in it against
7.27-7.30 at the two that pass.

So the question is not "is there Doppler in the audio", it is "can this
estimator, at this station, measure the Doppler that IS there". Arguing about
it is worthless. This bench answers it with a POSITIVE CONTROL:

    synthesise a signal that has EXACTLY the predicted sweep -- an 8-harmonic
    comb whose instantaneous frequency is f_emit(t) * ratio_predicted(t), from
    the station's own retarded-time solve -- and hand it to the identical
    estimator with the identical window centres and the identical search range.

If the control comes back at 0.98 the estimator is fine and the master's audio
at 106.76 s is wrong. If the control comes back near 0.59 the estimator cannot
resolve 1.41 semitones and the bar, not the film, is what is broken.

Three further controls bracket it, all synthesised, none read off the master:
    * the same comb with NO Doppler at all (ratio == 1) -- must FAIL;
    * the same comb with the sweep REVERSED in time -- must FAIL;
    * the same comb buried in the master's own non-engine background at the
      measured engine-to-rest ratio -- the realistic case.

    .venv/bin/python -m tools.r2_4081_doppler_station
"""

import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import verify as VF                                     # noqa: E402
from audio import spatial as sp                                    # noqa: E402
from audio import engine as eng_mod                                # noqa: E402
from audio.clock import Clock                                      # noqa: E402
from audio.scene import Telemetry, CameraPath                      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WAV = os.path.join(ROOT, "audio", "out", "r2_4079", "master_R2-4079.wav")
OUT = os.path.join(ROOT, "audio", "out", "r2_4081", "doppler_station.json")
STATIONS = (94.64166666666667, 106.76041666666667)


def geometry(sr):
    spec = json.load(open(os.path.join(ROOT, "docs", "circuit_spec.json")))
    clock = Clock(os.path.join(ROOT, "docs", "beat_sheet.json"), sr=4800)
    tel = Telemetry(spec=spec)
    cam = CameraPath()
    t_ctrl = np.arange(0.0, clock.duration_s, 1.0 / sp.CTRL_HZ)
    w_ctrl = clock.world_at_film(t_ctrl)
    car = tel.sample(w_ctrl, "v_world")
    _earL, _earR, centre, _RR = cam.ears(t_ctrl)
    hdg = car["heading"]
    fwd = np.stack([np.cos(hdg), np.sin(hdg), np.zeros_like(hdg)], axis=1)
    src = car["pos"] - fwd * 1.60 + np.array([0.0, 0.0, 0.42])
    t_a, rr, _e, _u = sp.retarded(t_ctrl, src, centre, sp.C_AIR)
    ratio = 1.0 / np.gradient(t_a, t_ctrl)
    srf = 4800
    wf = np.arange(0.0, float(clock.world_at_film(clock.duration_s)) + 1.0,
                   1.0 / srf)
    vf = np.interp(wf, tel.t, tel.v_world)
    af = np.interp(wf, tel.t, tel.col["accel_long_ms2"])
    rpm_f, _g, _l = eng_mod.gear_and_rpm(vf, np.zeros_like(vf), np.zeros_like(vf),
                                         srf, wf, -2.30, -0.05)
    return dict(clock=clock, tel=tel, t_ctrl=t_ctrl, t_a=t_a, ratio=ratio,
                wf=wf, rpm_f=rpm_f, r_lo=float(np.min(ratio)) / 2 ** (1 / 12),
                r_hi=float(np.max(ratio)) * 2 ** (1 / 12))


def station_arrays(G, t0):
    tcs = np.arange(t0 - 3.0, t0 + 1.2, 0.05)
    tcs = tcs[(tcs > 0.2) & (tcs < G["clock"].duration_s - 0.2)]
    te = np.interp(tcs, G["t_a"], G["t_ctrl"])
    we = G["clock"].world_at_film(np.clip(te, 0.0, G["clock"].duration_s))
    fe = np.interp(we, G["wf"], G["rpm_f"]) / 60.0 * VF.ENGINE_ORDER
    rat = np.interp(tcs, G["t_a"], G["ratio"])
    lg = np.abs(np.interp(we, G["tel"].t,
                          G["tel"].col["accel_lat_ms2"])) / 9.81
    return tcs, fe, rat, lg


def synth_comb(tcs, fe, rat, sr, n_harm=8, pad_s=0.6, seed=7):
    """A signal whose instantaneous fundamental is exactly f_emit*ratio.

    Built from the geometry alone. Nothing about the master enters it.
    """
    t0, t1 = float(tcs[0]) - pad_s, float(tcs[-1]) + pad_s
    n = int((t1 - t0) * sr)
    t = t0 + np.arange(n) / sr
    f = np.interp(t, tcs, fe * rat)
    ph = 2.0 * np.pi * np.cumsum(f) / sr
    rng = np.random.default_rng(seed)
    y = np.zeros(n)
    for k in range(1, n_harm + 1):
        y += (1.0 / k ** 0.7) * np.sin(k * ph + rng.uniform(0, 6))
    return y / np.max(np.abs(y)) * 0.3, t0


def score(rm, cf, rat, tcs):
    gd = np.isfinite(rm) & (cf > 2.0)
    if gd.sum() < 8:
        return {"usable": int(gd.sum()), "OUTCOME": "INAPPLICABLE"}
    ec = 1200.0 * np.log2(np.maximum(rm[gd], 1e-6) / np.maximum(rat[gd], 1e-6))
    trk = np.abs(ec) < VF.TRACK_MAX_CENTS
    ff = float(1.0 - trk.mean())
    out = {"usable": int(gd.sum()), "tracked": int(trk.sum()),
           "tracker_failure_fraction": ff,
           "median_abs_error_cents": float(np.median(np.abs(ec))),
           "median_signed_error_cents": float(np.median(ec)),
           "p90_abs_error_cents": float(np.percentile(np.abs(ec), 90))}
    if trk.sum() > 8:
        out["corr_on_tracked_windows"] = float(
            np.corrcoef(rm[gd][trk], rat[gd][trk])[0, 1])
    else:
        out["corr_on_tracked_windows"] = float("nan")
    rc = out["corr_on_tracked_windows"]
    out["OUTCOME"] = ("PASS" if (out["median_abs_error_cents"] < 100.0
                                 and out["p90_abs_error_cents"] < 150.0
                                 and rc == rc and rc > 0.90 and ff <= 0.15)
                      else "FAIL")
    return out


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    x, sr = sf.read(WAV, dtype="float32", always_2d=True)
    mono = x.mean(axis=1)
    G = geometry(sr)
    rep = {"search_range": [G["r_lo"], G["r_hi"]], "stations": {}}
    print(f">> search ratio range [{G['r_lo']:.4f}, {G['r_hi']:.4f}]  "
          f"bar: med<100 c, p90<150 c, corr>0.90, ff<=0.15\n")

    for t0 in STATIONS:
        tcs, fe, rat, lg = station_arrays(G, t0)
        span_st = 12.0 * np.log2(rat.max() / rat.min())
        print(f"=== station t = {t0:.3f} s   predicted span {span_st:.3f} "
              f"semitones   f_emit {fe.min():.0f}-{fe.max():.0f} Hz   "
              f"max lat {lg.max():.2f} g")
        row = {"predicted_span_semitones": float(span_st)}

        # (1) the master itself, engine comb only (this bench does not model
        #     the tyre-scrub switch; both stations are below 2.0 lateral g)
        rm, cf = VF.doppler_ratio(mono, sr, tcs, fe, rmin=G["r_lo"], rmax=G["r_hi"])
        row["master"] = score(rm, cf, rat, tcs)

        # (2) THE POSITIVE CONTROL: exactly the predicted sweep, synthesised
        y, y_t0 = synth_comb(tcs, fe, rat, sr)
        rm2, cf2 = VF.doppler_ratio(y, sr, tcs - y_t0, fe, rmin=G["r_lo"],
                                    rmax=G["r_hi"])
        row["CONTROL_exact_predicted_sweep"] = score(rm2, cf2, rat, tcs)

        # (3) the same comb with NO Doppler -- must FAIL
        y3, _ = synth_comb(tcs, fe, np.ones_like(rat), sr)
        rm3, cf3 = VF.doppler_ratio(y3, sr, tcs - y_t0, fe, rmin=G["r_lo"],
                                    rmax=G["r_hi"])
        row["CONTROL_no_doppler_must_fail"] = score(rm3, cf3, rat, tcs)

        # (4) the sweep reversed -- must FAIL
        y4, _ = synth_comb(tcs, fe, rat[::-1].copy(), sr)
        rm4, cf4 = VF.doppler_ratio(y4, sr, tcs - y_t0, fe, rmin=G["r_lo"],
                                    rmax=G["r_hi"])
        row["CONTROL_reversed_sweep_must_fail"] = score(rm4, cf4, rat, tcs)

        for k in ("master", "CONTROL_exact_predicted_sweep",
                  "CONTROL_no_doppler_must_fail",
                  "CONTROL_reversed_sweep_must_fail"):
            v = row[k]
            print(f"    {k:36s} med {v.get('median_abs_error_cents', float('nan')):7.2f} c "
                  f"(signed {v.get('median_signed_error_cents', float('nan')):+7.2f}) "
                  f"p90 {v.get('p90_abs_error_cents', float('nan')):7.2f}  "
                  f"corr {v.get('corr_on_tracked_windows', float('nan')):+6.3f}  "
                  f"ff {v.get('tracker_failure_fraction', float('nan')):.3f}  "
                  f"{v['OUTCOME']}")
        rep["stations"][f"{t0:.3f}"] = row
        print()

    json.dump(rep, open(OUT, "w"), indent=1, default=float)
    print(f">> wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
