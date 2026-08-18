#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2366_paint_vs_geometry.py — is the paving's relief carried by RELIEF or by PAINT,
and are the three materials' fields actually different from each other?

WHY THIS EXISTS (R2-060). A four-vertex quad with z identically 0, painted with
stripes aligned to the light, scored dip 0.6308 on the relief check against real
2 mm ribs at 0.6082, because after a band-pass a sharp albedo STEP and a
lip-and-shadow leave the same bipolar signature. ALBEDO VARIATION IS NOT RELIEF.
The apron's shipped defect is exactly that shape — a per-cell albedo step
standing in for material — so it is not enough for the repair to score better;
it has to score better FOR THE RIGHT REASON.

THE METHOD IS TO SEPARATE THE SCENE, NOT TO FIND A CLEVERER STATISTIC. Re-running
a statistic that cannot tell the two apart will not tell them apart here either.
So the same measurement is run on arms that differ only in what has been taken
away:

    orig    the material as it ships
    geo     every PAINT input forced constant — Base Color, Roughness, Metallic,
            Specular, Emission. Normal is untouched. RELIEF ONLY.
    paint   the surface replaced by an Emission of its own base colour. No sun,
            no shadow, no normal. PAINT ONLY.
    flat    `geo` with the Normal unlinked as well. Neither. THE FLOOR, and the
            arm that makes the others mean something — without it a low `paint`
            number could just be a dark region.

Same scene, same camera, same sun, same sampler, same denoiser, and every plane
samples THE SAME OBJECT-SPACE REGION: the materials are driven from Object
coordinates, so moving a plane in world space carries its texture with it and
the arms stay comparable by construction rather than by hope.

    dip survives in `geo`   ->  the relief is REAL
    dip collapses in `geo`,
        survives in `paint` ->  it was PAINT

AND THE VARIETY HALF. The three paving materials share one relief ladder with
per-material scale and shift. If those did not take, all three would carry a
bit-identical field and the surfaces would tile into each other across the real
joints between them — the no-repeated-assets law in its procedural form, which
the world-level spam check cannot see because it counts meshes. The three `geo`
arms are cross-correlated here; identical fields give 1.000.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/r2366_paint_vs_geometry.py -- --mode build --out SCENE.blend
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/r2366_paint_vs_geometry.py -- --mode measure --exr R.exr

