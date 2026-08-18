"""Measure the gate's own relief statistic on the positive-control ladder.

    # add the ALIGNED decoy to the shipped control blend (once, after a rebuild)
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/relief_control_measure.py -- --augment

    # measure
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/relief_control_measure.py -- --dir render/relief_control

Reuses `relief_anisotropy()` STRAIGHT OUT OF tools/item_gate.py — importing the
real function, not a reimplementation. A reimplementation would test my
understanding of the check rather than the check itself, which is the same class
of error as measuring the wrong quantity in the first place.

WHAT A PASS LOOKS LIKE

    dip(a_flat)  ~ dip(f_printed) ~ 0     flat plate and printed decoy read as nothing
    dip(d_8mm)  >> dip(a_flat)            real relief is found
    dip(b) < dip(c) < dip(d)              MONOTONIC in feature height

Monotonicity is the strongest available evidence. A single threshold can be luck;
a statistic that tracks the physical quantity across four known heights is
measuring what it claims to.

THE DECOY IS THE POINT. Panel (f) is the rib pattern painted on as an albedo
change with zero geometry. If it scores like a real rib panel, the check is
measuring CONTRAST rather than RELIEF — and 21 of the gate's 28 verdicts rest on
it.

R2-060 — THE DECOY PASSES ON A COINCIDENCE, AND PANEL (g) IS WHY
================================================================
Panel (f) scores ~0. It scores ~0 because its stripes run along OBJECT X while
`plate()` lays the ribs on the sun's ground direction — 32 deg apart. That
misalignment splits the band-passed response near-equally between the along- and
across-light terms of `relief_anisotropy`, and the two cancel.

Panel (g) is panel (f) with ONE Mapping node rotating the same painted stripes
onto the rib normal. Nothing else differs — same material builder, same plate
builder, same pitch, same albedos, four verts, z identically 0, no modifier, no
displacement, no normal map. MEASURED, CPU, both panels out of the same blend:

    a_flat        0 mm  plain grey                    dip 0.1003
    c_rib_2mm     2 mm  real trapezoidal ribs         dip 0.6082
    f_printed     0 mm  paint, 30 mm, 32 deg off      dip 0.0231
    g_printed     0 mm  paint, 30 mm, ALIGNED         dip 0.6308   <- beats the ribs

So a FLAT QUAD outscores 2 mm of real geometry. After the DoG band-pass a sharp
albedo STEP and a lip-and-shadow both leave a bipolar pair at the same ~2r
spacing, and this statistic cannot tell them apart.

WHAT THAT DOES AND DOES NOT INVALIDATE
--------------------------------------
The error is OVER-DETECTION. Passing requires `subject >= control + RELIEF_MARGIN`
with the control an untextured plain-grey primitive, so inflation can only
manufacture false PASSES, never false FAILs. Every FAIL still stands. What does
not stand is the claim this control was built to support: it establishes that the
check FINDS relief and is MONOTONIC in height, and NOT that it can tell paint
from geometry.

REPORTED NOW, GATING ONCE THE PASSES HAVE BEEN JUDGED — see
`GATE_ON_ALIGNED_DECOY` below, which is the whole of the switch.

THE REPAIR, AND WHAT IT IS NOT
==============================
    # build the extended ladder: 4 suns x 15 panels
    blender -b --factory-startup -P tools/relief_control_measure.py -- --build2
    # ... render every CAM_<panel> in world/relief_2light_{A,A2,B,C}.blend
    blender -b --factory-startup -P tools/relief_control_measure.py -- --measure2
    # the synthetic controls, no renderer, known answers
    blender -b --factory-startup -P tools/relief_control_measure.py -- --selftest
    # the eight relief PASSES, re-derived through the shipped analyser
    blender -b --factory-startup -P tools/relief_control_measure.py -- --items

`relief_anisotropy` IS UNCHANGED. It still cannot tell a painted step from a lip
and a shadow, and it never will: it measures the SPACING of a bipolar pair and
the two have the same spacing. What changed is that the dip is no longer the
whole of check 6. The frame is now staged and rendered on BOTH candidate sun
sides — the one `sun_side_chosen` picks and the one it rejects, which the gate
already computes — and the fine band is split in log luminance into the half
that MOVED when the sun moved and the half that did not:

    D = (DoG(log L_chosen) - DoG(log L_flip)) / 2      belongs to the LIGHT
    S = (DoG(log L_chosen) + DoG(log L_flip)) / 2      belongs to the SURFACE

Relief lives in D and paint lives in S, and D is compared with the same in-frame
luminance-matched smooth control that `fine_over_control` uses, at the same x2.00.

THE PROPOSED rho CLAUSE DID NOT SURVIVE ITS CONTROLS and is reported rather than
gated; see the note on LIGHT_OVER_CONTROL in item_gate.py. The short version is
that real relief carries a light-INVARIANT component of its own — a rib's flat
top is bright whichever side the sun is on — so `rho <= 0` rejects 3 mm
chamfered bolt heads (+0.1003) while accepting a plain grey plate (-0.8608).

THE CAVEAT THE FIRST LADDER COULD NOT ANSWER was that every one of its panels is
a FLAT HORIZONTAL QUAD, whose diffuse shading is invariant to sun azimuth by
construction. Panels j-n are curved. Measured, A vs B:

    l_cyl_rib_2mm   real 2 mm ribs on a cylinder   light x7.94   RELIEF
    k_cyl_printed   the same paint on a cylinder   light x1.40   reject
    n_sph_printed   the same paint on a sphere     light x1.04   reject

`n_sph_printed` is the row that matters most in this whole file: its dip is
0.6252 and its fine-band contrast is 25.45x the control, so it defeats check 6's
dip AND check 5 outright — and the light-driven amplitude catches it anyway.
"""

import argparse
import glob
import importlib.util
import json
import math
import os
import sys

import numpy as np
import bpy
import bmesh
import mathutils

# Imported by path, not by package: this runs inside Blender's interpreter with
# whatever cwd the caller happened to have.
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402

R2 = os.path.expanduser("~/f1-round2")

SUN_ELEV_DEG = 12.5
SUN_BEARING_DEG = -58.0

ORDER = ["a_flat_0mm", "b_rib_0p5mm", "c_rib_2mm", "d_rib_8mm",
         "e_bolts_3mm", "f_printed_0mm", "g_printed_aligned_0mm"]
HEIGHT_MM = {"a_flat_0mm": 0.0, "b_rib_0p5mm": 0.5, "c_rib_2mm": 2.0,
             "d_rib_8mm": 8.0, "e_bolts_3mm": 3.0, "f_printed_0mm": 0.0,
             "g_printed_aligned_0mm": 0.0}
PANEL_G = "g_printed_aligned_0mm"

# ---------------------------------------------------------------------------
# THE SWITCH. R2-060.
#
# False -> the aligned decoy is MEASURED AND PRINTED, and the verdict is decided
#          without it. The check's other properties (finds relief, monotonic in
#          height) are genuinely established and other agents are mid-flight on
#          verdicts that depend on them; flipping this while they are in the air
#          would strand that work on a conclusion nobody has had a chance to
#          answer.
# True  -> the aligned decoy GATES. `dip(c_rib_2mm) > dip(g_printed_aligned)`
#          becomes a required condition, and this tool returns
#          RELIEF_CHECK_SUSPECT until `relief_anisotropy` can separate a painted
#          step from a lip-and-shadow.
#
# FLIPPED TO True on 2026-08-03, after all eight relief PASSES were judged
# geometry-or-paint by `tools/relief_paint_vs_geometry.py` — those were the only
# verdicts this fault could have manufactured, and none of them turned out to be
# manufactured:
#
#     armco_post         PASS IS REAL    geo-only 1.3262 of a shipped 1.4515
#     catch_fence_post   PASS IS REAL    geo-only 0.3423 of a shipped 0.3929
#     crew_figure        PASS IS REAL    geo-only 0.2223 of a shipped 0.2999
#     gantry_truss       PASS IS REAL    geo-only 0.2634 of a shipped 0.2710
#     pit_wall_unit      PASS IS REAL    geo-only 0.1966 of a shipped 0.3056
#     pont_girder        PASS IS REAL    geo-only 0.1284 of a shipped 0.2045
#     heras_fence_panel  INCONCLUSIVE    no single arm carries it
#     tyre_wall_tyre     INCONCLUSIVE    no single arm clears its own bar
#
# So this tool now says what is true: the check FINDS relief and is MONOTONIC in
# height, and it CANNOT separate a painted step from a lip-and-shadow. Nothing in
# the repository calls this tool from a script — it is run by hand — so the
# status change strands no pipeline. It is a statement about the instrument.
#
# TO CLEAR IT: `relief_anisotropy` has to gain a term that a painted step cannot
# satisfy. The measured candidate is in `tools/relief_paint_vs_geometry.py
# --mode twolight`: render the frame under BOTH staged sun sides and correlate
# the band-passed pair. On this ladder that separates them outright — real ribs
# -0.4248 and -0.1833, both painted decoys +1.0000 — because a lip-and-shadow
# belongs to the light and an albedo step belongs to the surface.
# ---------------------------------------------------------------------------
GATE_ON_ALIGNED_DECOY = True

CONTROL_BLEND = os.path.join(R2, "world/relief_control.blend")


