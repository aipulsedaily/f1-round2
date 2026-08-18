"""THE MISSING CONTROL: known-truth relief AT ITEM-LIKE PIXEL DENSITY, and MIXED.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/relief_itemlike_control.py -- --out render/relief_itemlike.blend

WHY THIS EXISTS — THE KNOWN-TRUTH POPULATION DOES NOT CONTAIN THE POPULATION
UNDER TEST
===========================================================================
R2-633 left a contradiction that the existing ladder cannot adjudicate:

  * On `render/relief_2light/truth_table_A_vs_B.json` the dip clause contributes
    almost nothing. Scored as the gate actually runs it -- dip AND
    `light_amplitude` together -- CURRENT and the proposed light-driven variant
    tie at 14/15, because `light_amplitude` is already rejecting every painted
    decoy (x0.02-1.40 against its x2.00 bar).
  * On the 28 real items the dip clause rejects 15 of 21, while
    `light_amplitude` passes every single one at x29-x427.

Those two facts cannot both describe a healthy statistic, and the ladder cannot
say which is wrong, because EVERY PANEL ON IT IS A SINGLE-MATERIAL PLATE,
CYLINDER OR SPHERE AND EVERY ITEM IS NOT. Two differences are measurable and
both are large:

  1. PIXEL DENSITY. `relief_positive_control.py` frames a 0.60 m panel with a
     50 mm lens at 0.75 m: 3840 * 50 / 36 / 0.75 = **7111 px/m**. The wave-1
     items are filmed at **170 to 2333 px/m** -- the ladder is 3x to 42x
     coarser-grained than anything it licenses a verdict about. And the bands
     the statistic reads are in PIXELS, so the physical scale they correspond to
     moves with the framing. On 11 of 30 items the r8/r16 bands could not be
     measured at all (R2-635); on the ladder they always can.
  2. MATERIAL COUNT. Every ladder panel is one material. `crew_fireproof_overall`
     has four, `driver_figure` more. A material boundary IS a sharp albedo step,
     which is the exact thing the band-pass cannot distinguish from a lip, and
     the contaminated band of R2-633 is contaminated BY those steps.

So this builds the two specimens the ladder is missing, with the truth known by
construction, and it changes NOTHING else: same sun, same world, same plate
builder, same materials, all imported from `relief_positive_control` rather than
re-implemented, because a re-implementation would test my copy of the rig
instead of the rig.

WHAT IT BUILDS
--------------
ARM 1 -- THE SAME LADDER, RE-FRAMED. The existing `a_flat / c_rib_2mm /
d_rib_8mm / f_printed / g_printed_aligned` panels, each given four cameras at
**7111, 2000, 600 and 250 px/m**. Nothing about the geometry changes. If the
statistic's verdicts move with framing alone, the item failures are an artefact
of distance and not a property of the items, and that is decidable from this arm
by itself.

ARM 2 -- MULTI-MATERIAL, INCLUDING THE MIXED CASE:

    p_multi_relief   4 materials, ALL bands real 2 mm ribs        truth relief
    q_multi_paint    4 materials, ALL bands painted, zero height  truth paint
    r_multi_mixed    2 bands real 2 mm ribs, 2 bands painted      truth MIXED

`r_multi_mixed` is the specimen the whole R2-633 argument turns on. The
contaminated band mixes a light-driven half with a still half; on a real item
those two halves come from DIFFERENT MATERIALS on the same body. No panel on the
existing ladder does that, so no existing measurement says what the statistic
reports when they are mixed in known proportion. Here the proportion is 50/50
and built.

HOW IT IS MEASURED
------------------
Not by this file. It emits a blend with named cameras and a JSON manifest of
(camera, panel, truth, px_per_m); the frames are rendered with `rq render
--scene relief_itemlike.blend --cam <name>` on both sun sides, and measured by
the SAME `two_light_bands` / `relief_anisotropy` out of `tools/item_gate.py`
that `relief_control_measure.py` already imports. One instrument throughout.

NO EXEC BUNDLE. The build is procedural, local and takes seconds; only the
render leaves the box. That also keeps this clear of the `StaleBundle` failure
that is killing 96-file bundles drawn from directories eight agents are editing.
"""

import argparse
import importlib.util
import json
import math
import os
import sys

import bpy
from mathutils import Vector

