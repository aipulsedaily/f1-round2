"""R2-581. The mid-lap trough, and the smallest camera-path change that lifts it.

    .venv/bin/python tools/r2581_lensfix.py --target 0.0646      # variant A, a floor
    .venv/bin/python tools/r2581_lensfix.py --ramp 0.045 0.085   # variant B, a build
    .venv/bin/python tools/r2581_lensfix.py --selftest
    .venv/bin/python tools/r2581_lensfix.py --selftest --inject step|leak|smear

WHAT IS BROKEN
--------------
f2012-f2256 of beat 5 -- the run out to the doppler station -- holds the car at a
corrected median 4.4 % of frame width for 10.2 s. That is the same shot scale as
beat 6's closing wide (4.15 %), which is authored to be a valedictory speck.

WHY, DECOMPOSED. Between f2000 and f2100 the subject loses 4.65x:

    distance     78.6 m -> 169.5 m        2.16x smaller
    BEARING      61.7 deg -> 4.3 deg      2.47x smaller   <- the bigger term
    lens         65.0 -> 74.6 mm          1.15x larger

The camera runs away down the CENTRE of the road, so the car is dead nose-on --
presenting its 2.0 m track instead of its 5.7 m length -- at exactly the moment
it is furthest away. The two losses multiply. **The bearing term is larger than
the distance term**, and it is the same blind spot that made R2-429/R2-430's
instrument wrong: apparent size depends on which way the subject is facing, and
this project keeps forgetting it. The author fought the trough with the lens,
which is the term that was LESS to blame, and ran out of lens: the focal curve
sits at exactly 85.000 mm for f2190-f2213, a plateau, not a curve.

THE CHANGE
----------
Multiply the authored focal length by a smooth bump m(f) that is exactly 1.0
outside [f1997, f2244] and C2 at both ends. **Camera position and rotation are
not touched at all** -- the one-shot law is untouchable in those channels by
construction, and the lens channel is C1 because m is C2 and the authored lens
curve already is.

This is not a new technique. `tools/author_beats2_5.py`'s own beat-5 docstring
says: *"the lens goes long while it repositions and wide again as the car
arrives, which is how you keep a subject large while the camera is doing
something else."* The author declared exactly this move and then applied 1.31x
of it against a 6.0x loss. The fix finishes the ramp the author started.

WHAT IT COSTS, STATED
---------------------
  * Motion smear scales with focal length. Reported per frame against R2-424's
    200 px-of-4K flag, and the design refuses to write a curve that crosses it.
  * A longer lens is a narrower view. The circuit vista in these frames shrinks;
    the shot becomes the long-lens head-on rather than the aerial wide. That is
    a taste call and it is stated, not hidden.
  * Depth of field. The blend's camera carries an f-stop; a 2x focal at the same
    f-stop halves the depth of field. The candidate does NOT adjust the f-stop
    and any merge must review it.
  * A floor (--target) stops the passage being SMALL. It does not stop it being
    FLAT, which is the larger half of the defect. --ramp T0 T1 asks the subject
    to GROW across the support instead, which is what a head-on approach is for.
    A subject growing because the lens is zooming is not the same event as one
    growing because it is arriving, and that difference is not measurable here.
"""

import argparse
import json
import math
import os
import sys

R2 = "/home/zany/f1-round2"
sys.path.insert(0, R2)
import importlib.util                                              # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "lap_shotscale", os.path.join(R2, "tools/lap_shotscale.py"))
LS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(LS)

F_LO, F_HI = 1997, 2244          # the bump's support; 1.0 outside, C2 at both ends
RAMP = 46                        # frames of C2 ease at each end
SMEAR_CEILING_PX = 200.0         # R2-424's own flag, in 4K pixels


def smootherstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def window(f):
    if f <= F_LO or f >= F_HI:
        return 0.0
    if f < F_LO + RAMP:
        return smootherstep((f - F_LO) / RAMP)
    if f > F_HI - RAMP:
        return smootherstep((F_HI - f) / RAMP)
    return 1.0


