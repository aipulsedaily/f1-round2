"""THE HERO BODYWORK'S PAINT — carbon, flake, clear, and the livery under it.

    /opt/blender-5.2.0-linux-x64/blender -b world/car_anim.blend \
        -P world/car_paint.py -- --save
    /opt/blender-5.2.0-linux-x64/blender -b world/car_anim.blend \
        -P world/car_paint.py -- --strip --save          # exact restore

WHY THIS FILE EXISTS
--------------------
`LiveryPaint` is round-1 geometry's material, authored in
`/home/zany/opus5-car-render/build/s03_materials.py::livery_paint`, and that tree
is READ-ONLY (project law 1).  Round 2 therefore retro-fits the car's materials
from its own side, exactly as `tools/imperfections.py` already does for the
imperfection layer.  This module is that file's sibling: `imperfections.py` owns
wear, dust, scratches and the clearcoat's micro break-up; this owns the paint
STACK — what the panel is made of.  Run this first, `imperfections.py` second;
both chain onto whatever they find, and both are reversible.

WHAT WAS MEASURED, AND WHAT IT SAID          (R2-521, pass probe, 2026-08-04)
----------------------------------------------------------------------------
The 14 `LiveryPaint` panels were masked by `pass_index` in the ladder's own
showroom — practicals levelled by `showroom_lighting.apply`, so it IS the film's
room — at the ladder's own two camera stations, and every light path leaving them
was measured separately.  Light passes multiplied by their colour passes, because
Cycles stores `Diffuse Direct` WITHOUT the surface colour:

    station                     diffuse   glossy   emission   TRANSMISSION
    head-on     (ONER f697)      2.78 %   96.44 %    0.78 %     0.0000 %
    three-quarter (ONER f655)    7.32 %   88.94 %    3.74 %     0.0000 %

    Zero transmission-pass pixels above 1e-6 out of 5,138 and 11,622; maximum
    transmission-pass pixel 0.0 at both stations; diffuse + glossy + emission +
    transmission equals the Combined pass to 3e-06.  Positive control — the same
    panels, the same light, Transmission Weight 0.35 — lights up 2,612 and 6,593
    transmission pixels, so the probe can see transmission when there is any.

    TRANSMISSION IS NOT THE CAUSE.  The bodywork is opaque and the "you can see
    the internals through the skin" read is a REFLECTION, proved by rendering the
    14 panels with all 602 other car meshes hidden: with nothing whatsoever
    behind the skin, the shell still reads as translucent pale-blue glass.

    WHAT IT ACTUALLY IS: THE PANEL HAS NO PAINT IN IT.  Its diffuse colour
    measures 0.0121 luminance — darker than asphalt (0.05-0.07) — and then
    Metallic 0.62 removes 62 % of what that leaves.  96 % of the hero subject's
    appearance is the room reflected in it.  A surface with no diffuse response
    is a mirror, and a mirror in a showroom full of structure looks like a window
    onto structure.  It also explains why f697 reads glass and f655 reads navy:
    not the material swinging with angle, but what the mirror is pointed at.

    The livery is a secondary finding rather than the cause: round 1 carries the
    ENTIRE artwork in `Emission Strength`, so the body-wide node-graph network is
    a body-wide light source.  It is 0.78 % of the panel head-on and 3.74 % at
    three-quarter, and it is what is being described as glowing internal wiring.

AFTER THIS MODULE, SAME PROBE, SAME RIG, SAME FRAMES:

    station                     diffuse   glossy   emission   albedo
    head-on         before       2.78 %   96.44 %    0.78 %   0.0121
                    after        7.85 %   91.50 %    0.65 %   0.0369
    three-quarter   before       7.32 %   88.94 %    3.74 %   0.0121
                    after       19.86 %   77.05 %    3.09 %   0.0389

A MEAN over the panel is dominated by its blown highlight, so read the per-pixel
distribution instead (`work/r2521/pass_stats.py`) — the diffuse PERCENTAGE of the
typical pixel is the thing that decides "painted" against "chromed":

                             p10     p25   median    p75    p90
    head-on       before    1.36    8.73    31.02  60.69  80.23
                  after     3.34   22.89    55.13  81.40  92.83
    three-quarter before    7.14   16.68    40.50  65.27  82.83
                  after    19.68   37.18    67.75  86.61  94.88

WHAT THIS BUILDS, ALL PROCEDURAL, NOTHING DOWNLOADED
----------------------------------------------------
    substrate   2x2 twill carbon, triplanar, 5.0 mm tow pitch, telegraphing
                through the paint as a faint quilt in albedo, roughness and
                normal — what a real thin race paint over a woven laminate does
    basecoat    a deep navy with an actual diffuse response, lifted by a SCREEN
                operator so the artwork's own highlights are untouched
    flake       per-cell random facet normals from a smooth Voronoi at 0.35 mm,
                plus a facing-driven pearl shift navy -> teal.  The shipped
                material's "flake" was a SCREEN blend of a scalar noise, which
                brightens but cannot sparkle: flake is a NORMAL, not a colour
    clear       coat tint returned to near-neutral, coat roughness 0.022 ->
                0.038, and round 1's orange-peel bump MOVED off the base normal
                (where a smooth coat hides it) onto the COAT normal (where it is
                the thing you actually see)

EVERY SOCKET IS FED BY NAME.  Blender 5.2 moved `Principled BSDF.Normal` from
index 5 to 6 and this project shipped 14 dead bump stacks to that bug.
"""

