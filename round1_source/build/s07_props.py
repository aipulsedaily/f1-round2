"""Showroom staging: props placed against what the cameras actually see.

The previous dressing was positioned by azimuth and hope. Measuring it found
83 % of the prop budget rendering zero pixels - TyreStackA + TyreStackB were
14,448 of 17,378 PROPS polys and neither appeared in any of the four delivered
frames - while PitCase_A/_B projected inside the car's screen box, behind it, as
6-poly boxes at 0.028 albedo. Meanwhile 44.6 % of the 4K hero frame was dark and
locally featureless, 82.2 % of it in the upper half.

Everything here therefore lives in one of four corridors that were projected
through all four cameras before any geometry was written:

  A  frame-left floor, world x -7.5..-9.4, y -0.35..+2.15 -> FQ frame x 0.01-0.30
  B  above the car,    world x -9..-14.8,  y +1.4..+8.4    -> FQ frame y 0.55-1.00
  C  the -X wall above s05's light line, z 2.6-3.2         -> FQ frame y 0.89-0.95
  D  behind the front lenses, world x > +11 -> negative depth for FQ and HeroLow

and outside the wedge that produced D114 twice: world x +1..+6, y -1..-5 at less
than 5.9 m from the front-quarter lens. Corridor A also has an inner bound that
the brief did not: r > 6.95, the barrier ring, because kit inside it is standing
in the exhibit rather than beside it.

Every placement was then re-checked against the geometry that actually got built,
by sampling real mesh vertices through all four cameras rather than bounding
boxes - a box false-flags every flat inlay and every object straddling a lens
plane. The current build has zero vertices anywhere that land inside the car's
screen box while nearer to a lens than the car. Measured frame boxes are recorded
next to each placement so the next person can tell a decision from a guess.

WHAT THIS MODULE OWNS, AFTER s02 AND s05 MOVED
----------------------------------------------
The design brief was written against a room that had bare walls, a bare floor and
a bare deck. While this was being built, s02 clad both solid walls in fluted
panels and drew datum inlays on the floor (r = 7.30) and the deck (y = +/-1.420,
groove at r = 3.200), and s05 replaced the rope-post ring with lit bollards and
ran an illuminated reveal along both walls at z = 2.44. Four of the brief's
twelve proposals were the same ideas, and building them anyway produced 115
interpenetrating object pairs against the new room.

So the division is now: s02 owns the room, s05 owns the light, and s07 owns the
things standing in it - plus all typography, which is the one thing neither of
the others has and which nothing else in this build can produce. The wall fin
field, the wall reveal, the deck datum ring, the deck dimension line and the
side-wall timing rail are deleted for that reason and each says so where it used
to be. Two hard dependencies run the other way and are annotated at the code that
honours them: s05's bollards are keyed to the barrier post's 0.108 m flare at
z = 0.026, and s05's wall line owns the z 2.415-2.465 band on both walls.

CLIPPING IS THE BINDING CONSTRAINT, NOT POLYCOUNT
-------------------------------------------------
The transfer curve measured for this project's view transform (AgX + Medium High
Contrast, exposure 0) is

    radiance  0.02  0.10  0.35  0.70  1.40  3.00  4.50  6.50
    8-bit       23    81   160   194   219   238   246   252

so peep.py's clip threshold of 250 is not reached until scene radiance ~5.6.
After the descope this module adds exactly one emitter, and it is specified in
radiance against that curve rather than by eye: three forecourt lamp heads at
3.0 (8-bit ~238), 0.3 m2 in total, 35 m away, outside the building and visible
only to RearQuarter. That radiates under 3 W against the rig's 2130 W and cannot
reach the >=250 metric at all. The other two emitters this file used to carry -
a back-wall reveal and a wall of timing screens - were deleted with the elements
they belonged to, so the clipping budget this pass spends is essentially zero.
Nothing here touches the light rig: a 1.6x global scale once took frame clipping
from 1.0 % to 6.2 %.

The rest of the clipping risk is specular, not emissive, which is why every large
flat metal face added here is at roughness >= 0.30 - see _SURFACES.

The other direction matters on one camera only: RearQuarter is at 0.360 % crushed
against a 0.500 % ceiling, so the two elements that land in that frame (the
vitrine and the forecourt) are built pale rather than dark. The forecourt apron
is a net win there - it replaces 0.020-albedo ExteriorGround, which is what is
crushing, with 0.28-albedo concrete.
"""

import math

import bpy
from mathutils import Euler, Matrix, Vector

import common as C
import s02_showroom as S
import s03_materials as M
import s04_car as CAR
import spec as SPEC

# The marque this exhibit is dressed for. The tyres already carry a supplier
# wordmark ("APEX", build/parts/wheel_tyre.py), so the constructor has to be a
# different name or the car reads as being sponsored by its own tyre brand.
MARQUE = "MERIDIAN"
MODEL = "MR-24"

DECK_Z = S.TT_TOP           # 0.340, the deck the car stands on

# Anything applied to the deck or the floor stands proud and is also sunk into
# its host, s02's rule: a face landing exactly on the host gives Cycles two
# coincident surfaces and a speckled seam across the most specular thing in shot.
INLAY_PROUD = 0.003


# --------------------------------------------------------------------------- #
# materials
# --------------------------------------------------------------------------- #

# name -> (base rgb, metallic, roughness). Large flat metal faces the key light
# reaches are all >= 0.30 roughness: at 0.16 a flat bar returns the 27.8 W/m2/sr
# key almost intact, which is five times the clip threshold. Small round parts
# can be shinier because their mirror image of a source is a few pixels wide.
_SURFACES = {
    "PropChrome":     ((0.620, 0.630, 0.650), 1.00, 0.16),
    "PropSteelDark":  ((0.085, 0.088, 0.095), 1.00, 0.42),
    "PropCase":       ((0.105, 0.112, 0.130), 0.35, 0.44),
    "PlaqueFace":     ((0.020, 0.021, 0.026), 0.20, 0.28),
    "PropSignFace":   ((0.032, 0.034, 0.040), 0.15, 0.35),
    # Deck inlay. The deck is 0.048 albedo / 0.86 metallic / 0.40 rough and reads
    # 0.4-0.6 luma in the front quarter but ~0.24 top-down, so a flat mid-grey
    # would vanish in one frame and shout in the other. 0.30 with a machined
    # bevel throws a specular line instead of relying on the albedo step, and
    # stays under the 0.35 ceiling the dais retune established.
    "PropInlay":      ((0.300, 0.302, 0.312), 0.85, 0.30),
    "PropFloorInlay": ((0.220, 0.224, 0.236), 0.90, 0.34),
    "PropFabric":     ((0.075, 0.078, 0.088), 0.00, 0.86),
    "PropStrap":      ((0.145, 0.105, 0.058), 0.00, 0.72),
    "PropRubber":     ((0.022, 0.023, 0.025), 0.00, 0.68),
    "PropFoam":       ((0.048, 0.050, 0.056), 0.00, 0.92),
    # Forecourt. Pale on purpose: this is the one frame where crush, not clip,
    # is the near constraint.
    "PropConcrete":   ((0.280, 0.280, 0.276), 0.00, 0.72),
    "PropKerb":       ((0.350, 0.350, 0.345), 0.00, 0.62),
    "PropFoliage":    ((0.062, 0.098, 0.052), 0.00, 0.80),
}


def _mat(name):
    """Get-or-create one of the prop surfaces, or a satin/bright anodised alu."""
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    # anodized_alu takes RGBA, not RGB: set_defaults writes straight into a
    # Principled colour socket, which rejects a 3-tuple outright.
    if name == "PropAluSatin":
        return M.anodized_alu("PropAluSatin", (0.420, 0.430, 0.450, 1.0), 0.34)
    if name == "PropAluBright":
        return M.anodized_alu("PropAluBright", (0.660, 0.670, 0.700, 1.0), 0.24)
    if name == "PropCaseGlass":
        return M.display_glass("PropCaseGlass")
    base, metallic, rough = _SURFACES[name]
    mat, nt, b = C.material(name)
    C.set_defaults(b, Base_Color=(*base, 1.0), Metallic=metallic, Roughness=rough)
    return mat


def _pole_emit():
    """Forecourt lamp heads: 3.0 -> ~238, and 0.3 m2 of it at 35 m."""
    return M.emitter("PropPoleEmit", (1.0, 0.93, 0.80), 3.0)


# --------------------------------------------------------------------------- #
# geometry helpers
# --------------------------------------------------------------------------- #

def _boxes(name, specs, coll, smooth=False):
    """One mesh from many (cx, cy, cz, sx, sy, sz, rot_z) boxes.

    Fin fields, tick marks, gear teeth and drawer fronts are all dozens of
    identical primitives. Emitting them as one mesh keeps the object count (and
    therefore the bevel-modifier count) proportional to the *part*, not to the
    number of repeats.
    """
    verts, faces = [], []
    for cx, cy, cz, sx, sy, sz, rz in specs:
        ca, sa = math.cos(rz), math.sin(rz)
        hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
        b = len(verts)
        for dz in (-hz, hz):
            for dx, dy in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
                verts.append((cx + dx * ca - dy * sa,
                              cy + dx * sa + dy * ca, cz + dz))
        faces += [(b, b + 3, b + 2, b + 1), (b + 4, b + 5, b + 6, b + 7),
                  (b, b + 1, b + 5, b + 4), (b + 1, b + 2, b + 6, b + 5),
                  (b + 2, b + 3, b + 7, b + 6), (b + 3, b, b + 4, b + 7)]
    return C.new_obj(name, verts, faces, coll=coll, smooth=smooth)


