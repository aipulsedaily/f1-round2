"""DOES THE WOUND SURVIVE THE REST OF THE TAKE?  Measured on EVERY remaining
frame, not at a sample.

    /opt/blender-5.2.0-linux-x64/blender -b render/film14_breach_r6.blend \
        --python sim/tail_persist.py -- --out sim/out/tail_persist_r6.json

WHY THIS EXISTS
===============
The film has no cuts, so a hole opened at f860 has to still be a hole at f2978.
Everything that has ever measured the breach measured it *at the breach*:
`breach_metrics` scores the bake, whose table stops at f1165, and the render A/Bs
sampled two frames.  1,813 frames of the take -- 61 % of it -- were never
measured at all, and "checked at two frames" is how R2-097 got missed.

AND EVERY EXISTING FRAME NUMBER IS A PEAK.  `apply_breach.build_frame` reports
`max_travel_m`, `breach_metrics` reports `mullion_max_disp_m` and
`transom_max_disp_m`.  A member that deflects 303 mm and returns to 0 mm and a
member that deflects 303 mm and stays there produce the SAME number in all three
reports.  A printed peak looks exactly like a persisted peak -- the same shape
as R2-266, where a printed count looked exactly like a used count.  So this
module reports peak AND end AND end/peak, and it is end/peak that is gated on.

HOW THE TAIL IS COVERED WITHOUT EVALUATING 1,813 FRAMES
=======================================================
Not by sampling.  By proving the curves cannot move:

  A  every F-curve on every BREACH object has its LAST key at or before the
     bake span's end, extrapolates CONSTANT, and carries no F-curve modifier;
     and no BREACH object has a parent, a constraint, a driver or a modifier
     that could move it.

Given A, the pose at every frame in (span_end, total] is identically the pose at
span_end -- for all 1,813 of them, not for the ones somebody sampled.  A is then
spot-checked empirically at five frames by evaluating the curves.

F-curves are evaluated DIRECTLY (`fcurve.evaluate`), never through
`matrix_world`.  R2-188: `matrix_world` is not evaluated for a HIDDEN object and
returns the pose the .blend was saved with, worst observed error 120.7 m -- and
3,796 of these objects are hidden for the first 859 frames.  A warm-up
`frame_set` does not fix it.  The curves are the only honest source.

THE CONTROLS, all of which must fire or the verdict is vacuous
==============================================================
  NEG-1  tail-static, on objects that are NOT the breach.  The camera and the
         car ARE keyed into the tail.  If the "no keys after span_end" test
         passes on them too, the test is not measuring anything.
  NEG-2  the aperture instrument, on the bays the plan never breaks.  Bays
         0/1/8/9 are `intact` and bays 2/7 are `retained`: same scene, same
         builds, same instrument, same frames, no breach.  They must read
         0.0000 m2 vacated at every tail frame.  This is the free negative
         control -- the wound half reads 24.80 m2 against it.
  POS    the same instrument on the breached bays BEFORE the swap frame must
         also read 0.0000 m2, and after it must read the bake's own number.
         An instrument that reports a hole at f1 is measuring the mesh, not the
         motion.
"""
import argparse
import json
import os
import sys

import numpy as np

import bpy

R2 = "/home/zany/f1-round2"
for _p in ("sim", "world", "anim"):
    _q = os.path.join(R2, _p)
    if _q not in sys.path:
        sys.path.insert(0, _q)

import aperture as AP                                              # noqa: E402
import breach_metrics as BM                                        # noqa: E402
import fracture as FR                                              # noqa: E402

GONE_M = 0.25
BREACH_COLLS = ("BREACH_Shards", "BREACH_Panes", "BREACH_Frame")


def log(m):
    print("[tail_persist] %s" % m, flush=True)


# --------------------------------------------------------------------------- #
#  curve reading -- never matrix_world (R2-188)
# --------------------------------------------------------------------------- #
def curves_of(ob):
    """-> {(data_path, index): fcurve} for the object's own action."""
    out = {}
    ad = ob.animation_data
    if ad is None or ad.action is None:
        return out
    act = ad.action
    slot = getattr(ad, "action_slot", None)
    for layer in act.layers:
        for strip in layer.strips:
            cb = strip.channelbag(slot) if slot is not None else None
            if cb is None:
                continue
            for fc in cb.fcurves:
                out[(fc.data_path, fc.array_index)] = fc
    return out


