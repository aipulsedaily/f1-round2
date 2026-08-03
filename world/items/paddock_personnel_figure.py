"""paddock_personnel_figure -- 260 people, the worked figure for `humankit`.

WHY THIS ITEM AND NOT A MARSHAL
-------------------------------
`marshal_figure_standing` reports the same 767.2 sharp px, and its manifest note
says "fully covered -- overall, gloves, helmet or balaclava -- so no skin is
needed, which is what makes this tractable". That is precisely why it is the
wrong item to prove a human foundation on: a balaclava is how the wave-1
modules avoided the face and the hands, which are two of the ten measured
defects. `paddock_personnel_figure`'s own note says the opposite --

    "HARDER than the trackside figures: exposed forearms, neck and face."

-- and it carries the same measured screen presence, 260 instances, and the
hero tier. So it exercises every layer: face, hair, hands with fingers,
clothing, footwear, skin.

WHAT THE MANIFEST OBLIGES
-------------------------
    nearest_camera_m      10.0        lens_at_closest_mm   35
    onscreen_px_4k        653         instances            260
    hero                  True        zone                 people

    px_per_m = 3840 x 35 / 36 / 10.0 = 373.3 px/m  ->  2.679 mm per pixel

`docs/screen_presence.json` measures this family at a peak SHARP **551.8 px**
and a minimum depth of **7.602 m** (regenerated 2026-08-03 03:58). That figure
is an UPPER BOUND (five people-zone items share one 28-host set and inherit its
best moment), so the module is gated at the manifest's 10.0 m and ALSO re-gated
with `--filmed-distance-m 7.602`, which is the hardest reading of the evidence.

**767.2 / 7.537 WAS WRONG IN THREE PLACES AND 39 % HIGH, AND IT WAS IN THIS
FILE FOUR TIMES.** `screen_presence.json` has no `peak_sharp_px` field at all,
only `peak_sharp_px_4k`; 767.2 was a pre-shutter-fix RAMPED number superseded
by R2-037. Corrected in `humankit`'s header and in `crew_figure` by the fifth
pass, and here by the sixth. `PEEP_PX` is deliberately LEFT at 767.2 and
documented below for the same reason `crew_figure.PEEP_PX` is: every peep
render and every gate run on this item was framed at 8.513 m when the film
never gets closer than 11.845 m sharp, which is a HARDER test than the evidence
requires, so those passes stand and do not have to be re-earned.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/paddock_personnel_figure.py -- --test-scene
"""

import argparse
import json
import math
import os
import sys
import time

import numpy as np

_WORLD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _WORLD not in sys.path:
    sys.path.insert(0, _WORLD)

import itemkit as K                                          # noqa: E402
import humankit as HK                                        # noqa: E402
import world_contract as C                                   # noqa: E402

try:
    import bpy
except ImportError:                                          # pure-python paths
    bpy = None

ITEM = "paddock_personnel_figure"
COLL = "W_Item_PaddockPersonnelFigure"
PFX = "PPF_"

FILMED_AT_M, LENS_MM = 10.0, 35.0
MEASURED_CLOSEST_M = 7.602            # docs/screen_presence.json, min_depth_m
#: The HONEST measurement of this family's macro resolve, regenerated
#: 2026-08-03: `peak_sharp_px_4k` on a 1.750 m figure. The 767.2 that stood
#: here was a pre-shutter-fix ramped figure, superseded by R2-037, and 39.0 %
#: high. Use this for any NEW judgement about what has to be built.
PRESENCE_PX = 551.8
#: What every peep and every gate run on this item was actually framed at.
#: Kept at 767.2 ON PURPOSE -- it is 8.513 m against the film's 11.845 m sharp
#: closest, i.e. a harder test than the evidence requires -- so the passes
#: earned under it stand. Do not "correct" it; correcting it would silently
#: make every previous verdict incomparable. See crew_figure.PEEP_PX.
PEEP_PX = 767.2
N_DECLARED = 260
PX_PER_M = K.px_per_m(FILMED_AT_M, LENS_MM)
SEED = 20260802

# A 60 x 60 m patch of `build_architecture:paving` verified to have NO terrain
# ownership anywhere in it, so `world_ground_z` is analytic over the whole crowd
# and nothing is seated on an invented height (itemkit.ground_z would refuse).
AREA_CENTRE = (-44.0, -50.0)
AREA = (-64.0, -68.0, -24.0, -32.0)          # x0, y0, x1, y1 -- 40 x 36 m
# What the paddock is looking at: the car, at the manifest's own measured size.
FOCUS = (-44.0, -30.0, 1.05)