def load_gate():
    """Import the REAL item_gate module, so we test the shipped code."""
    path = os.path.join(R2, "tools/item_gate.py")
    spec = importlib.util.spec_from_file_location("item_gate", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["item_gate"] = mod
    spec.loader.exec_module(mod)
    return mod


def load_png(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float64).reshape(h, w, 4)
    bpy.data.images.remove(img)
    a = a[::-1]                                  # row 0 = top
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    alpha = a[..., 3]
    return lum, alpha


def structure_angle(G, L, mask, r=2):
    """Dominant direction the band-passed FEATURES run, in screen degrees.

    Structure tensor of the DoG image. Measured from screen +col toward screen
    +row, in (-90, +90], with the coherence beside it.

    This is the independent read on R2-060: the fault is an ORIENTATION
    coincidence, so the orientation has to be a measured quantity rather than an
    argument. On the ladder it separates the two decoys outright -- the shipped
    one runs along object X and reads ~0 deg, the aligned one and the real ribs
    both read ~-39 deg.
    """
    B = G._dog(L, r)
    gy, gx = np.gradient(B)
    jxx = float((gx[mask] ** 2).mean())
    jyy = float((gy[mask] ** 2).mean())
    jxy = float((gx[mask] * gy[mask]).mean())
    ang = math.degrees(0.5 * math.atan2(2.0 * jxy, jxx - jyy)) + 90.0
    coh = math.hypot(jxx - jyy, 2.0 * jxy) / max(jxx + jyy, 1e-30)
    while ang > 90.0:
        ang -= 180.0
    while ang <= -90.0:
        ang += 180.0
    return ang, coh


# ===========================================================================
# PANEL (g) -- THE ALIGNED DECOY
# ===========================================================================
def augment_with_panel_g(blend=CONTROL_BLEND):
    """Add the ALIGNED printed decoy to the shipped control blend.

    Panel (g) must differ from panel (f) in EXACTLY ONE THING or it is not a
    control. So it is built by calling `relief_positive_control`'s own
    `printed_material()` and `plate()` -- the shipped builders, imported, not
    copied -- and then inserting one Mapping node between the texture
    coordinates and the wave. Same pitch, same albedos, same plate, same
    material code path.

    THE ROTATION IS DERIVED FROM THE RIB GEOMETRY, NOT TYPED IN. `plate()` lays
    the ribs at successive offsets along the sun's ground direction
    (sin(az), -cos(az)), so THAT vector is the rib normal. A Mapping node in
    POINT mode emits x' = cos(phi)*x - sin(phi)*y, whose level sets have normal
    (cos phi, -sin phi) at angle -phi. Setting phi = -atan2(sy, sx) therefore
    points the painted stripes' normal along the rib normal.

    AND THE PANEL IS THEN PROVEN FLAT, not assumed flat: every vertex z is
    asserted to be exactly 0, the modifier stack asserted empty, and the
    material asserted to drive nothing but Base Color. A decoy with any relief
    in it would make this whole finding an artefact of a botched build.
    """
    if not os.path.exists(blend):
        raise SystemExit(f"REFUSING: no control blend at {blend}; build it with "
                         "tools/relief_positive_control.py first")
    spec = importlib.util.spec_from_file_location(
        "relief_positive_control", os.path.join(R2,
                                                "tools/relief_positive_control.py"))
    RPC = importlib.util.module_from_spec(spec)
    sys.modules["relief_positive_control"] = RPC
    spec.loader.exec_module(RPC)

    bpy.ops.wm.open_mainfile(filepath=blend)
    scn = bpy.context.scene
    name = "RC_" + PANEL_G
    if bpy.data.objects.get(name) is not None:
        print(f">> {name} is already in {blend}; nothing to do")
        return 0

    ref = bpy.data.objects.get("RC_f_printed_0mm")
    if ref is None:
        raise SystemExit("REFUSING: the control blend has no RC_f_printed_0mm, "
                         "so there is nothing for panel (g) to be a control ON.")
    step = RPC.PANEL_M + RPC.GAP_M

    mat = RPC.printed_material("RC_Printed_Aligned")
    nt = mat.node_tree
    wave = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeTexWave")
    tex = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeTexCoord")
    az = math.radians(SUN_BEARING_DEG)
    sx, sy = math.sin(az), -math.cos(az)          # sun ground dir == rib normal
    phi = -math.atan2(sy, sx)
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.vector_type = "POINT"
    mp.inputs["Rotation"].default_value = (0.0, 0.0, phi)
    for lk in list(wave.inputs["Vector"].links):
        nt.links.remove(lk)
    nt.links.new(tex.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])

    # one step past (f), so the existing six panels do not move. A SUN is
    # directional and the sky is uniform, so where the panel sits on the row
    # changes nothing it is measured for.
    x0 = ref.location.x + step
    ob = RPC.plate(name, x0, 0.0, mat, chamfer_bolts=False)

    # ---- PROVE THE NULL: this panel has NO relief in it whatsoever ---------
    zs = [round(v.co.z, 12) for v in ob.data.vertices]
    if len(ob.data.vertices) != 4 or any(z != 0.0 for z in zs):
        raise SystemExit(f"REFUSING: panel (g) is not a flat quad -- "
                         f"{len(ob.data.vertices)} verts, z values {sorted(set(zs))}")
    if len(ob.modifiers) != 0:
        raise SystemExit(f"REFUSING: panel (g) carries modifiers "
                         f"{[m.type for m in ob.modifiers]}")
    bsdf = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    for sock in ("Normal", "Tangent"):
        s = bsdf.inputs.get(sock)
        if s is not None and s.links:
            raise SystemExit(f"REFUSING: panel (g)'s BSDF has {sock} linked; the "
                             "decoy must have no normal or bump input at all")
    out = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial")
    if out.inputs["Displacement"].links:
        raise SystemExit("REFUSING: panel (g) has a displacement link")
    print(f">> panel (g): {len(ob.data.vertices)} verts, z == 0 exactly, "
          f"0 modifiers, no normal/bump/displacement")
    print(f">> stripes rotated {math.degrees(phi):+.3f} deg so their normal "
          f"lies on the rib normal ({sx:+.4f}, {sy:+.4f})")

    cd = bpy.data.cameras.new("CAM_" + name)
    cd.lens, cd.sensor_width = 50.0, 36.0
    cam = bpy.data.objects.new("CAM_" + name, cd)
    cam.location = mathutils.Vector((x0, -0.42, 0.62))
    cam.rotation_euler = (mathutils.Vector((x0, 0.0, 0.0)) - cam.location) \
        .to_track_quat("-Z", "Y").to_euler()
    scn.collection.objects.link(cam)

    bpy.ops.wm.save_as_mainfile(filepath=blend, compress=False)
    print(f">> saved {blend} with {name} and CAM_{name}")
    return 0


def sun_screen_dir(bearing_deg=None):
    """The sun's direction projected into screen space, as (drow, dcol).

    The camera looks from (cx, -0.42, 0.62) at (cx, 0, 0): a level-ish view down
    the +Y axis. Screen +col is world +X, screen +row is world -Y (into the
    frame). The sun bearing is measured from +Y toward +X.
    """
    el = math.radians(SUN_ELEV_DEG)
    az = math.radians(SUN_BEARING_DEG if bearing_deg is None else bearing_deg)
    dx = math.cos(el) * math.sin(az)
    dy = -math.cos(el) * math.cos(az)
    return (-dy, dx)


# ===========================================================================
# R2-060 -- THE TWO-LIGHT LADDER
#
# The shipped ladder proved the check FINDS relief and is MONOTONIC in height,
# and proved -- by panel (g) -- that it CANNOT tell paint from geometry. This
# second ladder is built to answer whether the proposed repair can, and it is
# built to be able to say NO.
#
# THE THREE SUNS. `sun_side_chosen` in every witness spec is already picked from
# two candidates: the sun sits at cam_az +/- SUN_AZ_OFF_CAM_DEG and whichever
# gives the larger cos(incidence) on the subject's dominant visible normal wins.
# So the second render the repair costs is the RUNNER-UP SIDE, not an arbitrary
# new light -- and the runner-up is a MIRROR of the winner about the camera
# azimuth, NOT its opposite. These cameras look down +Y, so bearing -58 mirrors
# to bearing +58 and the pair is 116 deg apart on the compass, not 180.
#
#   A  bearing  -58   the shipped ladder's sun, unchanged
#   B  bearing  +58   THE GATE'S OWN OTHER CANDIDATE -- what the repair costs
#   C  bearing +122   a true 180 deg reversal -- the best case the physics
#                     allows, rendered only to bound how much of the separation
#                     comes from the mirror being imperfect. NOT what ships.
#
# Rendering C as well is the difference between "the repair works" and "the
# repair works when the sun is exactly opposite, which the gate can never
# arrange". A separator that only exists at 180 deg is not a separator for this
# gate.
# ===========================================================================
# A2 IS THE NULL, AND IT IS THE MOST IMPORTANT ROW IN THE TABLE.
#
# The amplitude clause says the band that MOVED when the sun moved must be twice
# the smooth control's. Uncorrelated Monte-Carlo residual moves too: two renders
# of the same scene differ by their noise, and that difference lands ENTIRELY in
# the "light-driven" half. So a subject that is merely noisier than the control
# could clear the bar with no relief on it at all.
#
# A2 is sun A rendered a second time at a DIFFERENT SEED and nothing else. The
# light does not move. Whatever the light-driven band reports across an A/A2
# pair is therefore noise and nothing but noise, measured rather than assumed --
# and the ribs, which report 6.67 % against sun B, have to collapse to that floor
# here or their 6.67 was never about the sun.
SUN_BEARINGS = {"A": -58.0, "A2": -58.0, "B": +58.0, "C": 122.0}
SUN_SEED = {"A": 0, "A2": 20260803, "B": 0, "C": 0}
ROW2_Y = 2.0            # the curved row, far enough that no shadow reaches row 1
ROW2_STEP = 1.2         # > the 0.68 m shadow a 0.15 m radius throws at 12.5 deg
CURVE_R = 0.15
CYL_LEN = 0.60
RING_N = 8192           # 0.115 mm per sample around the rim: a 2.4 mm rib flank
                        # is 21 samples, so smooth shading rounds the corners by
                        # a tenth of a millimetre against a 2 mm rib
