"""POSITIVE CONTROL for the gate's relief check — does it find relief that IS there?

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/relief_positive_control.py -- --out world/relief_control.blend

WHY THIS EXISTS
---------------
21 of the item gate's 28 verdicts rest on ONE check:

    relief_reads_as_lip_and_shade   15 FAIL  +  6 NOT MEASURED  =  21 of 28

Its author flagged the single-point-of-failure plainly: *"If that check is wrong
in some systematic way I haven't found, most of the table is wrong with it. It is
the one to attack first."*

The check has synthetic validation (dipoles +0.42, isotropic marks +0.00, noise
+0.00) and it has already survived one rewrite that fixed a real confound — the
first version used `rho_across - rho_along`, which read a deck of parallel boards
as -0.133 "anti-relief" purely because a board correlates with itself along its
own length. That history is exactly why it deserves an EMPIRICAL control rather
than another synthetic one: the failure that got fixed was invisible to synthetic
tests and only appeared on real geometry.

WHAT THIS BUILDS
----------------
One plate carrying a LADDER of relief at known heights, under the contract sun,
framed so every feature lands at a known pixel size:

    a  flat reference                       0.0 mm   — must read as no relief
    b  proud ribs                           0.5 mm
    c  proud ribs                           2.0 mm
    d  proud ribs                           8.0 mm   — unmistakable
    e  bolt heads with a real chamfer      3.0 mm high, 15 px across
    f  PRINTED marks, zero height           0.0 mm   — the decoy

Panel (f) is the one that matters as much as (d). It is the same pattern as the
ribs painted on as an albedo change with no geometry at all. A check that cannot
tell (f) from (c) is not measuring relief, it is measuring contrast — and that is
precisely the failure mode the whole gate exists to catch.

WHAT A PASS LOOKS LIKE
----------------------
    dip(a) ~ dip(f) ~ 0        the flat plate and the printed decoy read as nothing
    dip(d) >> dip(a)           real relief is found
    dip(b) < dip(c) < dip(d)   the statistic is MONOTONIC in feature height

Monotonicity is the strongest evidence available. Any single threshold can be
luck; a statistic that tracks the physical quantity across four heights is
measuring the thing it claims to measure.

If (f) scores like (c), the check is broken and 21 verdicts are unsafe.
If (d) scores like (a), the check is blind and 21 verdicts are unsafe.
Either way this is a ~10 minute test against a ~1,400 agent-run decision.
"""

import argparse
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

R2 = os.path.expanduser("~/f1-round2")
sys.path.insert(0, os.path.join(R2, "world"))

import itemkit as K                                          # noqa: E402

# The contract sun. Same numbers the gate stages its own witness frame with, so
# a result here transfers directly.
SUN_ELEV_DEG = 12.5
SUN_BEARING_DEG = -58.0

