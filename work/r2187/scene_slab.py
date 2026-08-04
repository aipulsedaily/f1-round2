"""THE BAY-4 CLAIM, ASKED OF THE SCENE INSTEAD OF THE TABLE.

    blender -b render/film14_breach.blend -P work/r2187/scene_slab.py -- \
        --bays 2,3,4,5,6,7 --out X.json

R2-097 was closed on numbers taken from `sim/out/breach_film.npz`.  That file is
byte-identical between the film13 apply and this one, so re-running `slabcheck`
on it asserts NOTHING about whether THIS apply carried the bake.  What can be
wrong here is the CURVES: the applier decimates to 65.3 % of keys and writes
LINEAR interpolation, and a shard whose keys were written to the wrong object,
in the wrong order, or about the wrong origin leaves the table untouched.

So this reads the f-curves on the objects that will render and reproduces
slabcheck's own measure:

    d3(f) = |P(f) - P(ref)|,  ref = the table's first frame (845), which is home
    the reported number is the MEDIAN of d3 over the bay's shards

---------------------------------------------------------------------------
DO NOT MEASURE THIS THROUGH `matrix_world`.  I did, and it produced a clean,
plausible, WRONG table: bay 4 read 3,933 mm at f866 against the table's 2,288,
and every bay read EXACTLY 0.0 mm at the last frame.

The reference frame is f845, and at f845 every shard is `hide_viewport` — that
is the whole point of the swap, the glass has not broken yet.  **A hidden object
is not evaluated by the depsgraph**, so its `matrix_world` is never flushed and
still holds the pose the .blend was SAVED with, which for an applied breach
scene is the field's resting pose at the table's LAST frame.  `object.location`
reads the f-curve correctly at the same instant; `matrix_world` and
`evaluated_get(depsgraph).matrix_world` both do not.  Measured on
`GS_b04_00000` at f845: location (14.9607, −0.0243, 0.0973),
matrix_world.translation (16.1952, 3.5810, 0.1268) — its f1165 value.
Worst case over the field, `GS_b05_00018`, is **120.7 m** of disagreement.

So home reads as the resting pose, "how far has it travelled" becomes "how far
is it from where it ends", and the last frame reads 0.0 mm from home — a field
that has flown 5 m reported as never having left.  Both of those are numbers a
reader would believe.

The f-curves are read directly instead.  That is legitimate here and the
control below is what makes it legitimate: the BREACH collection is not
parented and not offset (requirement R7), so `location` IS the world position —
and that is asserted, at a frame where the shards are visible and the two
CAN be compared, rather than assumed.
---------------------------------------------------------------------------

Also, on the same curves, the two open items that are properties of this
decimated reconstruction rather than of the raw bake:

    BELOW FLOOR  a body whose lowest mesh vertex ends under z = 0 - 4 mm
    NOT AT REST  a body still moving more than 1 mm between the last two frames
"""
import argparse
import json
import sys

import numpy as np

import bpy


REF = 845
AT = (860, 866, 880, 900, 920)
SINK_M = 0.004


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--bays", default="2,3,4,5,6,7")
    p.add_argument("--last", type=int, default=1165)
    p.add_argument("--visible-frame", type=int, default=900,
                   help="a frame where the shards are shown, for the R7 control")
    return p.parse_args(argv)


def loc_curves(o):
    """The three location f-curves of an object, by array index."""
    ad = o.animation_data
    if ad is None or ad.action is None:
        return None
    out = {}
    for layer in ad.action.layers:
        for strip in layer.strips:
            cb = strip.channelbag(ad.action_slot)
            if cb is None:
                continue
            for fc in cb.fcurves:
                if fc.data_path == "location":
                    out[fc.array_index] = fc
    return out if len(out) == 3 else None


