"""human_bench -- a small, fast scene for LOOKING at a figure while iterating.

The gate is necessary and not sufficient, and on this project the instrument has
been the broken thing fourteen times. Everything here exists to shorten the loop
between changing a line of `humankit` and seeing what it did to a rendered
pixel, so the answer comes from a picture rather than from a number.

It is deliberately NOT the item test scene:

  * a handful of figures, not 260, so a build is seconds and a render is a
    modest job on a queue three other agents are sharing;
  * ONE camera (`rq` prewarms every camera in a blend, and a blend with 19 of
    them once destroyed a healthy instance);
  * figures posed and spaced ON PURPOSE -- side on, three-quarter, back --
    because the defects that got the last build rejected were on the shoulder,
    the shoe and the back of the head, and a random crowd hides all three;
  * the same contract sun and the same concrete-albedo ground as the item test
    scene, because a 0.8-albedo default plane under a 12.5 deg sun is a 58 m
    reflector and every appearance judgement made under it is made under the
    wrong light.

    blender -b --factory-startup -P world/items/human_bench.py -- \
        --role crew --n 5 --px 767 --out world/items/human_bench.blend
"""

import argparse
import math
import os
import sys

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

COLL = "W_HumanBench"
# The paddock apron the item module verified terrain-free over 60 m. A standin
# ground at an invented height is a contact shadow in the wrong place, and
# `itemkit.ground_plane` refuses rather than inventing one.
BENCH_CENTRE = (-44.0, -50.0)
PFX = "HB_"
LENS_MM = 35.0
SEED = 20260803

# Poses chosen to expose the defects, not to flatter: arms down puts the
# shoulder seam side-on to the sun, `hands_hips` opens the armhole, `back` turns
# the head away so the hair mass is the whole read.
BENCH = (
    ("stand_relaxed", 0.0),
    ("stand_weight_side", 96.0),
    ("hands_on_hips", 180.0),
    ("arms_folded", 232.0),
    ("pointing", 300.0),
)


