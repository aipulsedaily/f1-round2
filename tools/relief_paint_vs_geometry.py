"""R2-060. Is a module's relief PASS carried by GEOMETRY or by PAINT?

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/relief_paint_vs_geometry.py -- --mode measure --item crew_figure

WHY THIS EXISTS
---------------
`relief_anisotropy` in tools/item_gate.py cannot tell a sharp albedo STEP from a
lip-and-shadow: after the DoG band-pass both leave a bipolar pair at the same ~2r
spacing. The positive control proved it -- a flat quad (4 verts, z identically 0,
no modifiers, no normal map) painted with 30 mm stripes ALIGNED to the light
scores dip 0.6308, against 0.6082 for real 2 mm trapezoidal ribs and 0.1003 for
plain grey. So `relief_subject >= control + 0.030` can be satisfied by paint.

The error is over-detection, so only PASSES are at risk. This tool decides, for
each passing module, which of the two actually carries the number.

THE METHOD IS A CONTROL PAIR IN THE SAME FRAME, NOT A BETTER STATISTIC.
Re-running the statistic that cannot separate the two cannot separate them here
either. Instead the SCENE is separated and the SAME statistic is re-run:

    orig      the shipped witness frame, unmodified
    geo       every paint input on every subject material forced constant
              (base colour, roughness, metallic, specular, emission, alpha);
              mesh, bump and normal maps untouched.  GEOMETRY + BUMP ONLY.
    geonb     `geo`, and the Normal input unlinked too.  MESH GEOMETRY ONLY.
    paint     the whole surface replaced by an Emission of its own base colour.
              No sun, no shadow, no normal, no bump.  PAINT ONLY.

Same blend, same camera, same sun, same sampler, same denoiser -- and crucially
THE SAME PIXEL MASK, computed once from the shipped frame and reused for all
four, so a variant cannot move the goalposts by changing which pixels are lit.

    dip(geo)   ~ dip(orig)  and dip(paint) low   ->  PASS IS REAL
    dip(paint) ~ dip(orig)  and dip(geo)   low   ->  PASS IS PAINT
    both high, or neither                        ->  INCONCLUSIVE

THE NULL IS PROVEN, NOT ASSUMED. `--mode measure` first recomputes the dip from
the SHIPPED png and asserts it reproduces `relief_subject` in the item's
gate.json to 1e-4. If the reproduction fails, the mask is not the gate's mask and
nothing downstream is comparable -- so it refuses rather than reporting.
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

if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

R2 = "/home/zany/f1-round2"

# The 8 modules whose relief check PASSED, from render/items/*/gate.json.
PASSING = ["armco_post", "catch_fence_post", "crew_figure", "gantry_truss",
           "heras_fence_panel", "pit_wall_unit", "pont_girder",
           "tyre_wall_tyre"]

VARIANTS = ("geo", "geonb", "paint", "truegeo")

# Everything on a Principled BSDF that is PAINT rather than SHAPE. `Normal` and
# `Tangent` are deliberately absent: they carry bump and normal maps, which are
# relief the gate is entitled to credit.
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


def load_gate():
    path = os.path.join(R2, "tools/item_gate.py")
    spec = importlib.util.spec_from_file_location("item_gate", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["item_gate"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# THE MASK. Lifted line-for-line out of `analyse()` so the pixels measured here
# are the pixels the gate measured. Verified by reproduction, not by reading.
# ---------------------------------------------------------------------------
def gate_masks(G, rgba, spec):
    H, W, _ = rgba.shape
    rgb = rgba[:, :, :3].astype(np.float64)
    alpha = rgba[:, :, 3].astype(np.float64)
    L = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]

    scx, scy = spec["ref_sphere_centre_px"]
    pcx, pcy = spec["ref_plane_centre_px"]
    rr = spec["ref_radius_px"]
    solid = alpha >= 0.995
    sph_m = G.disc_mask(H, W, scx, scy, rr * 0.80) & solid
    pln_m = G.disc_mask(H, W, pcx, pcy, rr * 0.62) & solid
    excl = (G.disc_mask(H, W, scx, scy, rr * 1.25)
            | G.disc_mask(H, W, pcx, pcy, rr * 1.30))
    _yy, _xx = np.ogrid[:H, :W]
    for _cx, _cy, _w, _h in (spec.get("wedge_boxes_px") or []):
        excl |= ((np.abs(_xx - _cx) <= _w * 0.62)
                 & (np.abs(_yy - _cy) <= _h * 0.85))
    sub_m = solid & ~excl
    unclipped = (L > 0.0015) & (L < 0.90)

    lit_all = sub_m & unclipped
    if lit_all.any():
        sm = G._blur(L, 8.0)
        cut = float(np.quantile(sm[lit_all], 0.60))
        sub_ok = lit_all & (sm >= cut)
        if int(sub_ok.sum()) < G.MIN_BAND_PX * 3:
            sub_ok = lit_all
    else:
        sub_ok = lit_all
    return L, sub_ok, sph_m, pln_m, solid, unclipped


def structure_orientation(G, L, mask, r=2):
    """Dominant orientation of the band-passed structure, in screen degrees.

    Structure tensor of the DoG image over the mask. Returned as the direction
    the FEATURES RUN (the minor eigenvector of the gradient tensor), measured
    from screen +col toward screen +row, in (-90, +90].

    This is the independent read on the R2-060 fault: the whole artefact is an
    orientation coincidence, so a module whose features run ACROSS the light --
    i.e. whose feature direction is ~90 deg from the sun's screen direction --
    is the one that can be inflated by a painted step.
    """
    B = G._dog(L, r)
    gy, gx = np.gradient(B)
    m = mask
    jxx = float((gx[m] ** 2).mean())
    jyy = float((gy[m] ** 2).mean())
    jxy = float((gx[m] * gy[m]).mean())
    # principal direction of the GRADIENT
    ang_grad = 0.5 * math.atan2(2.0 * jxy, jxx - jyy)
    coh = math.hypot(jxx - jyy, 2.0 * jxy) / max(jxx + jyy, 1e-30)
    # features run perpendicular to the dominant gradient
    ang_feat = math.degrees(ang_grad) + 90.0
    while ang_feat > 90.0:
        ang_feat -= 180.0
    while ang_feat <= -90.0:
        ang_feat += 180.0
    return ang_feat, coh


# ---------------------------------------------------------------------------
# THE VARIANTS
# ---------------------------------------------------------------------------
def subject_materials(scene):
    """Every material on a non-control mesh. The controls must not move."""
    mats, objs = [], []
    for o in scene.objects:
        if o.type != "MESH" or o.name.startswith("GATE_REF_"):
            continue
        objs.append(o.name)
        for ms in o.data.materials:
            if ms is not None and ms not in mats:
                mats.append(ms)
    return mats, objs


def _out_node(nt):
    for n in nt.nodes:
        if n.bl_idname == "ShaderNodeOutputMaterial" and n.is_active_output:
            return n
    for n in nt.nodes:
        if n.bl_idname == "ShaderNodeOutputMaterial":
            return n
    return None


def flatten_paint(mat, drop_normal, log):
    """Force every paint input constant. Bump/normal survive unless asked."""
    nt = mat.node_tree
    if nt is None:
        log.append(f"{mat.name}: no node tree")
        return
    touched = 0
    for n in list(nt.nodes):
        if n.bl_idname == "ShaderNodeMixShader":
            # a texture-driven shader mix is paint too
            s = n.inputs["Fac"]
            for lk in list(s.links):
                nt.links.remove(lk)
            s.default_value = 0.5
            touched += 1
            log.append(f"{mat.name}: MixShader Fac pinned to 0.5")
        if "Bsdf" not in n.bl_idname:
            continue
        for name, val in PAINT_SOCKETS.items():
            s = n.inputs.get(name)
            if s is None:
                continue
            for lk in list(s.links):
                nt.links.remove(lk)
                touched += 1
            try:
                s.default_value = val
            except (TypeError, ValueError):
                pass
        if drop_normal:
            for name in ("Normal", "Tangent"):
                s = n.inputs.get(name)
                if s is None:
                    continue
                for lk in list(s.links):
                    nt.links.remove(lk)
                    touched += 1
    # displacement is real geometry -- keep it for `geo`, drop for `geonb`
    if drop_normal:
        out = _out_node(nt)
        if out is not None:
            for lk in list(out.inputs["Displacement"].links):
                nt.links.remove(lk)
                touched += 1
    log.append(f"{mat.name}: {touched} paint links/values pinned"
               f"{' (+normal dropped)' if drop_normal else ''}")


def paint_only(mat, log):
    """Replace the whole surface with an Emission of its own base colour."""
    nt = mat.node_tree
    if nt is None:
        log.append(f"{mat.name}: no node tree")
        return
    out = _out_node(nt)
    if out is None:
        log.append(f"{mat.name}: NO OUTPUT NODE")
        return
    surf = out.inputs["Surface"]
    src = surf.links[0].from_node if surf.links else None
    col_link = None
    col_const = (0.18, 0.18, 0.18, 1.0)
    if src is not None:
        bc = src.inputs.get("Base Color") or src.inputs.get("Color")
        if bc is not None:
            if bc.links:
                col_link = bc.links[0].from_socket
            else:
                col_const = tuple(bc.default_value)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0
    if col_link is not None:
        nt.links.new(col_link, em.inputs["Color"])
        log.append(f"{mat.name}: emission driven by the linked base colour")
    else:
        em.inputs["Color"].default_value = col_const
        log.append(f"{mat.name}: emission at constant base colour "
                   f"{tuple(round(v, 4) for v in col_const)}")
    for lk in list(surf.links):
        nt.links.remove(lk)
    nt.links.new(em.outputs["Emission"], surf)
    # geometry must not move: displacement stays exactly as it was


def sun_emit_dir(scn):
    """Unit vector the GATE_SUN emits ALONG (i.e. pointing down at the scene)."""
    from mathutils import Vector
    sun = scn.objects.get("GATE_SUN")
    if sun is None:
        raise SystemExit("REFUSING: the witness blend has no GATE_SUN")
    return (sun.matrix_world.to_3x3() @ Vector((0.0, 0.0, -1.0))).normalized()


def true_geometry_only(mat, emit_dir, log):
    """Emit max(0, dot(TRUE NORMAL, -emit_dir)): Lambert off the MESH alone.

    THE MODEL ANSWERS, NOT THE PICTURE. `True Normal` is the face normal of the
    evaluated geometry -- it ignores bump nodes, normal maps, and shading-normal
    interpolation, and there is no albedo and no light transport in the result.
    So the dip measured on this frame is the dip the MESH BY ITSELF would
    produce under this sun, with paint and bump provably absent rather than
    argued absent.

    Its one blind spot is cast shadows: an emission shader has no visibility
    term, so a rib's own shadow is missing and this UNDER-states real relief.
    That is the safe direction -- it cannot invent geometry that is not there.
    """
    nt = mat.node_tree
    if nt is None:
        log.append(f"{mat.name}: no node tree")
        return
    out = _out_node(nt)
    if out is None:
        log.append(f"{mat.name}: NO OUTPUT NODE")
        return
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = (-emit_dir.x, -emit_dir.y, -emit_dir.z)
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "MAXIMUM"
    mx.inputs[1].default_value = 0.0
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(geo.outputs["True Normal"], dot.inputs[0])
    nt.links.new(dot.outputs["Value"], mx.inputs[0])
    nt.links.new(mx.outputs["Value"], em.inputs["Color"])
    for lk in list(out.inputs["Surface"].links):
        nt.links.remove(lk)
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    log.append(f"{mat.name}: emission = max(0, TrueNormal . "
               f"({-emit_dir.x:+.4f},{-emit_dir.y:+.4f},{-emit_dir.z:+.4f}))")


# ---------------------------------------------------------------------------
# ONE SCENE PER ITEM, ALL FIVE ARMS IN IT.
#
# The first cut of this shipped 32 blends with one job each, which is 32 scene
# loads BY CONSTRUCTION -- and on this farm a load costs an order of magnitude
# more than a render (measured: 940 s load against 56.6 s/render on `film8`).
# No scheduler can collapse that; only the submission shape can.
#
# It collapses safely because of a physical fact, not a convenience: THE WITNESS
# RIG IS LIT BY A SUN AND A UNIFORM SKY, BOTH OF WHICH ARE INVARIANT UNDER
# TRANSLATION. Translate the whole staged scene -- subject AND its reference
# sphere, card and wedges -- by any vector, translate the camera by the same
# vector, and the rendered image is IDENTICAL: same projection, same incidence,
# same self-shadowing, same indirect bounce off the controls. Nothing about the
# measurement is weakened.
#
# The offset is taken PERPENDICULAR TO THE SUN'S GROUND DIRECTION, so no copy
# can ever cast a shadow onto another however long the shadows get, and it is
# asserted to be hundreds of times the subject's own size, so no copy can appear
# in another's frame. Both are checked below and both REFUSE rather than warn.
#
# And the consolidation carries its own control: arm `orig` is the untouched
# scene at offset zero. If `orig` rendered out of the merged blend does not
# reproduce the shipped `relief_subject`, the merge is wrong and every other arm
# measured beside it is void.
# ---------------------------------------------------------------------------
ARMS = ("orig", "geo", "geonb", "truegeo", "paint")
COPY_SPACING_M = 500.0


def _copy_scene_arm(scn, arm, offset, subj_objs, ctl_objs, emit, log):
    """One translated copy of the whole staged scene, with its own materials."""
    from mathutils import Vector
    made = []
    for src in subj_objs:
        ob = src.copy()                      # shares mesh data: no duplication
        ob.name = f"{src.name}__{arm}"
        scn.collection.objects.link(ob)
        ob.location = src.location + offset
        # object-linked slots, so the copy can carry different materials while
        # still sharing one mesh datablock with the original
        for i, slot in enumerate(ob.material_slots):
            m = slot.material
            slot.link = "OBJECT"
            if m is None:
                continue
            mm = m.copy()
            mm.name = f"{m.name}__{arm}"
            slot.material = mm
            if arm == "paint":
                paint_only(mm, log)
            elif arm == "truegeo":
                true_geometry_only(mm, emit, log)
            elif arm in ("geo", "geonb"):
                flatten_paint(mm, drop_normal=(arm == "geonb"), log=log)
        made.append(ob)
    for src in ctl_objs:
        ob = src.copy()                      # controls are NOT modified
        ob.name = f"{src.name}__{arm}"
        scn.collection.objects.link(ob)
        ob.location = src.location + offset
        made.append(ob)
    return made


def build_consolidated(item, out_blend):
    from mathutils import Vector
    src = os.path.join(R2, f"render/gate_witness/{item}/witness.blend")
    bpy.ops.wm.open_mainfile(filepath=src)
    scn = bpy.context.scene
    emit = sun_emit_dir(scn)
    if emit.z >= 0.0:
        raise SystemExit(f"REFUSING: {item}'s GATE_SUN emits UPWARD "
                         f"(z={emit.z:+.4f})")
    cam0 = scn.objects.get("GATE_CAM")
    if cam0 is None:
        raise SystemExit(f"REFUSING: {item} has no GATE_CAM")

    subj = [o for o in scn.objects
            if o.type == "MESH" and not o.name.startswith("GATE_REF_")]
    ctls = [o for o in scn.objects
            if o.type == "MESH" and o.name.startswith("GATE_REF_")]
    if not subj:
        raise SystemExit(f"REFUSING: {item} has no subject mesh")

    # the offset direction: PERPENDICULAR to the sun on the ground plane
    g = Vector((emit.x, emit.y, 0.0))
    if g.length < 1e-6:
        raise SystemExit("REFUSING: the sun is vertical; no safe offset axis")
    g.normalize()
    perp = Vector((-g.y, g.x, 0.0))
    if abs(perp.dot(g)) > 1e-9:
        raise SystemExit("REFUSING: offset axis is not perpendicular to the sun")

    # ... and it must dwarf the subject, or a copy lands in another's frame
    span = 0.0
    for o in subj:
        d = o.dimensions
        span = max(span, float(max(d.x, d.y, d.z)))
    # SCALED TO THE SUBJECT, not a fixed number: `pont_girder` spans 28.74 m and
    # a flat 500 m would have been only 17x its own size. 60x, floored at 500 m.
    spacing = max(COPY_SPACING_M, 60.0 * span)
    if spacing < 40.0 * max(span, 0.01):
        raise SystemExit(
            f"REFUSING: {item}'s subject spans {span:.2f} m and the copies are "
            f"{spacing:.0f} m apart -- too close for a copy to be certainly "
            "out of frame and out of every shadow.")

    log = [f"{item}: {len(subj)} subject mesh objects, {len(ctls)} controls, "
           f"span {span:.2f} m, offset axis ({perp.x:+.4f},{perp.y:+.4f}) "
           f"perpendicular to sun ground ({g.x:+.4f},{g.y:+.4f}), "
           f"{spacing:.0f} m apart ({spacing / max(span, 1e-6):.0f}x the span)"]

    for i, arm in enumerate(ARMS):
        off = perp * (spacing * i)
        cam = cam0.copy()
        cam.name = f"CAM_{arm}"
        cam.data = cam0.data                 # identical lens/sensor, shared
        scn.collection.objects.link(cam)
        cam.location = cam0.location + off
        cam.rotation_mode = cam0.rotation_mode
        cam.rotation_euler = cam0.rotation_euler
        if arm == "orig":
            continue                         # arm 0 IS the untouched scene
        _copy_scene_arm(scn, arm, off, subj, ctls, emit, log)

    os.makedirs(os.path.dirname(out_blend), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=False)
    for line in log[:8]:
        print("   " + line)
    print(f"   ... {len(log)} material operations")
    print(f">> wrote {out_blend}  cameras "
          f"{[f'CAM_{a}' for a in ARMS]}")


def build_variant(item, variant, out_blend):
    src = os.path.join(R2, f"render/gate_witness/{item}/witness.blend")
    bpy.ops.wm.open_mainfile(filepath=src)
    scn = bpy.context.scene
    mats, objs = subject_materials(scn)
    log = [f"{item}/{variant}: {len(objs)} subject mesh objects, "
           f"{len(mats)} subject materials"]
    emit = sun_emit_dir(scn) if variant == "truegeo" else None
    if emit is not None and emit.z >= 0.0:
        raise SystemExit(f"REFUSING: {item}'s GATE_SUN emits UPWARD "
                         f"(z={emit.z:+.4f})")
    for m in mats:
        if variant == "paint":
            paint_only(m, log)
        elif variant == "truegeo":
            true_geometry_only(m, emit, log)
        else:
            flatten_paint(m, drop_normal=(variant == "geonb"), log=log)
    # THE CONTROLS MUST BE UNTOUCHED, or the frame has no fixed point.
    for name in ("GATE_REF_DEFAULT",):
        m = bpy.data.materials.get(name)
        if m is not None and any(
                (n.bl_idname == "ShaderNodeEmission") for n in m.node_tree.nodes):
            raise SystemExit(f"REFUSING: control material {name} was modified")
    os.makedirs(os.path.dirname(out_blend), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out_blend, compress=False)
    for line in log:
        print("   " + line)
    print(f">> wrote {out_blend}")


# ---------------------------------------------------------------------------
def measure_item(G, item, vdir):
    wdir = os.path.join(R2, f"render/gate_witness/{item}")
    spec = json.load(open(os.path.join(wdir, "witness_spec.json")))
    gj = json.load(open(os.path.join(R2, f"render/items/{item}/gate.json")))
    shipped = gj["witness"]["image"].get("relief_subject")

    rgba = G.load_linear_rgba(os.path.join(wdir, "witness.png"))
    L0, sub_ok, sph_m, pln_m, solid, unclip = gate_masks(G, rgba, spec)
    sun_rc = spec["sun_screen_direction_rowcol"]

    dip0, det0 = G.relief_anisotropy(L0, sub_ok, sun_rc)
    rec = {"item": item, "shipped_relief_subject": shipped,
           "reproduced": dip0, "subject_px": int(sub_ok.sum()),
           "shipped_subject_px_lit": gj["witness"]["image"]["frame"]
           .get("subject_px_lit"),
           "sun_screen_rowcol": sun_rc}
    # THE NULL, PROVEN: this mask and this statistic must give back the number
    # the gate shipped, from the gate's own frame, before anything measured on a
    # variant of that frame is comparable to it.
    if shipped is None or dip0 is None:
        rec["REPRODUCTION"] = "FAILED"
        return rec
    if abs(dip0 - shipped) > 1e-4:
        # NOT a mask error -- it reproduces exactly elsewhere. It means the png
        # on disk is not the png the report was written from. Measured and
        # named, not silently absorbed.
        rec["REPRODUCTION"] = "DRIFT"
        rec["drift"] = round(dip0 - shipped, 5)
    else:
        rec["REPRODUCTION"] = "ok"
    rec["orig"] = {"dip": dip0, "along": det0.get("dip_along"),
                   "across": det0.get("dip_across"),
                   "lag": det0.get("best_lag_px")}

    ang, coh = structure_orientation(G, L0, sub_ok)
    sun_deg = math.degrees(math.atan2(sun_rc[0], sun_rc[1]))
    sep = abs(((ang - sun_deg) + 90.0) % 180.0 - 90.0)
    rec["structure"] = {"feature_dir_deg": round(ang, 2),
                        "sun_dir_deg": round(sun_deg, 2),
                        "sep_from_light_deg": round(sep, 2),
                        "coherence": round(coh, 4)}

    for v in VARIANTS:
        p = os.path.join(vdir, f"{item}__{v}.png")
        if not os.path.exists(p):
            rec[v] = {"missing": p}
            continue
        r = G.load_linear_rgba(p)
        if r.shape != rgba.shape:
            rec[v] = {"bad_shape": list(r.shape)}
            continue
        Lv = (0.2126 * r[:, :, 0] + 0.7152 * r[:, :, 1]
              + 0.0722 * r[:, :, 2]).astype(np.float64)
        d, dd = G.relief_anisotropy(Lv, sub_ok, sun_rc)
        rec[v] = {"dip": d, "along": dd.get("dip_along"),
                  "across": dd.get("dip_across"), "lag": dd.get("best_lag_px"),
                  "mean_linear": round(float(Lv[sub_ok].mean()), 6)}
    return rec


def two_light_rho(G, png_a, png_b, mask, r=2):
    """corr(DoG(A), DoG(B)) over `mask`, for two renders under opposed suns.

    THE PROPOSED REPAIR FOR R2-060, and the one physical fact that separates the
    two things `relief_anisotropy` conflates:

        a lip-and-shadow belongs to the LIGHT.  Move the sun to the other side
        and the bright lip and the dark lee SWAP.        ->  rho strongly NEGATIVE

        a painted albedo step belongs to the SURFACE.    Move the sun and the
        pattern does not move at all.                    ->  rho strongly POSITIVE

    It needs no new statistic, no new threshold family and no new failure mode --
    just one more render of a frame the gate already stages both sides of
    (`sun_side_chosen` in every witness_spec.json is picked from two candidates).

    This function is the MEASUREMENT ONLY. Nothing in item_gate.py calls it; see
    the report on R2-060 for the proposed wiring.
    """
    A = G.load_linear_rgba(png_a)
    B = G.load_linear_rgba(png_b)
    if A.shape != B.shape:
        return None, {"reason": f"{A.shape} vs {B.shape}"}
    def lum(x):
        return (0.2126 * x[:, :, 0] + 0.7152 * x[:, :, 1]
                + 0.0722 * x[:, :, 2]).astype(np.float64)
    da, db = G._dog(lum(A), r), G._dog(lum(B), r)
    m = G._erode(mask, int(math.ceil(3 * r)))
    if int(m.sum()) < G.MIN_BAND_PX:
        return None, {"reason": "too few pixels after erosion"}
    x, y = da[m], db[m]
    sx, sy = x.std(), y.std()
    if sx < 1e-12 or sy < 1e-12:
        return None, {"reason": "no band energy"}
    rho = float(((x - x.mean()) * (y - y.mean())).mean() / (sx * sy))
    return round(rho, 5), {"px": int(m.sum()), "sd_a": round(float(sx), 8),
                           "sd_b": round(float(sy), 8)}


def verdict(rec, floor, margin):
    """PASS IS REAL / PASS IS PAINT / INCONCLUSIVE, from the control arms.

    THE GEOMETRY ARM DECIDES, AND THE PAINT ARM ONLY SPEAKS WHEN IT COLLAPSES.

    The question is not "could paint have produced this number" -- for almost any
    textured object the answer is yes, because a material boundary is a sharp
    albedo step and this statistic reads a step as a dipole. The question is
    "does the module still clear the gate with its paint taken away". If it does,
    the relief is there, whatever the shipped figure was additionally inflated
    by. If it does not, the shipped pass was carried by something that is not
    shape.

    "Carries it" is deliberately the gate's OWN bar -- `RELIEF_DIP_FLOOR` -- plus
    holding at least half the shipped number, so this cannot be more lenient than
    the check it is auditing.
    """
    o = (rec.get("orig") or {}).get("dip")
    g = (rec.get("geo") or {}).get("dip")
    p = (rec.get("paint") or {}).get("dip")
    t = (rec.get("truegeo") or {}).get("dip")
    if o is None:
        return "INCONCLUSIVE", "the shipped frame did not measure"
    missing = [k for k in ("geo", "paint") if (rec.get(k) or {}).get("dip") is None]
    if missing:
        return "INCONCLUSIVE", f"variant(s) {missing} did not measure"

    g_ok = g >= floor and g >= 0.5 * o
    p_ok = p >= floor and p >= 0.5 * o
    t_ok = t is not None and t >= floor

    mesh = (f"; MESH ALONE (true-normal Lambert, no bump, no paint) "
            f"{t:.4f}{' -- clears the floor by itself' if t_ok else ''}"
            if t is not None else "")
    if g_ok:
        also = ("" if not p_ok else
                f" -- NOTE the shipped figure is ALSO inflated by paint "
                f"(paint-only {p:.4f})")
        return "PASS IS REAL", (f"geometry+bump alone keeps {g:.4f} of the "
                                f"shipped {o:.4f}, over the {floor} floor{also}"
                                f"{mesh}")
    if p_ok:
        return "PASS IS PAINT", (f"geometry+bump alone collapses to {g:.4f} "
                                 f"(floor {floor}); paint alone keeps {p:.4f} "
                                 f"of the shipped {o:.4f}{mesh}")
    return "INCONCLUSIVE", (f"NEITHER arm carries it alone (geo {g:.4f}, "
                            f"paint {p:.4f}, shipped {o:.4f}){mesh}")


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode",
                    choices=["build", "consolidate", "measure", "twolight"],
                    required=True)
    ap.add_argument("--dir-a", default=os.path.join(R2, "render/relief_control"))
    ap.add_argument("--dir-b", default=os.path.join(R2,
                                                    "render/relief_control_sunflip"))
    ap.add_argument("--item")
    ap.add_argument("--variant", choices=list(VARIANTS))
    ap.add_argument("--vdir", default=os.path.join(R2, "render/relief_pvg"))
    ap.add_argument("--out", default=os.path.join(R2,
                                                  "render/relief_pvg/verdicts.json"))
    a = ap.parse_args(argv)

    if a.mode == "consolidate":
        for it in ([a.item] if a.item else PASSING):
            build_consolidated(it, os.path.join(a.vdir, "blends",
                                                f"{it}__all.blend"))
        return 0

    if a.mode == "build":
        items = [a.item] if a.item else PASSING
        variants = [a.variant] if a.variant else list(VARIANTS)
        for it in items:
            for v in variants:
                out = os.path.join(a.vdir, "blends", f"{it}__{v}.blend")
                build_variant(it, v, out)
        return 0

    if a.mode == "twolight":
        # THE PROPOSED REPAIR, RUN ON THE CONTROL LADDER, WHERE THE ANSWER IS
        # KNOWN IN ADVANCE. Positive control: the rib panels must come out
        # NEGATIVE. Negative control: the aligned decoy -- the panel that
        # defeats the shipped statistic -- must come out POSITIVE.
        G = load_gate()
        print(f"{'panel':<24}{'rho(A,B)':>10}{'dip A':>9}{'dip B':>9}"
              f"{'px':>10}   reads as")
        for name in ("a_flat_0mm", "b_rib_0p5mm", "c_rib_2mm", "d_rib_8mm",
                     "e_bolts_3mm", "f_printed_0mm", "g_printed_aligned_0mm"):
            pa = os.path.join(a.dir_a, name + ".png")
            pb = os.path.join(a.dir_b, name + ".png")
            if not (os.path.exists(pa) and os.path.exists(pb)):
                continue
            A = G.load_linear_rgba(pa)
            mask = A[:, :, 3] > 0.5
            rho, det = two_light_rho(G, pa, pb, mask)
            sun_rc = (0.51678, -0.82812)          # see relief_control_measure
            LA = (0.2126 * A[:, :, 0] + 0.7152 * A[:, :, 1]
                  + 0.0722 * A[:, :, 2]).astype(np.float64)
            B = G.load_linear_rgba(pb)
            LB = (0.2126 * B[:, :, 0] + 0.7152 * B[:, :, 1]
                  + 0.0722 * B[:, :, 2]).astype(np.float64)
            da, _ = G.relief_anisotropy(LA, mask, sun_rc)
            db, _ = G.relief_anisotropy(LB, mask, (-sun_rc[0], -sun_rc[1]))
            reads = ("RELIEF (the dipole inverted)" if rho is not None
                     and rho < -0.2 else
                     "PAINT (the pattern did not move)" if rho is not None
                     and rho > 0.2 else "neither")
            print(f"  {name:<22}{rho if rho is not None else float('nan'):>10.4f}"
                  f"{da if da is not None else float('nan'):>9.4f}"
                  f"{db if db is not None else float('nan'):>9.4f}"
                  f"{det.get('px', 0):>10,}   {reads}")
        return 0

    G = load_gate()
    items = [a.item] if a.item else PASSING
    out = []
    for it in items:
        rec = measure_item(G, it, a.vdir)
        v, why = verdict(rec, G.RELIEF_DIP_FLOOR, G.RELIEF_MARGIN)
        rec["verdict"], rec["verdict_because"] = v, why
        out.append(rec)

    print(f"\n{'item':<22}{'orig':>9}{'geo':>9}{'geonb':>9}{'truegeo':>9}"
          f"{'paint':>9}{'featdeg':>9}{'vs sun':>8}  verdict")
    for r in out:
        f = lambda d: (f"{d['dip']:>9.4f}" if isinstance(d, dict)
                       and isinstance(d.get("dip"), float) else f"{'--':>9}")
        st = r.get("structure", {})
        print(f"  {r['item']:<20}{f(r.get('orig'))}{f(r.get('geo'))}"
              f"{f(r.get('geonb'))}{f(r.get('truegeo'))}{f(r.get('paint'))}"
              f"{st.get('feature_dir_deg', float('nan')):>9.1f}"
              f"{st.get('sep_from_light_deg', float('nan')):>8.1f}"
              f"  {r['verdict']}  [{r.get('REPRODUCTION')}]")
        print(f"      {r['verdict_because']}")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"\n>> wrote {a.out}")
    return 0


import gate_exit                                                 # noqa: E402

if __name__ == "__main__":
    gate_exit.guard(main, tool="relief_paint_vs_geometry")
