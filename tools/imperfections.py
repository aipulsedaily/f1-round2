"""R2-014 / R2-015 — the shared, procedural imperfection layer.

    /opt/blender-5.2.0-linux-x64/blender -b world/beat1_audit.blend \
        --factory-startup -P tools/imperfections.py -- \
        --out world/beat1_imp.blend [--strength 1.0] \
        [--keep-cams MACRO_SW,MACRO_MB] [--debug Wear,Dust,Scratch] [--strip]

WHY THIS EXISTS
---------------
The macro audit rendered `SW` at the beat sheet's real distance (1.39 m focus,
50 mm, f/2.8, 3840x2160) and the 1:1 peep produced two failures:

  R2-015  no imperfection layer anywhere on the car. Every surface is pristine.
          The brief requires, for parts presented this close, "imperfection
          layers (subtle dust, fingerprint-level surface variation on paint)".
          The geometry and weave are excellent, which is exactly what makes the
          cleanliness read as CG: everything else in the frame says "real
          object", the absence of skin oil on a grip a driver holds says
          "render".

  R2-014  the LCD cover glass carries a single hard diagonal specular streak
          that terminates with a knife edge, because the surface is perfectly
          flat with perfectly uniform roughness.

Both are the same underlying fault — surfaces with no variation — so both are
fixed by one system rather than two patches.

WHAT IT IS, AND WHAT IT DELIBERATELY IS NOT
-------------------------------------------
It is ONE shared node group (`R2_Imperfection`) instanced into every car
material, driven entirely by GEOMETRY, so the layer lands where dirt and wear
physically go rather than being painted on:

  * Geometry > Pointiness, convex side  -> WEAR on exposed edges
  * Ambient Occlusion + Pointiness, concave side -> DUST in recesses, panel
    gaps, around fasteners, in button wells
  * world-normal Z                      -> dust settles harder on upward faces
  * fine noise at ~2-4 mm               -> MICRO surface variation, so no
    highlight is ever perfectly smooth
  * broad noise at ~7 cm                -> PATCH, which multiplies everything
    else so no effect is ever uniform
  * anisotropic Voronoi edge network    -> SCRATCH, handling marks

It is NOT a uniform grunge overlay and it is NOT one strength for every
surface. Each material class gets a different *kind* of imperfection, because a
driver's grip, carbon bodywork, machined titanium and rubber do not age alike:

  grip            skin oil and polish-wear   -> roughness DOWN, sheen UP
  paint           orange-peel micro normal + clearcoat break-up
  gloss carbon    fine dust + clearcoat micro-scratches
  machined metal  handling marks, edges rub POLISHED not rough
  anodised        edges rub through to pale bare aluminium
  rubber          a dulling film
  cover glass     non-planarity + roughness break-up  (R2-014)

CALIBRATION RULE
----------------
"If a viewer can point at 'the dirt effect', it is too strong." Every number in
K and AMOUNTS below was set by rendering at 3840x2160 / 512 on the 5090, peeping
at 1:1 and 2:1, and backing off — six passes over SW, MB and CORNER_FL, with FW
rendered at the end as a cluster that was never used to tune anything. Pass 1 was
2-15x too strong on every single material; the record is in DEFECT-LOG-R2.md.

Two-stage calibration, and the order matters:

    # 1. the MASKS, locally and almost free: where does the layer land?
    blender -b <scene> -P tools/imperfections.py -- --out work/_raw.blend \
        --debug Point,Occl,Micro
    blender -b work/_raw.blend -P tools/render_local.py -- --cam MACRO_SW \
        --res 1600 900 --samples 16 --standard --alpha --nocomp --isolate SW_ \
        --depth 8 -o work/raw_SW.png
    .venv/bin/python tools/mask_stats.py work/raw_SW.png

    # 2. only then the STRENGTHS, on the farm, at delivery resolution.

Stage 1 costs a minute on the local 1070 and sets the ramps from the geometry's
measured percentiles. Guessing a pointiness ramp and paying 65 s of 4K render per
guess is how a tuning pass becomes an afternoon.

COORDINATE CHOICE (a real trap, avoided on purpose)
---------------------------------------------------
Texture coordinates come from `Texture Coordinate > Object` pushed through a
`Vector Transform` (VECTOR, Object -> World). That applies the object's rotation
and scale but NOT its translation, which buys two things at once:

  * feature sizes are in real metres regardless of unapplied object scale — and
    this car has objects at 90-420x scale (the SW display and LED strips) and
    tyres at 1.2-1.6x Z, per the inventory's "surprises" table. Raw object
    coordinates would make the micro noise 420x too coarse on exactly the parts
    the camera looks at closest.
  * the field is glued to the object, so when Beat 1 flies 616 parts to their
    seats the texture does not swim. World-space Position would have looked
    correct in a still and crawled in motion.

IDEMPOTENCY
-----------
Every node this script creates is named `R2IMP_*` and every socket it takes over
is recorded in `material["r2imp"]`. `--strip` removes the layer and restores the
original links exactly, so the script can be re-run and re-tuned rather than
being a one-off edit.
"""

import argparse
import json
import os
import sys

import bpy

GROUP = "R2_Imperfection"
PFX = "R2IMP_"

# Pale warm grey. Dust is NOT black: it desaturates and lightens whatever is
# under it and raises roughness. Mixing toward black would read as soot.
DUST_RGB = (0.340, 0.325, 0.298, 1.0)
# Bare aluminium showing through anodising at a rubbed edge.
BARE_ALU = (0.620, 0.605, 0.585, 1.0)


