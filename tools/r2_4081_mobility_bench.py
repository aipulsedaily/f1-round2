#!/usr/bin/env python
"""R2-4081 -- G-ROOM(b) MOBILITY: IS THE 0.525 -> 0.600 REGRESSION THE FILM OR
THE CLUSTERER?

R2-4080 gave every part in a cluster its own size, shape and material, which is
what moved G-GESTURE and G-NOVEL to PASS. It also moved G-ROOM(b)'s mobility
limb the wrong way, 0.525 -> 0.600, and its author declined to net that off.
The stated cause was "more distinct peaks per burst means more recurrence".

`peak_recurrence` clusters the pooled per-burst peak frequencies with

    if abs(v - clusters[-1][-1]) / v * 100 <= tol_pct: clusters[-1].append(v)

which is SINGLE-LINKAGE on a sorted list. Every member need only be within 1 %
of the PREVIOUS member, so a chain of observations each 0.9 % apart merges into
one "recurring line" of unbounded width. The gate's own output already shows
this: R2-4079's strongest cluster is reported at 5822.5 Hz with
`spread_hz = 351.6` -- a 6.0 % wide "line" under a 1 % tolerance.

That is exactly the mechanism that turns MORE DISTINCT PEAKS into MORE
RECURRENCE: denser coverage of the frequency axis makes the chain easier to
close. So the regression's stated cause and the clusterer's defect are the same
phenomenon, and they have different owners.

This bench measures both, on the same signals, with nothing else changed:

  * `single`   -- the shipped rule, verbatim;
  * `centroid` -- a member joins only if it is within tol of the RUNNING MEAN
                  of the cluster it joins, so a cluster can never be wider than
                  2*tol. Same tolerance, same top-8, same everything else.

and reports, for each: recurrence, the widest cluster, and how much of the
recurrence comes from clusters wider than the tolerance they were built under.

It runs on the two masters, on the controls that must FAIL this limb, and on
the control that must PASS it -- because a clusterer that lowers the film's
number and also lowers the defect's number has fixed nothing.

    .venv/bin/python -m tools.r2_4081_mobility_bench
"""

import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                     # noqa: E402
from audio.controls import synth as C                              # noqa: E402
from tools import percept_matrix as M                              # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio", "out", "r2_4081", "mobility_bench.json")


def observations(mono, sr, bursts, top_k=8, f_lo=200.0, f_hi=6000.0):
    """Verbatim the first half of `percept.peak_recurrence` -- the part that
    finds the per-burst peaks. Shared by both clusterers so the only difference
    measured is the clustering."""
    obs = []
    for s, n in bursts:
        seg = mono[s:s + n]
        if len(seg) < 2048:
            continue
        win = min(8192, 1 << int(np.log2(len(seg))))
        Pw, f = P._stft_power(seg, sr, win=win)
        if Pw.shape[0] == 0:
            continue
        S = Pw.mean(axis=0)
        pre = P._pre_onset(mono, sr, s)
        if len(pre) >= win:
            Pp, _ = P._stft_power(pre, sr, win=win)
            if Pp.shape[0]:
                S = np.maximum(S - Pp.mean(axis=0), S * 1e-6)
        m = (f >= f_lo) & (f <= f_hi)
        Sb, fb = S[m], f[m]
        k = max(int(len(Sb) / 60) | 1, 5)
        ldb = 10 * np.log10(np.maximum(Sb, 1e-20))
        rel = ldb - P._sig.savgol_filter(ldb, k, 2)
        pk, _ = P._sig.find_peaks(rel, distance=max(int(len(Sb) / 200), 2))
        if len(pk) == 0:
            continue
        pk = pk[np.argsort(-rel[pk])][:top_k]
        obs.append([float(fb[p]) for p in pk])
    return obs


def _score(obs, clusters, tol_pct):
    n_obs = sum(len(r) for r in obs)
    recurring, top, wide = 0, [], 0
    for c in clusters:
        mu = float(np.mean(c))
        nb = sum(1 for row in obs
                 if any(abs(v - mu) / mu * 100.0 <= tol_pct for v in row))
        if nb >= 3:
            recurring += len(c)
            spread = float(max(c) - min(c))
            top.append({"f_hz": mu, "bursts": int(nb), "spread_hz": spread,
                        "spread_pct": spread / mu * 100.0, "n": len(c)})
            if spread / mu * 100.0 > tol_pct:
                wide += len(c)
    top.sort(key=lambda r: -r["bursts"])
    return {"recurrence": recurring / max(n_obs, 1), "n_observations": n_obs,
            "n_bursts": len(obs), "n_clusters": len(clusters),
            "widest_pct": max((t["spread_pct"] for t in top), default=0.0),
            "recurrence_from_overwide_clusters": wide / max(n_obs, 1),
            "top": top[:6]}


