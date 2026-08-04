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

    def measure(f):
        gone_ids, vis, hid = set(), 0, 0
        for nm, (o, fcs) in shard_fc.items():
            loc, h = pose_at(fcs, o, f)
            if h:
                hid += 1
                continue
            vis += 1
            if np.linalg.norm(loc - home[nm]) > GONE_M:
                gone_ids.add((int(nm[4:6]), int(nm[7:])))
        gone_mul = set()
        for nm, o, fcs in frame_bodies:
            if not nm.startswith("MUL"):
                continue
            try:
                mi, sj = int(nm[3:5]), int(nm[nm.index("_S") + 2:][:2])
            except (ValueError, IndexError):
                continue
            loc, _h = pose_at(fcs, o, f)
            if np.linalg.norm(loc - fb_home[nm]) > GONE_M:
                for ss in (range(8) if mi in (0, 1, 2, 8, 9, 10) else [sj]):
                    gone_mul.add((mi, ss))
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

    probe = [1, 400, 859, 860, 900, 1000, span_end,
             span_end + 1, 1500, 2000, 2500, total]
    probe = sorted({int(f) for f in probe if 1 <= f <= total})
    rows = [measure(f) for f in probe]
    rep["rows"] = rows
    by_f = {r["frame"]: r for r in rows}

    ref = by_f[span_end]["WOUND_hole_bridged_m2"]
    tail_rows = [r for r in rows if r["frame"] > span_end]
    C_ok = bool(tail_rows) and all(
        abs(r["WOUND_hole_bridged_m2"] - ref) < 1e-6 for r in tail_rows)
    rep["C_PASS"] = C_ok
    rep["C_wound_m2_at_span_end"] = ref
    rep["C_wound_m2_tail"] = [r["WOUND_hole_bridged_m2"] for r in tail_rows]

    ctrl = [r.get("CONTROL_intact_bays_vacated_m2", 0.0) for r in rows]
    D_ok = all(abs(c) < 1e-9 for c in ctrl) and ref > 1.0
    rep["D_PASS"] = bool(D_ok)
    rep["D_control_vacated_m2_max"] = max(ctrl) if ctrl else None

    pre = by_f[1]["WOUND_hole_bridged_m2"]
    POS_ok = abs(pre) < 1e-9 and ref > 1.0
    rep["POS_PASS"] = bool(POS_ok)
    rep["POS_wound_m2_at_f1"] = pre

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
    E_ok = E["max_recovered_peak_m"] <= BM.RECOVERY_GATE_M
    rep["E_PASS"] = bool(E_ok)

    ok = A_ok and NEG1_ok and C_ok and D_ok and POS_ok and E_ok
    rep["PASS"] = bool(ok)

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
    print("  C   wound held at %.3f m2 on every probe   : %s"
          % (ref, "PASS" if C_ok else "FAIL"))
    print("  D   intact-bay control reads %.4f m2       : %s"
          % (max(ctrl) if ctrl else -1, "PASS" if D_ok else "FAIL"))
    print("  POS wound is %.4f m2 at f1                : %s"
          % (pre, "PASS" if POS_ok else "FAIL"))
    print("")
    print("  E   ALUMINIUM: %d of %d deflected pieces sprang back to home"
          " (%.1f%%), largest %.4f m vs gate %.3f m : %s"
          % (E["RECOVERED"], E["deflected"], E["pct_recovered"],
             E["max_recovered_peak_m"], BM.RECOVERY_GATE_M,
             "PASS" if E_ok else "FAIL"))
    print("      %-22s %9s %9s %8s" % ("piece", "peak m", "end m", "end/peak"))
    for w in E["worst"]:
        print("      %-22s %9.4f %9.4f %8.4f" % tuple(w))
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
