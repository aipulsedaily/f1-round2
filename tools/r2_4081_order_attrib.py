#!/usr/bin/env python
"""R2-4081 -- G-ORDER: IS THE COMB MISPLACED, SMEARED, OR DROWNED?

R2-4079 reads 0.19 of 300-4000 Hz energy on the lines its own telemetry
predicts, against a 0.60 bar, with the wrong-fundamental control at 0.07. Three
explanations fit that one number and they call for three different fixes, so
this bench separates them BEFORE anything is changed. It measures, with
G-ORDER's own `percept.order_energy_fraction` throughout:

  MISPLACED  the fraction as a function of a deliberate offset in f_fund. If the
             maximum is not at offset 0, the comb is somewhere else and the
             telemetry or the Doppler solve is wrong.
  SMEARED    the fraction as a function of the analysis window, and the rpm
             SWEEP inside each window expressed as a percentage against the
             gate's own +-1.5 % tolerance. A comb that moves 8 % inside the
             window cannot sit inside a 1.5 % band however well it is placed.
  DROWNED    the same fraction on the ENGINE STEM ALONE against the mix. If the
             stem scores and the mix does not, the lines are there and the
             denominator is everything else.

Every row carries the number it is being compared with. Nothing here writes to
the render path.

    .venv/bin/python -m tools.r2_4081_order_attrib --wav <master> [--stems <dir>]
"""

import argparse
import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                    # noqa: E402
from tools import percept_matrix as M                             # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_BEATS = ("4_transit", "5_lap")


def windows(b, tel, step=0.5):
    """The gate's own window list: 0.5 s, on throttle, rpm >= 3000."""
    out = []
    t = b.t0 + 0.25
    while t + step <= b.t1:
        rpm = float(tel["rpm_at"](t))
        thr = tel.get("throttle_at")
        if thr is not None and float(thr(t)) <= 0.10:
            t += step
            continue
        if np.isfinite(rpm) and rpm >= 3000.0:
            dop = tel.get("doppler_at")
            ratio = float(dop(t)) if dop is not None else 1.0
            rpm_end = float(tel["rpm_at"](min(t + step, b.t1)))
            out.append((t, rpm, ratio, rpm_end))
        t += step
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav", default=os.path.join(
        ROOT, "audio", "out", "r2_4079", "master_R2-4079.wav"))
    ap.add_argument("--stems", default=None)
    ap.add_argument("--out", default=os.path.join(
        ROOT, "audio", "out", "r2_4081", "order_attrib.json"))
    a = ap.parse_args()

    x, sr = sf.read(a.wav, always_2d=True)
    mono = P.to_mono(x)
    sheet = json.load(open(os.path.join(ROOT, "docs", "beat_sheet.json")))
    beats = P.beats_from_sheet(sheet, len(mono) / sr)
    tel = M._telemetry("film")
    order = P.ENGINE_FIRING_ORDER
    tol = P.V("G_ORDER.line_tolerance_pct")
    stems = None
    if a.stems:
        stems = {}
        for fn in sorted(os.listdir(a.stems)):
            if fn.endswith(".wav"):
                y, ysr = sf.read(os.path.join(a.stems, fn), always_2d=True)
                stems[fn[:-4]] = (P.to_mono(y), ysr)

    rep = {"wav": a.wav, "order": order, "tolerance_pct": tol,
           "bar": P.V("G_ORDER.min_energy_on_predicted_lines"), "beats": {}}
    for b in beats:
        if b.name not in ENGINE_BEATS:
            continue
        seg = P._slice(mono, sr, b)
        w = windows(b, tel)
        if len(w) < 6:
            continue
        row = {"n_windows": len(w)}

        # ---- SMEARED: how far does the comb move INSIDE one window? -------
        sweep = [abs(re - r) / r * 100.0 for _t, r, _q, re in w]
        row["rpm_sweep_pct_within_window"] = {
            "median": float(np.median(sweep)), "p90": float(np.percentile(sweep, 90)),
            "max": float(np.max(sweep)), "gate_tolerance_pct": tol,
            "windows_sweeping_more_than_tolerance": float(
                np.mean(np.array(sweep) > tol))}

        def frac(signal, ssr, f_scale=1.0, step_s=0.5):
            vals = []
            for t, rpm, ratio, _re in w:
                i0 = int((t - b.t0) * ssr)
                i1 = int((t - b.t0 + step_s) * ssr)
                v = P.order_energy_fraction(signal[i0:i1], ssr,
                                            order * rpm / 60.0 * ratio * f_scale,
                                            tol_pct=tol)
                if np.isfinite(v):
                    vals.append(v)
            return float(np.median(vals)) if vals else float("nan")

        # ---- MISPLACED: the fraction against a deliberate offset ----------
        row["offset_scan"] = {
            ("%+.1f%%" % ((s - 1.0) * 100.0)): frac(seg, sr, s)
            for s in (0.94, 0.97, 0.985, 1.0, 1.015, 1.03, 1.06)}

        # ---- SMEARED, second limb: shorter windows track a moving comb ----
        row["window_scan"] = {("%.2f s" % s): frac(seg, sr, 1.0, s)
                              for s in (0.5, 0.25, 0.125)}

        # ---- DROWNED: the engine stem alone, and every stem's share -------
        if stems:
            per = {}
            for name, (sx, ssr) in stems.items():
                sb = P._slice(sx, ssr, b)
                pw = float(np.mean(sb ** 2))
                per[name] = {"power_share": pw}
            tot = sum(v["power_share"] for v in per.values()) or 1.0
            for name, v in per.items():
                v["power_share"] /= tot
            eng = stems.get("engine")
            if eng is not None:
                row["engine_stem_alone"] = frac(P._slice(eng[0], eng[1], b),
                                                eng[1])
            row["stem_power_share"] = {
                k: round(v["power_share"], 5) for k, v in
                sorted(per.items(), key=lambda kv: -kv[1]["power_share"])[:8]}
        rep["beats"][b.name] = row

    print(json.dumps(rep, indent=1, default=float))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(rep, fh, indent=1, default=float)
    print(">> wrote %s" % os.path.relpath(a.out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