import argparse
import json
import os
import sys

import bpy

VERSION = 3
PREFIX = "R2CP_"
SNAP_KEY = "R2CP_SNAPSHOT"
VER_KEY = "R2CP_VERSION"
RESULT = "R2521_CARPAINT"

TARGET_MATERIAL = "LiveryPaint"

# --------------------------------------------------------------------------- #
# TUNABLES.  Every one of these is a number somebody has to be able to argue
# with, so each says what it is and where it came from.
# --------------------------------------------------------------------------- #

# ---- the basecoat ---------------------------------------------------------
# A SCREEN lift, not a gain.  screen(a, b) = 1 - (1-a)(1-b): it maps black to b
# exactly and leaves white at white, so the navy gains a diffuse response while
# the livery's own signal-white bars (0.56 linear, already calibrated against a
# 1100 W key in round 1) do not move.  A multiply would have pushed them to 1.7
# and clipped them.
#
# VOID_NAVY is (0.0060, 0.0105, 0.0260), luminance 0.0107 and blue/red 4.3.
# Screened with this it becomes (0.0130, 0.0230, 0.0850) — luminance 0.0254, 2.4x,
# blue/red 6.5.  It is deliberately NOT a neutral lift.
#
# TUNED ON THE PICTURE, TWICE, AND BOTH CORRECTIONS ARE WORTH KEEPING.
#   * A neutral lift to luminance 0.0400 was the more defensible physical number
#     for a navy basecoat and rendered WORSE: in a showroom lit to 46 kW of
#     levelled practicals the panel came back a pale HAZY SLATE, and the macro
#     crop against the untouched arm read as a loss of depth even though the
#     measured diffuse share had gone up.
#   * A neutral lift to 0.0283 was still slate, because lifting R and G in step
#     with B is what DESATURATES a navy.  Presence and depth are not the same
#     axis: presence is luminance, depth is the blue-to-red ratio.  This lift
#     buys presence in B and spends almost nothing in R.
BASE_LIFT = (0.0070, 0.0126, 0.0606)

# Metallic 0.62 was on a PAINTED panel.  Metallic is not "has metal flake in it"
# — it removes the diffuse lobe and colours the specular by the base colour, so
# 0.62 was deleting 62 % of the one response that measured missing.  Real
# metallic basecoat is a dielectric binder holding metal flakes: the flake is
# geometry (see FLAKE_* below), not a metallic weight.  0.10 keeps a trace of
# the flake's own conductor response.
#
# Applied as a SCALE on the existing link, so the nose's carbon-dissolve region,
# which round 1 drives to metallic 0, still reaches 0.
METALLIC_TARGET = 0.10
METALLIC_SHIPPED = 0.62

# ---- the carbon substrate -------------------------------------------------
# 5.0 mm tow pitch = 200 repeats/m.  Round 1 learned this the hard way (D081):
# the weave was authored at 760 repeats/m, a 1.3 mm twill, which is below a pixel
# at any sane render scale, averaged to nothing, and left every carbon panel a
# dead-flat mirror.  Real 2x2 twill is about 5 mm.
WEAVE_PITCH_M = 0.0050
# Under paint the weave is a QUILT, not a texture: the laminate's tow crowns sit
# proud by tens of microns and the paint film follows them.  These are the
# amplitudes of that telegraphing, not of bare weave.
WEAVE_ALBEDO = 0.070       # +-7.0 % on the basecoat
WEAVE_ROUGH = 0.022        # tow crowns polish slightly smoother than the valleys
WEAVE_BUMP_M = 0.000040    # 40 um of relief
WEAVE_BUMP_STR = 0.35
# Cycles cannot prefilter a procedural.  At grazing incidence many weave cells
# fall inside one pixel and the twill aliases into a moire that a real lens would
# have blurred away.  Fade toward the weave's own mean over this |dot(N, I)|
# band — the same guard round 1 put on its bare-carbon weave.
WEAVE_FADE_LO, WEAVE_FADE_HI = 0.10, 0.42

# ---- the flake ------------------------------------------------------------
# 0.35 mm cells = 2860 /m.  Automotive flake is 10-50 um and therefore always
# sub-pixel; rendering it at true size gives sampling noise and no sparkle.  At
# 0.35 mm it is ~1 px at a 4 K close-up and averages to a sheen further out,
# which is what the eye reads as flake.
FLAKE_SCALE = 2860.0
FLAKE_SMOOTH = 0.35        # smooth-F1 so each cell is a facet, not a spike
FLAKE_BUMP_M = 0.0000075   # 7.5 um -> a fraction of a degree of facet tilt
FLAKE_BUMP_STR = 0.30
FLAKE_ROUGH = 0.030        # facets are glossier than the binder between them
# The pearl.  A two-coat pearl shifts hue with view angle; this is that shift,
# small, and biased to the teal the livery already owns so the car does not grow
# a second palette.
PEARL_TEAL = (0.0160, 0.0500, 0.0800)
PEARL_BLEND = 0.30         # LayerWeight Blend — see the note in `_pearl`
PEARL_MAX = 0.20           # peak fraction of pearl at the shoulder

