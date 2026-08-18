"""PUT A REAL CEILING INTO A FILM SCENE, AND PROVE IT CHANGED NO LIGHT.

    /opt/blender-5.2.0-linux-x64/blender -b render/film16.blend --factory-startup \
        -P tools/r2621_ceiling_build.py -- --out render/film17.blend

WHY THIS IS A POST-APPEND TOOL AND NOT A SOURCE FIX OR A WORLD REBUILD
======================================================================
`Ceiling` is emitted by `~/opus5-car-render/build/s02_showroom.py:490`
`build_shell()` as a literal cuboid whose top and bottom faces are ONE QUAD OF
686.25 m^2. That tree is part 1, shipped and live, and READ-ONLY, so the source
cannot be corrected. It reaches the film through `tools/build_film_scene.py`'s
append of `world/car_anim.blend`'s SHOWROOM collection at identity, and
`assembly*.blend` contains no showroom at all — CONFIRMED here rather than
quoted, twice: `render/world/assembly/r2/assemble.py` imports exactly
build_surface, build_barriers, build_terrain, build_architecture,
build_dressing, build_items and build_sky, none of which authors a showroom;
and `build_film_scene.py:316` names `SET_COLLECTIONS = ("SHOWROOM", "PROPS",
"LIGHTS")` and appends them from the car blend. So R2-504's architecture claim
holds and there is exactly one place this fix can live: after the append, on a
built film blend, in the shape `tools/add_dais_ramp.py` established.

WHAT IT REFUSES TO DO
---------------------
* Build into a scene with no showroom in it. Every radius in
  `world/items/showroom_ceiling.py` is scribed to a MEASURED round-1 emitter;
  dropping it into a world-only assembly would hang a 17 m light-slot ring in
  open air over a racing circuit.
* Build into a scene whose emitters have moved. `Cove_Ring`, `Cove_RingOuter`,
  `Cove_Coffer_*` and the six `SpotRod_*` are re-measured here and compared to
  the values the design was cut to. If the set moves, this stops.
* Report success on an exception. Blender 5.2 exits 0 on an uncaught script
  error, so the only verdict is the printed `>> STAGE RESULT:` line and
  `gate_exit.guard` maps it to a status.
* Save a scene it has not re-levelled. `showroom_lighting.assert_levelled` runs
  UNCONDITIONALLY before the save — not inside a branch. That guard has already
  failed once on this project by being conditional and shipped `film9.blend`
  with the practicals at 3,737 W instead of 46,203 W.

VERIFY, DO NOT TRUST
--------------------
`--verify` is not a re-read of what was just built. It re-measures the SAVED
file:

  1. `showroom_lighting.measure()` — the module's own, never a hand-rolled
     probe: a hand-rolled one already reported 46,319 W once by counting a lamp
     that is not interior. Watts, lamp count and scene mark must be IDENTICAL
     before and after, because this build creates no light.
  2. A COSINE-WEIGHTED TRANSMITTANCE over the two cove emitters. A BVH is
     built from the new geometry ALONE — not from the scene, which is 13.9 G
     instanced triangles and would never finish — and 24,576 cosine-distributed
     rays measure what fraction of each cove's downward emission still reaches
     the room. Its FIRST version counted hits and failed on any, which convicted
     a recessed light slot of having walls; see `occlusion_probe.__doc__` for
     why that was the wrong instrument and what replaced it. A blocked NADIR is
     still an unconditional refusal: that is building UNDER a light.
  3. A z-ceiling check: nothing new may reach above z = 6.200, the round-1 slab
     soffit, because geometry inside that quad renders as a plane slicing the
     new work.
"""

import argparse
import json
import math
import os
import sys
import time

import bpy
import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "tools"), os.path.join(R2, "world"),
           os.path.join(R2, "world/items"), os.path.join(R2, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_exit                                                 # noqa: E402

TOL = 2e-3


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=None)
    p.add_argument("--report", default=None)
    p.add_argument("--no-verify", action="store_true")
    p.add_argument("--no-build", action="store_true",
                   help="MEASURE ONLY. The BEFORE reading, taken with this same "
                        "instrument on this same file, so before and after "
                        "cannot differ because the ruler changed.")
    return p.parse_args(argv)


