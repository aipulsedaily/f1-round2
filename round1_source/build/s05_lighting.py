"""Showroom lighting: cold architecture, warm object.

The rig is split into three jobs with three colour temperatures - architecture
(cool, low radiance, grazing the walls), display (warm, tight, on the car) and
separation (cold, high radiance, small) - so that the room is described by its
own light instead of by leakage from the car's.

WHY THE RIG WAS REBUILT
-----------------------
The previous version lit the car adequately and the room by accident. Three
measurements said so:

  * A raycast frame map of the hero cameras shows 37 % (front quarter) and 49 %
    (hero low) of all pixels are bare wall. Those walls received 1.0 W/m2, all of
    it spill from the key and fill, and measured a flat 0.107-0.196 display luma
    with no gradient. Half the frame was an unlit grey field.
  * Every region of the hero frame measured R:G:B = 0.99:1.00:1.03. There was no
    colour information anywhere in the image - architectural and display light
    were the same white.
  * The same frame map shows the ceiling is never in shot from any hero camera.
    Six spot cans and four cove rings - 1,377 W of emissive mesh plus 1,380 W of
    spot lamps - were fixtures nobody can see, producing a wash that flattened
    rather than shaped.

THE RULE THAT GOVERNS CLIPPING HERE
-----------------------------------
Measured transfer curve for this project's exact view transform (AgX + Medium
High Contrast, exposure 0):

    radiance  0.02  0.10  0.35  0.70  1.40  3.00  4.50  6.50
    8-bit       23    81   160   194   219   238   246   252

Clipping (>= 250 in all three channels) starts at scene radiance ~5.6. On the
0.042-albedo walls that needs 419 W/m2 of irradiance, which is unreachable; on
the 0.40-albedo dais it needs 44 W/m2 against the 7.0 it actually gets. Diffuse
surfaces in this room essentially cannot clip, so every clipped pixel in these
renders is SPECULAR - the mirror image of a high-radiance source in the car's
clearcoat, the turntable deck or the polished floor.

That makes source AREA, not wattage, the clipping control. Irradiance from an
area lamp depends only on its total power, while its radiance is
power / (area * pi). Widening a source at constant wattage therefore leaves the
exposure of the scene exactly where it was and divides the specular highlight's
peak brightness by the area ratio. The Rim, the Kick and the floor grazer below
are all fixed that way: same watts, same light on the subject, less than half the
radiance.

This is the constructive form of the D007 lesson. D007 said "match by radiance,
not watts" because 1900 W on 1.26 m2 was 17x the radiance of 1100 W on 12.6 m2.
The same identity run forwards says: to kill a specular clip without changing
exposure, grow the source and leave the watts alone.

A TRAP WORTH RECORDING
----------------------
Area-light `spread` is documented as "how widely the emitted light fans out, as
in the case of a gridded softbox", which sounds subtractive - narrow the cone,
lose the wide light, keep the rest. It is not. Measured on a 4.2 x 3.0 m panel at
4 m with a probe on axis and a second probe 4 m off it:

    spread     180    120     90     60     40     25
    on-axis   1.00   2.05   3.11   4.60   5.09   5.13
    spill     1.00   1.31   1.03   0.23   0.00   0.00

Blender conserves total power and concentrates it. Narrowing the key from 120 to
60 deg without touching its energy would have multiplied the light on the car by
2.2x. Spread is the right tool for killing spill, but it also multiplies the
radiance a specular surface sees, so it has to be counted twice: once as more
light on the subject and once as a brighter reflection.

TWO THINGS THIS SCHEME GOT WRONG FIRST, BOTH CAUGHT ONLY BY RENDERING
---------------------------------------------------------------------
The design predicted +0.1 pp of clipping; the first render measured +4.1 pp. Form
factors and a transfer curve are not a substitute for a frame.

1. Widening a source can push it INTO the frame. Growing the Rim from
   3.6 x 0.35 to 4.8 x 0.62 halved its radiance exactly as intended, but its
   centre sits 2 % above the top of the front-quarter frame, so the extra 135 mm
   of height dropped its lower edge into shot. At radiance 30 a directly visible
   lamp is pure white: it clipped 6.4 % of the upper-left on its own, far more
   than the 2.2 % specular highlight the widening was meant to cure. Every lamp
   in the car rig is now visible_camera = False. None of them is a practical, and
   the flag also makes future size changes safe.

2. A low side light blows the dais rim before it helps the car. A "Flank" lamp -
   low and level, to exploit the cosine advantage a vertical surface has over a
   horizontal one - took dais_front from 1.7 % to 34.1 % clipped. The geometry is
   decisive and no aiming fixes it: the dais rim is itself a vertical 0.40-albedo
   surface at r = 3.7 m facing the lamp, while the car flank is 0.18 albedo and
   2.6x further away. Per unit power the rim collects about 3.9x the irradiance
   and returns 2.2x as much of it, an 8.5x advantage to the plinth. Any source
   low enough to graze the car must cross the platform that surrounds it, so no
   such source exists here.

   The useful negative result: the dais-to-car ratio cannot be improved by ADDING
   light anywhere. It can only be improved by taking light off the dais or by
   lowering its albedo further, and the albedo was already retuned 0.60 -> 0.40.
   It is a material problem wearing a lighting problem's clothes.

MEASURED A/B, ROOM ONLY, 1080p
------------------------------
                 old     new                        old     new
    FrontQuarter clip   0.153 %  0.062 %     wall_behind luma  0.167  0.261
    HeroLow clip        0.000 %  0.000 %     wall_corner luma  0.106  0.194
    crushed, both       0.000 %  0.000 %     bg_upper_mid      0.113  0.225
    dais_front clip     1.689 %  0.690 %     dais_flank clip   0.906 %  0.434 %

The dais retune that took the platform from 7.96 % to 0.43 % clipped is not
undone by any of this - it is improved. Dais clipping roughly halved, because
lowering every source's radiance removes the specular hits that caused it.

That A/B could not see the car, and two lamps differ here from the version it was
rendered at, both for reasons argued at the lamp: the Fill is back at spread 120
because widening it cost the rear quarter's key side 21 %, and the floor grazer is
on a 0.30 m panel instead of 0.10 because at 0.10 its own mirror image clips. Both
changes move a car or floor number and leave the walls within 2 %.
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
LINE_PROUD = 0.012
FIN_PROUD = 0.080

# Three colour groups. Luma is listed because Blender's light `color` multiplies
# the spectrum: recolouring a lamp without dividing its energy by the new colour's
# luma silently dims it. Every wattage below is quoted pre-correction, i.e. as the
# neutral-white power that would deliver the same level.
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

    `power` is the wattage that would deliver the intended irradiance at neutral
    white; it is divided by the colour's luma so that changing a lamp's colour
    changes only its hue, never its level.
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
    # The wash lamps sit inside the frame at z ~2.4 near the walls and the
    # practicals sit 0.45 m off the floor. The emissive line and the bollard rings
    # are the fixtures the viewer is meant to see; the lamps doing the work hide.
    ob.visible_camera = visible
    return ob


def _aim(ob, target):
    from mathutils import Vector
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def _offset_along(lamp, dist):
    """Point `dist` down a lamp's beam, taken from its euler rather than its matrix.

    matrix_world is filled in by the depsgraph, and nothing has evaluated it on a
    lamp created three lines earlier - it still reads as identity, so the old
    version of this returned "straight down" for every fixture. Measured on the
    built scene: the cans sat 0.23-0.25 m and the lenses 0.36-0.38 m off their own
    beam axis, which put each emissive lens inside its tilted can instead of at the
    mouth. These lamps have no parent and no scale, so the euler is the world
    rotation and this needs no evaluation at all.
    """
    from mathutils import Vector
    fwd = lamp.rotation_euler.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    return Vector(lamp.location) + fwd * dist


def _emissive(name, color, strength):
    """Emission material, rebuilt every call.

    Deliberately not a get-or-create: a cached material from an earlier build in
    the same session would keep its old strength, and a cove silently running at
    the previous iteration's brightness is exactly the kind of change that gets
    blamed on the lamp being tuned.
    """
    import s03_materials as M
    return M.emitter(name, color, strength)


def build_wall_line(coll):
    """A continuous illuminated reveal at z = 2.44 on both solid walls.

    This is the single biggest change in the scheme, because it is aimed at the
    single biggest thing in the frame: 37-49 % of the hero pixels are these two
    walls. It does four jobs at once. It puts a converging perspective line in
    shot - the two runs meet at the (-15, +11) corner, whose azimuth from the front
    quarter camera is 143.5 deg against that camera's 142.6, so the line converges
    on a point one degree off frame centre and directly behind the car. That is the
    strongest depth cue available and it is what the flat grey field was missing.
    It gives the polished floor something
    worth reflecting, the floor being 15 % of the front quarter and 22 % of the
    rear quarter and currently mirroring nothing but the dais. It is a practical
    that is actually visible, unlike every ceiling fixture. And it carries the cool
    half of the palette, against which the warm car reads.

    Radiance 3.0 puts the line at 233-238/255 - bright enough to read as a light
    source, comfortably inside the 250 clip threshold, and it is only 5 cm tall so
    even if it did clip the pixel count would be negligible.
    """
    made = []
    line_mat = _emissive("WallLineEmit", (0.72, 0.84, 1.00), 3.0)
    fin_mat = bpy.data.materials["CeilingMat"]

    bx = WALL_BACK_X + LINE_PROUD
    sy = WALL_SIDE_Y - LINE_PROUD

    # The back run owns the corner and the side run starts at the back run's own
    # proud face, so the two lines join instead of crossing. Coincident coplanar
    # faces in that corner would z-fight, and the corner is dead centre of the
    # front-quarter frame.
    back = C.box("WallLine_Back", bx, bx + 0.004, -S.ROOM_Y, S.ROOM_Y,
                 LINE_Z - LINE_H * 0.5, LINE_Z + LINE_H * 0.5, coll=coll)
    side = C.box("WallLine_Side", bx, S.ROOM_X, sy - 0.004, sy,
                 LINE_Z - LINE_H * 0.5, LINE_Z + LINE_H * 0.5, coll=coll)
    for ob in (back, side):
        C.assign(ob, line_mat)
        ob.visible_shadow = False
        made.append(ob)

    # Shallow fins above and below turn the strip into a reveal instead of a
    # glowing tape stuck on a flat wall. Kept to 80 mm so they do not shadow the
    # wash lamps, which sit 550 mm out. The side fins start 1 mm clear of the back
    # fins' end faces for the same anti-z-fight reason as the lines.
    for i, dz in enumerate((-0.075, 0.075)):
        f = C.box(f"WallLine_BackFin_{i}", WALL_BACK_X, WALL_BACK_X + FIN_PROUD,
                  -S.ROOM_Y, S.ROOM_Y, LINE_Z + dz - 0.018, LINE_Z + dz + 0.018,
                  coll=coll)
        C.assign(f, fin_mat)
        made.append(f)
        g = C.box(f"WallLine_SideFin_{i}", WALL_BACK_X + FIN_PROUD + 0.001,
                  S.ROOM_X, WALL_SIDE_Y - FIN_PROUD, WALL_SIDE_Y,
                  LINE_Z + dz - 0.018, LINE_Z + dz + 0.018, coll=coll)
        C.assign(g, fin_mat)
        made.append(g)
    return made


def build_wall_wash(coll):
    """Four long, low-radiance grazers that wash up and down from the line.

    Only the visible run of each wall is lit. The front quarter sees the back wall
    over y = +1.5..+11.0 and the side wall over x = -13.7..-3.3; the hero low sees
    y = -0.5..+10.4 and x = -14.2..-3.9. An 11.5 m source centred on the union
    covers both, and lighting the other 40 m of wall that no camera can see would
    only add render cost and ambient flattening.

    Radiance is deliberately tiny - 8.6 flat, 14 once spread 150 is counted,
    against the Rim's 77 - and on a 0.042 wall these cannot clip anything even at
    the scallop peak just below the fin: the wall would need 419 W/m2 and gets 4.4.
    The lamps themselves are hidden from camera, and the mirror geometry puts their
    floor reflections inside the dais radius where the platform occludes them.
    What they buy is a 50-60 % lift in wall luma, which is the whole point:
    0.167 -> 0.261 measured, and the wash is over half the back wall's total.
    """
    made = []
    # Standoff matters more than power. At 0.30 m off the wall the wash measured a
    # 10:1 drop between z = 2.2 and z = 5.2 - a tight halo hugging the fin and
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
        made.append(area_light(name, coll, loc, aim, length, 0.12, power, COOL,
                               spread_deg=150.0, visible=False))
    return made


def build_floor_practicals(coll):
    """Luminous bases on the stanchion ring, with a real pool under each.

    s07 puts eight rope posts at r = 6.95 with the ring rotated -11.5 deg so no
    post lands on a camera sightline; the same radius and phase are reused here so
    the glow sits on the posts rather than beside them, and the post profile is
    0.108 m at z = 0.026, so the ring starts exactly at the post's flare. s07 is
    left alone.

    Eight warm pools at a known radius give the dark floor scale and depth, and the
    polished floor doubles them. Four of the eight land on visible floor in the
    front quarter. This is the fixture that justifies floor light: the ceiling rig
    never appears in any hero frame, so its wash reads as ambient with no source.
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

        # A disc emitter this small lights nothing on its own (0.02 m2 at radiance
        # 2.5 is a third of a watt), so the pool is a real lamp. 0.60 m across
        # rather than 0.30: visible_camera hides a lamp from primary rays but not
        # from the polished floor, and the mirror geometry puts each lamp's
        # reflection about a metre from its own bollard, inside the pool where it
        # is certainly seen. A 0.30 m disc carries in-cone radiance 142 and that
        # reflection computes to 14 even at the floor's mildest Fresnel angle -
        # clipped white. At 0.60 m it is 35 and the reflection 3.5, or 241/255, and
        # the front quarter measured 0.062 % clipped with these in place against
        # 0.153 % without them.
        made.append(area_light(f"Bollard_Lamp_{i}", coll, (x, y, 0.45), (x, y, 0.0),
                               0.60, 0.60, 18.0, (1.00, 0.86, 0.66),
                               shape="DISK", spread_deg=150.0, visible=False))
    return made


