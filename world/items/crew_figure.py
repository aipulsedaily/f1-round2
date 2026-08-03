"""crew_figure -- 120 pit crew in fireproofs, the COVERED tier of `humankit`.

WHY THIS ITEM
-------------
The human brief names two tiers and calls this one the hard one:

    "Pit crew -- the HARD tier. Fully-covered figures seen at 10-30 m. Helmets,
     gloves, fireproof overalls, boots. Covered does not mean easy: it means
     fabric, seams, folds, equipment and posture carry the entire read."

and the manifest agrees -- `crew_figure`, 120 instances, "completely covered --
helmet, visor, balaclava, fireproofs, gloves -- zero exposed skin".

That is the opposite of `paddock_personnel_figure`, which was chosen as the
worked item precisely because it exposes face, forearms and neck. Together they
exercise the whole stack: one proves the skin, the face and the hands, this one
proves the cloth, the seams, the equipment and the silhouette -- and this one is
where the last build failed, because a covered figure has nowhere to hide a
fabric shader that renders as felt.

WHAT THE EVIDENCE OBLIGES
-------------------------
    manifest      nearest_camera_m 12.0   lens 35 mm   onscreen_px_4k 544
                  instances 120           hero True    zone people
    measured      peak_sharp_px_4k 551.8  min_depth_m 7.602   (screen_presence,
                                                               regenerated
                                                               2026-08-03 03:58)

`peak_sharp_px_4k` is the field that matters and it is **551.8**, marginally
above the manifest's own 544 -- so this module is gated at the manifest's 12.0 m
AND looked at at 11.845 m, which is where 551.8 px on a 1.750 m figure puts the
camera on a 35 mm lens.

**THIS SAID 767.2 px / 7.537 m UNTIL 2026-08-03 AND THE PIXEL FIGURE WAS
WRONG.** It was a pre-shutter-fix RAMPED number, superseded by R2-037, and it
overstates the real macro resolve by 39.0 %. Two consequences, both in this
module's favour and both worth stating rather than quietly correcting:

  * every peep render and the ITEM_ACCEPTED 8/8 gate run were framed at 767 px,
    i.e. at **8.518 m when the film never gets closer than 11.845 m sharp**.
    That is a HARDER test than the evidence requires, so the pass stands; it is
    not a pass that has to be re-earned.
  * `PEEP_PX` still drives `HK.LOD.for_px`, and both 767.2 and 551.8 land on
    **L0**, so no geometry changed. The tier was never at risk here. It IS at
    risk on the seated crowd, where the same class of stale number is what put
    85 % of a grandstand on L1 mittens.

`PEEP_PX` is deliberately left at the harder 767.2 so that the accepted
artefacts and the numbers quoted against them stay comparable; `PRESENCE_PX` is
the honest measurement and `--peep-px` overrides either.

    px_per_m = 3840 x 35 / 36 / 12.0 = 311.1 px/m  ->  3.214 mm per pixel

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/crew_figure.py -- --test-scene
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

try:
    import bpy
except ImportError:
    bpy = None

ITEM = "crew_figure"
COLL = "W_Item_CrewFigure"
PFX = "CRF_"

FILMED_AT_M, LENS_MM = 12.0, 35.0
MEASURED_CLOSEST_M = 7.602            # screen_presence.json min_depth_m
PRESENCE_PX = 551.8                   # ... peak_sharp_px_4k, THE MEASUREMENT
PEEP_PX = 767.2                       # ... what the accepted artefacts used;
#                                       39 % closer than the film ever gets,
#                                       kept so the 8/8 run stays comparable.
#                                       Both tier to L0. See the docstring.
N_DECLARED = 120
PX_PER_M = K.px_per_m(FILMED_AT_M, LENS_MM)
SEED = 20260803

# The same 60 x 60 m patch of `build_architecture:paving` that
# `paddock_personnel_figure` verified has NO terrain ownership anywhere in it,
# so `world_ground_z` is analytic over the whole group and nobody is standing on
# an invented height. A crew works in the pit lane; the pit lane's own paving is
# built by another module and this item does not own it, so the standin ground
# here is the paddock apron at the same contract height.
AREA_CENTRE = (-44.0, -50.0)
AREA = (-60.0, -64.0, -28.0, -36.0)
FOCUS = (-44.0, -33.0, 0.65)          # the car in the box: crew watch the CAR

# See `paddock_personnel_figure`: 20 mm of BASE_EMBED_M sinks a third of a
# 30 mm race-boot sole into the concrete and loses the welt line, which is the
# brightest edge on the boot under a 12.5 deg sun. A deliberate, stated
# deviation from Law 5, recorded so it can be overruled rather than discovered.
FOOT_EMBED_M = 0.008

# A pit crew stands and kneels around a car; it does not wander a paddock. The
# archetypes are weighted to that, and `crew_roles` below turns the weighting
# into named jobs so the group reads as a crew rather than as a queue.
CREW_POSES = (
    ("stand_relaxed", 0.10), ("arms_folded", 0.13), ("hands_on_hips", 0.11),
    ("hands_behind_back", 0.07), ("radio_talk", 0.10), ("clipboard", 0.08),
    ("pointing", 0.07), ("talking_turned", 0.09), ("watching_up", 0.06),
    ("arms_akimbo_watch", 0.09), ("lean_on_rail", 0.05), ("adjust_cap", 0.05),
)


def _team_for_group(gid):
    """A brand from itemkit's ONE book (Law 2), per crew group.

    A pit crew is a TEAM, so the team colour is a property of the group and not
    of the person: a group of six in six different liveries is the tell that
    nobody thought about it.
    """
    return K.pick_brand(SEED, 4441, int(gid))


def build(scene=None, count=None, lod=None, seed=SEED, test_scene=False,
          samples=256, quiet=False):
    """Emit `count` crew figures, ONE OBJECT EACH, into COLL."""
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
    mats = HK.figure_materials(PFX, crew=True)

    plan = HK.compose_crowd(seed, n, AREA, focus=FOCUS, walk_frac=0.16,
                            focus_frac=0.62, spacing=1.10)
    if len(plan) < n:
        raise RuntimeError(
            "compose_crowd placed %d of %d figures in %s -- say what the item "
            "needs instead of quietly shipping a thinner crew."
            % (len(plan), n, AREA))

    from mathutils import Matrix, Vector
    figs, objs, stats = [], [], []
    for i, rec in enumerate(plan):
        fseed = seed * 1000003 + i * 7919
        b = HK.sample_body(HK.rng_for(fseed, 1), adult_only=True)
        x, y = rec["pos"]
        gaze = None
        if rec["look_at"] is not None:
            gaze = HK.gaze_to((x, y, 0.87 * b.stature), rec["look_at"],
                              rec["yaw_deg"])
        tier = lod or HK.LOD.for_px(PEEP_PX)
        rp = HK.rng_for(fseed, 4)
        arche = HK._pick_weighted(rp.u(), CREW_POSES)
        w = HK.sample_wardrobe(HK.rng_for(fseed, 2), b, role="crew",
                               team=_team_for_group(rec["group"]),
                               team_frac=1.0)
        fig = HK.build_figure(seed=fseed, lod=tier, kind=rec["kind"],
                              role="crew", body=b, wardrobe=w, gaze=gaze,
                              archetype=arche)
        ob = HK.emit_mesh("%sFig_%03d" % (PFX, i), fig["mesh"], root, mats)
        yaw = math.radians(rec["yaw_deg"])
        R = Matrix.Rotation(yaw, 3, "Z")
        gz = K.ground_z(x, y)
        ob.rotation_mode = "XYZ"
        ob.rotation_euler = (0.0, 0.0, yaw)
        ob.location = Vector((x, y, gz - FOOT_EMBED_M)) + (R @ Vector(ob.location))
        objs.append(ob)
        figs.append(fig)
        st = HK.figure_stats(fig)
        st.update({"x": round(x, 3), "y": round(y, 3),
                   "yaw_deg": round(rec["yaw_deg"], 1),
                   "group": rec["group"], "group_size": rec["group_size"],
                   "head_kit": fig["wardrobe"].get("head_kit"),
                   "team": fig["wardrobe"].get("team"),
                   "walking": rec["walking"], "ground_z": round(gz, 4)})
        stats.append(st)
        if not quiet and (i % 20 == 0):
            HK.log("figure %3d/%d  %.1fs" % (i, n, time.time() - t0))

    K.assert_no_external_assets()
    tris = sum(s["tris"] for s in stats)
    HK.log("%d crew, %d triangles (%.0f per person), %.1fs"
           % (len(objs), tris, tris / max(len(objs), 1), time.time() - t0))
    if test_scene:
        _test_scene(scene, root, objs, figs, samples)
    return {"root": root, "objects": objs, "figures": figs, "stats": stats,
            "materials": mats, "triangles": tris}


def _test_scene(scene, root, objs, figs, samples):
    """Contract sun, a concrete-albedo standin ground, TWO cameras."""
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
    gm = K.NT(PFX + "StandinGround")
    _gp = gm.object_coords()
    _gn = gm.noise(_gp, HK.tex_scale("noise", 0.55), detail=5.0, rough=0.55)
    gm.principled_out(
        base_color=gm.ramp(_gn, [(0.0, (0.052, 0.050, 0.047)),
                                 (1.0, (0.086, 0.084, 0.080))]),
        roughness=gm.maprange(_gn, 0.3, 0.7, 0.72, 0.90), metallic=0.0)
    K.ground_plane(PFX, stand, centre=AREA_CENTRE, span=58.0, res=180,
                   material=gm.m)

    order = sorted(range(len(objs)), key=lambda i: figs[i]["tris"])
    k = order[len(order) // 2]
    ob = objs[k]
    ctr = np.array(ob.location) + np.array([0.0, 0.0, 0.92])
    az, el = math.radians(212.0), math.radians(10.0)
    d = np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az),
                  math.sin(el)])
    K.macro_rig(PFX + "CAM_MACRO_4K", tuple(ctr + d * FILMED_AT_M), tuple(ctr),
                LENS_MM, cams, scene=scene, samples=samples,
                want_distance_m=FILMED_AT_M)

    # The 767 px peep: `screen_presence.json`'s own peak SHARP figure for this
    # family, which is closer than the manifest and is the framing the brief
    # says to ask "is this a person" at.
    ppm = PEEP_PX / 1.750
    d767 = K.RES_X_4K * LENS_MM / K.SENSOR_MM / ppm
    bpy.context.view_layer.update()
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    top_z = max(float(c.z) for c in bb)
    hctr = np.array([ob.location[0], ob.location[1], top_z - 0.42])
    dd = np.array([math.cos(math.radians(6.0)) * math.cos(math.radians(206.0)),
                   math.cos(math.radians(6.0)) * math.sin(math.radians(206.0)),
                   math.sin(math.radians(6.0))])
    K.macro_rig(PFX + "CAM_PEEP_767", tuple(hctr + d767 * dd), tuple(hctr),
                LENS_MM, cams, scene=scene, samples=samples,
                want_distance_m=d767)
    scene.camera = bpy.data.objects[PFX + "CAM_MACRO_4K"]
    HK.log("macro subject %s (%d tris, median of %d); peep at %.3f m -> %.1f "
           "px/m" % (ob.name, figs[k]["tris"], len(objs), d767, ppm))
    return ob


def report(res, path=None):
    figs, stats = res["figures"], res["stats"]
    var = HK.measure_variation(figs, verbose=False)
    pose = HK.measure_pose_spread(figs, verbose=False)
    tri = np.array([s["tris"] for s in stats], float)
    st = np.array([s["stature_m"] for s in stats], float)
    below = np.array([s["contact"]["below_plane_mm"] for s in stats], float)
    io = [HK.inside_out_fraction(f, n_rays=400, seed=1000 + i)
          for i, f in enumerate(figs[:12])]
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
        "distinct_triangle_counts": int(len(set(int(v) for v in tri))),
        "geometry_below_contact_plane_mm_max": float(below.max()),
        "head_kits": {k: sum(1 for s in stats if s["head_kit"] == k)
                      for k in {s["head_kit"] for s in stats}},
        "teams": len({s["team"] for s in stats}),
        "groups": len({s["group"] for s in stats}),
        "pose_archetypes": len({s["archetype"] for s in stats}),
        "inside_out_fraction_max_of_12": float(max(io)),
        "orient_pieces_flipped_mean": float(np.mean(
            [f["orient"]["flipped"] for f in figs])),
        "orient_pieces_undecided_total": int(sum(
            len(f["orient"]["abstained"]) for f in figs)),
        "variation": var,
        "pose_spread": pose,
        "px_per_m_at_manifest_distance": PX_PER_M,
        "px_per_m_at_767px_peep": PEEP_PX / 1.750,
        "foot_embed_m": FOOT_EMBED_M,
    }
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".",
                    exist_ok=True)
        json.dump(doc, open(path, "w"), indent=1, default=float)
        HK.log("report -> %s" % path)
    return doc


def selftest(n=48, verbose=True):
    """Pure python, on the artefact, with controls."""
    ok, fails = [], []

    def chk(name, good, detail):
        ok.append((name, bool(good), detail))
        if not good:
            fails.append(name)
        if verbose:
            print("  %-34s %-4s %s" % (name, "PASS" if good else "FAIL", detail))

    plan = HK.compose_crowd(SEED, n, AREA, focus=FOCUS, focus_frac=0.62)
    figs = []
    for i, rec in enumerate(plan):
        fseed = SEED * 1000003 + i * 7919
        b = HK.sample_body(HK.rng_for(fseed, 1), adult_only=True)
        rp = HK.rng_for(fseed, 4)
        figs.append(HK.build_figure(
            seed=fseed, lod=HK.LOD_L2, kind=rec["kind"], role="crew", body=b,
            archetype=HK._pick_weighted(rp.u(), CREW_POSES)))
    tri = np.array([f["tris"] for f in figs])

    # ZERO EXPOSED SKIN is the manifest's own words, so it is MEASURED and not
    # asserted: rays cast inward from a sphere, first hit taken, and the share
    # that lands on the skin slot reported. The CONTROL is the same bodies
    # built as paddock personnel, whose own manifest note says they show
    # "exposed forearms, neck and face" -- so the check is shown to be able to
    # report a covered figure and an uncovered one differently.
    sk_crew, sk_ctl = [], []
    for i, f in enumerate(figs[:6]):
        sk_crew.append(HK.visible_material_fraction(f, HK.MAT_SKIN,
                                                    n_rays=700, seed=31 + i))
        ctl = HK.build_figure(seed=f["seed"], lod=HK.LOD_L2, role="paddock",
                              body=f["body"])
        sk_ctl.append(HK.visible_material_fraction(ctl, HK.MAT_SKIN,
                                                   n_rays=700, seed=31 + i))
    chk("skin_is_covered",
        float(np.mean(sk_crew)) < 0.030
        and float(np.mean(sk_ctl)) > 3.0 * float(np.mean(sk_crew)),
        "%.1f %% of the visible surface is bare skin; the same bodies built as "
        "PADDOCK personnel (face, neck, forearms exposed by design) measure "
        "%.1f %%. Not literally zero -- the residue is the neck inside the "
        "collar and the wrist inside the gauntlet, both of which are seen "
        "edge-on at most"
        % (100 * float(np.mean(sk_crew)), 100 * float(np.mean(sk_ctl))))
    kits = {f["wardrobe"].get("head_kit") for f in figs}
    chk("every_crew_head_is_covered", kits and None not in kits,
        "head kits realised over %d figures: %s" % (len(figs), sorted(kits)))
    chk("triangles_beat_the_mannequin", tri.min() > 4000,
        "%d..%d tris per crew member (the rejected crowd measured 390)"
        % (tri.min(), tri.max()))
    io = max(HK.inside_out_fraction(f, n_rays=400, seed=99 + i)
             for i, f in enumerate(figs[:8]))
    chk("no_surface_renders_inside_out", io < 0.06,
        "at most %.1f %% of the visible surface is inside-out over 8 figures "
        "(the shipped humankit measured 10.5 %%)" % (100 * io))
    und = sum(len(f["orient"]["abstained"]) for f in figs)
    chk("orientation_decided_everywhere", und == 0,
        "%d pieces undecided over %d figures" % (und, len(figs)))
    below = max(f["contact"]["below_plane_mm"] for f in figs)
    chk("contact_solved", below < 1.0,
        "worst geometry below the contact plane %.4f mm over %d figures"
        % (below, len(figs)))
    ps = HK.measure_pose_spread(figs, verbose=False)
    chk("poses_do_not_repeat",
        ps["nn_pose_distance_deg_min"] > 8.0
        and ps["control_6_pose_table_nn_min"] < 1.0,
        "closest pose pair %.1f deg; the 6-pose table this replaces measures "
        "%.1f deg" % (ps["nn_pose_distance_deg_min"],
                      ps["control_6_pose_table_nn_min"]))
    var = HK.measure_variation(figs, verbose=False)
    chk("variation_is_not_rank1",
        var["participation_ratio"] > 6.0
        and var["participation_ratio"] > 4.0
        * var["participation_ratio_of_rank1_control"],
        "participation ratio %.2f of %d parameters; a rank-1 population of the "
        "same size measures %.2f"
        % (var["participation_ratio"], var["n_parameters"],
           var["participation_ratio_of_rank1_control"]))
    print("\n  %s selftest: %d checks, %d FAILED %s"
          % (ITEM, len(ok), len(fails), fails or ""))
    return not fails


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    p = argparse.ArgumentParser(prog=ITEM)
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
    K.interface_json(ITEM, os.path.join(_WORLD, "items",
                                        ITEM + "_interface.json"),
                     collection=COLL, prefix=PFX,
                     figures=len(res["objects"]), triangles=res["triangles"],
                     materials=[m.name for m in res["materials"]],
                     vertex_attributes=list(HK.Mesh.CHANNELS) + ["hk_col"],
                     foot_embed_m=FOOT_EMBED_M, humankit="world/humankit.py")
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=a.save, compress=True)
        HK.log("saved %s" % a.save)
        HK.log("gate: " + " ".join(K.gate_command(ITEM, a.save,
                                                  collection=COLL)))


if __name__ == "__main__":
    main()