R2 = os.path.expanduser("~/f1-round2")
for _p in (os.path.join(R2, "world"), os.path.join(R2, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Import the shipped ladder builder BY PATH and reuse its plate, its materials,
# its sun and its constants. Not a copy: a copy would drift, and the whole point
# is that this specimen is comparable to the one already measured.
_spec = importlib.util.spec_from_file_location(
    "relief_positive_control", os.path.join(R2, "tools/relief_positive_control.py"))
RPC = importlib.util.module_from_spec(_spec)
_sv = sys.argv
sys.argv = ["blender"]                      # its parse_args runs at import time
try:
    _spec.loader.exec_module(RPC)
finally:
    sys.argv = _sv

SENSOR_MM = 36.0
LENS_MM = 50.0
RES_X = 3840

#: The densities that matter. 7111 is the shipped ladder's own framing; the
#: other three bracket the wave-1 items' measured 170-2333 px/m.
PX_PER_M = (7111, 2000, 600, 250)

#: R2-1286 (W2-R). 170-2333 px/m is the density the items were GATED at, not the
#: density the CAMERA gives them. Re-derived from `docs/screen_presence.json`
#: (`measured.peak_unocc_sharp_px_4k`, the largest the camera ever sees the item
#: sharp and unoccluded across all 2,978 frames) the 32 built modules run
#: **3.7 to 534 px/m**: the entire population sits at or below this ladder's
#: LOWEST rung, and 27 of 32 sit below it by 2x to 336x.
#:
#: So a null from the relief check at measured framing is not yet interpretable.
#: Nothing has ever established that the check can find relief that IS there at
#: 15-120 px/m, and "the relief is too fine for the camera" and "the check
#: stops working down here" produce the same number. `--px-per-m` exists to
#: tell them apart. It is purely ADDITIVE: omit it and the four shipped rungs
#: are unchanged, which is what every existing result was measured against.

#: 2 mm ribs are the ladder's mid rung and the one both statistics agree on at
#: 7111 px/m, so it is the cleanest rung to carry down the density ladder.
RIB_H_M = 0.002


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=os.path.join(R2, "render/relief_itemlike.blend"))
    p.add_argument("--manifest",
                   default=os.path.join(R2, "work/relief_itemlike/manifest.json"))
    p.add_argument("--sun-bearing", type=float, default=None,
                   help="override the contract sun's bearing. The two-light "
                        "measurement needs the SAME panels under the chosen sun "
                        "and its runner-up; -58 is the contract, +58 the flip.")
    p.add_argument("--px-per-m", type=float, nargs="+", default=None,
                   help="R2-1286. Densities to build cameras for, replacing the "
                        "four shipped rungs. The items this ladder licenses "
                        "verdicts about are filmed at 3.7-534 px/m, below its "
                        "lowest rung of 250. Recorded in the manifest so no "
                        "reader has to infer which rungs a result came from.")
    return p.parse_args(argv)


def cam_distance_for(px_per_m):
    """Distance that puts a metre of panel across `px_per_m` pixels."""
    return (RES_X * LENS_MM / SENSOR_MM) / float(px_per_m)


def _clip_to_band(ob, xc, lo, hi):
    """Delete every face of `ob` whose centre is outside [xc+lo, xc+hi] in x.

    CLIPPED, NOT SCALED, AND THAT IS NOT A DETAIL. The first version of this
    built one plate per band and set `ob.scale = (0.25, 1, 1)`. `RPC.plate` lays
    its ribs PERPENDICULAR TO THE SUN'S GROUND DIRECTION and repeats them along
    it -- see its docstring, which records getting the axis wrong once already --
    so a 0.25 scale in x compresses the 30 mm rib pitch to 7.5 mm AND swings the
    rib axis off the sun. Every arm-2 measurement would have been taken on ribs
    of the wrong pitch at the wrong angle, and it would have looked fine.
    Clipping removes geometry and moves none, so pitch, axis and height are the
    shipped ladder's exactly.
    """
    import bmesh
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    doomed = [f for f in bm.faces
              if not (lo <= f.calc_center_median().x <= hi)]
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    bm.to_mesh(me)
    bm.free()
    me.update()
    return len(me.polygons)


def multi_plate(name, x0, bands):
    """A 0.60 m plate whose four spanwise quarters carry DIFFERENT materials.

    `bands` is four (material, height_m) pairs. One FULL plate is built per
    distinct height in the set and then clipped to the quarters that want that
    height, so the ribs keep the shipped pitch, axis and profile and the only
    new things are the material boundaries -- which are the point. A material
    boundary is the sharp albedo step the band-pass cannot tell from a lip, and
    `r_multi_mixed` exists to measure what happens when half the bands have a
    real lip and half only have the step.
    """
    made = []
    sub = RPC.PANEL_M / 4.0
    for i, (mat, h) in enumerate(bands):
        lo = -RPC.PANEL_M * 0.5 + i * sub
        hi = lo + sub
        ob = RPC.plate("%s_q%d" % (name, i), x0, h, mat, chamfer_bolts=False)
        # plate() emits at x0 in WORLD x with local coords centred on 0
        n = _clip_to_band(ob, x0, lo, hi)
        if n == 0:
            raise SystemExit("%s_q%d clipped to nothing (band %.3f..%.3f)"
                             % (name, i, lo, hi))
        made.append(ob)
    return made


def main():
    a = parse_args()
    # R2-1286. Bound once, here, so every later use -- the cameras, the
    # manifest and the printed summary -- reads the SAME list. A flag that
    # changes the cameras but not the manifest is how a result stops knowing
    # what it was measured at.
    global PX_PER_M
    if a.px_per_m:
        PX_PER_M = tuple(a.px_per_m)
    RPC.clear()
    scn = bpy.context.scene
    if a.sun_bearing is not None:
        RPC.SUN_BEARING_DEG = float(a.sun_bearing)

    # ---- materials: four visually distinct greys, plus their painted twins --
    rel_mats, pnt_mats = [], []
    for i, alb in enumerate((0.10, 0.18, 0.26, 0.34)):
        rel_mats.append(RPC.grey_material("IL_Grey_%d" % i, base=alb, rough=0.55))
        pnt_mats.append(RPC.printed_material("IL_Printed_%d" % i, base=alb,
                                             mark=max(alb * 0.5, 0.04)))

    base = RPC.grey_material("IL_Base", base=0.18)
    decoy = RPC.printed_material("IL_Decoy", base=0.18, mark=0.09)

    # PANEL SEPARATION IS SET BY THE WIDEST FRAMING, NOT BY TIDINESS.
    # The shipped ladder abuts its panels at PANEL_M + GAP_M = 0.66 m because it
    # is only ever framed at 0.75 m, where a 50 mm lens sees 0.54 m. At the
    # item-like end of this experiment the camera stands 21.33 m back and sees
    # 3840/250 = 15.4 m -- the whole shipped ladder and then some. Every
    # measurement at 250 and 600 px/m would have had four other panels, three
    # other truths and six extra material boundaries inside the subject frame,
    # which is precisely the contamination this specimen exists to isolate.
    # 20 m of separation puts one panel and nothing else in every frame at every
    # density. The plates are independent; spacing changes nothing about the
    # relief on any of them.
    step = max(RPC.PANEL_M + RPC.GAP_M, 20.0)
    panels = []          # (panel_name, truth, builder)

    # ARM 1 -- the shipped ladder's rungs, unchanged, to be re-framed
    arm1 = [("a_flat_0mm", "smooth", 0.000, base, False),
            ("c_rib_2mm", "relief", RIB_H_M, base, False),
            ("d_rib_8mm", "relief", 0.008, base, False),
            ("f_printed_0mm", "paint", 0.000, decoy, False)]
    # ARM 2 -- multi-material, including the mixed case
    arm2 = [("p_multi_relief", "relief",
             [(rel_mats[i], RIB_H_M) for i in range(4)]),
            ("q_multi_paint", "paint",
             [(pnt_mats[i], 0.000) for i in range(4)]),
            ("r_multi_mixed", "mixed",
             [(rel_mats[0], RIB_H_M), (pnt_mats[1], 0.000),
              (rel_mats[2], RIB_H_M), (pnt_mats[3], 0.000)])]

    n = len(arm1) + len(arm2)
    x0 = -step * (n - 1) * 0.5
    idx = 0
    for nm, truth, h, mat, bolts in arm1:
        RPC.plate("IL_" + nm, x0 + idx * step, h, mat, chamfer_bolts=bolts)
        panels.append((nm, truth, x0 + idx * step)); idx += 1
    for nm, truth, bands in arm2:
        multi_plate("IL_" + nm, x0 + idx * step, bands)
        panels.append((nm, truth, x0 + idx * step)); idx += 1

    # ---- the contract sun and world, verbatim from the shipped rig ---------
    el = math.radians(RPC.SUN_ELEV_DEG)
    az = math.radians(RPC.SUN_BEARING_DEG)
    d = Vector((math.cos(el) * math.sin(az), -math.cos(el) * math.cos(az),
                math.sin(el)))
    sd = bpy.data.lights.new("IL_Sun", type="SUN")
    sd.energy = 115.754                      # build_sky's published irradiance
    sd.angle = math.radians(0.545)
    sun = bpy.data.objects.new("IL_Sun", sd)
    # `d` points TOWARD the sun; to_track_quat('Z','Y') aligns local +Z with it,
    # which for a sun lamp emitting along -Z gives downward light. Passing -d
    # here lit the shipped ladder from the sky and was misread as a broken
    # CHECK -- see relief_positive_control's note.
    sun.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    scn.collection.objects.link(sun)

    w = bpy.data.worlds.new("IL_World")
    w.use_nodes = True
    scn.world = w
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.30, 0.42, 0.62, 1.0)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

    # ---- one camera per (panel, density) ----------------------------------
    rows = []
    for nm, truth, cx in panels:
        for ppm in PX_PER_M:
            dist = cam_distance_for(ppm)
            cname = "CAM_%s_%d" % (nm, ppm)
            cd = bpy.data.cameras.new(cname)
            cd.lens = LENS_MM
            cd.sensor_width = SENSOR_MM
            cd.clip_start, cd.clip_end = 0.01, 500.0
            cam = bpy.data.objects.new(cname, cd)
            # same oblique the shipped rig uses, scaled out along its own axis
            # so the sun rakes the ribs at an identical angle at every density
            u = Vector((0.0, -0.42, 0.62)).normalized()
            cam.location = Vector((cx, 0.0, 0.0)) + u * dist
            cam.rotation_euler = (Vector((cx, 0.0, 0.0)) - cam.location) \
                .to_track_quat("-Z", "Y").to_euler()
            scn.collection.objects.link(cam)
            rows.append({"camera": cname, "panel": nm, "truth": truth,
                         "px_per_m": ppm, "distance_m": round(dist, 4),
                         "lens_mm": LENS_MM,
                         "mm_per_px": round(1000.0 / ppm, 4)})

    scn.render.resolution_x, scn.render.resolution_y = RES_X, 2160
    scn.render.engine = "CYCLES"
    scn.view_settings.view_transform = "Standard"   # the gate measures Standard
    scn.view_settings.look = "None"
    scn.view_settings.exposure = 0.0

    outp = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=outp, compress=False)

    man = {"blend": outp, "sun_elev_deg": RPC.SUN_ELEV_DEG,
           "panel_separation_m": step,
           "sun_bearing_deg": RPC.SUN_BEARING_DEG,
           "panel_m": RPC.PANEL_M, "rib_pitch_m": RPC.RIB_PITCH_M,
           "res_x": RES_X, "lens_mm": LENS_MM, "sensor_mm": SENSOR_MM,
           "densities_px_per_m": list(PX_PER_M),
           "WHY": "R2-636. The known-truth ladder was framed at 7111 px/m and "
                  "every panel was one material; the items it licenses verdicts "
                  "about run 170-2333 px/m and are multi-material. These "
                  "specimens close both gaps and `r_multi_mixed` is the 50/50 "
                  "relief-and-paint case the contaminated band of R2-633 mixes.",
           "cameras": rows}
    os.makedirs(os.path.dirname(os.path.abspath(a.manifest)), exist_ok=True)
    json.dump(man, open(a.manifest, "w"), indent=1)

    print(">> %d panels x %d densities = %d cameras" % (len(panels), len(PX_PER_M), len(rows)))
    for nm, truth, _cx in panels:
        print("   %-18s truth=%s" % (nm, truth))
    print(">> distances: " + ", ".join("%d px/m -> %.2f m" % (p, cam_distance_for(p))
                                       for p in PX_PER_M))
    print(">> saved %s  %.1f MB" % (outp, os.path.getsize(outp) / 1048576.0))
    print(">> manifest %s" % a.manifest)
    print(">> STAGE RESULT: RELIEF_ITEMLIKE_BUILT")


if __name__ == "__main__":
    main()