def cluster_single(flat, tol_pct):
    """The shipped rule: within tol of the PREVIOUS member."""
    out = []
    for v in flat:
        if out and abs(v - out[-1][-1]) / v * 100.0 <= tol_pct:
            out[-1].append(v)
        else:
            out.append([v])
    return out


def cluster_centroid(flat, tol_pct):
    """Within tol of the cluster's own RUNNING MEAN. A cluster can never be
    wider than 2*tol, so "a line that recurs" means what it says."""
    out = []
    for v in flat:
        if out:
            mu = float(np.mean(out[-1]))
            if abs(v - mu) / mu * 100.0 <= tol_pct:
                out[-1].append(v)
                continue
        out.append([v])
    return out


def measure(mono, sr, sheet, beat="1_assembly", tol_pct=1.0):
    beats = P.beats_from_sheet(sheet, len(mono) / sr)
    b = [x for x in beats if x.name == beat]
    if not b:
        return None
    seg = P._slice(mono, sr, b[0])
    bursts = P.find_bursts(seg, sr)
    obs = observations(seg, sr, bursts)
    if len(obs) < 4:
        return {"inapplicable": f"{len(obs)} usable bursts"}
    flat = sorted(x for row in obs for x in row)
    return {"single": _score(obs, cluster_single(flat, tol_pct), tol_pct),
            "centroid": _score(obs, cluster_centroid(flat, tol_pct), tol_pct)}


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    sheet = json.load(open(os.path.join(ROOT, "docs", "beat_sheet.json")))
    rep, rows = {}, []

    def add(tag, mono, sr, sh=None, must=None):
        r = measure(mono, sr, sh or sheet)
        rep[tag] = {"result": r, "must": must}
        if not r or "inapplicable" in (r or {}):
            print(f"    {tag:38s} INAPPLICABLE")
            return
        s, c = r["single"], r["centroid"]
        rows.append((tag, s, c, must))
        print(f"    {tag:38s} {s['recurrence']:.3f} -> {c['recurrence']:.3f}   "
              f"widest {s['widest_pct']:5.2f}% -> {c['widest_pct']:4.2f}%   "
              f"obs {s['n_observations']:4d}  chain-borne {s['recurrence_from_overwide_clusters']:.3f}"
              + (f"   [must {must}]" if must else ""))

    print(">> G-ROOM(b) mobility, beat 1. bar 0.35. "
          "single-linkage (shipped) -> centroid-linkage\n")
    for tag, path in (
            ("R2-4079 (this master)", "audio/out/r2_4079/master_R2-4079.wav"),
            ("R2-4069 (before per-part timbre)", "audio/out/r2_4064/master_R2-4069.wav"),
            ("C4 delivered master (must FAIL)", "audio/out/master.wav")):
        p = os.path.join(ROOT, path)
        if not os.path.exists(p):
            continue
        x, sr = sf.read(p, dtype="float32", always_2d=True)
        add(tag, x.mean(axis=1), sr, must=("FAIL" if "C4" in tag else None))

    print()
    # the synthesised controls, including the mutation that IS this limb's defect
    base = C.physical_showroom_beat()
    sr = C.SR
    add("C8b physical showroom (must PASS)", base.mean(axis=1), sr,
        C.BEAT1_SHEET, must="PASS")
    for label, fn in (("M-ROOMb fixed resonator bank (must FAIL)", M._fixed_resonators),
                      ("M-ROOMa 8-tap FDN, no diffusion (must FAIL)", M._fdn_comb_tail),
                      ("M-GEST one gesture repeated", M._identical_gestures)):
        y = fn(base.copy(), sr)
        add(label, P.to_mono(y), sr, C.BEAT1_SHEET,
            must=("FAIL" if "must FAIL" in label else None))

    print("\n>> VERDICTS AT THE 0.35 BAR")
    print("    signal                                 single  centroid  required")
    ok = True
    for tag, s, c, must in rows:
        vs = "FAIL" if s["recurrence"] > 0.35 else "PASS"
        vc = "FAIL" if c["recurrence"] > 0.35 else "PASS"
        flag = ""
        if must and vc != must:
            flag = "  <-- CENTROID BREAKS THIS CONTROL"
            ok = False
        print(f"    {tag:38s} {vs:6s}  {vc:8s}  {must or '-':8s}{flag}")
    print(f"\n>> centroid clusterer preserves every control verdict: {ok}")

    json.dump(rep, open(OUT, "w"), indent=1, default=float)
    print(f">> wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
