#!/usr/bin/env python
"""R2-4081 -- G-HNR's +8 dB BEAT-1 BAR, AGAINST A POSITIVE CONTROL.

    THIS BENCH'S CONCLUSION WAS OVERTURNED BY R2-4084, USING THIS BENCH'S OWN
    SWEEP. The finding below -- that C8b clears +8 dB by 24 dB, so the bar
    stands -- rests on C8b being a signal that should pass. The sweep in this
    file is what shows it is not: at its shipped dry_gain of 0.13, C8b is
    98.3 % SUSTAINED TONE BY POWER. A physics-true assembly cell (C9,
    `audio.controls.synth.assembly_cell`) reads -5.36 dB on the same
    instrument, and so does a passage of 660 struck plates containing no noise
    source at all (-3.78 dB) -- both BELOW every negative in the corpus. The
    bar was not merely unreachable; the statistic is inverted for percussive
    material, and the beat-1 median limb is RETIRED
    (`percept.RETIRED`). The numbers this file produced are correct and are
    the evidence for that; what changed is what they mean. Kept, unedited
    below this note, because a bench whose conclusion was wrong is worth more
    on the record than off it.

R2-4076 item 4 and R2-4080 item 6 both said the same thing: do not move the
bar to find out whether it is reachable -- build a showroom a listener would
call tonal, measure it, and see which side it lands on.

The suite already contains one such control and nobody had read its number.
`C8b_physical_showroom_beat` returns **G-HNR median +32.21 dB** against the
+8 dB bar. So the bar is not merely reachable, it is cleared by 24 dB -- and
`source=artefact` was never needed and is not attempted.

That answer on its own is not useful, because C8b mixes its impact shower at
0.13 against a servo bed normalised to 1.0: it is 99 % drone by power. The
useful question is the one this bench asks: **at what tone/impact balance does
a beat-1-like passage cross +8 dB, and where does the film sit on that axis?**

The sweep is over C8b's OWN construction with ONE number changed -- the dry
impact gain -- so every other property (gravity-scattered arrivals, per-part
plate geometries, per-cluster servo voices, velvet tail with independent L/R)
is held fixed. Nothing is imported from `audio.layers`; this is a control, not
the render path.

The film's own beat 1 is then decomposed the same way from its stems, so the
comparison is between two measured numbers rather than between a number and an
opinion.

    .venv/bin/python -m tools.r2_4081_hnr_control
"""

import json
import math
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audio import percept as P                                     # noqa: E402
from audio.controls import synth as C                              # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "audio", "out", "r2_4081", "hnr_control.json")


def showroom_at(dry_gain, parts_scale=1.0, sr=C.SR, total_s=C.BEAT1_S, seed=808):
    """C8b verbatim, with two free numbers and nothing else touched.

    dry_gain    = 0.13 is C8b as shipped (98.3 % of its power is the servo bed).
    parts_scale = 1.0 is C8b as shipped: 15 clusters of 3-13 parts, ~120
                  contacts. The FILM's beat 1 has 777 contacts across the same
                  15 clusters over the same 33 s, and that count is
                  PICTURE-LOCKED -- 616 first contacts are the parts the
                  delivered 4K frames show arriving, plus 161 restitution
                  bounces inside the animation's own 3-frame settle.

    Returns (stereo, tone_power_share, n_contacts).
    """
    rng = np.random.default_rng(seed)
    n = int(total_s * sr)
    dry = np.zeros(n)
    gaps, g = [], 2.35
    while sum(gaps) < total_s - 4.0 and len(gaps) < 15:
        gaps.append(g)
        g *= 0.86
    times = np.cumsum([2.0] + gaps)[:15]
    n_parts = [max(1, int(round(int(rng.integers(3, 14)) * parts_scale)))
               for _ in times]
    ges = C.distinct_gestures(sr, n=int(sum(n_parts)), seed=seed + 1)
    gi = 0
    for i, t in enumerate(times):
        s = int(t * sr)
        for _p in range(n_parts[i]):
            g_i = ges[gi]; gi += 1
            h = float(rng.uniform(0.15, 4.0))
            rel = float(rng.uniform(0.0, 0.9))
            dt = rel + math.sqrt(2.0 * h / 9.81) * float(rng.uniform(0.9, 1.1))
            for k, amp in ((0, 1.0), (1, 0.34)):
                ss = s + int((dt * (1 + 0.62 * k)) * sr)
                L = min(len(g_i), n - ss)
                if L > 16 and ss >= 0:
                    dry[ss:ss + L] += amp * g_i[:L] * float(rng.uniform(0.5, 1.0))
    rates = [float(rng.uniform(90.0, 190.0)) for _ in times]
    teeth = [int(rng.integers(9, 23)) for _ in times]
    tone = C._norm(C._servo_bed(sr, n, times, rates, teeth, seed + 100), 1.0)
    d = C._norm(dry, 1.0) * dry_gain
    src = d + tone
    share = float((tone ** 2).mean() / max(((tone ** 2).mean() +
                                            (d ** 2).mean()), 1e-30))
    L = src + 0.05 * C.diffuse_tail(src, sr, rt60_s=1.1, seed=seed + 11)
    R = src + 0.05 * C.diffuse_tail(src, sr, rt60_s=1.1, seed=seed + 12)
    return (np.stack([C._norm(L, 0.09), C._norm(R, 0.09)], axis=1), share,
            int(sum(n_parts)) * 2)


