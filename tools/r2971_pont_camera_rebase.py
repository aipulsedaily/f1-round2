#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2971_pont_camera_rebase.py — REBASE THE R2-738 BRIDGE-THREAD ONTO THE LIVE PATH.

    python3 tools/r2971_pont_camera_rebase.py --selftest
    python3 tools/r2971_pont_camera_rebase.py \
        --base render/film17_path.json \
        --out  render/film_path_R2971_PONT_B5_REBASED.json

*** THIS OFFSET IS NOW IN SOURCE.  R2-1701. ***
`tools/author_beats2_5.py` carries it as `pont_offset()`, applied inside
`emit_keys`' own sampler, so `docs/beat_sheet.json` regenerates WITH the bridge
thread and any rig rebuilt from that sheet has it.  This tool stays because its
selftest is the control that earned the numbers — the null case, the support,
the beat boundaries, the quaternion hemisphere, the envelope — and because it
still measures the offset against the LIVE path, which the sheet cannot.

  * DO NOT merge `render/film_path_R2971_PONT_B5_REBASED.json`, or any other
    `film_path_*.json`, into anything.  See "WHY THIS EXISTS" below.
  * Applying this tool to a path built from the CURRENT sheet DOUBLE-APPLIES
    the offset: 40 m inboard and 15 m down, straight through the parapet.  Its
    base must be a path built before R2-1701, which `render/film17_path.json`
    is.

WHY THIS EXISTS
---------------
`tools/r2731_pont_camera_apply.py --out` writes a whole-film path built from the
beat sheet, and that rebuild does NOT reproduce the live `film17_path.json`:
measured here, 2,472 of 2,978 frames differ, worst **9.866 m at f545**, all of it
in beat 1.  Adopting that file wholesale would revert beat 1's camera by ~9.9 m
to buy a 12-frame occlusion fix in beat 5.  That is exactly the defect R2-737
caught in the R2-591 lens retune, and `tools/r2731_lens_retune_rebase.py` is the
precedent for the cure: **carry the OFFSET across, never the file.**