# ---- the clearcoat --------------------------------------------------------
# (0.68, 0.82, 0.90) tints everything under the coat blue and darkens red by
# 32 %.  On a panel that is 88 % reflection it did not buy the intended cast, and
# on the 2.8 % that IS the car it removed a third of the red.  A real clear is
# very slightly warm-neutral; this keeps a whisper of the intended blue.
COAT_TINT = (0.960, 0.975, 1.000)
# 0.022 is a mirror, and a mirror returns a LEGIBLE IMAGE of the room — which is
# what makes the panel read as chromed rather than painted even once it has a
# basecoat under it.  Measured automotive clear runs 0.03-0.06 depending on how
# hard it was polished.  A concours show car is at the bottom of that band; an F1
# car's paint is sprayed as thin as it can be flown and is not cut and polished
# to a mirror, so it belongs at the TOP.  0.055 keeps the highlight bright and
# blurs the ceiling's edges into a sheen instead of a picture.
# `imperfections.py` then adds a PROPORTIONAL +-20 % on top of whatever it finds
# here, so lifting the base value widens that break-up in the same proportion.
COAT_ROUGH = 0.055

# ---- the livery -----------------------------------------------------------
# HOW ROUND 1 CARRIES THE ARTWORK, because the fix depends on it:
# `Emission Color` is a FLAT colour — PULSE_CYAN, crossfaded to LAB_VIOLET over
# the last 280 mm of the tail — and carries no pattern at all.  ALL of the
# artwork's shape lives in `Emission Strength`, as round 1's own ladder:
#
#     S_STREAM      0.35   particle streams along the flank
#     S_GRAPH_EDGE  0.40   the body-wide node-graph network      <- the "wiring"
#     S_GRAPH_NODE  3.20   its junction discs
#     S_PULSE_CORE  6.00   the pulse line          DESIGNED LIGHT SOURCE
#     S_NUMERAL     9.00   the race number         DESIGNED LIGHT SOURCE
#
# So a flat scale on emission would dim the film's own motif by exactly as much
# as it dims the network that is the problem.  Instead the strength is passed
# through a ramp that cuts the BOTTOM of the ladder and leaves the top alone:
# the network and the streams stop radiating, the pulse line and the numeral do
# not move.  One MapRange, and it targets the defect and nothing else.
EMIS_KEEP_LO = 0.25        # multiplier at and below EMIS_RAMP_LO
EMIS_RAMP_LO = 0.45        # ... which is just above S_GRAPH_EDGE (0.40)
EMIS_RAMP_HI = 3.10        # ... and just below S_GRAPH_NODE (3.20)
# ...and what the network stops radiating it gains as PIGMENT: the same pattern,
# printed in the same cyan, under the clearcoat, which is where a livery lives.
# The factor is read off the emission strength, normalised over the ladder's
# lower half so the network prints strongly and the two designed sources — which
# are already saturated light — do not also become saturated paint.
# MEASURED AND RETUNED.  The first rendered pass used 0.60 with the flat cyan
# `Emission Color` (0.028, 0.807, 1.000) as the ink and normalised over 0.90, so
# the graph edges (0.40) and the particle streams (0.35) — which cover the whole
# upper body — printed at ~0.3 of a saturated cyan EVERYWHERE.  The car came back
# pale slate-cyan instead of navy.  A printed livery is an INK, not a light
# source's colour: this is a deep teal, mixed weakly, normalised over the ladder
# so the faint rungs print faintly and the junctions and the pulse line print.
LIVERY_INK = (0.0130, 0.0720, 0.0980)
LIVERY_PIGMENT = 0.30
PIGMENT_NORM_HI = 2.20


def log(*a):
    print("[carpaint]", *a)
    sys.stdout.flush()