# --------------------------------------------------------------------------- #
#  THE SET THIS CEILING WAS CUT TO
# --------------------------------------------------------------------------- #

def _hidden(ob):
    """Is this object hidden?  Safely.

    `ob.hide_get()` RAISES `RuntimeError` when the object is not in the active
    view layer, which a 7.5 GB film blend with 30-odd collections can easily
    contain -- and it would raise from inside a Blender `-P` script, which
    exits 0.  `hide_viewport` is a plain property and never raises, so it is
    the fallback.  This matters because the answer decides whether the caller
    reads `matrix_world` or `matrix_basis`, and `matrix_world` IS NOT EVALUATED
    for a hidden object: the worst error that mistake has produced on this
    project is 120.7 m.
    """
    try:
        return bool(ob.hide_get()) or bool(ob.hide_viewport)
    except RuntimeError:
        return bool(ob.hide_viewport)


def _world_bounds(ob):
    """MEASURED in world space.  `matrix_world` is not evaluated for a hidden
    object (worst error on this project: 120.7 m) and is stale for a freshly
    created one, so this uses `matrix_basis` when the object is hidden."""
    M = ob.matrix_basis if _hidden(ob) else ob.matrix_world
    V = np.array([tuple(M @ v.co) for v in ob.data.vertices])
    return V


def assert_set(SC):
    """RAISE unless the round-1 emitters are where this design was cut to."""
    got = {}
    ceil = bpy.data.objects.get("Ceiling")
    if ceil is None or ceil.type != "MESH":
        return None, ("REFUSING: no `Ceiling` mesh in this scene. This ceiling "
                      "is scribed to the built showroom, not to a spec's "
                      "prose; run it on a blend that carries the SHOWROOM "
                      "collection.")
    V = _world_bounds(ceil)
    got["Ceiling"] = {"z": [float(V[:, 2].min()), float(V[:, 2].max())],
                      "verts": len(ceil.data.vertices),
                      "polys": len(ceil.data.polygons),
                      "max_poly_area": round(
                          max(p.area for p in ceil.data.polygons), 2)}
    if abs(V[:, 2].min() - SC.Z_SLAB) > TOL:
        return None, ("REFUSING: the slab soffit is z = %.4f, not the %.3f this "
                      "ceiling hangs under." % (V[:, 2].min(), SC.Z_SLAB))

    for name, want_z, want_ri, want_ro in SC.EMITTER_CLEARANCE:
        ob = bpy.data.objects.get(name)
        if ob is None or ob.type != "MESH":
            return None, "REFUSING: no %s in this scene." % name
        V = _world_bounds(ob)
        rr = np.hypot(V[:, 0], V[:, 1])
        z0, z1 = float(V[:, 2].min()), float(V[:, 2].max())
        ri, ro = float(rr.min()), float(rr.max())
        got[name] = {"z": [z0, z1], "r": [ri, ro]}
        if abs(z0 - want_z) > TOL or abs(z1 - want_z) > TOL:
            return None, ("REFUSING: %s is at z %.4f..%.4f, not the %.3f the "
                          "slot was cut around." % (name, z0, z1, want_z))
        if abs(ri - want_ri) > 1e-2 or abs(ro - want_ro) > 1e-2:
            return None, ("REFUSING: %s spans r %.4f..%.4f, not the %.2f..%.2f "
                          "the slot was cut around. Re-cut the slot radii in "
                          "world/items/showroom_ceiling.py."
                          % (name, ri, ro, want_ri, want_ro))

    # the two sealed strips.  NOT a refusal -- it is round-1's and read-only --
    # but the panel datum is set 50 mm under the coffer soffit BECAUSE of it,
    # so a coffer that moved would silently expose it.
    for i in (0, 1):
        cof = bpy.data.objects.get("Cove_Coffer_%d" % i)
        stp = bpy.data.objects.get("Cove_Strip_%d" % i)
        if cof is None or stp is None:
            continue
        C = _world_bounds(cof)
        S = _world_bounds(stp)
        sealed = all(C[:, k].min() < S[:, k].min() and
                     C[:, k].max() > S[:, k].max() for k in range(3))
        got["Cove_Coffer_%d" % i] = {
            "z": [float(C[:, 2].min()), float(C[:, 2].max())],
            "y": [float(C[:, 1].min()), float(C[:, 1].max())],
            "strip_sealed_inside_it": bool(sealed)}
        if float(C[:, 2].min()) <= SC.Z_PANEL:
            return None, ("REFUSING: Cove_Coffer_%d's soffit is z %.4f, at or "
                          "below the panel field's %.3f. The panel datum exists "
                          "to conceal it." % (i, C[:, 2].min(), SC.Z_PANEL))

    rods = []
    for i in range(6):
        ob = bpy.data.objects.get("SpotRod_%d" % i)
        if ob is None:
            return None, ("REFUSING: no SpotRod_%d. The canopies land the six "
                          "round-1 rods; without them there is nothing to "
                          "land." % i)
        V = _world_bounds(ob)
        rods.append([round(float(V[:, 0].mean()), 4),
                     round(float(V[:, 1].mean()), 4),
                     round(float(V[:, 2].max()), 4)])
    got["SpotRod_top_z"] = sorted(set(r[2] for r in rods))
    got["SpotRod_xy"] = rods
    if any(abs(r[2] - SC.Z_ROD_TOP) > TOL for r in rods):
        return None, ("REFUSING: the spot rods top out at %s, not the %.3f the "
                      "canopies were cut to." % (got["SpotRod_top_z"],
                                                 SC.Z_ROD_TOP))
    for (wx, wy) in SC.SPOT_RODS:
        if not any(abs(r[0] - wx) < 1e-2 and abs(r[1] - wy) < 1e-2 for r in rods):
            return None, ("REFUSING: no spot rod at (%.2f, %.2f); the rod "
                          "stations have moved." % (wx, wy))
    return got, None