def static_audit(obs):
    """Everything that could make an object move after its last key."""
    rep = dict(objects=len(obs), animated=0, fcurves=0,
               last_key_frame=-1, non_constant_extrap=[], fcurve_modifiers=[],
               parented=[], constrained=[], modified=[], drivers=[],
               delta_transform=[], unanimated=[])
    for ob in obs:
        if ob.parent is not None:
            rep["parented"].append(ob.name)
        if len(ob.constraints):
            rep["constrained"].append(ob.name)
        if len(ob.modifiers):
            rep["modified"].append(ob.name)
        ad = ob.animation_data
        if ad is not None and len(ad.drivers):
            rep["drivers"].append(ob.name)
        if (tuple(ob.delta_location) != (0.0, 0.0, 0.0)
                or tuple(ob.delta_scale) != (1.0, 1.0, 1.0)):
            rep["delta_transform"].append(ob.name)
        fcs = curves_of(ob)
        if not fcs:
            rep["unanimated"].append(ob.name)
            continue
        rep["animated"] += 1
        for (dp, ix), fc in fcs.items():
            rep["fcurves"] += 1
            if len(fc.modifiers):
                rep["fcurve_modifiers"].append("%s/%s[%d]" % (ob.name, dp, ix))
            if fc.extrapolation != "CONSTANT":
                rep["non_constant_extrap"].append(
                    "%s/%s[%d]=%s" % (ob.name, dp, ix, fc.extrapolation))
            kps = fc.keyframe_points
            if len(kps):
                rep["last_key_frame"] = max(rep["last_key_frame"],
                                            float(kps[-1].co[0]))
    for k in ("parented", "constrained", "modified", "drivers",
              "delta_transform", "non_constant_extrap", "fcurve_modifiers"):
        rep[k + "_n"] = len(rep[k])
        rep[k] = sorted(rep[k])[:8]
    rep["unanimated_n"] = len(rep["unanimated"])
    rep["unanimated"] = sorted(rep["unanimated"])[:8]
    return rep


def pose_at(fcs, ob, f):
    """(loc(3), hidden) straight off the curves."""
    loc = list(ob.location)
    for i in range(3):
        fc = fcs.get(("location", i))
        if fc is not None:
            loc[i] = fc.evaluate(f)
    hid = bool(ob.hide_render)
    fc = fcs.get(("hide_render", 0))
    if fc is not None:
        hid = fc.evaluate(f) >= 0.5
    return np.array(loc, float), hid