# --------------------------------------------------------------------------- #
# a very small node-building helper
# --------------------------------------------------------------------------- #
class T:
    """Node factory that tags everything it makes so `--strip` is exact."""

    def __init__(self, nt):
        self.nt = nt
        self.n = 0

    def new(self, idname, label="", loc=(0, 0), **kw):
        nd = self.nt.nodes.new(idname)
        self.n += 1
        nd.name = "%s%03d_%s" % (PREFIX, self.n, label or idname)
        nd.label = label
        nd.location = loc
        for k, v in kw.items():
            setattr(nd, k, v)
        return nd

    def set(self, node, name, value):
        """Set an input BY NAME.  Never by index — 5.2 renumbered Principled."""
        if name not in node.inputs:
            raise SystemExit("%s has no input %r (it has %s)"
                             % (node.bl_idname, name,
                                [i.name for i in node.inputs]))
        node.inputs[name].default_value = value

    def link(self, out, node, name):
        if name not in node.inputs:
            raise SystemExit("%s has no input %r (it has %s)"
                             % (node.bl_idname, name,
                                [i.name for i in node.inputs]))
        return self.nt.links.new(out, node.inputs[name])

    # -- scalar maths ------------------------------------------------------ #
    def math(self, op, a, b=None, c=None, loc=(0, 0), label="", clamp=False):
        nd = self.new("ShaderNodeMath", label or op.lower(), loc)
        nd.operation = op
        nd.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if hasattr(v, "is_output"):
                self.nt.links.new(v, nd.inputs[i])
            else:
                nd.inputs[i].default_value = v
        return nd.outputs["Value"]

    def mapr(self, v, fmin, fmax, tmin=0.0, tmax=1.0, loc=(0, 0), label="",
             smooth=True):
        nd = self.new("ShaderNodeMapRange", label or "range", loc)
        nd.clamp = True
        # 5.2: the property is `interpolation_type`, not `interpolation`
        nd.interpolation_type = "SMOOTHSTEP" if smooth else "LINEAR"
        self.link(v, nd, "Value") if hasattr(v, "is_output") else \
            self.set(nd, "Value", v)
        self.set(nd, "From Min", fmin)
        self.set(nd, "From Max", fmax)
        self.set(nd, "To Min", tmin)
        self.set(nd, "To Max", tmax)
        return nd.outputs["Result"]

    def mixf(self, fac, a, b, loc=(0, 0), label=""):
        nd = self.new("ShaderNodeMix", label or "mixf", loc)
        nd.data_type = "FLOAT"
        for sock, v in ((nd.inputs[0], fac), (nd.inputs[2], a), (nd.inputs[3], b)):
            if hasattr(v, "is_output"):
                self.nt.links.new(v, sock)
            else:
                sock.default_value = float(v)
        return nd.outputs[0]

    def mixc(self, fac, a, b, loc=(0, 0), label="", blend="MIX"):
        nd = self.new("ShaderNodeMix", label or "mixc", loc)
        nd.data_type = "RGBA"
        nd.blend_type = blend
        # inputs[0] is the FLOAT Factor; [6] and [7] are the RGBA A and B.  They
        # are addressed by index and not by name on purpose: ShaderNodeMix
        # carries several sockets all called "Factor" and all called "A", one
        # per data type, and a name lookup silently returns the wrong one.
        if hasattr(fac, "is_output"):
            self.nt.links.new(fac, nd.inputs[0])
        else:
            nd.inputs[0].default_value = float(fac)
        for sock, v in ((nd.inputs[6], a), (nd.inputs[7], b)):
            if hasattr(v, "is_output"):
                self.nt.links.new(v, sock)
            else:
                sock.default_value = v if hasattr(v, "__len__") else (v, v, v, 1.0)
        return nd.outputs[2]


def bsdf_of(mat):
    nt = mat.node_tree
    out = next((n for n in nt.nodes
                if n.type == "OUTPUT_MATERIAL" and n.is_active_output), None)
    if out is None or not out.inputs["Surface"].is_linked:
        raise SystemExit("%s has no active surface output" % mat.name)
    b = out.inputs["Surface"].links[0].from_node
    if b.bl_idname != "ShaderNodeBsdfPrincipled":
        raise SystemExit("%s's surface is %s, not a Principled BSDF"
                         % (mat.name, b.bl_idname))
    return nt, b


# --------------------------------------------------------------------------- #
# snapshot / strip — this module must be exactly reversible
# --------------------------------------------------------------------------- #
SNAP_SOCKETS = ("Base Color", "Metallic", "Roughness", "Normal", "Coat Normal",
                "Coat Weight", "Coat Roughness", "Coat Tint",
                "Emission Color", "Emission Strength")


def snapshot(mat):
    nt, b = bsdf_of(mat)
    snap = {"sockets": {}}
    for name in SNAP_SOCKETS:
        if name not in b.inputs:
            continue
        s = b.inputs[name]
        e = {"linked": s.is_linked}
        if s.is_linked:
            l = s.links[0]
            e["from_node"] = l.from_node.name
            e["from_socket"] = l.from_socket.name
        else:
            v = s.default_value
            e["value"] = list(v) if hasattr(v, "__len__") else float(v)
        snap["sockets"][name] = e
    return snap


def strip(mat, quiet=False):
    """Remove every node this module made and put the original links back."""
    nt = mat.node_tree
    raw = mat.get(SNAP_KEY)
    made = [n for n in nt.nodes if n.name.startswith(PREFIX)]
    for n in made:
        nt.nodes.remove(n)
    restored = 0
    if raw:
        snap = json.loads(raw)
        _nt, b = bsdf_of(mat)
        for name, e in snap["sockets"].items():
            if name not in b.inputs:
                continue
            s = b.inputs[name]
            for l in list(s.links):
                nt.links.remove(l)
            if e["linked"]:
                src = nt.nodes.get(e["from_node"])
                if src is None or e["from_socket"] not in src.outputs:
                    raise SystemExit(
                        "cannot restore %s.%s: node %r socket %r is gone"
                        % (mat.name, name, e["from_node"], e["from_socket"]))
                nt.links.new(src.outputs[e["from_socket"]], s)
            else:
                v = e["value"]
                s.default_value = v if isinstance(v, list) else v
            restored += 1
        del mat[SNAP_KEY]
    if VER_KEY in mat:
        del mat[VER_KEY]
    if not quiet:
        log("stripped %s: removed %d nodes, restored %d sockets"
            % (mat.name, len(made), restored))
    return len(made), restored


# --------------------------------------------------------------------------- #
# the paint stack
# --------------------------------------------------------------------------- #
def _object_coords(t, loc):
    """Object-space P, and its three components."""
    tc = t.new("ShaderNodeTexCoord", "object coords", loc)
    sep = t.new("ShaderNodeSeparateXYZ", "P.xyz", (loc[0] + 200, loc[1]))
    t.link(tc.outputs["Object"], sep, "Vector")
    return tc, sep