# ---------------------------------------------------------------------------
# per-material calibration
# ---------------------------------------------------------------------------
# `cls` selects the recipe (what KIND of imperfection); the rest scale it.
# All amounts are multiplied by --strength, so a global "too much / too little"
# is one number, while the relative balance between materials is preserved.
AMOUNTS = {
    # --- carbon bodywork: fine dust, micro-scratches in the clearcoat -------
    "CarbonFibre":   dict(cls="carbon", dust=0.85, wear=0.85, micro=0.50,
                          scratch=0.45, coat=True),
    "CarbonMatte":   dict(cls="carbon", dust=1.00, wear=0.70, micro=0.85,
                          scratch=0.35, coat=False),
    # --- paint: fingerprint-level surface variation ------------------------
    "LiveryPaint":   dict(cls="paint", dust=0.80, wear=0.70, micro=0.45,
                          scratch=0.12),
    # --- machined metal: handling marks, edges polish rather than roughen --
    "Titanium":      dict(cls="metal", dust=0.90, wear=1.00, micro=0.65,
                          scratch=0.60),
    "SteelFastener": dict(cls="metal", dust=1.00, wear=1.10, micro=0.70,
                          scratch=0.65),
    "WheelRim":      dict(cls="metal", dust=0.90, wear=0.80, micro=0.60,
                          scratch=0.50),
    # --- anodised: rubs through to bare alu on edges -----------------------
    "AnodisedRed":   dict(cls="anodised", dust=0.85, wear=0.60, micro=0.45,
                          scratch=0.40),
    "AnodisedGold":  dict(cls="anodised", dust=0.85, wear=0.60, micro=0.45,
                          scratch=0.40),
    # --- matte plastics / composites ---------------------------------------
    "MatteBlack":    dict(cls="matte", dust=1.00, wear=0.70, micro=0.80,
                          scratch=0.40),
    "CarbonCeramic": dict(cls="matte", dust=0.60, wear=0.45, micro=0.70,
                          scratch=0.30),
    # --- the driver's grip: skin oil and polish-wear ------------------------
    "SuedeGrip":     dict(cls="grip", dust=0.35, wear=1.00, micro=1.00,
                          scratch=0.00),
    # --- rubber: a dulling film --------------------------------------------
    "TyreRubber":    dict(cls="rubber", dust=0.90, wear=0.50, micro=0.60,
                          scratch=0.00),
    # --- R2-014: the display cover glass ------------------------------------
    "DisplayGlass":  dict(cls="glass", dust=0.55, wear=0.00, micro=1.00,
                          scratch=0.00),
}

# Left alone ON PURPOSE — recorded here so "not done" and "decided" are
# distinguishable by a later reader.
SKIPPED = {
    "DisplayEmit": "emissive readout; dirt belongs on the glass in front of it, "
                   "not on the light source",
    "*SHOWROOM*": "room shell, not the car; out of the defect's scope",
    "*PROPS*": "set dressing, not the car",
    "*LIGHTS*": "emitters and fixtures",
}

# Shape of the shared drivers. These live on the group's interface, so a change
# here retunes the whole car at once — that is the point of the system.
# Calibrated from measured percentiles of the raw drivers over the SW cluster
# (`--debug Point,Occl,Micro` + tools/mask_stats.py), not by eye.
GRP = dict(
    ao_distance=0.020,    # m. Long rays turned every neighbouring part into a
                          # source of "dust"; a steering wheel is dense enough
                          # that 50 mm rays occluded its entire face.

    # Pointiness is NOT comparable between parts, and assuming it was is the
    # trap here. Measured medians: SW 0.533, MB 0.503, CORNER_FL 0.503 — the
    # steering wheel reads convex EVERYWHERE because it is 65 small parts, so a
    # threshold tight enough to pick edges on the monocoque paints the whole
    # wheel. The answer is a deliberately wide, smoothstepped ramp: the SW's
    # raised baseline becomes a faint general burnish (wear~0.08, which is
    # defensible — it is the most handled object on the car) while genuine
    # edges, the 99th percentile on every cluster, still reach 0.5+.
    edge_start=0.515,
    edge_full=0.615,

    # Occlusion at 20 mm, measured: SW p50 0.107 / p95 0.52; MB p95 0.070;
    # CORNER p95 0.133. Starting at 0.20 leaves 34% of the SW, 1.7% of MB and
    # 3.5% of CORNER able to hold any dust at all, and only the deepest ~1%
    # saturates. Anything lower greys out whole panels.
    cavity_start=0.200,
    cavity_full=0.620,

    micro_scale=380.0,    # ~2.6 mm features; ~10 px at the SW's 0.26 mm/px
    patch_scale=14.0,     # ~7 cm, so a 0.28 m steering wheel still sees
                          # patchiness rather than one constant value
    scratch_scale=125.0,  # ~8 mm cells -> ~0.6 mm scratches, ~2 px at 4K
)

# Blender's fBm noise Factor is not uniform on 0..1 — measured over three
# clusters it sits at mean 0.500 with p5/p95 of 0.40/0.60. Feeding it straight
# into an amplitude means the amplitude is a fifth of what it says, so the
# noise fields are normalised through this window before use and every K[]
# below is then a true peak deviation.
NOISE_LO, NOISE_HI = 0.385, 0.615

