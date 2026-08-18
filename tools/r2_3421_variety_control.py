"""R2-3421 -- WHAT DOES A REPEATED ASSET ACTUALLY LOOK LIKE ON THIS GROUND?

    # 1. build the probe once (nlib forced to the SHIPPING 11, not the probe's 9)
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -noaudio \
        -P tools/r2_3421_variety_control.py -- --build work/r23421/probe.blend

    # 2. render the ladder, one mode per invocation
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -noaudio \
        -P tools/r2_3421_variety_control.py -- \
        --load work/r23421/probe.blend --mode top100 --out work/r23421/top100.png

WHY
---
The red line is "no repeated assets -- one tree spammed 100 times is the named
failure", and it is policed by a single number: the share of all realized
instances taken by the commonest source mesh.  On `assembly14` that number is
2.03 %, over a 2.00 % ceiling that was derived against a 311-source population
when the shipping world has 1,569.

A share cannot answer a perceptual rule, and nobody on this project has ever
looked at what a repeated asset looks like HERE.  So this builds the ladder:

    ship        as built -- 11 hero meshes per grass kind, so the commonest
                fescue mesh is 1/11 = 9.09 % of fescue-hero and 2.03 % of VEG
    top20       the commonest fescue mesh forced to 20 % of fescue-hero
    top100      the commonest fescue mesh forced to 100 % -- ONE mesh, the
                literal named failure, at the exact same 183 k positions
    allgrass100 every grass kind AND tier collapsed to one mesh each
    stamp       allgrass100 AND the per-instance yaw, mirror and anisotropic
                scale removed -- the true stamp

EVERY MODE RENDERS THE SAME POSITIONS.  `gn_kind` writes `inst_idx`, `inst_rot`
and `inst_scl` as named attributes on the emitter point mesh and Geometry Nodes
reads them back; the collapse rewrites `inst_idx` ONLY (except `stamp`, which is
the point).  So placement, density, scale, lighting, camera and seed are held
and the ONLY difference between two frames in the ladder is how many distinct
meshes the picks land on.  A ladder that also moved the points would be
evidence about the points.

`stamp` is the control on the control.  If `top100` looks like `ship` but
`stamp` reads as obviously repetitive, then what defeats repetition here is the
per-instance randomisation, NOT the size of the library -- and top-share, which
cannot see randomisation at all, is measuring the wrong thing.

THE CAMERA IS f2319'S, NOT A CONVENIENT ONE
-------------------------------------------
f2319 is the frame where `VEG_grass_fescue_H` is simultaneously largest and
sharpest anywhere in the delivery: 448 px/m at 4K, 8.6 px of median shutter
smear, nearest clump 16.7 m.  Measured off `world/camera_rig_path.json`:
lens 69.95 mm, eye 3.26 m above the local ground, optical axis 2.99 deg below
horizontal.  Those four numbers are reproduced here rather than approximated,
and the render is a 960x540 CROP OF A 3840x2160 frame, so px/m is the
delivery's, not a proxy's.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
import bpy
from mathutils import Vector

R2 = os.path.expanduser("~/f1-round2")
_HERE = os.path.dirname(os.path.abspath(__file__))
for p in (_HERE, os.path.join(R2, "world")):
    if p not in sys.path:
        sys.path.insert(0, p)
import gate_exit                                                   # noqa: E402

# ---- CONSTANTS, IMPORTED, NEVER RETYPED -------------------------------------
# The delivery's frame size and sensor come from tools/screen_presence.py, which
# is what measured every px/m number this block quotes.
from screen_presence import RES_X, RES_Y, SENSOR_MM                # noqa: E402

# THE SHIPPING GRASS LIBRARY.  `render/world/assembly/r2/assembly14_build.json`
# records grass_library = 55 over the five kinds in build_terrain.GRASS, i.e.
# nlib = 11 hero meshes per kind.  macro_probe() hardcodes max(3, 9*q) = 9,
# which would make the probe's top source 1/9 = 11.1 % instead of the ship's
# 1/11 = 9.09 % and quietly bias the whole ladder.  Read, not assumed.
_BUILD_JSON = os.path.join(R2, "render/world/assembly/r2/assembly14_build.json")

# f2319, measured off world/camera_rig_path.json by this block. See the docstring.
CAM_LENS_MM = 69.9468
CAM_EYE_M = 3.26
CAM_PITCH_DEG = 2.9883
CAM_STATION_S = 2560.0          # SVIEWS["doppler_v"]'s station: verge both sides
CAM_STATION_U = -14.0

# the crop: 960 x 540 of the 3840 x 2160 frame, bottom-centre, which is where
# the near-field verge lands (measured: proxy y 362..538, i.e. 4K y 1449..2153)
CROP_X0, CROP_X1 = 0.375, 0.625
CROP_Y0, CROP_Y1 = 0.000, 0.250

MODES = ("ship", "top20", "top100", "allgrass100", "stamp")


def _shipping_nlib():
    """nlib from the shipping build record, not from the probe's own default.

    `grass_library` is nested under mods/terrain/summary, and the first draft of
    this function looked for it at the top level, found nothing and exited 1.
    That failure was loud and cost four minutes; a version that had DEFAULTED to
    the probe's own 9 would have biased every frame in the ladder silently, so
    the search is exhaustive and its absence is still fatal.
    """
    import build_terrain as BT
    d = json.load(open(_BUILD_JSON))
    found = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "grass_library" and isinstance(v, int):
                    found.append(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(d)
    if not found:
        raise SystemExit("no grass_library anywhere in " + _BUILD_JSON)
    if len(set(found)) != 1:
        raise SystemExit("grass_library disagrees with itself in %s: %r"
                         % (_BUILD_JSON, found))
    v, n_kinds = found[0], len(BT.GRASS)
    if v % n_kinds:
        raise SystemExit("grass_library %d is not a multiple of the %d kinds "
                         "in build_terrain.GRASS" % (v, n_kinds))
    return v // n_kinds


# =============================================================================
# BUILD
# =============================================================================
def do_build(out):
    import build_terrain as BT

    nlib = _shipping_nlib()
    print("[R2-3421] shipping nlib = %d hero meshes per grass kind "
          "(top source = 1/%d = %.2f %% of its kind)" % (nlib, nlib, 100.0 / nlib))

    # force the probe's library to the ship's, without editing build_terrain
    _orig = BT.build_grass

    def _build_grass(*a, **k):
        k["nlib"] = nlib
        return _orig(*a, **k)
    BT.build_grass = _build_grass

    # f2319's camera, expressed as a station view so it lands on the contract's
    # own datum whatever the widths do.  The optical axis meets the ground at
    # eye / tan(pitch) metres; that is the look point.
    reach = CAM_EYE_M / math.tan(math.radians(CAM_PITCH_DEG))
    BT.SVIEWS["r2_3421_f2319"] = (CAM_STATION_S, CAM_STATION_U, CAM_EYE_M,
                                  CAM_STATION_S + reach, CAM_STATION_U, 0.0,
                                  CAM_LENS_MM)
    print("[R2-3421] control camera: lens %.2f mm, eye %.2f m, pitch %.3f deg, "
          "axis meets ground at %.1f m" % (CAM_LENS_MM, CAM_EYE_M,
                                           CAM_PITCH_DEG, reach))

    stats = BT.macro_probe(view="r2_3421_f2319", half=60.0)
    BT.bake_cameras(["r2_3421_f2319"])

    # WHAT THE PROBE ACTUALLY BUILT, per emitter -- the ladder's own baseline.
    stats["emitters"] = _emitter_census()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print("[R2-3421] wrote %s" % out)
    print(json.dumps(stats, indent=1))
    return stats


def _emitter_census():
    """Every gn_kind emitter: points, library size, and the pick histogram."""
    rows = []
    for ob in bpy.data.objects:
        a = ob.data.attributes.get("inst_idx") if ob.type == "MESH" else None
        if a is None:
            continue
        n = len(ob.data.vertices)
        idx = np.empty(n, np.int32)
        a.data.foreach_get("value", idx)
        lib = _lib_of(ob)
        h = np.bincount(idx, minlength=(len(lib.objects) if lib else idx.max() + 1))
        rows.append({"emitter": ob.name, "points": int(n),
                     "library": int(len(lib.objects)) if lib else None,
                     "top_share": round(float(h.max()) / max(1, n), 4),
                     "hist": [int(v) for v in h]})
    rows.sort(key=lambda r: -r["points"])
    return rows


def _lib_of(ob):
    """The Collection Info collection the emitter's node group picks from."""
    for m in ob.modifiers:
        ng = getattr(m, "node_group", None)
        if ng is None:
            continue
        for nd in ng.nodes:
            if nd.bl_idname == "GeometryNodeCollectionInfo":
                return nd.inputs[0].default_value
    return None