def _object_normal(t, loc):
    """The surface normal IN OBJECT SPACE.

    `ShaderNodeNewGeometry.Normal` is world space.  Blending object-space
    projections by a world-space normal picks the wrong projection wherever the
    object is rotated, which round 1 found striping the brake drums into
    corduroy.  The conversion is one node and there is no excuse for skipping it.
    """
    geo = t.new("ShaderNodeNewGeometry", "geometry", loc)
    vt = t.new("ShaderNodeVectorTransform", "N -> object", (loc[0] + 200, loc[1]))
    vt.vector_type = "NORMAL"
    vt.convert_from = "WORLD"
    vt.convert_to = "OBJECT"
    t.link(geo.outputs["Normal"], vt, "Vector")
    nsep = t.new("ShaderNodeSeparateXYZ", "N.xyz", (loc[0] + 380, loc[1]))
    t.link(vt.outputs["Vector"], nsep, "Vector")
    return geo, nsep


TWO_PI = 6.283185307179586


def _twill_plane(t, ux, vy, loc, label):
    """A 2x2 twill on one plane, from two coordinates already in TOW UNITS.

    The construction, so it can be argued with:

      * A tow is a bundle of fibres with a rounded cross-section, so its height
        across its own width is a dome.  `dome(f) = 1 - (2f - 1)^2` is that
        parabola: 0 at the tow's edges, 1 at its crown.  Warp tows run along u,
        so a warp's dome varies with `fract(v)`; wefts the other way.
      * A 2/2 twill floats each warp over two wefts and under two, the float
        advancing one tow per row.  The FLOAT PHASE is therefore a function of
        `u - v` with period 4.
      * WHICH TOW IS ON TOP MUST BE A CONTINUOUS FUNCTION, and the first build
        of this module got that wrong.  It selected with
        `mod(floor(u) - floor(v), 4) < 2` — correct as combinatorics, and a step
        function.  A step in a height field is an infinite gradient, and a Bump
        node reads the GRADIENT: the panel rendered as flat 4x1 tow PLATEAUS
        with hard stair-steps at every tile edge, ~110 x 30 px at the macro
        station, which is a parquet floor and not a weave.
        `f = 0.5 + 0.5 * cos(2*pi*(u - v)/4)` carries the same period, the same
        diagonal and the same phase, and is smooth everywhere.
      * The two tow families are then combined by **MAXIMUM, not by MIX**:
        `warp_ridge = dome(fv) * f`, `weft_ridge = dome(fu) * (1 - f)`,
        `h = max(warp_ridge, weft_ridge)`.  Both terms are continuous and both
        fall to zero where their own tow is buried, so the maximum is continuous
        too — but it is the tow ITSELF that is proud, not a crossfade between
        two, so the float reads as an unbroken diagonal rib.
        MIX was tried first and rendered as a CHEVRON: crossfading a ridge
        running along u into a ridge running along v averages the two into a
        zigzag, which does not match the 2/2 twill on the exposed `CarbonFibre`
        parts sitting next to these panels in the same frame.  A car's paint and
        its bare carbon are the same laminate and must show the same weave.

    Returns a 0..1 height.  Albedo, roughness and relief are all read off this
    one field, so the weave cannot disagree with itself.
    """
    x0, y0 = loc
    fu = t.math("FRACT", ux, loc=(x0, y0 - 120), label="fu")
    fv = t.math("FRACT", vy, loc=(x0, y0 - 240), label="fv")

    d = t.math("SUBTRACT", ux, vy, loc=(x0 + 180, y0 + 60), label="u-v")
    ph = t.math("MULTIPLY", d, TWO_PI / 4.0, loc=(x0 + 340, y0 + 60),
                label="float phase")
    c = t.math("COSINE", ph, loc=(x0 + 500, y0 + 60), label="cos")
    f = t.math("MULTIPLY_ADD", c, 0.5, 0.5, loc=(x0 + 660, y0 + 60),
               label="warp on top")
    fbar = t.math("SUBTRACT", 1.0, f, loc=(x0 + 820, y0 + 60), label="weft on top")

    def dome(x, yy, lab):
        a = t.math("MULTIPLY_ADD", x, 2.0, -1.0, loc=(x0 + 180, yy),
                   label=lab + " centred")
        s = t.math("MULTIPLY", a, a, loc=(x0 + 340, yy), label=lab + " squared")
        return t.math("SUBTRACT", 1.0, s, loc=(x0 + 500, yy), label=lab + " dome")

    weft_h = dome(fu, y0 - 240, "weft")
    warp_h = dome(fv, y0 - 420, "warp")
    weft_r = t.math("MULTIPLY", weft_h, fbar, loc=(x0 + 700, y0 - 240),
                    label="weft ridge")
    warp_r = t.math("MULTIPLY", warp_h, f, loc=(x0 + 700, y0 - 420),
                    label="warp ridge")
    return t.math("MAXIMUM", warp_r, weft_r, loc=(x0 + 900, y0 - 300),
                  label="twill height")