# Base magnitudes, in the units of the socket they modify. Multiplied by the
# per-material scalars above and by --strength.
K = dict(
    # ---- PASS 2 -------------------------------------------------------------
    # Pass 1 rendered at these values x2-15 and every one of them was visible as
    # an effect: the carbon twill turned to sandpaper, the anodised buttons
    # crackled, the paint clearcoat went from mirror to sandblasted, titanium
    # read as corroded castings, and the cover glass looked like crumpled
    # cellophane. The dominant error was in the BUMP terms and is worth stating
    # plainly, because the arithmetic is not obvious:
    #
    #   A Bump node's tilt comes from the height field's DERIVATIVE, and an fBm
    #   noise's derivative is dominated by its finest octave, not by its base
    #   wavelength. At Detail 5 with Roughness 0.55 the octave gradients go as
    #   (0.55*2)^i, so the normalised field's slope is ~3.5x what the base
    #   wavelength predicts. Sizing a bump from "amplitude over half a
    #   wavelength" therefore under-predicts the tilt several-fold, and 1.3 deg
    #   of intended orange peel rendered as roughly 5-9 deg of visible crumple.
    #
    # The fix is both: Detail on the bump-driving noise is down to 1.5, and the
    # distances are down again on top of that.
    # dust
    dust_rough=0.070,     # roughness added where dust settles
    dust_tint=0.070,      # mix toward DUST_RGB
    # wear (convex edges)
    wear_rough=0.035,     # coated surfaces: edges roughen
    wear_polish=0.045,    # bare metal: edges polish SMOOTHER
    wear_lift=0.055,      # base colour lifted on worn edges
    wear_coat=0.160,      # clearcoat thinning on edges
    # Pass 2 still read as damage on the small anodised buttons: Wear is
    # patchy on an 8 mm dome, so mixing 9% pale bare-aluminium into a saturated
    # red desaturated it in blotches. Rub-through is real but it belongs on a
    # hard edge, not across a cap face.
    wear_anod=0.040,      # anodising rubbing through to bare alu
    # micro
    micro_rough=0.018,    # peak +/- roughness deviation
    micro_bump=0.000032,  # metres; ~0.35 deg of tilt at Detail 1.5
    micro_bump_str=0.18,
    # A CLEARCOAT'S ROUGHNESS MUST BE MODULATED IN PROPORTION, NOT BY ADDITION.
    # LiveryPaint's Coat Roughness is 0.022, so pass 3's absolute +/-0.006 was a
    # +/-27% swing, and at grazing incidence — where the coat's Fresnel is near 1
    # and it is mirroring a large bright source — that rendered as a crazed,
    # flaking-lacquer cell pattern. The same absolute number on carbon's 0.16
    # coat is +/-4% and was invisible, which is exactly why one constant could
    # not serve both. These are fractions of each material's own coat roughness.
    coat_micro_rel=0.20,
    coat_scratch_rel=0.18,
    coat_dust_rel=0.50,
    coat_bump=0.00012,    # orange-peel on the clearcoat; ~1.25 deg
    coat_bump_str=0.20,
    # scratch
    scratch_rough=0.020,
    # grip
    oil_rough=0.058,      # skin oil polishing suede
    oil_sheen=0.030,
    oil_spec=0.045,
    oil_darken=0.075,
    # glass (R2-014)
    glass_wave=0.00022,   # bump distance for the gentle non-planarity, metres
    glass_wave_str=0.220, # -> ~0.37 deg. At 1.0 deg (pass 2) the highlight did
                          # break up, but into hard-edged facets that read as
                          # crumpled foil. Most of the softening should come
                          # from roughness, which spreads a highlight smoothly
                          # and cannot distort the readout behind the glass at
                          # all; the normal only needs to stop the termination
                          # being a straight line.
    glass_rough=0.013,    # roughness break-up amplitude
    glass_base=0.010,     # constant lift: 0.045 is near-mirror, and a mirror
                          # ends a highlight exactly where its geometry ends
    glass_smudge=0.005,
    # paint orange peel gets its own, longer wavelength: at the shared 2.6 mm
    # micro scale a clearcoat perturbation reads as hammered metal, because the
    # wobble is finer than the reflected features. Real orange peel is a slow
    # 5-15 mm undulation.
    paint_peel_scale=140.0,
    # Cut hard again at pass 5. At a grazing angle a clearcoat's Fresnel is near
    # 1 and it is mirroring a hard-edged bright source, so the reflection flips
    # between "ceiling" and "dark" over a fraction of a degree: the VISIBILITY of
    # a coat-normal perturbation there is close to a step function of nothing to
    # do with its amplitude. Halving 0.00018 barely changed the picture; this is
    # a 6x cut, to ~0.12 deg, which is the point where the ripple stops reading
    # as crazed lacquer and starts reading as a panel that is not a mirror.
    paint_peel=0.00003,
    paint_peel_str=0.20,
)


# ---------------------------------------------------------------------------
# small node helpers
# ---------------------------------------------------------------------------
class Tree:
    """Thin wrapper that names every node it makes `R2IMP_n` so the layer can be
    found and stripped again without guessing."""

    def __init__(self, nt):
        self.nt = nt
        self.n = 0
        self.frame = None

    def new(self, idname, **kw):
        node = self.nt.nodes.new(idname)
        node.name = f"{PFX}{self.n:03d}"
        self.n += 1
        node.label = kw.pop("label", "")
        for k, v in kw.items():
            setattr(node, k, v)
        return node

    def link(self, out, inp):
        self.nt.links.new(out, inp)

    def plug(self, inp, src):
        if hasattr(src, "is_output"):
            self.nt.links.new(src, inp)
        else:
            inp.default_value = src

    def math(self, op, a, b=None, clamp=False, label=""):
        n = self.new("ShaderNodeMath", label=label)
        n.operation = op
        n.use_clamp = clamp
        self.plug(n.inputs[0], a)
        if b is not None:
            self.plug(n.inputs[1], b)
        return n.outputs[0]

    def maprange(self, v, fmin, fmax, tmin=0.0, tmax=1.0, smooth=True, label=""):
        n = self.new("ShaderNodeMapRange", label=label)
        n.interpolation_type = "SMOOTHSTEP" if smooth else "LINEAR"
        n.clamp = True
        self.plug(n.inputs[0], v)
        for i, val in ((1, fmin), (2, fmax), (3, tmin), (4, tmax)):
            self.plug(n.inputs[i], val)
        return n.outputs[0]

    def mixf(self, fac, a, b, label=""):
        n = self.new("ShaderNodeMix", label=label)
        n.data_type = "FLOAT"
        self.plug(n.inputs[0], fac)
        self.plug(n.inputs[2], a)
        self.plug(n.inputs[3], b)
        return n.outputs[0]

    def mixrgb(self, fac, a, b, label=""):
        n = self.new("ShaderNodeMix", label=label)
        n.data_type = "RGBA"
        n.blend_type = "MIX"
        n.clamp_factor = True
        self.plug(n.inputs[0], fac)
        self.plug(n.inputs[6], a)
        self.plug(n.inputs[7], b)
        return n.outputs[2]

    def clamp(self, v, lo, hi):
        n = self.new("ShaderNodeClamp")
        self.plug(n.inputs[0], v)
        n.inputs[1].default_value = lo
        n.inputs[2].default_value = hi
        return n.outputs[0]


def cur(sock):
    """Whatever the socket carries today: an upstream output, or its constant."""
    if sock.is_linked:
        return sock.links[0].from_socket
    try:
        v = sock.default_value
    except AttributeError:
        return 0.0
    return tuple(v) if hasattr(v, "__len__") else v