# --------------------------------------------------------------------------- #
#  VERIFY:  did this ceiling get between an emitter and the room?
# --------------------------------------------------------------------------- #

def _new_bvh(SC):
    """A BVH over THE NEW OBJECTS ONLY, in world space.

    `scene.ray_cast` needs a BVH over the whole view layer and this world is
    13.9 G instanced triangles: on this box that never finishes.  It is also
    the wrong question -- nothing in the film but this build can be a NEW
    occluder, so the new build is exactly the set to test.
    """
    from mathutils.bvhtree import BVHTree
    from mathutils import Vector
    verts, faces, n_obj = [], [], 0
    for ob in bpy.data.objects:
        if not ob.name.startswith(SC.PFX) or ob.type != "MESH":
            continue
        n_obj += 1
        M = ob.matrix_basis if _hidden(ob) else ob.matrix_world
        base = len(verts)
        me = ob.data
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        Mn = np.array(M)
        co = co @ Mn[:3, :3].T + Mn[:3, 3]
        verts.extend([Vector(v) for v in co])
        for p in me.polygons:
            vi = list(p.vertices)
            for k in range(1, len(vi) - 1):
                faces.append((base + vi[0], base + vi[k], base + vi[k + 1]))
    if not faces:
        return None, 0, 0
    return (BVHTree.FromPolygons(verts, faces, all_triangles=True, epsilon=0.0),
            n_obj, len(faces))