def _weave(t, tc, nsep, loc):
    """The twill, triplanar, blended by the object-space normal."""
    x0, y0 = loc
    inv = 1.0 / WEAVE_PITCH_M
    sc = t.new("ShaderNodeVectorMath", "to tow units", (x0, y0))
    sc.operation = "SCALE"
    t.link(tc.outputs["Object"], sc, "Vector")
    t.set(sc, "Scale", inv)
    sep = t.new("ShaderNodeSeparateXYZ", "P in tows", (x0 + 200, y0))
    t.link(sc.outputs["Vector"], sep, "Vector")

    planes = {}
    for k, (a, b, dy) in enumerate((("X", "Y", 900), ("Y", "Z", -900),
                                    ("Z", "X", -2700))):
        planes[k] = _twill_plane(t, sep.outputs[a], sep.outputs[b],
                                 (x0 + 420, y0 + dy), "%s%s" % (a, b))

    # Blend weights from |N|^16 in object space.  Exponent 4 is too soft: at a
    # 45 deg normal two projections blend 50/50 and two perpendicular twills beat
    # into a hexagonal moire that is visibly NOT carbon.  Procedurals interfere
    # far harder than photographs do, so the blend has to be near-hard.
    w = {}
    for k, axis in enumerate(("Z", "X", "Y")):        # XY faced by Z, YZ by X, ZX by Y
        ab = t.math("ABSOLUTE", nsep.outputs[axis], loc=(x0 + 1900, y0 - 200 * k),
                    label="|N.%s|" % axis)
        w[k] = t.math("POWER", ab, 16.0, loc=(x0 + 2060, y0 - 200 * k),
                      label="w%s" % axis)
    s = t.math("ADD", w[0], w[1], loc=(x0 + 2240, y0), label="w sum")
    s = t.math("ADD", s, w[2], loc=(x0 + 2400, y0), label="w sum")
    nz = t.math("DIVIDE", w[0], s, loc=(x0 + 2560, y0 + 200), label="nz")
    ny = t.math("DIVIDE", w[2], s, loc=(x0 + 2560, y0 - 200), label="ny")

    m1 = t.mixf(nz, planes[1], planes[0], loc=(x0 + 2740, y0), label="YZ<-XY")
    m2 = t.mixf(ny, m1, planes[2], loc=(x0 + 2900, y0), label="<-ZX")

    # grazing-angle fade toward the weave's mean, standing in for the mip
    # filtering a procedural never gets
    geo = t.new("ShaderNodeNewGeometry", "incidence", (x0 + 2740, y0 - 500))
    dot = t.new("ShaderNodeVectorMath", "N.I", (x0 + 2900, y0 - 500))
    dot.operation = "DOT_PRODUCT"
    t.nt.links.new(geo.outputs["Normal"], dot.inputs[0])
    t.nt.links.new(geo.outputs["Incoming"], dot.inputs[1])
    fac = t.math("ABSOLUTE", dot.outputs["Value"], loc=(x0 + 3060, y0 - 500),
                 label="facing")
    keep = t.mapr(fac, WEAVE_FADE_LO, WEAVE_FADE_HI, 0.0, 1.0,
                  loc=(x0 + 3220, y0 - 500), label="weave visibility")
    faded = t.mixf(keep, 0.5, m2, loc=(x0 + 3400, y0), label="weave faded")
    return faded


def _flake(t, tc, loc):
    """Metal flake: random facet normals, plus a per-cell gloss lift.

    The shipped material's flake was `Mix(SCREEN, 0.06)` of a scale-1800 noise
    into the base colour.  A colour operation cannot sparkle: sparkle is what
    happens when neighbouring microfacets point in different directions and one
    of them catches the key.  So this is a NORMAL, and the colour term it does
    carry is the pearl, which is a real thing paint does and is angular too.
    """
    x0, y0 = loc
    v = t.new("ShaderNodeTexVoronoi", "flake cells", (x0, y0))
    v.feature = "SMOOTH_F1"
    v.distance = "EUCLIDEAN"
    t.link(tc.outputs["Object"], v, "Vector")
    t.set(v, "Scale", FLAKE_SCALE)
    t.set(v, "Smoothness", FLAKE_SMOOTH)
    t.set(v, "Randomness", 1.0)
    # Distance from the cell centre is a smooth dome per cell -> a facet.
    height = v.outputs["Distance"]
    # A second, much coarser cell field so the flake is not uniformly dense:
    # real flake settles in drifts as the paint flows.
    drift = t.new("ShaderNodeTexNoise", "flake drift", (x0, y0 - 300))
    t.link(tc.outputs["Object"], drift, "Vector")
    t.set(drift, "Scale", 55.0)
    t.set(drift, "Detail", 2.0)
    t.set(drift, "Roughness", 0.5)
    dens = t.mapr(drift.outputs["Fac"], 0.35, 0.65, 0.55, 1.0,
                  loc=(x0 + 200, y0 - 300), label="flake density")
    return height, dens


def _pearl(t, loc):
    """A facing-driven pearl weight.

    `LayerWeight.Facing` is 1 - |dot(N, I)|^(2*Blend), not a Fresnel.  Round 1
    established on this same car why that matters: at Blend 0.28 the Fresnel
    output puts its whole transition inside the last 12 degrees before grazing —
    a sliver nobody sees — while Facing puts the same transition across 61-86
    degrees, which is the shoulder-wide band a pearl actually occupies.
    """
    lw = t.new("ShaderNodeLayerWeight", "pearl facing", loc)
    t.set(lw, "Blend", PEARL_BLEND)
    return t.mapr(lw.outputs["Facing"], 0.10, 0.70, 0.0, PEARL_MAX,
                  loc=(loc[0] + 200, loc[1]), label="pearl weight")


