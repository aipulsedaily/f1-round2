"""PUT THE DELIVERY RAMP INTO A FILM SCENE, AND PROVE IT LANDED.

    /opt/blender-5.2.0-linux-x64/blender -b render/film8.blend --factory-startup \
        -P tools/add_dais_ramp.py -- --out render/film9.blend

WHY THIS IS ITS OWN TOOL AND NOT A LINE IN `build_film_scene.py`
================================================================
The showroom reaches the film scene as an APPEND of `world/car_anim.blend`'s
SHOWROOM / PROPS / LIGHTS collections — the post-unparent artefact — and
`build_film_scene.py` is owned by another agent this session. Rebuilding a
4.5 GB film blend to add one 4.25 M-triangle object would also mean re-appending
616 car meshes and re-keying the camera rig, which is 30 minutes of risk for a
change that is additive by construction.

So this opens the film blend that already exists, builds
`world/items/dais_delivery_ramp.py` into it, ASSERTS the set it is landing
against, and saves. `world/items/dais_delivery_ramp.py` remains the one
definition of the geometry; nothing about the ramp is described twice.

WHAT IT REFUSES TO DO
---------------------
* Build into a scene with no showroom. The ramp is scribed to `Turntable_Deck`'s
  measured rim and bears on `Platform_Dais`'s measured ring; dropping it into a
  world-only assembly would put it 3.7 m from a dais that is not there.
* Build into a scene whose dais is not where it was measured. The scribe radius,
  the 12.5 mm running clearance and the 0.300 m bearing are all derived from
  `work/ramp/dais_probe.json`. If the set moves, this stops.
* Report success on an exception. `gate_exit.guard` — Blender 5.2 exits 0 on an
  uncaught script error, which is how a crash after a save once read as a pass.

VERIFY, do not trust: `--verify` re-measures the saved file by raycasting
straight down under every keyed contact patch over the launch, with the car
excluded from the view layer so the ray cannot stop on the inside of a tyre.
That is `work/film6/contact_mesh.py`'s method, which is the method that found
the defect.
"""

import argparse
import json
import math
import os
import sys
import time

import bpy

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "tools"), os.path.join(R2, "world"),
           os.path.join(R2, "world/items"), os.path.join(R2, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_exit                                             # noqa: E402

TOL = 1e-3


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=None)
    p.add_argument("--report", default=None)
    p.add_argument("--frames", default="836-858")
    p.add_argument("--no-verify", action="store_true")
    p.add_argument("--no-build", action="store_true",
                   help="measure ONLY. The BEFORE reading, taken with this same "
                        "instrument on this same file lineage, so the before and "
                        "after numbers cannot differ because the ruler changed.")
    return p.parse_args(argv)


def assert_set(D):
    """The dais this ramp was scribed to must be the dais in this file."""
    import numpy as np
    got = {}
    for name, want_top, want_r in (
            ("Turntable_Deck", D.DECK_TOP_Z, D.DECK_RIM_R),
            ("Platform_Dais", D.PLATFORM_TOP_Z, D.PLATFORM_R),
            ("Floor", 0.0, None)):
        ob = bpy.data.objects.get(name)
        if ob is None or ob.type != "MESH":
            return None, ("REFUSING: no %s mesh in this scene. The ramp is "
                          "scribed to the built dais, not to the spec's prose; "
                          "run this on a blend that carries the SHOWROOM "
                          "collection." % name)
        M = ob.matrix_world
        V = np.array([tuple(M @ v.co) for v in ob.data.vertices])
        top = float(V[:, 2].max())
        r = float(np.hypot(V[:, 0], V[:, 1]).max())
        got[name] = {"top_z": top, "r_max": r}
        if abs(top - want_top) > TOL:
            return None, ("REFUSING: %s top is z = %.5f, not the %.3f this ramp "
                          "was measured against." % (name, top, want_top))
        if want_r is not None and abs(r - want_r) > TOL:
            return None, ("REFUSING: %s outermost radius is %.5f, not the %.5f "
                          "this ramp's scribe arc was cut to. Re-measure with "
                          "work/ramp/probe_dais.py and rebuild."
                          % (name, r, want_r))
    return got, None


