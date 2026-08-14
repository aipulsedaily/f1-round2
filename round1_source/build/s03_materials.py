"""Material library. Every factory is idempotent - re-running rebuilds the tree."""

import math

import bpy

import common as C
import spec


# --------------------------------------------------------------------------- #
# showroom
# --------------------------------------------------------------------------- #

def floor_polished():
    """Dark polished terrazzo/microcement: mirror-ish but with real mottling.

    A perfectly uniform roughness reads as CG, so roughness is broken up by two
    noise octaves and the base colour gets faint aggregate speckle.
    """
    mat, nt, b = C.material("FloorPolished")
    C.set_defaults(b, Base_Color=(0.035, 0.037, 0.042, 1.0), Metallic=0.0,
                   Roughness=0.10, IOR=1.52, Specular_IOR_Level=0.55)
    b.inputs["Coat Weight"].default_value = 0.45
    b.inputs["Coat Roughness"].default_value = 0.045

    texco = C.node(nt, "ShaderNodeTexCoord", (-1200, 0))
    mapn = C.node(nt, "ShaderNodeMapping", (-1020, 0))
    mapn.inputs["Scale"].default_value = (0.09, 0.09, 0.09)
    C.wire(nt, texco, "Object", mapn, "Vector")

    # broad polish unevenness
    n1 = C.node(nt, "ShaderNodeTexNoise", (-840, 160))
    C.set_defaults(n1, Scale=2.4, Detail=4.0, Roughness=0.55, Distortion=0.0)
    C.wire(nt, mapn, "Vector", n1, "Vector")
    r1 = C.node(nt, "ShaderNodeValToRGB", (-640, 160))
    r1.color_ramp.elements[0].position = 0.34
    r1.color_ramp.elements[0].color = (0.055, 0.055, 0.055, 1)
    r1.color_ramp.elements[1].position = 0.70
    r1.color_ramp.elements[1].color = (0.155, 0.155, 0.155, 1)
    C.wire(nt, n1, "Fac", r1, "Fac")

    # fine micro-scratch grain
    n2 = C.node(nt, "ShaderNodeTexNoise", (-840, -60))
    C.set_defaults(n2, Scale=140.0, Detail=2.0, Roughness=0.5)
    C.wire(nt, mapn, "Vector", n2, "Vector")
    mixr = C.node(nt, "ShaderNodeMix", (-420, 80), data_type="RGBA", blend_type="OVERLAY")
    mixr.inputs["Factor"].default_value = 0.10
    C.wire(nt, r1, "Color", mixr, 6)      # A
    C.wire(nt, n2, "Color", mixr, 7)      # B
    C.wire(nt, mixr, 2, b, "Roughness")

    # aggregate speckle in the base colour
    spec = C.node(nt, "ShaderNodeTexNoise", (-840, -280))
    C.set_defaults(spec, Scale=38.0, Detail=6.0, Roughness=0.75)
    C.wire(nt, mapn, "Vector", spec, "Vector")
    sramp = C.node(nt, "ShaderNodeValToRGB", (-640, -280))
    sramp.color_ramp.elements[0].position = 0.52
    sramp.color_ramp.elements[0].color = (0.030, 0.032, 0.036, 1)
    sramp.color_ramp.elements[1].position = 0.63
    sramp.color_ramp.elements[1].color = (0.058, 0.060, 0.068, 1)
    C.wire(nt, spec, "Fac", sramp, "Fac")
    C.wire(nt, sramp, "Color", b, "Base Color")

    # extremely shallow surface undulation - makes reflections live
    bump = C.node(nt, "ShaderNodeBump", (-200, -240))
    bump.inputs["Strength"].default_value = 0.06
    bump.inputs["Distance"].default_value = 0.02
    C.wire(nt, n1, "Fac", bump, "Height")
    C.wire(nt, bump, "Normal", b, "Normal")
    return mat


def platform_body():
    """Matte off-white lacquer dais.

    D009: at 0.80 albedo the dais flank clipped wherever the kick light grazed
    it. Real showroom lacquer sits nearer 0.55-0.62 reflectance.
    """
    mat, nt, b = C.material("PlatformBody")
    C.set_defaults(b, Base_Color=(0.60, 0.605, 0.62, 1.0), Metallic=0.0,
                   Roughness=0.34, IOR=1.5, Specular_IOR_Level=0.5)
    b.inputs["Coat Weight"].default_value = 0.25
    b.inputs["Coat Roughness"].default_value = 0.16
    return mat


def turntable_top():
    """Dark circular-brushed metal deck the car stands on.

    D003: a linear brush built from noise scaled (180, 1, 1) on object coords put
    a pinwheel singularity dead centre of the disc. Real turntable decks are
    *circular* brushed anyway, so the grain now comes from a RINGS wave texture
    concentric with the axis - no pole artifact, and physically the right look.

    D006/D007: the first ring wave used Scale 1.0 with Distortion 13, which makes
    metre-scale blobs - the deck read as rippling mercury and clipped to pure
    white. Brushing must be a *fine, low-contrast* grain: high ring frequency,
    small distortion, and a narrow roughness band. Base roughness also went up so
    the deck stops behaving like a mirror aimed at the cove.
    """
    mat, nt, b = C.material("TurntableTop")
    C.set_defaults(b, Base_Color=(0.048, 0.049, 0.053, 1.0), Metallic=0.86,
                   Roughness=0.40)
    # D010: anisotropy needs a tangent field; on a disc the default tangent is
    # degenerate at the axis and drew a dark bowtie converging on dead centre.
    # The ring-roughness texture already carries the brushed read, so drop it.
    b.inputs["Anisotropic"].default_value = 0.0

    texco = C.node(nt, "ShaderNodeTexCoord", (-900, 0))

    rings = C.node(nt, "ShaderNodeTexWave", (-660, 60),
                   wave_type="RINGS", rings_direction="Z", wave_profile="SIN")
    C.set_defaults(rings, Scale=55.0, Distortion=1.4, Detail=4.0,
                   Detail_Scale=1.0, Detail_Roughness=0.5, Phase_Offset=0.0)
    C.wire(nt, texco, "Object", rings, "Vector")

    fine = C.node(nt, "ShaderNodeTexWave", (-660, -200),
                  wave_type="RINGS", rings_direction="Z", wave_profile="SAW")
    C.set_defaults(fine, Scale=260.0, Distortion=2.5, Detail=2.0, Detail_Scale=1.0)
    C.wire(nt, texco, "Object", fine, "Vector")

    mix = C.node(nt, "ShaderNodeMix", (-430, 0), data_type="RGBA", blend_type="MIX")
    mix.inputs["Factor"].default_value = 0.40
    C.wire(nt, rings, "Color", mix, 6)
    C.wire(nt, fine, "Color", mix, 7)

    # D008: concentric rings have unbounded frequency as r -> 0, so the very
    # centre of the disc turned into a shimmering normal singularity - a dark
    # smudge dead centre. Fade the pattern out to a constant inside r = 0.45 m.
    radius = C.node(nt, "ShaderNodeVectorMath", (-660, -420), operation="LENGTH")
    C.wire(nt, texco, "Object", radius, 0)
    rmask = C.node(nt, "ShaderNodeMapRange", (-480, -420))
    C.set_defaults(rmask, From_Min=0.06, From_Max=0.45, To_Min=0.0, To_Max=1.0)
    rmask.clamp = True
    C.wire(nt, radius, "Value", rmask, "Value")

    masked = C.node(nt, "ShaderNodeMix", (-300, -180), data_type="RGBA", blend_type="MIX")
    masked.inputs[6].default_value = (0.5, 0.5, 0.5, 1.0)   # flat centre
    C.wire(nt, rmask, "Result", masked, "Factor")
    C.wire(nt, mix, 2, masked, 7)

    ramp = C.node(nt, "ShaderNodeValToRGB", (-110, 0))
    ramp.color_ramp.elements[0].position = 0.20
    ramp.color_ramp.elements[0].color = (0.335, 0.335, 0.335, 1)
    ramp.color_ramp.elements[1].position = 0.82
    ramp.color_ramp.elements[1].color = (0.455, 0.455, 0.455, 1)
    C.wire(nt, masked, 2, ramp, "Fac")
    C.wire(nt, ramp, "Color", b, "Roughness")

    bump = C.node(nt, "ShaderNodeBump", (60, -300))
    bump.inputs["Strength"].default_value = 0.02
    bump.inputs["Distance"].default_value = 0.0001
    C.wire(nt, masked, 2, bump, "Height")
    C.wire(nt, bump, "Normal", b, "Normal")
    return mat


def glass_panel(tint=(0.86, 0.92, 0.90, 1.0), rough=0.012):
    """Architectural curtain-wall glass: thin-wall so panes stay cheap to trace."""
    mat, nt, b = C.material("GlassPanel")
    C.set_defaults(b, Base_Color=tint, Metallic=0.0, Roughness=rough,
                   IOR=1.52, Transmission_Weight=1.0)
    b.inputs["Thin Wall"].default_value = True
    mat.use_backface_culling = False
    try:
        mat.surface_render_method = "DITHERED"
    except (AttributeError, TypeError):
        pass
    return mat


def anodized_alu(name="MullionAlu", base=(0.42, 0.43, 0.45, 1.0), rough=0.30):
    mat, nt, b = C.material(name)
    C.set_defaults(b, Base_Color=base, Metallic=1.0, Roughness=rough)
    # same unwired-Vector class as Titanium/SteelFastener
    texco = C.node(nt, "ShaderNodeTexCoord", (-880, 0))
    mapn = C.node(nt, "ShaderNodeMapping", (-690, 0))
    mapn.inputs["Scale"].default_value = (220.0, 220.0, 220.0)
    C.wire(nt, texco, "Object", mapn, "Vector")
    n = C.node(nt, "ShaderNodeTexNoise", (-500, 0))
    C.set_defaults(n, Scale=1.0, Detail=2.0, Roughness=0.5)
    C.wire(nt, mapn, "Vector", n, "Vector")
    ramp = C.node(nt, "ShaderNodeValToRGB", (-300, 0))
    ramp.color_ramp.elements[0].position = 0.40
    ramp.color_ramp.elements[0].color = (rough * 0.8,) * 3 + (1,)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (min(rough * 1.35, 1.0),) * 3 + (1,)
    C.wire(nt, n, "Fac", ramp, "Fac")
    C.wire(nt, ramp, "Color", b, "Roughness")
    return mat