# FOOT EMBED -- A DELIBERATE, STATED DEVIATION FROM LAW 5.
#
# `world_contract.BASE_EMBED_M` is 0.020 m and Law 5 says anything standing on
# ground embeds at least that. That number is right for a post, a barrier foot
# or a slab, and wrong for a shoe: the outsole here is 26-38 mm thick, so a
# 20 mm embed sinks a third of the sole into the concrete and the welt line --
# the brightest edge on the whole shoe under a 12.5 deg sun -- disappears.
# `spectator_seated` reached the same conclusion independently and used 6 mm.
# 8 mm is used here, and it is a CHOICE, recorded so it can be overruled rather
# than discovered.
FOOT_EMBED_M = 0.008


def _team_for_group(gid):
    """A brand from itemkit's ONE book (Law 2), per conversation group."""
    return K.pick_brand(SEED, 7717, int(gid))


def build(scene=None, count=None, lod=None, seed=SEED, test_scene=False,
          samples=256, quiet=False):
    """Emit `count` paddock figures, ONE OBJECT EACH, into COLL.

    ONE OBJECT PER PERSON is not an accident of style. `tools/item_gate.py`
    frames the MEDIAN-TRIANGLE object of the population as its witness subject;
    if a figure were eleven objects the gate would point its camera at a shoe
    and report on the person. It also means `instance_variation` measures the
    spread of PEOPLE rather than the spread of body parts.
    """
    if bpy is None:
        raise RuntimeError("build() needs Blender")
    t0 = time.time()
    n = int(count or N_DECLARED)
    scene = scene or bpy.context.scene
    # Blender's factory Cube, spare Camera and 1000 W point Light --
    # see humankit.purge_factory_scene for why this is not cosmetic.
    _gone = HK.purge_factory_scene()
    if _gone:
        HK.log("purged the factory scene: %s" % (_gone,))
    root = K.coll(COLL)
    K.purge(PFX, COLL)
    root = K.coll(COLL)
    mats = HK.figure_materials(PFX)

    plan = HK.compose_crowd(seed, n, AREA, focus=FOCUS, walk_frac=0.34,
                            focus_frac=0.40, spacing=1.05)
    if len(plan) < n:
        raise RuntimeError(
            "compose_crowd placed %d of %d figures in %s -- the area is too "
            "small or the spacing too large. Say what the item needs instead "
            "of quietly shipping a thinner crowd." % (len(plan), n, AREA))

    figs, objs, stats = [], [], []
    from mathutils import Matrix, Vector
    for i, rec in enumerate(plan):
        fseed = seed * 1000003 + i * 7919
        b = HK.sample_body(HK.rng_for(fseed, 1), adult_only=True)
        x, y = rec["pos"]
        # SHARED ATTENTION (defect 9): the gaze is solved from the head's own
        # world position to the thing being looked at, so a figure at the far
        # end of the paddock turns further than one beside it -- which is what
        # makes a crowd look at something instead of merely facing it.
        gaze = None
        if rec["look_at"] is not None:
            head_w = (x, y, 0.87 * b.stature)
            gaze = HK.gaze_to(head_w, rec["look_at"], rec["yaw_deg"])
        tier = lod or HK.LOD.for_distance(FILMED_AT_M, LENS_MM, b.stature)
        w = HK.sample_wardrobe(HK.rng_for(fseed, 2), b, role="paddock",
                               team=_team_for_group(rec["group"]),
                               team_frac=0.34)
        fig = HK.build_figure(seed=fseed, lod=tier, kind=rec["kind"],
                              role="paddock", body=b, wardrobe=w, gaze=gaze)
        name = "%sFig_%03d" % (PFX, i)
        ob = HK.emit_mesh(name, fig["mesh"], root, mats)
        yaw = math.radians(rec["yaw_deg"])
        R = Matrix.Rotation(yaw, 3, "Z")
        gz = K.ground_z(x, y)
        T = Vector((x, y, gz - FOOT_EMBED_M))
        ob.rotation_mode = "XYZ"
        ob.rotation_euler = (0.0, 0.0, yaw)
        ob.location = T + (R @ Vector(ob.location))
        objs.append(ob)
        figs.append(fig)
        st = HK.figure_stats(fig)
        st.update({"x": round(x, 3), "y": round(y, 3),
                   "yaw_deg": round(rec["yaw_deg"], 1),
                   "group": rec["group"], "group_size": rec["group_size"],
                   "walking": rec["walking"], "ground_z": round(gz, 4),
                   "gaze_deg": None if gaze is None else
                   [round(gaze[0], 1), round(gaze[1], 1)]})
        stats.append(st)
        if not quiet and (i % 40 == 0):
            HK.log("figure %3d/%d  %.1fs" % (i, n, time.time() - t0))

    K.assert_no_external_assets()
    tris = sum(s["tris"] for s in stats)
    HK.log("%d figures, %d triangles (%.0f per person), %.1fs"
           % (len(objs), tris, tris / max(len(objs), 1), time.time() - t0))
    if test_scene:
        _test_scene(scene, root, objs, figs, samples)
    return {"root": root, "objects": objs, "figures": figs, "stats": stats,
            "materials": mats, "triangles": tris}