BLEND2 = os.path.join(R2, "world/relief_2light_%s.blend")

PANELS2_FLAT = [
    # name                     height_m  material   bolts
    ("a_flat_0mm", 0.0000, "grey", False),
    ("b_rib_0p5mm", 0.0005, "grey", False),
    ("c_rib_2mm", 0.0020, "grey", False),
    ("d_rib_8mm", 0.0080, "grey", False),
    ("e_bolts_3mm", 0.0030, "grey", True),
    ("f_printed_0mm", 0.0000, "printed", False),
    ("g_printed_aligned_0mm", 0.0000, "printed_aligned", False),
    # R2-060 residual #3, made into a panel instead of a caveat: the aligned
    # decoy fails `fine_over_control` only because it is SPARSE -- its fine band
    # is 0.74x the flat plate's. Paint with more contrast in it would clear that
    # bar. This is that paint: the same stripes, the same pitch, the same
    # alignment, albedo 0.60 against 0.02 instead of 0.18 against 0.09.
    ("h_printed_hi_0mm", 0.0000, "printed_hi", False),
    # ... and paint that is not albedo at all. Constant base colour, ROUGHNESS
    # in stripes. A specular lobe DOES move when the sun moves, so this is the
    # one painted decoy with a physical reason to defeat a two-light test, and
    # it is here to be given the chance.
    ("i_rough_stripes_0mm", 0.0000, "rough_stripes", False),
    # ... and h AGAIN, at a contrast the exposure can actually hold. Panel h is
    # albedo 0.60 against 0.02, and 0.60 renders at luminance 1.5 under the
    # ladder's own solved exposure: its bright stripes CLIP, and 60 % of the
    # panel (541,000 px of 909,000) is thrown out of every measurement taken on
    # it. That makes h an extreme-contrast decoy measured on its dark half only,
    # which is not the test R2-060 asked for. Panel o is 0.30 against 0.02 --
    # 15:1 against the aligned decoy's 2:1, and 0.30 renders at 0.75, inside the
    # range. THIS is the "a higher-contrast painted pattern would pass both
    # checks" case, posed properly.
    ("o_printed_hi2_0mm", 0.0000, "printed_hi2", False),
]
# Panels are laid from a FIXED anchor rather than recentred on the current
# count, so appending panel o leaves every other panel at exactly the x it was
# rendered at. A row that shuffles when it grows makes every earlier frame a
# frame of a different scene.
FLAT_ROW_ANCHOR = 9
PANELS2_CURVED = [
    # THE CAVEAT THE LADDER COULD NOT ANSWER. Every panel above is a FLAT
    # HORIZONTAL QUAD, whose diffuse shading is invariant to sun azimuth by
    # construction -- the easiest case a two-light test can be given. These are
    # the hard one. j/k differ ONLY in material and j/l ONLY in radius, so each
    # comparison moves exactly one thing.
    ("j_cyl_flat", "grey", "cyl", 0.0),
    ("k_cyl_printed", "printed_aligned", "cyl", 0.0),
    ("l_cyl_rib_2mm", "grey", "cyl", 0.002),
    ("m_sph_flat", "grey", "sph", 0.0),
    ("n_sph_printed", "printed_aligned", "sph", 0.0),
]
ORDER2 = ([p[0] for p in PANELS2_FLAT] + [p[0] for p in PANELS2_CURVED])
HEIGHT_MM2 = dict(
    [(p[0], p[1] * 1000.0) for p in PANELS2_FLAT]
    + [(p[0], p[3] * 1000.0) for p in PANELS2_CURVED])
# Which panels are PAINT and which are SHAPE. Written down before anything is
# measured, so the truth table is scored against a key rather than against
# whatever the numbers turn out to say.
TRUTH2 = {
    "a_flat_0mm": "smooth", "b_rib_0p5mm": "relief", "c_rib_2mm": "relief",
    "d_rib_8mm": "relief", "e_bolts_3mm": "relief", "f_printed_0mm": "paint",
    "g_printed_aligned_0mm": "paint", "h_printed_hi_0mm": "paint",
    "i_rough_stripes_0mm": "paint", "o_printed_hi2_0mm": "paint",
    "j_cyl_flat": "smooth",
    "k_cyl_printed": "paint", "l_cyl_rib_2mm": "relief",
    "m_sph_flat": "smooth", "n_sph_printed": "paint",
}


def _rpc():
    """The SHIPPED builders, imported. Panels a-g must be the same objects the
    first ladder measured or this is a different experiment."""
    spec = importlib.util.spec_from_file_location(
        "relief_positive_control",
        os.path.join(R2, "tools/relief_positive_control.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["relief_positive_control"] = mod
    spec.loader.exec_module(mod)
    return mod


def _sun_ground(bearing_deg):
    """(sx, sy): the direction the light TRAVELS across the ground."""
    az = math.radians(bearing_deg)
    return math.sin(az), -math.cos(az)


def _stripe_phi():
    """The Mapping rotation that lays painted stripes on the RIB normal.

    Identical derivation to `augment_with_panel_g`, and deliberately keyed to
    SUN_BEARING_DEG (sun A) rather than to whichever sun is being rendered: the
    stripes are painted on the object once and do not move when the sun does.
    That is the entire point of the decoy.
    """
    sx, sy = _sun_ground(SUN_BEARING_DEG)
    return -math.atan2(sy, sx)


def _align_stripes(mat, phi):
    """Insert one Mapping node between the texture coordinates and the wave."""
    nt = mat.node_tree
    wave = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeTexWave")
    tex = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.vector_type = "POINT"
    mp.inputs["Rotation"].default_value = (0.0, 0.0, phi)
    for lk in list(wave.inputs["Vector"].links):
        nt.links.remove(lk)
    nt.links.new(tex.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
    return mat


def _rough_stripe_material(RPC, name, phi, base=0.18, rough_lo=0.08,
                           rough_hi=0.80):
    """The SPECULAR decoy: one flat colour, roughness in aligned stripes.

    Built from `printed_material` so the wave, the pitch, the ramp and the
    alignment are the same code path as every other decoy; the only change is
    where the ramp lands. Base Colour is then pinned constant, so there is no
    albedo pattern here AT ALL -- if this panel reads as relief it is because a
    specular lobe moved, which is the one way paint has of moving with the light.
    """
    m = RPC.printed_material(name)
    _align_stripes(m, phi)
    nt = m.node_tree
    ramp = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeValToRGB")
    bsdf = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    for lk in list(bsdf.inputs["Base Color"].links):
        nt.links.remove(lk)
    bsdf.inputs["Base Color"].default_value = (base, base, base, 1.0)
    ramp.color_ramp.elements[0].color = (rough_lo,) * 3 + (1.0,)
    ramp.color_ramp.elements[1].color = (rough_hi,) * 3 + (1.0,)
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])
    return m


def _link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _corrugated_ring(radius, rib_h, pitch, width):
    """One cross-section: a circle, with trapezoidal ribs standing proud of it.

    rib_h = 0 gives an exact circle, so the smooth cylinder and the ribbed one
    come off the SAME code at the SAME vertex count and differ in nothing but
    the radius function. A control that differs in topology from the thing it
    controls is not a control.
    """
    w = width * 0.5
    pts = []
    for i in range(RING_N):
        th = 2.0 * math.pi * i / RING_N
        s = radius * th                       # arc length round the rim
        u = ((s + 0.5 * pitch) % pitch) - 0.5 * pitch
        au = abs(u)
        if rib_h <= 0.0 or au >= w:
            h = 0.0
        elif au <= 0.6 * w:
            h = rib_h
        else:
            h = rib_h * (w - au) / (0.4 * w)
        pts.append((th, radius + h))
    return pts


def _cylinder(name, centre, mat, rib_h, axis_xy):
    """A cylinder whose axis lies along `axis_xy`, built in WORLD-ALIGNED local
    coordinates with an identity object rotation.

    That matters: the painted decoy reads OBJECT coordinates, and its Mapping
    rotation is derived from a WORLD direction. Rotating the object would rotate
    the paint with it and the decoy would no longer be the same paint the flat
    panels carry.
    """
    RPC = _rpc()
    ring = _corrugated_ring(CURVE_R, rib_h, RPC.RIB_PITCH_M, RPC.RIB_WIDTH_M)
    ax = mathutils.Vector((axis_xy[0], axis_xy[1], 0.0)).normalized()
    e1 = mathutils.Vector((-ax.y, ax.x, 0.0))     # radial basis, in-plane
    e2 = mathutils.Vector((0.0, 0.0, 1.0))
    bm = bmesh.new()
    rows = []
    nseg = 4
    for k in range(nseg + 1):
        t = (k / nseg - 0.5) * CYL_LEN
        row = []
        for th, rad in ring:
            p = (ax * t + e1 * (rad * math.cos(th)) + e2 * (rad * math.sin(th)))
            row.append(bm.verts.new((p.x, p.y, p.z)))
        rows.append(row)
    for k in range(nseg):
        for i in range(RING_N):
            j = (i + 1) % RING_N
            bm.faces.new([rows[k][i], rows[k][j], rows[k + 1][j],
                          rows[k + 1][i]])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = mathutils.Vector(centre)
    ob.data.materials.append(mat)
    return _link(ob)


def _sphere(name, centre, mat):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=256, v_segments=128,
                              radius=CURVE_R)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.update()
    ob = bpy.data.objects.new(name, me)
    ob.location = mathutils.Vector(centre)
    ob.data.materials.append(mat)
    return _link(ob)


