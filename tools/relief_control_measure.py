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
"""

import argparse
import glob
import importlib.util
import math
import os
import sys

import numpy as np
import bpy
import mathutils

# Imported by path, not by package: this runs inside Blender's interpreter with
# whatever cwd the caller happened to have.
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402

R2 = "/home/zany/f1-round2"

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
# FLIP IT once the relief PASSES have been judged geometry-or-paint by
# `tools/relief_paint_vs_geometry.py` — those are the only verdicts this fault
# can have manufactured, and the flip is the honest state of the instrument
# afterwards. Do not flip it as a side effect of anything else: it turns a
# passing gate into a failing one for every caller that branches on $?.
# ---------------------------------------------------------------------------
GATE_ON_ALIGNED_DECOY = False

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


def sun_screen_dir():
    """The sun's direction projected into screen space, as (drow, dcol).

    The camera looks from (cx, -0.42, 0.62) at (cx, 0, 0): a level-ish view down
    the +Y axis. Screen +col is world +X, screen +row is world -Y (into the
    frame). The sun bearing is measured from +Y toward +X.
    """
    el = math.radians(SUN_ELEV_DEG)
    az = math.radians(SUN_BEARING_DEG)
    dx = math.cos(el) * math.sin(az)
    dy = -math.cos(el) * math.cos(az)
    return (-dy, dx)


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(R2, "render/relief_control"))
    ap.add_argument("--augment", action="store_true",
                    help="add the ALIGNED decoy (panel g) to the control blend "
                         "and stop. Idempotent. Re-run after any rebuild of "
                         "tools/relief_positive_control.py, which does not know "
                         "about panel (g).")
    a = ap.parse_args(argv)

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
            if GATE_ON_ALIGNED_DECOY:
                ok &= good
            elif not good:
                print("  ^ NOT GATING YET (GATE_ON_ALIGNED_DECOY is False). The "
                      "over-detection can only manufacture false PASSES, so "
                      "every FAIL verdict stands; the relief PASSES are the "
                      "ones this puts in doubt.")

    if not ok:
        print(">> 21 of the gate's 28 verdicts rest on this check. Do not trust "
              "them until this passes.")
    return gate_exit.verdict("RELIEF_CHECK_VALIDATED" if ok
                             else "RELIEF_CHECK_SUSPECT")


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised; guard() makes the verdict
    # main() returns the process status, and an exception a status 2.
    gate_exit.guard(main, tool="relief_control_measure")