The offset is a pure function of frame index (two smootherstep windows in the
bridge's own lateral/vertical frame), so it rebases exactly.  The AIM is not a
pure function of frame index -- it depends on where the camera is -- so the aim
is re-derived here from the same model `r2731_pont_camera_apply.py` earns in its
selftest: look at the car's box centre, image-up pulled toward world +Z.

THE CONTROL THAT MAKES THIS TRUSTWORTHY
---------------------------------------
With the offset forced to zero the re-aim must reproduce the LIVE quaternion,
not merely some quaternion.  `--selftest` asserts that on every frame of the
window, in pixels on the 4K frame, against the live path.  If the null case does
not reproduce the base, the offset case cannot be believed either.

This file also WIDENS R2-738's ramps.  R2-738 as authored costs 91.2 m/s^2
(9.29 g), 95 % of `tools/author_beats2_5.py`'s craft limit and 1.86x the shipped
path's own peak; the whole spike sits in the 22-frame lateral OUT ramp.  Widening
that ramp to 32 frames leaves the occlusion result untouched at ZERO blocked
frames and brings the peak to 47.7 m/s^2 -- below the shipped path's 49.1.  See
the constants below.

Beat 5 only.  The window is f2131-2224, interior to beat 5 (f1191-2714) by 940
and 490 frames, so both beat boundaries are bit-identical by construction and
the selftest asserts that too rather than assuming it.

Judge on the printed `>> STAGE RESULT:` line.  Blender 5.2 exits 0 for a script
that raised, and so does python when someone wraps this in a shell pipeline.
"""

import argparse
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "_pca", os.path.join(ROOT, "tools", "r2731_pont_camera_apply.py"))
PCA = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(PCA)

_spec2 = importlib.util.spec_from_file_location(
    "_lss", os.path.join(ROOT, "tools", "lap_shotscale.py"))
LSS = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(LSS)

# ---------------------------------------------------------------- the offset --
# Same displacement R2-738 chose (du +20.0 m inboard, dz -7.5 m, interior to the
# zero-blocked plateau du 18..24 x dz -6..-11), but with WIDER RAMPS.
#
# R2-738's windows put a 91.2 m/s^2 (9.29 g) acceleration peak at f2193 -- 95 %
# of `tools/author_beats2_5.py`'s 95.9 m/s^2 craft limit, and 1.86x the shipped
# path's own 49.1 m/s^2.  The spike is entirely in the lateral OUT ramp, which
# R2-738 runs over 22 frames.  Widening it to 32 frames (and starting both in
# ramps 12 frames earlier) drops the peak to 47.7 m/s^2 -- BELOW the shipped
# path's own peak, so the fix costs nothing in the camera envelope instead of
# nearly exhausting it.  The occlusion result is unchanged: zero blocked frames,
# measured with `tools/r2731_pont_full_sightline.py`, whose --selftest
# reproduces two independent raycasts.
DU, U_WIN = 20.0, (2133.0, 2165.0, 2178.0, 2210.0)
DZ, Z_WIN = -7.5, (2133.0, 2166.0, 2190.0, 2222.0)

# The offset's own support, plus the 2-frame skirt the in-Blender keying uses.
LO, HI = int(U_WIN[0]) - 2, int(Z_WIN[3]) + 2              # 2131 .. 2224
BEAT5 = (1191, 2714)
W, H = 3840, 2160


def offset_at(f):
    """Windowed (lateral, vertical) displacement in the bridge's own frame."""
    _x, _y, _z, hdg, _k = PCA.WC.centreline(PCA.PONT_S)
    lat = (-math.sin(hdg), math.cos(hdg), 0.0)
    wu, wz = DU * PCA.win(f, U_WIN), DZ * PCA.win(f, Z_WIN)
    return (wu * lat[0], wu * lat[1], wz)


def car_centre(car, world_t, f):
    pos, _yaw, _p, _r, _v, _s = car.at(world_t[f])
    return [pos[0], pos[1], pos[2] + PCA.CAR_TOP_Z * 0.5]


def rebase(base, car, world_t, scale=1.0):
    """Live path + `scale` x the offset above, re-aimed on the car."""
    out = {}
    for f, k in base.items():
        if not (LO <= f <= HI):
            out[f] = dict(k)
            continue
        d = offset_at(f)
        p = [k["p"][i] + scale * d[i] for i in range(3)]
        q = PCA.look_quat(p, car_centre(car, world_t, f))
        out[f] = dict(f=f, p=p, q=list(q), lens=k["lens"])
    return out


def px_gap(pa, qa, pb, qb, lens, target):
    """How far apart two cameras put the same world point, in 4K pixels."""
    xa, ya = PCA.project(pa, qa, lens, target)
    xb, yb = PCA.project(pb, qb, lens, target)
    if xa is None or xb is None:
        return None
    return math.hypot(xa - xb, ya - yb)


def selftest(base_path):
    ok = True

    def chk(nm, cond, detail=""):
        nonlocal ok
        print("   %-52s %s  %s" % (nm, "PASS" if cond else "FAIL", detail))
        ok = ok and bool(cond)

    sheet = json.load(open(os.path.join(ROOT, "docs/beat_sheet.json")))
    world_t = LSS.build_world_time(sheet, sheet["total_frames"])
    car = LSS.Car(os.path.join(ROOT, "telemetry/telemetry.csv"))
    base = LSS.load_path(base_path)

    # 1. THE NULL. offset x 0 must reproduce the LIVE quaternion, in pixels.
    null = rebase(base, car, world_t, scale=0.0)
    worst = 0.0
    for f in range(LO, HI + 1):
        g = px_gap(base[f]["p"], base[f]["q"], null[f]["p"], null[f]["q"],
                   base[f]["lens"], car_centre(car, world_t, f))
        if g is not None:
            worst = max(worst, g)
    chk("NULL: re-aim reproduces the live path (offset x 0)", worst < 60.0,
        "worst %.1f px of %d" % (worst, W))
    dp0 = max(math.dist(base[f]["p"], null[f]["p"]) for f in base)
    chk("NULL: no frame moves at all", dp0 < 1e-12, "worst %.2e m" % dp0)

    cand = rebase(base, car, world_t, scale=1.0)

    # 2. Support. Nothing outside the window may move, bit for bit.
    bad = [f for f in base
           if not (LO <= f <= HI)
           and (base[f]["p"] != cand[f]["p"] or base[f]["q"] != cand[f]["q"])]
    chk("support is exactly f%d-%d" % (LO, HI), not bad,
        "%d stray frame(s)" % len(bad))

    # 3. Both beat-5 boundaries, named and checked rather than assumed.
    b = all(base[f]["p"] == cand[f]["p"] and base[f]["q"] == cand[f]["q"]
            for f in (BEAT5[0] - 1, BEAT5[0], BEAT5[1], BEAT5[1] + 1))
    chk("beat boundaries f1190/1191 and f2714/2715 identical", b)

    # 4. The offset never exceeds its own length.
    moved = max(math.dist(base[f]["p"], cand[f]["p"]) for f in range(LO, HI + 1))
    chk("no frame moves further than the offset", moved <= math.hypot(DU, DZ) + 1e-6,
        "worst %.3f m of %.3f" % (moved, math.hypot(DU, DZ)))

    # 5. The car must stay put in frame -- this is a position edit, not a re-frame.
    worst_fr = 0.0
    for f in range(LO, HI + 1):
        g = px_gap(base[f]["p"], base[f]["q"], cand[f]["p"], cand[f]["q"],
                   base[f]["lens"], car_centre(car, world_t, f))
        if g is not None:
            worst_fr = max(worst_fr, g)
    chk("the car holds its screen position", worst_fr < 60.0,
        "worst %.1f px of %d" % (worst_fr, W))

    # 6. Quaternion hemisphere. Blender lerps F-curves component-wise, so a
    #    sign flip between adjacent keys runs the rotation the long way round.
    flips = sum(1 for f in range(LO - 4, HI + 4)
                if sum(cand[f]["q"][i] * cand[f + 1]["q"][i] for i in range(4)) < 0)
    base_flips = sum(1 for f in range(LO - 4, HI + 4)
                     if sum(base[f]["q"][i] * base[f + 1]["q"][i] for i in range(4)) < 0)
    chk("no new quaternion hemisphere flip", flips <= base_flips,
        "candidate %d, live %d" % (flips, base_flips))

    # 7. Envelope, from tools/author_beats2_5.py's own bounds.
    vmax = max(car.col["speed_ms"])
    v_lim, a_lim = 1.5 * vmax, 2.0 * 4.89 * 9.81
    for nm, P in (("live", base), ("candidate", cand)):
        vs = [math.dist(P[f]["p"], P[f + 1]["p"]) * 24.0
              for f in range(LO - 8, HI + 8)]
        acc = [abs(vs[i + 1] - vs[i]) * 24.0 for i in range(len(vs) - 1)]
        print("        %-10s peak v %6.1f m/s (limit %.1f)   peak |a| %6.1f m/s^2 "
              "= %.2f g (limit %.1f = %.2f g)"
              % (nm, max(vs), v_lim, max(acc), max(acc) / 9.81, a_lim, a_lim / 9.81))
        if nm == "candidate":
            chk("camera envelope holds", max(vs) <= v_lim and max(acc) <= a_lim,
                "%.0f%% of the accel budget" % (100 * max(acc) / a_lim))

    print(">> STAGE RESULT: %s"
          % ("PONT_REBASE_SELFTEST_OK" if ok else "PONT_REBASE_SELFTEST_FAIL"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.path.join(ROOT, "render/film17_path.json"))
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(0 if selftest(a.base) else 1)

    sheet = json.load(open(os.path.join(ROOT, "docs/beat_sheet.json")))
    world_t = LSS.build_world_time(sheet, sheet["total_frames"])
    car = LSS.Car(os.path.join(ROOT, "telemetry/telemetry.csv"))
    base = LSS.load_path(a.base)
    cand = rebase(base, car, world_t)
    out = a.out if os.path.isabs(a.out) else os.path.join(ROOT, a.out)
    with open(out, "w") as fh:
        json.dump(dict(
            frames=len(cand),
            path=[cand[f] for f in sorted(cand)],
            note="R2-971. R2-738's bridge thread (du +%.1f m inboard, dz %.1f m) "
                 "rebased onto %s with WIDER ramps u%s z%s: zero blocked "
                 "frames as R2-738, peak |a| 47.7 m/s^2 against R2-738's 91.2 "
                 "and the shipped path's 49.1. Support f%d-%d, interior to "
                 "beat 5; both beat boundaries bit-identical."
                 % (DU, DZ, os.path.basename(a.base), U_WIN, Z_WIN, LO, HI)), fh)
    print(">> wrote %s" % out)
    print(">> STAGE RESULT: PONT_REBASE_WRITTEN")


if __name__ == "__main__":
    main()
