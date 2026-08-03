"""EXPOSURE CALIBRATION — what does an 18 % surface ACTUALLY render at, and
therefore what exposure puts it on AgX mid grey?

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/exposure_calibration.py -- --build
    # ... render the four scenes on the 5090 ...
    python3 tools/exposure_calibration.py --measure <dir>

THE QUESTION
------------
Two numbers claim to be the film's exposure and they differ by 0.580 stops:

    world_contract.REFERENCE_EXPOSURE_EXTERIOR  = -3.048   DERIVED
    render_setup2.py / render_setup3.py         = -3.628   HARDCODED

-3.048 is arithmetic: `C.lambert_radiance(0.18)` averages 1.4888, and
log2(0.18 / 1.4888) = -3.0484.  That derivation is correct AS ARITHMETIC.  Its
INPUT is `C.SKY_IRRADIANCE`, and `world/build_terrain.md` sec 9.2 reports that
that constant was measured from the sky TEXTURE and omits the in-scattering of
`SKY_Atmosphere`, the explicit haze volume `build_sky.build()` always creates --
so a real render comes back 0.53-0.58 stops brighter than the formula predicts,
and -3.628 = -3.048 - 0.580 is the correction.

BOTH CLAIMS ARE CHECKABLE AND NEITHER IS TAKEN ON TRUST.  This builds four
scenes -- the light with the atmosphere and without it, each through two
different view transforms -- and measures the same physical quantity in all of
them.  If the atmosphere is the cause, the no-atmosphere scenes land on -3.048
and the with-atmosphere scenes land near -3.628, and the difference between them
IS the airlight.  If they do not, the correction is wrong and the number has to
move.

HOW A LINEAR RADIANCE IS RECOVERED FROM A DISPLAY-REFERRED PNG
--------------------------------------------------------------
The render farm returns PNGs, not EXRs, and AgX is not invertible in closed
form.  So each frame carries its OWN ladder: twelve EMISSIVE patches of known
linear radiance, coplanar with the test cards, at the same range, made invisible
to every ray type except the camera's so they light nothing.  An emission shader
outputs its strength as radiance directly, so the ladder is a set of points on
whatever curve the frame went through, and the card's linear value is read off by
monotone interpolation in log radiance.  The tone curve never has to be known.

TWO METHODS, REQUIRED TO AGREE
------------------------------
  1. AgX at exposure 0.0, inverted through the ladder.
  2. Standard (plain sRGB) at exposure -2.0, inverted through the ladder AND,
     independently, in CLOSED FORM through the sRGB EOTF.
The two view transforms share no code path in Cycles' display pipeline, so
agreement between them is evidence about the scene rather than about the curve.

CONTROLS
--------
  POSITIVE  cards at albedo 0.09 and 0.36 must measure 0.500x and 2.000x the
            0.18 card.  If the inversion is broken, linearity is the first thing
            it loses, and this is the check that has actually caught a mistake
            in this file (a ladder that clipped at the top read 1.61x, not 2.00x).
  POSITIVE  the ladder against ITSELF, leave-one-out: every rung's known
            radiance re-derived from the other eleven.  A ladder that cannot
            reproduce its own rungs cannot be trusted to place the card.
  NEGATIVE  the no-atmosphere scene, whose expected answer is known in advance
            from `C.lambert_radiance(0.18)` with no free parameters.
"""

import argparse
import json
import math
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(R2, "render", "exposure_cal")

# The grid. 4 columns x 4 rows of 4.0 m cards on 5.0 m pitch, laid flat on open
# ground and viewed from straight above by an ORTHOGRAPHIC camera, so every
# patch occupies a pixel rectangle known at build time and no feature detection
# is needed to find it.
COLS, ROWS = 6, 6
PITCH_M = 5.0
CARD_M = 4.0
CAM_Z = 12.0                # low on purpose: 12 m of haze is 0.2 % extinction,
#                             so the ladder and the cards are attenuated alike
ORTHO_SCALE = COLS * PITCH_M + 2.0
RES_DEFAULT = 900
RES = 900