def _camera(name, aim):
    """Same relative view for every panel: 0.75 m away, looking down at 56 deg.

    Copied from the shipped ladder's framing rather than re-chosen, so a number
    measured here is on the same scale as a number measured there.
    """
    cd = bpy.data.cameras.new("CAM_" + name)
    cd.lens, cd.sensor_width = 50.0, 36.0
    cam = bpy.data.objects.new("CAM_" + name, cd)
    aim = mathutils.Vector(aim)
    cam.location = aim + mathutils.Vector((0.0, -0.42, 0.62))
    cam.rotation_euler = (aim - cam.location).to_track_quat("-Z", "Y").to_euler()
    _link(cam)
    return cam


def build_two_light():
    """Write the three sun variants of the extended ladder.

    ONE SCENE PER SUN, fourteen cameras in each. The broker batches by scene, so
    this is three loads of a ~2 MB file for 42 frames rather than 42 loads --
    the same submission shape the five-arm study was rebuilt into, for the same
    reason.
    """
    RPC = _rpc()
    phi = _stripe_phi()
    out = []
    for tag, bearing in SUN_BEARINGS.items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scn = bpy.context.scene

        grey = RPC.grey_material("RC2_Grey")
        printed = RPC.printed_material("RC2_Printed")
        printed_al = _align_stripes(RPC.printed_material("RC2_PrintedAligned"),
                                    phi)
        printed_hi = _align_stripes(
            RPC.printed_material("RC2_PrintedHi", base=0.60, mark=0.02), phi)
        printed_hi2 = _align_stripes(
            RPC.printed_material("RC2_PrintedHi2", base=0.30, mark=0.02), phi)
        rough = _rough_stripe_material(RPC, "RC2_RoughStripes", phi)
        mats = {"grey": grey, "printed": printed, "printed_aligned": printed_al,
                "printed_hi": printed_hi, "printed_hi2": printed_hi2,
                "rough_stripes": rough}

        step = RPC.PANEL_M + RPC.GAP_M
        x0 = -step * (FLAT_ROW_ANCHOR - 1) * 0.5
        for i, (nm, hgt, mk, bolts) in enumerate(PANELS2_FLAT):
            cx = x0 + i * step
            RPC.plate(nm, cx, hgt, mats[mk], chamfer_bolts=bolts)
            _camera(nm, (cx, 0.0, 0.0))

        sx, sy = _sun_ground(SUN_BEARING_DEG)
        axis_xy = (-sy, sx)                    # the rib axis, as `plate()` lays it
        x0 = -ROW2_STEP * (len(PANELS2_CURVED) - 1) * 0.5
        for i, (nm, mk, kind, rib) in enumerate(PANELS2_CURVED):
            cx = x0 + i * ROW2_STEP
            c = (cx, ROW2_Y, CURVE_R)
            if kind == "cyl":
                _cylinder(nm, c, mats[mk], rib, axis_xy)
            else:
                _sphere(nm, c, mats[mk])
            _camera(nm, c)

        el = math.radians(SUN_ELEV_DEG)
        az = math.radians(bearing)
        d = mathutils.Vector((math.cos(el) * math.sin(az),
                              -math.cos(el) * math.cos(az), math.sin(el)))
        sd = bpy.data.lights.new("RC2_Sun", type="SUN")
        sd.angle = math.radians(0.545)
        sun = bpy.data.objects.new("RC2_Sun", sd)
        sun.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        _link(sun)

        w = bpy.data.worlds.new("RC2_World")
        w.use_nodes = True
        scn.world = w
        bg = w.node_tree.nodes["Background"]
        bg.inputs["Color"].default_value = (0.30, 0.42, 0.62, 1.0)
        bg.inputs["Strength"].default_value = 0.35

        scn.render.engine = "CYCLES"
        scn.cycles.device = "GPU"
        scn.cycles.samples = 512
        scn.cycles.seed = SUN_SEED[tag]
        scn.cycles.use_denoising = True
        scn.render.resolution_x = 1024
        scn.render.resolution_y = 1024
        scn.render.film_transparent = True
        scn.view_settings.view_transform = "Standard"
        scn.render.image_settings.color_depth = "16"
        scn.camera = bpy.data.objects["CAM_a_flat_0mm"]

        # ---- REFUSE TO SHIP A SCENE THAT CANNOT BE MEASURED ---------------
        # Three of the twenty-seven faults on this project were an instrument,
        # and one of them was THIS scene with its sun pointing at the sky. The
        # assertions are the shipped ones, re-run per sun.
        bpy.context.view_layer.update()
        emit = (sun.matrix_world.to_3x3()
                @ mathutils.Vector((0, 0, -1))).normalized()
        if emit.z >= 0.0:
            raise SystemExit(f"REFUSING: sun {tag} emits UPWARD ({emit.z:+.4f})")
        cos_inc = -emit.z
        sd.energy = 0.45 * math.pi / (0.18 * max(cos_inc, 1e-6))
        pred = 0.18 * sd.energy * cos_inc / math.pi
        if not (0.15 < pred < 0.85):
            raise SystemExit(f"REFUSING: sun {tag} predicts lit radiance {pred:.3f}")
        # ... and the sun MUST actually be on the other side, or the "two light"
        # test is one light rendered twice. Measured as the angle between the
        # two ground directions, printed, and asserted.
        gx, gy = _sun_ground(bearing)
        ax_, ay_ = _sun_ground(SUN_BEARING_DEG)
        sep = math.degrees(math.acos(max(-1.0, min(1.0, gx * ax_ + gy * ay_))))
        if tag not in ("A", "A2") and sep < 90.0:
            raise SystemExit(f"REFUSING: sun {tag} is only {sep:.1f} deg from "
                             "sun A; a lip and its shadow do not swap ends "
                             "until the light crosses to the other side")
        print(f">> sun {tag}: bearing {bearing:+.1f} deg, emit "
              f"{tuple(round(v, 4) for v in emit)}, energy {sd.energy:.2f}, "
              f"lit radiance {pred:.3f}, {sep:.1f} deg from sun A")

        p = BLEND2 % tag
        os.makedirs(os.path.dirname(p), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=p, compress=False)
        print(f">> saved {p} with {len(ORDER2)} panels and "
              f"{len(ORDER2)} cameras")
        out.append(p)

    # ---- PROVE THE NULLS, rather than assume them ------------------------
    # Every panel that claims zero relief is asserted to HAVE zero relief. The
    # whole finding rests on the painted panels being flat, and "I built it
    # flat" is not evidence.
    bpy.ops.wm.open_mainfile(filepath=BLEND2 % "A")
    for nm, kind in (("f_printed_0mm", "quad"), ("g_printed_aligned_0mm", "quad"),
                     ("h_printed_hi_0mm", "quad"), ("i_rough_stripes_0mm", "quad"),
                     ("o_printed_hi2_0mm", "quad"),
                     ("a_flat_0mm", "quad"), ("k_cyl_printed", "cyl"),
                     ("j_cyl_flat", "cyl"), ("n_sph_printed", "sph"),
                     ("m_sph_flat", "sph")):
        ob = bpy.data.objects[nm]
        if ob.modifiers:
            raise SystemExit(f"REFUSING: {nm} carries modifiers")
        nt = ob.data.materials[0].node_tree
        bsdf = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
        for sock in ("Normal", "Tangent"):
            s = bsdf.inputs.get(sock)
            if s is not None and s.links:
                raise SystemExit(f"REFUSING: {nm} drives {sock}")
        o = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial")
        if o.inputs["Displacement"].links:
            raise SystemExit(f"REFUSING: {nm} has a displacement link")
        if kind == "quad":
            zs = {round(v.co.z, 12) for v in ob.data.vertices}
            if len(ob.data.vertices) != 4 or zs != {0.0}:
                raise SystemExit(f"REFUSING: {nm} is not a flat quad "
                                 f"({len(ob.data.vertices)} verts, z {sorted(zs)})")
        else:
            rs = [math.dist((v.co.x, v.co.y, v.co.z), (0, 0, 0))
                  if kind == "sph" else
                  math.hypot(*_radial(ob, v)) for v in ob.data.vertices]
            spread = max(rs) - min(rs)
            if spread > 1e-6:
                raise SystemExit(f"REFUSING: {nm} is not a surface of revolution "
                                 f"of constant radius -- radius spread "
                                 f"{spread * 1000:.4f} mm")
        print(f">> null proven: {nm} has no geometry and no normal input")
    # ... and the POSITIVE control the same way round: the ribbed cylinder must
    # actually have 2 mm of relief on it, or it is a second smooth cylinder.
    ob = bpy.data.objects["l_cyl_rib_2mm"]
    rs = [math.hypot(*_radial(ob, v)) for v in ob.data.vertices]
    got = (max(rs) - min(rs)) * 1000.0
    if abs(got - 2.0) > 0.05:
        raise SystemExit(f"REFUSING: l_cyl_rib_2mm has {got:.4f} mm of radial "
                         "relief, not 2 mm")
    print(f">> positive control proven: l_cyl_rib_2mm carries {got:.4f} mm")
    return 0