def apply(mat, report=None):
    nt, b = bsdf_of(mat)
    strip(mat, quiet=True)                 # idempotent: never stack on itself
    nt, b = bsdf_of(mat)
    mat[SNAP_KEY] = json.dumps(snapshot(mat))

    t = T(nt)
    X0, Y0 = b.location.x - 4200, b.location.y + 600

    tc, _sep = _object_coords(t, (X0, Y0 + 400))
    _geo, nsep = _object_normal(t, (X0, Y0 + 100))

    weave = _weave(t, tc, nsep, (X0 + 500, Y0))
    flake_h, flake_dens = _flake(t, tc, (X0 + 500, Y0 - 3600))
    pearl_w = _pearl(t, (X0 + 500, Y0 - 4200))

    XB = b.location.x - 1400

    # ---------------------------------------------------------------- colour
    # order matters and it is the order of the real stack, bottom up:
    #   basecoat lift  ->  weave telegraphing  ->  pearl  ->  livery pigment
    src = b.inputs["Base Color"].links[0].from_socket \
        if b.inputs["Base Color"].is_linked else None
    if src is None:
        raise SystemExit("LiveryPaint's Base Color is not linked — this module "
                         "expects round 1's livery chain to be feeding it")

    lifted = t.mixc(1.0, src, (*BASE_LIFT, 1.0), loc=(XB, Y0), blend="SCREEN",
                    label="basecoat lift")

    # the weave darkens the valleys and brightens the crowns, symmetric about
    # the weave's own mean of 0.5 so it cannot shift the paint's average
    wdev = t.math("MULTIPLY_ADD", weave, 2.0 * WEAVE_ALBEDO, 1.0 - WEAVE_ALBEDO,
                  loc=(XB - 200, Y0 - 200), label="weave gain")
    # a scalar socket cannot drive a colour input, so widen it to a vector
    comb = t.new("ShaderNodeCombineXYZ", "weave as colour", (XB, Y0 - 200))
    for c in ("X", "Y", "Z"):
        t.nt.links.new(wdev, comb.inputs[c])
    woven = t.mixc(1.0, lifted, comb.outputs["Vector"], loc=(XB + 200, Y0),
                   blend="MULTIPLY", label="weave through paint")

    pearled = t.mixc(pearl_w, woven, (*PEARL_TEAL, 1.0), loc=(XB + 400, Y0),
                     label="pearl")

    # THE LIVERY, MOVED OUT OF THE GLOW AND INTO THE PIGMENT.
    # The pattern is in Emission STRENGTH (see the note on EMIS_* above); the
    # colour socket is flat, so it is the strength that has to drive the mix and
    # the colour that has to be mixed IN.  Feeding the colour socket to a mix
    # factor — the first draft of this module did exactly that — floods the whole
    # body flat cyan.
    esrc0 = b.inputs["Emission Strength"].links[0].from_socket \
        if b.inputs["Emission Strength"].is_linked else None
    ecol = b.inputs["Emission Color"].links[0].from_socket \
        if b.inputs["Emission Color"].is_linked else None
    if esrc0 is not None and ecol is not None:
        pfac = t.mapr(esrc0, 0.0, PIGMENT_NORM_HI, 0.0, LIVERY_PIGMENT,
                      loc=(XB + 400, Y0 - 250), label="livery -> pigment")
        pigment = t.mixc(pfac, pearled, (*LIVERY_INK, 1.0),
                         loc=(XB + 600, Y0), label="livery as pigment")
    else:
        pigment = pearled
    t.link(pigment, b, "Base Color")

    # -------------------------------------------------------------- metallic
    msrc = b.inputs["Metallic"].links[0].from_socket \
        if b.inputs["Metallic"].is_linked else None
    scale = METALLIC_TARGET / METALLIC_SHIPPED
    if msrc is not None:
        t.link(t.math("MULTIPLY", msrc, scale, loc=(XB + 600, Y0 - 400),
                      label="metallic -> paint"), b, "Metallic")
    else:
        b.inputs["Metallic"].default_value = METALLIC_TARGET

    # ------------------------------------------------------------- roughness
    rsrc = b.inputs["Roughness"].links[0].from_socket \
        if b.inputs["Roughness"].is_linked else None
    wr = t.math("MULTIPLY_ADD", weave, -2.0 * WEAVE_ROUGH, WEAVE_ROUGH,
                loc=(XB, Y0 - 700), label="weave roughness")
    fr = t.math("MULTIPLY", flake_h, -FLAKE_ROUGH, loc=(XB, Y0 - 850),
                label="flake gloss")
    fr = t.math("MULTIPLY", fr, flake_dens, loc=(XB + 160, Y0 - 850),
                label="flake gloss x density")
    dr = t.math("ADD", wr, fr, loc=(XB + 320, Y0 - 780), label="roughness delta")
    if rsrc is not None:
        t.link(t.math("ADD", rsrc, dr, loc=(XB + 600, Y0 - 780), clamp=True,
                      label="roughness"), b, "Roughness")
    else:
        t.link(t.math("ADD", 0.155, dr, loc=(XB + 600, Y0 - 780), clamp=True,
                      label="roughness"), b, "Roughness")

    # ---------------------------------------------------------- base normal
    # weave relief, then flake facets on top of it.  The base Normal is the right
    # place for both: they are the SUBSTRATE and the BASECOAT, under the clear.
    nb = t.new("ShaderNodeBump", "weave relief", (XB, Y0 - 1100))
    t.set(nb, "Strength", WEAVE_BUMP_STR)
    t.set(nb, "Distance", WEAVE_BUMP_M)
    t.link(weave, nb, "Height")

    fb = t.new("ShaderNodeBump", "flake facets", (XB + 250, Y0 - 1100))
    t.set(fb, "Strength", FLAKE_BUMP_STR)
    t.set(fb, "Distance", FLAKE_BUMP_M)
    t.link(flake_h, fb, "Height")
    t.link(nb.outputs["Normal"], fb, "Normal")
    t.link(fb.outputs["Normal"], b, "Normal")

    # ---------------------------------------------------------- coat normal
    # ROUND 1'S ORANGE PEEL WAS ON THE WRONG NORMAL.  `livery_paint` builds a
    # scale-140 noise -> Bump(0.035, 0.0025) and feeds it to Principled.Normal —
    # the BASE.  Orange peel is a clearcoat surface: it is what makes the
    # reflection ripple.  Under a 0.022-roughness coat the base normal's
    # perturbation is almost invisible, which is why the shipped panel mirrors.
    # The existing bump chain is not rebuilt, it is RE-ROUTED, so round 1's
    # tuning of it survives.
    peel_src = None
    snap = json.loads(mat[SNAP_KEY])
    old_n = snap["sockets"].get("Normal", {})
    if old_n.get("linked"):
        node = nt.nodes.get(old_n["from_node"])
        if node is not None and old_n["from_socket"] in node.outputs:
            peel_src = node.outputs[old_n["from_socket"]]
    if peel_src is not None:
        t.link(peel_src, b, "Coat Normal")
        moved = "%s.%s" % (old_n["from_node"], old_n["from_socket"])
    else:
        moved = None

    # ----------------------------------------------------------------- coat
    b.inputs["Coat Tint"].default_value = (*COAT_TINT, 1.0)
    b.inputs["Coat Roughness"].default_value = COAT_ROUGH

    # ------------------------------------------------------------- emission
    # Cut the bottom of round 1's emission ladder — the graph network and the
    # particle streams, which is what reads as internal wiring — and leave the
    # pulse line and the numeral, which are designed light sources, alone.
    if esrc0 is not None:
        keep = t.mapr(esrc0, EMIS_RAMP_LO, EMIS_RAMP_HI, EMIS_KEEP_LO, 1.0,
                      loc=(XB + 400, Y0 - 1400), label="keep the bright rungs")
        t.link(t.math("MULTIPLY", esrc0, keep, loc=(XB + 600, Y0 - 1400),
                      label="emission ladder"), b, "Emission Strength")
    else:
        b.inputs["Emission Strength"].default_value *= EMIS_KEEP_LO

    mat[VER_KEY] = VERSION
    info = {"material": mat.name, "version": VERSION, "nodes_added": t.n,
            "orange_peel_moved_from_Normal_to_Coat_Normal": moved,
            "base_lift": list(BASE_LIFT), "metallic": METALLIC_TARGET,
            "coat_tint": list(COAT_TINT), "coat_roughness": COAT_ROUGH,
            "emission_keep_lo": EMIS_KEEP_LO,
            "emission_ramp": [EMIS_RAMP_LO, EMIS_RAMP_HI],
            "livery_pigment": LIVERY_PIGMENT,
            "livery_ink": list(LIVERY_INK),
            "weave_pitch_m": WEAVE_PITCH_M, "flake_scale": FLAKE_SCALE}
    log("applied to %s: +%d nodes, orange peel %s"
        % (mat.name, t.n, "moved to Coat Normal" if moved else "NOT FOUND"))
    if report is not None:
        report.append(info)
    return info


