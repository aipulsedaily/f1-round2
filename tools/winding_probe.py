"""Winding probe — what does CYCLES actually do with a reversed face?

    blender -b --factory-startup -P tools/winding_probe.py -- --save probe.blend

Three claims are load-bearing in `itemkit` section 3b and none of them may be
asserted:

  1. a face whose winding is reversed in the VERTEX DATA renders with its
     shading normal flipped, so its bump relief INVERTS -- a ridge lights as a
     groove. This is the defect;
  2. an object mirrored by a NEGATIVE-DETERMINANT MATRIX does not, because
     Cycles carries a negative-scale flag and flips the normal back. This is
     not a defect, and treating it as one read `grandstand_riser_unit` as
     96.3 % inside-out on geometry that renders perfectly;
  3. neither of them renders BLACK, which is why nothing caught this for the
     life of the project.

The scene is one row of five spheres under the contract sun, each carrying the
same 6 mm-wavelength ridged bump, plus a matching row shaded by their own
geometric normal as emission so the answer is readable without judgement:

    A  correct
    B  winding reversed in the vertex array          <- the defect
    C  mirrored by matrix, scale x = -1              <- not a defect
    D  mirrored by matrix AND by the vertex array    <- two wrongs
    E  correct, flat-shaded control

Render it and LOOK. `--normals` builds the emission variant.
"""
import argparse
import math
import os
import sys

import numpy as np

import bpy

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "world"))
import itemkit as K                                          # noqa: E402
import world_contract as C                                   # noqa: E402

PFX = "WPB_"
# A DEMONSTRATION, NOT A SPEC. 12 mm at m = 2.2 is well above the cloth band on
# purpose: the point is to make the direction of the relief unmistakable at a
# glance, and a 0.28 pp surface is unmistakable to a pixel-peep and not to a
# thumbnail. 12 mm reads ~11 px at this framing.
LAM = 0.012
MOD = 2.20


def ridged_material(name, normals_only=False, shader="bump"):
    nt = K.NT(PFX + name)
    if shader == "backfacing":
        # THE PROOF THAT THE REVERSAL REACHED THE RENDERER. Cycles' own
        # `Geometry > Backfacing` is 1 where the ray hits the back of a face.
        # If the reversed sphere renders WHITE and the correct one BLACK, then
        # Cycles saw a reversed surface, and any claim that the two lit renders
        # are identical is a claim about SHADING, not about a build that failed
        # to take. Without this the whole probe could be measuring two copies
        # of the same file.
        g = nt.n("ShaderNodeNewGeometry")
        bf = [i for i, o in enumerate(g.outputs) if o.name == "Backfacing"][0]
        em = nt.n("ShaderNodeEmission")
        nt.pin(em, 1, 1.0)
        nt.pin(em, 0, (g, bf))
        out = nt.n("ShaderNodeOutputMaterial")
        nt.t.links.new(em.outputs[0], out.inputs["Surface"])
        return nt.m
    if shader == "displace":
        # TRUE DISPLACEMENT, which moves real geometry ALONG THE NORMAL. If
        # anything depends on which way the surface faces, this does.
        P0 = nt.object_coords()
        w0 = nt.wave(P0, scale=1.0 / LAM, distortion=0.0, detail=0.0,
                     direction="X")
        ds = nt.n("ShaderNodeDisplacement")
        nt.pin_named(ds, "Height", w0)
        nt.pin_named(ds, "Midlevel", 0.5)
        nt.pin_named(ds, "Scale", 0.004)
        bs = nt.n("ShaderNodeBsdfPrincipled")
        nt.pin(bs, 0, (0.20, 0.20, 0.20))
        nt.pin(bs, 2, 0.72)
        out = nt.n("ShaderNodeOutputMaterial")
        nt.t.links.new(bs.outputs[0], out.inputs["Surface"])
        nt.t.links.new(ds.outputs[0], out.inputs["Displacement"])
        nt.m.displacement_method = "DISPLACEMENT"
        return nt.m
    if normals_only:
        # THE UNJUDGEABLE VARIANT: emit the shading normal itself. If Cycles
        # hands back a flipped normal the sphere changes colour, and no opinion
        # is involved.
        g = nt.n("ShaderNodeNewGeometry")
        nd = nt.n("ShaderNodeVectorMath")
        nd.operation = "MULTIPLY_ADD"
        nt.pin(nd, 0, (g, 1))                       # Normal
        nd.inputs[1].default_value = (0.5, 0.5, 0.5)
        nd.inputs[2].default_value = (0.5, 0.5, 0.5)
        em = nt.n("ShaderNodeEmission")
        nt.t.links.new(nd.outputs[0], em.inputs[0])
        out = nt.n("ShaderNodeOutputMaterial")
        nt.t.links.new(em.outputs[0], out.inputs["Surface"])
        return nt.m
    P = nt.object_coords()
    # PARALLEL RIDGES, NOT ISOTROPIC NOISE. Inverting a symmetric noise field
    # gives a statistically identical picture and the A/B reads as "both look
    # grainy". A ridge inverted is a GROOVE: with a raking sun the bright edge
    # of every band jumps to the other side of the band, and that is a
    # difference an eye can name rather than feel.
    w = nt.wave(P, scale=1.0 / LAM, distortion=0.0, detail=0.0, direction="X")
    b = nt.bump(w, 1.0, modulation_pp=MOD, wavelength_m=LAM)
    nt.principled_out(base_color=(0.20, 0.20, 0.20), roughness=0.72, normal=b)
    return nt.m