PANEL_M = 0.60          # each panel is 600 mm square
GAP_M = 0.06
RIB_PITCH_M = 0.030     # 30 mm between ribs
RIB_WIDTH_M = 0.012


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=os.path.join(R2, "world/relief_control.blend"))
    return p.parse_args(argv)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def grey_material(name, base=0.18, rough=0.55):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (base, base, base, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return m


def printed_material(name, base=0.18, mark=0.09, pitch=RIB_PITCH_M,
                     width=RIB_WIDTH_M):
    """The DECOY: the rib pattern as albedo only, with zero geometry.

    Object-space coordinates so the stripes sit at exactly the rib pitch. If the
    relief check scores this like a real rib panel it is measuring contrast, not
    relief.
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    # a square wave in x at the rib pitch, via a wave texture
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.wave_profile = "SAW"
    # R2-058. THIS LINE USED TO READ `1.0 / pitch` AND THE DECOY WAS AT THE
    # WRONG FREQUENCY -- the one thing it must not be.
    #
    # The comment it replaces said: "Blender's Wave scale is 'bands per unit
    # along the axis', so the pitch is 1/scale directly. The first version
    # rendered visibly finer stripes than the ribs, which made the decoy a
    # different spatial frequency and therefore not a fair comparison at all."
    # The symptom was seen and the cause was misdiagnosed: 1/scale IS the finer
    # one. Blender multiplies the coordinate by 20 before the sine, so the
    # emitted pitch is 2*pi/20 = 0.31416 of 1/Scale. `Scale = 1/0.030` therefore
    # emitted a 9.42 mm stripe against a 30 mm rib -- 3.183x finer, in the
    # DECOY, whose entire job is to be the same spatial frequency as the ribs
    # with no geometry behind it. A control that runs at a different frequency
    # from the thing it decoys is not a control.
    #
    # REBUILT 2026-08-03. `world/relief_control.blend` now carries the corrected
    # factor; MEASURED through `itemkit.emitted_wavelength_m`, not read back:
    # 9.425 mm before, 30.000 mm after, against a 30 mm rib.
    #
    # R2-060. THE FREQUENCY WAS ONLY HALF THE FAULT, AND FIXING IT EXPOSED THE
    # OTHER HALF. These bands run along OBJECT X. The ribs do not: `plate()`
    # lays them on the sun's ground direction so the light rakes across them,
    # which is 32 deg away from object X. So the decoy is 30.000 mm along its
    # own normal but 35.375 mm ALONG THE LIGHT -- and along the light is the
    # only direction `relief_anisotropy` looks in.
    #
    # That 32 deg is doing the work. Same scene, same renderer, one Mapping node
    # rotating these coordinates by 148 deg onto the rib normal (MEASURED, CPU,
    # both panels from the same blend):
    #
    #     a_flat        0 mm  plain grey                      dip 0.1003
    #     c_rib_2mm     2 mm  real trapezoidal ribs            dip 0.6082
    #     f_printed     0 mm  paint, 30 mm, 32 deg off         dip 0.0231
    #     g_printed     0 mm  paint, 30 mm, ALIGNED            dip 0.6308
    #
    # A flat quad -- four verts, z identically 0, no displacement, no normal map
    # -- outscores the 2 mm ribs. The check reads a sharp albedo STEP running
    # across the light as a lip-and-shadow dipole, because after the DoG band
    # pass a step and a lip both leave a bipolar pair at the same ~2r spacing.
    # Panel (f) passes on its 32 deg misalignment, which splits the response
    # near-equally between the along- and across-light terms so the two cancel.
    #
    # SO THIS CONTROL DOES NOT PROVE WHAT ITS DOCSTRING CLAIMS. It establishes
    # that the check FINDS relief and is monotonic in height. It does NOT
    # establish that the check can tell paint from geometry.
    #
    # It does not overturn the FAIL verdicts: the error is over-detection, which
    # can only manufacture false PASSES, and the gate's in-frame smooth controls
    # are untextured primitives with no painted anisotropy to inflate them. The
    # verdicts at risk are the relief PASSES, not the failures.
    #
    # Panel (g) is deliberately NOT added here. Gating on it flips this tool's
    # verdict to RELIEF_CHECK_SUSPECT while other agents are mid-flight; that is
    # a call for whoever owns the gate, not a side effect of a rebuild.
    wave.inputs["Scale"].default_value = K.wave_scale_for(pitch)
    wave.inputs["Distortion"].default_value = 0.0
    wave.inputs["Detail"].default_value = 0.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (mark, mark, mark, 1.0)
    ramp.color_ramp.elements[1].position = width / pitch
    ramp.color_ramp.elements[1].color = (base, base, base, 1.0)
    nt.links.new(tex.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.55
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return m


def plate(name, x0, height_m, mat, chamfer_bolts=False):
    """One panel: a flat plate, optionally with proud ribs or bolt heads.

    RIB ORIENTATION IS THE WHOLE TEST AND I GOT IT WRONG THE FIRST TIME.

    The ribs must run ACROSS the light, so the sun rakes over each one and every
    rib casts a lip-and-shadow pair. In the first version they ran ALONG the
    light — parallel to the sun's azimuth — which casts NO shadow pair at all,
    and the check correctly measured nothing. I then read that as "the check is
    blind to 8 mm ribs", which would have condemned a working instrument.

    The sun bearing is -58 deg from +Y toward +X, so its ground-plane direction
    is roughly (sin(-58), -cos(-58)) = (-0.85, -0.53). Ribs are therefore laid
    perpendicular to that, i.e. running along (0.53, -0.85), and the rib axis is
    rotated into the plate rather than left aligned with world Y.
    """
    bm = bmesh.new()
    h = PANEL_M * 0.5
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=h)
    bm.faces.ensure_lookup_table()

    if chamfer_bolts:
        # 3 mm proud discs with a chamfer, on a 60 mm grid
        for gx in range(-3, 4):
            for gy in range(-3, 4):
                cx, cy = gx * 0.06, gy * 0.06
                for rad, z in ((0.010, 0.0), (0.009, height_m * 0.6),
                               (0.006, height_m)):
                    ring = []
                    for k in range(16):
                        a = 2 * math.pi * k / 16
                        ring.append(bm.verts.new(
                            (cx + rad * math.cos(a), cy + rad * math.sin(a), z)))
                    bm.faces.new(ring)
    elif height_m > 0.0:
        # rib axis perpendicular to the sun's ground direction, so the light
        # rakes ACROSS every rib
        az = math.radians(SUN_BEARING_DEG)
        sx, sy = math.sin(az), -math.cos(az)          # sun ground direction
        ax, ay = -sy, sx                              # rib axis, perpendicular
        n = int((PANEL_M * 1.6) / RIB_PITCH_M)
        L = PANEL_M                                   # rib half-length, generous
        for i in range(n):
            t = -PANEL_M * 0.8 + (i + 0.5) * RIB_PITCH_M
            w = RIB_WIDTH_M * 0.5

            def P(off, z):
                """point at lateral offset `off` from the rib centreline."""
                return (t * sx + off * sx + (0.0) * ax,
                        t * sy + off * sy + (0.0) * ay, z)

            def seg(off, z, end):
                cx = (t + off) * sx + end * ax
                cy = (t + off) * sy + end * ay
                return bm.verts.new((cx, cy, z))

            # trapezoidal rib: flat top, sloped sides -> a real lip
            v = [seg(-w, 0.0, -L), seg(-w, 0.0, L),
                 seg(-w * 0.6, height_m, L), seg(-w * 0.6, height_m, -L),
                 seg(w * 0.6, height_m, -L), seg(w * 0.6, height_m, L),
                 seg(w, 0.0, L), seg(w, 0.0, -L)]
            bm.faces.new([v[0], v[1], v[2], v[3]])
            bm.faces.new([v[3], v[2], v[5], v[4]])
            bm.faces.new([v[4], v[5], v[6], v[7]])

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = Vector((x0, 0.0, 0.0))
    ob.data.materials.append(mat)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def main():
    a = parse_args()
    clear()
    scn = bpy.context.scene

    base = grey_material("RC_Grey")
    decoy = printed_material("RC_Printed")

    step = PANEL_M + GAP_M
    panels = [
        ("RC_a_flat_0mm", 0.000, base, False),
        ("RC_b_rib_0p5mm", 0.0005, base, False),
        ("RC_c_rib_2mm", 0.002, base, False),
        ("RC_d_rib_8mm", 0.008, base, False),
        ("RC_e_bolts_3mm", 0.003, base, True),
        ("RC_f_printed_0mm", 0.000, decoy, False),
    ]
    x0 = -step * (len(panels) - 1) * 0.5
    for i, (nm, hgt, mat, bolts) in enumerate(panels):
        plate(nm, x0 + i * step, hgt, mat, chamfer_bolts=bolts)

    # ---- the contract sun ------------------------------------------------
    el = math.radians(SUN_ELEV_DEG)
    az = math.radians(SUN_BEARING_DEG)
    d = Vector((math.cos(el) * math.sin(az), -math.cos(el) * math.cos(az),
                math.sin(el)))
    sd = bpy.data.lights.new("RC_Sun", type="SUN")
    # THE CONTRACT SUN'S REAL IRRADIANCE. The first version used 3.2 and every
    # panel rendered near-black: at 12.5 deg elevation a horizontal plate
    # receives sin(12.5) = 0.216 of normal incidence, so a weak sun leaves the
    # whole ladder in the noise and every measurement is starved. Use the number
    # build_sky actually publishes.
    sd.energy = 115.754
    sd.angle = math.radians(0.545)
    sun = bpy.data.objects.new("RC_Sun", sd)
    # `d` points TOWARD the sun. A Blender sun lamp emits along its local -Z, and
    # to_track_quat('Z','Y') aligns local +Z with the vector given — so passing
    # `d` yields downward emission and passing `-d` points it at the sky.
    #
    # I wrote `-d` here and every panel rendered at 0.04 luminance, lit only by
    # the 0.35-strength sky. Then I read that darkness as evidence the relief
    # CHECK was broken. Verified against the built scene: emit dir z was +0.2164,
    # i.e. straight up. Exactly the bug I had wrongly accused spectator_seated of.
    sun.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    scn.collection.objects.link(sun)

    w = bpy.data.worlds.new("RC_World")
    w.use_nodes = True
    scn.world = w
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.30, 0.42, 0.62, 1.0)
    bg.inputs["Strength"].default_value = 0.35

    # ---- one camera per panel, each framing its panel identically ---------
    for i, (nm, _h, _m, _b) in enumerate(panels):
        cx = x0 + i * step
        cd = bpy.data.cameras.new("CAM_" + nm)
        cd.lens = 50.0
        cd.sensor_width = 36.0
        cam = bpy.data.objects.new("CAM_" + nm, cd)
        # straight down-ish but tilted, so the sun rakes across the ribs
        cam.location = Vector((cx, -0.42, 0.62))
        cam.rotation_euler = (Vector((cx, 0.0, 0.0)) - cam.location) \
            .to_track_quat("-Z", "Y").to_euler()
        scn.collection.objects.link(cam)
    scn.camera = bpy.data.objects["CAM_RC_a_flat_0mm"]

    scn.render.engine = "CYCLES"
    scn.cycles.device = "GPU"
    scn.cycles.samples = 512
    scn.cycles.use_denoising = True
    scn.render.resolution_x = 1024
    scn.render.resolution_y = 1024
    scn.render.film_transparent = True
    scn.view_settings.view_transform = "Standard"
    scn.render.image_settings.color_depth = "16"

    # ---- REFUSE TO SHIP A SCENE THAT CANNOT BE MEASURED -------------------
    # Twice now this control rendered at 0.04 luminance — lit only by a
    # 0.35-strength sky because the sun was pointing at it — and twice I went on
    # to measure the result and drew a conclusion about the CHECK from it. A
    # control that is itself broken produces confident nonsense, which is worse
    # than no control at all. Assert the sun before saving.
    bpy.context.view_layer.update()
    emit = (sun.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
    if emit.z >= 0.0:
        raise SystemExit(
            f"REFUSING TO SAVE: the sun emits UPWARD (z={emit.z:+.4f}). A sun "
            f"{SUN_ELEV_DEG} deg above the horizon must emit downward, or every "
            "panel is lit by sky alone and every measurement taken from it is "
            "meaningless.")
    cos_inc = -emit.z                       # plates are horizontal, normal +Z
    print(f">> sun emits {tuple(round(v, 4) for v in emit)}  "
          f"cos(incidence) on a horizontal plate {cos_inc:.4f}")

    # ---- AND REFUSE TO SHIP AN OVER-EXPOSED ONE TOO -----------------------
    # First attempt: sun energy 3.2 -> every panel at 0.04 luminance, lit by sky
    # alone. Second attempt: 115.754 with the sun finally pointing down -> the
    # printed decoy rendered PURE WHITE, its stripes clipped out of existence.
    # Both are unmeasurable and both looked like a result.
    #
    # The reflected radiance off a lambertian plate is roughly
    #     L = albedo * E * cos(i) / pi
    # and the Standard view transform clips at 1.0, so aim the LIT plate near
    # 0.45 and let the shadowed troughs fall where they may. Solving for E:
    #     E = target * pi / (albedo * cos(i))
    target_L = 0.45
    albedo = 0.18
    need_E = target_L * math.pi / (albedo * max(cos_inc, 1e-6))
    sd.energy = need_E
    pred = albedo * need_E * cos_inc / math.pi
    print(f">> sun energy solved to {need_E:.2f} W/m2 for a lit-plate radiance "
          f"of {pred:.3f} (target {target_L})")
    if not (0.15 < pred < 0.85):
        raise SystemExit(
            f"REFUSING TO SAVE: predicted lit radiance {pred:.3f} is outside "
            "0.15-0.85. Too dark and the ribs sit in noise; too bright and the "
            "printed decoy clips to white. Either way the ladder cannot be "
            "measured and any verdict drawn from it is meaningless.")
    print(f">> sky background {bg.inputs['Strength'].default_value:.2f}, "
          f"direct:sky ratio {need_E * cos_inc / max(bg.inputs['Strength'].default_value, 1e-6):.1f}:1")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out), compress=False)

    # px/m at the panel, so the reported feature sizes are honest
    dist = (Vector((0.0, 0.0, 0.0)) - Vector((0.0, -0.42, 0.62))).length
    px_per_m = (1024 * 50.0 / 36.0) / dist
    print(f">> saved {a.out}")
    print(f">> camera distance {dist:.3f} m, {px_per_m:.0f} px/m at the panel")
    print(f">> rib pitch {RIB_PITCH_M*1000:.0f} mm = {RIB_PITCH_M*px_per_m:.1f} px")
    print(f">> rib width {RIB_WIDTH_M*1000:.0f} mm = {RIB_WIDTH_M*px_per_m:.1f} px")
    for nm, hgt, _m, bolts in panels:
        kind = "bolts" if bolts else ("printed" if "printed" in nm else "ribs")
        print(f"     {nm:<22}{hgt*1000:>7.1f} mm  {kind}")
    print(">> STAGE RESULT: RELIEF_CONTROL_BUILT")



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
    gate_exit.guard(main, tool="relief_positive_control")
