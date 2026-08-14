"""Lighting scheme v2: cold architecture, warm object.

Drop-in replacement for s05_lighting. Not wired into rebuild_scene.py - swap the
STAGES entry from "s05_lighting" to "s05_lighting_v2" to try it.

WHY THIS EXISTS
---------------
v1 lights the car adequately and the room by accident. Three measurements say so:

  * A raycast frame map of the hero cameras shows 37 % (front quarter) and 49 %
    (hero low) of all pixels are bare wall. Those walls receive 1.0 W/m2, all of
    it spill from the key and fill, and measure a flat 0.107-0.196 display luma
    with no gradient. Half the frame is an unlit grey field.
  * Every region of the current hero frame measures R:G:B = 0.99:1.00:1.03. There
    is no colour information anywhere in the image - architectural and display
    light are the same white.
  * The frame map also shows the ceiling is never in shot from any hero camera.
    All six spot cans and all four cove rings - 1,377 W of emissive mesh plus
    1,380 W of spot lamps - are fixtures nobody can see, producing a wash that
    flattens rather than shapes.

The scheme here splits the rig into three jobs with three colour temperatures:
architecture (cool, low radiance, grazing), display (warm, tight, on the car
only) and separation (cold, high radiance, small). The room is described by its
own light instead of by leakage from the car's.

THE RULE THAT GOVERNS CLIPPING HERE
-----------------------------------
Measured transfer curve for this project's exact view transform (AgX + Medium
High Contrast, exposure 0) - see the radiance/8-bit table below:

    radiance  0.02  0.10  0.35  0.70  1.40  3.00  4.50  6.50
    8-bit       23    81   160   194   219   238   246   252

Clipping (>= 250) starts at scene radiance ~5.6. On the 0.042-albedo walls that
needs 419 W/m2 of irradiance, which is unreachable; on the 0.40-albedo dais it
needs 44 W/m2 against the 7.0 it currently gets. So diffuse surfaces in this room
essentially cannot clip. Every clipped pixel in the current renders is SPECULAR -
the mirror image of a high-radiance source in the car's clearcoat, the turntable
deck or the polished floor.

That makes source area, not wattage, the clipping control. Irradiance from an
area lamp depends only on its total power; radiance is power / (area * pi). So
widening a source at constant wattage leaves the exposure of the scene exactly
where it was and divides the specular highlight's peak brightness by the area
ratio. The Rim below is fixed that way: same 280 W, same light on the car, less
than half the radiance.

This is the constructive form of the D007 lesson. D007 said "match by radiance,
not watts" because 1900 W on 1.26 m2 was 17x the radiance of 1100 W on 12.6 m2.
The same identity run forwards says: to kill a specular clip without changing
exposure, grow the source and leave the watts alone.

A TRAP WORTH RECORDING
----------------------
Area-light `spread` is documented as "how widely the emitted light fans out, as
in the case of a gridded softbox", which sounds subtractive - narrow the cone,
lose the wide light, keep the rest. It is not. Measured on a 4.2 x 3.0 m panel at
4 m with a probe on axis and a second probe 45 deg off it:

    spread     180    120     90     60     40     25
    on-axis   1.00   2.05   3.11   4.60   5.09   5.13
    spill     1.00   1.31   1.03   0.23   0.00   0.00

Blender conserves total power and concentrates it. Narrowing the key from 120 to
60 deg without touching its energy would have multiplied the light on the car by
2.2x. Spread is still the right tool for killing spill - but energy must be
divided by the concentration factor at the same time, and the factor depends on
the geometry, so it has to be measured per lamp rather than assumed.

TWO THINGS THIS SCHEME GOT WRONG FIRST, BOTH CAUGHT BY RENDERING
----------------------------------------------------------------
Predicted +0.1 pp of clipping; the first render measured +4.1 pp. Form factors
and a transfer curve are not a substitute for a frame.

1. Widening a source can push it INTO the frame. Growing the Rim from
   3.6 x 0.35 to 4.8 x 0.62 halved its radiance exactly as intended, but its
   centre sits 2 % above the top of the front-quarter frame, so the extra 135 mm
   of height dropped its lower edge into shot. At radiance 30 a directly visible
   lamp is pure white: it clipped 6.4 % of the upper-left on its own - far more
   than the 2.2 % specular highlight the widening was meant to cure. Every lamp
   in the car rig is now visible_camera = False. None of them is a practical, and
   the flag also makes future size changes safe.

2. A low side light blows the dais rim before it helps the car. The "Flank" lamp
   added here - low and level, to exploit the cosine advantage a vertical surface
   has over a horizontal one - took dais_front from 1.7 % to 34.1 % clipped. The
   geometry is decisive and no aiming fixes it: the dais rim is itself a vertical
   0.40-albedo surface at r = 3.7 m facing the lamp, while the car flank is
   0.18 albedo and 2.6x further away. Per unit power the rim collects about 3.9x
   the irradiance and returns 2.2x as much of it - an 8.5x advantage to the
   plinth. Any source low enough to graze the car must cross the platform that
   surrounds it. The lamp is gone.

   The useful negative result: the dais-to-car ratio cannot be improved by ADDING
   light anywhere. It can only be improved by taking light off the dais or by
   lowering its albedo further, and the albedo was already retuned 0.60 -> 0.40.
   The ratio is a material problem wearing a lighting problem's clothes.
"""