def wall_dark():
    mat, nt, b = C.material("WallDark")
    C.set_defaults(b, Base_Color=(0.042, 0.043, 0.047, 1.0), Metallic=0.0, Roughness=0.62)
    n = C.node(nt, "ShaderNodeTexNoise", (-500, 0))
    C.set_defaults(n, Scale=14.0, Detail=4.0, Roughness=0.6)
    ramp = C.node(nt, "ShaderNodeValToRGB", (-300, 0))
    ramp.color_ramp.elements[0].color = (0.030, 0.031, 0.034, 1)
    ramp.color_ramp.elements[1].color = (0.058, 0.059, 0.064, 1)
    C.wire(nt, n, "Fac", ramp, "Fac")
    C.wire(nt, ramp, "Color", b, "Base Color")
    return mat


def ceiling_mat():
    mat, nt, b = C.material("CeilingMat")
    C.set_defaults(b, Base_Color=(0.075, 0.076, 0.080, 1.0), Metallic=0.0, Roughness=0.78)
    return mat


def emitter(name, color=(1.0, 0.96, 0.90), strength=12.0):
    """Pure emission - used for cove strips and the turntable seam glow."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = C.node(nt, "ShaderNodeOutputMaterial", (300, 0))
    em = C.node(nt, "ShaderNodeEmission", (60, 0))
    em.inputs["Color"].default_value = (*color, 1.0)
    em.inputs["Strength"].default_value = strength
    C.wire(nt, em, "Emission", out, "Surface")
    return mat


# --------------------------------------------------------------------------- #
# car
# --------------------------------------------------------------------------- #

def _planar_weave(nt, vec_node, vec_out, scale, loc):
    """One planar 2x2 twill: two perpendicular SIN bands overlaid."""
    mapn = C.node(nt, "ShaderNodeMapping", loc)
    mapn.inputs["Scale"].default_value = (scale, scale, scale)
    mapn.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(45.0))
    C.wire(nt, vec_node, vec_out, mapn, "Vector")

    warp = C.node(nt, "ShaderNodeTexWave", (loc[0] + 190, loc[1] + 90),
                  wave_type="BANDS", bands_direction="X", wave_profile="SIN")
    C.set_defaults(warp, Scale=1.0, Distortion=0.0, Detail=0.0)
    C.wire(nt, mapn, "Vector", warp, "Vector")

    weft = C.node(nt, "ShaderNodeTexWave", (loc[0] + 190, loc[1] - 90),
                  wave_type="BANDS", bands_direction="Y", wave_profile="SIN")
    C.set_defaults(weft, Scale=1.0, Distortion=0.0, Detail=0.0)
    C.wire(nt, mapn, "Vector", weft, "Vector")

    mix = C.node(nt, "ShaderNodeMix", (loc[0] + 380, loc[1]),
                 data_type="RGBA", blend_type="OVERLAY")
    mix.inputs["Factor"].default_value = 1.0
    C.wire(nt, warp, "Color", mix, 6)
    C.wire(nt, weft, "Color", mix, 7)
    return mix


def _weave(nt, scale=190.0, loc=(-2400, 0)):
    """2x2 twill carbon weave, TRIPLANAR.

    The single-projection version projected the twill down one object axis. On a
    swept part - a suspension leg, a halo tube, a fairing - every surface whose
    normal is perpendicular to that axis got the pattern smeared into stripes
    instead of twill. Whole-body inspection found it in 7 of 7 regions and called
    it the largest CG tell on the car.

    Fix: evaluate the weave on all three object-space planes (XY, YZ, ZX) and
    blend them by the squared surface normal, so every face is textured by
    whichever projection faces it most directly. Costs 3x the texture nodes and
    removes the stretch everywhere at once.
    """
    texco = C.node(nt, "ShaderNodeTexCoord", loc)
    sep = C.node(nt, "ShaderNodeSeparateXYZ", (loc[0] + 180, loc[1] - 320))
    C.wire(nt, texco, "Object", sep, "Vector")

    # three planar coordinate pairs
    planes = []
    for i, (a, b, dy) in enumerate((("X", "Y", 360), ("Y", "Z", 0), ("Z", "X", -360))):
        comb = C.node(nt, "ShaderNodeCombineXYZ", (loc[0] + 380, loc[1] + dy))
        C.wire(nt, sep, a, comb, "X")
        C.wire(nt, sep, b, comb, "Y")
        comb.inputs["Z"].default_value = 0.0
        planes.append(_planar_weave(nt, comb, "Vector", scale,
                                    (loc[0] + 560, loc[1] + dy)))

    # Blend weights from the surface normal, squared so the transition is tight.
    #
    # SPACE MISMATCH BUG: the three projections are built from OBJECT coordinates,
    # but ShaderNodeNewGeometry.Normal is in WORLD space. Blending object-space
    # projections by a world-space normal picks the wrong projection wherever the
    # object is rotated. On the brake drum - a barrel about the axle, so rotated
    # 90 deg from world - the YZ projection is a pure function of the angle round
    # the barrel, i.e. 1-D, and it won everywhere |cos th| > |sin th|, striping
    # the front and rear quadrants into corduroy. No per-part object frame could
    # fix that; the normal has to be converted into the same space as the
    # projections.
    geo = C.node(nt, "ShaderNodeNewGeometry", (loc[0] + 180, loc[1] - 640))
    nobj = C.node(nt, "ShaderNodeVectorTransform", (loc[0] + 300, loc[1] - 640),
                  vector_type="NORMAL", convert_from="WORLD", convert_to="OBJECT")
    C.wire(nt, geo, "Normal", nobj, "Vector")
    nsep = C.node(nt, "ShaderNodeSeparateXYZ", (loc[0] + 460, loc[1] - 640))
    C.wire(nt, nobj, "Vector", nsep, "Vector")

    def w_for(axis, dy):
        ab = C.node(nt, "ShaderNodeMath", (loc[0] + 560, loc[1] + dy),
                    operation="ABSOLUTE")
        C.wire(nt, nsep, axis, ab, 0)
        sq = C.node(nt, "ShaderNodeMath", (loc[0] + 720, loc[1] + dy),
                    operation="POWER")
        # Exponent 4 was too soft: at a 45 deg normal two projections blend
        # ~50/50 and two perpendicular twills beat into a hexagonal dot moire -
        # visibly NOT carbon. Procedural patterns interfere far more than images
        # do, so the blend has to be near-hard: 16 keeps one projection dominant
        # over almost the whole sphere of normals while still avoiding a seam.
        sq.inputs[1].default_value = 16.0
        C.wire(nt, ab, "Value", sq, 0)
        return sq

    # XY plane is faced by +-Z normals, YZ by +-X, ZX by +-Y
    wz, wx, wy = w_for("Z", -740), w_for("X", -880), w_for("Y", -1020)

    # normalise: w / (wx+wy+wz)
    s1 = C.node(nt, "ShaderNodeMath", (loc[0] + 900, loc[1] - 880), operation="ADD")
    C.wire(nt, wx, "Value", s1, 0)
    C.wire(nt, wy, "Value", s1, 1)
    s2 = C.node(nt, "ShaderNodeMath", (loc[0] + 1040, loc[1] - 880), operation="ADD")
    C.wire(nt, s1, "Value", s2, 0)
    C.wire(nt, wz, "Value", s2, 1)
    s2.use_clamp = False

    def norm(w, dy):
        d = C.node(nt, "ShaderNodeMath", (loc[0] + 1200, loc[1] + dy),
                   operation="DIVIDE")
        C.wire(nt, w, "Value", d, 0)
        C.wire(nt, s2, "Value", d, 1)
        return d

    nz, nx, ny = norm(wz, -740), norm(wx, -880), norm(wy, -1020)

    # blend XY over YZ over ZX by normalised weights
    m1 = C.node(nt, "ShaderNodeMix", (loc[0] + 1400, loc[1] + 180),
                data_type="RGBA", blend_type="MIX")
    C.wire(nt, planes[1], 2, m1, 6)          # YZ base
    C.wire(nt, planes[0], 2, m1, 7)          # XY over it
    C.wire(nt, nz, "Value", m1, "Factor")

    m2 = C.node(nt, "ShaderNodeMix", (loc[0] + 1600, loc[1]),
                data_type="RGBA", blend_type="MIX")
    C.wire(nt, m1, 2, m2, 6)
    C.wire(nt, planes[2], 2, m2, 7)          # ZX over the result
    C.wire(nt, ny, "Value", m2, "Factor")

    # Grazing-angle fade - a stand-in for the mip filtering procedurals do not get.
    # Cycles cannot prefilter a procedural, so wherever the surface is foreshortened
    # many weave cells fall inside one pixel and the twill aliases into a dot or comb
    # moire. A real lens blurs that detail away at the same angles. Fade the weave
    # toward its mid value as the surface turns edge-on: |dot(N, I)| is 1 head-on and
    # 0 at grazing.
    inc = C.node(nt, "ShaderNodeNewGeometry", (loc[0] + 1400, loc[1] - 1300))
    dot = C.node(nt, "ShaderNodeVectorMath", (loc[0] + 1600, loc[1] - 1300),
                 operation="DOT_PRODUCT")
    C.wire(nt, inc, "Normal", dot, 0)
    C.wire(nt, inc, "Incoming", dot, 1)
    facing = C.node(nt, "ShaderNodeMath", (loc[0] + 1780, loc[1] - 1300),
                    operation="ABSOLUTE")
    C.wire(nt, dot, "Value", facing, 0)
    ramp = C.node(nt, "ShaderNodeMapRange", (loc[0] + 1940, loc[1] - 1300))
    C.set_defaults(ramp, From_Min=0.10, From_Max=0.42, To_Min=0.0, To_Max=1.0)
    ramp.clamp = True
    C.wire(nt, facing, "Value", ramp, "Value")

    faded = C.node(nt, "ShaderNodeMix", (loc[0] + 2140, loc[1]),
                   data_type="RGBA", blend_type="MIX")
    faded.inputs[6].default_value = (0.5, 0.5, 0.5, 1.0)   # weave's mean value
    C.wire(nt, m2, 2, faded, 7)
    C.wire(nt, ramp, "Result", faded, "Factor")
    return faded, texco


def carbon_fibre(name="CarbonFibre", clearcoat=0.72, tint=(0.020, 0.021, 0.024)):
    """Lacquered exposed-weave carbon.

    D081: the weave was mapped at 760 repeats per metre - a 1.3 mm twill. That is
    far below a pixel at any sane render scale, so it averaged to nothing and
    every carbon panel behaved as a dead-flat mirror under a 0.045-roughness
    coat: flat endplates caught the cove and rendered as white plastic. Real 2x2
    twill is about 5 mm, i.e. ~190 repeats per metre, and the coat is lacquer,
    not chrome.
    """
    mat, nt, b = C.material(name)
    C.set_defaults(b, Base_Color=(*tint, 1.0), Metallic=0.0, Roughness=0.32,
                   IOR=1.46, Specular_IOR_Level=0.5)
    # D093: a 0.72 coat at 0.085 roughness over a near-black base turns every
    # flat panel and slim tube into a chrome mirror at grazing angles - the front
    # wing elements and endplates read as polished steel. Race lacquer is
    # satin, not chrome.
    b.inputs["Coat Weight"].default_value = 0.42
    b.inputs["Coat Roughness"].default_value = 0.16

    weave, _tc = _weave(nt)
    ramp = C.node(nt, "ShaderNodeValToRGB", (-800, 0))
    ramp.color_ramp.elements[0].position = 0.24
    ramp.color_ramp.elements[0].color = (*[c * 0.55 for c in tint], 1)
    ramp.color_ramp.elements[1].position = 0.78
    ramp.color_ramp.elements[1].color = (*[min(c * 2.2, 1.0) for c in tint], 1)
    C.wire(nt, weave, 2, ramp, "Fac")
    C.wire(nt, ramp, "Color", b, "Base Color")

    rr = C.node(nt, "ShaderNodeValToRGB", (-800, -230))
    rr.color_ramp.elements[0].position = 0.20
    rr.color_ramp.elements[0].color = (0.255, 0.255, 0.255, 1)
    rr.color_ramp.elements[1].position = 0.80
    rr.color_ramp.elements[1].color = (0.400, 0.400, 0.400, 1)
    C.wire(nt, weave, 2, rr, "Fac")
    C.wire(nt, rr, "Color", b, "Roughness")

    bump = C.node(nt, "ShaderNodeBump", (-560, -380))
    # D082: 0.42/2.2 mm made 33 mm suspension arms look knurled, like threaded
    # rod. Weave relief on real prepreg is a few tenths of a millimetre.
    # D108: on thin edges (floor rim, wing trailing edges) a strong weave bump
    # aliases into a comb pattern. Keep the relief gentle.
    bump.inputs["Strength"].default_value = 0.095
    bump.inputs["Distance"].default_value = 0.0005
    C.wire(nt, weave, 2, bump, "Height")
    C.wire(nt, bump, "Normal", b, "Normal")
    return mat


# --------------------------------------------------------------------------- #
# PULSE 01 - the livery
#
# The car is a signal path: air and data both enter at the nose as unstructured
# noise, are organised by the parts of the bodywork that work hardest, and leave
# the tail as clean parallel signal. The car's number is the `1` hiding inside
# the handle @aipulseda1ly, so the pulse line runs flat along the sidepod, throws
# a single vertical spike, and that spike is the numeral.
#
# Every field here is keyed off object-space coordinates, which for all fourteen
# LiveryPaint slots are CAR-LOCAL metres (tyre contact z = 0, nose tip x = +3.000,
# tail cap x = -2.470). No livery-bearing object carries an object-level
# transform, so one field is shared by every panel and the trace crosses panel
# gaps with no seam. That continuity is the thing that makes it look expensive.
#
# Two measurements govern every number below.
#
# 1. AgX destroys emitter saturation. Pushed through this scene's colour
#    management (s01_base: AgX, look "AgX - Medium High Contrast", exposure 0)
#    PULSE CYAN renders
#       S=0.40 -> #2D9DAE sat 0.74      S=6.0 -> #DDF8FC sat 0.12
#       S=1.30 -> #9AD2DC sat 0.30      S=9.0 -> #E8FDFF sat 0.09
#    A cyan emitter bright enough to bloom is not cyan any more, it is ice
#    white. So the colour is carried by the DIM sheaths and by the compositor's
#    own bloom halo (Glare, Bloom, threshold 1.4 scene-linear), which is the most
#    saturated cyan in the frame and costs nothing; the bright core carries none
#    of it. Nothing here exceeds S = 9.0 - at S = 22 a cyan emitter finally goes
#    neutral and clips.
#
# 2. tools/peep.py counts a pixel clipped only when ALL THREE channels are >= 250,
#    and crushed only when all three are <= 4. A chromatic cyan emitter holds red
#    at 232 even at S = 9, so it cannot register as clipped below S ~ 14; a
#    chromatic dark holds blue at 4x red, so VOID NAVY renders (7, 21, 40) and
#    cannot register as crushed. Chromatic extremes are metric-safe, neutral
#    extremes are not, and that is the only reason the base paint is allowed to
#    be this dark.
#
# The car is now near-black, so its silhouette is carried by the grazing flare
# and the pulse line rather than by the paint's diffuse. Expect mean luma and
# clipping to fall and crush to rise against the hq_v2 baseline (mean 0.3962,
# clipped 0.303 %, crushed 0.050 %). Local levers if a frame measures badly -
# never the light rig, scaling it 1.6 once took clipping from 1 % to 6.2 %:
#
#   crushed > 0.35 %          BASE_PAINT = ABYSS
#   clipped > 0.80 %          S_NUMERAL 9.0 -> 6.0
#   flare reads too weak      FLARE_BLEND 0.28 -> 0.36 (it is an exponent on
#                             |dot(N, I)|, so higher = wider band)
#   speckle/crawl on HeroLow   GRAPH_CELL 0.150 -> 0.220, or LIVERY_TIER = "C"
#   render time regression     LIVERY_TIER = "C"
# --------------------------------------------------------------------------- #

LIVERY_TIER = "B"          # "A" full, "B" delivered, "C" base + pulse + number

LIVERY_X0, LIVERY_X1 = -2.65, 3.10        # normalising span for every x field

# Palette, LINEAR. GRID BLUE is the banner's structural blue round-tripped exact
# (sRGB #206195); VOID NAVY renders at #071528 under this rig against the
# banner's own field of #030E23, so base and banner land on the same colour
# after AgX without anyone having to eyeball it.
VOID_NAVY = (0.0060, 0.0105, 0.0260)
ABYSS = (0.0090, 0.0150, 0.0340)          # crush-guard lift, see the note above
FLARE_TEAL = (0.0300, 0.1150, 0.1700)
FLARE_VIOLET = (0.0750, 0.0450, 0.1900)
PULSE_CYAN = (0.0284, 0.8070, 1.0000)
LAB_VIOLET = (0.3277, 0.0742, 1.0000)
# D009 again: 0.80 albedo lacquer clipped wherever the kick light grazed it.
# Sponsor white on a car under a 1100 W key is the same failure mode, and real
# vinyl is not paper - 0.60 measures #C9CCCE at 1.5x irradiance.
SIGNAL_WHITE = (0.5600, 0.6000, 0.6400)
CARBON_TINT = (0.0170, 0.0180, 0.0200)
COAT_TINT = (0.6800, 0.8200, 0.9000)
BASE_PAINT = VOID_NAVY

# Grazing flare. Blend is an exponent on |dot(N, I)| (see livery_paint), and the
# two ramp stops put the VOID-to-TEAL transition between 61 and 86 degrees off
# normal - a band about 12 % of a cylinder's screen radius wide.
FLARE_BLEND = 0.28
FLARE_LO, FLARE_HI = 0.34, 0.78

# Emission ladder. The bloom threshold is 1.4 scene-linear and PULSE CYAN carries
# 0.6554 luminance per unit strength, so S = 2.14 is the line between "a bright
# trace" and "a light source". Choose deliberately per element: the graph edges
# and the particle streams sit below it and stay saturated, the pulse core and
# the numeral sit above it and bloom.
S_PULSE_CORE = 6.00
S_PULSE_INNER = 1.30
S_PULSE_OUTER = 0.40
S_NUMERAL = 9.00
S_GRAPH_EDGE = 0.40
S_GRAPH_NODE = 3.20
S_STREAM = 0.35
# Violet is luminance-poor and needs S = 7.2 to bloom, by which point it is
# #E4D9FF at saturation 0.15 - lavender paper. Kept firmly sub-bloom.
S_VIOLET = 0.80
S_CEILING = 9.00

# The pulse line, in metres. Widths are diameters; the 12 mm core is 3.4 px at
# 1080p and 6.8 px at 4K. Nothing in this livery is narrower than 10 mm: at the
# worst camera that is 2.8 px, and procedurals get no mip filtering (D081, D108).
PULSE_DROP = 0.045
PULSE_CORE_HW = 0.006
PULSE_INNER_HW = 0.014
PULSE_OUTER_HW = 0.032
VIOLET_X0, VIOLET_X1 = -2.10, -2.38       # terminal 280 mm of the trace

# ORDER: 0 at the nose (noise), 1 behind the cockpit (signal).
ORDER_X0, ORDER_X1 = 3.00, -0.60
WORK_CROWN_W = 0.55                       # crown-height weight in the aero-work LUT

# Carbon dissolve at the nose: 100 % paint aft of x = +2.05, fully dissolved at
# the tip. 38 mm cells are ~23 px on CAM_HeroLow, which is a designed dissolve
# rather than mush.
DISSOLVE_X0, DISSOLVE_X1 = 2.05, 3.00
DISSOLVE_CELL = 0.038

# Node graph. 150 mm cells are a 42 px cell at 282 px/m - legible as a network,
# not as noise.
GRAPH_CELL = 0.150
GRAPH_ASPECT = 7.0                        # streamwise cell stretch at ORDER = 1
GRAPH_WARP = 0.075                        # metres of vector warp at ORDER = 0
EDGE_W_MIN, EDGE_W_MAX = 0.010, 0.022     # edge width driven by aero work
NODE_D = 0.026                            # junction disc diameter
NODE_WORK_GATE = 0.45                     # nodes only where the body works hard
GRAPH_UP0, GRAPH_UP1 = 0.35, 0.70         # object-space normal z gate

# Particle streams: 45 mm transverse pitch (12.8 px at 1080p), 10 mm hairlines,
# undulating along the flank by STREAM_WOBBLE.
STREAM_PITCH = 0.045
STREAM_W = 0.010
STREAM_WOBBLE = 0.030
STREAM_Z0, STREAM_Z1 = 0.300, 0.400
STREAM_Y = 0.45

# The numeral 1. Measured against the real flank: at x 0.20-0.41 the sidepod skin
# outboard of |y| = 0.52 spans z 0.325-0.555, so the brief's 260 mm glyph at
# z 0.355-0.615 would have folded its top 80 mm over the sidepod shoulder. 180 mm
# at z 0.360-0.540 sits inside the canvas with margin and is still 51 px at 1080p
# and 203 px at 4K - the first thing the eye lands on in the hero frame.
GLYPH_CX = 0.3055
GLYPH_Y = 0.52
GLYPH_Z0, GLYPH_Z1 = 0.360, 0.540
STEM_G0, STEM_G1 = 0.315, 0.375
FLAG_G0, FLAG_G1 = 0.236, 0.318
FLAG_Z0, FLAG_Z1 = 0.488, 0.552
FLAG_SLOPE = 0.5333                       # apex (0.315, 0.540) -> (0.240, 0.500)
FLAG_HALF_U = 0.0272                      # 48 mm measured perpendicular
GLYPH_SHEATH = 0.030

# Signal-bar wordmark: x0, x1, baseline, cap, pitch, |y| lo, |y| hi.
BAR_ROWS = [(-1.35, -0.30, 0.700, 0.110, 0.081, 0.0, 0.40)]
BAR_W = 0.035


def _u(x):
    return (x - LIVERY_X0) / (LIVERY_X1 - LIVERY_X0)


def _pulse_track():
    """(u, z) of the pulse line at all 27 loft stations.

    It is not a stripe at a constant height. It tracks the car's own shoulder,
    sitting PULSE_DROP below the sidepod-shoulder point of each station (field 8
    of the station tuple), so it sweeps z 0.267 at the nose tip, crests at 0.481
    behind the cockpit and falls to 0.093 at the tail cap. Reading it out of
    spec.BODY_STATIONS rather than hard-coding it is what stops the livery
    drifting from the geometry it is painted on.
    """
    return [(_u(s[0]), s[8] - PULSE_DROP) for s in spec.BODY_STATIONS][::-1]


def _aero_work():
    """(u, 0..1) of how hard each station of the bodywork is working.

    The graph is meant to be denser where the bodywork works hardest, which is
    computable rather than a matter of taste: differentiate the loft table. Rate
    of change of maximum section half-width, plus WORK_CROWN_W times rate of
    change of crown height, central differences, normalised to 1. Four peaks fall
    out - sidepod inlet +0.78, airbox rise -0.19, coke-bottle -1.08, tail taper
    -2.38 - and two dead zones, the whole nose and the flat sidepod top at +0.12.
    So every dense patch on this car is dense for a stated aerodynamic reason.
    """
    st = spec.BODY_STATIONS

    def halfwidth(s):
        return max(s[1], s[3], s[5], s[7], s[9], s[11])

    raw = []
    for i, s in enumerate(st):
        a, c = st[max(0, i - 1)], st[min(len(st) - 1, i + 1)]
        dx = c[0] - a[0]
        raw.append(abs((halfwidth(c) - halfwidth(a)) / dx)
                   + WORK_CROWN_W * abs((c[13] - a[13]) / dx))
    peak = max(raw)
    return [(_u(s[0]), v / peak) for s, v in zip(st, raw)][::-1]


def _ascending(stops):
    """ColorRamp positions must be inside [0, 1] and strictly increasing."""
    out, last = [], -1.0
    for pos, val in stops:
        p = min(1.0, max(0.0, float(pos)))
        if p <= last:
            p = min(1.0, last + 2e-4)
        out.append((p, val))
        last = p
    return out


def _lut(nt, loc, stops, src=None, src_out="Result", interpolation="LINEAR"):
    """A ColorRamp used as a 1-D lookup table over an object-space coordinate.

    The ramp's Fac input clamps to [0, 1] and its stop positions live in the same
    range, and car-local z and |y| are ALREADY inside it (the body spans z
    0.061-0.937, |y| <= 0.740). So a band on z or |y| is one node, not a
    normalise-then-threshold pair, and x only has to be normalised once into `u`.
    Greyscale stops are stored as (v, v, v): Cycles converts a colour socket to a
    float by luminance, and grey is grey under any weighting, so the value comes
    back out exactly.
    """
    r = C.node(nt, "ShaderNodeValToRGB", loc)
    r.color_ramp.interpolation = interpolation
    els = r.color_ramp.elements
    while len(els) > 1:
        els.remove(els[-1])
    for i, (pos, val) in enumerate(_ascending(stops)):
        col = (val, val, val, 1.0) if isinstance(val, (int, float)) else (*val, 1.0)
        if i == 0:
            els[0].position = pos
            els[0].color = col
        else:
            els.new(pos).color = col
    if src is not None:
        C.wire(nt, src, src_out, r, "Fac")
    return r


def _plateau(lo, hi, soft=0.004, ring=0.0, ring_level=0.0):
    """Stops for a 1-D box: 1 inside [lo, hi], `ring_level` for `ring` metres
    either side, 0 beyond.

    Combine two axes with MINIMUM, never MULTIPLY. A product squares the ring
    level in the corners, so the sheath would go dark exactly where two strokes
    of a glyph meet, which is the one place it has to be continuous.
    """
    if ring <= 0.0:
        return [(lo - soft, 0.0), (lo, 1.0), (hi, 1.0), (hi + soft, 0.0)]
    return [(lo - ring - soft, 0.0), (lo - ring, ring_level), (lo - soft, ring_level),
            (lo, 1.0), (hi, 1.0),
            (hi + soft, ring_level), (hi + ring, ring_level), (hi + ring + soft, 0.0)]


def _op(nt, loc, operation, a, b=None):
    """One Math node. `a` and `b` are each either (node, socket) or a constant."""
    n = C.node(nt, "ShaderNodeMath", loc, operation=operation)
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, tuple):
            C.wire(nt, v[0], v[1], n, i)
        else:
            n.inputs[i].default_value = float(v)
    return n


def _fmix(nt, loc, a, b, factor):
    """One float Mix. Socket 0 is the float Factor, 2/3 are A/B, output 0."""
    n = C.node(nt, "ShaderNodeMix", loc, data_type="FLOAT")
    for i, v in ((2, a), (3, b)):
        if isinstance(v, tuple):
            C.wire(nt, v[0], v[1], n, i)
        else:
            n.inputs[i].default_value = float(v)
    C.wire(nt, factor[0], factor[1], n, 0)
    return n


def _range(nt, loc, src, src_out, fmin, fmax, tmin=0.0, tmax=1.0):
    n = C.node(nt, "ShaderNodeMapRange", loc)
    C.set_defaults(n, From_Min=fmin, From_Max=fmax, To_Min=tmin, To_Max=tmax)
    n.clamp = True
    C.wire(nt, src, src_out, n, "Value")
    return n


def _signal_bars(nt, loc, sep, uu, ay, x0, x1, baseline, cap, pitch, y_lo, y_hi):
    """Thirteen vertical ticks of varying height on a wordmark baseline.

    The handle would have to be built from stroke SDFs - ~270 nodes for thirteen
    glyphs - and the pixel budget says it would not repay them: the engine-cover
    wordmark is 19 px per glyph at 1080p, which is texture rather than text. A
    signal-strength bar chart is indistinguishable from small type at that size,
    is four percent of the cost, and is itself on-brand. A 1-D Voronoi gives both
    the tick spacing and a stable per-tick random height in one texture.
    """
    v = C.node(nt, "ShaderNodeTexVoronoi", loc, voronoi_dimensions="1D", feature="F1")
    C.set_defaults(v, Scale=1.0 / pitch, Randomness=1.0)
    C.wire(nt, sep, "X", v, "W")

    tick = _range(nt, (loc[0] + 190, loc[1] + 110), v, "Distance",
                  0.5 * BAR_W / pitch, 0.5 * BAR_W / pitch + 0.045, 1.0, 0.0)
    rnd = C.node(nt, "ShaderNodeSeparateColor", (loc[0] + 190, loc[1] - 110))
    C.wire(nt, v, "Color", rnd, "Color")
    height = _range(nt, (loc[0] + 370, loc[1] - 110), rnd, "Red",
                    0.0, 1.0, 0.30 * cap, cap)

    zrel = _op(nt, (loc[0] + 370, loc[1] - 280), "SUBTRACT", (sep, "Z"), baseline)
    head = _op(nt, (loc[0] + 550, loc[1] - 180), "SUBTRACT",
               (height, "Result"), (zrel, "Value"))
    below = _range(nt, (loc[0] + 730, loc[1] - 180), head, "Value", 0.0, 0.004)
    above = _range(nt, (loc[0] + 730, loc[1] - 320), zrel, "Value", -0.002, 0.002)

    xg = _lut(nt, (loc[0] + 370, loc[1] + 260),
              _plateau(_u(x0), _u(x1), 0.002), uu, "Result")
    yg = _lut(nt, (loc[0] + 370, loc[1] + 60), _plateau(y_lo, y_hi, 0.030),
              ay, "Value")

    m1 = _op(nt, (loc[0] + 930, loc[1] + 60), "MULTIPLY",
             (tick, "Result"), (below, "Result"))
    m2 = _op(nt, (loc[0] + 1090, loc[1] + 60), "MULTIPLY",
             (m1, "Value"), (above, "Result"))
    m3 = _op(nt, (loc[0] + 1250, loc[1] + 60), "MULTIPLY",
             (m2, "Value"), (xg, "Color"))
    return _op(nt, (loc[0] + 1410, loc[1] + 60), "MULTIPLY",
               (m3, "Value"), (yg, "Color"))


def livery_paint(name="LiveryPaint", tier=None):
    """PULSE 01. See the block comment above for the concept and the numbers.

    Tier A adds the real triplanar weave under the nose dissolve; B is the
    delivered livery; C strips back to the base, the pulse line and the number,
    which is still a complete livery on its own if render time forces it.

    What is NOT here and why: the brief's letterform typography (a 270-node
    stroke-SDF set for @aipulseda1ly, SIGNAL > NOISE and EVERYWHERE AI HAPPENS)
    is skipped in favour of the bar abstraction - by the brief's own pixel budget
    the sidepod wordmark is 10 px per glyph at 1080p, so 270 nodes would buy
    illegible text on three of the four cameras. The sidepod wordmark row is
    dropped outright: measuring the real flank shows the panel dies above
    z = 0.56 outboard of |y| = 0.55, leaving a 50 mm strip above the pulse line
    where the brief assumed 95 mm, and the space below the line is already the
    particle-stream field.
    """
    tier = (tier or LIVERY_TIER).upper()
    full = tier in ("A", "B")

    mat, nt, b = C.material(name)
    C.set_defaults(b, Base_Color=(*BASE_PAINT, 1.0), Metallic=0.62,
                   Roughness=0.155, IOR=1.47)
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.022
    b.inputs["Coat Tint"].default_value = (*COAT_TINT, 1.0)

    # ----- shared object-space fields ------------------------------------- #
    texco = C.node(nt, "ShaderNodeTexCoord", (-2800, 0))
    sep = C.node(nt, "ShaderNodeSeparateXYZ", (-2620, 0))
    C.wire(nt, texco, "Object", sep, "Vector")

    uu = _range(nt, (-2440, 140), sep, "X", LIVERY_X0, LIVERY_X1)
    ay = _op(nt, (-2440, -20), "ABSOLUTE", (sep, "Y"))
    # ORDER runs the noise-to-signal transformation: 0 at the nose, 1 behind the
    # cockpit. One field drives the graph's randomness, its cell aspect and its
    # vector warp, so the change is one artwork being resolved rather than a
    # crossfade between two. WORK is the aero-work LUT that sets graph density.
    # Only the graph reads either of them, so tier C does not build them.
    order = work = None
    if full:
        order = _range(nt, (-2440, -180), sep, "X", ORDER_X0, ORDER_X1)
        work = _lut(nt, (-2260, 300), _aero_work(), uu, "Result")

    track = _lut(nt, (-2260, 60), _pulse_track(), uu, "Result")

    # ----- L0 base: VOID with a grazing flare ------------------------------ #
    # LayerWeight's Facing output, not its Fresnel output. Fresnel at Blend 0.28
    # is eta 1.39, which puts the whole 0.34-0.78 transition inside the last 12
    # degrees before grazing - about 2 % of a cylinder's screen radius, i.e. a
    # sliver nobody would see. Facing is 1 - |dot(N, I)|^(2*Blend), which puts the
    # same two ramp stops at 61-86 degrees and gives a band 12 % of the radius
    # wide: the shoulder-wide rim the design actually asks for. Blend still reads
    # in the intended direction, higher being more flare.
    lw = C.node(nt, "ShaderNodeLayerWeight", (-2000, 720))
    lw.inputs["Blend"].default_value = FLARE_BLEND
    flare = _lut(nt, (-1800, 720), [
        (FLARE_LO, VOID_NAVY), (FLARE_HI, FLARE_TEAL),
        # Violet is 0.17 % of the banner's lit pixels, so it gets 0.17 % of the
        # car: the last half-degree of silhouette, and nothing else but the tail.
        (0.92, FLARE_TEAL), (1.00, FLARE_VIOLET)], lw, "Facing")

    # Retained from the previous paint - dead-flat lacquer reads as CG.
    fl = C.node(nt, "ShaderNodeTexNoise", (-2000, 520))
    C.set_defaults(fl, Scale=1800.0, Detail=2.0, Roughness=0.85)
    C.wire(nt, texco, "Object", fl, "Vector")
    flaked = C.node(nt, "ShaderNodeMix", (-1560, 660), data_type="RGBA",
                    blend_type="SCREEN")
    flaked.inputs["Factor"].default_value = 0.06
    C.wire(nt, flare, "Color", flaked, 6)
    C.wire(nt, fl, "Fac", flaked, 7)

    peel = C.node(nt, "ShaderNodeTexNoise", (-2000, -1120))
    C.set_defaults(peel, Scale=140.0, Detail=2.0, Roughness=0.4)
    C.wire(nt, texco, "Object", peel, "Vector")
    bump = C.node(nt, "ShaderNodeBump", (-1700, -1120))
    bump.inputs["Strength"].default_value = 0.035
    bump.inputs["Distance"].default_value = 0.0025
    C.wire(nt, peel, "Fac", bump, "Height")
    normal_out = bump

    colour = flaked
    colour_out = 2

    # ----- L2 carbon dissolve at the nose ---------------------------------- #
    if full:
        dvor = C.node(nt, "ShaderNodeTexVoronoi", (-2000, 300), feature="F1")
        C.set_defaults(dvor, Scale=1.0 / DISSOLVE_CELL, Randomness=1.0)
        C.wire(nt, texco, "Object", dvor, "Vector")
        # The Color output is a uniform random per cell; take one channel rather
        # than its luminance, which would bunch the threshold around 0.35 and
        # make the dissolve front non-linear in x.
        dcell = C.node(nt, "ShaderNodeSeparateColor", (-1800, 300))
        C.wire(nt, dvor, "Color", dcell, "Color")
        dfront = _range(nt, (-2000, 160), sep, "X", DISSOLVE_X0, DISSOLVE_X1)
        dmask = _op(nt, (-1620, 300), "LESS_THAN",
                    (dcell, "Red"), (dfront, "Result"))

        if tier == "A":
            weave, _tc = _weave(nt, loc=(-5200, -2400))
            bare = C.node(nt, "ShaderNodeValToRGB", (-1620, 140))
            bare.color_ramp.elements[0].position = 0.24
            bare.color_ramp.elements[0].color = (*[c * 0.55 for c in CARBON_TINT], 1)
            bare.color_ramp.elements[1].position = 0.78
            bare.color_ramp.elements[1].color = (*[c * 2.2 for c in CARBON_TINT], 1)
            C.wire(nt, weave, 2, bare, "Fac")
        else:
            bare = None

        diss = C.node(nt, "ShaderNodeMix", (-1360, 520), data_type="RGBA",
                      blend_type="MIX")
        diss.inputs[7].default_value = (*CARBON_TINT, 1.0)
        C.wire(nt, colour, colour_out, diss, 6)
        if bare is not None:
            C.wire(nt, bare, "Color", diss, 7)
        C.wire(nt, dmask, "Value", diss, "Factor")
        colour, colour_out = diss, 2

        # Bare weave is not metallic and is not lacquer-smooth.
        metal = _fmix(nt, (-1360, 300), 0.62, 0.0, (dmask, "Value"))
        C.wire(nt, metal, 0, b, "Metallic")

        dn = C.node(nt, "ShaderNodeTexNoise", (-2000, 20))
        C.set_defaults(dn, Scale=36.0, Detail=3.0, Roughness=0.55)
        C.wire(nt, texco, "Object", dn, "Vector")
        drough = _lut(nt, (-1800, 20), [(0.32, 0.28), (0.70, 0.44)], dn, "Fac")
        rough = C.node(nt, "ShaderNodeMix", (-1360, 100), data_type="FLOAT")
        rough.inputs[2].default_value = 0.155
        C.wire(nt, drough, "Color", rough, 3)
        C.wire(nt, dmask, "Value", rough, 0)
        C.wire(nt, rough, 0, b, "Roughness")

    # ----- L3 the pulse line ------------------------------------------------ #
    zoff = _op(nt, (-2040, -60), "SUBTRACT", (sep, "Z"), (track, "Color"))
    dist = _op(nt, (-1880, -60), "ABSOLUTE", (zoff, "Value"))
    r_in = S_PULSE_INNER / S_PULSE_CORE
    r_out = S_PULSE_OUTER / S_PULSE_CORE
    profile = _lut(nt, (-1700, -60), [
        (0.0, 1.0),
        (PULSE_CORE_HW - 0.0010, 1.0),
        (PULSE_CORE_HW + 0.0015, r_in),
        (PULSE_INNER_HW - 0.0010, r_in),
        (PULSE_INNER_HW + 0.0025, r_out),
        (PULSE_OUTER_HW - 0.0020, r_out),
        (PULSE_OUTER_HW + 0.0025, 0.0),
    ], dist, "Value")
    pulse = _op(nt, (-1460, -60), "MULTIPLY", (profile, "Color"), S_PULSE_CORE)

    # ----- L4 the numeral 1 ------------------------------------------------- #
    # A race number reads correctly from both sides of the car, so the glyph is
    # mirrored about its own centre by the sign of y. On the -Y flank the nose is
    # to the viewer's right (CAM_FrontQuarter, the hero, shoots that side); on the
    # +Y flank it is to the left. Without this the number is mirrored in the hero
    # frame, which no team has ever shipped.
    sgn = _op(nt, (-2440, -420), "SIGN", (sep, "Y"))
    flip = _op(nt, (-2260, -420), "MULTIPLY", (sgn, "Value"), -1.0)
    gdx = _op(nt, (-2260, -560), "SUBTRACT", (sep, "X"), GLYPH_CX)
    gmul = _op(nt, (-2080, -480), "MULTIPLY", (gdx, "Value"), (flip, "Value"))
    g = _op(nt, (-1900, -480), "ADD", (gmul, "Value"), GLYPH_CX)

    # Core and sheath in one profile: the plateau carries S_NUMERAL, the 30 mm
    # ring carries the inner-sheath level, and MINIMUM keeps both intact where
    # strokes cross.
    ring = S_PULSE_INNER / S_NUMERAL
    stem_g = _lut(nt, (-1700, -400), _plateau(STEM_G0, STEM_G1, 0.004,
                                              GLYPH_SHEATH, ring), g, "Value")
    stem_z = _lut(nt, (-1700, -600), _plateau(GLYPH_Z0, GLYPH_Z1, 0.004,
                                              GLYPH_SHEATH, ring), sep, "Z")
    stem = _op(nt, (-1440, -500), "MINIMUM", (stem_g, "Color"), (stem_z, "Color"))

    # The flag is a 45-ish degree stroke, so it is a band on z - slope*g: two
    # maths nodes, then the same plateau machinery as the axis-aligned strokes.
    fslope = _op(nt, (-1700, -800), "MULTIPLY", (g, "Value"), FLAG_SLOPE)
    fu = _op(nt, (-1540, -800), "SUBTRACT", (sep, "Z"), (fslope, "Value"))
    flag_u_c = GLYPH_Z1 - FLAG_SLOPE * STEM_G0
    flag_u = _lut(nt, (-1360, -800), _plateau(flag_u_c - FLAG_HALF_U,
                                              flag_u_c + FLAG_HALF_U, 0.004,
                                              GLYPH_SHEATH, ring), fu, "Value")
    flag_g = _lut(nt, (-1360, -980), _plateau(FLAG_G0, FLAG_G1, 0.004,
                                              GLYPH_SHEATH, ring), g, "Value")
    flag_z = _lut(nt, (-1360, -1160), _plateau(FLAG_Z0, FLAG_Z1, 0.004,
                                               GLYPH_SHEATH, ring), sep, "Z")
    fl1 = _op(nt, (-1140, -880), "MINIMUM", (flag_u, "Color"), (flag_g, "Color"))
    flag = _op(nt, (-980, -880), "MINIMUM", (fl1, "Value"), (flag_z, "Color"))

    glyph = _op(nt, (-800, -640), "MAXIMUM", (stem, "Value"), (flag, "Value"))
    # Confine the mark to the sidepod flank. Without this the same x/z box paints
    # the numeral across the top of the monocoque, where |y| < 0.31.
    gy = _lut(nt, (-1700, -1000), [(GLYPH_Y, 0.0), (GLYPH_Y + 0.04, 1.0)],
              ay, "Value")
    gmask = _op(nt, (-640, -640), "MULTIPLY", (glyph, "Value"), (gy, "Color"))
    numeral = _op(nt, (-480, -640), "MULTIPLY", (gmask, "Value"), S_NUMERAL)

    emissive = [(pulse, "Value"), (numeral, "Value")]
    bars = None

    if full:
        # ----- surface-orientation fields ---------------------------------- #
        geo = C.node(nt, "ShaderNodeNewGeometry", (-2800, -1500))
        nobj = C.node(nt, "ShaderNodeVectorTransform", (-2620, -1500),
                      vector_type="NORMAL", convert_from="WORLD",
                      convert_to="OBJECT")
        C.wire(nt, geo, "Normal", nobj, "Vector")
        nsep = C.node(nt, "ShaderNodeSeparateXYZ", (-2440, -1500))
        C.wire(nt, nobj, "Vector", nsep, "Vector")
        # The graph is an upper-surface applique, and object space cannot select
        # objects - the object-space normal can.
        up = _range(nt, (-2260, -1500), nsep, "Z", GRAPH_UP0, GRAPH_UP1)

        # Grazing fade, exactly as _weave() does it: Cycles cannot prefilter a
        # procedural, so wherever the surface is foreshortened many cells fall
        # inside one pixel and the pattern aliases. A real lens blurs that away at
        # the same angles.
        dotni = C.node(nt, "ShaderNodeVectorMath", (-2620, -1700),
                       operation="DOT_PRODUCT")
        C.wire(nt, geo, "Normal", dotni, 0)
        C.wire(nt, geo, "Incoming", dotni, 1)
        facing = _op(nt, (-2440, -1700), "ABSOLUTE", (dotni, "Value"))
        fade = _range(nt, (-2260, -1700), facing, "Value", 0.10, 0.42)

        # ----- L5 the node graph -------------------------------------------- #
        warp_n = C.node(nt, "ShaderNodeTexNoise", (-2620, -2100))
        C.set_defaults(warp_n, Scale=2.6, Detail=2.0, Roughness=0.5)
        C.wire(nt, texco, "Object", warp_n, "Vector")
        warp_c = C.node(nt, "ShaderNodeVectorMath", (-2440, -2100),
                        operation="SUBTRACT")
        C.wire(nt, warp_n, "Color", warp_c, 0)
        warp_c.inputs[1].default_value = (0.5, 0.5, 0.5)
        warp_amp = _range(nt, (-2440, -2260), order, "Result", 0.0, 1.0,
                          GRAPH_WARP, 0.0)
        warp_s = C.node(nt, "ShaderNodeVectorMath", (-2260, -2100),
                        operation="SCALE")
        C.wire(nt, warp_c, "Vector", warp_s, 0)
        C.wire(nt, warp_amp, "Result", warp_s, "Scale")
        warped = C.node(nt, "ShaderNodeVectorMath", (-2080, -2100),
                        operation="ADD")
        C.wire(nt, texco, "Object", warped, 0)
        C.wire(nt, warp_s, "Vector", warped, 1)

        # At ORDER 0 the cells are isotropic, randomness 1 and the coordinate is
        # warped: scatter. At ORDER 1 randomness drops to 0.15, the warp is gone
        # and the cells are stretched GRAPH_ASPECT:1 downstream, so the same web
        # resolves into parallel streamwise lines. The brief stretched y and z
        # instead, but that divides the transverse cell pitch by 7 - a 21 mm
        # pitch is 6 px at 1080p and would alias. Stretching x keeps the pitch,
        # and the aspect ratio, which is what carries the read, is identical.
        gscale = _range(nt, (-2260, -1900), order, "Result", 0.0, 1.0,
                        1.0 / GRAPH_CELL, 1.0 / (GRAPH_CELL * GRAPH_ASPECT))
        gvec = C.node(nt, "ShaderNodeCombineXYZ", (-2080, -1900))
        C.wire(nt, gscale, "Result", gvec, "X")
        gvec.inputs["Y"].default_value = 1.0 / GRAPH_CELL
        gvec.inputs["Z"].default_value = 1.0 / GRAPH_CELL
        gmap = C.node(nt, "ShaderNodeMapping", (-1900, -2000))
        C.wire(nt, warped, "Vector", gmap, "Vector")
        C.wire(nt, gvec, "Vector", gmap, "Scale")

        grnd = _range(nt, (-2260, -2400), order, "Result", 0.0, 1.0, 1.0, 0.15)

        vor_e = C.node(nt, "ShaderNodeTexVoronoi", (-1700, -1900),
                       feature="DISTANCE_TO_EDGE")
        vor_e.inputs["Scale"].default_value = 1.0
        C.wire(nt, gmap, "Vector", vor_e, "Vector")
        C.wire(nt, grnd, "Result", vor_e, "Randomness")
        # A triple junction is exactly where you are close to an edge and far from
        # every cell centre, so F1 on the SAME vector, scale and randomness puts
        # the dots on the web at its junctions instead of floating inside cells.
        vor_f = C.node(nt, "ShaderNodeTexVoronoi", (-1700, -2200), feature="F1")
        vor_f.inputs["Scale"].default_value = 1.0
        C.wire(nt, gmap, "Vector", vor_f, "Vector")
        C.wire(nt, grnd, "Result", vor_f, "Randomness")

        # Distances come back in cell units, so a width in metres is w / cell.
        ew = _range(nt, (-1700, -1700), work, "Color", 0.0, 1.0,
                    0.5 * EDGE_W_MIN / GRAPH_CELL, 0.5 * EDGE_W_MAX / GRAPH_CELL)
        eratio = _op(nt, (-1500, -1800), "DIVIDE",
                     (vor_e, "Distance"), (ew, "Result"))
        edge = _range(nt, (-1320, -1800), eratio, "Value", 0.72, 1.0, 1.0, 0.0)
        # Sparse over the nose, erupting at the sidepod inlet and the airbox.
        eamp = _range(nt, (-1500, -1620), work, "Color", 0.05, 0.35, 0.25, 1.0)
        edge_a = _op(nt, (-1140, -1740), "MULTIPLY",
                     (edge, "Result"), (eamp, "Result"))

        far = _range(nt, (-1500, -2200), vor_f, "Distance", 0.50, 0.62)
        near = _range(nt, (-1500, -2360), vor_e, "Distance",
                      0.5 * NODE_D / GRAPH_CELL * 1.35, 0.5 * NODE_D / GRAPH_CELL)
        ngate = _range(nt, (-1500, -2520), work, "Color",
                       NODE_WORK_GATE - 0.05, NODE_WORK_GATE + 0.05)
        disc0 = _op(nt, (-1320, -2280), "MULTIPLY",
                    (far, "Result"), (near, "Result"))
        disc = _op(nt, (-1140, -2280), "MULTIPLY",
                   (disc0, "Value"), (ngate, "Result"))

        ge = _op(nt, (-960, -1740), "MULTIPLY", (edge_a, "Value"), S_GRAPH_EDGE)
        gn = _op(nt, (-960, -2280), "MULTIPLY", (disc, "Value"), S_GRAPH_NODE)
        gsum = _op(nt, (-800, -2000), "ADD", (ge, "Value"), (gn, "Value"))
        gup = _op(nt, (-640, -2000), "MULTIPLY", (gsum, "Value"), (up, "Result"))
        graph = _op(nt, (-480, -2000), "MULTIPLY",
                    (gup, "Value"), (fade, "Result"))
        emissive.append((graph, "Value"))

        # ----- L8 node relief ----------------------------------------------- #
        # 0.8 mm on a 26 mm disc, a 1:32 aspect, so the nodes read as physical
        # raised bosses catching a specular glint even when the emission is dark.
        # D082 (knurled suspension arms) and D108 (combed thin edges) are both
        # well above that. The bump takes the orange-peel bump's Normal as its own
        # so the two compose instead of one overwriting the other.
        relief0 = _op(nt, (-800, -2600), "MULTIPLY", (edge, "Result"), 0.55)
        relief1 = _op(nt, (-640, -2600), "ADD",
                      (relief0, "Value"), (disc, "Value"))
        relief = _op(nt, (-480, -2600), "MULTIPLY",
                     (relief1, "Value"), (up, "Result"))
        nbump = C.node(nt, "ShaderNodeBump", (-300, -2600))
        nbump.inputs["Strength"].default_value = 0.22
        nbump.inputs["Distance"].default_value = 0.0008
        C.wire(nt, relief, "Value", nbump, "Height")
        C.wire(nt, bump, "Normal", nbump, "Normal")
        normal_out = nbump

        # ----- L6 particle streams ------------------------------------------ #
        # A 1-D Voronoi on z, not a 3-D one on an anisotropically scaled vector.
        # Scaling y and z by 1/pitch and leaving x alone does give cells a metre
        # long, but Voronoi's distance-to-edge is measured in the SCALED space, so
        # the walls that face along x light up a band 220 mm wide - broad
        # transverse smears through what are supposed to be hairlines. Keying a
        # 1-D texture off z gives streamwise lines by construction, and a slow
        # noise added to z before the lookup makes them undulate along the flank
        # instead of ruling it like a comb.
        wmap = C.node(nt, "ShaderNodeMapping", (-2260, -3000))
        C.wire(nt, texco, "Object", wmap, "Vector")
        wmap.inputs["Scale"].default_value = (2.2, 2.2, 0.35)
        wnoise = C.node(nt, "ShaderNodeTexNoise", (-2080, -3000))
        C.set_defaults(wnoise, Scale=1.0, Detail=2.0, Roughness=0.5)
        C.wire(nt, wmap, "Vector", wnoise, "Vector")
        wcen = _op(nt, (-1900, -3000), "SUBTRACT", (wnoise, "Fac"), 0.5)
        wamp = _op(nt, (-1740, -3000), "MULTIPLY", (wcen, "Value"), STREAM_WOBBLE)
        wz = _op(nt, (-1580, -3000), "ADD", (sep, "Z"), (wamp, "Value"))
        vor_p = C.node(nt, "ShaderNodeTexVoronoi", (-1400, -3000),
                       voronoi_dimensions="1D", feature="F1")
        C.set_defaults(vor_p, Scale=1.0 / STREAM_PITCH, Randomness=1.0)
        C.wire(nt, wz, "Value", vor_p, "W")
        streak = _range(nt, (-1220, -3000), vor_p, "Distance",
                        0.5 * STREAM_W / STREAM_PITCH,
                        0.5 * STREAM_W / STREAM_PITCH + 0.06, 1.0, 0.0)
        pz = _lut(nt, (-1500, -3180), _plateau(STREAM_Z0, STREAM_Z1, 0.018),
                  sep, "Z")
        py = _lut(nt, (-1500, -3340), [(STREAM_Y, 0.0), (STREAM_Y + 0.06, 1.0)],
                  ay, "Value")
        s1 = _op(nt, (-1140, -3080), "MULTIPLY",
                 (streak, "Result"), (pz, "Color"))
        s2 = _op(nt, (-980, -3080), "MULTIPLY", (s1, "Value"), (py, "Color"))
        s3 = _op(nt, (-820, -3080), "MULTIPLY", (s2, "Value"), (fade, "Result"))
        stream = _op(nt, (-660, -3080), "MULTIPLY", (s3, "Value"), S_STREAM)
        emissive.append((stream, "Value"))

        # ----- L7 signal-bar wordmark --------------------------------------- #
        for i, (x0, x1, base_z, cap, pitch, y_lo, y_hi) in enumerate(BAR_ROWS):
            row = _signal_bars(nt, (-2600, -3800 - i * 900), sep, uu, ay,
                               x0, x1, base_z, cap, pitch, y_lo, y_hi)
            bars = row if bars is None else _op(
                nt, (-600, -3800 - i * 900), "MAXIMUM",
                (bars, "Value"), (row, "Value"))

    # ----- typography over the paint ---------------------------------------- #
    if bars is not None:
        vinyl = C.node(nt, "ShaderNodeMix", (-260, 400), data_type="RGBA",
                       blend_type="MIX")
        vinyl.inputs[7].default_value = (*SIGNAL_WHITE, 1.0)
        C.wire(nt, colour, colour_out, vinyl, 6)
        C.wire(nt, bars, "Value", vinyl, "Factor")
        colour, colour_out = vinyl, 2

    C.wire(nt, colour, colour_out, b, "Base Color")
    C.wire(nt, normal_out, "Normal", b, "Normal")

    # ----- emission: one strength, one colour, on the Principled ------------ #
    # A separate ShaderNodeEmission mixed at the output is view-independent and
    # reads as a decal stuck on the surface. Driving the Principled's own inputs
    # keeps the clearcoat over the trace, so it still catches the cove reflection
    # and rolls with the body - an electroluminescent channel under lacquer.
    total = emissive[0]
    for i, src in enumerate(emissive[1:]):
        n = _op(nt, (-300 + i * 160, -300), "ADD", total, src)
        total = (n, "Value")
    # Layers overlap - the pulse runs through the base of the numeral - and the
    # ladder only holds up to S = 9.0, so the sum is capped rather than allowed
    # to stack into a neutral white.
    capped = _op(nt, (340, -300), "MINIMUM", total, S_CEILING)

    violet = _lut(nt, (-2000, -180), [(_u(VIOLET_X1), 1.0), (_u(VIOLET_X0), 0.0)],
                  uu, "Result")
    ecol = C.node(nt, "ShaderNodeMix", (-40, -160), data_type="RGBA",
                  blend_type="MIX")
    ecol.inputs[6].default_value = (*PULSE_CYAN, 1.0)
    ecol.inputs[7].default_value = (*LAB_VIOLET, 1.0)
    C.wire(nt, violet, "Color", ecol, "Factor")
    vscale = _fmix(nt, (340, -480), 1.0, S_VIOLET / S_PULSE_CORE,
                   (violet, "Color"))
    estr = _op(nt, (500, -300), "MULTIPLY", (capped, "Value"), (vscale, 0))

    C.wire(nt, ecol, 2, b, "Emission Color")
    C.wire(nt, estr, "Value", b, "Emission Strength")
    return mat


def tyre_rubber(name="TyreRubber", compound=(0.150, 0.0115, 0.0125)):
    """Slick compound: near-black rubber with the coloured sidewall band.

    D027: the first version set Sheen Weight 0.12. Sheen is a broad grazing-angle
    white lobe, and on a barrel-shaped tyre almost the whole visible surface is at
    a grazing angle - it washed a 1.35 % albedo surface out to mid grey, brighter
    than the blue bodywork next to it, which is impossible for a diffuse surface
    under the same light. Sheen is now essentially off.

    The tyre mesh is built around +Z and then rotated onto the axle, so in OBJECT
    space the axle is still Z: radius = |xy|, sidewall = large |z|. That is what
    the compound band and the tread/sidewall split key off.
    """
    mat, nt, b = C.material(name)
    C.set_defaults(b, Base_Color=(0.0135, 0.0135, 0.0142, 1.0), Metallic=0.0,
                   Roughness=0.62, IOR=1.52, Specular_IOR_Level=0.30)
    b.inputs["Sheen Weight"].default_value = 0.015
    b.inputs["Sheen Roughness"].default_value = 0.5

    texco = C.node(nt, "ShaderNodeTexCoord", (-1500, 0))
    sep = C.node(nt, "ShaderNodeSeparateXYZ", (-1320, -260))
    C.wire(nt, texco, "Object", sep, "Vector")

    flat = C.node(nt, "ShaderNodeCombineXYZ", (-1140, -300))
    C.wire(nt, sep, "X", flat, "X")
    C.wire(nt, sep, "Y", flat, "Y")
    flat.inputs["Z"].default_value = 0.0
    radius = C.node(nt, "ShaderNodeVectorMath", (-960, -300), operation="LENGTH")
    C.wire(nt, flat, "Vector", radius, 0)

    axial = C.node(nt, "ShaderNodeMath", (-1140, -480), operation="ABSOLUTE")
    C.wire(nt, sep, "Z", axial, 0)

    # coloured compound band, sidewall only
    band = C.node(nt, "ShaderNodeValToRGB", (-760, -240))
    band.color_ramp.interpolation = "CONSTANT"
    e = band.color_ramp.elements
    e[0].position = 0.0
    e[0].color = (0, 0, 0, 1)
    # D041: 0.292-0.327 was a 35 mm band and the red was so bright it read as
    # neon pink. Real compound markings are ~22 mm and a deep, dark red.
    e[1].position = 0.3005
    e[1].color = (1, 1, 1, 1)
    e2 = band.color_ramp.elements.new(0.3225)
    e2.color = (0, 0, 0, 1)
    C.wire(nt, radius, "Value", band, "Fac")

    sidewall = C.node(nt, "ShaderNodeValToRGB", (-760, -480))
    sw = sidewall.color_ramp.elements
    sw[0].position = 0.082
    sw[0].color = (0, 0, 0, 1)
    sw[1].position = 0.104
    sw[1].color = (1, 1, 1, 1)
    C.wire(nt, axial, "Value", sidewall, "Fac")

    stripe = C.node(nt, "ShaderNodeMath", (-540, -360), operation="MULTIPLY")
    C.wire(nt, band, "Color", stripe, 0)
    C.wire(nt, sidewall, "Color", stripe, 1)

    col = C.node(nt, "ShaderNodeMix", (-330, -60), data_type="RGBA", blend_type="MIX")
    col.inputs[6].default_value = (0.0135, 0.0135, 0.0142, 1.0)
    col.inputs[7].default_value = (*compound, 1.0)
    C.wire(nt, stripe, "Value", col, "Factor")
    C.wire(nt, col, 2, b, "Base Color")

    # mould pebble; scale kept low enough not to alias at high zoom
    peb = C.node(nt, "ShaderNodeTexNoise", (-960, 220))
    C.set_defaults(peb, Scale=210.0, Detail=3.0, Roughness=0.55)
    C.wire(nt, texco, "Object", peb, "Vector")

    # tread is matte and scuffed; the sidewall is a touch glossier
    rr = C.node(nt, "ShaderNodeValToRGB", (-760, 220))
    rr.color_ramp.elements[0].position = 0.35
    rr.color_ramp.elements[0].color = (0.60, 0.60, 0.60, 1)
    rr.color_ramp.elements[1].position = 0.70
    rr.color_ramp.elements[1].color = (0.74, 0.74, 0.74, 1)
    C.wire(nt, peb, "Fac", rr, "Fac")
    rmix = C.node(nt, "ShaderNodeMix", (-540, 160), data_type="RGBA", blend_type="MIX")
    rmix.inputs[7].default_value = (0.48, 0.48, 0.48, 1)
    C.wire(nt, sidewall, "Color", rmix, "Factor")
    C.wire(nt, rr, "Color", rmix, 6)
    C.wire(nt, rmix, 2, b, "Roughness")

    bump = C.node(nt, "ShaderNodeBump", (-330, -600))
    bump.inputs["Strength"].default_value = 0.10
    bump.inputs["Distance"].default_value = 0.0005
    C.wire(nt, peb, "Fac", bump, "Height")
    C.wire(nt, bump, "Normal", b, "Normal")
    return mat


def brushed_titanium(name="Titanium"):
    """Brushed titanium with a real machining direction.

    The noise had NOTHING wired to its Vector input, so it fell back to Generated
    (per-object bounding box) space: a long swept part got 20-40 mm cloudy blobs
    while a small fastener got fine grain, and nothing had a brush direction.
    Whole-body inspection flagged it in 5 regions. Now driven from object space,
    stretched hard along one axis so it reads as linear brushing.
    """
    mat, nt, b = C.material(name)
    C.set_defaults(b, Base_Color=(0.55, 0.545, 0.525, 1.0), Metallic=1.0,
                   Roughness=0.30)
    texco = C.node(nt, "ShaderNodeTexCoord", (-1000, 0))
    mapn = C.node(nt, "ShaderNodeMapping", (-810, 0))
    mapn.inputs["Scale"].default_value = (26.0, 340.0, 340.0)  # anisotropic = brushed
    C.wire(nt, texco, "Object", mapn, "Vector")
    n = C.node(nt, "ShaderNodeTexNoise", (-620, 0))
    C.set_defaults(n, Scale=1.0, Detail=3.0, Roughness=0.5)
    C.wire(nt, mapn, "Vector", n, "Vector")
    r = C.node(nt, "ShaderNodeValToRGB", (-420, 0))
    r.color_ramp.elements[0].position = 0.35
    r.color_ramp.elements[0].color = (0.24, 0.24, 0.24, 1)
    r.color_ramp.elements[1].position = 0.72
    r.color_ramp.elements[1].color = (0.38, 0.38, 0.38, 1)
    C.wire(nt, n, "Fac", r, "Fac")
    C.wire(nt, r, "Color", b, "Roughness")
    return mat


def wheel_rim_mat(name="WheelRim"):
    mat, nt, b = C.material(name)
    C.set_defaults(b, Base_Color=(0.030, 0.031, 0.034, 1.0), Metallic=0.92,
                   Roughness=0.33)
    return mat


def matte_black(name="MatteBlack", rough=0.55):
    mat, nt, b = C.material(name)
    C.set_defaults(b, Base_Color=(0.010, 0.010, 0.011, 1.0), Metallic=0.0,
                   Roughness=rough, Specular_IOR_Level=0.28)
    return mat


def carbon_matte(name="CarbonMatte"):
    """Unlacquered structural weave — floors, fences, inner ducting."""
    mat = carbon_fibre(name=name, clearcoat=0.10, tint=(0.017, 0.018, 0.020))
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Coat Roughness"].default_value = 0.34
    return mat


def steel_fastener(name="SteelFastener"):
    """Same unwired-Vector bug as Titanium: the noise defaulted to Generated
    space, so grain scale varied with each fastener's bounding box."""
    mat, nt, b = C.material(name)
    C.set_defaults(b, Base_Color=(0.55, 0.555, 0.565, 1.0), Metallic=1.0,
                   Roughness=0.24)
    texco = C.node(nt, "ShaderNodeTexCoord", (-940, 0))
    mapn = C.node(nt, "ShaderNodeMapping", (-750, 0))
    mapn.inputs["Scale"].default_value = (900.0, 900.0, 900.0)
    C.wire(nt, texco, "Object", mapn, "Vector")
    n = C.node(nt, "ShaderNodeTexNoise", (-560, 0))
    C.set_defaults(n, Scale=1.0, Detail=2.0, Roughness=0.5)
    C.wire(nt, mapn, "Vector", n, "Vector")
    r = C.node(nt, "ShaderNodeValToRGB", (-360, 0))
    r.color_ramp.elements[0].position = 0.38
    r.color_ramp.elements[0].color = (0.19, 0.19, 0.19, 1)
    r.color_ramp.elements[1].position = 0.68
    r.color_ramp.elements[1].color = (0.32, 0.32, 0.32, 1)
    C.wire(nt, n, "Fac", r, "Fac")
    C.wire(nt, r, "Color", b, "Roughness")
    return mat