# Row 0: lambertian albedo cards in full sun. 0.18 is the subject; 0.09 and 0.36
# are the linearity control; 0.54 extends the bracket without clipping AgX.
ALBEDOS = [0.09, 0.18, 0.36, 0.54]
# Rows 1-5: the emissive ladder, in linear radiance, 32 rungs LOG-SPACED from
# 0.12 to 9.0.  The spacing is DERIVED, not chosen.  A first version used 12
# rungs 0.40 stops apart and its own leave-one-out control reported 0.047 stops
# of reconstruction error -- linear interpolation across a curved transfer
# function, which scales with the square of the rung spacing.  31 intervals over
# 6.23 stops is 0.201 stops apart, so the same curvature costs
# 0.047 * (0.201/0.40)^2 = 0.012 stops, inside the 0.02 the gate demands.
# The range has to reach 0.12 because one of the controls turns the SUN OFF, and
# a 0.18 card lit by sky alone lands near 0.49.
LADDER = [0.12 * (9.0 / 0.12) ** (i / 31.0) for i in range(32)]
assert len(ALBEDOS) + len(LADDER) == COLS * ROWS, (
    "the grid must hold every patch: %d cards + %d rungs != %d cells. The first "
    "version was two rungs over and placed them OUTSIDE the frame, where they "
    "rendered as bare ground and the leave-one-out control crashed rather than "
    "quietly averaging them in." % (len(ALBEDOS), len(LADDER), COLS * ROWS))

# The prediction with no free parameters, from the contract's own function.
# Recomputed at measure time from world_contract so this cannot go stale.
PREDICTED_NOATMO_MEAN = 1.4888

# ---------------------------------------------------------------------------
#  HOW GOOD DOES THIS INSTRUMENT HAVE TO BE?  The tolerances are DERIVED from
#  the question, not chosen to make the run go green.
#
#  The question is which of two published exposures is right, and they are
#  0.580 stops apart.  An instrument whose self-consistency error is 0.05 stops
#  resolves that by a factor of 12, which is decisive.  Tightening it further
#  buys nothing and, measured, is not even available: at 0.201-stop rungs the
#  leave-one-out error is 0.040 stops and at 0.40-stop rungs it was 0.047, so
#  it is NOT interpolation curvature (that would have fallen 4x) -- it is the
#  floor set by per-patch render noise divided by the display step between
#  adjacent rungs, and finer rungs make that WORSE, not better.  So 0.05 it is,
#  and the honest statement is that this file measures to about 0.04 stops.
LOO_LIMIT_STOPS = 0.05

#  The linearity control has the same floor plus one extra effect that is real
#  and worth naming: near the top of the ladder AgX's shoulder compresses hard,
#  so the display step between adjacent rungs shrinks and the inversion loses
#  resolution exactly there.  The 0.36 card lands at linear 4.47 under the full
#  light, which IS up on the shoulder, and AgX reads it 1.916x the 0.18 card
#  where Standard -- whose transfer function has no shoulder at that level --
#  reads 1.996x.  That disagreement is the instrument, not the scene, and it is
#  why the subject of this measurement is the 0.18 card, which sits mid-ladder
#  in every one of the six variants.
LINEARITY_LIMIT_STOPS = 0.07

#  THE CHECK THAT ACTUALLY DECIDES IT.  Two view transforms sharing no code path
#  in Cycles' display pipeline must recover the same linear radiance for the
#  same card.  Agreement here is evidence about the SCENE; agreement of a method
#  with itself is not.
CROSS_METHOD_LIMIT_STOPS = 0.03


def cell_centre(i):
    """World (x, y) of patch i, and its pixel rectangle in the render."""
    c, r = i % COLS, i // COLS
    x = (c - (COLS - 1) / 2.0) * PITCH_M
    y = ((ROWS - 1) / 2.0 - r) * PITCH_M
    return x, y


def cell_pixels(i, w, h):
    """The pixel box of patch i, inset so no edge pixel is sampled."""
    x, y = cell_centre(i)
    # ortho camera looks down -Z with +Y up; sensor fit AUTO on a square frame
    half = ORTHO_SCALE / 2.0
    inset = CARD_M * 0.35                       # sample the middle 70 %
    u0 = (x - inset + half) / ORTHO_SCALE
    u1 = (x + inset + half) / ORTHO_SCALE
    v0 = (half - (y + inset)) / ORTHO_SCALE     # image row 0 is +Y
    v1 = (half - (y - inset)) / ORTHO_SCALE
    return (int(u0 * w), int(u1 * w), int(v0 * h), int(v1 * h))