# Which smooth control each panel is scored against. A painted SPHERE compared
# with a flat plate would be the exact divisor hazard `contrast_bands` documents
# -- different mean, different shading, different noise -- so each shape class
# gets a control of its own shape, differing from it in NOTHING but material.
CONTROL_FOR = {
    "cyl": "j_cyl_flat", "sph": "m_sph_flat", "flat": "a_flat_0mm",
}


def _shape_of(name):
    if name.startswith(("j_cyl", "k_cyl", "l_cyl")):
        return "cyl"
    if name.startswith(("m_sph", "n_sph")):
        return "sph"
    return "flat"


def _panel_stats(G, pa, pb, sun_rc):
    """Everything the combined rule needs, for one panel, from one sun pair."""
    A = G.load_linear_rgba(pa)
    B = G.load_linear_rgba(pb)
    if A.shape != B.shape:
        return {"reason": f"{A.shape} vs {B.shape}"}

    def lum(x):
        return (0.2126 * x[:, :, 0] + 0.7152 * x[:, :, 1]
                + 0.0722 * x[:, :, 2]).astype(np.float64)

    LA, LB = lum(A), lum(B)
    solidA, solidB = A[:, :, 3] >= 0.995, B[:, :, 3] >= 0.995
    agree = float((solidA == solidB).mean())
    # THE WHOLE LIT PANEL, not the gate's `lit_core`, AND THE REASON IS
    # MEASURED. `lit_core` keeps the brightest 40 % of a blurred copy, which is
    # right on a real subject with real shading and DEGENERATE on a uniformly
    # lit flat plate: there the cut is made on noise, the retained region
    # shatters, and erosion deletes most of what is left. Run on this ladder it
    # takes the flat plate from 262,000 px to 10,749 and its dip from 0.1003 to
    # 0.4158 -- a baseline four times higher than the thing it is the baseline
    # FOR. So the panels are measured over `solid & unclipped`, which is also
    # the mask the shipped ladder numbers were taken with, and every ratio below
    # has its control measured through the same mask.
    okA = solidA & (LA > 0.0015) & (LA < 0.90)
    okB = solidB & (LB > 0.0015) & (LB < 0.90)
    both = okA & okB
    mu = float(LA[okA].mean()) if okA.any() else 0.0
    st, det = G.two_light_bands(LA, LB, both, G.LOG_FLOOR_FRAC * max(mu, 1e-6))
    dipA, _ = G.relief_anisotropy(LA, okA, sun_rc)
    bands, _, _ = G.contrast_bands(LA, okA)
    fine = G._agg(bands or {}, G.FINE_BANDS)
    out = {"dip": dipA, "fine": fine, "px_both": int(both.sum()),
           "px_a": int(okA.sum()), "px_b": int(okB.sum()),
           "alpha_agreement": round(agree, 6), "mean": round(mu, 6)}
    if st is not None:
        out.update(st)
        d2 = (det.get("D") or {}).get(2)
        if d2 is not None:
            out["dip_light"], _ = G.relief_anisotropy(LA, both, sun_rc, r=2,
                                                      band=d2)
    return out


def measure_two_light(root, sun_b):
    """The combined rule, scored over the extended ladder. R2-060.

    Every row is scored against `TRUTH2`, which was written down before any of
    these frames existed. The point of the table is not that the new rule passes
    the ribs -- the old one did that too -- but that it FAILS both painted
    decoys, the high-contrast one, the roughness one and the CURVED one, while
    still failing the flat plate that the rho clause on its own would pass.
    """
    G = load_gate()
    dir_a = os.path.join(root, "sunA")
    dir_b = os.path.join(root, "sun" + sun_b)
    sun_rc = sun_screen_dir(SUN_BEARINGS["A"])
    rc_b = sun_screen_dir(SUN_BEARINGS[sun_b])
    dot = sun_rc[0] * rc_b[0] + sun_rc[1] * rc_b[1]
    scr = math.degrees(math.acos(max(-1.0, min(1.0, dot))))
    print(f">> sun A bearing {SUN_BEARINGS['A']:+.1f}, sun {sun_b} bearing "
          f"{SUN_BEARINGS[sun_b]:+.1f}; screen dir A "
          f"({sun_rc[0]:+.4f}, {sun_rc[1]:+.4f}), {sun_b} "
          f"({rc_b[0]:+.4f}, {rc_b[1]:+.4f})")
    # HOW HARD A CASE THIS LADDER IS, stated as a number rather than assumed.
    # What matters to a lip and its shadow is not how far the sun moved on the
    # COMPASS but how far it moved ACROSS THE PICTURE, and the two are not the
    # same: the screen foreshortens the depth axis. Measured on the eight real
    # witness frames, the gate's own two candidate sides come out 178.2 deg
    # apart ON SCREEN despite being 140 deg apart on the ground. This ladder's
    # A/B pair is 114.7 deg on screen and its A/C pair 162.4 deg, because these
    # cameras look down at 56 deg from close range while the gate's look at an
    # item from its filmed distance.
    #
    # I FIRST WROTE HERE that B is therefore a harder case than the gate will
    # ever meet and that a separator working on it works a fortiori on the real
    # frames. THAT IS FALSE AND SUN C IS WHAT DISPROVED IT. Separability is not
    # monotone in the angle: at 162 deg the two suns light nearly disjoint sides
    # of a smooth convex body, what survives in BOTH frames is a grazing band
    # where cos(i) is small and changing fast, and the painted cylinder's
    # light-driven amplitude rises from x1.40 to x2.05 -- across the x2.00 bar.
    # The real frames sit at 178.2 deg, i.e. NEARER TO C THAN TO B, so the C
    # column is evidence about the shipping configuration and not a curiosity.
    # It is reported in full for that reason.
    print(f">> the two suns are {scr:.1f} deg apart ON SCREEN "
          f"({abs(SUN_BEARINGS[sun_b] - SUN_BEARINGS['A']):.0f} deg on the "
          f"ground). The gate's own two candidates measure 178.2 deg on screen "
          f"on all eight witness frames.")
    print(f">> thresholds: dip >= {G.RELIEF_DIP_FLOOR} and >= control + "
          f"{G.RELIEF_MARGIN}; fine >= x{G.FINE_OVER_CONTROL}; light >= "
          f"x{G.LIGHT_OVER_CONTROL}. rho is printed but NOT gated.")

    st = {}
    for nm in ORDER2:
        pa, pb = os.path.join(dir_a, nm + ".png"), os.path.join(dir_b, nm + ".png")
        if not (os.path.exists(pa) and os.path.exists(pb)):
            print(f"   (missing {nm}: A={os.path.exists(pa)} "
                  f"{sun_b}={os.path.exists(pb)})")
            continue
        st[nm] = _panel_stats(G, pa, pb, sun_rc)

    hdr = (f"{'panel':<24}{'truth':>8}{'dip':>8}{'fine/c':>8}{'light/c':>9}"
           f"{'rho':>9}{'dipLD':>8}{'still%':>8}  OLD -> NEW")
    print("\n" + hdr)
    print("  " + "-" * (len(hdr) - 2))
    rows, wrong_old, wrong_new = [], [], []
    for nm in ORDER2:
        s = st.get(nm)
        if not s or s.get("dip") is None:
            continue
        ctl = st.get(CONTROL_FOR[_shape_of(nm)]) or {}
        foc = (s["fine"] / ctl["fine"]) if (s.get("fine") and ctl.get("fine")) \
            else float("nan")
        loc = (s["light_pct"] / ctl["light_pct"]) \
            if (s.get("light_pct") and ctl.get("light_pct")) else float("nan")
        dip_ok = (s["dip"] >= G.RELIEF_DIP_FLOOR
                  and s["dip"] >= (ctl.get("dip") or 0.0) + G.RELIEF_MARGIN)
        fine_ok = foc == foc and foc >= G.FINE_OVER_CONTROL
        amp_ok = loc == loc and loc >= G.LIGHT_OVER_CONTROL
        # rho is MEASURED AND PRINTED, and deliberately not part of the rule.
        # It reads well -- +0.99 means "the same picture under both suns" --
        # but it puts a smooth cylinder (+0.9193) in the same bin as paint and
        # 3 mm chamfered bolt heads (+0.1003) outside the relief bin, because
        # real relief carries a light-INVARIANT component of its own: a rib's
        # flat top is bright whichever side the sun is on. See the note on
        # LIGHT_OVER_CONTROL in item_gate.py.
        inv_ok = s.get("rho") is not None and s["rho"] <= 0.0
        old = dip_ok
        new = dip_ok and fine_ok and amp_ok
        want = TRUTH2[nm] == "relief"
        if old != want:
            wrong_old.append(nm)
        if new != want:
            wrong_new.append(nm)
        print(f"  {nm:<22}{TRUTH2[nm]:>8}{s['dip']:>8.4f}{foc:>8.2f}"
              f"{loc:>9.2f}{(s.get('rho') if s.get('rho') is not None else float('nan')):>9.4f}"
              f"{(s.get('dip_light') if s.get('dip_light') is not None else float('nan')):>8.4f}"
              f"{(s.get('still_pct') or float('nan')):>8.3f}  "
              f"{'RELIEF' if old else 'reject':<7}-> "
              f"{'RELIEF' if new else 'reject':<7}"
              f"{'' if new == want else '   *** WRONG'}")
        rows.append({"panel": nm, "truth": TRUTH2[nm], "height_mm": HEIGHT_MM2[nm],
                     "dip": s["dip"], "fine_over_control": round(foc, 4),
                     "light_over_control": round(loc, 4), "rho": s.get("rho"),
                     "light_pct": s.get("light_pct"),
                     "still_pct": s.get("still_pct"),
                     "dip_light_driven": s.get("dip_light"),
                     "px_both": s["px_both"], "px_a": s["px_a"],
                     "px_b": s["px_b"],
                     "alpha_agreement": s["alpha_agreement"],
                     "clauses": {"dip": dip_ok, "fine": fine_ok,
                                 "light_amplitude": amp_ok},
                     "rho_would_have_said": ("relief" if inv_ok else "paint"),
                     "separates": None,
                     "old_verdict": "RELIEF" if old else "reject",
                     "new_verdict": "RELIEF" if new else "reject",
                     "correct": new == want})

    print(f"\n  the DIP ALONE gets {len(rows) - len(wrong_old)}/{len(rows)} "
          f"right; wrong on {wrong_old or 'nothing'}")
    print(f"  the COMBINED RULE gets {len(rows) - len(wrong_new)}/{len(rows)} "
          f"right; wrong on {wrong_new or 'nothing'}")

    # ---- SCORED THE WAY THE FAULT WAS SHAPED -----------------------------
    # R2-060 is an OVER-detection: paint passing as relief. So the question
    # that decides whether it is repaired is whether every PAINT panel and
    # every SMOOTH panel is now rejected -- and, separately, whether the new
    # clause ever costs a relief panel that the SHIPPED gate would have
    # accepted. Those are different questions and conflating them into one
    # score hides both.
    #
    # THE SECOND ONE IS NOT A LET-OFF. A relief panel may be rejected only if
    # `fine_over_control` -- check 5, unchanged, shipped, nothing to do with
    # two lights -- already rejected it. Then the new clause is not the
    # deciding vote and the change is monotone in the safe direction. A relief
    # panel rejected by the light clause ALONE is a regression and fails this.
    by = {r["panel"]: r for r in rows}
    paint = [r for r in rows if r["truth"] == "paint"]
    smooth = [r for r in rows if r["truth"] == "smooth"]
    relief = [r for r in rows if r["truth"] == "relief"]
    paint_bad = [r["panel"] for r in paint if r["new_verdict"] == "RELIEF"]
    smooth_bad = [r["panel"] for r in smooth if r["new_verdict"] == "RELIEF"]
    relief_lost = [r for r in relief if r["new_verdict"] != "RELIEF"]
    sole = [r["panel"] for r in relief_lost if r["clauses"]["fine"]
            and r["clauses"]["dip"]]
    print(f"\n  PAINT panels rejected      {len(paint) - len(paint_bad)}/"
          f"{len(paint)}  {'' if not paint_bad else '*** STILL PASSING: '
          + str(paint_bad)}")
    print(f"  SMOOTH panels rejected     {len(smooth) - len(smooth_bad)}/"
          f"{len(smooth)}  {'' if not smooth_bad else '*** STILL PASSING: '
          + str(smooth_bad)}")
    print(f"  RELIEF panels accepted     {len(relief) - len(relief_lost)}/"
          f"{len(relief)}")
    for r in relief_lost:
        pre = ("ALSO fails the shipped fine_over_control at "
               f"x{r['fine_over_control']:.2f} -- the light clause is not the "
               "deciding vote" if not r["clauses"]["fine"] else
               "*** REJECTED BY THE LIGHT CLAUSE ALONE -- a regression")
        print(f"    {r['panel']:<22} light x{r['light_over_control']:.2f}, "
              f"fine x{r['fine_over_control']:.2f}: {pre}")
    print(f"  no relief panel lost to the new clause alone: "
          f"{'YES' if not sole else '*** NO: ' + str(sole)}")
    # ---- THE NULL IS NOT SCORED, IT IS SUBTRACTED -----------------------
    # An A/A2 pair is the SAME SUN at a different seed. There is no light
    # change in it, so "does this read as relief" is not a question it can be
    # asked -- and the RATIOS above are misleading on it, because the control's
    # light-driven band is also collapsed and a ratio of two tiny numbers is
    # still whatever it is. What the null is FOR is the ABSOLUTE collapse, and
    # the quadrature difference between the two pairings, which separates the
    # part that moved with the sun from the uncorrelated Monte-Carlo residual
    # that lands in the light half no matter what.
    if sun_b == "A2":
        pb = os.path.join(root, "truth_table_A_vs_B.json")
        if os.path.exists(pb):
            real = {r["panel"]: r for r in json.load(open(pb))["rows"]}
            print(f"\n  --- THE NULL: same sun, different seed ---")
            print(f"  {'panel':<24}{'truth':>7}{'light A/B':>11}{'light NULL':>12}"
                  f"{'collapse':>10}{'signal':>9}")
            for nm in ORDER2:
                if nm not in real or nm not in st or st[nm].get("light_pct") is None:
                    continue
                lab, ln = real[nm]["light_pct"], st[nm]["light_pct"]
                sig = math.sqrt(max(lab * lab - ln * ln, 0.0))
                print(f"  {nm:<22}{TRUTH2[nm]:>9}{lab:>11.4f}{ln:>12.4f}"
                      f"{lab / max(ln, 1e-9):>9.1f}x{sig:>9.4f}")
            print("  `collapse` is how much of the light-driven band goes away "
                  "when the light does not move; `signal` is the quadrature "
                  "difference, i.e. the part that is not render noise.")

    out = os.path.join(root, f"truth_table_A_vs_{sun_b}.json")
    json.dump({"sun_a_bearing": SUN_BEARINGS["A"],
               "sun_b_bearing": SUN_BEARINGS[sun_b],
               "thresholds": {"dip_floor": G.RELIEF_DIP_FLOOR,
                              "dip_margin": G.RELIEF_MARGIN,
                              "fine_over_control": G.FINE_OVER_CONTROL,
                              "light_over_control": G.LIGHT_OVER_CONTROL,
                              "rho": "reported, not gated"},
               "control_for": CONTROL_FOR, "rows": rows}, open(out, "w"),
              indent=1)
    print(f">> wrote {out}")
    good = not paint_bad and not smooth_bad and not sole and len(rows) >= 14
    return gate_exit.verdict("RELIEF_SEPARATOR_VALIDATED" if good
                             else "RELIEF_SEPARATOR_SUSPECT")


