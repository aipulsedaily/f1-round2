"""How far does car geometry actually go BELOW a surface? Depth, not hit count.

The BVH gate reports triangle pairs that intersect, which fires on CONTACT as
well as on penetration — an assembled car's floor and monocoque are bolted
together and touch by design, and a tyre resting on a deck is coplanar with it.
Counting those as defects would condemn a correct car.

The question that matters is DEPTH: how far below the deck's top surface does any
car vertex actually sit? Contact is 0. Anything more is the suspension going
through the floor.

TWO DEFECTS FIXED HERE                                             (R2, 2026-08-02)
-----------------------------------------------------------------------------
1. THE VERDICT WAS NOT WIRED TO THE MEASUREMENT.

   The last line of this file used to be, unconditionally:

       print(">> STAGE RESULT: DEPTH_PROBE_OK")

   On the positive control — `CAR_Wheel` 200.0 mm inside `Turntable_Deck`, the
   exact defect this tool exists to catch — it measured 200.00 mm, wrote 200.00
   mm to the JSON, printed the 200.00 mm line, and then said DEPTH_PROBE_OK.
   Anyone reading the verdict instead of the JSON got the wrong answer every
   time, and the verdict is what a battery log greps for. Eighteenth instrument
   on this project to be the broken thing rather than the work.

   The verdict now derives from the measurement, per surface, per frame.

2. IT WAS BOUNDED ON ONE SIDE ONLY.

   `worst.get(sn, (0, ""))[0]` seeded the running maximum at ZERO, so only
   penetration was ever recorded. A car hovering above the deck produced an
   EMPTY result — and the shipped NEGATIVE control is precisely that: a wheel
   200 mm ABOVE the deck top. Its report is `"frames": {"1": {}}`. The tool
   measured nothing at all and called it a pass.

   That is the same shape as the defect found in `build_architecture` this week:
   it asserts paving is never PROUD of the datum and never that it is not far
   BELOW it, and 100 mm of sunken forecourt went unseen for exactly that reason.
   Both bounds are now measured and both are enforced: `worst_signed` is the
   most-positive `surface_top - z` over every car vertex in plan, so

       > max_depth_mm      PENETRATION -- the car is THROUGH that surface
       within tolerance    CONTACT     -- it is resting on it
       < -max_float_mm     ABOVE       -- it is clear of that surface

   and the frame is FLOATING when it is ABOVE every surface it overlaps, i.e.
   nothing is holding it up. Levitation has to be judged per FRAME rather than
   per surface because the surfaces are stacked: `Turntable_Deck`'s top is at
   0.340 and it stands inside `Floor`'s plan extent at 0.000, so a car correctly
   parked on the dais is 340 mm above the floor and a per-surface rule would
   condemn it.

   A frame where the car is legitimately airborne has to be NAMED
   (`--airborne-frames`), because a skip that appears on the command line is one
   a reader can see, and a skip the tool decides for itself is one nobody can.

`--selftest` builds both failure modes and the pass case from scratch and exits
non-zero unless each behaves. It needs no world file and no control .blend, so
the controls cannot be lost, skipped, or left behind by a rename.
"""
import argparse, json, os, sys
import bpy
from mathutils import Vector

# Imported by path, not by package: this runs inside Blender's interpreter with
# whatever cwd the caller happened to have.
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402

SURFACE_NAMES = ("Turntable_Deck", "Platform_Dais", "Floor")


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", default="1,792")
    ap.add_argument("--out", required=False)
    ap.add_argument("--selftest", action="store_true")
    # 1 mm. Contact is 0 by definition; the tolerance covers float rounding on a
    # matrix multiply, not a gap anybody could see. Stated as a number so it can
    # be argued with, rather than living inside an `if`.
    ap.add_argument("--max-depth-mm", type=float, default=1.0,
                    help="deeper than this below a reference surface is a FAIL")
    ap.add_argument("--max-float-mm", type=float, default=1.0,
                    help="the car's lowest point over a reference surface may "
                         "not sit higher than this above it")
    ap.add_argument("--airborne-frames", default="",
                    help="frames where the car is MEANT to be off the ground. "
                         "Exempt from the float bound only — penetration is "
                         "still a failure — and listed in the report.")
    return ap.parse_args(argv)