def verify(D, frames):
    """Raycast the BUILT MESH under every keyed contact patch. The instrument
    that found the defect, pointed at the repair."""
    import numpy as np
    from mathutils import Vector

    scene = bpy.context.scene
    vl = bpy.context.view_layer
    excluded = []

    # KEEP ONLY THE SURFACES THAT CAN BE UNDER A WHEEL ON THE LAUNCH, and say
    # why. `scene.ray_cast` needs a BVH over the whole view layer, and this
    # world is 13.9 G instanced triangles: on this box that never finishes.
    # Excluding everything but the showroom set and the ramp takes it to a few
    # million and costs nothing, because the launch runs from x = 0 to x = 15
    # INSIDE the showroom -- the only meshes that can be beneath a contact patch
    # are Floor, Turntable_Deck, Platform_Dais, the props on the showroom floor
    # and the ramp itself. That is not an assumption: `surfaces_hit` below names
    # every object the rays actually landed on, so if something outside this set
    # were the ground the report would come back with nothing under the wheels
    # rather than with a quietly wrong number.
    KEEP = {"SHOWROOM", "PROPS", "LIGHTS", "W_Item_DaisDeliveryRamp",
            "W_Item_DaisDeliveryRamp/Cameras", "W_Item_DaisDeliveryRamp/Standins"}

    def prune(lc):
        for c in list(lc.children):
            if c.collection.name in KEEP:
                continue
            c.exclude = True
            excluded.append(c.collection.name)

    CORN = ("FL", "FR", "RL", "RR")
    hubs = {c: bpy.data.objects.get("CARRIG_SPIN_%s" % c) for c in CORN}
    if any(v is None for v in hubs.values()):
        return {"verdict": "VACUOUS", "why": "no CARRIG_SPIN_* hubs: no car"}

    # PASS 1 — where the wheels are, with the car still in the scene
    poses = []
    for f in frames:
        scene.frame_set(f)
        vl.update()
        poses.append({"frame": f,
                      **{c: [float(x) for x in hubs[c].matrix_world.translation]
                         for c in CORN}})

    prune(vl.layer_collection)
    if "CAR" not in excluded:
        return {"verdict": "VACUOUS",
                "why": "the CAR collection was not excluded, so a ray fired "
                       "from a wheel centre would stop on the inside of that "
                       "same tyre and report a 0.000 m gap for a car in orbit"}
    print(">> raycast view layer: kept %s, excluded %d collection(s) %s"
          % (sorted(KEEP & set(c.name for c in bpy.data.collections)),
             len(excluded), excluded[:8]))
    vl.update()
    dg = bpy.context.evaluated_depsgraph_get()

    # THE TYRE RIDES THE LANDS, NOT THE GROOVE FLOOR. A single ray dropped from
    # the wheel centre can land inside a 1.6 mm milled groove and report the
    # ramp as 1.6 mm lower than anything the tyre can touch. So each contact
    # patch is sampled over its own FOOTPRINT and the HIGHEST hit is taken:
    # that is the surface the rubber is actually carried on. The front contact
    # patch is ~0.30 m wide, the rear ~0.40 m; +-0.09 m along x is the patch
    # length at this load. Measured on the same file, this alone moves the worst
    # reading 10.59 -> the land height, and the difference is exactly one groove
    # depth.
    PATCH = [(dx, dy) for dx in (-0.09, -0.045, 0.0, 0.045, 0.09)
             for dy in (-0.12, -0.06, 0.0, 0.06, 0.12)]

    out, hit_objs = [], {}
    for rec in poses:
        row = {"frame": rec["frame"]}
        for c in CORN:
            hx, hy, hz = rec[c]
            # ...AND "HIGHEST" MEANS HIGHEST *GROUND*, NOT HIGHEST THING. The
            # first patch-max run reported a -0.785 m gap at frame 854 because
            # `Barrier_Rail_0` passes 0.785 m ABOVE the floor within 120 mm of
            # the rear wheel and is the highest hit in the footprint. A rail
            # over your head is not what you are standing on. Only hits at or
            # below the tyre's own bottom (+10 mm, so a tyre bedded into a
            # surface still counts) can be ground. Reported separately, because
            # a rail that close to the car is worth someone knowing about.
            ceiling = hz - D.WHEEL_R + 0.010
            best_z, best_ob, over = None, None, {}
            for dx, dy in PATCH:
                o = Vector((hx + dx, hy + dy, hz + 0.55))
                hit, loc, _n, _i, ob_, _m = scene.ray_cast(
                    dg, o, Vector((0, 0, -1)), distance=5.0)
                if not hit:
                    continue
                if loc.z > ceiling:
                    over[ob_.name] = round(float(loc.z), 4)
                    continue
                if best_z is None or loc.z > best_z:
                    best_z, best_ob = float(loc.z), ob_
            ok = best_z is not None

            class _L:                       # keep the shape of the old record
                pass
            loc = _L()
            loc.z = best_z if ok else 0.0
            ob = best_ob
            wb = hz - D.WHEEL_R
            row[c] = {"x": round(hx, 5), "wheel_bottom_z": round(wb, 6),
                      "mesh_z": (round(float(loc.z), 6) if ok else None),
                      "obj": (ob.name if ok else None),
                      "gap_m": (round(wb - float(loc.z), 6) if ok else None),
                      "above_the_tyre": over or None}
            if ok:
                hit_objs[ob.name] = hit_objs.get(ob.name, 0) + 1
        out.append(row)

    real = [row[c]["gap_m"] for row in out for c in CORN
            if row[c]["gap_m"] is not None]
    misses = [(row["frame"], c) for row in out for c in CORN
              if row[c]["gap_m"] is None]
    overhead = {}
    for row in out:
        for c in CORN:
            for k, v in (row[c].get("above_the_tyre") or {}).items():
                overhead.setdefault(k, []).append([row["frame"], c, v])
    if overhead:
        print(">> OVERHEAD, NOT GROUND: %d object(s) sit ABOVE a contact patch "
              "within its own footprint -- reported, not counted as ground:"
              % len(overhead))
        for k, v in overhead.items():
            print("     %-22s %d probe(s), first %s, z up to %.4f"
                  % (k, len(v), v[0][:2], max(r[2] for r in v)))
    return {"verdict": "MEASURED", "frames": [f for f in frames],
            "overhead_not_ground": overhead,
            "n_probes": len(real) + len(misses),
            "no_surface": misses,
            "gap_max_m": max(real) if real else None,
            "gap_min_m": min(real) if real else None,
            "gap_rms_m": (sum(g * g for g in real) / len(real)) ** 0.5 if real else None,
            "surfaces_hit": hit_objs,
            "samples": out}