def sphere(name, centre, kind, mat, coll_, r=0.35):
    V, Q = K._ctl_sphere(nu=200, nv=140, r=r)
    if kind in ("reversed", "both"):
        Q = Q[:, ::-1].copy()
    me, off = K.new_mesh(PFX + name, V, quads=Q, smooth_deg=33.0, orient=False)
    ob = bpy.data.objects.new(PFX + name, me)
    ob.location = (centre[0] + off[0], centre[1] + off[1], centre[2] + off[2])
    if kind in ("mirrored", "both"):
        ob.scale = (-1.0, 1.0, 1.0)
    me.materials.append(mat)
    coll_.objects.link(ob)
    return ob


def build(variant="correct", normals=False, shader="bump"):
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    scene = bpy.context.scene
    root = K.coll("W_WindingProbe")
    K.purge(PFX, None)
    mat = ridged_material("Mat", normals_only=normals, shader=shader)
    kinds = [(variant, variant)]
    R = 0.35
    # THE LIGHT HAS TO RAKE OR THERE IS NOTHING TO SEE. The gate's own witness
    # rig puts the sun 70 deg off the camera azimuth for exactly this reason; a
    # sun behind the lens flattens every bump it is meant to reveal. The camera
    # azimuth is DERIVED from the contract's sun bearing, so it stays raking if
    # the sun moves -- and the row is laid out along the camera's own RIGHT, or
    # three spheres 0.8 m apart line up one behind another and occlude each
    # other, which is what the first version of this did.
    saz = math.atan2(C.SUN_DIR[1], C.SUN_DIR[0])
    caz = saz + math.radians(80.0)
    right = (-math.sin(caz), math.cos(caz), 0.0)
    for nm, kind in kinds:
        sphere(nm, (0.0, 0.0, R), kind, mat, root, r=R)
    K.contract_sun(PFX, scene=scene, coll_=root)
    dist_m = 1.55
    loc = (math.cos(caz) * dist_m, math.sin(caz) * dist_m, R + 0.16)
    cams = K.coll("W_WindingProbe/Cameras", root)
    cam, dist = K.add_camera(PFX + "CAM", loc, (0.0, 0.0, R), 35.0, cams)
    scene.camera = cam
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 96
    if normals:
        scene.view_settings.view_transform = "Standard"
        scene.view_settings.exposure = 0.0
        scene.world.node_tree.nodes.clear() if scene.world and \
            scene.world.node_tree else None
    K.assert_no_external_assets()
    return root


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", required=True)
    ap.add_argument("--normals", action="store_true")
    ap.add_argument("--variant", default="correct",
                    choices=["correct", "reversed", "mirrored"])
    ap.add_argument("--shader", default="bump",
                    choices=["bump", "backfacing", "displace"])
    a = ap.parse_args(argv)
    build(variant=a.variant, normals=a.normals, shader=a.shader)
    # `ob.scale` does not reach `matrix_world` until the view layer updates, and
    # without this every det read +1.0 -- the probe would have "proved" that
    # mirroring does nothing by never mirroring anything.
    bpy.context.view_layer.update()
    # and state what the audit says about the same five, so the picture and the
    # number are produced by the same run
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        r = K.object_winding_report(ob)
        print("PROBE %-14s pieces %d inward %d  det %+.1f  mirrored %s"
              % (ob.name, r["pieces"], r["inward"], r["matrix_det"],
                 r["mirrored_by_matrix"]))
    objs = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in objs:
        f = K.inside_out_fraction([o], n_rays=300, seed=5)
        print("PROBE ray %-14s back %.3f of %d hits" % (o.name, f["fraction"],
                                                        f["hits"]))
    bpy.ops.wm.save_as_mainfile(filepath=a.save)
    print("PROBE saved", a.save)



# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised: `blender -b -P x.py`
    # prints the traceback and exits 0, MEASURED on this box. A gate that
    # crashed was indistinguishable from one that passed. guard() makes an
    # uncaught exception a status 2 and passes any real verdict through
    # unchanged. One shared helper, not N copies -- see tools/gate_exit.py.
    gate_exit.guard(main, tool="winding_probe")