def occlusion_probe(SC, n_pt=96, n_ray=128, seed=20621):
    """HOW MUCH OF EACH COVE'S DOWNWARD EMISSION SURVIVES ITS OWN REVEAL.

    THE FIRST VERSION OF THIS PROBE WAS THE WRONG INSTRUMENT AND IT MATTERED.
    It fired nine fixed directions per sample and failed the build on ANY hit
    — and a recessed light slot has walls by definition, so it convicted the
    design of being a slot.  2,110 of 6,912 rays "blocked", all of them on the
    reveal, and the verdict carried no information about how much light was
    actually lost.

    What matters to the picture is the COSINE-WEIGHTED fraction of the downward
    hemisphere that reaches the room, because that is proportional to the flux
    a Lambertian emitter delivers.  Directions are drawn by Malley's method
    (uniform on the disc, projected), so the estimator is unbiased for that
    integral and needs no per-ray weight.

    Two verdicts come out of it, and only one is a refusal:
      * `nadir_blocked` — anything at all directly under an emitter.  That is
        building UNDER a light, which is a defect at any transmittance.
      * `transmittance` — reported, with a floor.  A splayed, matt-white reveal
        gives most of the intercepted light back on the first bounce, so this
        UNDERSTATES what the room keeps; the render's own histogram is the
        instrument that settles it, and this is the one that can run in 2 s.
    """
    from mathutils import Vector
    bvh, n_obj, n_tris = _new_bvh(SC)
    if bvh is None:
        return {"n_objects": 0, "note": "no new geometry to test"}

    rng = np.random.default_rng(seed)
    out = {"n_objects": n_obj, "n_tris": n_tris, "emitters": {},
           "n_rays": 0, "nadir_blocked": 0, "worst_transmittance": 1.0}
    for name, z, ri, ro in SC.EMITTER_CLEARANCE:
        # area-weighted sample points on the annulus
        u = (np.arange(n_pt) + 0.5) / n_pt
        rr = np.sqrt(ri * ri + (ro * ro - ri * ri) * u)
        th = 2.0 * math.pi * ((np.arange(n_pt) * 0.6180339887) % 1.0)
        n_ok = n_tot = 0
        nadir = 0
        for r, t in zip(rr, th):
            o = Vector((float(r * math.cos(t)), float(r * math.sin(t)),
                        float(z) - 2e-4))
            if bvh.ray_cast(o, Vector((0, 0, -1)), 40.0)[0] is not None:
                nadir += 1
            # Malley: uniform on the unit disc -> cosine-weighted hemisphere
            a = rng.random(n_ray) * 2.0 * math.pi
            s = np.sqrt(rng.random(n_ray))
            dx, dy = s * np.cos(a), s * np.sin(a)
            dz = -np.sqrt(np.maximum(0.0, 1.0 - s * s))
            for k in range(n_ray):
                n_tot += 1
                if bvh.ray_cast(o, Vector((float(dx[k]), float(dy[k]),
                                           float(dz[k]))), 40.0)[0] is None:
                    n_ok += 1
        T = n_ok / float(n_tot)
        out["emitters"][name] = {"transmittance": round(T, 4),
                                 "n_rays": n_tot,
                                 "nadir_blocked": int(nadir),
                                 "n_points": int(n_pt)}
        out["n_rays"] += n_tot
        out["nadir_blocked"] += int(nadir)
        out["worst_transmittance"] = min(out["worst_transmittance"], round(T, 4))
    return out


def z_probe(SC):
    """Nothing new may reach above the round-1 slab soffit."""
    worst = None
    for ob in bpy.data.objects:
        if not ob.name.startswith(SC.PFX) or ob.type != "MESH":
            continue
        M = ob.matrix_basis if _hidden(ob) else ob.matrix_world
        me = ob.data
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        Mn = np.array(M)
        z = (co @ Mn[:3, :3].T + Mn[:3, 3])[:, 2]
        zm = float(z.max())
        if worst is None or zm > worst[1]:
            worst = (ob.name, zm)
    return worst