# ---------------------------------------------------------------------------
# the shared driver group
# ---------------------------------------------------------------------------
def build_group():
    """One node group, instanced into every touched material.

    Everything downstream reads from these outputs, which is what makes this a
    SYSTEM rather than 13 hand edits: retuning the cavity ramp here retunes the
    whole car at once.
    """
    ng = bpy.data.node_groups.get(GROUP)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(GROUP, "ShaderNodeTree")
    ifc = ng.interface

    def sock_in(name, default, lo=None, hi=None, desc=""):
        s = ifc.new_socket(name, in_out="INPUT", socket_type="NodeSocketFloat")
        s.default_value = default
        if lo is not None:
            s.min_value = lo
        if hi is not None:
            s.max_value = hi
        s.description = desc
        return s

    sock_in("AO Distance", GRP["ao_distance"], 0.0, 2.0,
            "metres; how deep a recess has to be to collect dust")
    sock_in("Edge Start", GRP["edge_start"], 0.0, 1.0,
            "pointiness where edge wear begins")
    sock_in("Edge Full", GRP["edge_full"], 0.0, 1.0,
            "pointiness where edge wear saturates")
    sock_in("Cavity Start", GRP["cavity_start"], 0.0, 1.0,
            "occlusion where dust begins")
    sock_in("Cavity Full", GRP["cavity_full"], 0.0, 1.0,
            "occlusion where dust saturates")
    sock_in("Micro Scale", GRP["micro_scale"], 1.0, 20000.0,
            "features per metre")
    sock_in("Patch Scale", GRP["patch_scale"], 0.01, 500.0, "features per metre")
    sock_in("Scratch Scale", GRP["scratch_scale"], 1.0, 20000.0,
            "scratch cell density per metre")

    for nm in ("Wear", "Dust", "Micro", "Patch", "Scratch", "Open",
               "Occl", "Point"):
        ifc.new_socket(nm, in_out="OUTPUT", socket_type="NodeSocketFloat")
    ifc.new_socket("Coord", in_out="OUTPUT", socket_type="NodeSocketVector")

    t = Tree(ng)
    gi = t.new("NodeGroupInput"); gi.location = (-1400, 0)
    go = t.new("NodeGroupOutput"); go.location = (1500, 0)
    I = {s.name: gi.outputs[s.name] for s in gi.outputs if s.name}

    # -- object-anchored, world-metric coordinates -------------------------
    tc = t.new("ShaderNodeTexCoord"); tc.location = (-1200, -600)
    vt = t.new("ShaderNodeVectorTransform"); vt.location = (-1000, -600)
    vt.vector_type = "VECTOR"          # linear part only: no translation, so
    vt.convert_from = "OBJECT"         # the field cannot swim when the part flies
    vt.convert_to = "WORLD"
    t.link(tc.outputs["Object"], vt.inputs[0])
    coord = vt.outputs[0]

    # -- curvature ---------------------------------------------------------
    geo = t.new("ShaderNodeNewGeometry"); geo.location = (-1200, 400)
    pnt = geo.outputs["Pointiness"]
    wear = t.maprange(pnt, I["Edge Start"], I["Edge Full"], 0.0, 1.0,
                      label="convex -> wear")
    # concave side, mirrored about 0.5
    c_lo = t.math("SUBTRACT", 1.0, I["Edge Start"])
    c_hi = t.math("SUBTRACT", 1.0, I["Edge Full"])
    concave = t.maprange(pnt, c_lo, c_hi, 0.0, 1.0, label="concave -> crevice")

    # -- occlusion ---------------------------------------------------------
    # only_local stays OFF: the dust that reads is the dust in the gap between a
    # button cap and its bezel ring, and those are separate objects. Cluster
    # clearance in the exploded field is >=120 mm against a 50 mm ray, so no
    # cluster can dirty its neighbour.
    ao = t.new("ShaderNodeAmbientOcclusion"); ao.location = (-1200, 100)
    # 1 ray per shading sample. The AO node's own `samples` exists for low-spp
    # previews; at 512 path samples the integrator averages it 512 times over,
    # and 8 rays multiplied the cost of the whole layer for no converged gain.
    ao.samples = 2
    ao.inside = False
    ao.only_local = False
    t.plug(ao.inputs["Distance"], I["AO Distance"])
    openness = ao.outputs["AO"]
    occl = t.math("SUBTRACT", 1.0, openness, clamp=True)
    cav = t.maprange(occl, I["Cavity Start"], I["Cavity Full"], 0.0, 1.0,
                     label="occlusion -> cavity")

    # -- dust settles on horizontal-ish faces ------------------------------
    sep = t.new("ShaderNodeSeparateXYZ"); sep.location = (-1000, 250)
    t.link(geo.outputs["Normal"], sep.inputs[0])
    upface = t.maprange(sep.outputs["Z"], -0.35, 0.55, 0.30, 1.0,
                        label="normal.z -> settling")

    # -- noise fields ------------------------------------------------------
    def noise(scale, detail, rough, loc, lab):
        n = t.new("ShaderNodeTexNoise", label=lab); n.location = loc
        n.noise_dimensions = "3D"
        t.plug(n.inputs["Vector"], coord)
        t.plug(n.inputs["Scale"], scale)
        n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        return n.outputs["Factor"]

    micro_raw = noise(I["Micro Scale"], 1.5, 0.55, (-800, -900), "micro")
    micro = t.maprange(micro_raw, NOISE_LO, NOISE_HI, 0.0, 1.0,
                       label="micro normalised")
    patch_raw = noise(I["Patch Scale"], 3.0, 0.60, (-800, -1150), "patch")
    patch = t.maprange(patch_raw, 0.420, 0.580, 0.0, 1.0, label="patch shaped")

    # -- scratches: two anisotropic Voronoi edge networks -------------------
    # Distance-to-edge on a cell field stretched 30:1 gives long thin lines;
    # crossing two of them at different angles reads as random handling swirl
    # instead of brushed metal.
    def scratch_field(rot, squash, loc):
        mp = t.new("ShaderNodeMapping"); mp.location = loc
        t.link(coord, mp.inputs["Vector"])
        mp.inputs["Rotation"].default_value = rot
        # squash a DIFFERENT axis in each field. Rotating alone was not enough:
        # on a flat panel both fields still ran the same way on screen and read
        # as brushed metal rather than as random handling swirl.
        t.plug(mp.inputs["Scale"], squash)
        vr = t.new("ShaderNodeTexVoronoi"); vr.location = (loc[0] + 200, loc[1])
        vr.feature = "DISTANCE_TO_EDGE"
        vr.voronoi_dimensions = "3D"
        t.link(mp.outputs["Vector"], vr.inputs["Vector"])
        t.plug(vr.inputs["Scale"], I["Scratch Scale"])
        vr.inputs["Randomness"].default_value = 1.0
        # Line WIDTH matters more than it looks: distance-to-edge is measured
        # in cell units, so 0.010 gave 0.08 mm scratches — a third of a pixel at
        # the SW's 0.26 mm/px, which renders as aliasing sparkle rather than as
        # a scratch. 0.075 of an 8 mm cell is ~0.6 mm, about 2 px at 4K.
        return t.maprange(vr.outputs["Distance"], 0.0, 0.050, 1.0, 0.0,
                          label="edge -> scratch")

    s1 = scratch_field((0.0, 0.0, 0.0), (1.0, 0.032, 1.0), (-800, -1450))
    s2 = scratch_field((0.9, 0.35, 1.15), (0.032, 1.0, 1.0), (-800, -1750))
    scratch = t.math("MAXIMUM", s1, s2, label="scratch union")
    # sparse: only where the patch mask allows, so the whole part is never
    # covered in scratches at once
    scratch = t.math("MULTIPLY", scratch,
                     t.maprange(patch_raw, 0.50, 0.62, 0.00, 1.0),
                     label="scratch sparsity")

    # -- dust assembly -----------------------------------------------------
    dust = t.math("MAXIMUM", cav, t.math("MULTIPLY", concave, 0.55))
    dust = t.math("MULTIPLY", dust, upface)
    dust = t.math("MULTIPLY", dust,
                  t.maprange(patch, 0.0, 1.0, 0.40, 1.05),
                  label="dust patchiness")
    dust = t.clamp(dust, 0.0, 1.0)

    for nm, s in (("Wear", wear), ("Dust", dust), ("Micro", micro),
                  ("Patch", patch), ("Scratch", scratch), ("Open", openness),
                  # raw, unshaped drivers: these exist so the ramps above can be
                  # set from a measured histogram of the actual geometry instead
                  # of from a guess at what "pointiness on a bevel" comes to
                  ("Occl", occl), ("Point", pnt)):
        t.link(s, go.inputs[nm])
    t.link(coord, go.inputs["Coord"])
    return ng