def _test_scene(scene, root, objs, figs, samples):
    """Contract sun, a contract-height ground, and the macro camera at 4K."""
    from mathutils import Vector
    cams = K.coll(COLL + "/Cameras", root)
    stand = K.coll(COLL + "/Standins", root)
    K.contract_sun(PFX, scene=scene, coll_=stand)
    # AND THEN OFF THE REFUTED EXPOSURE `contract_sun` LEAVES BEHIND.
    # Every frame this item has ever been judged on -- including the
    # ITEM_ACCEPTED 8-of-8 gate run -- was shot 0.580 stops over, at
    # world_contract's -3.048 rather than the film's measured -3.628.
    # See humankit.film_exposure; it raises rather than falling back.
    HK.film_exposure(scene)
    # THE STANDIN GROUND NEEDS A MATERIAL, and it is not cosmetic.
    # `K.ground_plane(material=None)` leaves Blender's default 0.8-albedo grey.
    # Under the contract sun that is a 58 m reflector, and the first 767 px peep
    # came back with every figure washed pale and colourless from the bounce --
    # every appearance judgement made on it was made under the wrong light,
    # which is WAVE1-PEEP-SYNTHESIS systemic 1 in a new costume. The paddock
    # here is `build_architecture`'s paving, so this is a concrete albedo.
    gm = K.NT(PFX + "StandinGround")
    _gp = gm.object_coords()
    _gn = gm.noise(_gp, HK.tex_scale("noise", 0.55), detail=5.0, rough=0.55)
    gm.principled_out(
        base_color=gm.ramp(_gn, [(0.0, (0.052, 0.050, 0.047)),
                                 (1.0, (0.086, 0.084, 0.080))]),
        roughness=gm.maprange(_gn, 0.3, 0.7, 0.72, 0.90), metallic=0.0)
    K.ground_plane(PFX, stand, centre=AREA_CENTRE, span=58.0, res=180,
                   material=gm.m)

    # Frame the MEDIAN figure by triangle count -- the same instance the gate
    # will pick, so the delivered macro and the witness frame are about the same
    # person rather than about whichever one flatters the module.
    order = sorted(range(len(objs)), key=lambda i: figs[i]["tris"])
    k = order[len(order) // 2]
    ob = objs[k]
    ctr = np.array(ob.location) + np.array([0.0, 0.0, 0.92])
    az = math.radians(212.0)
    el = math.radians(11.0)
    d = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az),
                  math.sin(el)])
    loc = ctr + d * FILMED_AT_M
    K.macro_rig(PFX + "CAM_MACRO_4K", tuple(loc), tuple(ctr), LENS_MM, cams,
                scene=scene, samples=samples, want_distance_m=FILMED_AT_M)

    # ---- THE 767 px PEEP -------------------------------------------------
    # 767.2 px on a declared 1.750 m figure is 438.4 px/m, and on the film's
    # 35 mm lens it is 8.513 m -- closer than the manifest's 10.0 m and further
    # than the measured 7.602 m minimum depth. It is NOT the measured presence:
    # that is PRESENCE_PX = 551.8 (see its note). This framing is kept because
    # it is HARDER than the film, not because it is the film. The gate is scored at the manifest
    # distance; this camera exists because the brief's last instruction is
    # "then render at 767 px and ask whether it is a person", and a question
    # about a face cannot be answered at a framing nobody looks at.
    #
    # It frames the HEAD, not the bounding-box centre: at 767 px a whole figure
    # is 767 px and its head is 100, which is the number that decides whether
    # the face was worth building.
    ppm_767 = PEEP_PX / 1.750
    d767 = K.RES_X_4K * LENS_MM / K.SENSOR_MM / ppm_767
    # AIM OFF THE OBJECT'S REAL BOUNDING BOX, NOT OFF ITS ORIGIN.
    # `K.new_mesh` recentres, so `ob.location.z` is the middle of the figure,
    # not its feet. The first version added the figure's height to it and put
    # the aim point 0.98 m above the head: the peep still delivered the right
    # 438.4 px/m, but the subject sat at ndc y 0.03-0.35 instead of centred.
    # Caught by projecting the subject's vertices through the camera BEFORE
    # spending a GPU render, which is the cheap half of "look at the artefact".
    bpy.context.view_layer.update()
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    top_z = max(float(c.z) for c in bb)
    hctr = np.array([ob.location[0], ob.location[1], top_z - 0.115])
    loc7 = hctr + d767 * np.array(
        [math.cos(math.radians(6.0)) * math.cos(math.radians(206.0)),
         math.cos(math.radians(6.0)) * math.sin(math.radians(206.0)),
         math.sin(math.radians(6.0))])
    K.macro_rig(PFX + "CAM_PEEP_767", tuple(loc7), tuple(hctr), LENS_MM, cams,
                scene=scene, samples=samples, want_distance_m=d767)
    HK.log("peep camera at %.3f m -> %.1f px/m; a %.3f m figure reads %.0f px "
           "and its head %.0f px"
           % (d767, ppm_767, 1.750, PEEP_PX, ppm_767 * 0.230))
    scene.camera = bpy.data.objects[PFX + "CAM_MACRO_4K"]
    HK.log("macro subject %s (%d tris, the median of %d)"
           % (ob.name, figs[k]["tris"], len(objs)))
    return ob