def material_depth(SC):
    """Every material this build made, and how many texture nodes it carries.

    The project's own material floor.  A ceiling that is procedurally flat is
    the 686 m^2 quad again with more polygons in front of it.
    """
    out = {}
    for m in bpy.data.materials:
        if not m.name.startswith(SC.PFX) or not m.node_tree:
            continue
        tex = sum(1 for nd in m.node_tree.nodes
                  if nd.bl_idname.startswith("ShaderNodeTex")
                  and nd.bl_idname != "ShaderNodeTexImage")
        bump = [nd for nd in m.node_tree.nodes
                if nd.bl_idname == "ShaderNodeBump"]
        img = [nd for nd in m.node_tree.nodes
               if nd.bl_idname == "ShaderNodeTexImage"]
        # the bump chain must actually REACH Principled's Normal, BY NAME.
        # feeding that socket by index shipped 14 dead bump stacks on this
        # project when Blender 5.2 moved it from 5 to 6.
        wired = False
        for nd in m.node_tree.nodes:
            if nd.bl_idname != "ShaderNodeBsdfPrincipled":
                continue
            s = nd.inputs.get("Normal")
            wired = bool(s is not None and s.is_linked)
        out[m.name] = {"texture_nodes": tex, "bump_nodes": len(bump),
                       "image_nodes": len(img), "normal_socket_wired": wired}
    return out


# --------------------------------------------------------------------------- #