def reference_surfaces():
    """Top plane and plan extent of each reference surface present."""
    out = {}
    deps = bpy.context.evaluated_depsgraph_get()
    for n in SURFACE_NAMES:
        ob = bpy.data.objects.get(n)
        if not ob or ob.type != "MESH":
            continue
        oe = ob.evaluated_get(deps)
        me = oe.to_mesh()
        mw = ob.matrix_world
        pts = [mw @ v.co for v in me.vertices]
        if pts:
            out[n] = {"top": max(p.z for p in pts),
                      "xr": (min(p.x for p in pts), max(p.x for p in pts)),
                      "yr": (min(p.y for p in pts), max(p.y for p in pts))}
        oe.to_mesh_clear()
    return out


def car_objects(scene):
    return [o for o in scene.objects
            if o.type == "MESH" and "CAR" in {c.name for c in o.users_collection}]


def measure_frame(scene, surfaces):
    """Worst SIGNED offset of any car vertex relative to each surface top.

    Positive = below the top (penetration). Negative = above it (a gap).
    Seeded at -inf, not at 0 — seeding at 0 is what made levitation invisible.
    """
    deps = bpy.context.evaluated_depsgraph_get()
    worst = {}
    counts = {k: 0 for k in surfaces}
    for ob in car_objects(scene):
        oe = ob.evaluated_get(deps)
        try:
            me = oe.to_mesh()
        except Exception:
            continue
        if me is None:
            continue
        mw = ob.matrix_world
        for v in me.vertices:
            p = mw @ v.co
            for sn, s in surfaces.items():
                if s["xr"][0] <= p.x <= s["xr"][1] and s["yr"][0] <= p.y <= s["yr"][1]:
                    counts[sn] += 1
                    d = s["top"] - p.z
                    if d > worst.get(sn, (-1e30, ""))[0]:
                        worst[sn] = (d, ob.name)
        oe.to_mesh_clear()
    return worst, counts


def judge(worst, counts, max_depth_mm, max_float_mm, airborne):
    """Verdicts, derived from the numbers. Nothing else decides.

    PENETRATION is PER SURFACE — going through any of them is wrong on its own.

    FLOATING is PER FRAME, and it has to be: the reference surfaces are STACKED.
    `Turntable_Deck`'s top is at z = 0.340 and it stands inside `Floor`'s plan
    extent at z = 0.000, so a car correctly parked on the dais is 340 mm above
    the floor. Judging levitation per surface would call that a defect. The
    physical claim is "nothing is holding the car up", which is only true when
    the car is clear of EVERY surface beneath it.
    """
    rows = {}
    for sn, n in counts.items():
        if n == 0 or sn not in worst:
            rows[sn] = {"verdict": "NO_OVERLAP", "vertices_in_plan": 0,
                        "depth_mm": None, "object": None}
            continue
        d, who = worst[sn]
        mm = d * 1000.0
        if mm > max_depth_mm:
            verdict = "PENETRATION"
        elif mm < -max_float_mm:
            verdict = "ABOVE"
        else:
            verdict = "CONTACT"
        rows[sn] = {"verdict": verdict, "vertices_in_plan": n,
                    "depth_mm": round(mm, 2), "object": who}

    seen = [r for r in rows.values() if r["verdict"] != "NO_OVERLAP"]
    supported = any(r["verdict"] in ("CONTACT", "PENETRATION") for r in seen)
    if seen and not supported:
        # Clear of every surface it overlaps. Attribute it to the nearest one.
        nearest = max(seen, key=lambda r: r["depth_mm"])
        nearest["verdict"] = "AIRBORNE_OK" if airborne else "FLOATING"
    return rows