def report(res, path=None):
    """Everything measured about this population, in real units."""
    figs = res["figures"]
    stats = res["stats"]
    var = HK.measure_variation(figs)
    pose = HK.measure_pose_spread(figs)
    tri = np.array([s["tris"] for s in stats], float)
    hgt = np.array([s["height_m"] for s in stats], float)
    st = np.array([s["stature_m"] for s in stats], float)
    below = np.array([s["contact"]["below_plane_mm"] for s in stats], float)
    resid = np.array([s["contact"]["residual_mm"] for s in stats], float)
    grp = {}
    for s in stats:
        grp.setdefault(s["group"], []).append(s)
    doc = {
        "item": ITEM,
        "figures": len(stats),
        "triangles_total": int(tri.sum()),
        "triangles_per_person_mean": float(tri.mean()),
        "triangles_per_person_min": int(tri.min()),
        "triangles_per_person_max": int(tri.max()),
        "triangles_per_person_rejected_baseline": 390,
        "stature_m": [float(st.min()), float(st.mean()), float(st.max())],
        "cv_stature": float(st.std() / st.mean()),
        "height_incl_hair_m": [float(hgt.min()), float(hgt.max())],
        "distinct_triangle_counts": int(len(set(int(v) for v in tri))),
        "contact_residual_mm_max": float(resid.max()),
        "geometry_below_contact_plane_mm_max": float(below.max()),
        "groups": len(grp),
        "group_size_mean": float(np.mean([len(v) for v in grp.values()])),
        "walking_fraction": float(np.mean([s["walking"] for s in stats])),
        "gazing_fraction": float(np.mean([s["gaze_deg"] is not None
                                          for s in stats])),
        "sex_fraction_F": float(np.mean([s["sex"] == "F" for s in stats])),
        "garment_types_top": len({s["top"] for s in stats}),
        "garment_types_bottom": len({s["bottom"] for s in stats}),
        "hair_styles": len({s["hair"] for s in stats}),
        "headwear_types": len({s["headwear"] for s in stats}),
        "pose_archetypes": len({s["archetype"] for s in stats}),
        "variation": var,
        "pose_spread": pose,
        "px_per_m_at_manifest_distance": PX_PER_M,
        "mm_per_px_at_manifest_distance": 1000.0 / PX_PER_M,
        "px_per_m_at_measured_closest": K.px_per_m(MEASURED_CLOSEST_M, LENS_MM),
        "foot_embed_m": FOOT_EMBED_M,
        "foot_embed_note": "deliberate deviation from BASE_EMBED_M 0.020; see "
                           "the module docstring",
    }
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".",
                    exist_ok=True)
        json.dump(doc, open(path, "w"), indent=1, default=float)
        HK.log("report -> %s" % path)
    return doc