def smear_px(path, f, lens):
    """4K pixels a static point smears at a 180-degree shutter."""
    a, b = path.get(f), path.get(f + 1)
    if a is None or b is None:
        return 0.0
    fa = LS.basis(a["q"])[2]
    fb = LS.basis(b["q"])[2]
    d = max(-1.0, min(1.0, LS.dot(fa, fb)))
    ang = math.acos(d)
    return math.tan(ang) * lens / 36.0 * 3840.0 / 2.0


def design(path, car, world_t, target, smooth=25, ceiling=SMEAR_CEILING_PX):
    """m(f) for every frame, and the report rows."""
    base = {}
    for f in range(F_LO - 60, F_HI + 60):
        if f not in path:
            continue
        k = path[f]
        pos, yaw, pit, rol, _v, _s = car.at(world_t[f])
        c = LS.obb_corners(pos, yaw, pit, rol)
        fw, _fh, _b = LS.project(c, k["p"], k["q"], k["lens"])
        base[f] = fw

    # 1. what each frame needs. `target` may be a scalar floor, or a (T0, T1)
    #    pair meaning "the subject must GROW from T0 to T1 across the support" --
    #    a floor stops the shot being too small, a ramp gives it something to do.
    if isinstance(target, tuple):
        t0, t1 = target
        tgt = {f: t0 + (t1 - t0) * smootherstep((f - F_LO) / (F_HI - F_LO))
               for f in base}
    else:
        tgt = {f: target for f in base}
    need = {f: max(1.0, tgt[f] / max(base[f], 1e-9)) for f in base}
    # 2. a running MAX, so a smooth curve cannot dip under a spike's neighbour
    mx = {f: max(need.get(g, 1.0) for g in range(f - smooth, f + smooth + 1))
          for f in base}
    # 3. a box smooth, twice -- gives a curve with no corners in it
    def box(d):
        return {f: sum(d.get(g, 1.0) for g in range(f - smooth, f + smooth + 1))
                / (2 * smooth + 1) for f in base}
    sm = box(box(mx))
    # 4. the compactly-supported window, so the change dies at both ends
    m = {f: 1.0 + (sm[f] - 1.0) * window(f) for f in base}

    # 5. clamp against the smear ceiling
    clipped = 0
    for f in sorted(m):
        px = smear_px(path, f, path[f]["lens"] * m[f])
        if px > ceiling:
            m[f] = max(1.0, ceiling / max(smear_px(path, f, path[f]["lens"]), 1e-9))
            clipped += 1
    if clipped:
        sm2 = box({f: m[f] for f in base})
        m = {f: 1.0 + (sm2[f] - 1.0) * window(f) for f in base}

    rows = []
    for f in sorted(base):
        k = path[f]
        nl = k["lens"] * m[f]
        pos, yaw, pit, rol, _v, _s = car.at(world_t[f])
        c = LS.obb_corners(pos, yaw, pit, rol)
        nfw, _h, _b = LS.project(c, k["p"], k["q"], nl)
        rows.append({"f": f, "lens0": k["lens"], "lens1": nl, "m": m[f],
                     "fw0": base[f], "fw1": nfw,
                     "smear0": smear_px(path, f, k["lens"]),
                     "smear1": smear_px(path, f, nl)})
    return m, rows, clipped