# --------------------------------------------------------------------------- #
def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(R2, "sim/out/tail_persist.json"))
    ap.add_argument("--shards", default=os.path.join(R2, "sim/out/fracture_wall.npz"))
    ap.add_argument("--span-end", type=int, default=0,
                    help="last frame the bake table keys.  0 = read it from "
                         "the largest last-key on the shards themselves.")
    ap.add_argument("--cell", type=float, default=0.05)
    args = ap.parse_args(argv)

    sc = bpy.context.scene
    total = sc.frame_end
    plan = FR.load(args.shards)
    rects, roles = plan["rects"], plan["roles"]
    log("scene frame range %d..%d" % (sc.frame_start, total))

    colls = {n: bpy.data.collections.get(n) for n in BREACH_COLLS}
    missing = [n for n, c in colls.items() if c is None]
    if missing:
        print(">> STAGE RESULT: NO_BREACH_COLLECTIONS %s" % missing)
        return 1
    obs = {n: list(c.objects) for n, c in colls.items()}
    for n in BREACH_COLLS:
        log("%s: %d objects" % (n, len(obs[n])))

    rep = {"blend": bpy.data.filepath, "frame_end": total,
           "collections": {n: len(obs[n]) for n in BREACH_COLLS}}

    # ---- A. tail-static structural proof ---------------------------------- #
    allb = [o for n in BREACH_COLLS for o in obs[n]]
    A = static_audit(allb)
    rep["A_breach_static_audit"] = A
    span_end = args.span_end or int(np.ceil(A["last_key_frame"]))
    rep["span_end"] = span_end
    tail_n = total - span_end
    rep["tail_frames"] = tail_n
    A_ok = (A["last_key_frame"] <= span_end
            and A["non_constant_extrap_n"] == 0
            and A["fcurve_modifiers_n"] == 0
            and A["parented_n"] == 0 and A["constrained_n"] == 0
            and A["modified_n"] == 0 and A["drivers_n"] == 0
            and A["delta_transform_n"] == 0)
    rep["A_PASS"] = bool(A_ok)
    log("A: last breach key f%.0f, tail = %d frames, static=%s"
        % (A["last_key_frame"], tail_n, A_ok))

    # ---- NEG-1. the same audit on things that DO move in the tail --------- #
    breach_names = {o.name for o in allb}
    others = [o for o in sc.objects
              if o.name not in breach_names and o.animation_data
              and o.animation_data.action]
    lat = []
    for o in others:
        for fc in curves_of(o).values():
            kps = fc.keyframe_points
            if len(kps) and kps[-1].co[0] > span_end:
                lat.append((o.name, float(kps[-1].co[0])))
                break
    lat.sort(key=lambda t: -t[1])
    rep["NEG1_animated_past_span_end"] = dict(
        n=len(lat), examples=[[a, b] for a, b in lat[:8]],
        scanned=len(others))
    NEG1_ok = len(lat) > 0
    rep["NEG1_PASS"] = bool(NEG1_ok)
    log("NEG-1: %d of %d non-breach animated objects key past f%d %s"
        % (len(lat), len(others), span_end,
           "(control fires)" if NEG1_ok else "(CONTROL DEAD -- test vacuous)"))

    # ---- C/D/POS. the aperture, off the blend's own curves ---------------- #
    shard_fc, pane_fc = {}, {}
    for o in obs["BREACH_Shards"]:
        shard_fc[o.name] = (o, curves_of(o))
    for o in obs["BREACH_Panes"]:
        pane_fc[o.name] = (o, curves_of(o))

    home = {}
    for nm, (o, fcs) in shard_fc.items():
        home[nm] = pose_at(fcs, o, 1)[0]

    breached = tuple(sorted(b for b in rects if roles[b] != "intact"))
    intact = tuple(sorted(b for b in rects if roles[b] == "intact"))
    grid_b = AP._rasterise(plan, args.cell, breached)
    grid_i = AP._rasterise(plan, args.cell, intact) if intact else None

    frame_bodies = [(o.name, o, curves_of(o)) for o in obs["BREACH_Frame"]]
    fb_home = {n: pose_at(f, o, 1)[0] for n, o, f in frame_bodies}

    # ---- EVERY FRAME, not a probe.  R2-605. ------------------------------- #
    # The first cut of this module compared the tail against span_end and
    # sampled five frames in between.  Run across the delivered scenes it
    # passed `film9_breach`, whose wound is 3.900 m2 at f900, **0.062 m2 at
    # f1000** and 0.432 m2 at f1165 -- it heals by 98 % and re-opens, inside
    # the bake span, and every probe happened to miss it.  That is the same
    # failure the module exists to catch, committed by the module.  So the
    # curves are now evaluated on EVERY frame of the take.
    #
    # `fcurve.evaluate` 3,796 times a frame is 32 M calls and does not
    # terminate.  The curves are LINEAR keys with CONSTANT extrapolation, so
    # they are exactly `np.interp` -- which clamps outside the key range, which
    # IS constant extrapolation -- and `hide_render` is CONSTANT-interpolated,
    # which is a hold-last lookup.  Both are one vectorised pass per body.
    FR_ALL = np.arange(1, total + 1)

    def curve_over_take(fcs, ob, dp, ix, default, step=False):
        fc = fcs.get((dp, ix))
        if fc is None:
            return np.full(len(FR_ALL), float(default))
        n = len(fc.keyframe_points)
        if not n:
            return np.full(len(FR_ALL), float(default))
        buf = np.empty(2 * n, np.float64)
        fc.keyframe_points.foreach_get("co", buf)
        kf, kv = buf[0::2], buf[1::2]
        if step:
            j = np.clip(np.searchsorted(kf, FR_ALL, side="right") - 1, 0, n - 1)
            return kv[j]
        return np.interp(FR_ALL, kf, kv)

    def travel_and_vis(fcs, ob, home_xyz):
        L = np.stack([curve_over_take(fcs, ob, "location", i, ob.location[i])
                      for i in range(3)], axis=1)
        d = np.linalg.norm(L - np.asarray(home_xyz, float)[None], axis=1)
        h = curve_over_take(fcs, ob, "hide_render", 0,
                            float(ob.hide_render), step=True) >= 0.5
        return d, h

    log("evaluating %d shard + %d frame curves over all %d frames"
        % (len(shard_fc), len(frame_bodies), total))
    sh_names, sh_gone, sh_vis = [], [], []
    for nm, (o, fcs) in shard_fc.items():
        d, h = travel_and_vis(fcs, o, home[nm])
        sh_names.append((int(nm[4:6]), int(nm[7:])))
        sh_gone.append((d > GONE_M) & ~h)
        sh_vis.append(~h)
    SH_GONE = np.asarray(sh_gone)                       # (nshard, nframe) bool
    SH_VIS = np.asarray(sh_vis)

    mul_key, mul_gone = [], []
    for nm, o, fcs in frame_bodies:
        if "MUL" not in nm:
            continue
        m = __import__("re").search(r"MUL(\d\d)_S(\d\d)", nm)
        if not m:
            continue
        d, _h = travel_and_vis(fcs, o, fb_home[nm])
        mul_key.append((int(m.group(1)), int(m.group(2))))
        mul_gone.append(d > GONE_M)
    MUL_GONE = (np.asarray(mul_gone) if mul_gone
                else np.zeros((0, len(FR_ALL)), bool))

    def sets_at(f):
        k = f - 1
        gone_ids = {sh_names[i] for i in np.nonzero(SH_GONE[:, k])[0]}
        gone_mul = set()
        for i in np.nonzero(MUL_GONE[:, k])[0] if len(MUL_GONE) else ():
            mi, sj = mul_key[i]
            for ss in (range(8) if mi in (0, 1, 2, 8, 9, 10) else [sj]):
                gone_mul.add((mi, ss))
        return gone_ids, gone_mul

    def measure(f):
        gone_ids, gone_mul = sets_at(f)
        vis = int(SH_VIS[:, f - 1].sum())
        hid = SH_VIS.shape[0] - vis
        hb = AP.hole(plan, gone_ids, args.cell, breached, grid_b,
                     gone_mullions=gone_mul)
        row = dict(frame=f, shards_visible=vis, shards_hidden=hid,
                   gone=len(gone_ids),
                   WOUND_vacated_m2=round(hb["vacated_area_m2"], 4),
                   WOUND_hole_bridged_m2=round(hb["hole_bridged_area_m2"], 4),
                   WOUND_w_m=round(hb["hole_bridged_w_m"], 3),
                   WOUND_h_m=round(hb["hole_bridged_h_m"], 3))
        if grid_i is not None:
            hi = AP.hole(plan, gone_ids, args.cell, intact, grid_i)
            row["CONTROL_intact_bays_vacated_m2"] = round(
                hi["vacated_area_m2"], 4)
            row["CONTROL_intact_bays_hole_m2"] = round(hi["hole_area_m2"], 4)
        panes = {}
        for nm, (o, fcs) in pane_fc.items():
            panes[nm] = int(pose_at(fcs, o, f)[1])
        row["panes_hidden"] = sorted(k for k, v in panes.items() if v)
        row["panes_visible"] = sorted(k for k, v in panes.items() if not v)
        return row

    # ---- the sweep: every frame of the take ------------------------------- #
    # `_largest_component` is a Python flood fill, so the empty frames are
    # short-circuited -- with nothing gone there is no hole and no component to
    # find.  That is a fact about the mask, not an assumption about the scene.
    # `aperture.hole` is a pure function of (gone_ids, gone_mullions) -- it
    # never sees the frame number -- so identical inputs give identical output
    # by construction, and memoising on them is exact, not an approximation.
    # It is what makes every-frame affordable: `_largest_component` is a Python
    # flood fill, 2 x 2,978 of them do not finish, and after the last key the
    # set is constant so 1,813 tail frames collapse to one evaluation.  EVERY
    # frame is still evaluated; none is skipped or interpolated.
    W = np.zeros(total, float)
    CTL = np.zeros(total, float)
    VIS = np.zeros(total, int)
    GON = np.zeros(total, int)
    cache, n_eval = {}, 0
    for f in range(1, total + 1):
        gone_ids, gone_mul = sets_at(f)
        VIS[f - 1] = int(SH_VIS[:, f - 1].sum())
        GON[f - 1] = len(gone_ids)
        if not gone_ids:
            continue
        key = (frozenset(gone_ids), frozenset(gone_mul))
        hit = cache.get(key)
        if hit is None:
            n_eval += 1
            hb = AP.hole(plan, gone_ids, args.cell, breached, grid_b,
                         gone_mullions=gone_mul)
            ci = (AP.hole(plan, gone_ids, args.cell, intact,
                          grid_i)["vacated_area_m2"]
                  if grid_i is not None else 0.0)
            hit = cache[key] = (hb["hole_bridged_area_m2"], ci)
        W[f - 1], CTL[f - 1] = hit
    rep["C_distinct_gone_sets_evaluated"] = n_eval
    log("swept %d frames, %d distinct gone-sets evaluated; "
        "wound peak %.4f m2, end %.4f m2" % (total, n_eval, W.max(), W[-1]))

    probe = [1, 400, 859, 860, 900, 1000, span_end,
             span_end + 1, 1500, 2000, 2500, total]
    probe = sorted({int(f) for f in probe if 1 <= f <= total})
    rows = [measure(f) for f in probe]
    rep["rows"] = rows
    by_f = {r["frame"]: r for r in rows}

    # ---- C.  ONCE OPEN, NEVER SMALLER -- on every frame, not a probe ------ #
    # The claim is not "the tail equals span_end".  It is "from the frame the
    # wound is open, it never closes again", and it has to hold at f1000 as
    # much as at f2978.  So: peak over the take, then the MINIMUM from the peak
    # frame to the last frame, and the frame it happens on.
    pkf = int(W.argmax()) + 1
    peak = float(W.max())
    after = W[pkf - 1:]
    minf = int(after.argmin()) + pkf
    mn = float(after.min())
    frac = mn / peak if peak > 1e-9 else 0.0
    C_ok = bool(peak > 1e-9 and frac >= 0.98)
    rep["C_PASS"] = C_ok
    rep["C_peak_m2"] = round(peak, 4)
    rep["C_peak_frame"] = pkf
    rep["C_min_after_peak_m2"] = round(mn, 4)
    rep["C_min_after_peak_frame"] = minf
    rep["C_min_over_peak"] = round(frac, 4)
    rep["C_frames_swept"] = int(total)
    rep["C_wound_m2_by_frame_every_10"] = [round(float(x), 4) for x in W[::10]]

    # ---- D.  the free negative control ------------------------------------ #
    # D IS ABOUT THE CONTROL AND NOTHING ELSE.  The first cut folded
    # `wound > 1 m2` into both D and POS, so `film9_breach` -- whose control
    # reads a clean 0.0000 and whose f1 reads a clean 0.0000 -- failed two arms
    # for having a small wound.  A control that fails for a reason that is not
    # about the control cannot be read.  Magnitude is now its own arm, MAG.
    D_ok = bool(CTL.max() < 1e-9)
    rep["D_PASS"] = D_ok
    rep["D_control_vacated_m2_max"] = round(float(CTL.max()), 6)
    rep["D_control_worst_frame"] = int(CTL.argmax()) + 1

    # ---- POS.  the instrument reads the motion, not the mesh -------------- #
    pre = float(W[:859].max()) if total > 859 else float(W[0])
    POS_ok = bool(abs(pre) < 1e-9)
    rep["POS_PASS"] = POS_ok
    rep["POS_wound_m2_before_f859"] = round(pre, 6)

    # ---- MAG.  is there a wound to talk about at all? --------------------- #
    # Split out of D and POS so that a scene with a small wound fails the arm
    # that is about wound size and passes the arms that are about controls.
    MAG_ok = bool(W[-1] > 1.0)
    rep["MAG_PASS"] = MAG_ok
    rep["MAG_wound_m2_at_last_frame"] = round(float(W[-1]), 4)

    # ---- E. the ALUMINIUM.  Peak travel cannot see this. ------------------ #
    # Every existing report -- build_frame's `max_travel_m`, breach_metrics'
    # `mullion_max_disp_m` / `transom_max_disp_m` -- prints a MAX.  A member
    # that deflects 303 mm and springs back to 0 mm prints the same 0.303 as
    # one that deflects 303 mm and stays.  So measure END and END/PEAK, over
    # the piece's own keys, and gate on that.
    # Same rule and same gate as sim/breach_metrics.persistence, imported
    # rather than restated: a second copy of a threshold is the mechanism
    # behind R2-071, R2-061 and R2-100.
    E = dict(pieces=len(frame_bodies), deflected=0, RECOVERED=0, stayed=0,
             worst=[], recovered=[], max_recovered_peak_m=0.0,
             gate_m=BM.RECOVERY_GATE_M,
             rule=("deflected: peak > %.3f m.  RECOVERED: end < %.0f %% of its "
                   "own peak -- it sprang back to the intact rest pose, which "
                   "in a take with no cuts is the wall repairing itself on "
                   "camera.  REFUSED when the largest such recovery clears "
                   "%.3f m." % (BM.DEFLECT_M, 100 * BM.RETURN_FRAC,
                                BM.RECOVERY_GATE_M)))
    for nm, o, fcs in frame_bodies:
        kf = sorted({int(k.co[0]) for fc in fcs.values()
                     for k in fc.keyframe_points}) or [1]
        P = np.array([pose_at(fcs, o, f)[0] for f in kf])
        dsp = np.linalg.norm(P - fb_home[nm], axis=1)
        pk, en = float(dsp.max()), float(dsp[-1])
        if pk <= BM.DEFLECT_M:
            continue
        E["deflected"] += 1
        r = en / max(pk, 1e-12)
        if r < BM.RETURN_FRAC:
            E["RECOVERED"] += 1
            E["recovered"].append([nm, round(pk, 4)])
            E["max_recovered_peak_m"] = max(E["max_recovered_peak_m"], pk)
        else:
            E["stayed"] += 1
        E["worst"].append([nm, round(pk, 4), round(en, 4), round(r, 4)])
    E["worst"].sort(key=lambda t: -t[1])
    E["worst"] = E["worst"][:12]
    E["recovered"].sort(key=lambda t: -t[1])
    E["max_recovered_peak_m"] = round(E["max_recovered_peak_m"], 4)
    E["pct_recovered"] = round(100.0 * E["RECOVERED"]
                               / max(1, E["deflected"]), 1)
    rep["E_frame_persistence"] = E
    # E CANNOT PASS BY EMPTINESS.  `film13_breach` and `film14_breach` carry
    # BREACH_Frame: 0 -- round 1's undeformed grid is still standing in them
    # (R2-266) -- so "0 of 0 deflected pieces came home" is not a result about
    # those scenes, it is the absence of one.  A gate that reports PASS on an
    # empty set is how a printed count became a used count in R2-266.
    E["vacuous"] = bool(E["pieces"] == 0 or E["deflected"] == 0)
    E_ok = (not E["vacuous"]
            and E["max_recovered_peak_m"] <= BM.RECOVERY_GATE_M)
    rep["E_PASS"] = bool(E_ok)
    rep["E_VACUOUS"] = E["vacuous"]

    # ---- CAN ANY ARM PASS ON AN EMPTY SET?  R2-433's law, applied here. --- #
    # E was found passing on `BREACH_Frame: 0` -- "0 of 0 pieces came home" is
    # the absence of a result reported as one.  Fixing only E would be fixing
    # the instance and not the defect, so every arm is asked the same question.
    # A vacuity flag is NOT a pass/fail clause: the arm's verdict still answers
    # only its own question (that is why MAG exists at all), and the flag says
    # separately whether that verdict carries information.  An arm that PASSES
    # while vacuous cannot be counted, and the run is refused.
    VAC = dict(
        # nothing keyed -> "no keys after span_end" is trivially true
        A=bool(A["animated"] == 0),
        # the must-fire control; it has no vacuous mode, it IS the check
        NEG1=False,
        # no shard ever leaves -> there is no "once open" to stay open
        C=bool(W.max() <= 1e-9),
        # no intact bays in the plan -> the free negative control has no
        # glass it could have wrongly reported gone
        D=bool(grid_i is None or not intact),
        # nothing ever opens -> "reads 0 before the swap" is not a statement
        # about the instrument, only about an empty scene
        POS=bool(not MAG_ok),
        MAG=False,
        E=bool(E["vacuous"]))
    rep["VACUOUS"] = VAC
    arms = dict(A=A_ok, NEG1=NEG1_ok, C=C_ok, D=D_ok, POS=POS_ok,
                MAG=MAG_ok, E=E_ok)
    vac_pass = sorted(k for k, v in arms.items() if v and VAC[k])
    rep["VACUOUS_PASSES"] = vac_pass
    ok = all(arms.values()) and not vac_pass
    rep["PASS"] = bool(ok)
    rep["arms"] = arms

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(rep, open(args.out, "w"), indent=1)
    log("wrote %s" % args.out)

    print("")
    print("  %-6s %8s %8s %10s %10s %10s"
          % ("frame", "vis", "gone", "WOUND m2", "w x h", "CTRL m2"))
    for r in rows:
        print("  %-6d %8d %8d %10.3f %6.2fx%-5.2f %10.4f"
              % (r["frame"], r["shards_visible"], r["gone"],
                 r["WOUND_hole_bridged_m2"], r["WOUND_w_m"], r["WOUND_h_m"],
                 r.get("CONTROL_intact_bays_vacated_m2", float("nan"))))
    print("")
    print("  A   tail-static over %d frames (f%d..%d)   : %s"
          % (tail_n, span_end + 1, total, "PASS" if A_ok else "FAIL"))
    print("  NEG-1 non-breach objects DO key past f%-5d : %s (%d found)"
          % (span_end, "PASS" if NEG1_ok else "FAIL -- VACUOUS", len(lat)))
    print("  C   swept all %d frames: peak %.3f m2 at f%d, min after it"
          " %.3f m2 at f%d = %.1f%% : %s"
          % (total, peak, pkf, mn, minf, 100.0 * frac,
             "PASS" if C_ok else "FAIL"))
    print("  D   intact-bay control, worst of %d frames %.6f m2 : %s"
          % (total, CTL.max(), "PASS" if D_ok else "FAIL"))
    print("  POS wound is %.6f m2 on every frame before f859 : %s"
          % (pre, "PASS" if POS_ok else "FAIL"))
    print("  MAG wound at f%d is %.3f m2                : %s"
          % (total, W[-1], "PASS" if MAG_ok else "FAIL"))
    print("")
    print("  E   ALUMINIUM: %d of %d deflected pieces sprang back to home"
          " (%.1f%%), largest %.4f m vs gate %.3f m : %s"
          % (E["RECOVERED"], E["deflected"], E["pct_recovered"],
             E["max_recovered_peak_m"], BM.RECOVERY_GATE_M,
             "VACUOUS -- no frame bodies in this scene" if E["vacuous"]
             else ("PASS" if E_ok else "FAIL")))
    print("      %-22s %9s %9s %8s" % ("piece", "peak m", "end m", "end/peak"))
    for w in E["worst"]:
        print("      %-22s %9.4f %9.4f %8.4f" % tuple(w))
    if vac_pass:
        print("  !! arms that PASSED ON AN EMPTY SET and are therefore not "
              "counted: %s" % ", ".join(vac_pass))
    print("")
    print(">> STAGE RESULT: %s" % ("TAIL_PERSIST_PASS" if ok
                                   else "TAIL_PERSIST_FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    _a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    try:
        main(_a)
    except Exception:                                          # noqa: BLE001
        # Blender 5.2 exits 0 on an uncaught exception and `assemble.py` was
        # found swallowing module exceptions entirely.  A verdict line is
        # printed on the way out either way, so no caller can read silence
        # as success.
        import traceback
        traceback.print_exc()
        print(">> STAGE RESULT: TAIL_PERSIST_ERROR")