def selftest(n=64, verbose=True):
    """Pure-python. Measures what the module claims, and includes controls."""
    ok, fails = [], []

    def chk(name, good, detail):
        ok.append((name, bool(good), detail))
        if not good:
            fails.append(name)
        if verbose:
            print("  %-36s %-4s %s" % (name, "PASS" if good else "FAIL", detail))

    plan = HK.compose_crowd(SEED, n, AREA, focus=FOCUS)
    figs = []
    for i, rec in enumerate(plan):
        fseed = SEED * 1000003 + i * 7919
        b = HK.sample_body(HK.rng_for(fseed, 1), adult_only=True)
        figs.append(HK.build_figure(seed=fseed, lod=HK.LOD_L2, kind=rec["kind"],
                                    role="paddock", body=b))
    tri = np.array([f["tris"] for f in figs])
    chk("crowd_is_grouped", len({r["group"] for r in plan}) < n * 0.75,
        "%d figures in %d groups (mean %.2f) -- a uniform scatter gives n groups"
        % (n, len({r["group"] for r in plan}), n / len({r["group"] for r in plan})))
    chk("some_are_walking", 0.05 < np.mean([r["walking"] for r in plan]) < 0.45,
        "%.0f %% walking" % (100 * np.mean([r["walking"] for r in plan])))
    chk("shared_attention", np.mean([r["look_at"] is not None for r in plan]) > 0.6,
        "%.0f %% have a gaze target" % (100 * np.mean(
            [r["look_at"] is not None for r in plan])))
    var = HK.measure_variation(figs, verbose=False)
    chk("variation_is_not_rank1",
        var["participation_ratio"] > 6.0
        and var["participation_ratio"] > 4.0 * var[
            "participation_ratio_of_rank1_control"],
        "participation ratio %.2f of %d parameters; a rank-1 population of the "
        "same size measures %.2f" % (var["participation_ratio"],
                                     var["n_parameters"],
                                     var["participation_ratio_of_rank1_control"]))
    ps = HK.measure_pose_spread(figs, verbose=False)
    chk("poses_do_not_repeat",
        ps["nn_pose_distance_deg_min"] > 8.0
        and ps["control_6_pose_table_nn_min"] < 1.0,
        "closest pose pair %.1f deg; the 6-pose table this replaces measures "
        "%.1f deg" % (ps["nn_pose_distance_deg_min"],
                      ps["control_6_pose_table_nn_min"]))
    chk("triangles_beat_the_mannequin", tri.min() > 4000,
        "%d..%d tris per person (the rejected crowd measured 390)"
        % (tri.min(), tri.max()))
    below = max(f["contact"]["below_plane_mm"] for f in figs)
    chk("contact_solved", below < 1.0,
        "worst geometry below the contact plane %.4f mm over %d figures"
        % (below, n))
    print("\n  %s selftest: %d checks, %d FAILED %s"
          % (ITEM, len(ok), len(fails), fails or ""))
    return not fails


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    p = argparse.ArgumentParser(prog=ITEM)
    p.add_argument("--build", action="store_true")
    p.add_argument("--test-scene", action="store_true")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--count", type=int, default=N_DECLARED)
    p.add_argument("--lod", default=None)
    p.add_argument("--samples", type=int, default=256)
    p.add_argument("--save", default=os.path.join(
        _WORLD, "items", ITEM + "_test.blend"))
    p.add_argument("--report", default=os.path.join(
        os.path.dirname(_WORLD), "render/items", ITEM, "population.json"))
    a = p.parse_args(argv)
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    lod = {"L0": HK.LOD_L0, "L1": HK.LOD_L1, "L2": HK.LOD_L2,
           "L3": HK.LOD_L3}.get(a.lod)
    res = build(count=a.count, lod=lod, test_scene=a.test_scene,
                samples=a.samples)
    report(res, a.report)
    K.interface_json(ITEM, os.path.join(_WORLD, "items", ITEM + "_interface.json"),
                     collection=COLL, prefix=PFX,
                     figures=len(res["objects"]),
                     triangles=res["triangles"],
                     materials=[m.name for m in res["materials"]],
                     vertex_attributes=list(HK.Mesh.CHANNELS) + ["hk_col"],
                     foot_embed_m=FOOT_EMBED_M,
                     humankit="world/humankit.py")
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=a.save, compress=True)
        HK.log("saved %s" % a.save)
        HK.log("gate: " + " ".join(K.gate_command(ITEM, a.save,
                                                  collection=COLL)))


if __name__ == "__main__":
    main()