def carbon_ceramic(name="CarbonCeramic"):
    """Brake disc: dark grey C/C with a fine radial grain."""
    mat, nt, b = C.material(name)
    C.set_defaults(b, Base_Color=(0.052, 0.050, 0.048, 1.0), Metallic=0.0,
                   Roughness=0.58, Specular_IOR_Level=0.35)
    texco = C.node(nt, "ShaderNodeTexCoord", (-820, 0))
    w = C.node(nt, "ShaderNodeTexWave", (-620, 0), wave_type="RINGS",
               rings_direction="Z", wave_profile="SAW")
    C.set_defaults(w, Scale=220.0, Distortion=6.0, Detail=3.0)
    C.wire(nt, texco, "Object", w, "Vector")
    r = C.node(nt, "ShaderNodeValToRGB", (-400, 0))
    r.color_ramp.elements[0].position = 0.30
    r.color_ramp.elements[0].color = (0.50, 0.50, 0.50, 1)
    r.color_ramp.elements[1].position = 0.74
    r.color_ramp.elements[1].color = (0.66, 0.66, 0.66, 1)
    C.wire(nt, w, "Color", r, "Fac")
    C.wire(nt, r, "Color", b, "Roughness")
    bump = C.node(nt, "ShaderNodeBump", (-200, -240))
    bump.inputs["Strength"].default_value = 0.10
    bump.inputs["Distance"].default_value = 0.0004
    C.wire(nt, w, "Color", bump, "Height")
    C.wire(nt, bump, "Normal", b, "Normal")
    return mat