# ---------------------------------------------------------------------------
# per-material injection
# ---------------------------------------------------------------------------
def find_bsdf(mat):
    out = next((n for n in mat.node_tree.nodes
                if n.bl_idname == "ShaderNodeOutputMaterial"), None)
    if out is None or not out.inputs["Surface"].is_linked:
        return None
    n = out.inputs["Surface"].links[0].from_node
    return n if n.bl_idname == "ShaderNodeBsdfPrincipled" else None


def snapshot(bsdf, name):
    """What a socket carries RIGHT NOW, in a form `strip` can put back.

    Must be taken on FIRST touch only. Several recipes modify the same socket
    twice (roughness picks up dust, then scratches), and re-snapshotting would
    record this script's own output as the original — an undo that quietly
    bakes the layer in permanently.
    """
    s = bsdf.inputs[name]
    if s.is_linked:
        l = s.links[0]
        return {"link": [l.from_node.name, l.from_socket.identifier]}
    v = s.default_value
    return {"value": list(v) if hasattr(v, "__len__") else v}


def strip(mat):
    """Undo a previous injection exactly: delete the tagged nodes, then put the
    original links / constants back from the recorded backup."""
    if "r2imp" not in mat.keys() or not mat.use_nodes:
        return False
    nt = mat.node_tree
    for n in [n for n in nt.nodes if n.name.startswith(PFX)]:
        nt.nodes.remove(n)
    bsdf = find_bsdf(mat)
    rec = json.loads(mat["r2imp"])
    if bsdf:
        for nm, d in rec.items():
            s = bsdf.inputs.get(nm)
            if s is None:
                continue
            if "link" in d:
                src = nt.nodes.get(d["link"][0])
                if src:
                    so = next((o for o in src.outputs
                               if o.identifier == d["link"][1]), None)
                    if so:
                        nt.links.new(so, s)
            else:
                v = d["value"]
                s.default_value = v if not isinstance(v, list) else v
    del mat["r2imp"]
    return True