def build(n=5, role="paddock", px=767.2, seed=SEED, lod=None, samples=256,
          spacing=1.15, archetypes=None, kind=None, yaws=None, aim="body",
          headwear=None, hair_styles=None):
    if bpy is None:
        raise RuntimeError("human_bench needs Blender")
    # CLEAR THE FACTORY SCENE FIRST. `--factory-startup` ships a Cube, a Camera
    # and a POINT LIGHT at 5.9 m, and the first bench render came back with a
    # 2 m white box occluding the middle figure and every figure lit by a lamp
    # that is not the contract sun -- i.e. every appearance judgement made on it
    # would have been made under the wrong light, which is the systemic error
    # this project has hit repeatedly. Found by looking at the picture.
    for _o in list(bpy.data.objects):
        bpy.data.objects.remove(_o, do_unlink=True)
    root = K.coll(COLL)
    K.purge(PFX, COLL)
    root = K.coll(COLL)
    mats = HK.figure_materials(PFX, crew=(role == "crew"))
    stand = K.coll(COLL + "/Standins", root)
    cams = K.coll(COLL + "/Cameras", root)
    K.contract_sun(PFX, scene=bpy.context.scene, coll_=stand)
    # AND THEN OFF THE REFUTED EXPOSURE IT LEAVES BEHIND. The A/B ladders in
    # HUMAN-REFERENCE secs 0, 00 and 000 -- every appearance judgement about
    # cloth, skin and the face that this project has made -- were all shot on
    # this bench at world_contract's -3.048, which is 0.580 stops over the
    # film's own measured -3.628. See humankit.film_exposure.
    HK.film_exposure(bpy.context.scene)

    gm = K.NT(PFX + "Ground")
    _gp = gm.object_coords()
    _gn = gm.noise(_gp, HK.tex_scale("noise", 0.55), detail=5.0, rough=0.55)
    gm.principled_out(
        base_color=gm.ramp(_gn, [(0.0, (0.052, 0.050, 0.047)),
                                 (1.0, (0.086, 0.084, 0.080))]),
        roughness=gm.maprange(_gn, 0.3, 0.7, 0.72, 0.90), metallic=0.0)
    K.ground_plane(PFX, stand, centre=BENCH_CENTRE, span=56.0, res=180,
                   material=gm.m)

    from mathutils import Vector
    objs, figs = [], []
    tbl = list(archetypes) if archetypes else [b[0] for b in BENCH]
    # THE YAWS DECIDE WHAT IS ON TRIAL. The default row turns three of five
    # figures away, which is right for judging a shoulder seam and useless for
    # judging a face -- A1 and A2 both came back with three backs to camera.
    yaws = list(yaws) if yaws else [b[1] for b in BENCH]
    for i in range(int(n)):
        fseed = seed * 1000003 + i * 7919
        b = HK.sample_body(HK.rng_for(fseed, 1), adult_only=True)
        tier = lod or HK.LOD.for_px(px)
        # A DIFFERENT TEAM PER FIGURE, on purpose. The item scene gives a whole
        # group one livery, which is right for a crew and wrong for a bench:
        # here the question is whether the pattern language has range, so the
        # five figures carry five brands out of itemkit's one book.
        wd = None
        if role == "crew":
            wd = HK.sample_wardrobe(HK.rng_for(fseed, 2), b, role="crew",
                                    team=K.pick_brand(seed, 4441, i * 7 + 3),
                                    team_frac=1.0)
        # THE HAIR BENCH HAS TO PUT HAIR ON TRIAL, and the wardrobe draw will
        # not: `HEADWEAR` puts a hat on 42 % of people and 30 % of the styles
        # drawn are `crop` or `bald`, so a five-figure row can easily contain
        # one head of hair. `--headwear none --hair-styles ...` forces the
        # subject, which is the same reason `--yaws` exists.
        if hair_styles:
            st = next(s for s in HK.HAIR_STYLES
                      if s[0] == hair_styles[i % len(hair_styles)])
            b.hair_style, b.hair_len, b.hair_vol = st[0], st[1], st[2]
            b.hair_part = float(st[3])
        if headwear is not None:
            wd = wd or HK.sample_wardrobe(HK.rng_for(fseed, 2), b, role=role)
            wd["headwear"] = headwear
        fig = HK.build_figure(seed=fseed, lod=tier, role=role, body=b,
                              kind=kind, wardrobe=wd,
                              archetype=tbl[i % len(tbl)],
                              covered=(role == "crew"))
        ob = HK.emit_mesh("%sFig_%02d" % (PFX, i), fig["mesh"], root, mats)
        yaw = math.radians(yaws[i % len(yaws)])
        ob.rotation_mode = "XYZ"
        ob.rotation_euler = (0.0, 0.0, yaw)
        x = BENCH_CENTRE[0] + (i - (n - 1) * 0.5) * spacing
        y = BENCH_CENTRE[1]
        ob.location = Vector((x, y, K.ground_z(x, y))) + Vector(ob.location)
        objs.append(ob)
        figs.append(fig)
        lv = fig["wardrobe"].get("livery")
        HK.log("  fig %d  %s  %d tris  flipped %d  team %s/%s  kit %s"
               % (i, fig["archetype"], fig["tris"],
                  fig["orient"]["flipped"],
                  (lv or {}).get("team"), (lv or {}).get("pattern"),
                  fig["wardrobe"].get("head_kit")))

    # ONE camera, framing the row's centre figure at the asked-for px/m.
    ppm = float(px) / 1.750
    d = K.RES_X_4K * LENS_MM / K.SENSOR_MM / ppm
    bpy.context.view_layer.update()
    mid = objs[len(objs) // 2]
    bb = [mid.matrix_world @ Vector(c) for c in mid.bound_box]
    top_z = max(float(c.z) for c in bb)
    # `hair` aims at the CROWN and looks slightly down on it from behind the
    # shoulder line. `head` frames a face, which is the wrong question for a
    # hair mass: the crown, the parting and the hairline are all above and
    # behind the eyeline and a face framing puts every one of them off frame.
    drop = {"head": 0.115, "hair": 0.045}.get(aim, 0.62)
    ctr = np.array([mid.location[0], mid.location[1], top_z - drop])
    az = math.radians(206.0 if aim != "hair" else 246.0)
    el = math.radians({"head": 2.0, "hair": 15.0}.get(aim, 7.0))
    loc = ctr + d * np.array([math.cos(el) * math.cos(az),
                              math.cos(el) * math.sin(az), math.sin(el)])
    K.macro_rig(PFX + "CAM", tuple(loc), tuple(ctr), LENS_MM, cams,
                scene=bpy.context.scene, samples=samples, want_distance_m=d)
    bpy.context.scene.camera = bpy.data.objects[PFX + "CAM"]
    HK.log("bench: %d figures, camera at %.3f m -> %.1f px/m (a 1.75 m figure "
           "reads %.0f px)" % (len(objs), d, ppm, px))
    K.assert_no_external_assets()
    return {"objects": objs, "figures": figs, "camera": PFX + "CAM",
            "px_per_m": ppm, "distance_m": d}


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    p = argparse.ArgumentParser(prog="human_bench")
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--role", default="paddock")
    # 767.2 is NOT the measured presence. `screen_presence.json`'s
    # `peak_sharp_px_4k` for the marshal/crew/paddock family is **551.8**
    # (regenerated 2026-08-03); 767.2 is a pre-shutter-fix ramped figure that
    # survived R2-037 and is 39 % high. It is kept as the DEFAULT because a
    # bench exists to find defects and a harder framing finds more of them --
    # and because every A/B in HUMAN-REFERENCE secs 0, 00 and 000 was shot at
    # it, so moving it would make this pass's frames incomparable with theirs.
    # Pass `--px 551.8` for the framing the film actually reaches.
    p.add_argument("--px", type=float, default=767.2)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--lod", default=None)
    p.add_argument("--kind", default=None)
    p.add_argument("--samples", type=int, default=256)
    p.add_argument("--archetypes", default=None)
    p.add_argument("--yaws", default=None)
    p.add_argument("--aim", default="body", choices=("body", "head", "hair"))
    p.add_argument("--headwear", default=None,
                   help="force every figure's headwear (`none` for bare heads)")
    p.add_argument("--hair-styles", default=None,
                   help="comma list from humankit.HAIR_STYLES, cycled over the "
                        "row, so a five-figure bench can hold five styles")
    # THE CLOTH LADDER. Each of these names a stage of the garment shell that
    # was superseded, or a half of the relief that can be switched off, so the
    # A/B is rendered rather than argued. See humankit.relax_spec / FOLD_GAIN.
    p.add_argument("--relax", default=None,
                   help="none|base|lowpass|cloth_v|cloth|dilate")
    p.add_argument("--roll", type=float, default=None,
                   help="override CLOTH_ROLL_M, metres")
    p.add_argument("--fold-gain", type=float, default=None,
                   help="gain on the GEOMETRY fold field; 0 turns it off")
    p.add_argument("--shader-relief", type=float, default=None,
                   help="gain on every fabric bump; 0 turns it off")
    # THE FACE LADDER -- defect 1. Same idea, one layer up: 0 on either half
    # and the four corners of the pair say which layer the face is made of.
    p.add_argument("--face-relief", type=float, default=None,
                   help="gain on HEAD_LOBES' displacement; 0 = no brow, nose, "
                        "orbit or lip GEOMETRY, skin grain kept")
    p.add_argument("--face-tint", type=float, default=None,
                   help="gain on the lip/brow/orbital COLOUR masks; 0 = the "
                        "same geometry with no face tinting at all")
    # THE HAIR LADDER -- defect 3, "a granular crust at every distance". Same
    # instrument again: three layers can own the crust and only a rendered pair
    # can say which. See humankit.HAIR_RELIEF.
    p.add_argument("--hair-relief", type=float, default=None,
                   help="gain on the hair SHADER's bumps; 0 turns them off")
    p.add_argument("--hair-lump", type=float, default=None,
                   help="gain on the hair MESH's thickness field (locks, "
                        "volume, parting); 0 leaves a smooth shell")
    p.add_argument("--hair-strands", type=float, default=None,
                   help="gain on the strand COUNT; 0 emits no strand tubes")
    p.add_argument("--hair-legacy", action="store_true",
                   help="build the SHIPPED hair -- shader, mesh and strands -- "
                        "as the positive control. See humankit.HAIR_LEGACY")
    p.add_argument("--out", default=os.path.join(_WORLD, "items",
                                                 "human_bench.blend"))
    a = p.parse_args(argv)
    lod = {"L0": HK.LOD_L0, "L1": HK.LOD_L1, "L2": HK.LOD_L2,
           "L3": HK.LOD_L3}.get(a.lod)
    if a.relax is not None:
        HK.relax_spec(a.relax)                       # refuse an unknown name
        HK.GARMENT_RELAX = a.relax
    if a.roll is not None:
        HK.CLOTH_ROLL_M = float(a.roll)
    if a.fold_gain is not None:
        HK.FOLD_GAIN = float(a.fold_gain)
    if a.shader_relief is not None:
        HK.SHADER_RELIEF = float(a.shader_relief)
    if a.face_relief is not None:
        HK.FACE_RELIEF = float(a.face_relief)
    if a.face_tint is not None:
        HK.FACE_TINT = float(a.face_tint)
    if a.hair_legacy:
        HK.HAIR_LEGACY = True
    for _flag, _name in (("hair_relief", "HAIR_RELIEF"),
                         ("hair_lump", "HAIR_LUMP"),
                         ("hair_strands", "HAIR_STRAND_GAIN")):
        _v = getattr(a, _flag)
        if _v is not None:
            setattr(HK, _name, float(_v))
    HK.log("hair ladder:  legacy=%s relief=%.2f lump=%.2f strands=%.2f"
           % (HK.HAIR_LEGACY, HK.HAIR_RELIEF, HK.HAIR_LUMP,
              HK.HAIR_STRAND_GAIN))
    HK.log("cloth ladder: relax=%s roll=%.3f m fold_gain=%.2f shader_relief=%.2f"
           % (HK.GARMENT_RELAX, HK.CLOTH_ROLL_M, HK.FOLD_GAIN,
              HK.SHADER_RELIEF))
    HK.log("face ladder:  face_relief=%.2f face_tint=%.2f"
           % (HK.FACE_RELIEF, HK.FACE_TINT))
    res = build(n=a.n, role=a.role, px=a.px, seed=a.seed, lod=lod,
                samples=a.samples, kind=a.kind, aim=a.aim,
                headwear=a.headwear,
                hair_styles=(a.hair_styles.split(",") if a.hair_styles
                             else None),
                yaws=([float(v) for v in a.yaws.split(",")] if a.yaws else None),
                archetypes=(a.archetypes.split(",") if a.archetypes else None))
    bpy.ops.wm.save_as_mainfile(filepath=a.out, compress=True)
    HK.log("saved %s  (camera %s)" % (a.out, res["camera"]))


if __name__ == "__main__":
    main()