def build_floor_graze(coll):
    """A grazing sheet along the glazing - the rear quarter's floor story.

    The rear quarter is 22 % bare floor over x = -4.4..+12.5, y = -10.6..+3.7 and
    it currently reflects nothing. This is a specular fixture, not a wash: at
    0.16 m above the floor its light arrives at almost 90 deg to the floor normal,
    so the diffuse return is nil and what the camera sees is the strip's own mirror
    image. That image lands at about (3.2, -9.3), which is 15 deg off the rear
    quarter's axis and just above frame centre, so it is certainly in shot.

    Sized 14.0 x 0.30 rather than the 14.0 x 0.10 the design called for, for the
    reason the Rim and the Kick were widened. The design capped this at radiance
    4.0 to stay under the threshold, but that figure was the panel's flat radiance
    and left out what spread does to it: 110 deg concentrates by 2.40x. At 0.10 m
    the panel holds 21.7 W over 1.4 m2, so 4.95 flat becomes 11.9 in the blue
    channel, and the floor's Fresnel term at 83 deg grazing is 0.68 once the coat
    is counted - the mirrored streak arrives at 8.1, which is pure white. At 0.30 m
    the same 17.6 W sits on 4.2 m2 for an in-cone 3.96 and a mirrored 2.69, or
    235/255. Same light on the floor, a bright streak instead of a blown one.

    This is still the one item in the scheme that has never been in a frame - the
    effect is entirely specular and no form-factor model can see it. If the rear
    quarter comes back with a clipped line near the glazing, halve the power
    rather than shrinking the panel.
    """
    return [area_light("FloorGraze", coll, (4.0, -10.55, 0.16), (4.0, -4.0, 0.02),
                       14.0, 0.30, 17.6, COOL, spread_deg=110.0, visible=False)]