def main():
    a = parse()
    sc = bpy.context.scene
    bays = [int(x) for x in a.bays.split(",")]

    shards, curves = {}, {}
    for o in sc.objects:
        if not o.name.startswith("GS_b"):
            continue
        b = int(o.name[4:6])
        c = loc_curves(o)
        if c is None:
            continue
        shards.setdefault(b, []).append(o)
        curves[o.name] = c
    for b in shards:
        shards[b].sort(key=lambda o: o.name)

    # ---- R7 CONTROL: location IS the world position -------------------------
    # Asked at a frame where the shards are VISIBLE, because at a frame where
    # they are hidden matrix_world is not evaluated and the comparison is
    # vacuous -- which is the trap this whole file is about.
    sc.frame_set(a.visible_frame)
    bpy.context.view_layer.update()
    worst, worst_at = 0.0, None
    n_ctl = 0
    for b in bays:
        for o in shards.get(b, [])[:200]:
            if o.hide_viewport:
                continue
            n_ctl += 1
            c = curves[o.name]
            d = max(abs(c[i].evaluate(a.visible_frame)
                        - o.matrix_world.translation[i]) for i in range(3))
            if d > worst:
                worst, worst_at = d, o.name
    ctl = dict(frame=a.visible_frame, n_compared=n_ctl,
               worst_m=round(worst, 9), worst_at=worst_at,
               passed=bool(n_ctl > 0 and worst < 1e-5))
    if not ctl["passed"]:
        print("REFUSING: at f%d the location curve and matrix_world disagree "
              "by %.6f m (%s) over %d objects -- either the BREACH collection "
              "has acquired a parent or an offset (R7), or nothing was "
              "visible to compare"
              % (a.visible_frame, worst, worst_at, n_ctl))
        print("STAGE RESULT: scene_slab FAIL")
        sys.exit(1)

    # ---- NEGATIVE CONTROL: the trap itself, measured, not asserted ----------
    sc.frame_set(REF)
    bpy.context.view_layer.update()
    trap, trap_at = 0.0, None
    for b in bays:
        for o in shards.get(b, [])[:200]:
            c = curves[o.name]
            d = max(abs(c[i].evaluate(REF) - o.matrix_world.translation[i])
                    for i in range(3))
            if d > trap:
                trap, trap_at = d, o.name
    trap_row = dict(frame=REF, worst_m=round(trap, 4), worst_at=trap_at,
                    hidden_at_ref=bool(shards[bays[0]][0].hide_viewport),
                    note="matrix_world is NOT evaluated for a hidden object; "
                         "this is how big the lie is at the reference frame")

    # ---- the field, off the curves ------------------------------------------
    P = {}
    for f in sorted(set([REF] + list(AT) + [a.last, a.last - 1])):
        P[f] = {b: np.array([[curves[o.name][i].evaluate(f) for i in range(3)]
                             for o in shards.get(b, [])], float)
                for b in bays}

    rad = {b: np.array([min((v.co[2] for v in o.data.vertices), default=0.0)
                        for o in shards.get(b, [])], float) for b in bays}

    out = {"ref_frame": REF,
           "measured_on": "the applied location f-curves, evaluated",
           "R7_control": ctl,
           "hidden_object_matrix_trap": trap_row,
           "bays": {}}
    for b in bays:
        if not len(P[REF][b]):
            continue
        d = {"n": int(len(P[REF][b]))}
        for f in AT:
            d3 = np.linalg.norm(P[f][b] - P[REF][b], axis=1)
            d[str(f)] = dict(net_median_mm=round(float(1000 * np.median(d3)), 1),
                             gone_over_250mm=int((d3 > 0.25).sum()))
        d3l = np.linalg.norm(P[a.last][b] - P[REF][b], axis=1)
        d["last"] = dict(frame=a.last,
                         net_median_mm=round(float(1000 * np.median(d3l)), 1),
                         gone_over_250mm=int((d3l > 0.25).sum()))
        out["bays"][str(b)] = d

    lo, worstz, tot = 0, 0.0, 0
    for b in bays:
        z = P[a.last][b][:, 2] + rad[b]
        lo += int((z < -SINK_M).sum())
        worstz = max(worstz, float(-z.min()))
        tot += len(z)
    out["sink_at_last_key"] = dict(
        below_floor=lo, worst_m=round(worstz, 3), of=tot, tol_m=SINK_M,
        note="GS_* shards only.  verify_breach counts the table's 3,948 "
             "bodies, which include the 152 MUL*/TRN* frame bodies this scene "
             "does not instance, so the two totals are not the same set.")

    mv, mx = 0, 0.0
    for b in bays:
        step = np.linalg.norm(P[a.last][b] - P[a.last - 1][b], axis=1)
        mv += int((step > 0.001).sum())
        mx = max(mx, float(step.max()))
    out["motion_at_last_key"] = dict(over_1mm_per_frame=mv,
                                     worst_m_per_frame=round(mx, 4), of=tot)

    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print("R7 control: %d objects, worst |location - matrix_world| = %.3g m "
          "at f%d  -> PASS" % (ctl["n_compared"], ctl["worst_m"], ctl["frame"]))
    print("the trap at f%d (all shards hidden): worst %.1f m  (%s)"
          % (REF, trap_row["worst_m"], trap_row["worst_at"]))
    for b, d in sorted(out["bays"].items(), key=lambda kv: int(kv[0])):
        print("bay %s  n=%-5d f866 %8.1f mm  f900 %8.1f mm  f%d %8.1f mm"
              % (b, d["n"], d["866"]["net_median_mm"],
                 d["900"]["net_median_mm"], a.last, d["last"]["net_median_mm"]))
    print("SINK %s" % json.dumps(out["sink_at_last_key"]))
    print("MOTION %s" % json.dumps(out["motion_at_last_key"]))
    print("STAGE RESULT: scene_slab written to %s" % a.out)


if __name__ == "__main__":
    main()