# =============================================================================
# THE COLLAPSE
# =============================================================================
def _emitters(pattern):
    out = []
    for ob in bpy.data.objects:
        if ob.type != "MESH" or not ob.name.startswith(pattern):
            continue
        if ob.data.attributes.get("inst_idx") is not None:
            out.append(ob)
    return out


def _collapse(ob, share, rng):
    """Force the commonest source of ONE emitter to `share` of its picks.

    Returns (top_slot, achieved_share, library_size).  Positions, rotations and
    scales are untouched: only which library slot each point picks changes.
    """
    me = ob.data
    n = len(me.vertices)
    a = me.attributes["inst_idx"]
    idx = np.empty(n, np.int32)
    a.data.foreach_get("value", idx)
    lib = _lib_of(ob)
    L = len(lib.objects) if lib else int(idx.max()) + 1
    top = int(np.bincount(idx, minlength=L).argmax())
    if L < 2:
        return top, 1.0, L
    hit = rng.random(n) < share
    other = np.array([j for j in range(L) if j != top], np.int32)
    new = np.where(hit, top, other[rng.integers(0, len(other), n)]).astype(np.int32)
    a.data.foreach_set("value", new)
    me.update()
    return top, float((new == top).mean()), L


def _destroy_randomisation(ob):
    """Remove the per-instance yaw, the mirror and the anisotropic scale.

    This is what makes a stamp a stamp.  Yaw goes to a constant, the two lean
    angles go to their means, and every instance takes the MEAN scale of the
    emitter -- so the size drift that hides a repeat is gone too, but the
    clump heights are still the emitter's own, not invented.
    """
    me = ob.data
    n = len(me.vertices)
    for nm, k in (("inst_rot", 3), ("inst_scl", 3)):
        at = me.attributes.get(nm)
        if at is None:
            continue
        v = np.empty(n * k, np.float32)
        at.data.foreach_get("vector", v)
        v = v.reshape(n, k)
        if nm == "inst_rot":
            v[:] = v.mean(0)                      # one yaw, one lean, for all
        else:
            m = np.abs(v).mean(0)                 # kills the +-x mirror as well
            v[:] = m
        at.data.foreach_set("vector", v.ravel())
    me.update()