def _separator_clears(dip_alone_good):
    """Can RELIEF_CHECK_SUSPECT be cleared? R2-060.

    THE QUESTION THIS PANEL EXISTS TO ASK is whether the CHECK can tell paint
    from geometry -- not whether one term of it can. So the gating condition
    moved from `dip(c_rib_2mm) > dip(g_printed_aligned)` to the whole combined
    rule's verdict on the whole extended ladder, scored against a key written
    down before the frames existed.

    THIS IS NOT THE PANEL BEING RELAXED, and the difference matters. The decoy
    was not softened, moved, dimmed or re-rendered; it is still a four-vertex
    quad with z identically zero that beats real 2 mm ribs on the dip, that
    fact is still printed above in full, and the rule still has to REJECT it.
    What it now has to reject it WITH is the check, all of it. If the separator
    table is missing, incomplete, or wrong on a single panel, this returns False
    and the tool still says RELIEF_CHECK_SUSPECT. `dip_alone_good` is passed in
    and deliberately ignored for the verdict: a version of this that could be
    cleared by the dip term alone would be the old claim again.
    """
    p = os.path.join(R2, "render/relief_2light/truth_table_A_vs_B.json")
    print("\n  the DIP TERM alone separates the decoy: "
          + ("yes" if dip_alone_good else
             "NO -- and the combined rule is what now has to"))
    if not os.path.exists(p):
        print(f"  *** the separator has NOT been measured ({p} is absent). "
              "Build the two-light ladder with `-- --build2`, render all four "
              "sun variants, and score it with `-- --measure2`. Until then the "
              "check is not known to separate paint from geometry and this "
              "tool will keep saying so.")
        return False
    t = json.load(open(p))
    rows = t.get("rows") or []
    missing = [n for n in ORDER2 if n not in {r["panel"] for r in rows}]
    paint_bad = [r["panel"] for r in rows
                 if r["truth"] == "paint" and r["new_verdict"] == "RELIEF"]
    smooth_bad = [r["panel"] for r in rows
                  if r["truth"] == "smooth" and r["new_verdict"] == "RELIEF"]
    sole = [r["panel"] for r in rows if r["truth"] == "relief"
            and r["new_verdict"] != "RELIEF" and r["clauses"]["fine"]
            and r["clauses"]["dip"]]
    print(f"  the separator table has {len(rows)} of {len(ORDER2)} panels; "
          f"missing {missing or 'none'}")
    print(f"  paint still passing: {paint_bad or 'none'}; smooth still "
          f"passing: {smooth_bad or 'none'}; relief lost to the new clause "
          f"alone: {sole or 'none'}")
    if missing or paint_bad or smooth_bad or sole or not rows:
        print("  *** FAIL: the check is still not known to separate paint from "
              "geometry over its own ladder.")
        return False
    print("  PASS: every painted decoy is rejected -- the aligned one, the "
          "HIGH-CONTRAST one, the roughness-only one, and BOTH CURVED ones -- "
          "both smooth controls are rejected, and no real relief panel is lost "
          "to the new clause that the shipped fine-band clause was not already "
          "rejecting.")
    # ---- AND THE STRESS CASE, PRINTED WHETHER OR NOT IT AGREES -----------
    # This gates on the A/B table because A/B is THE GATE'S OWN ARRANGEMENT:
    # two side lights either side of the camera-to-subject axis, 116 deg apart
    # here against the gate's 140, NEITHER of them a back-light. The A/C pair is
    # a front light and a back light 180 deg apart, which the side-picker can
    # never choose -- it rejects the opposed sun precisely because it leaves the
    # subject in its own shadow, and four wave-1 items were failed by the rig
    # for exactly that. So C is a stress case and not the shipping geometry.
    #
    # IT IS PRINTED ANYWAY, EVERY RUN, because it is the one configuration in
    # which a painted panel still gets through, and a caveat that is only in a
    # report nobody re-reads is not a caveat.
    pc = os.path.join(R2, "render/relief_2light/truth_table_A_vs_C.json")
    if os.path.exists(pc):
        c = json.load(open(pc))
        cb = [(r["panel"], r["light_over_control"]) for r in c["rows"]
              if r["truth"] == "paint" and r["new_verdict"] == "RELIEF"]
        cl = [(r["panel"], r["light_over_control"]) for r in c["rows"]
              if r["truth"] == "relief" and r["new_verdict"] != "RELIEF"
              and r["clauses"]["fine"] and r["clauses"]["dip"]]
        print(f"  STRESS CASE (sun C, a true 180 deg reversal, NOT a geometry "
              f"the gate can stage): paint still passing {cb or 'none'}; "
              f"relief lost to the light clause alone {cl or 'none'}.")
        if cb or cl:
            print("  ^ that is the measured boundary of this repair. On a "
                  "SMOOTH CONVEX painted body under opposed suns the region lit "
                  "in both frames collapses to a grazing band, and the paint's "
                  "light-driven amplitude crosses the x2.00 bar. Not tuned "
                  "around: raising the bar to x3.00 would reject real 8 mm ribs "
                  "at x2.83 in the same column.")
    else:
        print("  (the sun-C stress case has not been measured; run "
              "`--measure2 --sun-b C`)")
    return True