def inject(mat, amt, S):
    """Apply the recipe named by amt['cls'] to `mat`, scaled by S."""
    bsdf = find_bsdf(mat)
    if bsdf is None:
        return None
    nt = mat.node_tree
    t = Tree(nt)
    t.n = 1 + max([int(n.name[len(PFX):]) for n in nt.nodes
                   if n.name.startswith(PFX) and n.name[len(PFX):].isdigit()]
                  or [-1])

    g = t.new("ShaderNodeGroup"); g.node_tree = bpy.data.node_groups[GROUP]
    g.location = (bsdf.location.x - 1000, bsdf.location.y - 700)
    G = {o.name: o for o in g.outputs}

    d = amt["dust"] * S
    w = amt["wear"] * S
    m = amt["micro"] * S
    sc = amt["scratch"] * S
    cls = amt["cls"]

    orig = {}

    def take(names):
        for nm in names:
            if nm not in orig and nm in bsdf.inputs:
                orig[nm] = snapshot(bsdf, nm)

    def add_rough(sock_name, terms, lo=0.008, hi=1.0):
        """roughness' = clamp(roughness + sum(terms))"""
        s = bsdf.inputs.get(sock_name)
        if s is None:
            return
        take([sock_name])
        acc = cur(s)
        for term in terms:
            acc = t.math("ADD", acc, term)
        t.plug(s, t.clamp(acc, lo, hi))

    def rel_rough(sock_name, terms, lo=0.004, hi=0.6):
        """roughness' = clamp(roughness * (1 + sum(terms))) — proportional, so
        the same recipe is sane on a 0.022 clearcoat and on a 0.16 one."""
        sk = bsdf.inputs.get(sock_name)
        if sk is None:
            return
        take([sock_name])
        acc = None
        for term in terms:
            acc = term if acc is None else t.math("ADD", acc, term)
        t.plug(sk, t.clamp(t.math("MULTIPLY", cur(sk),
                                  t.math("ADD", 1.0, acc)), lo, hi))

    def tint(sock_name, color, fac):
        s = bsdf.inputs.get(sock_name)
        if s is None:
            return
        take([sock_name])
        t.plug(s, t.mixrgb(fac, cur(s), color))

    def bump(sock_name, height, strength, distance):
        s = bsdf.inputs.get(sock_name)
        if s is None:
            return
        take([sock_name])
        b = t.new("ShaderNodeBump", label="R2 micro relief")
        b.inputs["Strength"].default_value = strength
        b.inputs["Distance"].default_value = distance
        t.link(height, b.inputs["Height"])
        if s.is_linked:
            t.link(s.links[0].from_socket, b.inputs["Normal"])
        t.plug(s, b.outputs["Normal"])

    def scale_sock(sock_name, factor_socket):
        s = bsdf.inputs.get(sock_name)
        if s is None:
            return
        take([sock_name])
        t.plug(s, t.math("MULTIPLY", cur(s), factor_socket, clamp=True))

    # micro deviation centred on zero: +/- half the amplitude
    def micro_dev(amp):
        return t.math("MULTIPLY", t.math("SUBTRACT", G["Micro"], 0.5), 2.0 * amp)

    # ---------------------------------------------------------------- carbon
    if cls == "carbon":
        add_rough("Roughness", [
            t.math("MULTIPLY", G["Dust"], K["dust_rough"] * d),
            t.math("MULTIPLY", G["Wear"], K["wear_rough"] * w),
            micro_dev(K["micro_rough"] * m),
        ])
        tint("Base Color", DUST_RGB,
             t.math("MULTIPLY", G["Dust"], K["dust_tint"] * d))
        if amt.get("coat"):
            # clearcoat thins where the part is handled on its edges
            scale_sock("Coat Weight",
                       t.math("SUBTRACT", 1.0,
                              t.math("MULTIPLY", G["Wear"], K["wear_coat"] * w)))
            rel_rough("Coat Roughness", [
                micro_dev(K["coat_micro_rel"] * m),
                t.math("MULTIPLY", G["Scratch"], K["coat_scratch_rel"] * sc),
                t.math("MULTIPLY", G["Dust"], K["coat_dust_rel"] * 0.7 * d),
            ])
            bump("Coat Normal", G["Micro"],
                 K["coat_bump_str"] * m, K["coat_bump"])
        else:
            add_rough("Roughness",
                      [t.math("MULTIPLY", G["Scratch"], K["scratch_rough"] * sc)])
            bump("Normal", G["Micro"], K["micro_bump_str"] * m, K["micro_bump"])

    # ----------------------------------------------------------------- paint
    elif cls == "paint":
        # The brief's "fingerprint-level surface variation on paint" lives here:
        # a micro perturbation of the CLEARCOAT normal, which is what makes a
        # real painted panel's reflection quiver instead of being mirror-clean.
        peel = t.new("ShaderNodeTexNoise", label="clearcoat orange peel")
        t.link(G["Coord"], peel.inputs["Vector"])
        peel.inputs["Scale"].default_value = K["paint_peel_scale"]
        peel.inputs["Detail"].default_value = 1.0
        peel.inputs["Roughness"].default_value = 0.5
        peeln = t.maprange(peel.outputs["Factor"], NOISE_LO, NOISE_HI, 0.0, 1.0,
                           label="peel normalised")
        bump("Coat Normal", peeln, K["paint_peel_str"] * m, K["paint_peel"])
        rel_rough("Coat Roughness", [
            micro_dev(K["coat_micro_rel"] * m),
            t.math("MULTIPLY", G["Scratch"], K["coat_scratch_rel"] * sc),
            t.math("MULTIPLY", G["Dust"], K["coat_dust_rel"] * d),
        ])
        scale_sock("Coat Weight",
                   t.math("SUBTRACT", 1.0,
                          t.math("MULTIPLY", G["Wear"], K["wear_coat"] * 0.7 * w)))
        add_rough("Roughness", [
            t.math("MULTIPLY", G["Dust"], K["dust_rough"] * 0.75 * d),
            micro_dev(K["micro_rough"] * 0.5 * m),
        ])
        tint("Base Color", DUST_RGB,
             t.math("MULTIPLY", G["Dust"], K["dust_tint"] * 0.8 * d))

    # ----------------------------------------------------------------- metal
    elif cls == "metal":
        # Handled metal does NOT roughen on its edges — it burnishes. Edges get
        # smoother and brighter; the flats collect the handling marks.
        add_rough("Roughness", [
            t.math("MULTIPLY", G["Dust"], K["dust_rough"] * d),
            t.math("MULTIPLY", G["Scratch"], K["scratch_rough"] * sc),
            micro_dev(K["micro_rough"] * m),
            t.math("MULTIPLY", t.math("MULTIPLY", G["Wear"], -1.0),
                   K["wear_polish"] * w),
        ], lo=0.015)
        base = cur(bsdf.inputs["Base Color"])
        take(["Base Color"])
        lit = t.mixrgb(t.math("MULTIPLY", G["Wear"], K["wear_lift"] * w),
                       base, (0.82, 0.81, 0.79, 1.0), label="burnished edge")
        t.plug(bsdf.inputs["Base Color"],
               t.mixrgb(t.math("MULTIPLY", G["Dust"], K["dust_tint"] * d),
                        lit, DUST_RGB, label="dust"))
        bump("Normal", G["Micro"], K["micro_bump_str"] * m, K["micro_bump"])

    # -------------------------------------------------------------- anodised
    elif cls == "anodised":
        add_rough("Roughness", [
            t.math("MULTIPLY", G["Dust"], K["dust_rough"] * d),
            t.math("MULTIPLY", G["Scratch"], K["scratch_rough"] * 0.8 * sc),
            micro_dev(K["micro_rough"] * m),
            t.math("MULTIPLY", t.math("MULTIPLY", G["Wear"], -1.0),
                   K["wear_polish"] * 0.6 * w),
        ], lo=0.015)
        base = cur(bsdf.inputs["Base Color"])
        take(["Base Color"])
        # anodising is a few microns thick; a rubbed edge shows bare metal
        rub = t.mixrgb(t.math("MULTIPLY", G["Wear"], K["wear_anod"] * w),
                       base, BARE_ALU, label="anodising rubbed through")
        t.plug(bsdf.inputs["Base Color"],
               t.mixrgb(t.math("MULTIPLY", G["Dust"], K["dust_tint"] * d),
                        rub, DUST_RGB, label="dust"))
        bump("Normal", G["Micro"], K["micro_bump_str"] * m, K["micro_bump"])

    # ----------------------------------------------------------------- matte
    elif cls == "matte":
        add_rough("Roughness", [
            t.math("MULTIPLY", G["Dust"], K["dust_rough"] * 0.6 * d),
            micro_dev(K["micro_rough"] * 0.8 * m),
            t.math("MULTIPLY", t.math("MULTIPLY", G["Wear"], -1.0),
                   K["wear_polish"] * 0.8 * w),
        ], lo=0.05)
        tint("Base Color", DUST_RGB,
             t.math("MULTIPLY", G["Dust"], K["dust_tint"] * 1.15 * d))
        bump("Normal", G["Micro"], K["micro_bump_str"] * 0.8 * m, K["micro_bump"])

    # ------------------------------------------------------------------ grip
    elif cls == "grip":
        # Skin oil goes where a hand can actually reach: exposed surface (high
        # AO openness), in patches, never in the stitching or the crevices. It
        # POLISHES — lower roughness, more sheen, slightly darker — which is the
        # opposite of dust, and is why the grip cannot share the generic recipe.
        exposed = t.math("POWER", G["Open"], 2.0)
        oil = t.math("MULTIPLY", exposed,
                     t.maprange(G["Patch"], 0.45, 0.95, 0.0, 1.0,
                                label="handled zone"))
        oil = t.math("MULTIPLY", oil, w)
        # fingerprint-scale break-up inside the oiled zone
        oilm = t.math("MULTIPLY", oil,
                      t.maprange(G["Micro"], 0.30, 0.78, 0.45, 1.0))
        add_rough("Roughness", [
            t.math("MULTIPLY", oilm, -K["oil_rough"]),
            t.math("MULTIPLY", G["Dust"], K["dust_rough"] * 0.5 * d),
            micro_dev(K["micro_rough"] * 0.7 * m),
        ], lo=0.25)
        add_rough("Sheen Weight",
                  [t.math("MULTIPLY", oilm, K["oil_sheen"])], lo=0.0, hi=1.0)
        add_rough("Specular IOR Level",
                  [t.math("MULTIPLY", oilm, K["oil_spec"])], lo=0.0, hi=1.0)
        base = cur(bsdf.inputs["Base Color"])
        take(["Base Color"])
        # oil darkens and slightly warms a suede grip
        dark = t.mixrgb(t.math("MULTIPLY", oilm, K["oil_darken"]),
                        base, (0.009, 0.0085, 0.008, 1.0), label="skin oil")
        t.plug(bsdf.inputs["Base Color"],
               t.mixrgb(t.math("MULTIPLY", G["Dust"], K["dust_tint"] * 0.7 * d),
                        dark, DUST_RGB, label="dust"))
        bump("Normal", G["Micro"], K["micro_bump_str"] * 0.9 * m,
             K["micro_bump"] * 1.4)

    # ---------------------------------------------------------------- rubber
    elif cls == "rubber":
        # A slick tyre is convex and almost unoccluded, so a cavity-driven layer
        # does nothing to it at all — at pass 4 the sidewall was indistinguishable
        # from the original. The dulling film on new rubber is not dirt in
        # crevices, it is mould-release bloom across the whole flank, so here the
        # broad PATCH field carries most of the weight rather than DUST.
        add_rough("Roughness", [
            t.math("MULTIPLY", G["Dust"], K["dust_rough"] * 0.55 * d),
            t.math("MULTIPLY", G["Patch"], 0.045 * d),
            micro_dev(K["micro_rough"] * 0.6 * m),
        ], lo=0.2)
        # a dulling film: desaturating, not dirtying
        tint("Base Color", (0.055, 0.053, 0.050, 1.0),
             t.math("ADD", t.math("MULTIPLY", G["Dust"], 0.16 * d),
                    t.math("MULTIPLY", G["Patch"], 0.10 * d)))
        bump("Normal", G["Micro"], K["micro_bump_str"] * 0.7 * m, K["micro_bump"])

    # ----------------------------------------------------------------- glass
    elif cls == "glass":
        # R2-014. Two independent causes of the knife edge, so two fixes.
        #
        # 1. the surface is perfectly planar. A real cover glass is not: it has
        #    a gentle long-wavelength waviness from lamination. A ~1.3 deg
        #    normal deviation over ~18 mm is invisible on the readout behind the
        #    glass but doubles the angular width of a reflected highlight and
        #    makes its edge wander.
        wav = t.new("ShaderNodeTexNoise", label="cover glass waviness")
        t.link(G["Coord"], wav.inputs["Vector"])
        wav.inputs["Scale"].default_value = 55.0     # ~18 mm, so ~7 waves
        wav.inputs["Detail"].default_value = 1.0     # across a 125 mm display
        wav.inputs["Roughness"].default_value = 0.4
        wavn = t.maprange(wav.outputs["Factor"], NOISE_LO, NOISE_HI, 0.0, 1.0,
                          label="waviness normalised")
        # 0.30 of Micro here was the crumpled-cellophane failure: Micro's
        # wavelength is 7x shorter than the waviness, so at equal Distance it
        # contributed 7x the slope and swamped the gentle non-planarity it was
        # meant to season.
        height = t.mixf(0.05, wavn, G["Micro"], label="waviness + a little micro")
        bump("Normal", height, K["glass_wave_str"] * m, K["glass_wave"])

        # 2. roughness is uniform, so the highlight terminates where the
        #    geometry does. Break it up at ~2.6 mm and the termination dissolves
        #    into a soft uneven smear instead of a cut.
        smudge = t.math("MULTIPLY", t.math("POWER", G["Open"], 2.0),
                        t.maprange(G["Patch"], 0.35, 0.95, 0.0, 1.0),
                        label="finger smudge")
        add_rough("Roughness", [
            K["glass_base"] * m,
            micro_dev(K["glass_rough"] * m),
            t.math("MULTIPLY", smudge, K["glass_smudge"] * m),
            t.math("MULTIPLY", G["Dust"], 0.030 * d),
        ], lo=0.012, hi=0.35)
        tint("Base Color", DUST_RGB,
             t.math("MULTIPLY", G["Dust"], 0.10 * d))
    else:
        raise SystemExit(f"unknown recipe class {cls!r}")

    # tidy: park the new nodes under the shader so the graph stays readable
    fr = nt.nodes.new("NodeFrame")
    fr.name = f"{PFX}FRAME"
    fr.label = "R2 imperfection layer"
    for n in nt.nodes:
        if n.name.startswith(PFX) and n is not fr:
            n.parent = fr
    mat["r2imp"] = json.dumps(orig)
    return sorted(orig)