# --------------------------------------------------------------------------- #
def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--material", default=TARGET_MATERIAL)
    ap.add_argument("--strip", action="store_true")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--save-as", default="")
    ap.add_argument("--report", default="")
    a = ap.parse_args(argv)

    mat = bpy.data.materials.get(a.material)
    if mat is None:
        raise SystemExit("no material %r in this blend (it has %d materials)"
                         % (a.material, len(bpy.data.materials)))

    rep = []
    if a.strip:
        n, r = strip(mat)
        rep.append({"stripped": mat.name, "nodes_removed": n,
                    "sockets_restored": r})
    else:
        apply(mat, rep)

    nt, b = bsdf_of(mat)
    print("\n---- %s after ----" % mat.name)
    for name in SNAP_SOCKETS:
        if name not in b.inputs:
            continue
        s = b.inputs[name]
        if s.is_linked:
            print("   %-18s <- %s" % (name, s.links[0].from_node.name))
        else:
            v = s.default_value
            v = [round(float(x), 4) for x in v] if hasattr(v, "__len__") \
                else round(float(v), 4)
            print("   %-18s =  %s" % (name, v))
    print("   nodes in tree      %d" % len(nt.nodes))

    if a.report:
        with open(a.report, "w") as f:
            json.dump(rep, f, indent=1)

    if a.save_as:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save_as),
                                    compress=False)
        log("saved as", a.save_as)
    elif a.save:
        bpy.ops.wm.save_mainfile()
        log("saved in place", bpy.data.filepath)

    print(">> STAGE RESULT: %s_%s_OK" % (RESULT, "STRIP" if a.strip else "APPLY"))


# Blender runs a `-P` script with __name__ == "__main__"; an `importlib`
# consumer gets "car_paint".  Without this guard, importing the module to call
# `apply()` also runs the CLI and applies the stack a second time.
if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        print(">> STAGE RESULT: %s_FAIL" % RESULT)
        sys.stdout.flush()
