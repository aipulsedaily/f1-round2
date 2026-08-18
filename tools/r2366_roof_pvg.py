#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2-375.  IS THE SHOWROOM ROOF'S RELIEF CARRIED BY GEOMETRY OR BY PAINT?

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/r2366_roof_pvg.py -- --arm after --out work/r2366/pvg/after.blend

THE TRAP THIS ANSWERS  (defect R2-060, already paid for)
========================================================
A flat 4-vertex quad with z identically 0, painted with 30 mm stripes ALIGNED
to the light, scored dip 0.6308 against 0.6082 for REAL 2 mm trapezoidal ribs.
After a band-pass a sharp albedo STEP and a lip-and-shadow leave the same
signature. So passing a relief check is not the same as passing it for the
right reason, and a roof whose "detail" is a painted mottle would pass exactly
as a roof whose detail is a parapet and 36 plant units.

THE METHOD IS `tools/relief_paint_vs_geometry.py`'s, unchanged: not a better
statistic -- a statistic that cannot separate the two here could not separate
them there either -- but the SAME statistic re-run on the SAME camera, the SAME
sun and the SAME PIXEL MASK, with the scene taken apart:

    before      the shipped flat slab, `CeilingMat` untouched
    before_geo  the same slab with its paint forced constant
    after       the built roof
    after_geo   every paint input on every RRF_ material forced constant
                (base colour, roughness, metallic, specular, emission, alpha);
                mesh, bump and normal untouched.  GEOMETRY + BUMP ONLY.
    after_geonb `after_geo` with the Normal input unlinked too.  MESH ONLY.
    after_truegeo  every roof surface emits max(0, TrueNormal . sun).  Lambert
                off the EVALUATED MESH, ignoring every bump node and normal
                map. MESH ONLY, answered by the model rather than the picture.
    after_paint every roof surface replaced by an Emission of its own base
                colour. No sun, no shadow, no normal, no bump.  PAINT ONLY.
    after_null  `after` again, so the arm differences have a floor

    THE GEOMETRY ARM DECIDES. dip(after_geo) carrying the number means the
    relief is real; dip collapsing to the flat-plate floor while dip(after_paint)
    carries it means it is paint.

WHY A REDUCED SCENE
-------------------
The arms differ by MATERIAL SURGERY, so each arm is a different file. Eight
copies of a 5 GB film blend is 40 GB of upload for a question that is entirely
local to the roof: the subject, its own shadow, the slab it sits on and the sun.
So this builds the subject from `r2366_roof_build`'s OWN builder -- one
definition of the geometry, not a second description of it -- on the round-1
datum, under `itemkit.contract_sun`, at the film's exact f2978 ONER pose read
out of `world/camera_rig_path.json`, with `film_exposure.apply`.

That makes the arms comparable to EACH OTHER, which is the whole question. It
does NOT make them comparable to the delivered frame, and this tool never
claims it does: the delivered frame's A/B is `tools/r2366_roof_ab.py`, on the
film blend itself.