def report(out_path, out, frame_rows, thresholds):
    bad = [(fr, sn, r) for fr, rows in frame_rows.items() for sn, r in rows.items()
           if r["verdict"] in ("PENETRATION", "FLOATING")]
    measured = [(fr, sn, r) for fr, rows in frame_rows.items()
                for sn, r in rows.items() if r["verdict"] != "NO_OVERLAP"]
    out["thresholds_mm"] = thresholds
    out["failures"] = [{"frame": fr, "surface": sn, **r} for fr, sn, r in bad]
    if not measured:
        # A probe that overlapped nothing measured nothing. Emitting a pass on
        # an empty set is worse than erroring: the reader banks it as evidence.
        out["vacuous"] = True
        out["reason"] = ["no car vertex lies over any reference surface in any "
                         "frame — nothing was measured"]
        if out_path:
            json.dump(out, open(out_path, "w"), indent=1)
        print(">> REFUSING TO REPORT: no car vertex over any reference surface")
        # `return 0` used to make this refusal indistinguishable from a pass to
        # every caller that branched on $?. VACUOUS is code 3.
        return gate_exit.verdict("DEPTH_PROBE_VACUOUS")
    if out_path:
        json.dump(out, open(out_path, "w"), indent=1)
    if bad:
        print(f">> {len(bad)} DEPTH FAILURE(S)")
        for fr, sn, r in bad:
            print(f"     frame {fr}  {sn:<18} {r['verdict']:<12} "
                  f"{r['depth_mm']:>9.2f} mm   {r['object']}")
        return gate_exit.verdict("DEPTH_PROBE_FAIL")
    n_contact = sum(1 for _f, _s, r in measured if r["verdict"] == "CONTACT")
    n_above = sum(1 for _f, _s, r in measured if r["verdict"] == "ABOVE")
    n_air = sum(1 for _f, _s, r in measured if r["verdict"] == "AIRBORNE_OK")
    print(f">> {len(measured)} surface-frame(s) measured: {n_contact} in contact "
          f"within +{thresholds['max_depth_mm']} / -{thresholds['max_float_mm']} mm, "
          f"{n_above} clear above a lower surface, {n_air} waived as airborne")
    return gate_exit.verdict("DEPTH_PROBE_OK")


def run(a, scene):
    surfaces = reference_surfaces()
    cars = car_objects(scene)

    # A GATE THAT CANNOT FIND ITS SUBJECT MUST NOT REPORT OK.
    #
    # On the world-only assembly this found no surfaces (Turntable_Deck /
    # Platform_Dais / Floor are showroom objects) and no CAR collection, measured
    # exactly nothing, and printed DEPTH_PROBE_OK. Fifth repeat of the same
    # failure -- see the note in collision_gate.py and R2-017.
    if not surfaces or not cars:
        missing = []
        if not surfaces:
            missing.append("none of %s is in this scene" % " / ".join(SURFACE_NAMES))
        if not cars:
            missing.append("no objects in a CAR collection")
        print(">> REFUSING TO REPORT: " + "; ".join(missing))
        print(">> Nothing here for this probe to measure. That is NOT a pass.")
        if a.out:
            json.dump({"surfaces": surfaces, "frames": {}, "vacuous": True,
                       "reason": missing}, open(a.out, "w"), indent=1)
        # `return 0` used to make this refusal read as a pass. VACUOUS is 3.
        return gate_exit.verdict("DEPTH_PROBE_VACUOUS")

    airborne = {int(f) for f in a.airborne_frames.split(",") if f.strip()}
    if airborne:
        print(f">> float bound WAIVED on frames {sorted(airborne)} "
              f"(named on the command line); penetration still enforced")
    print(f">> {len(surfaces)} reference surfaces, {len(cars)} car objects")

    out = {"surfaces": surfaces, "frames": {},
           "airborne_frames": sorted(airborne)}
    frame_rows = {}
    for fr in [int(f) for f in a.frames.split(",")]:
        scene.frame_set(fr)
        bpy.context.view_layer.update()
        worst, counts = measure_frame(scene, surfaces)
        rows = judge(worst, counts, a.max_depth_mm, a.max_float_mm,
                     fr in airborne)
        frame_rows[fr] = rows
        out["frames"][str(fr)] = rows
        print(f">> frame {fr}:")
        for k, r in sorted(rows.items(),
                           key=lambda x: -(x[1]["depth_mm"] or -1e30)):
            if r["verdict"] == "NO_OVERLAP":
                print(f"     below {k:<18} NO_OVERLAP  (no car vertex in plan)")
            else:
                print(f"     below {k:<18} {r['depth_mm']:>9.2f} mm  "
                      f"{r['verdict']:<12} worst: {r['object']}")
    return report(a.out, out, frame_rows,
                  {"max_depth_mm": a.max_depth_mm,
                   "max_float_mm": a.max_float_mm})


# ===========================================================================
#  SELFTEST
# ===========================================================================
#
# Three cases, built here so they cannot be lost:
#
#   POSITIVE (penetration) a wheel 200 mm INSIDE the deck. This is the defect
#                          the tool was written for, and the case on which the
#                          shipped tool printed DEPTH_PROBE_OK.
#   POSITIVE (levitation)  a wheel 200 mm ABOVE the deck. This is the shipped
#                          "negative" control -- which measured nothing and was
#                          also called OK. Both sides, both must fail.
#   NEGATIVE               a wheel resting ON the deck. Must pass, or the tool
#                          has been made to fail everything, which is no better.
#
# Neither positive control depends on any other module staying broken: each
# builds its own geometry and asserts on this file's own verdict.