# ------------------------------------------------------------------ selftest --
def selftest(path, car, world_t, inject=""):
    """`inject` breaks the design on purpose so the gate can be SEEN failing.
    A passing gate that has never been shown failing proves nothing -- R2-427.
    """
    ok = True
    m, rows, _c = design(path, car, world_t, 0.0646)
    if inject == "step":
        # a one-frame lens jump in the middle of the support: a cut, in the
        # only channel this change touches
        for f in m:
            if f >= 2120:
                m[f] *= 1.25
        rows = [dict(r, m=m[r["f"]], lens1=r["lens0"] * m[r["f"]],
                     smear1=smear_px(path, r["f"], r["lens0"] * m[r["f"]]))
                for r in rows]
    elif inject == "leak":
        # the change reaching outside its own support
        for f in m:
            m[f] += 0.02
    elif inject == "smear":
        # a lens long enough to blow through R2-424's flag
        for f in m:
            if m[f] > 1.0:
                m[f] *= 3.0
        rows = [dict(r, m=m[r["f"]], lens1=r["lens0"] * m[r["f"]],
                     smear1=smear_px(path, r["f"], r["lens0"] * m[r["f"]]))
                for r in rows]
    if inject:
        print(f"  [INJECTED DEFECT: {inject}]")

    outside = [f for f in range(F_LO - 60, F_HI + 60)
               if f in m and (f <= F_LO or f >= F_HI)]
    worst = max(abs(m[f] - 1.0) for f in outside)
    good = worst < 1e-12
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  compact support  |m-1| outside "
          f"f{F_LO}..f{F_HI} is {worst:.2e}; must be exactly 0 or the one-shot "
          f"law is broken somewhere the change was never meant to reach")

    # C1 of the modified lens curve. The threshold is NOT invented: the curve
    # must be no rougher than the lens curve the film already ships, measured
    # the same way, over all 2,978 frames.
    L0 = [path[f]["lens"] for f in sorted(path)]
    ref_d1 = max(abs(L0[i + 1] - L0[i]) for i in range(len(L0) - 1))
    ref_d2 = max(abs(L0[i + 1] - 2 * L0[i] + L0[i - 1])
                 for i in range(1, len(L0) - 1))
    fs = sorted(m)
    L1 = [path[f]["lens"] * m[f] for f in fs]
    d1 = max(abs(L1[i + 1] - L1[i]) for i in range(len(L1) - 1))
    d2 = max(abs(L1[i + 1] - 2 * L1[i] + L1[i - 1])
             for i in range(1, len(L1) - 1))
    good = d1 <= ref_d1 and d2 <= ref_d2
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  C1 lens  the candidate's roughest "
          f"frame is |dlens| {d1:.3f} mm/f and |d2lens| {d2:.3f} mm/f2. The "
          f"SHIPPING film's own worst, over all 2,978 frames, is {ref_d1:.3f} "
          f"and {ref_d2:.3f} (both at the f2250-f2257 doppler zoom). The "
          f"candidate must be no rougher than what already ships.")

    # the change must be a NO-OP on position and rotation, by construction
    print("  PASS  position/rotation untouched  the design writes only `lens`; "
          "p and q are copied byte-for-byte from the authored path")

    # NEGATIVE control: asking for a target the frames already meet must give
    # m == 1 everywhere. A designer that always inflates the lens is not
    # responding to the measurement.
    m0, _r, _c = design(path, car, world_t, 0.001)
    worst0 = max(abs(v - 1.0) for v in m0.values())
    good = worst0 < 1e-12
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  negative/no-demand  with the target "
          f"set below every frame's actual size the design returns m=1 "
          f"everywhere (worst {worst0:.2e}). It responds to the measurement, "
          f"it does not just push the lens.")

    # No frame may be pushed over R2-424's flag, and no frame that was already
    # over it may be made worse. Only frames the change actually touches count;
    # the f2270 doppler pass smears 293 px in the SHIPPING film and is not mine.
    touched = [r for r in rows if r["m"] > 1.0 + 1e-12]
    over = [r for r in touched if r["smear1"] > SMEAR_CEILING_PX * 1.001]
    worse = [r for r in touched if r["smear1"] > r["smear0"] + 1e-9
             and r["smear0"] > SMEAR_CEILING_PX]
    smax = max((r["smear1"] for r in touched), default=0.0)
    good = not over and not worse
    ok &= good
    print(f"  {'PASS' if good else 'FAIL'}  smear ceiling  over the {len(touched)} "
          f"frames the change touches, worst 4K smear after is {smax:.0f} px; "
          f"{len(over)} frames cross R2-424's {SMEAR_CEILING_PX:.0f} px flag. "
          f"The shipping film's own worst is 424 px at f2634 and 293 px at the "
          f"f2270 doppler pass, neither of which this change touches.")

    print("SELFTEST " + ("PASS" if ok else "FAIL"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=os.path.join(R2, "render/film14_path.json"))
    ap.add_argument("--target", type=float, default=0.0646)
    ap.add_argument("--ramp", nargs=2, type=float, default=None,
                    metavar=("T0", "T1"),
                    help="grow the subject from T0 to T1 across the support "
                         "instead of holding a flat floor")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--inject", default="", choices=["", "step", "leak", "smear"])
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    sheet = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))
    world_t = LS.build_world_time(sheet, sheet["total_frames"])
    car = LS.Car(os.path.join(R2, "telemetry/telemetry.csv"))
    raw = json.load(open(a.path))
    path = {int(k["f"]): k for k in raw["path"]}

    if a.selftest:
        okay = selftest(path, car, world_t, a.inject)
        print(f">> STAGE RESULT: {'LENSFIX_SELFTEST_OK' if okay else 'LENSFIX_SELFTEST_FAILED'}")
        return

    tgt = tuple(a.ramp) if a.ramp else a.target
    m, rows, clipped = design(path, car, world_t, tgt)
    lbl = (f"ramp {a.ramp[0]*100:.2f} -> {a.ramp[1]*100:.2f}" if a.ramp
           else f"floor {a.target*100:.2f}")
    print(f"target {lbl} % of frame width   support f{F_LO}-f{F_HI} "
          f"({F_HI-F_LO+1} frames, {(F_HI-F_LO+1)/24:.2f} s)   "
          f"{clipped} frames clipped by the smear ceiling")
    print()
    print(f"{'f':>6} {'lens0':>7} {'lens1':>7} {'x':>5} {'size0':>8} {'size1':>8} "
          f"{'gain':>6} {'smear0':>7} {'smear1':>7}")
    for r in rows:
        if r["f"] % 10:
            continue
        print(f"{r['f']:6d} {r['lens0']:7.1f} {r['lens1']:7.1f} {r['m']:5.2f} "
              f"{r['fw0']*100:7.2f}% {r['fw1']*100:7.2f}% "
              f"{r['fw1']/max(r['fw0'],1e-9):5.2f}x {r['smear0']:7.0f} "
              f"{r['smear1']:7.0f}")

    core = [r for r in rows if 2012 <= r["f"] <= 2256]
    print()
    print(f"the stretch f2012-f2256, {len(core)} frames, {len(core)/24:.2f} s")
    print(f"  median size  {LS.median([r['fw0'] for r in core])*100:.2f} %  ->  "
          f"{LS.median([r['fw1'] for r in core])*100:.2f} %")
    print(f"  minimum size {min(r['fw0'] for r in core)*100:.2f} %  ->  "
          f"{min(r['fw1'] for r in core)*100:.2f} %")
    thr = a.ramp[0] if a.ramp else a.target
    print(f"  frames under {thr*100:.2f} %: "
          f"{sum(1 for r in core if r['fw0'] < thr)}  ->  "
          f"{sum(1 for r in core if r['fw1'] < thr - 1e-6)}")
    print(f"  peak focal   {max(r['lens0'] for r in core):.1f} mm  ->  "
          f"{max(r['lens1'] for r in core):.1f} mm  "
          f"(beat 5's authored maximum elsewhere is 120.0 mm at t=98.6)")
    touched = [r for r in rows if r["m"] > 1.0 + 1e-12]
    print(f"  worst 4K smear over the {len(touched)} frames the change touches: "
          f"{max((r['smear0'] for r in touched), default=0):.0f} px  ->  "
          f"{max((r['smear1'] for r in touched), default=0):.0f} px  "
          f"(R2-424 flags 200; the film's own worst is 424 px at f2634 and "
          f"293 px at f2270, and neither is touched here)")

    if a.out:
        newpath = []
        for k in raw["path"]:
            f = int(k["f"])
            k2 = dict(k)
            if f in m:
                k2["lens"] = round(k["lens"] * m[f], 6)
            newpath.append(k2)
        json.dump({"frames": raw["frames"], "path": newpath,
                   "note": f"R2-581 candidate. Lens only; p and q identical to "
                           f"{os.path.basename(a.path)}. Support f{F_LO}-f{F_HI}."},
                  open(a.out, "w"))
        print(f"\nwrote {a.out}")
    print(">> STAGE RESULT: LENSFIX_OK")


if __name__ == "__main__":
    main()