def _slab(name, centre, size, coll, rot_z=0.0):
    cx, cy, cz = centre
    return _boxes(name, [(cx, cy, cz, size[0], size[1], size[2], rot_z)], coll)


def _ring(name, r_in, r_out, z0, z1, coll, segments=96):
    """Flat annulus as a closed rectangular section, for inlays and collars."""
    return C.revolve(name, [(r_in, z0), (r_out, z0), (r_out, z1),
                            (r_in, z1), (r_in, z0)],
                     segments=segments, coll=coll, auto_smooth=30.0)


def _scale_mesh(ob, sx, sy, sz=1.0):
    for v in ob.data.vertices:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    ob.data.update()
    return ob


def _bbox(ob):
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    if not xs:
        return 0.0, 0.0
    return max(xs) - min(xs), max(ys) - min(ys)


def _transform_group(objs, loc, rot=(0.0, 0.0, 0.0)):
    """Move a group built at the origin into place as one rigid body.

    Sub-assemblies (plaque, pit board, vitrine) are far easier to author facing
    +Y at the origin and then placed, than to author in situ with every vertex
    pre-rotated. Composing matrices keeps the parts locked together no matter how
    the assembly is later re-aimed.
    """
    # matrix_world is only recomputed from location/rotation_euler when the
    # depsgraph runs, so a caller that sets those and calls straight in here
    # composes onto a STALE matrix - identity, for an object created this build.
    # The per-object placement is then overwritten and the whole group collapses
    # onto `loc` with `rot`. That silently flattened every plaque text run and
    # both stencils onto their group origin; the groups that survived did so only
    # because a later text_mesh() happened to call view_layer.update() first.
    bpy.context.view_layer.update()
    m = Matrix.Translation(Vector(loc)) @ Euler(rot, "XYZ").to_matrix().to_4x4()
    for ob in objs:
        ob.matrix_world = m @ ob.matrix_world
    return objs


def _face_azimuth(frm, to):
    """rot_z that turns a group whose face normal is local -Y to look at `to`.

    The sign here must agree with PANEL_TEXT_ROT, which orients text to face
    local -Y (every caller offsets its text to a negative local y to stand it
    proud of its panel). This returned the +Y-facing angle, so all three groups
    built with it - the spec plaque, the hand-held pit board and the vitrine
    caption - were turned exactly 180 degrees away from the camera they were
    aimed at, and rendered as blank slabs. Roughly 6,400 vertices of typography
    were in every frame and legible in none of them.
    """
    return math.atan2(to[1] - frm[1], to[0] - frm[0]) + math.pi / 2.0


_FONT_WARNED = []