def do_collapse(mode, seed=20263421):
    rng = np.random.default_rng(seed)
    report = {"mode": mode, "emitters": []}
    if mode == "ship":
        pass
    elif mode in ("top20", "top100"):
        share = 0.20 if mode == "top20" else 1.0
        for ob in _emitters("VEG_grass_fescue_H"):
            t, got, L = _collapse(ob, share, rng)
            report["emitters"].append({"emitter": ob.name, "library": L,
                                       "top_slot": t, "top_share": round(got, 4)})
    elif mode in ("allgrass100", "stamp"):
        for ob in _emitters("VEG_grass_"):
            t, got, L = _collapse(ob, 1.0, rng)
            if mode == "stamp":
                _destroy_randomisation(ob)
            report["emitters"].append({"emitter": ob.name, "library": L,
                                       "top_slot": t, "top_share": round(got, 4)})
    else:
        raise SystemExit("unknown mode " + mode)
    if mode != "ship" and not report["emitters"]:
        # A collapse that collapsed nothing renders a picture of the ship and
        # calls it a control. That is the vacuous pass this project keeps
        # finding, so it is a refusal, not a render.
        print(">> REFUSING: mode %s matched NO emitter with an inst_idx "
              "attribute, so the control is identical to the ship." % mode)
        gate_exit.done("VARIETY_CONTROL_VACUOUS")
    for e in report["emitters"]:
        print("[R2-3421] %-28s library %2d  top slot %2d -> %.1f %% of picks"
              % (e["emitter"], e["library"], e["top_slot"], e["top_share"] * 100))
    return report


# =============================================================================
# RENDER
# =============================================================================
def do_render(out, samples, mode_report):
    sc = bpy.context.scene
    cam = bpy.data.objects.get("CAM_r2_3421_f2319")
    if cam is None:
        raise SystemExit("no CAM_r2_3421_f2319 in the blend; rebuild with --build")
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = RES_X, RES_Y
    sc.render.resolution_percentage = 100
    sc.render.use_border = True
    sc.render.use_crop_to_border = True
    sc.render.border_min_x, sc.render.border_max_x = CROP_X0, CROP_X1
    sc.render.border_min_y, sc.render.border_max_y = CROP_Y0, CROP_Y1
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.device = 'CPU'                     # the 1070 is not visible to nvml
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '8'
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sc.render.filepath = out
    print("[R2-3421] rendering %d x %d crop of a %d x %d frame, %d samples, CPU"
          % (int((CROP_X1 - CROP_X0) * RES_X), int((CROP_Y1 - CROP_Y0) * RES_Y),
             RES_X, RES_Y, samples))
    bpy.ops.render.render(write_still=True)
    print("[R2-3421] wrote %s" % out)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--build")
    ap.add_argument("--load")
    ap.add_argument("--mode", choices=MODES, default="ship")
    ap.add_argument("--out")
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--report")
    a = ap.parse_args(argv)

    if a.build:
        do_build(a.build)
        return gate_exit.verdict("VARIETY_CONTROL_BUILT")

    if not a.load or not a.out:
        raise SystemExit("--load and --out are required without --build")
    bpy.ops.wm.open_mainfile(filepath=a.load)
    rep = do_collapse(a.mode)
    do_render(a.out, a.samples, rep)
    rep["out"] = a.out
    rep["samples"] = a.samples
    if a.report:
        json.dump(rep, open(a.report, "w"), indent=1)
    return gate_exit.verdict("VARIETY_CONTROL_RENDER_OK")


if __name__ == "__main__":
    gate_exit.guard(main)