def hnr_of(y, sr, sheet=None):
    rep = P.run_suite(y, sr, sheet or C.BEAT1_SHEET, gates=("G-HNR",))
    row = rep["gates"]["G-HNR"]["per_beat"].get("1_assembly")
    if row is None:
        return None
    return row


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    rep = {"bar_db": 8.0, "sweep": [], "film": {}}
    sr = C.SR

    print(">> THE POSITIVE CONTROL SWEEP. C8b's construction, dry impact gain "
          "as the only variable.\n")
    print("    dry gain   tonal share of power   HNR median   frac<0 dB   "
          "verdict at +8 dB")
    for dg in (0.13, 0.30, 0.60, 1.00, 1.80, 3.00, 6.00, 12.0, 25.0):
        y, share, nc = showroom_at(dg, 1.0, sr)
        r = hnr_of(y, sr)
        if r is None:
            continue
        rep["sweep"].append({"dry_gain": dg, "tone_power_share": share,
                             "n_contacts": nc,
                             "hnr_median_db": r["median_db"],
                             "fraction_below_0db": r["fraction_below_0db"]})
        print(f"    {dg:7.2f}   {share*100:16.2f} %   {r['median_db']:+8.2f} dB "
              f"  {r['fraction_below_0db']:8.3f}   "
              f"{'PASS' if r['median_db'] >= 8.0 else 'FAIL'}")

    print("\n>> THE SECOND AXIS: EVENT DENSITY, WHICH IS PICTURE-LOCKED.")
    print("   The film's beat 1 has 777 contacts in 33 s across 15 clusters "
          "because\n   that is what the delivered 4K frames show arriving. "
          "C8b has ~120.\n")
    print("    contacts   tonal share   HNR median   frac<0 dB   verdict at +8 dB")
    rep["density_sweep"] = []
    for ps in (1.0, 2.0, 3.5, 5.0, 6.5, 9.0, 13.0):
        y, share, nc = showroom_at(0.13, ps, sr)
        r = hnr_of(y, sr)
        if r is None:
            continue
        rep["density_sweep"].append({"parts_scale": ps, "n_contacts": nc,
                                     "tone_power_share": share,
                                     "hnr_median_db": r["median_db"],
                                     "fraction_below_0db": r["fraction_below_0db"]})
        print(f"    {nc:8d}   {share*100:9.2f} %   {r['median_db']:+8.2f} dB "
              f"  {r['fraction_below_0db']:8.3f}   "
              f"{'PASS' if r['median_db'] >= 8.0 else 'FAIL'}")

    print("\n   and the same density ladder with the servo bed REMOVED, so the "
          "shower\n   is measured on its own:")
    print("    contacts   HNR median   verdict at +8 dB")
    rep["density_sweep_dry"] = []
    for ps in (1.0, 3.5, 6.5, 13.0):
        y, share, nc = showroom_at(1e6, ps, sr)
        r = hnr_of(y, sr)
        if r is None:
            continue
        rep["density_sweep_dry"].append({"parts_scale": ps, "n_contacts": nc,
                                         "hnr_median_db": r["median_db"]})
        print(f"    {nc:8d}   {r['median_db']:+8.2f} dB   "
              f"{'PASS' if r['median_db'] >= 8.0 else 'FAIL'}")

    # ---- the film, decomposed the same way ---------------------------------
    print("\n>> THE FILM'S OWN BEAT 1, FROM ITS STEMS (R2-4079)\n")
    stems = os.path.join(ROOT, "audio", "out", "r2_4079", "stems")
    sheet = json.load(open(os.path.join(ROOT, "docs", "beat_sheet.json")))
    names = [f[:-4] for f in sorted(os.listdir(stems)) if f.endswith(".wav")]
    acc, srs, pw = None, None, {}
    for nm in names:
        y, srs = sf.read(os.path.join(stems, nm + ".wav"), dtype="float32",
                         always_2d=True)
        b1 = y[:int(33.0 * srs)]
        pw[nm] = float((b1 ** 2).mean())
        acc = b1.copy() if acc is None else acc + b1
    tot = sum(pw.values())
    print("    stem power share of beat 1:")
    for nm in sorted(pw, key=lambda k: -pw[k])[:6]:
        print(f"      {nm:18s} {pw[nm]/tot*100:6.2f} %")
    sh1 = {"beats": [{"name": "1_assembly", "start_s": 0.0}]}
    r = hnr_of(acc, srs, sh1)
    rep["film"]["stem_sum_beat1"] = r
    rep["film"]["stem_power_share"] = {k: v / tot for k, v in pw.items()}
    print(f"\n    stem sum, beat 1:  HNR median {r['median_db']:+.2f} dB, "
          f"frac<0 {r['fraction_below_0db']:.3f}")

    for nm in ("assembly", "room", "engine", "crowd", "bed"):
        if nm not in names:
            continue
        y, _ = sf.read(os.path.join(stems, nm + ".wav"), dtype="float32",
                       always_2d=True)
        rr = hnr_of(y[:int(33.0 * srs)], srs, sh1)
        rep["film"][nm] = rr
        if rr:
            print(f"    {nm:18s} alone:  HNR median {rr['median_db']:+8.2f} dB "
                  f"   ({pw[nm]/tot*100:5.2f} % of the beat)")

    json.dump(rep, open(OUT, "w"), indent=1, default=float)
    print(f"\n>> wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