def text_mesh(name, body, size, coll, extrude=0.005, res=4, spacing=1.0,
              bevel=0.0, fit_width=None, mat=None):
    """Extruded typography with no font file and no operators.

    bpy.ops.object.convert needs an object-mode 3D-viewport context that does not
    exist under `blender -b --factory-startup`; it is the same trap that broke
    shade_auto_smooth. meshes.new_from_object on the evaluated FONT curve is the
    ops-free equivalent and costs 55-70 polys per glyph at resolution_u=4.

    fit_width scales the finished mesh to a target world width so that layout
    does not depend on the built-in font's metrics, which are not ours to pin.
    """
    cu = bpy.data.curves.new(name + "_CU", type="FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.resolution_u = res
    cu.space_character = spacing
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    if bevel:
        cu.bevel_depth = bevel
        cu.bevel_resolution = 1
        cu.offset = -bevel * 0.5      # a bevel fattens the outline; take it back

    tmp = bpy.data.objects.new(name + "_CU", cu)
    coll.objects.link(tmp)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(
        tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.curves.remove(cu)

    if not me.polygons:
        # No built-in font available. Degrade to a blank plate rather than
        # shipping an invisible sign, and say so once.
        if not _FONT_WARNED:
            print("!! s07_props: no usable font, typography degraded to plates")
            _FONT_WARNED.append(True)
        bpy.data.meshes.remove(me)
        w = fit_width or size * 0.62 * len(body)
        ob = _boxes(name, [(0, 0, 0, w, size * 0.72, extrude * 2, 0.0)], coll)
    else:
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)

    if fit_width:
        w, _h = _bbox(ob)
        if w > 1e-6:
            k = fit_width / w
            _scale_mesh(ob, k, k)     # z left alone: extrusion depth is spec'd
    C.assign(ob, mat or _mat("PropAluBright"))
    return ob


# Text lying flat on a horizontal surface reads along the surface's local +X,
# which is left-to-right in FrontQuarter, HeroLow and TopDown (screen-right has a
# positive X component in all three). RearQuarter's screen-right is -X, so
# anything on the deck's +Y band renders mirrored there; that is why all deck
# typography is on the -Y band, where the car itself hides it from RearQuarter.
#
# Text on the -X wall must read along +Y with its normal along +X.
WALL_TEXT_ROT = (math.pi / 2.0, 0.0, math.pi / 2.0)
# Text on a vertical panel whose face normal is the group's local +Y.
# Text is authored in the XY plane reading toward +Z. Rotating +90 deg about X
# maps +Z to -Y, so the glyphs face -Y - which is the side every caller places
# them on (all use a negative-Y offset to stand proud of their panel). The extra
# pi about Z that used to be here flipped them to face +Y, i.e. INTO their own
# board, so every panel was showing the BACK of its text and read mirrored:
# the pit board rendered "TH4 10 TUO" instead of "OUT 01 4HT".
PANEL_TEXT_ROT = (math.pi / 2.0, 0.0, 0.0)


# --------------------------------------------------------------------------- #
# 1. wall wordmark  (corridor C, -X)
# --------------------------------------------------------------------------- #

# s02 fluting: 40 mm panel standoff + 100 mm fin projection, so the face of the
# back wall's fins is at x = -14.860 and the side wall's at y = +10.860.
FLUTE_FACE_X = -S.ROOM_X + S.PANEL_STANDOFF + S.FLUTE_D
# s05's illuminated reveal runs at z 2.44 +/- 25 mm on both walls. Nothing here
# may sit in that band or stand in front of it: that line is the room's strongest
# depth cue and it converges one degree off frame centre behind the car. The sign
# is positioned from the top of that band rather than from an absolute z, so if
# s05 moves its line the sign moves with it instead of landing on top of it.
WALL_LINE_Z = 2.44
WALL_LINE_H = 0.05
WALL_SIGN_BASE = WALL_LINE_Z + WALL_LINE_H * 0.5 + 0.163


def build_wall_wordmark(coll):
    """Applied signage on the -X wall, and nothing else.

    THIS WAS A FIN FIELD WITH A LIT REVEAL AND IS NOT ANY MORE. Between the
    design brief and this implementation, s02 built fluted panels over both solid
    walls (1.20 m bay, 130 mm face, 100 mm projection) and s05 put a continuous
    illuminated reveal at z 2.44 on both of them. Both of those are the same idea
    as the brief's proposal 1, they are already measured against these frames,
    and they own the wall. Building a second fin field 60-92 mm proud of x=-15
    put 5 interpenetrating pairs into the scene and would have covered the
    reveal. Deleted; what is left is the one thing neither module has, which is
    typography.

    So this mounts 46 mm proud of the fluting face at x = -14.860, and sits at
    z 2.78-3.12 - above s05's line at 2.415-2.465 with 315 mm of clear wall
    between them, so the line still runs unbroken behind the car.
    """
    made = []
    bright = _mat("PropAluBright")
    x_face = FLUTE_FACE_X + 0.024

    # 340 mm caps centred at y +5.40: clear of the gantry at y +7.60, and
    # measured to FrontQuarter frame x 0.14-0.26 - the dead upper-left quadrant,
    # above the car's screen top of 0.690 - and HeroLow x 0.25-0.36.
    word = text_mesh("WallSign_Word", MARQUE, 0.34, coll, extrude=0.022,
                     res=4, spacing=1.18, bevel=0.004, fit_width=2.60,
                     mat=bright)
    word.rotation_euler = WALL_TEXT_ROT
    word.location = (x_face, 5.40, WALL_SIGN_BASE + 0.322)
    made.append(word)

    strap = text_mesh("WallSign_Strap", "GRAND PRIX COLLECTION", 0.072, coll,
                      extrude=0.008, res=3, spacing=1.30, fit_width=2.30,
                      mat=bright)
    strap.rotation_euler = WALL_TEXT_ROT
    strap.location = (x_face - 0.012, 5.40, WALL_SIGN_BASE + 0.060)
    made.append(strap)

    # A hairline rule under the strapline ties the two together and gives the
    # grazing wall wash a horizontal to catch.
    rule = _boxes("WallSign_Rule", [
        (x_face - 0.020, 5.40, WALL_SIGN_BASE, 0.016, 2.60, 0.008, 0.0)], coll)
    C.assign(rule, bright)
    made.append(rule)
    return made


# --------------------------------------------------------------------------- #
# 2. deck typography  (front quarter, HeroLow, TopDown)
# --------------------------------------------------------------------------- #

def build_deck_type(coll):
    """Labels for the deck datum s02 already draws, in the deck's own frame.

    ALSO DESCOPED, and for the same reason. The brief asked for a datum ring at
    r 3.20, quadrant ticks and a wheelbase dimension line; s02 has since built a
    groove at r 3.200 and datum lines at y = +/-1.420 with station ticks at
    x = 0, 0.95, 1.90, 2.70. Adding a ring at 3.180-3.220 would have laid metal
    straight on top of the groove. What their datum has never had is a number on
    it, so that is what this adds.

    The brief said to align this to the car's +X and not to the deck's 12 degree
    yaw. That was right when the deck carried nothing; it is wrong now. These are
    labels ON s02's datum lines, and a caption running 12 degrees off the line it
    annotates reads as a mistake, so the whole group shares TT_ROT_DEG. Text
    still runs along the deck's local +X, which is left-to-right in
    FrontQuarter, HeroLow and TopDown - RearQuarter's screen-right is -X, which
    is why nothing is put on the +Y band where that camera would see it mirrored.
    """
    made = []
    inlay = _mat("PropInlay")
    yaw = math.radians(S.TT_ROT_DEG)
    z = DECK_Z + INLAY_PROUD * 0.5

    # s02's datum line sits at |y| 1.4075-1.4325 with ticks reaching 1.3375.
    # The band between that and the car's 1.000 half-width is 0.34 m wide, so
    # both lines are sized to fit it with clearance rather than to look big.
    rows = [("DeckType_Word", MARQUE, 0.100, 1.50, -1.130),
            ("DeckType_Dim", f"{int(round(SPEC.WHEELBASE * 1000))} mm WHEELBASE",
             0.058, 1.34, -1.272)]
    for name, body, size, width, y_local in rows:
        t = text_mesh(name, body, size, coll, extrude=0.0025, res=4,
                      spacing=1.18, fit_width=width, mat=inlay)
        # NOT yaw + pi. Adding pi was tried and is wrong: it reads correctly
        # in the TOP-DOWN camera as authored, which is the only camera where
        # deck lettering is legible at all. In the three oblique cameras the
        # text reads away from the lens at a grazing angle, which superficially
        # resembles mirroring but is not - the glyphs are correctly formed.
        # Verified from CAM_TopDown, where +pi rendered it visibly upside down.
        t.rotation_euler = (0.0, 0.0, yaw)
        t.location = (-y_local * math.sin(yaw), y_local * math.cos(yaw), z)
        made.append(t)
    return made


# --------------------------------------------------------------------------- #
# 4. floor graphics  (front quarter + rear quarter)
# --------------------------------------------------------------------------- #

BOX_HX, BOX_HY = 8.20, 4.60


def build_floor_graphics(coll):
    """Inlaid pit-box outline: 80 mm brushed lines on a 0.035-albedo mirror.

    This is what gives the room its scale. The front quarter sees the far leg and
    the +Y leg (47/164 sampled points in frame, zero of them nearer to the lens
    than the car); the rear quarter sees the -Y leg (48/164). Different legs for
    different cameras is honest - one bay drawn once, read from two sides.

    s02's floor datum ring at r = 7.30 crosses this bay at four points. That is
    fine - crossing inlays is what real floor graphics do - but the two must
    never share a top plane, so this sits 2 mm proud against the ring's 3 mm and
    borrows s02's rule of sinking 4 mm into the slab so no face is coplanar with
    the largest specular surface in the room.
    """
    made = []
    z0, z1 = -S.INLAY_SINK, 0.002
    w = 0.080
    zc, zt = (z0 + z1) * 0.5, z1 - z0
    specs = [
        (0.0, BOX_HY, zc, 2 * BOX_HX + w, w, zt, 0.0),
        (0.0, -BOX_HY, zc, 2 * BOX_HX + w, w, zt, 0.0),
        (BOX_HX, 0.0, zc, w, 2 * BOX_HY - w, zt, 0.0),
        (-BOX_HX, 0.0, zc, w, 2 * BOX_HY - w, zt, 0.0),
    ]
    # Corner ticks: short inboard returns that make the corners read as set out
    # rather than as four lines that happen to meet.
    for sx in (-1, 1):
        for sy in (-1, 1):
            specs.append((sx * (BOX_HX - 0.45), sy * (BOX_HY - 0.30), zc,
                          0.90, 0.048, zt, 0.0))
            specs.append((sx * (BOX_HX - 0.30), sy * (BOX_HY - 0.45), zc,
                          0.048, 0.90, zt, 0.0))
    lines = _boxes("Floor_PitBox", specs, coll)
    C.add_bevel(lines, width=0.0008, segments=2)
    C.assign(lines, _mat("PropFloorInlay"))
    made.append(lines)

    # Bay number stencilled inside the far leg, reading along +Y so it is correct
    # in both front cameras. At (-7.90, +3.00) it is 2.5 m outside the rear
    # quarter's frame and clear of the corridor-A cluster.
    bay = text_mesh("Floor_BayNumber", f"PIT 01  {MODEL}", 0.34, coll,
                    extrude=zt * 0.5, res=3, spacing=1.15, fit_width=2.40,
                    mat=_mat("PropFloorInlay"))
    bay.rotation_euler = (0.0, 0.0, math.pi / 2.0)
    bay.location = (-7.90, 3.00, zc)
    made.append(bay)
    return made


# --------------------------------------------------------------------------- #
# 3 + 12. pit-garage kit  (corridor A)
# --------------------------------------------------------------------------- #

def _castors(name, centre, half_x, half_y, coll, r=0.048):
    """Four swivel castors under a trolley or case."""
    made = []
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        w = C.revolve(f"{name}_Castor{i}", [
            (0.000, -0.020), (r * 0.62, -0.020), (r, -0.008), (r, 0.008),
            (r * 0.62, 0.020), (0.000, 0.020), (0.000, -0.020)],
            segments=16, coll=coll, auto_smooth=40.0)
        w.rotation_euler = (math.pi / 2.0, 0.0, 0.4 * i)
        w.location = (centre[0] + sx * half_x, centre[1] + sy * half_y, r)
        C.assign(w, _mat("PropRubber"))
        made.append(w)
        yoke = _slab(f"{name}_Yoke{i}", (centre[0] + sx * half_x,
                                         centre[1] + sy * half_y, r + 0.055),
                     (0.052, 0.052, 0.070), coll)
        C.assign(yoke, _mat("PropChrome"))
        made.append(yoke)
    return made


def build_wheel_gun_rack(x, y, coll, rot=0.0):
    """Four wheel guns on hangers in a welded frame."""
    made = []
    alu, dark = _mat("PropAluSatin"), _mat("PropSteelDark")
    frame = []
    for sx in (-0.38, 0.38):
        frame.append((sx, 0.0, 0.66, 0.048, 0.048, 1.32, 0.0))
    for z in (0.06, 0.70, 1.28):
        frame.append((0.0, 0.0, z, 0.80, 0.042, 0.042, 0.0))
    for sx in (-0.38, 0.38):                       # feet
        frame.append((sx, 0.0, 0.020, 0.110, 0.300, 0.040, 0.0))
    fr = _boxes("GunRack_Frame", frame, coll)
    C.add_bevel(fr, width=0.005, segments=2)
    C.assign(fr, alu)
    made.append(fr)

    for i in range(4):
        gx = -0.285 + i * 0.190
        body = C.revolve(f"GunRack_Gun{i}", [
            (0.000, 0.000), (0.052, 0.000), (0.058, 0.026), (0.062, 0.090),
            (0.058, 0.150), (0.046, 0.176), (0.030, 0.186), (0.030, 0.230),
            (0.041, 0.246), (0.041, 0.300), (0.026, 0.316), (0.000, 0.320)],
            segments=20, coll=coll, auto_smooth=36.0)
        body.location = (gx, 0.0, 0.74)
        C.assign(body, dark)
        made.append(body)
        # the square drive that actually turns the wheel nut
        drive = _slab(f"GunRack_Socket{i}", (gx, 0.0, 0.705),
                      (0.048, 0.048, 0.070), coll, rot_z=0.4)
        C.assign(drive, _mat("PropChrome"))
        made.append(drive)
        grip = _slab(f"GunRack_Grip{i}", (gx, 0.085, 0.905),
                     (0.046, 0.150, 0.052), coll)
        C.add_bevel(grip, width=0.010, segments=2)
        C.assign(grip, _mat("PropFoam"))
        made.append(grip)
        # air line looping from the gun butt down to the frame foot
        hose = CAR.tube(f"GunRack_Line{i}", [
            (gx, 0.0, 1.060), (gx, 0.115, 1.140), (gx + 0.05, 0.170, 1.020),
            (gx + 0.02, 0.130, 0.760), (gx - 0.03, 0.055, 0.420),
            (gx, 0.0, 0.120)], 0.011, coll, segments=8)
        C.assign(hose, _mat("PropRubber"))
        made.append(hose)

    _transform_group(made, (x, y, 0.0), (0.0, 0.0, rot))
    return made


def build_hose_reel(x, y, coll, rot=0.0):
    """Air-line reel on a floor stand with the hose coiled on the drum."""
    made = []
    stand = _boxes("HoseReel_Stand", [
        (0.0, 0.0, 0.020, 0.560, 0.400, 0.040, 0.0),
        (-0.230, 0.0, 0.400, 0.060, 0.070, 0.720, 0.0),
        (0.230, 0.0, 0.400, 0.060, 0.070, 0.720, 0.0),
        (0.0, 0.0, 0.775, 0.520, 0.070, 0.055, 0.0)], coll)
    C.add_bevel(stand, width=0.005, segments=2)
    C.assign(stand, _mat("PropAluSatin"))
    made.append(stand)

    drum = C.revolve("HoseReel_Drum", [
        (0.000, -0.150), (0.235, -0.150), (0.235, -0.128), (0.130, -0.120),
        (0.130, 0.120), (0.235, 0.128), (0.235, 0.150), (0.000, 0.150),
        (0.000, -0.150)],
        segments=32, coll=coll, auto_smooth=36.0)
    drum.rotation_euler = (math.pi / 2.0, 0.0, 0.0)
    drum.location = (0.0, 0.0, 0.560)
    C.assign(drum, _mat("PropSteelDark"))
    made.append(drum)

    # Coiled hose: a helix on the drum, then a lead running off to the floor.
    coil = []
    turns, per = 5.0, 16
    for i in range(int(turns * per) + 1):
        t = i / per
        a = C.TAU * t
        r = 0.152 + 0.0115 * t
        coil.append((0.0 + r * math.cos(a), -0.085 + 0.034 * t, 0.560 + r * math.sin(a)))
    # The lead runs out toward the gun rack and stops at its foot. It used to run
    # the other way, to local +x, which put it straight across the bollard s05
    # lights at (-6.81, 1.38) - a rubber hose lying over an emissive annulus.
    coil += [(-0.26, -0.10, 0.34), (-0.36, -0.24, 0.13), (-0.44, -0.40, 0.030),
             (-0.46, -0.50, 0.026)]
    hose = CAR.tube("HoseReel_Hose", coil, 0.013, coll, segments=8)
    C.assign(hose, _mat("PropRubber"))
    made.append(hose)

    _transform_group(made, (x, y, 0.0), (0.0, 0.0, rot))
    return made


def build_tool_chest(x, y, coll, rot=0.0):
    """Roll-cab with drawer fronts, pulls, castors and a stencilled car number."""
    made = []
    w, d, h = 1.04, 0.62, 0.94
    body = _slab("ToolChest_Body", (0.0, 0.0, 0.10 + h * 0.5), (w, d, h), coll)
    C.add_bevel(body, width=0.014, segments=3)
    C.assign(body, _mat("PropCase"))
    made.append(body)

    top = _slab("ToolChest_Top", (0.0, 0.0, 0.10 + h + 0.018),
                (w + 0.030, d + 0.030, 0.036), coll)
    C.add_bevel(top, width=0.008, segments=2)
    C.assign(top, _mat("PropAluSatin"))
    made.append(top)

    fronts, pulls = [], []
    zc = 0.16
    for i, dh in enumerate((0.115, 0.115, 0.155, 0.195, 0.245)):
        fronts.append((0.0, -d * 0.5 - 0.006, zc + dh * 0.5,
                       w - 0.040, 0.016, dh - 0.014, 0.0))
        pulls.append((0.0, -d * 0.5 - 0.028, zc + dh * 0.5,
                      w - 0.240, 0.030, 0.022, 0.0))
        zc += dh
    fr = _boxes("ToolChest_Fronts", fronts, coll)
    C.add_bevel(fr, width=0.005, segments=2)
    C.assign(fr, _mat("PropSteelDark"))
    made.append(fr)
    pl = _boxes("ToolChest_Pulls", pulls, coll)
    C.add_bevel(pl, width=0.006, segments=2)
    C.assign(pl, _mat("PropChrome"))
    made.append(pl)

    made += _castors("ToolChest", (0.0, 0.0, 0.0), w * 0.42, d * 0.34, coll)

    stencil = text_mesh("ToolChest_Stencil", MODEL, 0.085, coll, extrude=0.002,
                        res=3, spacing=1.20, fit_width=0.34,
                        mat=_mat("PropAluBright"))
    stencil.rotation_euler = PANEL_TEXT_ROT
    stencil.location = (0.0, -d * 0.5 - 0.036, 0.10 + h + 0.048)
    made.append(stencil)

    _transform_group(made, (x, y, 0.0), (0.0, 0.0, rot))
    return made


def build_wing_trolley(x, y, coll, rot=0.0):
    """Front-wing trolley, left empty.

    Empty is the point: it says the wing is on the car. A second wing lying here
    would read as a duplicate of the one already in frame.
    """
    made = []
    frame = [
        (0.0, 0.0, 0.560, 1.180, 0.050, 0.048, 0.0),
        (0.0, 0.0, 0.560, 0.050, 0.700, 0.048, 0.0),
        (0.0, 0.0, 0.130, 1.180, 0.048, 0.044, 0.0),
    ]
    for sx in (-0.545, 0.545):
        for sy in (-0.320, 0.320):
            frame.append((sx, sy, 0.320, 0.046, 0.046, 0.430, 0.0))
    fr = _boxes("WingTrolley_Frame", frame, coll)
    C.add_bevel(fr, width=0.005, segments=2)
    C.assign(fr, _mat("PropAluSatin"))
    made.append(fr)

    # Foam cradles shaped to a wing that is not there.
    cradles = []
    for sx in (-0.40, 0.40):
        cradles.append((sx, -0.14, 0.625, 0.180, 0.130, 0.082, 0.0))
        cradles.append((sx, 0.16, 0.640, 0.180, 0.110, 0.112, 0.0))
    cr = _boxes("WingTrolley_Cradles", cradles, coll)
    C.add_bevel(cr, width=0.016, segments=2)
    C.assign(cr, _mat("PropFoam"))
    made.append(cr)

    handle = CAR.tube("WingTrolley_Handle", [
        (-0.60, -0.34, 0.585), (-0.72, -0.34, 0.700), (-0.76, -0.34, 0.860),
        (-0.76, 0.0, 0.905), (-0.76, 0.34, 0.860), (-0.72, 0.34, 0.700),
        (-0.60, 0.34, 0.585)], 0.019, coll, segments=8)
    C.assign(handle, _mat("PropChrome"))
    made.append(handle)

    made += _castors("WingTrolley", (0.0, 0.0, 0.0), 0.545, 0.320, coll)
    _transform_group(made, (x, y, 0.0), (0.0, 0.0, rot))
    return made


def build_flight_cases(x, y, coll, rot=0.0):
    """The replacement for PitCase_A/_B.

    The originals were 6-poly boxes at 0.028 albedo, parked at (-6.05, 4.85) and
    (-7.25, 4.35) where they projected inside the car's screen box and behind it
    - invisible twice over. Rebuilt as real cases with corner castings, latches
    and castors, and moved into corridor A where the front cameras see them.
    """
    made = []
    dark, alu = _mat("PropCase"), _mat("PropAluSatin")
    stack = [(0.92, 0.60, 0.54, 0.10), (0.78, 0.52, 0.40, 0.66)]
    for k, (w, d, h, z) in enumerate(stack):
        body = _slab(f"FlightCase{k}_Body", (0.0, 0.0, z + h * 0.5), (w, d, h), coll)
        C.add_bevel(body, width=0.010, segments=2)
        C.assign(body, dark)
        made.append(body)

        # Extrusion channel round every edge plus corner castings: the profile
        # that makes a flight case read as one at 15 m instead of as a crate.
        rails, corners = [], []
        for sz in (z + 0.012, z + h - 0.012):
            rails.append((0.0, 0.0, sz, w + 0.014, d + 0.014, 0.024, 0.0))
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (z + 0.030, z + h - 0.030):
                    corners.append((sx * w * 0.5, sy * d * 0.5, sz,
                                    0.070, 0.070, 0.070, 0.0))
        rl = _boxes(f"FlightCase{k}_Rails", rails, coll)
        C.add_bevel(rl, width=0.004, segments=2)
        C.assign(rl, alu)
        made.append(rl)
        cn = _boxes(f"FlightCase{k}_Corners", corners, coll)
        C.add_bevel(cn, width=0.009, segments=2)
        C.assign(cn, alu)
        made.append(cn)

        latches = []
        for sx in (-w * 0.28, w * 0.28):
            latches.append((sx, -d * 0.5 - 0.014, z + h * 0.46, 0.090, 0.030, 0.062, 0.0))
        lt = _boxes(f"FlightCase{k}_Latches", latches, coll)
        C.add_bevel(lt, width=0.005, segments=2)
        C.assign(lt, _mat("PropChrome"))
        made.append(lt)

    stencil = text_mesh("FlightCase_Stencil", f"{MARQUE}  02", 0.062, coll,
                        extrude=0.002, res=3, spacing=1.20, fit_width=0.52,
                        mat=_mat("PropAluBright"))
    stencil.rotation_euler = PANEL_TEXT_ROT
    stencil.location = (0.0, -0.316, 0.86)
    made.append(stencil)

    made += _castors("FlightCase", (0.0, 0.0, 0.0), 0.36, 0.22, coll)
    _transform_group(made, (x, y, 0.0), (0.0, 0.0, rot))
    return made


def build_pit_kit(coll):
    """Corridor A, on the public side of the barrier.

    The first layout put the trolley at (-6.05, -1.00) and the gun rack at
    (-6.60, -0.40), radius 6.13 and 6.61, which is INSIDE the r = 6.95 barrier
    ring - service kit standing in the exhibit with the car - and the rail chord
    between the posts at (-5.80, -3.84) and (-6.81, 1.38) passed straight through
    the gun rack at 1.32 m tall. The chord's closest approach to the origin is
    6.421 m, so everything here is at r >= 7.5 and clears it and the posts.

    The other constraint is s05's bollards, which are 0.15 m emissive annuli on
    the same ring; the nearest one to this cluster is at (-6.81, 1.38) and the
    closest prop keeps 0.89 m from it.

    Gridding the pocket showed corridor A projects to a horizontal band at
    FrontQuarter frame y 0.48-0.70 for every position in it, and that frame x is
    driven almost entirely by world y: y = -0.4 lands at x 0.00-0.13 and y = +2.4
    at x 0.21-0.35. Items are spread across that range so the cluster reads in
    depth instead of as a row, and nothing sits below y = -0.4 where it would
    start bleeding off the left edge.

    No refuelling rig. Refuelling has been banned since 2010 and it is the one
    prop an F1 audience would read as wrong; the period-correct kit is guns, air,
    tools and trolleys.
    """
    made = []
    made += build_wing_trolley(-7.50, -0.35, coll, rot=math.radians(-14.0))
    made += build_wheel_gun_rack(-8.35, 0.50, coll, rot=math.radians(24.0))
    made += build_hose_reel(-7.70, 1.45, coll, rot=math.radians(-8.0))
    made += build_tool_chest(-9.30, 1.35, coll, rot=math.radians(16.0))
    made += build_flight_cases(-9.40, 0.05, coll, rot=math.radians(-6.0))
    return made


# --------------------------------------------------------------------------- #
# 5. tyre bay  (corridor B)
# --------------------------------------------------------------------------- #

def build_tyre_stack(name, x, y, count, coll, hw=CAR.REAR_HW, rot=0.0):
    """Stack of spare slicks - the same profile as the car's, so they match."""
    made = []
    for i in range(count):
        t = C.revolve(f"{name}_T{i}", CAR.tyre_profile(hw), segments=64,
                      coll=coll, auto_smooth=34.0)
        t.location = (x, y, 2 * hw * i + hw + 0.002)
        t.rotation_euler = (0.0, 0.0, rot + i * 0.7)
        C.assign(t, bpy.data.materials["TyreRubber"])
        made.append(t)

        # rim visible through the bore
        r = C.revolve(f"{name}_R{i}", CAR.rim_profile(hw), segments=48,
                      coll=coll, auto_smooth=30.0)
        r.location = t.location
        r.rotation_euler = t.rotation_euler
        C.assign(r, bpy.data.materials["WheelRim"])
        made.append(r)
    return made


def build_tyre_bay(coll, x=-9.50, y=2.50, count=4, hw=CAR.REAR_HW):
    """Relocated stack with blankets, straps and a controller.

    D-class placement failure: the old pair sat at (-6.35, -4.55) and
    (-7.10, -4.10), which is 14,448 polys - 53 % of the whole showroom - that no
    delivered frame ever contained a pixel of. Front quarter put them at frame
    x -0.375 and -0.321, rear quarter at +1.75 and +1.94, both off the ends of
    the frame. TyreStackB is deleted outright and TyreStackA moves here:
    FrontQuarter (0.18-0.27, 0.56-0.79) at 17.2-18.6 m, above the car's 0.690,
    HeroLow (0.25-0.33, 0.46-0.66). Corridor B, blocking nothing.
    """
    made = build_tyre_stack("TyreStackA", x, y, count, coll, hw=hw)
    fabric, strap = _mat("PropFabric"), _mat("PropStrap")

    # Blankets on the top three only: the bottom casing in a stack is the one
    # that is not going on the car next, and leaving it bare says so.
    for i in range(max(0, count - 3), count):
        zc = 2 * hw * i + hw + 0.002
        sleeve = C.revolve(f"TyreBlanket_{i}", [
            (0.372, -hw + 0.012), (0.376, -hw + 0.030), (0.376, hw - 0.030),
            (0.372, hw - 0.012), (0.366, hw - 0.006), (0.366, -hw + 0.006),
            (0.372, -hw + 0.012)],
            segments=48, coll=coll, auto_smooth=44.0)
        sleeve.location = (x, y, zc)
        C.assign(sleeve, fabric)
        made.append(sleeve)

        band = _ring(f"TyreStrap_{i}", 0.377, 0.383, zc - 0.030, zc + 0.030,
                     coll, segments=40)
        band.location = (x, y, 0.0)
        C.assign(band, strap)
        made.append(band)

        a = 0.55 + 0.9 * i
        buckle = _slab(f"TyreBuckle_{i}", (x + 0.386 * math.cos(a),
                                           y + 0.386 * math.sin(a), zc),
                       (0.070, 0.048, 0.086), coll, rot_z=a)
        C.add_bevel(buckle, width=0.006, segments=2)
        C.assign(buckle, _mat("PropChrome"))
        made.append(buckle)

    # Controller on the far side of the stack: the near side is 0.25 m from the
    # pit board's pole and 0.41 m from the tool chest.
    cx, cy = x - 0.70, y + 0.35
    ctrl = _slab("TyreCtrl_Body", (cx, cy, 0.170), (0.320, 0.240, 0.340),
                 coll, rot_z=0.5)
    C.add_bevel(ctrl, width=0.010, segments=2)
    C.assign(ctrl, _mat("PropCase"))
    made.append(ctrl)
    face = _slab("TyreCtrl_Face", (cx, cy, 0.260), (0.190, 0.255, 0.120),
                 coll, rot_z=0.5)
    C.assign(face, _mat("PropSignFace"))
    made.append(face)

    lead = CAR.tube("TyreCtrl_Lead", [
        (cx + 0.12, cy - 0.10, 0.060), (cx + 0.30, cy - 0.26, 0.030),
        (cx + 0.58, cy - 0.30, 0.028), (cx + 0.76, cy - 0.14, 0.030),
        (cx + 0.74, cy + 0.10, 0.032), (cx + 0.58, cy + 0.18, 0.120),
        (cx + 0.42, cy + 0.10, 0.330)], 0.014, coll, segments=8)
    C.assign(lead, _mat("PropRubber"))
    made.append(lead)
    return made


# --------------------------------------------------------------------------- #
# 6. signage
# --------------------------------------------------------------------------- #

def build_spec_plaque(coll, x=-0.60, y=-5.60):
    """Spec plaque with real extruded type.

    D114 (real culprit): this sat at (4.35, -3.35) - azimuth -37.6 deg, the
    front-quarter camera's sightline to within half a degree, so it speared the
    car in frame. The fix then overshot: at (1.90, -5.95) it left the front
    quarter AND HeroLow frames entirely, the two cameras it was moved to protect,
    and only survived in the rear quarter as a blank grey card.

    The design brief proposed (3.2, -4.6), which is inside the brief's own
    keepout - x +1..+6, y -1..-5 at under 5.9 m from the front-quarter lens - and
    probing put it at frame x 0.015, fifteen thousandths from spearing the hero
    shot again. Measured alternatives instead:

        (+1.90, -5.95)  RQ x[0.719,0.797] behind the car, 13.8 m   (today)
        (+3.20, -4.60)  FQ x max +0.015 at 3.2 m - the D114 trap
        (-0.20, -5.30)  RQ interleaved with the car in depth
        (-0.60, -5.60)  RQ x[0.893,0.988] CLEAR of the car, 11.7 m  <- chosen

    (-0.60, -5.60) is 4.93 m off the front-quarter axis against a 2.24 m frame
    half-width and 5.16 m off HeroLow's against 1.17 m, so both front frames miss
    it by more than a frame width, and it is 18 % larger in the rear quarter than
    the position it replaces.
    """
    made = []
    chrome = _mat("PropChrome")
    stem = C.revolve("Plaque_Stem", [
        (0.000, 0.000), (0.140, 0.000), (0.146, 0.014), (0.030, 0.030),
        (0.022, 0.030), (0.022, 0.860), (0.000, 0.870)],
        segments=24, coll=coll, auto_smooth=30.0)
    C.assign(stem, chrome)
    made.append(stem)

    panel = _slab("Plaque_Panel", (0.0, 0.0, 0.0), (0.540, 0.024, 0.360), coll)
    C.add_bevel(panel, width=0.008, segments=2)
    C.assign(panel, _mat("PlaqueFace"))
    surround = _slab("Plaque_Surround", (0.0, 0.006, 0.0),
                     (0.576, 0.014, 0.396), coll)
    C.add_bevel(surround, width=0.006, segments=2)
    C.assign(surround, _mat("PropAluSatin"))

    title = text_mesh("Plaque_Title", f"{MARQUE} {MODEL}", 0.060, coll,
                      extrude=0.004, res=4, spacing=1.14, fit_width=0.430,
                      mat=_mat("PropAluBright"))
    rule = _slab("Plaque_Rule", (0.0, -0.014, 0.028), (0.430, 0.006, 0.004), coll)
    C.assign(rule, _mat("PropAluBright"))
    line1 = text_mesh("Plaque_Line1", "V6 TURBO HYBRID  1.6 L  15000 RPM",
                      0.028, coll, extrude=0.002, res=3, spacing=1.16,
                      fit_width=0.430, mat=_mat("PropAluBright"))
    line2 = text_mesh("Plaque_Line2", "798 KG  3600 MM WHEELBASE  2024 SPEC",
                      0.028, coll, extrude=0.002, res=3, spacing=1.16,
                      fit_width=0.430, mat=_mat("PropAluBright"))

    for ob, (u, w) in ((title, (0.0, 0.084)), (line1, (0.0, -0.020)),
                       (line2, (0.0, -0.070))):
        ob.rotation_euler = PANEL_TEXT_ROT
        ob.location = (u, -0.016, w)
    made += [panel, surround, rule, title, line1, line2]

    # Everything above the stem is built flat at the origin, tilted back 24 deg
    # and then aimed at the rear-quarter lens as one body.
    head = [panel, surround, rule, title, line1, line2]
    _transform_group(head, (0.0, 0.0, 0.845), (math.radians(-24.0), 0.0, 0.0))
    _transform_group(made, (x, y, 0.0),
                     (0.0, 0.0, _face_azimuth((x, y), (-7.10, 5.55))))
    return made


def build_pit_board(coll, x=-8.60, y=2.15):
    """Hanging pit board on a pole, aimed at the front-quarter lens.

    Moved off (-7.10, 1.35), which was 0.29 m from the bollard s05 puts at
    (-6.81, 1.38) - the pole was standing in the middle of a lit annulus. Here it
    is 1.98 m clear of that bollard and at r = 8.86, outside the barrier, and it
    is the tallest thing in corridor A so it takes the right-hand end of the
    cluster at FrontQuarter frame x ~0.19-0.28, where the pocket grid puts
    world y +2.15.
    """
    made = []
    pole = C.revolve("PitBoard_Pole", [
        (0.000, 0.000), (0.165, 0.000), (0.170, 0.016), (0.036, 0.034),
        (0.026, 0.034), (0.026, 2.240), (0.000, 2.252)],
        segments=22, coll=coll, auto_smooth=30.0)
    C.assign(pole, _mat("PropChrome"))
    made.append(pole)

    # Pole sits at the group origin and the board's readable face points local
    # -Y, so the whole head has to move NEGATIVE in y to put the pole behind it.
    # Offsetting +0.045 was tried first and does the opposite - it leaves the
    # chrome column standing in front of the text, straight down the middle.
    board = _slab("PitBoard_Face", (0.0, -0.045, 0.0), (0.700, 0.030, 0.940), coll)
    C.add_bevel(board, width=0.008, segments=2)
    C.assign(board, _mat("PropSignFace"))
    edge = _slab("PitBoard_Edge", (0.0, -0.037, 0.0), (0.736, 0.016, 0.976), coll)
    C.add_bevel(edge, width=0.006, segments=2)
    C.assign(edge, _mat("PropAluSatin"))
    made += [board, edge]

    # A real board is a car number and a gap, in that order of size.
    rows = [("PitBoard_Num", "24", 0.240, 0.300, 0.300),
            ("PitBoard_Pos", "P1", 0.130, 0.230, 0.052),
            ("PitBoard_Gap", "+1.284", 0.100, 0.440, -0.130),
            ("PitBoard_Lap", "L 41 / 57", 0.075, 0.480, -0.300)]
    for name, body, size, width, w in rows:
        t = text_mesh(name, body, size, coll, extrude=0.003, res=4,
                      spacing=1.15, fit_width=width, mat=_mat("PropAluBright"))
        t.rotation_euler = PANEL_TEXT_ROT
        t.location = (0.0, -0.065, w)
        made.append(t)

    head = [ob for ob in made if ob is not pole]
    _transform_group(head, (0.0, 0.0, 1.760))
    _transform_group(made, (x, y, 0.0),
                     (0.0, 0.0, _face_azimuth((x, y), (7.05, -5.35))))
    return made


# --------------------------------------------------------------------------- #
# 7. side-wall timing rail - NOT BUILT
# --------------------------------------------------------------------------- #
#
# The brief's proposal 7 put eight trackside monitors on the +Y wall at
# z 2.25-2.85, aimed at the dead upper-RIGHT quadrant of the hero frame. It was
# already the highest-risk item in the set for one reason - 1.5 % of frame in
# emitters - and it is now unbuildable for a better one: s05 runs its
# illuminated reveal along that wall at z 2.44, dead centre of where the rail
# would hang. A bezel 60 mm proud of the wall across x -12..-5 would cover seven
# metres of the line that s05 measured as the single biggest change in the
# scheme, converging one degree off frame centre behind the car.
#
# Covering another module's best element to fill dead frame is a bad trade, and
# I cannot render to check the emissive cost either - the Integrate agent renders
# once, for everyone. Both reasons point the same way, so it is not built. If the
# upper-right quadrant still reads as empty after s05's line lands, the cheap
# non-emissive answer is to raise the rail above z 3.2, clear of the line, and
# measure it then.


# --------------------------------------------------------------------------- #
# 8. barrier
# --------------------------------------------------------------------------- #

BARRIER_R = 6.95
BARRIER_N = 8
BARRIER_OFFSET = math.radians(-11.5)
RAIL_TOP = 0.785
# Gate spans are indexed by the post the span starts at, going anticlockwise.
GATE_SPANS = (7, 3)


def build_barrier(coll, radius=BARRIER_R, count=BARRIER_N, height=0.86):
    """Cast base plates, tapered posts and a flat machined top rail.

    THE RING GEOMETRY IS NOT NEGOTIABLE and is carried over unchanged. D114: at
    r=5.15 a post landed on the front-quarter sightline (azimuth -37 deg) and
    speared the car. Camera azimuths are front quarter -37.2, hero -31.2, rear
    quarter +142.0; with 8 posts at 45 deg the -11.5 deg ring offset puts posts
    at -11.5/-56.5 - a gap centred -34, covering both front cameras - and at
    123.5/168.5, a gap centred +146 for the rear quarter. Moving the ring out
    alone never helped: the post has to miss the sightline, not just be far away.

    Those two gaps become explicit walk-in gates, which also deletes the two rail
    spans that crossed nearest to the front and rear lenses.

    The rope this replaces swept z 0.670-0.785 (0.115 m of catenary sag below a
    0.785 m attachment). The new rail occupies z 0.759-0.785, a strict subset, so
    on the far arc - which does cross the car's screen box in both front cameras,
    at FrontQuarter (0.36-0.55, 0.52-0.68) - it can only occlude less than what
    is there today. That is why it is a flat bar and not the glass balustrade the
    brief floated: glass would cut a translucent band clean across the HeroLow
    frame at the car's mid-height.

    THE POST BASE BELOW z = 0.030 IS ALSO NOT NEGOTIABLE, and that is new. s05
    now rings every post with an emissive annulus from r 0.108 to 0.150 at
    z = 0.026 and says so in its own docstring: "the post profile is 0.108 m at
    z = 0.026, so the ring starts exactly at the post's flare. s07 is left
    alone." The cast base plates this function first grew - 0.190 m across and
    0.030 tall - swallowed that annulus whole on all eight posts and would have
    silently deleted a fixture s05 measured at 0.153 % -> 0.062 % clipped. The
    original flare is kept to the millimetre and the redesign happens above it.
    """
    made = []
    steel = _mat("PropChrome")
    rail_mat = _mat("PropAluSatin")

    centres = []
    for i in range(count):
        a = C.TAU * i / count + BARRIER_OFFSET
        cx, cy = radius * math.cos(a), radius * math.sin(a)
        centres.append((cx, cy))
        gate = (i in GATE_SPANS or (i - 1) % count in GATE_SPANS)

        # Gate posts are heavier above the flare and carry a machined cap, so
        # the two openings read as designed entrances rather than as missing
        # hardware. The first four profile points are s05's contract.
        r_base, r_top = (0.038, 0.030) if gate else (0.030, 0.021)
        top = height + (0.055 if gate else 0.0)
        post = C.revolve(f"Barrier_Post_{i}", [
            (0.000, 0.000), (0.105, 0.000), (0.112, 0.012), (0.108, 0.026),
            (r_base, 0.048), (r_base, 0.070), (r_top, top - 0.090),
            (r_top + 0.014, top - 0.070), (r_top + 0.014, top - 0.026),
            (r_top + 0.005, top - 0.010), (0.000, top)],
            segments=28, coll=coll, auto_smooth=30.0)
        post.location = (cx, cy, 0.0)
        C.assign(post, steel)
        made.append(post)

    # Top rail: a swept section, not a box. The two shallow grooves in the top
    # face are the laser-cut brand fret reduced to something that cannot grow the
    # silhouette - removed material, and two specular lines along every span.
    section = [(-0.045, 0.000), (-0.045, 0.020), (-0.038, 0.026),
               (-0.030, 0.026), (-0.030, 0.021), (-0.022, 0.021),
               (-0.022, 0.026), (0.022, 0.026), (0.022, 0.021),
               (0.030, 0.021), (0.030, 0.026), (0.038, 0.026),
               (0.045, 0.020), (0.045, 0.000)]
    for i in range(count):
        if i in GATE_SPANS:
            continue
        x0, y0 = centres[i]
        x1, y1 = centres[(i + 1) % count]
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        ux, uy = dx / length, dy / length
        nx, ny = -uy, ux
        rings = []
        for t in (0.0, 1.0):
            px, py = x0 + dx * t, y0 + dy * t
            ring = [(px + nx * u, py + ny * u, RAIL_TOP - 0.026 + v)
                    for u, v in section]
            ring += [(px + nx * u, py + ny * u, RAIL_TOP - 0.026 - v * 0.62)
                     for u, v in reversed(section[1:-1])]
            rings.append(ring)
        verts, faces = C.loft(rings, closed=True, cap_start=True, cap_end=True)
        rail = C.new_obj(f"Barrier_Rail_{i}", verts, faces, coll=coll,
                         smooth=True, auto_smooth=34.0)
        C.assign(rail, rail_mat)
        made.append(rail)
    return made


# --------------------------------------------------------------------------- #
# 9. rear-quarter vitrine  (corridor D)
# --------------------------------------------------------------------------- #

def build_vitrine(coll, x=13.20, y=-4.20):
    """Component case behind the front lenses.

    Corridor D is the only part of the room that is structurally incapable of
    blocking the hero shot. Measured at this position the whole case is 2.52 m
    BEHIND the front-quarter lens plane and 7.24 m behind HeroLow's, while
    landing at RearQuarter x[0.111, 0.239] y[0.620, 0.751] at 20.3-23.2 m. The
    brief's (10.6, -1.2) has corners 1.19 m in FRONT of the front-quarter lens
    and (11.6, -1.6) has them 0.16 m in front; both are one edit from a speared
    frame, which is exactly the failure this corridor exists to make impossible.

    Contents are new simple geometry, not copies of car parts - a display case
    holding a second copy of something already on the car reads as a duplicate.
    Body albedo is deliberately mid-grey: the rear quarter is the one frame near
    its crush ceiling (0.360 % of 0.500 %), so dark objects there cost from the
    other direction.
    """
    made = []
    alu, bright = _mat("PropAluSatin"), _mat("PropAluBright")
    w, d, hp = 2.40, 0.90, 0.62

    plinth = _slab("Vitrine_Plinth", (0.0, 0.0, hp * 0.5), (w, d, hp), coll)
    C.add_bevel(plinth, width=0.010, segments=2)
    C.assign(plinth, _mat("PropSteelDark"))
    made.append(plinth)
    cap = _slab("Vitrine_Cap", (0.0, 0.0, hp + 0.018), (w + 0.040, d + 0.040, 0.036), coll)
    C.add_bevel(cap, width=0.008, segments=2)
    C.assign(cap, alu)
    made.append(cap)

    gw, gd, gh = w - 0.12, d - 0.12, 0.44
    z0 = hp + 0.036
    posts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            posts.append((sx * gw * 0.5, sy * gd * 0.5, z0 + gh * 0.5,
                          0.030, 0.030, gh, 0.0))
    ps = _boxes("Vitrine_Posts", posts, coll)
    C.add_bevel(ps, width=0.004, segments=2)
    C.assign(ps, alu)
    made.append(ps)

    # Thin-wall glass, like GlassPanel and DisplayGlass: transmission bounces are
    # capped at 32 and a solid pane would spend them on a slab nobody can see
    # into.
    panes = []
    for sy in (-1, 1):
        panes.append([(-gw * 0.5, sy * gd * 0.5, z0), (gw * 0.5, sy * gd * 0.5, z0),
                      (gw * 0.5, sy * gd * 0.5, z0 + gh), (-gw * 0.5, sy * gd * 0.5, z0 + gh)])
    for sx in (-1, 1):
        panes.append([(sx * gw * 0.5, -gd * 0.5, z0), (sx * gw * 0.5, gd * 0.5, z0),
                      (sx * gw * 0.5, gd * 0.5, z0 + gh), (sx * gw * 0.5, -gd * 0.5, z0 + gh)])
    panes.append([(-gw * 0.5, -gd * 0.5, z0 + gh), (gw * 0.5, -gd * 0.5, z0 + gh),
                  (gw * 0.5, gd * 0.5, z0 + gh), (-gw * 0.5, gd * 0.5, z0 + gh)])
    for i, quad in enumerate(panes):
        g = C.new_obj(f"Vitrine_Glass_{i}", quad, [(0, 1, 2, 3)], coll=coll,
                      smooth=False)
        C.assign(g, _mat("PropCaseGlass"))
        made.append(g)

    def stand(tag, sx, top):
        s = C.revolve(f"Vitrine_Stand{tag}", [
            (0.000, 0.000), (0.085, 0.000), (0.090, 0.008), (0.030, 0.018),
            (0.024, 0.024), (0.024, top - 0.014), (0.034, top - 0.006),
            (0.034, top), (0.000, top)],
            segments=20, coll=coll, auto_smooth=32.0)
        s.location = (sx, 0.0, z0)
        C.assign(s, bright)
        return s

    # brake disc and bell
    made.append(stand("A", -0.78, 0.120))
    disc = C.revolve("Vitrine_Disc", [
        (0.062, -0.016), (0.140, -0.016), (0.140, 0.016), (0.062, 0.016),
        (0.062, -0.016)], segments=40, coll=coll, auto_smooth=34.0)
    disc.rotation_euler = (math.radians(74.0), 0.0, 0.5)
    disc.location = (-0.78, 0.0, z0 + 0.268)
    C.assign(disc, bpy.data.materials.get("CarbonCeramic") or _mat("PropSteelDark"))
    made.append(disc)
    bell = C.revolve("Vitrine_Bell", [
        (0.000, 0.020), (0.058, 0.020), (0.062, 0.006), (0.062, -0.038),
        (0.052, -0.046), (0.000, -0.046), (0.000, 0.020)],
        segments=28, coll=coll, auto_smooth=34.0)
    bell.rotation_euler = disc.rotation_euler
    bell.location = disc.location
    C.assign(bell, bright)
    made.append(bell)

    # gear cluster
    made.append(stand("B", 0.02, 0.100))
    teeth = []
    for k, (r, hh, zc) in enumerate(((0.092, 0.020, 0.128), (0.070, 0.018, 0.168),
                                     (0.054, 0.016, 0.202))):
        gear = C.revolve(f"Vitrine_Gear{k}", [
            (0.018, -hh), (r - 0.010, -hh), (r - 0.010, hh), (0.018, hh),
            (0.018, -hh)], segments=32, coll=coll, auto_smooth=34.0)
        gear.location = (0.02, 0.0, z0 + zc)
        C.assign(gear, bright)
        made.append(gear)
        n = 22 - 4 * k
        for i in range(n):
            a = C.TAU * i / n
            teeth.append((0.02 + (r - 0.004) * math.cos(a),
                          (r - 0.004) * math.sin(a), z0 + zc,
                          0.016, 0.009, hh * 1.8, a))
    tt = _boxes("Vitrine_GearTeeth", teeth, coll)
    C.assign(tt, bright)
    made.append(tt)
    shaft = C.revolve("Vitrine_Shaft", [
        (0.000, 0.100), (0.018, 0.100), (0.018, 0.235), (0.000, 0.235)],
        segments=16, coll=coll, auto_smooth=30.0)
    shaft.location = (0.02, 0.0, z0)
    C.assign(shaft, _mat("PropChrome"))
    made.append(shaft)

    # wishbone section
    made.append(stand("C", 0.82, 0.090))
    apex = (0.82, 0.030, z0 + 0.300)
    for k, tip in enumerate(((0.60, -0.180, z0 + 0.130), (1.02, -0.170, z0 + 0.140),
                             (0.82, 0.230, z0 + 0.115))):
        leg = CAR.tube(f"Vitrine_Wishbone{k}",
                       [apex, tuple(C.lerp(apex[j], tip[j], 0.5) for j in range(3)),
                        tip], 0.017, coll, segments=10)
        C.assign(leg, bpy.data.materials.get("CarbonFibre") or _mat("PropSteelDark"))
        made.append(leg)
        rod = C.revolve(f"Vitrine_RodEnd{k}", [
            (0.000, -0.018), (0.026, -0.018), (0.030, -0.008), (0.030, 0.008),
            (0.026, 0.018), (0.000, 0.018), (0.000, -0.018)],
            segments=16, coll=coll, auto_smooth=34.0)
        rod.location = tip
        C.assign(rod, _mat("PropChrome"))
        made.append(rod)

    caption = text_mesh("Vitrine_Caption", "SYSTEMS  BRAKE  GEARBOX  SUSPENSION",
                        0.040, coll, extrude=0.002, res=3, spacing=1.16,
                        fit_width=1.60, mat=bright)
    caption.rotation_euler = PANEL_TEXT_ROT
    caption.location = (0.0, -d * 0.5 - 0.012, hp - 0.140)
    made.append(caption)

    _transform_group(made, (x, y, 0.0),
                     (0.0, 0.0, _face_azimuth((x, y), (-7.10, 5.55))))
    return made


# --------------------------------------------------------------------------- #
# 10. back-left gantry  (corridor B)
# --------------------------------------------------------------------------- #

def build_gantry(coll, y=7.60, x_wall=FLUTE_FACE_X + 0.05, x_free=-10.40,
                 z0=3.15, z1=3.70):
    """Pit-lane sign gantry across the back-left corner.

    A ceiling truss is rejected by measurement: (-10, 0, 5.40) projects to
    FrontQuarter frame y 1.324 and HeroLow 1.150, above every frame. Nothing over
    about z 3.6 near the room centre is visible to the hero camera at all, which
    is why this is a gantry at 3.15-3.70 and not a truss at 5.4. Measured here:
    FrontQuarter x[0.13, 0.49] y[0.94, 1.04] - the top 6 % band - and HeroLow
    x[0.24, 0.54] y[0.74, 0.86].

    y = +7.60 puts it directly under s05's ceiling cove run, so it is lit from
    above and throws its shadow straight down onto the floor instead of across
    the wall wordmark at y +4.10..+6.70. That is the whole reason for this y and
    not the brief's.

    x_wall tracks s02's fluting face rather than the structural wall: the fins
    project 100 mm past a 40 mm standoff, so a bracket keyed to x = -15 buried
    itself 90 mm inside the panelling.
    """
    made = []
    alu = _mat("PropAluSatin")
    length = x_free - x_wall
    chords, lattice = [], []
    for sy in (-0.30, 0.30):
        for z in (z0 + 0.05, z1 - 0.05):
            chords.append(((x_wall + x_free) * 0.5, y + sy, z,
                           length, 0.070, 0.070, 0.0))
    n = 9
    for i in range(n):
        px = x_wall + length * (i + 0.5) / n
        lattice.append((px, y, (z0 + z1) * 0.5, 0.046, 0.560, 0.046, 0.0))
    ch = _boxes("Gantry_Chords", chords, coll)
    C.add_bevel(ch, width=0.006, segments=2)
    C.assign(ch, alu)
    made.append(ch)
    la = _boxes("Gantry_Lattice", lattice, coll)
    C.assign(la, alu)
    made.append(la)

    # Zig-zag web between the chords, as tubes between the real chord nodes.
    # These were boxes rotated -42 deg about Y, which rotates about the OBJECT
    # ORIGIN - the world origin, 12 m away - and flung the whole web across the
    # frame: the audit caught it as a gantry spanning frame y 0.001 to 0.999.
    # Building the members between their endpoints cannot go wrong that way.
    zt, zb = z1 - 0.05, z0 + 0.05
    for sy in (-0.30, 0.30):
        for i in range(n):
            xa = x_wall + length * i / n
            xb = x_wall + length * (i + 1) / n
            za, zb2 = (zb, zt) if i % 2 else (zt, zb)
            web = CAR.tube(f"Gantry_Web_{'A' if sy < 0 else 'B'}{i}",
                           [(xa, y + sy, za), (xb, y + sy, zb2)],
                           0.020, coll, segments=8)
            C.assign(web, alu)
            made.append(web)

    leg = _boxes("Gantry_Leg", [
        (x_free, y, (z0 - 0.10) * 0.5, 0.150, 0.150, z0 - 0.10, 0.0),
        (x_free, y, 0.025, 0.520, 0.520, 0.050, 0.0),
        (x_free, y, z0 - 0.06, 0.320, 0.740, 0.070, 0.0)], coll)
    C.add_bevel(leg, width=0.008, segments=2)
    C.assign(leg, alu)
    made.append(leg)

    bracket = _boxes("Gantry_Bracket", [
        (x_wall - 0.06, y, (z0 + z1) * 0.5, 0.120, 0.820, (z1 - z0) + 0.16, 0.0)],
        coll)
    C.add_bevel(bracket, width=0.006, segments=2)
    C.assign(bracket, _mat("PropSteelDark"))
    made.append(bracket)

    # Hanging bay panels, clear of the wall wordmark at y +4.10..+6.70.
    for i, body in enumerate(("PIT", "01", "OUT")):
        px = x_wall + length * (0.24 + 0.26 * i)
        panel = _slab(f"Gantry_Panel_{i}", (px, y, 2.90), (0.560, 0.028, 0.400), coll)
        C.add_bevel(panel, width=0.008, segments=2)
        C.assign(panel, _mat("PropSignFace"))
        made.append(panel)
        hang = _boxes(f"Gantry_Hang_{i}", [
            (px - 0.20, y, 3.06, 0.024, 0.024, 0.180, 0.0),
            (px + 0.20, y, 3.06, 0.024, 0.024, 0.180, 0.0)], coll)
        C.assign(hang, _mat("PropChrome"))
        made.append(hang)
        # fit_width forces every string to the SAME WIDTH, so a 3-glyph "PIT",
        # a 2-glyph "01" and a 3-glyph "OUT" ended up at cap heights of 0.190,
        # 0.329 and 0.125 m on panels hanging side by side. Drop fit_width and
        # let a common `size` set a common cap height instead; the panel is
        # 0.560 wide and the longest string at 0.150 is comfortably inside it.
        t = text_mesh(f"Gantry_Text_{i}", body, 0.150, coll, extrude=0.004,
                      res=4, spacing=1.16, mat=_mat("PropAluBright"))
        t.rotation_euler = PANEL_TEXT_ROT
        t.location = (px, y - 0.020, 2.90)
        made.append(t)
    return made


# --------------------------------------------------------------------------- #
# 11. exterior forecourt  (outside the shell, rear quarter only)
# --------------------------------------------------------------------------- #

def build_forecourt(coll):
    """A lit apron beyond the curtain wall.

    Physically incapable of blocking anything: it is outside the building, and it
    is behind both front lenses (-12 to -22 m). It shows only in the rear
    quarter, at frame x 0.23-0.71, y 0.69-0.74 for the apron and x ~0.42,
    y 0.71-1.10 for the poles at 35 m.

    It is also the cheapest available fix for that frame's crush. RearQuarter is
    at 0.360 % crushed against a 0.500 % ceiling and the band it fills is
    currently ExteriorGround at 0.020 albedo, which is dark enough to read as
    crushed black. Replacing it with 0.28 concrete raises that band by a factor
    of fourteen without adding a single lumen to the room.
    """
    made = []
    apron = _slab("Forecourt_Apron", (22.70, -18.70, 0.070), (15.40, 14.60, 0.140), coll)
    C.assign(apron, _mat("PropConcrete"))
    made.append(apron)

    # Kerb defining a drop-off lane, plus expansion joints so 15 m of concrete
    # does not read as one poured slab.
    joints = []
    for i in range(6):
        joints.append((16.20 + i * 2.50, -18.70, 0.142, 0.040, 14.60, 0.006, 0.0))
    for i in range(5):
        joints.append((22.70, -24.60 + i * 2.70, 0.142, 15.40, 0.040, 0.006, 0.0))
    jt = _boxes("Forecourt_Joints", joints, coll)
    C.assign(jt, _mat("PropSteelDark"))
    made.append(jt)

    kerb = _boxes("Forecourt_Kerb", [
        (24.60, -18.70, 0.220, 0.320, 14.60, 0.160, 0.0),
        (22.70, -25.60, 0.220, 15.40, 0.320, 0.160, 0.0)], coll)
    C.add_bevel(kerb, width=0.020, segments=2)
    C.assign(kerb, _mat("PropKerb"))
    made.append(kerb)

    for i, (px, py) in enumerate(((22.00, -16.00), (25.50, -20.50), (18.50, -12.80))):
        pole = C.revolve(f"Forecourt_Pole_{i}", [
            (0.000, 0.140), (0.220, 0.140), (0.230, 0.170), (0.085, 0.210),
            (0.062, 0.240), (0.052, 3.360), (0.062, 3.400), (0.000, 3.420)],
            segments=18, coll=coll, auto_smooth=30.0)
        pole.location = (px, py, 0.0)
        C.assign(pole, _mat("PropAluSatin"))
        made.append(pole)
        shroud = _slab(f"Forecourt_Head_{i}", (px, py, 3.470),
                       (0.420, 0.300, 0.110), coll)
        C.add_bevel(shroud, width=0.014, segments=2)
        C.assign(shroud, _mat("PropAluSatin"))
        made.append(shroud)
        lamp = C.new_obj(f"Forecourt_Lamp_{i}",
                         [(px - 0.18, py - 0.12, 3.414), (px + 0.18, py - 0.12, 3.414),
                          (px + 0.18, py + 0.12, 3.414), (px - 0.18, py + 0.12, 3.414)],
                         [(0, 1, 2, 3)], coll=coll, smooth=False)
        C.assign(lamp, _pole_emit())
        lamp.visible_shadow = False
        made.append(lamp)

    planters, foliage = [], []
    for i in range(4):
        py = -22.20 + i * 2.60
        planters.append((26.60, py, 0.330, 1.800, 0.900, 0.520, 0.0))
        foliage.append((26.60, py, 0.660, 1.640, 0.760, 0.220, 0.0))
    pl = _boxes("Forecourt_Planters", planters, coll)
    C.add_bevel(pl, width=0.024, segments=2)
    C.assign(pl, _mat("PropKerb"))
    made.append(pl)
    fo = _boxes("Forecourt_Foliage", foliage, coll)
    C.add_bevel(fo, width=0.060, segments=2)
    C.assign(fo, _mat("PropFoliage"))
    made.append(fo)
    return made


# --------------------------------------------------------------------------- #

def build():
    C.purge_collection("PROPS")
    coll = C.collection("PROPS")

    groups = [
        ("wall_sign", build_wall_wordmark(coll)),
        ("deck_type", build_deck_type(coll)),
        ("floor_graphics", build_floor_graphics(coll)),
        ("pit_kit", build_pit_kit(coll)),
        ("tyre_bay", build_tyre_bay(coll)),
        ("plaque", build_spec_plaque(coll)),
        ("pit_board", build_pit_board(coll)),
        ("barrier", build_barrier(coll)),
        ("vitrine", build_vitrine(coll)),
        ("gantry", build_gantry(coll)),
        ("forecourt", build_forecourt(coll)),
    ]

    report, total = {}, 0
    for name, objs in groups:
        polys = sum(len(o.data.polygons) for o in objs
                    if getattr(o, "type", None) == "MESH")
        report[name] = {"objects": len(objs), "polys": polys}
        total += polys
    # Base-mesh polys: the bevel modifiers on almost everything here are not
    # applied, so the render-time figure is several times this. Printed because a
    # staging pass that is not measured is how the room got two invisible tyre
    # stacks in the first place.
    print("   props " + "  ".join(f"{k}={v['polys']}" for k, v in report.items()))
    return {"props": sum(v["objects"] for v in report.values()),
            "polys": total, "groups": report}