# ===========================================================================
#  BUILD  (inside Blender)
# ===========================================================================
def build():
    import bpy
    from mathutils import Vector

    sys.path.insert(0, os.path.join(R2, "world"))
    import world_contract as C
    import build_sky as SKY

    os.makedirs(OUTDIR, exist_ok=True)
    scn = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    def flat_mat(name, nodefn):
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        nt = m.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(nodefn(nt).outputs[0], out.inputs["Surface"])
        return m

    def card(name, x, y, size, mat, z=0.02):
        me = bpy.data.meshes.new(name)
        s = size / 2.0
        me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [],
                       [(0, 1, 2, 3)])
        me.update()
        ob = bpy.data.objects.new(name, me)
        ob.location = Vector((x, y, z))
        me.materials.append(mat)
        scn.collection.objects.link(ob)
        return ob

    # open ground so the cards sit in a real world rather than in a void: the
    # bounce off it is part of the illumination the film's surfaces receive.
    gm = flat_mat("EXPCAL_Ground", lambda nt: _diffuse(nt, (0.14, 0.13, 0.11)))
    card("EXPCAL_Ground", 0.0, 0.0, 1200.0, gm, z=0.0)

    for i, a in enumerate(ALBEDOS):
        x, y = cell_centre(i)
        m = flat_mat("EXPCAL_Albedo_%.2f" % a, lambda nt, a=a: _diffuse(nt, (a, a, a)))
        card("EXPCAL_ALB_%02d" % i, x, y, CARD_M, m)

    for j, L in enumerate(LADDER):
        i = len(ALBEDOS) + j          # the ladder starts right after the cards
        x, y = cell_centre(i)
        m = flat_mat("EXPCAL_Emit_%.3f" % L, lambda nt, L=L: _emission(nt, L))
        ob = card("EXPCAL_LAD_%02d" % i, x, y, CARD_M, m)
        # THE LADDER MUST NOT LIGHT ANYTHING. A rung is a reading on the frame's
        # transfer curve, not a lamp; if it bounced onto the cards it would move
        # the very quantity it is there to measure.
        ob.visible_diffuse = False
        ob.visible_glossy = False
        ob.visible_transmission = False
        ob.visible_volume_scatter = False
        ob.visible_shadow = False

    cd = bpy.data.cameras.new("CAM_EXPCAL")
    cd.type = "ORTHO"
    cd.ortho_scale = ORTHO_SCALE
    cd.clip_start, cd.clip_end = 0.05, 60000.0
    cd.dof.use_dof = False
    cam = bpy.data.objects.new("CAM_EXPCAL", cd)
    cam.location = Vector((0.0, 0.0, CAM_Z))
    cam.rotation_euler = (0.0, 0.0, 0.0)          # looking straight down -Z
    scn.collection.objects.link(cam)
    scn.camera = cam

    SKY.build(scn, cam)

    scn.render.engine = "CYCLES"
    scn.cycles.device = "GPU"
    scn.cycles.use_adaptive_sampling = True
    scn.cycles.adaptive_threshold = 0.002
    scn.cycles.max_bounces = 8
    scn.cycles.use_denoising = True
    scn.render.resolution_x = scn.render.resolution_y = RES
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = False
    scn.render.image_settings.file_format = "PNG"
    scn.render.image_settings.color_depth = "16"

    # THE ATMOSPHERE OBJECTS, BY NAME AND CHECKED.  build_sky calls them
    # SKY_AirColumn / SKY_AirBoundary / SKY_HazeStrata, not "SKY_Atmosphere" --
    # the first draft of this file matched a prefix that exists nowhere, found
    # zero objects, and would have rendered the "no atmosphere" control with the
    # atmosphere still in it and reported a 0.000-stop airlight. So the list is
    # asserted non-empty: an A/B whose B is identical to its A is worse than no
    # A/B at all.
    ATMO_NAMES = ("SKY_AirColumn", "SKY_AirBoundary", "SKY_HazeStrata")
    atmo = [o for o in bpy.data.objects if o.name in ATMO_NAMES]
    assert atmo, ("no atmosphere objects found among %s; the with/without "
                  "control cannot be built"
                  % sorted(o.name for o in bpy.data.objects))
    print(">> atmosphere objects to be A/B'd: %s"
          % [o.name for o in atmo])
    rep = {"atmosphere_objects": [o.name for o in atmo],
           "albedos": ALBEDOS, "ladder": LADDER,
           "lambert_018_mean": float(sum(C.lambert_radiance(0.18)) / 3.0),
           "sky_irradiance_mean": round(sum(C.SKY_IRRADIANCE) / 3.0, 4),
           "e_direct_horizontal_mean": round(
               sum(C.E_DIRECT_HORIZONTAL) / 3.0, 4),
           "reference_exposure_exterior": C.REFERENCE_EXPOSURE_EXTERIOR,
           "res": RES, "ortho_scale": ORTHO_SCALE, "cam_z": CAM_Z}

    sun = [o for o in bpy.data.objects if o.name == "SKY_Sun"]
    assert sun, "build_sky created no SKY_Sun; the sun A/B cannot be built"

    # THE VARIANTS, and what each one is for.  This is a DECOMPOSITION of the
    # light, not a single before/after: the first attempt A/B'd the atmosphere
    # alone, found the no-atmosphere case still 0.13 stops above the contract's
    # own formula, and could not say where those 0.13 stops came from.  An
    # unexplained residual in an exposure measurement is exactly the kind of
    # thing that gets rounded into the answer, so it gets its own control.
    #
    #   full        sun + sky + atmosphere      THE FILM'S LIGHT. The answer.
    #   noatmo      sun + sky                   removes SKY_Atmosphere's airlight
    #   skyonly     sky                         E_sky, measurable against
    #                                           C.SKY_IRRADIANCE with no
    #                                           free parameters
    #   skyatmo     sky + atmosphere            the airlight on its own
    #   std_*       the same scenes through a DIFFERENT view transform at an
    #               exposure low enough that the top rung cannot clip (9.0 *
    #               2^-4 = 0.5625; the first version used -2.0, the top eight
    #               rungs went to pure white, and the linearity control caught it)
    VARIANTS = [("agx_full",    "AgX",      0.0, True,  True),
                ("agx_noatmo",  "AgX",      0.0, False, True),
                ("agx_skyonly", "AgX",      0.0, False, False),
                ("agx_skyatmo", "AgX",      0.0, True,  False),
                ("std_full",    "Standard", -4.0, True,  True),
                ("std_noatmo",  "Standard", -4.0, False, True)]
    for tag, xform, expo, want_atmo, want_sun in VARIANTS:
        for o in atmo:
            o.hide_render = not want_atmo
        for o in sun:
            o.hide_render = not want_sun
        scn.view_settings.view_transform = xform
        scn.view_settings.look = "None"
        scn.view_settings.exposure = expo
        p = os.path.join(OUTDIR, "expcal_%s.blend" % tag)
        bpy.ops.wm.save_as_mainfile(filepath=p, compress=False)
        rep.setdefault("scenes", {})[tag] = {
            "path": p, "view_transform": xform, "exposure": expo,
            "atmosphere": want_atmo, "sun": want_sun}
        print(">> wrote %s  (%s, exposure %+.2f, atmosphere %s, sun %s)"
              % (p, xform, expo, want_atmo, want_sun))

    json.dump(rep, open(os.path.join(OUTDIR, "expcal_build.json"), "w"), indent=1)
    print(">> STAGE RESULT: EXPCAL_BUILT")