def _build(dz, with_floor=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    deck = bpy.context.object
    deck.name = "Turntable_Deck"
    deck.scale = (6.9, 6.9, 0.340)
    deck.location = (0.0, 0.0, 0.340 - 0.170)      # top at z = 0.340
    if with_floor:
        # The stacked case: a wide Floor at z = 0 UNDER the dais, exactly as the
        # showroom has it. A car resting on the deck is 340 mm above this.
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, -0.05))
        flo = bpy.context.object
        flo.name = "Floor"
        flo.scale = (30.0, 22.0, 0.10)
    bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 0.340 + dz + 0.25))
    part = bpy.context.object
    part.name = "CAR_Wheel"
    c = bpy.data.collections.new("CAR")
    sc.collection.children.link(c)
    for oc in list(part.users_collection):
        oc.objects.unlink(part)
    c.objects.link(part)
    bpy.context.view_layer.update()
    return sc


def selftest(a):
    cases = [("POSITIVE penetration: CAR_Wheel 200 mm inside the deck",
              -0.200, False, "PENETRATION"),
             ("POSITIVE levitation:  CAR_Wheel 200 mm above the deck",
              +0.200, False, "FLOATING"),
             ("NEGATIVE contact:     CAR_Wheel resting on the deck",
              0.0, False, "CONTACT"),
             # STACKED SURFACES. A car correctly parked on the dais is 340 mm
             # above the showroom Floor. Judging levitation per surface would
             # call that a defect; it is not one, and this control says so.
             ("NEGATIVE stacked:     on the deck, 340 mm above the Floor",
              0.0, True, "CONTACT")]
    rows, fails = [], []
    for label, dz, floor, want in cases:
        sc = _build(dz, with_floor=floor)
        surfaces = reference_surfaces()
        worst, counts = measure_frame(sc, surfaces)
        got = judge(worst, counts, a.max_depth_mm, a.max_float_mm, False)
        v = got.get("Turntable_Deck", {"verdict": "NO_OVERLAP", "depth_mm": None})
        ok = (v["verdict"] == want)
        rows.append({"case": label, "expected": want, "got": v["verdict"],
                     "depth_mm": v["depth_mm"], "ok": ok})
        print(f"   {'PASS' if ok else 'FAIL'}  {label:<58} "
              f"got {v['verdict']:<12} ({v['depth_mm']} mm), expected {want}")
        if not ok:
            fails.append(label)

    # And the verdict LINE, not just the row: the defect was the print, so the
    # control has to exercise the print.
    sc = _build(-0.200)
    surfaces = reference_surfaces()
    worst, counts = measure_frame(sc, surfaces)
    rows_pen = judge(worst, counts, a.max_depth_mm, a.max_float_mm, False)
    rc = report(None, {"surfaces": surfaces, "frames": {}},
                {1: rows_pen}, {"max_depth_mm": a.max_depth_mm,
                                "max_float_mm": a.max_float_mm})
    ok = (rc == 1)
    rows.append({"case": "the STAGE RESULT line fails on the 200 mm penetration",
                 "expected": "DEPTH_PROBE_FAIL / rc=1", "got": f"rc={rc}",
                 "ok": ok})
    print(f"   {'PASS' if ok else 'FAIL'}  "
          f"{'verdict line fails on the 200 mm penetration':<58} rc={rc}")
    if not ok:
        fails.append("verdict line did not fail on the positive control")

    if a.out:
        json.dump({"controls": rows, "failures": fails}, open(a.out, "w"), indent=1)
    if fails:
        print(f">> {len(fails)} CONTROL(S) MISBEHAVED: {fails}")
        return gate_exit.verdict("DEPTH_PROBE_SELFTEST_FAIL")
    print(f">> all {len(rows)} controls behaved")
    return gate_exit.verdict("DEPTH_PROBE_SELFTEST_OK")


def main():
    _a = parse_args()
    return selftest(_a) if _a.selftest else run(_a, bpy.context.scene)


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised; guard() makes an
    # exception a status 2 instead of a silent pass.
    gate_exit.guard(main, tool="depth_probe")