def selftest_two_light():
    """Synthetic controls for `two_light_bands`, where the answer is known.

    Four cases with no renderer in them at all, so a failure here is a fault in
    the STATISTIC and cannot be blamed on a scene. Every one of them has to come
    out a particular way or the separator does not mean what it claims:

      paint, flat            rho -> +1, and the band sits almost entirely in the
                             half that did NOT move
      relief                 rho -> -1, and the band sits in the half that DID
      structureless          rho -> 0 and light -> the noise floor: two
                             independent renders of nothing correlate at nothing
      PAINT ON CURVATURE     the case the flat ladder cannot pose. Same painted
                             stripes, two DIFFERENT smooth irradiance fields --
                             which is what a curved surface does to paint when
                             the sun moves. In log luminance it must come out
                             indistinguishable from the flat painted case; the
                             same pair measured WITHOUT the log is printed
                             beside it to show the leak the log is removing.
    """
    G = load_gate()
    rng = np.random.default_rng(7)
    N = 600
    m = np.zeros((N, N), bool)
    m[20:N - 20, 20:N - 20] = True
    _yy, xx = np.mgrid[0:N, 0:N]
    stripe = 0.5 + 0.25 * np.sign(np.sin(2 * np.pi * xx / 12.0))
    dip = 0.10 * np.sin(2 * np.pi * xx / 12.0)
    cA = 0.55 + 0.35 * np.cos((xx - N / 2) / N * 2.2)
    cB = 0.55 + 0.35 * np.cos((xx - N / 2) / N * 2.2 + 1.1)
    nz = lambda s: rng.normal(0, s, (N, N))                      # noqa: E731

    def run(name, A, B, want):
        st, _ = G.two_light_bands(A, B, m, 0.02 * float(A[m].mean()))
        good = want(st)
        print(f"  {name:<34} rho {st['rho']:+.4f}  light {st['light_pct']:8.4f}"
              f"  still {st['still_pct']:8.4f}   {'PASS' if good else '*** FAIL'}")
        return good, st

    ok = True
    good, _ = run("paint, flat surface", stripe * (1 + nz(0.002)),
                  stripe * (1 + nz(0.002)),
                  lambda s: s["rho"] > 0.9 and s["still_pct"] > 10 * s["light_pct"])
    ok &= good
    good, _ = run("relief, dipole inverts", (0.5 + dip) * (1 + nz(0.002)),
                  (0.5 - dip) * (1 + nz(0.002)),
                  lambda s: s["rho"] < -0.9 and s["light_pct"] > 5 * s["still_pct"])
    ok &= good
    good, _ = run("structureless, noise only", 0.5 * (1 + nz(0.002)),
                  0.5 * (1 + nz(0.002)),
                  lambda s: abs(s["rho"]) < 0.1 and s["light_pct"] < 0.5)
    ok &= good
    A, B = stripe * cA * (1 + nz(0.002)), stripe * cB * (1 + nz(0.002))
    good, st = run("paint on curvature (log, shipped)", A, B,
                   lambda s: s["rho"] > 0.9
                   and s["still_pct"] > 10 * s["light_pct"])
    ok &= good
    r = 2
    mm = G._erode(m, 3 * r)
    a, b = G._dog(A, r), G._dog(B, r)
    x, y = a[mm] - a[mm].mean(), b[mm] - b[mm].mean()
    mu = float(A[mm].mean())
    lin = (float((x * y).mean() / (x.std() * y.std())),
           100 * float((0.5 * (a - b))[mm].std()) / mu,
           100 * float((0.5 * (a + b))[mm].std()) / mu)
    print(f"  {'  the same pair WITHOUT the log':<34} rho {lin[0]:+.4f}  "
          f"light {lin[1]:8.4f}  still {lin[2]:8.4f}   <- the paint leaks into "
          "the light half")
    leak = lin[1] / max(st["light_pct"], 1e-9)
    good = leak > 3.0
    ok &= good
    print(f"  the log removes {leak:.1f}x of that leak   "
          f"{'PASS' if good else '*** FAIL: the log is not doing the job claimed'}")
    return gate_exit.verdict("TWO_LIGHT_SELFTEST_PASSES" if ok
                             else "TWO_LIGHT_SELFTEST_FAILS")


PASSING = ["armco_post", "catch_fence_post", "crew_figure", "gantry_truss",
           "heras_fence_panel", "pit_wall_unit", "pont_girder",
           "tyre_wall_tyre"]