# ---------------------------------------------------------------------------
# mask debug
# ---------------------------------------------------------------------------
def debug_masks(channels):
    """Replace every target material with an emission of the mask triple.

    The masks get calibrated FIRST, cheaply and locally, because guessing a
    pointiness ramp and then paying 58 s of 4K render per guess is how a tuning
    pass turns into an afternoon.
    """
    names = [c.strip() for c in channels.split(",")]
    for mname in AMOUNTS:
        mat = bpy.data.materials.get(mname)
        if not mat or not mat.use_nodes:
            continue
        nt = mat.node_tree
        nt.nodes.clear()
        t = Tree(nt)
        out = t.new("ShaderNodeOutputMaterial")
        em = t.new("ShaderNodeEmission")
        g = t.new("ShaderNodeGroup"); g.node_tree = bpy.data.node_groups[GROUP]
        comb = t.new("ShaderNodeCombineColor")
        for i, nm in enumerate(names[:3]):
            t.link(g.outputs[nm], comb.inputs[i])
        t.link(comb.outputs[0], em.inputs["Color"])
        em.inputs["Strength"].default_value = 1.0
        t.link(em.outputs[0], out.inputs["Surface"])
    sc = bpy.context.scene
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    # The scene composites through `ShowroomComp`, which is a Glare node. Bloom
    # smeared the first mask render into a solid green field and made the dust
    # driver look ten times broader than it is — a calibration read straight off
    # a graded, bloomed image is a measurement of the grade.
    sc.render.use_compositing = False
    sc.render.use_sequencer = False
    # a mask render must not be lit by anything
    for ob in bpy.data.objects:
        if ob.type == "LIGHT":
            ob.hide_render = True
    w = bpy.data.worlds.new("R2_black")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.0
    sc.world = w
    print(f">> DEBUG mask mode: R,G,B = {names[:3]}")