def main():
    a = parse_args()
    t0 = time.time()
    src = bpy.data.filepath
    print(">> source %s (%.2f GB)" % (src, os.path.getsize(src) / 2 ** 30))

    import dais_delivery_ramp as D
    import carrig as CR
    D.WHEEL_R = CR.WHEEL_RADIUS_M           # 0.360, read not retyped

    got, why = assert_set(D)
    if why:
        print(why)
        return gate_exit.verdict("RAMP_NO_SET_REFUSED", why)
    print(">> SET DATUMS OK: %s" % json.dumps(got))

    stats = {"objects": 0, "tris": 0}
    if a.no_build:
        print(">> --no-build: MEASURING ONLY. This is the BEFORE reading.")
    else:
        D.build(scene=bpy.context.scene, test_scene=False, stats=stats)
        print(">> built %s: %d objects, %.3f M triangles"
              % (D.ITEM, stats["objects"], stats["tris"] / 1e6))

    # The ramp must not have landed inside the dais it is scribed to.
    import numpy as np
    # UPDATE THE VIEW LAYER FIRST. A freshly created object's `matrix_world` is
    # still identity until the depsgraph runs, and `new_mesh(recentre=True)`
    # puts the whole ramp 4.7 m from its own origin -- so reading it early said
    # the deck reached r = 0.00239 and this check REFUSED a correct build. It
    # was right to refuse: an unevaluated matrix is not a position.
    bpy.context.view_layer.update()
    deck = bpy.data.objects.get(D.PFX + "Deck")
    if deck is None and a.no_build:
        rmin = None
    else:
        M = deck.matrix_world
        V = np.array([tuple(M @ v.co) for v in deck.data.vertices])
        r = np.hypot(V[:, 0], V[:, 1])
        rmin = float(r.min())
    if rmin is not None and rmin < D.DECK_RIM_R:
        why = ("REFUSING: the ramp deck reaches r = %.5f, INSIDE the rotating "
               "Turntable_Deck's outermost vertex at %.5f. A turntable that "
               "fouls its ramp is worse than a missing ramp."
               % (rmin, D.DECK_RIM_R))
        print(why)
        return gate_exit.verdict("RAMP_FOULS_TURNTABLE_VIOLATION", why)
    if rmin is not None:
        print(">> ramp deck inner radius %.5f m, clearance to the rotating deck "
              "%.1f mm; plan extent x %.4f..%.4f  y %.4f..%.4f  z %.5f..%.5f"
              % (rmin, 1000 * (rmin - D.DECK_RIM_R), V[:, 0].min(), V[:, 0].max(),
                 V[:, 1].min(), V[:, 1].max(), V[:, 2].min(), V[:, 2].max()))

    ext = [i.filepath for i in bpy.data.images if i.source == "FILE"]
    if ext:
        why = "REFUSING TO SAVE: external images %s (Law 1)" % ext
        print(why)
        return gate_exit.verdict("RAMP_EXTERNAL_ASSETS_REJECT", why)

    out = os.path.abspath(a.out) if a.out else None
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
        print(">> saved %s (%.2f GB) in %.0f s"
              % (out, os.path.getsize(out) / 2 ** 30, time.time() - t0))

    rep = {"source": src, "out": out, "set": got, "build": stats,
           "deck_inner_r": rmin}
    if not a.no_verify:
        lo, hi = (int(x) for x in a.frames.split("-"))
        rep["verify"] = verify(D, list(range(lo, hi + 1)))
        v = rep["verify"]
        print(">> VERIFY %s: %d probes, %d with no surface under them"
              % (v["verdict"], v["n_probes"], len(v.get("no_surface", []))))
        if v["verdict"] == "MEASURED":
            print(">>   gap  min %+.5f  max %+.5f  rms %.5f m"
                  % (v["gap_min_m"], v["gap_max_m"], v["gap_rms_m"]))
            print(">>   surfaces hit: %s" % v["surfaces_hit"])
            for row in v["samples"]:
                print("     f%-5d " % row["frame"] + "  ".join(
                    "%s x%7.3f gap %+8.4f m %-22s" %
                    (c, row[c]["x"], row[c]["gap_m"] if row[c]["gap_m"] is not None
                     else float("nan"), str(row[c]["obj"])[:22])
                    for c in ("FL", "RL")))

    if a.report:
        p = os.path.abspath(a.report)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(rep, open(p, "w"), indent=1)
        print(">> report -> %s" % p)

    v = rep.get("verify")
    if v and v["verdict"] == "MEASURED":
        if v["no_surface"]:
            return gate_exit.verdict(
                "RAMP_STILL_UNSUPPORTED_FAIL",
                "%d probes still find no surface: %s"
                % (len(v["no_surface"]), v["no_surface"][:8]))
        # 15 mm, and here is the whole of it. `world/items/dais_delivery_ramp`
        # selftest [4] decomposes the residual on the worst frame: 3.06 mm is a
        # rigid wheel's lowest point sitting above the 13.1 % plane it is
        # TANGENT to (not a gap at all -- it touches 46.7 mm behind), and up to
        # 4.74 mm is `anim/carrig`'s suspension compliance, added on top of the
        # contact solve and owned by the animation. Neither is the ramp's, and
        # neither can be removed from this file. The bar is set above their sum
        # with room for the plate's own 2.0 mm waviness, and the BEFORE reading
        # on the same instrument is 336 mm, so it is nowhere near a bar that
        # forgives the defect.
        if v["gap_max_m"] > 0.015:
            return gate_exit.verdict(
                "RAMP_STILL_FLOATING_FAIL",
                "worst gap %.4f m exceeds 15 mm; the envelope + compliance "
                "residue alone is 7.8 mm" % v["gap_max_m"])
    return gate_exit.verdict("RAMP_IN_FILM_SCENE_OK",
                             "%.3f M triangles added" % (stats["tris"] / 1e6))


if __name__ == "__main__":
    gate_exit.guard(main, tool="add_dais_ramp")