def measure_items(items):
    """Re-run the WHOLE shipped analyser on each item's two-sun witness pair.

    `item_gate.analyse()` itself, called with the flip frame, so the numbers
    below are the gate's numbers and not a second implementation of them. The
    reproduction of `relief_subject` against the shipped gate.json is asserted
    first: if the dip does not come back, the mask is not the gate's mask and
    nothing beside it is comparable.
    """
    G = load_gate()
    out = []
    for it in items:
        wdir = os.path.join(R2, "render/gate_witness", it)
        png = os.path.join(wdir, "witness.png")
        flip = os.path.join(wdir, "witness_flip.png")
        spec_p = os.path.join(wdir, "witness_spec.json")
        if not (os.path.exists(png) and os.path.exists(spec_p)):
            print(f"   ({it}: no witness frame)")
            continue
        spec = json.load(open(spec_p))
        img, notes = G.analyse(png, spec,
                               flip_png=flip if os.path.exists(flip) else None)
        rec = {"item": it, "notes": notes}
        if img is None:
            rec["error"] = notes
            out.append(rec)
            continue
        gj = os.path.join(R2, f"render/items/{it}/gate.json")
        shipped = None
        if os.path.exists(gj):
            shipped = (json.load(open(gj)).get("witness", {}).get("image", {})
                       .get("relief_subject"))
        rec.update({
            "shipped_relief_subject": shipped,
            "reproduced": img.get("relief_subject"),
            "relief_control": img.get("relief_control"),
            "gate_bar": (round(img["relief_control"] + G.RELIEF_MARGIN, 5)
                         if img.get("relief_control") is not None else
                         G.RELIEF_DIP_FLOOR),
            "fine_over_control": img.get("fine_over_control"),
            "two_light": img.get("two_light"),
            "why_two_light": img.get("why", {}).get("two_light"),
        })
        if shipped is not None and rec["reproduced"] is not None:
            rec["reproduction_delta"] = round(rec["reproduced"] - shipped, 6)
        out.append(rec)

    print(f"\n{'item':<22}{'shipped':>9}{'repro':>9}{'bar':>8}{'fine/c':>8}"
          f"{'light/c':>9}{'rho':>9}{'dipLD':>8}{'still%':>8}")
    for r in out:
        tl = r.get("two_light") or {}
        f = lambda v, w=9, p=4: (f"{v:>{w}.{p}f}" if isinstance(v, (int, float))
                                 else f"{'--':>{w}}")
        print(f"  {r['item']:<20}{f(r.get('shipped_relief_subject'))}"
              f"{f(r.get('reproduced'))}{f(r.get('gate_bar'), 8)}"
              f"{f(r.get('fine_over_control'), 8, 2)}"
              f"{f(tl.get('light_over_control'), 9, 2)}"
              f"{f(tl.get('rho'))}{f(tl.get('dip_light_driven'), 8)}"
              f"{f(tl.get('still_pct'), 8, 3)}")
        if r.get("why_two_light"):
            print(f"      two-light NOT MEASURED: {r['why_two_light']}")
        if r.get("notes"):
            print(f"      frame notes: {r['notes']}")
    p = os.path.join(R2, "render/relief_2light/items_two_light.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(out, open(p, "w"), indent=1, default=str)
    print(f">> wrote {p}")
    return 0


def _radial(ob, v):
    """(along-axis-removed) radius components of a vertex of a built cylinder."""
    sx, sy = _sun_ground(SUN_BEARING_DEG)
    ax = mathutils.Vector((-sy, sx, 0.0)).normalized()
    p = mathutils.Vector(v.co)
    q = p - ax * p.dot(ax)
    return (q.length, 0.0)


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(R2, "render/relief_control"))
    ap.add_argument("--build2", action="store_true",
                    help="R2-060. Build the three sun variants of the EXTENDED "
                         "ladder -- the shipped seven panels plus a "
                         "high-contrast painted decoy, a roughness-only "
                         "painted decoy, and five CURVED panels -- and stop.")
    ap.add_argument("--selftest", action="store_true",
                    help="R2-060. Synthetic controls for the two-light "
                         "separator -- no renderer, known answers, including "
                         "the painted-curvature case the flat ladder cannot "
                         "pose.")
    ap.add_argument("--items", nargs="*", default=None,
                    help="R2-060. Re-run the shipped analyser on each item's "
                         "two-sun witness pair. No names = all eight relief "
                         "passes.")
    ap.add_argument("--measure2", action="store_true",
                    help="R2-060. Score the combined rule over the extended "
                         "ladder and print the truth table.")
    ap.add_argument("--dir2", default=os.path.join(R2, "render/relief_2light"))
    ap.add_argument("--sun-b", default="B", choices=["A2", "B", "C"],
                    help="which second sun the truth table is scored with. B "
                         "is the gate's own runner-up side and is what ships; "
                         "C is a true 180 deg reversal and is reported only to "
                         "bound how much the mirror being imperfect costs. A2 "
                         "is sun A at a different seed -- the NULL, where the "
                         "light does not move at all.")
    ap.add_argument("--augment", action="store_true",
                    help="add the ALIGNED decoy (panel g) to the control blend "
                         "and stop. Idempotent. Re-run after any rebuild of "
                         "tools/relief_positive_control.py, which does not know "
                         "about panel (g).")
    a = ap.parse_args(argv)

    if a.selftest:
        return selftest_two_light()
    if a.items is not None:
        return measure_items(a.items or PASSING)
    if a.build2:
        return build_two_light()
    if a.measure2:
        return measure_two_light(a.dir2, a.sun_b)

    if a.augment:
        return augment_with_panel_g()

    G = load_gate()
    print(f">> imported relief_anisotropy from tools/item_gate.py")
    print(f">> RELIEF_MARGIN {G.RELIEF_MARGIN}  RELIEF_DIP_FLOOR "
          f"{G.RELIEF_DIP_FLOOR}  RELIEF_CONTROL_SANE {G.RELIEF_CONTROL_SANE}")

    sun_rc = sun_screen_dir()
    print(f">> sun screen dir (row, col) = ({sun_rc[0]:+.3f}, {sun_rc[1]:+.3f})")

    rows = []
    for name in ORDER:
        p = os.path.join(a.dir, name + ".png")
        if not os.path.exists(p):
            print(f"   (missing {name}.png)")
            continue
        lum, alpha = load_png(p)
        mask = alpha > 0.5
        if int(mask.sum()) < 5000:
            print(f"   ({name}: only {int(mask.sum())} subject px)")
            continue
        dip, detail = G.relief_anisotropy(lum, mask, sun_rc, r=2)
        ang, coh = structure_angle(G, lum, mask, r=2)
        rows.append((name, HEIGHT_MM[name], dip, detail, int(mask.sum()),
                     ang, coh))

    sun_deg = math.degrees(math.atan2(sun_rc[0], sun_rc[1]))
    print(f"\n{'panel':<24}{'height':>9}{'dip':>10}{'along':>9}{'across':>9}"
          f"{'lag':>6}{'featdeg':>9}{'coh':>7}{'px':>10}")
    for name, hmm, dip, detail, npx, ang, coh in rows:
        if dip is None:
            print(f"  {name:<22}{hmm:>8.1f}mm   NOT MEASURED "
                  f"({detail.get('reason')})")
            continue
        print(f"  {name:<22}{hmm:>8.1f}mm{dip:>10.4f}"
              f"{detail.get('dip_along', float('nan')):>9.4f}"
              f"{detail.get('dip_across', float('nan')):>9.4f}"
              f"{detail.get('best_lag_px', 0):>6}{ang:>9.2f}{coh:>7.3f}"
              f"{npx:>10,}")
    print(f"  (sun runs at {sun_deg:+.2f} deg on screen; `featdeg` is the "
          f"direction the band-passed features RUN)")

    d = {n: v for n, _h, v, _dd, _p, _a, _c in rows if v is not None}

    print("\n--- VERDICT ---")
    ok = True

    if "a_flat_0mm" in d and "d_rib_8mm" in d:
        found = d["d_rib_8mm"] - d["a_flat_0mm"]
        good = found > G.RELIEF_MARGIN
        ok &= good
        print(f"  8 mm ribs over flat plate      {found:+.4f}  "
              f"(needs > {G.RELIEF_MARGIN})  {'PASS' if good else '*** FAIL: '
              'the check is BLIND to real relief'}")

    if "f_printed_0mm" in d and "a_flat_0mm" in d:
        decoy = d["f_printed_0mm"] - d["a_flat_0mm"]
        good = decoy <= G.RELIEF_MARGIN
        ok &= good
        print(f"  printed decoy over flat plate  {decoy:+.4f}  "
              f"(needs <= {G.RELIEF_MARGIN})  {'PASS' if good else '*** FAIL: '
              'the check scores PAINT as RELIEF'}")

    if "f_printed_0mm" in d and "c_rib_2mm" in d:
        sep = d["c_rib_2mm"] - d["f_printed_0mm"]
        good = sep > 0.0
        ok &= good
        print(f"  2 mm ribs over printed decoy   {sep:+.4f}  "
              f"(needs > 0)          {'PASS' if good else '*** FAIL: cannot tell '
              'geometry from paint'}")

    ladder = [d.get(k) for k in ("a_flat_0mm", "b_rib_0p5mm", "c_rib_2mm",
                                 "d_rib_8mm")]
    if all(v is not None for v in ladder):
        mono = all(ladder[i] <= ladder[i + 1] + 1e-9 for i in range(3))
        ok &= mono
        print(f"  monotonic 0 -> 0.5 -> 2 -> 8 mm  "
              f"{[round(v,4) for v in ladder]}  "
              f"{'PASS' if mono else '*** FAIL: not monotonic in feature height'}")

    if "e_bolts_3mm" in d and "a_flat_0mm" in d:
        bolts = d["e_bolts_3mm"] - d["a_flat_0mm"]
        good = bolts > G.RELIEF_MARGIN
        ok &= good
        print(f"  3 mm chamfered bolts over flat {bolts:+.4f}  "
              f"(needs > {G.RELIEF_MARGIN})  {'PASS' if good else '*** FAIL: '
              'misses the exact feature marshal_post_deck was failed for'}")

    # -----------------------------------------------------------------------
    # R2-060 -- THE ALIGNED DECOY. Reported here whatever it says; gating only
    # when GATE_ON_ALIGNED_DECOY is set. See the comment on that constant.
    # -----------------------------------------------------------------------
    print("\n--- R2-060: PAINT vs GEOMETRY "
          f"({'GATING' if GATE_ON_ALIGNED_DECOY else 'MEASURED AND REPORTED, '
             'NOT GATING'}) ---")
    if PANEL_G not in d:
        print(f"  {PANEL_G}.png is NOT PRESENT. The control has not been asked "
              "the one question it was rebuilt to answer.")
        print("  Add the panel with `-- --augment` and render "
              f"CAM_RC_{PANEL_G} into --dir.")
        if GATE_ON_ALIGNED_DECOY:
            ok = False
            print("  *** FAIL: this row GATES and it was not measured.")
    else:
        g = d[PANEL_G]
        for other, label in (("a_flat_0mm", "flat plate"),
                             ("c_rib_2mm", "2 mm ribs"),
                             ("d_rib_8mm", "8 mm ribs"),
                             ("f_printed_0mm", "the 32 deg-off decoy")):
            if other in d:
                print(f"  aligned decoy vs {label:<21}"
                      f"{g - d[other]:+.4f}   (g {g:.4f} vs {d[other]:.4f})")
        if "c_rib_2mm" in d:
            sep = d["c_rib_2mm"] - g
            good = sep > 0.0
            verdict_txt = ("PASS" if good else
                           "*** A FLAT QUAD OUTSCORES 2 mm OF REAL GEOMETRY. "
                           "The check cannot separate a painted step from a "
                           "lip-and-shadow.")
            print(f"  2 mm ribs over ALIGNED decoy   {sep:+.4f}  "
                  f"(needs > 0)          {verdict_txt}")
            if not good:
                print("  ^ THE DIP TERM ALONE STILL CANNOT DO THIS, and it is "
                      "not expected to. `relief_anisotropy` is unchanged: it "
                      "measures the SPACING of a bipolar pair, and a painted "
                      "step and a lip-and-shadow have the same spacing. What "
                      "changed is that the dip is no longer the whole check.")
            if GATE_ON_ALIGNED_DECOY:
                ok &= _separator_clears(good)

    if not ok:
        print(">> 21 of the gate's 28 verdicts rest on this check. Do not trust "
              "them until this passes.")
    return gate_exit.verdict("RELIEF_CHECK_VALIDATED" if ok
                             else "RELIEF_CHECK_SUSPECT")


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised; guard() makes the verdict
    # main() returns the process status, and an exception a status 2.
    gate_exit.guard(main, tool="relief_control_measure")