Blender 5.2 exits 0 on an uncaught exception. Judge on `STAGE RESULT`.
"""

import argparse
import json
import math
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "tools"), os.path.join(R2, "world")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bpy                                                       # noqa: E402
import gate_exit                                                 # noqa: E402
import itemkit as K                                              # noqa: E402
import world_contract as C                                       # noqa: E402
import film_exposure as FX                                       # noqa: E402
import r2366_roof_build as RB                                    # noqa: E402

FRAME = 2978
CAM = "ONER"

ARMS = ("before", "before_geo", "before_geonb", "before_truegeo",
        "before_paint",
        "after", "after_geo", "after_geonb", "after_truegeo", "after_paint",
        "after_null")

# Everything on a Principled BSDF that is PAINT rather than SHAPE. `Normal` and
# `Tangent` are deliberately absent: they carry bump and normal maps, which are
# relief the check is entitled to credit. Lifted from
# relief_paint_vs_geometry.PAINT_SOCKETS so the two tools cannot drift.
PAINT_SOCKETS = {
    "Base Color": (0.18, 0.18, 0.18, 1.0),
    "Roughness": 0.5,
    "Metallic": 0.0,
    "Specular IOR Level": 0.5,
    "Specular Tint": (1.0, 1.0, 1.0, 1.0),
    "Emission Color": (0.0, 0.0, 0.0, 1.0),
    "Emission Strength": 0.0,
    "Alpha": 1.0,
    "Transmission Weight": 0.0,
    "Coat Weight": 0.0,
    "Sheen Weight": 0.0,
    "Subsurface Weight": 0.0,
    "Anisotropic": 0.0,
}


# ---------------------------------------------------------------------------
# the set
# ---------------------------------------------------------------------------
def cam_pose():
    p = json.load(open(os.path.join(R2, "world", "camera_rig_path.json")))["path"]
    e = [r for r in p if r["f"] == FRAME]
    if not e:
        raise SystemExit("REFUSING: frame %d is not in camera_rig_path.json"
                         % FRAME)
    return e[0]


def build_set(with_roof):
    """The round-1 datum, rebuilt exactly, plus (optionally) the roof."""
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    sc = bpy.context.scene

    # ground
    g = K.NT("PVG_Ground")
    g.principled_out(base_color=(0.118, 0.112, 0.098), roughness=0.85,
                     metallic=0.0)
    me, off = K.new_mesh("PVG_Ground", np.array(
        [(-400, -400, 0), (400, -400, 0), (400, 400, 0), (-400, 400, 0)]),
        quads=np.array([(0, 1, 2, 3)]), smooth_deg=None, orient=False)
    me.materials.append(g.m)
    ob = bpy.data.objects.new("PVG_Ground", me)
    ob.location = off
    sc.collection.objects.link(ob)

    # the shell below the slab, so the roof sits on a building and not in air
    w = K.NT("PVG_Wall")
    w.principled_out(base_color=(0.152, 0.150, 0.146), roughness=0.66,
                     metallic=0.0)
    V = np.array([(-15.25, -11.25, 0.0), (15.25, -11.25, 0.0),
                  (15.25, 11.25, 0.0), (-15.25, 11.25, 0.0),
                  (-15.25, -11.25, 6.2), (15.25, -11.25, 6.2),
                  (15.25, 11.25, 6.2), (-15.25, 11.25, 6.2)])
    Q = np.array([(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2),
                  (2, 6, 7, 3), (3, 7, 4, 0)])
    me, off = K.new_mesh("PVG_Shell", V, quads=Q, smooth_deg=None)
    me.materials.append(w.m)
    ob = bpy.data.objects.new("PVG_Shell", me)
    ob.location = off
    sc.collection.objects.link(ob)

    # THE DATUM ITSELF, cut to the same numbers `assert_datum` checks, so the
    # roof builder runs against the same set it runs against in the film.
    cm = K.NT("CeilingMat")
    cm.principled_out(base_color=(0.075, 0.076, 0.080), metallic=0.0,
                      roughness=0.78)
    V = np.array([(-15.25, -11.25, 6.2), (15.25, -11.25, 6.2),
                  (15.25, 11.25, 6.2), (-15.25, 11.25, 6.2),
                  (-15.25, -11.25, 6.5), (15.25, -11.25, 6.5),
                  (15.25, 11.25, 6.5), (-15.25, 11.25, 6.5)])
    me = bpy.data.meshes.new("Ceiling")
    me.from_pydata([tuple(v) for v in V], [], [tuple(q) for q in Q])
    me.update()
    me.materials.append(cm.m)
    ob = bpy.data.objects.new("Ceiling", me)
    sc.collection.objects.link(ob)

    got, why = RB.assert_datum()
    if why:
        raise SystemExit(why)

    if with_roof:
        RB.build(sc)
    bpy.context.view_layer.update()
    return got


def add_sun_and_camera(flip=False):
    sc = bpy.context.scene
    lamp = K.contract_sun("PVG_", scene=sc, sky=True)
    if flip:
        # THE R2-060 SEPARATOR, FROM THE OTHER SIDE. A lip and its shadow swap
        # ends when the sun crosses the surface; a painted step does not move at
        # all. The sun is mirrored in BOTH horizontal components -- the azimuth
        # is turned through 180 deg -- keeping the elevation, the energy, the
        # colour and the disc size identical, so anything that changes between
        # the two frames is light and not paint.
        from mathutils import Vector
        d = Vector((-C.SUN_DIR[0], -C.SUN_DIR[1], C.SUN_DIR[2])).normalized()
        lamp.rotation_mode = "QUATERNION"
        lamp.rotation_quaternion = d.to_track_quat("Z", "Y")
        lamp.location = (d.x * 2000.0, d.y * 2000.0, d.z * 2000.0)
        emit = (lamp.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0)))
        if emit.z > -0.05:
            # R2-021: a sun pointing at the sky, twice in one session.
            raise RuntimeError("REFUSING: flipped sun emits toward z %+.4f"
                               % emit.z)
        sk = [n for n in sc.world.node_tree.nodes
              if n.bl_idname == "ShaderNodeTexSky"]
        for n in sk:      # and the SKY has to move with it, or the two frames
            if hasattr(n, "sun_rotation"):     # differ by more than the sun
                n.sun_rotation = math.radians(C.SKY_SUN_ROTATION_DEG + 180.0)

    e = cam_pose()
    cd = bpy.data.cameras.new(CAM)
    cd.lens = float(e["lens"])
    cd.sensor_width = 36.0
    cd.sensor_fit = 'AUTO'
    cd.clip_start, cd.clip_end = 0.1, 20000.0
    cd.dof.use_dof = True
    cd.dof.focus_distance = 595.366
    cd.dof.aperture_fstop = 5.6
    ob = bpy.data.objects.new(CAM, cd)
    ob.location = tuple(e["p"])
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = tuple(e["q"])
    bpy.context.scene.collection.objects.link(ob)
    sc.camera = ob
    sc.render.resolution_x, sc.render.resolution_y = 3840, 2160
    sc.render.resolution_percentage = 100
    sc.render.engine = 'CYCLES'
    FX.apply(sc)
    return ob


# ---------------------------------------------------------------------------
# the arms
# ---------------------------------------------------------------------------
def subject_materials(before):
    if before:
        return [bpy.data.materials["CeilingMat"]]
    return [m for m in bpy.data.materials if m.name.startswith(RB.PFX)]


def _principleds(mat):
    return [n for n in mat.node_tree.nodes
            if n.bl_idname == "ShaderNodeBsdfPrincipled"]


def arm_geo(mats, drop_normal=False):
    n_set = 0
    for m in mats:
        for b in _principleds(m):
            for name, val in PAINT_SOCKETS.items():
                if name not in b.inputs:
                    continue
                s = b.inputs[name]
                for lk in list(s.links):
                    m.node_tree.links.remove(lk)
                s.default_value = val
                n_set += 1
            if drop_normal and "Normal" in b.inputs:
                for lk in list(b.inputs["Normal"].links):
                    m.node_tree.links.remove(lk)
    return n_set


# Emission strength that puts a flat, sunlit roof at the SAME render value the
# real membrane lands on, so every arm can keep the film's own AgX transform and
# FILM_EXPOSURE. Two arms on `Standard` and five on AgX would have put a tone
# curve between the numbers being subtracted, for no gain: the statistic is a
# normalised correlation and what it needs is that nothing but the SUBJECT
# changes between arms.
#   membrane radiance  = 0.21 * (E_direct_h + E_sky) / pi  = 1.74
#   truegeo at flat    = S * (n.L) = S * sin(12.47 deg)    = S * 0.2159
EMIT_S = 8.06


def arm_truegeo(mats):
    """Every subject surface emits max(0, TrueNormal . sun).

    Lambert off the EVALUATED MESH. Bump nodes and normal maps cannot reach
    this arm at all -- `Geometry -> True Normal` is the polygon normal -- so a
    number that survives here is carried by triangles and nothing else.
    """
    L = np.array(C.SUN_DIR, float)
    L = L / np.linalg.norm(L)
    for m in mats:
        nt = m.node_tree
        nt.nodes.clear()
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        dot = nt.nodes.new("ShaderNodeVectorMath")
        dot.operation = 'DOT_PRODUCT'
        dot.inputs[1].default_value = tuple(L)
        nt.links.new(geo.outputs["True Normal"], dot.inputs[0])
        mx = nt.nodes.new("ShaderNodeMath")
        mx.operation = 'MAXIMUM'
        mx.inputs[1].default_value = 0.0
        nt.links.new(dot.outputs["Value"], mx.inputs[0])
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = EMIT_S
        nt.links.new(mx.outputs[0], em.inputs["Color"])
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs[0], out.inputs["Surface"])


def arm_paint(mats):
    """Every subject surface replaced by an Emission of its own base colour."""
    for m in mats:
        nt = m.node_tree
        srcs = []
        for b in _principleds(m):
            s = b.inputs["Base Color"]
            srcs.append(s.links[0].from_socket if s.links
                        else tuple(s.default_value))
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = EMIT_S
        if srcs and hasattr(srcs[0], "node"):
            nt.links.new(srcs[0], em.inputs["Color"])
        elif srcs:
            em.inputs["Color"].default_value = srcs[0]
        for n in list(nt.nodes):
            if n.bl_idname == "ShaderNodeOutputMaterial":
                nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs[0], out.inputs["Surface"])


def kill_light():
    """No sun, no sky. The paint arm must not be able to borrow a shadow."""
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT':
            bpy.data.objects.remove(o, do_unlink=True)
    w = bpy.context.scene.world
    if w and w.node_tree:
        for n in w.node_tree.nodes:
            if n.bl_idname == "ShaderNodeBackground":
                n.inputs["Strength"].default_value = 0.0


def build_arm(arm, flip=False):
    before = arm.startswith("before")
    build_set(with_roof=not before)
    add_sun_and_camera(flip=flip)
    mats = subject_materials(before)
    detail = {"arm": arm, "subject_materials": [m.name for m in mats]}
    if arm.endswith("_geo"):
        detail["sockets_forced"] = arm_geo(mats)
    elif arm.endswith("_geonb"):
        detail["sockets_forced"] = arm_geo(mats, drop_normal=True)
    elif arm.endswith("_truegeo"):
        arm_truegeo(mats)
        kill_light()
    elif arm.endswith("_paint"):
        arm_paint(mats)
        kill_light()
    return detail


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sunflip", action="store_true")
    a = ap.parse_args(argv)

    arm = a.arm
    base = arm[:-8] if arm.endswith("_sunflip") else arm
    flip = a.sunflip or arm.endswith("_sunflip")
    if base not in ARMS:
        return gate_exit.verdict("PVG_UNKNOWN_ARM_REFUSED",
                                 " %r not in %s" % (base, ARMS))
    detail = build_arm(base, flip=flip)
    detail["sunflip"] = bool(flip)

    K.assert_no_external_assets()
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
    detail["out"] = out
    detail["objects"] = len(bpy.context.scene.objects)
    detail["lights"] = len([o for o in bpy.context.scene.objects
                            if o.type == 'LIGHT'])
    print(">> %s" % json.dumps(detail))
    print(">> saved %s (%.1f MB)" % (out, os.path.getsize(out) / 1e6))
    return gate_exit.verdict("PVG_ARM_BUILT_OK", " %s" % arm)


if __name__ == "__main__":
    gate_exit.guard(main, tool="r2366_roof_pvg")