Blender 5.2 exits 0 on an uncaught script exception; judge on `STAGE RESULT`.
"""
import argparse
import math
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))

MATS = ["A_ConcSlab", "A_ConcApron", "A_ForecourtSlab"]
ARMS = ["orig", "geo", "paint", "flat"]

# Everything on a Principled BSDF that is PAINT rather than SHAPE. `Normal` is
# deliberately absent: it carries the relief the check is entitled to credit.
PAINT_SOCKETS = {
    "Base Color": (0.18, 0.18, 0.18, 1.0),
    "Roughness": 0.5,
    "Metallic": 0.0,
    "Specular IOR Level": 0.5,
    "Emission Color": (0.0, 0.0, 0.0, 1.0),
    "Emission Strength": 0.0,
}

#: The absolute bar the relief arm must clear, in peak-to-peak log luminance.
#: 0.010 p-p is about a 1 % radiance modulation — an order of magnitude below
#: `RELIEF_BANDS`' 0.35 floor, so it asks only "is there relief at all", which
#: is the question this tool is for. The BANDING question is answered by
#: `tools/r2366_relief_audit.py`, in the law's own units.
MARGIN_PP = 0.010

#: Scales the contract sun for this probe only. See the note beside the lamp.
SUN_SCALE = 0.04

TILE = 24.0          # metres of paving per panel — 4.5 `settle` cycles across
GAP = 4.0


def strip_paint(nt):
    """Force every paint input constant, leaving `Normal` alone."""
    n_cut = 0
    for nd in nt.nodes:
        if nd.bl_idname != "ShaderNodeBsdfPrincipled":
            continue
        for name, val in PAINT_SOCKETS.items():
            if name not in nd.inputs:
                continue                      # socket genuinely absent in 5.2
            sk = nd.inputs[name]
            for lk in list(sk.links):
                nt.links.remove(lk)
                n_cut += 1
            try:
                sk.default_value = val
            except Exception:                            # noqa: BLE001
                pass
    return n_cut


def cut_normal(nt):
    n_cut = 0
    for nd in nt.nodes:
        if nd.bl_idname != "ShaderNodeBsdfPrincipled":
            continue
        if "Normal" in nd.inputs:
            for lk in list(nd.inputs["Normal"].links):
                nt.links.remove(lk)
                n_cut += 1
    return n_cut


def to_paint(nt):
    """Replace the surface with an Emission of its own base colour."""
    import bpy                                            # noqa: F401
    bsdf = next((n for n in nt.nodes
                 if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    out = next((n for n in nt.nodes
                if n.bl_idname == "ShaderNodeOutputMaterial"), None)
    if bsdf is None or out is None:
        return False
    em = nt.nodes.new("ShaderNodeEmission")
    em.location = (bsdf.location[0], bsdf.location[1] - 400)
    em.inputs["Strength"].default_value = 1.0
    src = bsdf.inputs["Base Color"]
    if src.links:
        nt.links.new(src.links[0].from_socket, em.inputs["Color"])
    else:
        em.inputs["Color"].default_value = src.default_value
    for lk in list(out.inputs["Surface"].links):
        nt.links.remove(lk)
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return True


def build(out):
    import bpy
    import build_architecture as BA
    import world_contract as WC
    import film_exposure as FE
    from mathutils import Vector

    for fn in ("build_materials", "build_materials_extra"):
        getattr(BA, fn)()
    sc = bpy.context.scene

    missing = [m for m in MATS if m not in bpy.data.materials]
    if missing:
        print("STAGE RESULT: r2366_paint_vs_geometry FAIL (no %s)" % missing)
        sys.exit(1)

    # WHERE EACH MATERIAL IS PROBED, AND WHY IT IS NOT THE ORIGIN.
    #
    # These materials are driven from OBJECT coordinates and several of their
    # features are position-dependent. `A_ConcSlab` carries the pit-lane rubber
    # pick-up as a CLAMPED MapRange on object Y over 11..24.5 — below y = 11 it
    # clamps FULLY ON. Probed at the origin, as the first version of this tool
    # did, the paddock panel is solid rubber: its `orig` band power came back at
    # 1.3023 against a `geo` of 0.0329, i.e. the arm was dominated by a feature
    # the closing frame never shows, and `A_ForecourtSlab` landed in a flat patch
    # of its own 32 m mottle and read 0.0002.
    #
    # So the probe point is MEASURED: `tools/r2366_crop_owner.py` raycasts the
    # delivered frame and reports the median OBJECT-space coordinate at which
    # each material is actually sampled in the shot being fixed. The plane's
    # LOCAL vertices are centred there and the object's location cancels it, so
    # the panel sits in the display grid while its texture is read where the
    # film reads it.
    probe = {}
    cop = os.path.join(ROOT, "work", "r2366", "crop_owner_f2978.json")
    if os.path.exists(cop):
        probe = json.load(open(cop)).get("probe_object_xy", {})
    missing = [m for m in MATS if m not in probe]
    if missing:
        print("STAGE RESULT: r2366_paint_vs_geometry FAIL (no measured probe "
              "point for %s; run tools/r2366_crop_owner.py first — probing at "
              "the origin measures a region the film never shows)" % missing)
        sys.exit(1)
    for mn in MATS:
        print("[pvg] %-18s probed at object (%.2f, %.2f)"
              % (mn, probe[mn][0], probe[mn][1]))

    for i, mn in enumerate(MATS):
        rx, ry = probe[mn]
        for j, arm in enumerate(ARMS):
            me = bpy.data.meshes.new("PVG_%s_%s" % (mn, arm))
            h = TILE * 0.5
            me.from_pydata([(rx - h, ry - h, 0), (rx + h, ry - h, 0),
                            (rx + h, ry + h, 0), (rx - h, ry + h, 0)],
                           [], [(0, 1, 2, 3)])
            me.update()
            ob = bpy.data.objects.new("PVG_%s_%s" % (mn, arm), me)
            ob.location = Vector((j * (TILE + GAP) - rx,
                                  i * (TILE + GAP) - ry, 0.0))
            sc.collection.objects.link(ob)
            m = bpy.data.materials[mn]
            if arm != "orig":
                m = m.copy()
                m.name = "%s__%s" % (mn, arm)
                if arm == "geo":
                    strip_paint(m.node_tree)
                elif arm == "flat":
                    strip_paint(m.node_tree)
                    cut_normal(m.node_tree)
                elif arm == "paint":
                    to_paint(m.node_tree)
            me.materials.append(m)

    # THE CONTRACT'S OWN SUN, not an invented one.
    # SCALED DOWN SO NOTHING CLIPS, AND THAT IS MEASUREMENT-NEUTRAL HERE.
    # The contract sun is 115.754 W/m2; on ~0.5-albedo concrete at 12.47 deg
    # that is a radiance near 4.0, and the delivered image comes back CLIPPED AT
    # 1.0 AND QUANTISED TO 255 LEVELS. Measured on the clipped render, `flat`
    # read exactly 1.00002 with sd 0.000000 and every lit arm was saturated —
    # the tool was measuring the clip, not the surface, which is why two
    # genuinely different renders gave band powers identical to four decimals.
    # A uniform scale of the whole scene is an ADDITIVE OFFSET in log luminance
    # and the band-pass removes it exactly, so this changes no reported number
    # except by stopping the clip.
    sun_d = bpy.data.lights.new("PVG_SUN", 'SUN')
    sun_d.energy = WC.SUN_ENERGY * SUN_SCALE
    # the contract publishes the diameter in DEGREES; a getattr fallback onto an
    # invented radian constant would have been a quoted number wearing a
    # measurement's clothes, and 0.545 deg is not 0.00918 rad.
    sun_d.angle = math.radians(WC.SUN_ANGULAR_DIAM_DEG)
    sun = bpy.data.objects.new("PVG_SUN", sun_d)
    sc.collection.objects.link(sun)
    d = Vector(WC.SUN_DIR).normalized()
    sun.rotation_mode = 'QUATERNION'
    sun.rotation_quaternion = (-d).to_track_quat('-Z', 'Y')
    print("[pvg] sun %.3f W/m2 (contract %.3f x %.3f), dir %s"
          % (WC.SUN_ENERGY * SUN_SCALE, WC.SUN_ENERGY, SUN_SCALE,
             tuple(round(x, 4) for x in d)))

    # an ORTHO camera looking straight down: every panel is sampled at exactly
    # the same scale and incidence, so a difference between panels is the
    # material and nothing else.
    nx, ny = len(ARMS), len(MATS)
    cx = (nx - 1) * (TILE + GAP) * 0.5
    cy = (ny - 1) * (TILE + GAP) * 0.5
    cd = bpy.data.cameras.new("PVG_CAM")
    cd.type = 'ORTHO'
    cd.ortho_scale = nx * (TILE + GAP)
    cam = bpy.data.objects.new("PVG_CAM", cd)
    cam.location = Vector((cx, cy, 200.0))
    sc.collection.objects.link(cam)
    sc.camera = cam

    wd = bpy.data.worlds.new("PVG_W")
    sc.world = wd
    wd.use_nodes = True
    bn = wd.node_tree.nodes.get("Background")
    if bn:
        bn.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
        bn.inputs["Strength"].default_value = 0.0

    sc.render.engine = 'CYCLES'
    sc.render.resolution_x = sc.render.resolution_y = 2048
    sc.render.resolution_percentage = 100
    sc.cycles.samples = 512
    # DENOISER OFF. It is a low-pass filter aimed at the exact quantity here.
    sc.cycles.use_denoising = False
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'
    sc.view_settings.view_transform = 'Standard'
    FE  # exposure is irrelevant to a 32-bit linear EXR; kept imported for clarity

    # THE PANEL RECTS ARE COMPUTED HERE, FROM THE SCENE, AND WRITTEN DOWN.
    # The first version of this tool let `measure` assume the panels tiled the
    # frame; they do not — 4 columns and 3 rows do not fill a square render, so
    # every row window straddled the black background, log(1e-8) dominated the
    # band-pass and all four arms came back at p-p ~8 with geo/flat = 1.00. A
    # measurement that reads the same for `geo` and `flat` is not measuring
    # relief at all. The rects now come from the same numbers that placed the
    # planes, so they cannot drift apart.
    RES = sc.render.resolution_x
    S = cd.ortho_scale
    x_lo, y_hi = cx - S * 0.5, cy + S * 0.5
    lay = {"resolution": RES, "ortho_scale": S, "panels": {}}
    for i, mn in enumerate(MATS):
        for j, arm in enumerate(ARMS):
            px, py = j * (TILE + GAP), i * (TILE + GAP)
            # 12 % inset off each edge, so a panel's own border never enters
            k = TILE * 0.5 * 0.88
            u0 = (px - k - x_lo) / S * RES
            u1 = (px + k - x_lo) / S * RES
            v0 = (y_hi - (py + k)) / S * RES
            v1 = (y_hi - (py - k)) / S * RES
            lay["panels"]["%s|%s" % (mn, arm)] = [int(round(u0)), int(round(v0)),
                                                  int(round(u1)), int(round(v1))]
    lp = os.path.splitext(out)[0] + "_layout.json"
    json.dump(lay, open(lp, "w"), indent=1)
    print("[pvg] wrote %s" % lp)

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print("[pvg] %d panels, ortho %.1f m, %.2f px/m"
          % (nx * ny, cd.ortho_scale, RES / cd.ortho_scale))
    print("STAGE RESULT: r2366_paint_vs_geometry PASS (built %s)"
          % os.path.basename(out))


def _gauss(a, sigma):
    """Separable Gaussian blur, numpy only.

    Blender's bundled Python has no scipy, and the alternative — reading the EXR
    through PIL in the project venv — comes back as 8-bit 0..255, i.e. tone
    mapped and clamped, which destroys exactly the linear values being measured.
    Ten lines of separable convolution keeps the float data and the measurement
    in the same process.
    """
    import numpy as np
    r = max(1, int(round(sigma * 3.0)))
    x = np.arange(-r, r + 1, dtype=np.float64)
    k = np.exp(-0.5 * (x / sigma) ** 2)
    k /= k.sum()
    out = np.apply_along_axis(
        lambda m: np.convolve(np.pad(m, r, mode="reflect"), k, mode="valid"),
        0, a)
    return np.apply_along_axis(
        lambda m: np.convolve(np.pad(m, r, mode="reflect"), k, mode="valid"),
        1, out)


def measure_np(exr, jout=None, layout=None):
    """Read the EXR with Blender's own image API and score every panel."""
    import bpy
    import numpy as np

    img = bpy.data.images.load(exr)
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float64).reshape(h, w, 4)
    lum = a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722
    lum = lum[::-1]                        # Blender's origin is bottom-left
    if not layout or not os.path.exists(layout):
        raise SystemExit("the panel layout sidecar is required; it is written "
                         "by --mode build beside the .blend. Guessing the rects "
                         "is what made every arm read 8.1 with geo/flat 1.00.")
    lay = json.load(open(layout))
    if lay["resolution"] != w or w != h:
        raise SystemExit("layout says %d px, the EXR is %dx%d"
                         % (lay["resolution"], w, h))
    # REFUSE A CLIPPED RENDER. This tool measured one for three iterations: the
    # farm returned an image clamped to 1.0 at 255 levels, every lit arm
    # saturated, and the numbers were stable and plausible and meaningless.
    hi = float(lum.max())
    clip = float((lum >= 0.999).mean())
    print("[pvg] luminance max %.5f, %.4f %% of pixels at or above 0.999"
          % (hi, 100 * clip))
    if clip > 0.02:
        raise SystemExit("%.2f %% of the render is clipped at 1.0. Every lit "
                         "arm is saturated and the band powers below would be "
                         "measuring the clip. Lower SUN_SCALE and re-render."
                         % (100 * clip))

    def band_pp(g):
        """p-p of the band-passed LOG luminance — the same quantity the relief
        check bands, and log because paint on curvature leaks 40.9x more into a
        linear band-pass (R2-060)."""
        lg = np.log(np.maximum(g, 1e-8))
        b = _gauss(lg, 2.0) - _gauss(lg, 8.0)
        lo, hi = np.percentile(b, [1.0, 99.0])
        return float(hi - lo)

    res = {}
    panels = {}
    for mn in MATS:
        for arm in ARMS:
            x0, y0, x1, y1 = lay["panels"]["%s|%s" % (mn, arm)]
            g = lum[y0:y1, x0:x1]
            if g.size == 0 or g.max() <= 0.0:
                raise SystemExit("panel %s|%s is empty or black at %s — the "
                                 "layout does not describe this render"
                                 % (mn, arm, (x0, y0, x1, y1)))
            panels[(mn, arm)] = g
            res.setdefault(mn, {})[arm] = dict(
                mean=float(g.mean()), band_pp=band_pp(g))

    print("PAINT vs GEOMETRY — band-passed p-p of log luminance\n")
    print("  %-18s %9s %9s %9s %9s %11s"
          % ("material", "orig", "geo", "paint", "flat", "verdict"))
    verdicts = {}
    for mn in MATS:
        r = res[mn]
        fl = r["flat"]["band_pp"]
        ge, pa = r["geo"]["band_pp"], r["paint"]["band_pp"]
        # AN ABSOLUTE MARGIN, NOT A RATIO AGAINST THE FLOOR. `flat` is a
        # perfectly uniform plane under one sun, so its band-passed p-p is
        # identically zero for ANY valid input — and `geo / flat` then reads
        # 3e7 and passes a >= 2.0 bar no matter what `geo` is. A quantity that
        # is identically zero for every valid input is not a denominator, and a
        # check that cannot fail is not a check. The bar is now a physical one:
        # the relief arm must clear the floor by MARGIN_PP of peak-to-peak log
        # luminance, which at this sun is about a 1 % radiance modulation.
        v = ("RELIEF IS REAL" if ge >= fl + MARGIN_PP else
             "PAINT" if pa >= fl + MARGIN_PP else "INCONCLUSIVE")
        verdicts[mn] = dict(flat_pp=fl, geo_pp=ge, paint_pp=pa,
                            geo_minus_flat=ge - fl, margin_pp=MARGIN_PP,
                            relief_share=ge / max(ge + pa, 1e-12), verdict=v)
        print("  %-18s %9.4f %9.4f %9.4f %9.4f %11s"
              % (mn, r["orig"]["band_pp"], r["geo"]["band_pp"],
                 r["paint"]["band_pp"], fl, v))
    print("\n  %-18s %12s %12s %14s" % ("", "geo - flat", "bar", "relief share"))
    for mn in MATS:
        v = verdicts[mn]
        print("  %-18s %12.4f %12.4f %13.1f %%"
              % (mn, v["geo_minus_flat"], MARGIN_PP, 100 * v["relief_share"]))
    print("\n  `flat` is `geo` with Normal unlinked: neither paint nor relief.")
    print("  It is the REAL floor of this measurement — sampling noise plus the")
    print("  farm's 8-bit quantisation — and it is what `geo` has to clear.")
    print("  (On the earlier CLIPPED render it was identically 1.00002 with")
    print("  sd 0, which is why the bar is an absolute margin and not a ratio.)")
    print("  `relief share` is geo / (geo + paint).")

    # ---- variety: are the three relief fields actually different? ----------
    print("\nFIELD VARIETY — cross-correlation of the three `geo` arms")
    print("  1.000 would mean one field on three surfaces (a procedural repeat)")
    names = MATS
    cc = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            A = panels[(names[i], "geo")]
            B = panels[(names[j], "geo")]
            n = min(A.shape[0], B.shape[0]), min(A.shape[1], B.shape[1])
            A = A[:n[0], :n[1]]
            B = B[:n[0], :n[1]]
            A = A - A.mean()
            B = B - B.mean()
            r = float((A * B).sum() / max(np.sqrt((A ** 2).sum()
                                                  * (B ** 2).sum()), 1e-30))
            cc["%s|%s" % (names[i], names[j])] = r
            print("  %-22s %-22s r = %+.4f" % (names[i], names[j], r))

    out = dict(panels={m: res[m] for m in MATS}, verdicts=verdicts,
               cross_correlation=cc)
    if jout:
        os.makedirs(os.path.dirname(jout) or ".", exist_ok=True)
        json.dump(out, open(jout, "w"), indent=1)
        print("\nwrote %s" % jout)
    bad = [m for m in MATS if verdicts[m]["verdict"] != "RELIEF IS REAL"]
    worst = max(abs(v) for v in cc.values()) if cc else 0.0
    ok = (not bad) and worst < 0.30
    print("\nSTAGE RESULT: r2366_paint_vs_geometry %s "
          "(%d/%d relief real, worst |r| %.4f)"
          % ("PASS" if ok else "FAIL", len(MATS) - len(bad), len(MATS), worst))
    if not ok:
        sys.exit(1)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True,
                    choices=["build", "measure_np"])
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "r2366",
                                                  "pvg.blend"))
    ap.add_argument("--exr", default=None)
    ap.add_argument("--layout", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    if a.mode == "build":
        build(a.out)
    else:
        if not a.exr:
            raise SystemExit("--exr is required for --mode measure_np")
        measure_np(a.exr, a.json, a.layout)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        print("STAGE RESULT: r2366_paint_vs_geometry FAIL (uncaught exception)")
        sys.exit(1)