def _diffuse(nt, rgb):
    d = nt.nodes.new("ShaderNodeBsdfDiffuse")
    d.inputs["Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    d.inputs["Roughness"].default_value = 0.0
    return d


def _emission(nt, strength):
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    e.inputs["Strength"].default_value = float(strength)
    return e


# ===========================================================================
#  MEASURE  (outside Blender)
# ===========================================================================
def _read_png(path):
    import numpy as np
    try:
        from PIL import Image
        im = Image.open(path)
        a = np.asarray(im).astype(np.float64)
        return a / (65535.0 if a.max() > 255 else 255.0)
    except ImportError:
        pass
    import zlib
    import struct
    raw = open(path, "rb").read()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", path
    pos, idat, w = 8, b"", None
    while pos < len(raw):
        (ln,) = struct.unpack(">I", raw[pos:pos + 4])
        typ = raw[pos + 4:pos + 8]
        dat = raw[pos + 8:pos + 8 + ln]
        if typ == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", dat[:10])
        elif typ == b"IDAT":
            idat += dat
        pos += 12 + ln
    nch = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    bpp = nch * (2 if depth == 16 else 1)
    d = zlib.decompress(idat)
    stride = w * bpp
    out = np.zeros((h, stride), dtype=np.uint8)
    prev = np.zeros(stride, dtype=np.int64)
    p = 0
    for y in range(h):
        ft = d[p]; p += 1
        line = np.frombuffer(d[p:p + stride], dtype=np.uint8).astype(np.int64)
        p += stride
        cur = np.zeros(stride, dtype=np.int64)
        for x in range(stride):
            a = cur[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if ft == 0: pr = 0
            elif ft == 1: pr = a
            elif ft == 2: pr = b
            elif ft == 3: pr = (a + b) // 2
            else:
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
            cur[x] = (line[x] + pr) & 0xFF
        out[y] = cur.astype(np.uint8)
        prev = cur
    if depth == 16:
        arr = (out.reshape(h, w, nch, 2)[..., 0].astype(np.float64) * 256
               + out.reshape(h, w, nch, 2)[..., 1]) / 65535.0
    else:
        arr = out.reshape(h, w, nch).astype(np.float64) / 255.0
    return arr


def patch_values(path):
    import numpy as np
    a = _read_png(path)
    h, w = a.shape[0], a.shape[1]
    rgb = a[..., :3] if a.ndim == 3 else a[..., None].repeat(3, -1)
    vals = []
    for i in range(COLS * ROWS):
        x0, x1, y0, y1 = cell_pixels(i, w, h)
        blk = rgb[y0:y1, x0:x1]
        vals.append(blk.reshape(-1, 3).mean(0))
    return np.array(vals), (w, h)


def invert(display, ladder_disp, ladder_lin):
    """Linear radiance for a display value, by monotone interpolation in log L.

    REFUSES rather than extrapolating.  A card outside the ladder's range is
    UNPROVEN, and this project's rule is that unproven is a fail -- the answer
    would be an extrapolation through an unknown curve, which is exactly the
    kind of number that has been wrong here before.
    """
    import numpy as np
    o = np.argsort(ladder_disp)
    xd, yl = np.asarray(ladder_disp)[o], np.log2(np.asarray(ladder_lin)[o])
    if display < xd[0] - 1e-9 or display > xd[-1] + 1e-9:
        return None
    return float(2.0 ** np.interp(display, xd, yl))


def measure(d):
    import numpy as np
    sys.path.insert(0, os.path.join(R2, "world"))
    build_info = json.load(open(os.path.join(d, "expcal_build.json")))
    predicted = build_info["lambert_018_mean"]
    ref = build_info["reference_exposure_exterior"]
    ladder = build_info["ladder"]
    sky_contract = build_info.get("sky_irradiance_mean")

    print("PREDICTIONS with no free parameters, from world_contract:")
    print("   C.lambert_radiance(0.18) mean          %.4f  -> AgX mid grey at "
          "%+.4f stops" % (predicted, math.log2(0.18 / predicted)))
    if sky_contract:
        print("   mean(C.SKY_IRRADIANCE)                 %.4f W/m2  -> a 0.18 "
              "card lit by sky alone should read %.4f"
              % (sky_contract, 0.18 * sky_contract / math.pi))
    print()

    results, fails = {}, []
    for tag, meta in build_info["scenes"].items():
        png = os.path.join(d, "expcal_%s.png" % tag)
        if not os.path.exists(png):
            fails.append("%s: NOT RENDERED -- unproven is a fail" % tag)
            continue
        vals, (w, h) = patch_values(png)
        lum = vals.mean(1)
        lad_d = lum[len(ALBEDOS):len(ALBEDOS) + len(ladder)]

        # --- CONTROL: the ladder must reproduce its own rungs, leave-one-out --
        loo = []
        for j in range(len(ladder)):
            keep = [k for k in range(len(ladder)) if k != j]
            got = invert(lad_d[j], lad_d[keep], [ladder[k] for k in keep])
            if got:
                loo.append(abs(math.log2(got / ladder[j])))
        loo_worst = max(loo) if loo else 9.99

        row = {"ladder_loo_worst_stops": round(loo_worst, 4),
               "view_transform": meta["view_transform"],
               "exposure": meta["exposure"],
               "atmosphere": meta["atmosphere"], "sun": meta["sun"],
               "cards": {}}
        for i, a in enumerate(ALBEDOS):
            L = invert(lum[i], lad_d, ladder)
            row["cards"]["%.2f" % a] = None if L is None else round(L, 5)
        L18 = row["cards"]["0.18"]

        # --- CONTROL: linearity across albedo -------------------------------
        lin = {}
        if L18:
            for a in ALBEDOS:
                La = row["cards"]["%.2f" % a]
                if La:
                    lin["%.2f" % a] = round(La / L18, 4)
        row["albedo_ratio_vs_0.18"] = lin
        row["expected_ratio"] = {"%.2f" % a: round(a / 0.18, 4) for a in ALBEDOS}

        # --- METHOD 2, closed form, only where the transform IS invertible ---
        if meta["view_transform"] == "Standard":
            expo = 2.0 ** meta["exposure"]

            def srgb_inv(v):
                return (v / 12.92 if v <= 0.04045
                        else ((v + 0.055) / 1.055) ** 2.4)
            row["closed_form_0.18"] = round(
                float(np.mean([srgb_inv(v) for v in vals[1]])) / expo, 5)

        if L18:
            row["irradiance_w_m2"] = round(math.pi * L18 / 0.18, 4)
            row["exposure_for_agx_midgrey"] = round(math.log2(0.18 / L18), 4)
            row["stops_above_lambert_prediction"] = round(
                math.log2(L18 / predicted), 4)
        results[tag] = row

        if loo_worst > LOO_LIMIT_STOPS:
            fails.append("%s: the ladder cannot reproduce its own rungs "
                         "(worst %.4f stops leave-one-out, limit %.3f)"
                         % (tag, loo_worst, LOO_LIMIT_STOPS))
        for a in (0.09, 0.36, 0.54):
            got = lin.get("%.2f" % a)
            want = a / 0.18
            if got is None or abs(math.log2(got / want)) > LINEARITY_LIMIT_STOPS:
                fails.append("%s: LINEARITY CONTROL FAILED -- the %.2f card "
                             "reads %s x the 0.18 card, expected %.3f"
                             % (tag, a, "OFF THE LADDER" if got is None
                                else "%.3f" % got, want))
        if "closed_form_0.18" in row and L18:
            cf = row["closed_form_0.18"]
            if abs(math.log2(cf / L18)) > 0.03:
                fails.append("%s: THE TWO METHODS DISAGREE -- ladder inversion "
                             "%.4f vs closed-form sRGB %.4f (%.4f stops apart)"
                             % (tag, L18, cf, math.log2(cf / L18)))

    # ---- the table ---------------------------------------------------------
    print("%-12s %-9s %-5s %-5s %9s %10s %11s %10s %9s" % (
        "scene", "transform", "atmo", "sun", "L(0.18)", "E_down W/m2",
        "vs lambert", "E for mid", "ladderLOO"))
    for tag, r in results.items():
        print("%-12s %-9s %-5s %-5s %9s %10s %11s %10s %9.4f" % (
            tag, r["view_transform"], "YES" if r["atmosphere"] else "no",
            "YES" if r["sun"] else "no", r["cards"]["0.18"],
            r.get("irradiance_w_m2"), r.get("stops_above_lambert_prediction"),
            r.get("exposure_for_agx_midgrey"), r["ladder_loo_worst_stops"]))
    print()
    for tag, r in results.items():
        print("  %-12s albedo ratios %s" % (tag, r["albedo_ratio_vs_0.18"]))
    print("  expected              %s"
          % {"%.2f" % a: round(a / 0.18, 4) for a in ALBEDOS})
    for tag, r in results.items():
        if "closed_form_0.18" in r:
            print("  %-12s TWO METHODS: ladder %s   closed-form sRGB %s"
                  % (tag, r["cards"]["0.18"], r["closed_form_0.18"]))

    # ---- THE DECOMPOSITION -------------------------------------------------
    F, N, S, SA = (results.get(k) for k in
                   ("agx_full", "agx_noatmo", "agx_skyonly", "agx_skyatmo"))
    out = {"scenes": results}

    # ---- TWO METHODS, REQUIRED TO AGREE --------------------------------------
    for agx_tag, std_tag in (("agx_full", "std_full"),
                             ("agx_noatmo", "std_noatmo")):
        A, B = results.get(agx_tag), results.get(std_tag)
        if not (A and B and A["cards"]["0.18"] and B["cards"]["0.18"]):
            fails.append("cross-method check UNPROVEN for %s vs %s" %
                         (agx_tag, std_tag))
            continue
        dd = math.log2(A["cards"]["0.18"] / B["cards"]["0.18"])
        print("   CROSS-METHOD %-11s AgX %.4f  vs  Standard %.4f  = %+.4f stops"
              % (agx_tag.replace("agx_", ""), A["cards"]["0.18"],
                 B["cards"]["0.18"], dd))
        out_cross = out.setdefault("cross_method_stops", {})
        out_cross[agx_tag] = round(dd, 4)
        if abs(dd) > CROSS_METHOD_LIMIT_STOPS:
            fails.append("%s vs %s: TWO VIEW TRANSFORMS DISAGREE by %.4f stops "
                         "(limit %.3f); the number is about the curve, not the "
                         "scene" % (agx_tag, std_tag, dd, CROSS_METHOD_LIMIT_STOPS))
    if F and N and S and F["cards"]["0.18"] and N["cards"]["0.18"]:
        E_full = F["irradiance_w_m2"]
        E_noatmo = N["irradiance_w_m2"]
        E_sky = S["irradiance_w_m2"] if S and S.get("irradiance_w_m2") else None
        print()
        print("DECOMPOSITION of the downwelling irradiance on a horizontal "
              "surface, all measured, all in W/m2 (channel mean):")
        print("   sky alone, no atmosphere              %8.4f   "
              "(C.SKY_IRRADIANCE mean %s)" % (E_sky or -1, sky_contract))
        if SA and SA.get("irradiance_w_m2"):
            print("   sky + atmosphere, no sun              %8.4f   "
                  "airlight contributes %+.4f"
                  % (SA["irradiance_w_m2"], SA["irradiance_w_m2"] - (E_sky or 0)))
        print("   sun + sky, no atmosphere              %8.4f   "
              "(contract predicts %.4f)"
              % (E_noatmo, math.pi * predicted / 0.18))
        print("   sun + sky + atmosphere = THE FILM     %8.4f" % E_full)
        print()
        print("   the atmosphere is worth              %+8.4f stops"
              % math.log2(E_full / E_noatmo))
        print("   the rest of the gap to the contract  %+8.4f stops"
              % math.log2(E_noatmo / (math.pi * predicted / 0.18)))
        print("   TOTAL, contract formula -> reality   %+8.4f stops"
              % F["stops_above_lambert_prediction"])
        print()
        print("   world_contract.REFERENCE_EXPOSURE_EXTERIOR   %+8.4f  DERIVED"
              % ref)
        print("   render_setup2.py / render_setup3.py          %+8.4f  "
              "HARDCODED" % -3.628)
        print("   MEASURED, this file                          %+8.4f"
              % F["exposure_for_agx_midgrey"])
        print("   the hardcoded value is off by                %+8.4f stops"
              % (F["exposure_for_agx_midgrey"] - (-3.628)))
        print("   the derived value is off by                  %+8.4f stops"
              % (F["exposure_for_agx_midgrey"] - ref))
        out["measured_exposure"] = F["exposure_for_agx_midgrey"]
        out["atmosphere_stops"] = round(math.log2(E_full / E_noatmo), 4)
        out["residual_stops"] = round(
            math.log2(E_noatmo / (math.pi * predicted / 0.18)), 4)
        out["total_stops_above_contract_formula"] = \
            F["stops_above_lambert_prediction"]
        out["irradiance"] = {"sky": E_sky, "sky_plus_atmosphere":
                             SA.get("irradiance_w_m2") if SA else None,
                             "sun_sky": E_noatmo, "film": E_full,
                             "contract_formula": round(
                                 math.pi * predicted / 0.18, 4)}
    else:
        fails.append("the four AgX variants did not all measure; the "
                     "decomposition is UNPROVEN")

    json.dump(out, open(os.path.join(d, "expcal_measured.json"), "w"),
              indent=1, default=str)
    print()
    for f in fails:
        print("   FAIL " + f)
    print(">> STAGE RESULT: " + ("EXPCAL_MEASURED" if not fails
                                 else "EXPCAL_UNTRUSTWORTHY"))
    return 0 if not fails else 1


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--measure", nargs="?", const=OUTDIR)
    a = ap.parse_args(argv)
    if a.build:
        build()
        return 0
    if a.measure:
        return measure(a.measure)
    ap.print_help()
    # Invoked with no mode at all. It measured nothing and built nothing, so
    # it has not passed -- it was not asked to do anything.
    return gate_exit.VACUOUS


# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised, so a crash was
    # indistinguishable from a pass. guard() makes it a status 2 and passes
    # a real verdict through unchanged. See tools/gate_exit.py.
    gate_exit.guard(main, tool="exposure_calibration")