# ---------------------------------------------------------------------------
def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--strength", type=float, default=1.0,
                   help="global multiplier on every amount in AMOUNTS")
    p.add_argument("--only", default=None, help="comma list of material names")
    p.add_argument("--strip", action="store_true",
                   help="remove a previously injected layer and restore")
    p.add_argument("--debug", default=None,
                   help="render the drivers instead: e.g. Wear,Dust,Scratch")
    p.add_argument("--set", action="append", default=[],
                   help="override a K[] or GRP[] constant, e.g. glass_rough=0.05")
    p.add_argument("--keep-cams", default=None,
                   help="comma list of cameras to keep. The farm worker prewarms "
                        "EVERY camera at scene load, and this layer's AO node "
                        "makes each prewarm several times more expensive; 15 "
                        "cameras took 5.5 min of a 15 min readiness budget.")
    a = p.parse_args(argv)

    for kv in a.set:
        k, v = kv.split("=", 1)
        tgt = K if k in K else GRP if k in GRP else None
        if tgt is None:
            raise SystemExit(f"unknown constant {k!r}; "
                             f"known: {sorted(K)} {sorted(GRP)}")
        tgt[k] = float(v)
        print(f">> {'K' if tgt is K else 'GRP'}[{k}] = {tgt[k]}")

    targets = list(AMOUNTS)
    if a.only:
        want = {x.strip() for x in a.only.split(",")}
        targets = [m for m in targets if m in want]

    if a.keep_cams:
        keep = {x.strip() for x in a.keep_cams.split(",")}
        gone = [o.name for o in list(bpy.data.objects)
                if o.type == "CAMERA" and o.name not in keep]
        for n in gone:
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
        left = [o.name for o in bpy.data.objects if o.type == "CAMERA"]
        if not left:
            raise SystemExit(f"--keep-cams {sorted(keep)} matched no camera")
        bpy.context.scene.camera = bpy.data.objects[left[0]]
        print(f">> cameras: kept {left}, removed {len(gone)}")

    stripped = [m.name for m in bpy.data.materials if strip(m)]
    if stripped:
        print(f">> stripped previous layer from {len(stripped)}: {stripped}")
    if a.strip:
        report = {"stripped": stripped}
    else:
        build_group()
        report = {"strength": a.strength, "K": dict(K), "GRP": dict(GRP),
                  "materials": {}}
        for mname in targets:
            mat = bpy.data.materials.get(mname)
            if mat is None:
                print(f"!! material {mname} not present in this blend")
                continue
            if not mat.use_nodes:
                print(f"!! {mname} has no node tree, skipped")
                continue
            touched = inject(mat, AMOUNTS[mname], a.strength)
            if touched is None:
                print(f"!! {mname}: no Principled BSDF on the output, skipped")
                continue
            users = sum(1 for ob in bpy.data.objects if ob.type == "MESH"
                        for s in ob.material_slots
                        if s.material and s.material.name == mname)
            report["materials"][mname] = {
                "class": AMOUNTS[mname]["cls"], "sockets": touched,
                "amounts": AMOUNTS[mname], "mesh_slots": users}
            print(f">> {mname:<16} {AMOUNTS[mname]['cls']:<9} "
                  f"{users:4d} slots  -> {', '.join(touched)}")
        report["skipped"] = SKIPPED
        if a.debug:
            debug_masks(a.debug)
            report["debug"] = a.debug

    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.file.make_paths_absolute()
    bpy.ops.wm.save_as_mainfile(filepath=out, relative_remap=False, compress=False)
    json.dump(report, open(os.path.splitext(out)[0] + "_imp.json", "w"), indent=1)
    print(f">> saved {out} ({os.path.getsize(out)/1048576:.1f} MB), "
          f"{len(report.get('materials', {}))} materials carry the layer")
    print(">> STAGE RESULT: IMPERFECTIONS_OK")



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
    gate_exit.guard(main, tool="imperfections")