import math

import bpy

import common as C
import s02_showroom as S

CEIL = S.CEIL_Z

# Interior faces, not the outer shell: s02 builds the back wall as a box from
# x = -15.25 to -15.00, so the surface anything grazes is x = -15.00.
WALL_BACK_X = -S.ROOM_X
WALL_SIDE_Y = S.ROOM_Y

# The architectural light-line height. The visible wall band is z = 0.25-3.56 for
# the front quarter and 0.59-6.10 for the hero low, so 2.44 is inside both, and
# it clears the car (roof ~1.3 m) so the line runs behind the body rather than
# being occluded by it.
LINE_Z = 2.44
LINE_H = 0.05

# Three colour groups. Luma is listed because Blender's light `color` multiplies
# the spectrum: recolouring a lamp without dividing its energy by the new colour's
# luma silently dims it. Every energy below is quoted post-correction.
COOL = (0.70, 0.82, 1.00)      # ~6500 K architecture   luma 0.809
WARM = (1.00, 0.90, 0.76)      # ~3600 K display        luma 0.916
COLD = (0.88, 0.94, 1.00)      # ~5800 K separation     luma 0.930


def _luma(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _coll():
    return C.collection("LIGHTS")


def annulus(name, r_in, r_out, z, coll, segments=192, cz=(0.0, 0.0)):
    """Flat downward-facing ring - the cove that paints the body highlight."""
    rings = []
    for r in (r_in, r_out):
        rings.append([(cz[0] + r * math.cos(C.TAU * i / segments),
                       cz[1] + r * math.sin(C.TAU * i / segments), z)
                      for i in range(segments)])
    verts, faces = C.loft(rings, closed=True, cap_start=False, cap_end=False)
    return C.new_obj(name, verts, faces, coll=coll, smooth=False)


def area_light(name, coll, loc, target, size, size_y, power, color=(1, 1, 1),
               shape="RECTANGLE", spread_deg=120.0, visible=True):
    """Area lamp aimed at a point.

    `power` is taken as the wattage that would deliver the intended irradiance at
    neutral white; it is divided by the colour's luma so that changing colour
    changes only hue, never level.
    """
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = shape
    ld.size = size
    ld.size_y = size_y
    ld.energy = power / max(_luma(color), 1e-6)
    ld.color = color
    ld.spread = math.radians(spread_deg)
    ld.use_shadow = True
    ob = bpy.data.objects.new(name, ld)
    coll.objects.link(ob)
    ob.location = loc
    _aim(ob, target)
    # Wash lamps sit inside the frame at z ~2.4 near the walls. The emissive line
    # is the fixture the viewer is meant to see; the lamp doing the work hides.
    ob.visible_camera = visible
    return ob


def _aim(ob, target):
    from mathutils import Vector
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def _offset_along(lamp, dist):
    from mathutils import Vector
    fwd = lamp.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    return lamp.location + fwd * dist


def _emissive(name, color, strength):
    import s03_materials as M
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = M.emitter(name, color, strength)
    return mat


# --------------------------------------------------------------------------- #
# L1 - the architectural light-line and its double wall wash
# --------------------------------------------------------------------------- #

def build_wall_line(coll):
    """A continuous illuminated reveal at z = 2.44 on both solid walls.

    This is the single biggest change in the scheme, because it is aimed at the
    single biggest thing in the frame: 37-49 % of the hero pixels are these two
    walls. It does four jobs at once. It puts a converging perspective line in
    shot, which is the strongest depth cue available and the thing the flat grey
    field is missing. It gives the polished floor something worth reflecting -
    the floor is 15 % of the front quarter and 22 % of the rear quarter and
    currently mirrors nothing but the dais. It is a practical that is actually
    visible, unlike every ceiling fixture in v1. And it carries the cool half of
    the colour scheme, against which the warm car reads.

    Radiance 3.0 puts the line itself at 238/255 - bright enough to read as a
    light source, two stops inside the 250 clip threshold, and it is only 5 cm
    tall so even if it did clip the pixel count would be negligible.
    """
    made = []
    line_mat = _emissive("WallLineEmit", (0.72, 0.84, 1.00), 3.0)
    fin_mat = bpy.data.materials["CeilingMat"]

    # proud of the wall by 12 mm so the emitter never z-fights the wall face
    bx = WALL_BACK_X + 0.012
    sy = WALL_SIDE_Y - 0.012

    back = C.box("WallLine_Back", bx, bx + 0.004, -S.ROOM_Y, S.ROOM_Y,
                 LINE_Z - LINE_H * 0.5, LINE_Z + LINE_H * 0.5, coll=coll)
    side = C.box("WallLine_Side", -S.ROOM_X, S.ROOM_X, sy - 0.004, sy,
                 LINE_Z - LINE_H * 0.5, LINE_Z + LINE_H * 0.5, coll=coll)
    for ob in (back, side):
        C.assign(ob, line_mat)
        ob.visible_shadow = False
        made.append(ob)

    # Shallow fins above and below turn the strip into a reveal instead of a
    # glowing tape stuck on a flat wall. Kept to 80 mm so they do not shadow the
    # wash lamps, which sit 300 mm out.
    for i, dz in enumerate((-0.075, 0.075)):
        f = C.box(f"WallLine_BackFin_{i}", WALL_BACK_X, WALL_BACK_X + 0.080,
                  -S.ROOM_Y, S.ROOM_Y, LINE_Z + dz - 0.018, LINE_Z + dz + 0.018,
                  coll=coll)
        C.assign(f, fin_mat)
        made.append(f)
        g = C.box(f"WallLine_SideFin_{i}", -S.ROOM_X, S.ROOM_X,
                  WALL_SIDE_Y - 0.080, WALL_SIDE_Y,
                  LINE_Z + dz - 0.018, LINE_Z + dz + 0.018, coll=coll)
        C.assign(g, fin_mat)
        made.append(g)
    return made


def build_wall_wash(coll):
    """Four long, low-radiance grazers that wash up and down from the line.

    Only the visible run of each wall is lit. The front quarter sees the back
    wall over y = +1.5..+11.0 and the side wall over x = -13.7..-3.3; the hero
    low sees y = -0.5..+10.4 and x = -14.2..-3.9. An 11.5 m source centred on the
    union covers both, and lighting the other 40 m of wall that no camera can see
    would only add render cost and ambient flattening.

    Radiance is deliberately tiny - about 10, against the Rim's 30 and a clip
    threshold of 5.6 on a surface reflecting 100 %. On a 0.042 wall these cannot
    clip anything even at the scallop peak just below the fin.
    """
    made = []
    # (name, centre, half-length axis, size, aim z, power)
    # Standoff matters more than power. At 0.30 m off the wall the wash measured
    # a 10:1 drop between z=2.2 and z=5.2 - a tight halo hugging the fin and
    # almost nothing on the wall the cameras actually frame. 0.55 m spreads the
    # same watts over roughly three times the height.
    off = 0.55
    runs = [
        ("WallWash_BackDn", (WALL_BACK_X + off, 5.25, LINE_Z - 0.12),
         (WALL_BACK_X, 5.25, 0.80), 11.5, 30.0),
        ("WallWash_BackUp", (WALL_BACK_X + off, 5.25, LINE_Z + 0.12),
         (WALL_BACK_X, 5.25, 4.80), 11.5, 34.0),
        ("WallWash_SideDn", (-8.75, WALL_SIDE_Y - off, LINE_Z - 0.12),
         (-8.75, WALL_SIDE_Y, 0.80), 11.0, 30.0),
        ("WallWash_SideUp", (-8.75, WALL_SIDE_Y - off, LINE_Z + 0.12),
         (-8.75, WALL_SIDE_Y, 4.80), 11.0, 34.0),
    ]
    for name, loc, aim, length, power in runs:
        ob = area_light(name, coll, loc, aim, length, 0.12, power, COOL,
                        spread_deg=150.0, visible=False)
        made.append(ob)
    return made


# --------------------------------------------------------------------------- #
# L7 - practicals that are actually in shot
# --------------------------------------------------------------------------- #

def build_floor_practicals(coll):
    """Luminous bases on the stanchion ring, with a real pool under each.

    s07 puts eight rope posts at r = 6.95 with the ring rotated -11.5 deg so no
    post lands on a camera sightline; the same radius and phase are reused here
    so the glow sits on the posts rather than beside them. s07 is left alone.

    Eight warm pools at a known radius give the dark floor scale and depth, and
    the polished floor doubles them. This is the fixture that justifies floor
    light - the ceiling rig never appears in any hero frame.
    """
    made = []
    disc_mat = _emissive("BollardEmit", (1.00, 0.86, 0.66), 2.5)
    for i in range(8):
        a = C.TAU * i / 8 + math.radians(-11.5)
        x, y = 6.95 * math.cos(a), 6.95 * math.sin(a)

        ring = annulus(f"Bollard_Ring_{i}", 0.108, 0.150, 0.026, coll,
                       segments=32, cz=(x, y))
        C.assign(ring, disc_mat)
        ring.visible_shadow = False
        made.append(ring)

        # A disc emitter this small lights nothing on its own (0.03 m2 at
        # radiance 2.5 is well under a watt), so the pool is a real lamp.
        # 0.6 m rather than 0.3: visible_camera hides a lamp from primary rays
        # but not from the polished floor, and at 0.3 m this sat at radiance 25,
        # well above the 5.6 that clips a mirror at grazing incidence. Widening
        # it drops radiance to ~8 for the same pool.
        lp = area_light(f"Bollard_Lamp_{i}", coll, (x, y, 0.45), (x, y, 0.0),
                        0.60, 0.60, 18.0, (1.00, 0.86, 0.66),
                        shape="DISK", spread_deg=150.0, visible=False)
        made.append(lp)
    return made


def build_floor_graze(coll):
    """A grazing sheet along the glazing - the rear quarter's floor story.

    The rear quarter is 22 % bare floor over x = -4.4..+12.5, y = -10.6..+3.7 and
    it currently reflects nothing. At grazing incidence the floor's Fresnel term
    goes to ~1, so this strip is seen in the mirror at very nearly its own
    radiance: 4.0 lands at 244/255, deliberately just under the 250 threshold.
    Raising it further would clip the reflection, not the floor.
    """
    return [area_light("FloorGraze", coll, (4.0, -10.55, 0.16), (4.0, -4.0, 0.02),
                       14.0, 0.10, 17.6, COOL, spread_deg=110.0, visible=False)]


# --------------------------------------------------------------------------- #
# ceiling coves - kept, but demoted
# --------------------------------------------------------------------------- #

def build_coves(coll):
    """Ring coves over the platform, plus one demoted straight strip.

    v1 ran two 27 m2 strips at radiance 4.8 - 408 W each, the largest emissive
    load in the scene - at y = +/-7.6, which is 7.6 m off the car's axis and
    outside every hero frame. Their whole contribution was an even ambient wash:
    precisely the flat generic light the scheme is trying to replace. Contrast is
    made by removing light as much as by adding it.

    Halved rather than deleted, though. Deleting the +Y strip outright and taking
    the other to 1.6 cuts 83 % of the ambient, and ambient is what keeps the far
    corners off the floor of the histogram - the rear quarter already measures
    0.370 % crushed against a 0.5 % budget, so there is only about 0.13 pp of room
    to spend. Radiance 2.4 on both strips halves the flattening and leaves the
    shadow end alone. This is the one number in the scheme that a render has to
    confirm rather than a form factor.

    The ring coves stay at full strength. They are the source of the long
    highlight down the car's flank, which is the one thing v1's lighting does
    genuinely well.
    """
    made = []
    ring = annulus("Cove_Ring", 4.05, 4.85, CEIL - 0.14, coll)
    C.assign(ring, bpy.data.materials["CoveEmit"])
    ring.visible_shadow = False
    made.append(ring)

    ring2 = annulus("Cove_RingOuter", 6.60, 7.10, CEIL - 0.06, coll)
    C.assign(ring2, _emissive("CoveEmitSoft", (0.98, 0.97, 1.0), 3.4))
    ring2.visible_shadow = False
    made.append(ring2)

    soft = _emissive("CoveEmitAmbient", (0.96, 0.97, 1.0), 2.4)
    for i, y in enumerate((-7.6, 7.6)):
        strip = C.box(f"Cove_Strip_{i}", -12.5, 12.5, y - 0.26, y + 0.26,
                      CEIL - 0.10, CEIL - 0.08, coll=coll)
        C.assign(strip, soft)
        strip.visible_shadow = False
        made.append(strip)

    for i, y in enumerate((-7.6, 7.6)):
        h = C.box(f"Cove_Coffer_{i}", -12.6, 12.6, y - 0.38, y + 0.38,
                  CEIL - 0.11, CEIL + 0.02, coll=coll)
        C.assign(h, bpy.data.materials["CeilingMat"])
        made.append(h)
    return made


def build_spot_rig(coll):
    """Two working spots that make visible pools, four demoted to dressing.

    Measured per-probe, the six v1 spots contribute 0.02-0.35 W/m2 each - their
    largest single contribution anywhere is 4.8 % of one probe's total. Six even
    accents at that level are a sprinkle, not lighting. Spot_0 and Spot_2 are the
    only two that reach the car, so they get the budget and a tighter cone to lay
    real pools either side of the dais; the rest stay as fixture geometry at a
    token wattage so the ceiling still reads as a rigged showroom.
    """
    made = []
    body_mat = bpy.data.materials.get("SpotBody")
    if body_mat is None:
        body_mat, nt, b = C.material("SpotBody")
        C.set_defaults(b, Base_Color=(0.028, 0.028, 0.030, 1.0), Metallic=0.6,
                       Roughness=0.35)

    # x, y, aim, power, cone degrees
    placements = [
        (6.4, -5.2, (2.60, -2.30, 0.05), 430.0, 19.0),
        (6.4, 5.2, (0.4, 0.0, 0.80), 60.0, 30.0),
        (-5.8, -5.2, (-2.70, -2.20, 0.05), 360.0, 20.0),
        (-5.8, 5.2, (-0.6, 0.0, 0.75), 60.0, 32.0),
        (0.0, -7.0, (0.0, 0.0, 0.60), 55.0, 34.0),
        (0.0, 7.0, (0.0, 0.0, 0.60), 45.0, 34.0),
    ]

    for i, (x, y, target, power, spread) in enumerate(placements):
        z_top = CEIL - 0.06
        rod = C.box(f"SpotRod_{i}", x - 0.018, x + 0.018, y - 0.018, y + 0.018,
                    z_top - 0.34, z_top, coll=coll)
        C.assign(rod, body_mat)
        made.append(rod)

        can = C.revolve(f"SpotCan_{i}", [
            (0.000, 0.000), (0.088, 0.000), (0.096, 0.012), (0.096, 0.190),
            (0.088, 0.202), (0.000, 0.202)],
            segments=48, coll=coll, auto_smooth=32.0)
        can.location = (x, y, z_top - 0.54)
        C.assign(can, body_mat)
        made.append(can)

        lens = C.revolve(f"SpotLens_{i}", [(0.000, 0.0), (0.082, 0.0),
                                           (0.082, 0.006), (0.000, 0.006)],
                         segments=48, coll=coll, auto_smooth=None)
        lens.location = (x, y, z_top - 0.545)
        C.assign(lens, bpy.data.materials["SpotEmit"])
        lens.visible_shadow = False
        made.append(lens)

        lname = f"Spot_{i}"
        ld = bpy.data.lights.new(lname, "SPOT")
        ld.energy = power / _luma(WARM)
        ld.color = WARM
        ld.spot_size = math.radians(spread)
        ld.spot_blend = 0.42
        ld.shadow_soft_size = 0.10
        lo = bpy.data.objects.new(lname, ld)
        coll.objects.link(lo)
        lo.location = (x, y, z_top - 0.55)
        _aim(lo, target)
        made.append(lo)

        can.rotation_euler = lo.rotation_euler
        lens.rotation_euler = lo.rotation_euler
        can.location = _offset_along(lo, 0.36)
        lens.location = _offset_along(lo, 0.55)
    return made


# --------------------------------------------------------------------------- #
# the car rig
# --------------------------------------------------------------------------- #

def build_three_point(coll):
    """Key / fill / rim / kick, warm on the car and cold on its trailing edge."""
    focus = (0.15, 0.0, 0.78)
    made = [
        # KEY - same place as v1, but demoted from 1100 W to 700 and left to do
        # only what a high source is good for: the top surfaces, the engine cover
        # and the long cove highlight.
        #
        # Moving the key CLOSER was tried first and measured worse. At 5.6 m it
        # raised the car flank from 2.71 to 3.49 W/m2 but the dais top from 4.84
        # to 7.44, taking the plinth-to-subject ratio from 1.46 to 1.94 - the
        # wrong direction, and straight into the surface that was just retuned.
        # The reason is geometric and no amount of aiming fixes it: the dais is a
        # horizontal 0.40-albedo plane directly under the lamp, so it collects a
        # near-unity cosine, while the flank is vertical and collects very little.
        # A downward key always favours the plinth over the car.
        area_light("Key", coll, (6.2, -5.0, 4.6), (0.25, -0.10, 0.92),
                   4.6, 3.4, 1000.0, WARM, spread_deg=100.0, visible=False),
        # FILL - broad and weak from the opposite side, kills black shadow sides.
        # Cool, so the shadow side reads as room light rather than as more key.
        area_light("Fill", coll, (4.2, 5.6, 2.8), focus, 5.0, 3.4, 540.0,
                   COOL, spread_deg=140.0, visible=False),
        # RIM - v1's position, aim and wattage, deliberately unchanged. The ONLY
        # edit is shape: 3.6 x 0.35 m becomes 4.8 x 0.62, area 1.26 -> 2.98 m2.
        # Per-region measurement put 2.175 % clipping inside the rear-wing box and
        # this lamp is the cause: at radiance 68.6 it was the brightest source in
        # the scene and its own reflection in the wing's clearcoat clipped.
        # Irradiance from an area lamp depends only on total power, so widening it
        # leaves the light on the car exactly where it was and drops peak radiance
        # to 30 - below the ~60 at which a clearcoat highlight clips. Re-aiming it
        # was tried too and cost 0.6 W/m2 off the car's rear for a 0.4 gain on the
        # dais, so the aim stays put.
        area_light("Rim", coll, (-6.6, 1.8, 3.2), focus,
                   4.8, 0.62, 280.0, COLD, spread_deg=110.0, visible=False),
        # KICK - low and close, grazing the flank to reveal body curvature
        # Widened 2.6 x 0.5 -> 3.0 x 0.62 on the same principle as the Rim: at
        # 1.30 m2 it was the highest-radiance source left in the rig at 31.8, and
        # it grazes the livery at close range where a clearcoat clips easily.
        # Same 130 W, same light, radiance down to 22.
        area_light("Kick", coll, (3.4, -4.4, 0.62), (0.4, -0.2, 0.55),
                   3.0, 0.62, 130.0, WARM, spread_deg=120.0, visible=False),
    ]
    return made


def build():
    C.purge_collection("LIGHTS")
    coll = C.collection("LIGHTS")
    build_coves(coll)
    build_spot_rig(coll)
    build_three_point(coll)
    build_wall_line(coll)
    build_wall_wash(coll)
    build_floor_practicals(coll)
    build_floor_graze(coll)
    return {"lights": len([o for o in coll.objects if o.type == "LIGHT"]),
            "emitters": len([o for o in coll.objects if o.type == "MESH"])}