def anodised(name, base, rough=0.20):
    mat, nt, b = C.material(name)
    C.set_defaults(b, Base_Color=(*base, 1.0), Metallic=1.0, Roughness=rough)
    return mat


def display_glass(name="DisplayGlass"):
    mat, nt, b = C.material(name)
    C.set_defaults(b, Base_Color=(0.92, 0.94, 0.96, 1.0), Metallic=0.0,
                   Roughness=0.045, IOR=1.52, Transmission_Weight=1.0)
    b.inputs["Thin Wall"].default_value = True
    return mat


def display_emit(name="DisplayEmit"):
    """Steering wheel screen: dark panel with lit segments, not a white slab."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = C.node(nt, "ShaderNodeOutputMaterial", (520, 0))
    em = C.node(nt, "ShaderNodeEmission", (300, 0))
    em.inputs["Strength"].default_value = 2.6
    # A raw checker reads as a QR code / test pattern, not a dash. A real F1
    # readout is horizontal bands: a gear digit block, a bar-graph strip and a
    # few data rows. Banding the display vertically and only breaking it into
    # blocks horizontally gives that at a glance.
    texco = C.node(nt, "ShaderNodeTexCoord", (-820, 0))
    sep = C.node(nt, "ShaderNodeSeparateXYZ", (-640, -180))
    C.wire(nt, texco, "Object", sep, "Vector")

    rows = C.node(nt, "ShaderNodeTexWave", (-640, 120), wave_type="BANDS",
                  bands_direction="Z", wave_profile="SAW")
    C.set_defaults(rows, Scale=150.0, Distortion=0.0, Detail=0.0)
    C.wire(nt, texco, "Object", rows, "Vector")

    cols = C.node(nt, "ShaderNodeTexWave", (-640, -20), wave_type="BANDS",
                  bands_direction="Y", wave_profile="SAW")
    C.set_defaults(cols, Scale=90.0, Distortion=1.6, Detail=1.0)
    C.wire(nt, texco, "Object", cols, "Vector")

    seg = C.node(nt, "ShaderNodeMath", (-430, 40), operation="MULTIPLY")
    C.wire(nt, rows, "Color", seg, 0)
    C.wire(nt, cols, "Color", seg, 1)

    lit = C.node(nt, "ShaderNodeValToRGB", (-240, 40))
    lit.color_ramp.interpolation = "CONSTANT"
    el = lit.color_ramp.elements
    el[0].position = 0.0
    el[0].color = (0.004, 0.010, 0.014, 1.0)     # unlit pixels
    el[1].position = 0.42
    el[1].color = (0.05, 0.60, 0.22, 1.0)        # green segments
    e2 = lit.color_ramp.elements.new(0.78)
    e2.color = (0.78, 0.62, 0.06, 1.0)           # amber warning row
    C.wire(nt, seg, "Value", lit, "Fac")
    C.wire(nt, lit, "Color", em, "Color")
    C.wire(nt, em, "Emission", out, "Surface")
    return mat


def suede_grip(name="SuedeGrip"):
    """Alcantara-ish grip: matte, slightly fuzzy, with moulded finger relief."""
    mat, nt, b = C.material(name)
    C.set_defaults(b, Base_Color=(0.017, 0.017, 0.019, 1.0), Metallic=0.0,
                   Roughness=0.86, Specular_IOR_Level=0.22)
    # I repeated D027 here. Sheen is a broad grazing-angle WHITE lobe, and a grip
    # is a tube - almost all of it is at a grazing angle. At 0.32 it turned a
    # 1.7 % albedo alcantara grip into a light grey pillow, exactly as it turned
    # the tyres grey. Alcantara does have a faint nap sheen, but it is subtle.
    b.inputs["Sheen Weight"].default_value = 0.06
    b.inputs["Sheen Roughness"].default_value = 0.65
    texco = C.node(nt, "ShaderNodeTexCoord", (-700, 0))
    n = C.node(nt, "ShaderNodeTexNoise", (-500, 0))
    C.set_defaults(n, Scale=1400.0, Detail=3.0, Roughness=0.6)
    C.wire(nt, texco, "Object", n, "Vector")
    bump = C.node(nt, "ShaderNodeBump", (-260, -200))
    bump.inputs["Strength"].default_value = 0.28
    bump.inputs["Distance"].default_value = 0.0003
    C.wire(nt, n, "Fac", bump, "Height")
    C.wire(nt, bump, "Normal", b, "Normal")
    return mat


EXTRA_MATERIALS = {
    "CarbonMatte": carbon_matte,
    "SteelFastener": steel_fastener,
    "CarbonCeramic": carbon_ceramic,
    "AnodisedRed": lambda: anodised("AnodisedRed", (0.32, 0.020, 0.018), 0.18),
    "AnodisedGold": lambda: anodised("AnodisedGold", (0.72, 0.52, 0.16), 0.22),
    "DisplayGlass": display_glass,
    "DisplayEmit": display_emit,
    "SuedeGrip": suede_grip,
}


CAR = {
    "CarbonFibre": carbon_fibre,
    "LiveryPaint": livery_paint,
    "TyreRubber": tyre_rubber,
    "Titanium": brushed_titanium,
    "WheelRim": wheel_rim_mat,
    "MatteBlack": matte_black,
}


def build_car_materials():
    return {name: fn().name for name, fn in CAR.items()}


SHOWROOM = {
    "FloorPolished": floor_polished,
    "PlatformBody": platform_body,
    "TurntableTop": turntable_top,
    "GlassPanel": glass_panel,
    "MullionAlu": anodized_alu,
    "WallDark": wall_dark,
    "CeilingMat": ceiling_mat,
}


def build_showroom_materials():
    made = {}
    for name, fn in SHOWROOM.items():
        made[name] = fn().name
    # D005: seam glow at 22 blew the whole lower frame to clipped white and the
    # spot lenses were reading as pure paper. These are visible fixtures, not the
    # main light source - the area lights do that work.
    made["CoveEmit"] = emitter("CoveEmit", (1.0, 0.955, 0.90), 5.0).name
    made["SeamEmit"] = emitter("SeamEmit", (0.62, 0.78, 1.0), 4.5).name
    made["SpotEmit"] = emitter("SpotEmit", (1.0, 0.94, 0.86), 12.0).name
    return made