def build_coves(coll):
    """Ring coves over the platform, plus two demoted straight strips.

    The straight strips ran two 27 m2 emitters at radiance 4.8 - 408 W each, the
    largest emissive load in the scene - at y = +/-7.6, which is 7.6 m off the
    car's axis and outside every hero frame. Their whole contribution was an even
    ambient wash: precisely the flat generic light this scheme replaces. Contrast
    is made by removing light as much as by adding it.

    Halved rather than deleted, though. Ambient is what keeps the far corners off
    the floor of the histogram, and the rear quarter measures 0.360 % crushed
    against a 0.5 % budget, so there is only about 0.14 pp to spend. The crushed
    map for that camera puts the dark pixels in the car's own cavities and in the
    near foreground floor, which sits directly under the +7.6 strip - the one
    surface these emitters really do serve.

    Sensitivity, measured on the delivered rear-quarter frame rather than guessed:
    the near-black population is 0.360 % at code <= 4 and 0.491 % at <= 6, so
    darkening everything by one code point costs about 0.06 pp. Halving these two
    strips removes roughly 8 % of the scene's useful power; the AgX toe is close
    to code ~ radiance^0.83 there, so 8 % is a quarter of one code point, well
    under 0.02 pp. Against that, the cool wash and warm practicals add chroma to
    the shadows, and crushed requires ALL THREE channels at or below 4 - lifting
    just the strongest channel by one point takes 0.360 % to 0.267 %. The colour
    split alone has more effect on this metric than the demotion, and in the safe
    direction.

    The ring coves stay at full strength. They are the source of the long highlight
    down the car's flank, which is the one thing the old rig did genuinely well.
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

    # recessed housings so the strips read as coffers, not floating planes
    for i, y in enumerate((-7.6, 7.6)):
        h = C.box(f"Cove_Coffer_{i}", -12.6, 12.6, y - 0.38, y + 0.38,
                  CEIL - 0.11, CEIL + 0.02, coll=coll)
        C.assign(h, bpy.data.materials["CeilingMat"])
        made.append(h)
    return made


def build_spot_rig(coll):
    """Two working spots that make visible pools, four demoted to dressing.

    Measured per-probe, the six old spots contributed 0.02-0.35 W/m2 each; their
    largest single contribution anywhere was 4.8 % of one probe's total. Six even
    accents at that level are a sprinkle, not lighting. Spot_0 and Spot_2 are the
    only two that reach the display area, so they get the budget and a tighter cone
    to lay real pools across the dais edge and the floor beyond it; the rest stay
    as fixture geometry at a token wattage so the ceiling still reads as a rigged
    showroom rather than an empty slab.

    Note that a Blender spot is a point light with a cone mask, not a reflector: it
    does not concentrate, so a 19 deg cone at 430 W radiates about 3 W. That is why
    these read as pools and not as hot spots, and why the re-aim onto the dais rim
    costs the plinth only 0.6 W/m2 against the 7.0 it already receives.
    """
    made = []
    body_mat = bpy.data.materials.get("SpotBody")
    if body_mat is None:
        body_mat, nt, b = C.material("SpotBody")
        C.set_defaults(b, Base_Color=(0.028, 0.028, 0.030, 1.0), Metallic=0.6,
                       Roughness=0.35)

    # x, y, aim point, watts, cone degrees
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

        # rotate the fixture body to match its lamp so they do not disagree
        can.rotation_euler = lo.rotation_euler
        lens.rotation_euler = lo.rotation_euler
        can.location = _offset_along(lo, 0.36)
        lens.location = _offset_along(lo, 0.55)
    return made


def build_three_point(coll):
    """Key / fill / rim / kick, warm on the car and cold on its trailing edge."""
    focus = (0.15, 0.0, 0.78)
    made = [
        # KEY - same place as before, on a panel grown 12.6 -> 15.64 m2 so its
        # radiance drops 27.2 -> 22.2 at no cost to exposure, and narrowed to
        # spread 100 so less of it lands on walls that now have their own light.
        #
        # 1000 W, NOT the 1150 the design proposed to restore the car flank after
        # Spot_0 and Spot_2 were re-aimed at the floor. That proposal came from an
        # irradiance audit that culled samples outside each lamp's spread cone but
        # did not boost the radiance inside it - the same asymmetry the spread
        # table above warns about, applied to the measuring tool instead of the
        # lamp. Re-run with the measured concentration counted (2.05x at 120 deg,
        # 2.76x at 100 deg), the narrowed key already delivers 6.85 W/m2 to the
        # flank against the old rig's 5.55, and the whole probe reads 9.70 against
        # 8.76. Parity was never lost; 1150 W would have overshot the flank by
        # 22 % and the dais top by 29 %, straight back into the surface that was
        # expensively retuned. 1000 W is also the value the room-only A/B was
        # actually rendered at, so leaving it there keeps that measurement valid.
        #
        # Moving the key CLOSER was tried and measured worse. At 5.6 m it raised
        # the car flank by 29 % but the dais top by 54 %, taking the
        # plinth-to-subject ratio from 1.46 to 1.94 - the wrong direction. A
        # downward key always favours the plinth: the dais is a horizontal
        # 0.40-albedo plane directly under the lamp and collects a near-unity
        # cosine, while the flank is vertical and collects very little.
        area_light("Key", coll, (6.2, -5.0, 4.6), (0.25, -0.10, 0.92),
                   4.6, 3.4, 1000.0, WARM, spread_deg=100.0, visible=False),
        # FILL - broad and weak from the opposite side, kills the black shadow
        # side. Cool, so that side reads as room light rather than as more key.
        #
        # This, not the key, is where the car actually lost light. The design took
        # the fill from 620 W at spread 120 to 540 W at spread 140, and widening a
        # spread costs on-axis level: 1.70x concentration instead of 2.05x. The two
        # together compute to a 21 % drop on the +Y flank - which is the REAR
        # QUARTER's key side, so the loss lands on a delivered camera that the
        # room-only A/B could not see. Restored to v1 parity the cheap way, by
        # putting the spread back to 120 rather than by adding watts: at 600 W the
        # +Y flank computes 7.22 W/m2 against the old rig's 7.18, on 20 W less
        # power than v1. The measured spill table says 120 vs 140 deg changes what
        # reaches the wall by under 5 %, and the wall wash now supplies over half
        # the back wall's light anyway, so the room A/B stands.
        area_light("Fill", coll, (4.2, 5.6, 2.8), focus, 5.0, 3.4, 600.0,
                   COOL, spread_deg=120.0, visible=False),
        # RIM - position, aim and wattage deliberately unchanged. The ONLY edit is
        # shape: 3.6 x 0.35 m becomes 4.8 x 0.62, area 1.26 -> 2.98 m2. Per-region
        # measurement put 2.175 % clipping inside the rear-wing box and this lamp
        # was the cause: at radiance 68.6 it was the brightest source in the scene
        # and its own reflection in the wing's clearcoat clipped. Irradiance from an
        # area lamp depends only on total power, so widening it leaves the light on
        # the car exactly where it was and drops peak radiance to 30, below the ~60
        # at which a clearcoat highlight clips. Re-aiming it was tried too and cost
        # 0.6 W/m2 off the car's rear for a 0.4 gain on the dais, so the aim stays.
        area_light("Rim", coll, (-6.6, 1.8, 3.2), focus,
                   4.8, 0.62, 280.0, COLD, spread_deg=110.0, visible=False),
        # KICK - low and close, grazing the flank to reveal body curvature. Widened
        # 2.6 x 0.5 -> 3.0 x 0.62 on the same principle as the Rim: at 1.30 m2 it
        # was the highest-radiance source left in the rig at 31.8, and it grazes the
        # livery at close range where a clearcoat clips easily. Same 130 W, same
        # light, radiance down to 22.
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