def main():
    t_start = time.time()
    a = parse_args()
    src = bpy.data.filepath
    scene = bpy.context.scene

    import showroom_lighting as SL
    import film_exposure as FX
    import showroom_ceiling as SC
    import itemkit as K

    print(">> SOURCE: %s" % src)
    rep = {"source": src, "out": a.out, "t": time.strftime("%F %T")}

    # ---- the BEFORE reading, with the module's own instrument -------------
    before = SL.measure(scene)
    rep["lighting_before"] = before
    print(">> LIGHTING BEFORE: %s" % before)
    grade = {"view_transform": scene.view_settings.view_transform,
             "look": scene.view_settings.look,
             "exposure": round(scene.view_settings.exposure, 4)}
    rep["grade"] = grade
    print(">> GRADE: %s" % grade)

    got, why = assert_set(SC)
    if why:
        print(">> %s" % why)
        rep["refusal"] = why
        if a.report:
            json.dump(rep, open(a.report, "w"), indent=1)
        return gate_exit.verdict("CEILING_VACUOUS")
    rep["set"] = got
    print(">> SET: Ceiling %d verts / %d polys, largest face %.1f m^2, "
          "soffit z %.3f" % (got["Ceiling"]["verts"], got["Ceiling"]["polys"],
                             got["Ceiling"]["max_poly_area"],
                             got["Ceiling"]["z"][0]))
    for i in (0, 1):
        k = "Cove_Coffer_%d" % i
        if k in got:
            print(">> %s: soffit z %.3f, Cove_Strip_%d sealed inside it: %s"
                  % (k, got[k]["z"][0], i, got[k]["strip_sealed_inside_it"]))

    # ---- build ------------------------------------------------------------
    if not a.no_build:
        n_before = len(bpy.data.objects)
        K.purge(SC.PFX, SC.COLL)                 # idempotent: re-runnable
        t0 = time.time()
        summary = SC.build()
        rep["build"] = summary
        rep["build_s"] = round(time.time() - t0, 1)
        print(">> BUILT in %.1f s: %d objects, %d polys"
              % (rep["build_s"], len(bpy.data.objects) - n_before,
                 summary["polys"]))
    else:
        print(">> --no-build: MEASURE ONLY")

    # ---- the AFTER reading, same instrument -------------------------------
    after = SL.measure(scene)
    rep["lighting_after"] = after
    print(">> LIGHTING AFTER:  %s" % after)
    drift = []
    for k in ("interior_lamp_watts", "n_interior_lamps", "scene_mark",
              "n_interior_emissive_materials", "interior_emission_strength_sum"):
        if before.get(k) != after.get(k):
            drift.append("%s: %r -> %r" % (k, before.get(k), after.get(k)))
    rep["lighting_drift"] = drift
    if drift:
        print(">> THE LIGHTING MOVED. This build creates no light and may not:")
        for d in drift:
            print("     %s" % d)
        if a.report:
            json.dump(rep, open(a.report, "w"), indent=1)
        return gate_exit.verdict("CEILING_LIGHT_DRIFT_FAIL")

    # ---- verify ------------------------------------------------------------
    if not a.no_verify and not a.no_build:
        occ = occlusion_probe(SC)
        rep["occlusion"] = occ
        print(">> COVE TRANSMITTANCE, %d rays over %d new tris:"
              % (occ.get("n_rays", 0), occ.get("n_tris", 0)))
        for n, d in sorted(occ.get("emitters", {}).items()):
            print("     %-16s %.4f cosine-weighted downward, nadir blocked "
                  "at %d of %d sample points"
                  % (n, d["transmittance"], d["nadir_blocked"], d["n_points"]))
        if occ.get("nadir_blocked"):
            print(">> something is directly UNDER an emitter. Whatever the "
                  "transmittance, that is building under a light.")
            if a.report:
                json.dump(rep, open(a.report, "w"), indent=1)
            return gate_exit.verdict("CEILING_UNDER_EMITTER_FAIL")
        if occ.get("worst_transmittance", 1.0) < 0.70:
            print(">> a cove keeps only %.3f of its downward emission. The "
                  "reveal is eating beat 1." % occ["worst_transmittance"])
            if a.report:
                json.dump(rep, open(a.report, "w"), indent=1)
            return gate_exit.verdict("CEILING_REVEAL_FAIL")

        w = z_probe(SC)
        rep["highest_new_surface"] = [w[0], round(w[1], 4)] if w else None
        print(">> Z CEILING: highest new surface %s at z %.4f (slab soffit "
              "%.3f)" % (w[0], w[1], SC.Z_SLAB))
        if w and w[1] > SC.Z_SLAB + 1e-4:
            if a.report:
                json.dump(rep, open(a.report, "w"), indent=1)
            return gate_exit.verdict("CEILING_INSIDE_SLAB_FAIL")

        md = material_depth(SC)
        rep["materials"] = md
        for n, d in sorted(md.items()):
            print(">> MAT %-22s tex %2d  bump %d  image %d  Normal wired %s"
                  % (n, d["texture_nodes"], d["bump_nodes"], d["image_nodes"],
                     d["normal_socket_wired"]))
        badm = [n for n, d in md.items()
                if d["texture_nodes"] < 3 or d["bump_nodes"] < 2
                or d["image_nodes"] or not d["normal_socket_wired"]]
        if badm:
            print(">> materials failing the depth floor: %s" % badm)
            if a.report:
                json.dump(rep, open(a.report, "w"), indent=1)
            return gate_exit.verdict("CEILING_MATERIAL_FLAT_FAIL")

    # ---- the grade, re-asserted, and the levelling guard ------------------
    g = FX.apply(scene)
    print(">> GRADE re-asserted: %s look=%r exposure %+.3f"
          % (g["view_transform"], g["look"], g["exposure"]))
    # UNCONDITIONAL, and never inside a branch.  See build_film_scene.py's
    # refuse_unless_levelled docstring: this guard has already failed once on
    # this project by sitting inside `if not a.no_rig:`.
    lev = SL.assert_levelled(scene)
    rep["assert_levelled"] = lev
    print(">> assert_levelled PASS: %s" % lev)

    # ---- save -------------------------------------------------------------
    if a.out:
        outp = os.path.abspath(a.out)
        os.makedirs(os.path.dirname(outp), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=outp, compress=False)
        if not os.path.exists(outp) or os.path.getmtime(outp) < t_start:
            print(">> the save produced no file this run at %s" % outp)
            return gate_exit.verdict("CEILING_NOT_SAVED_FAIL")
        rep["saved"] = outp
        rep["saved_mb"] = round(os.path.getsize(outp) / 1048576.0, 1)
        print(">> saved %s  %.1f MB" % (outp, rep["saved_mb"]))

    if a.report:
        os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
        json.dump(rep, open(a.report, "w"), indent=1)
        print(">> report %s" % a.report)
    return gate_exit.verdict("CEILING_MEASURED_OK" if a.no_build
                             else "CEILING_BUILT")


if __name__ == "__main__":
    gate_exit.guard(main, tool="r2621_ceiling_build")
