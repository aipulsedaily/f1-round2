"""Showroom shell, polished floor, glazing, display platform + turntable.

Room is 30 x 22 x 6.2 m. Car sits nose-+X, centred on the platform; the
turntable deck top is at z = TT_TOP, which is the tyre contact height.

THE ARCHITECTURE PASS
---------------------
The room was 27 k polys against a 4.35 M car, and the reason was never budget -
nobody had measured what the four cameras actually frame. Projecting the room
analytically into each hero camera says:

  * No camera sees the ceiling. It is above frame in FrontQuarter and
    RearQuarter, below the camera in TopDown, and in HeroLow it is the top 5 %
    of frame at the back wall. Anything built up there is invisible.
  * FrontQuarter's frame above the car's silhouette is 643,000 px of unbroken
    wall at mean luma 0.1487 and standard deviation 0.0403. That single number
    is the defect: the wall has no variance, only a gradient.
  * TopDown is orthographic at scale 6.60, so its window is +-3.300 x +-1.856 m
    - smaller than the turntable deck. It sees deck and nothing else.

So the budget goes on the wall surface, the dais silhouette, the floor datum and
the glazing grid. Everything here is measured into frame percentages before it
is built; the keep-out bands below come from those projections.

WHAT THIS MODULE MUST NOT COLLIDE WITH
--------------------------------------
The room is being worked on by three modules at once and this one runs third of
six, so it can see neither of the others' output. Both couplings are hard-coded
and both are documented where they bite.

s05_lighting owns the light. It runs a continuous emissive reveal at z = 2.44 on
both solid walls, 12 mm proud, with 80 mm-proud fins at z = 2.35 and 2.53, plus
four wall-wash lamps standing 0.55 m off the walls. That line is deliberately
unbroken - the two runs converge on the corner behind the car, which is the
frame's strongest depth cue - so the fluted panels here stop at z = 1.80 and
restart at z = 3.00, leaving it a 1.20 m band with 0.47 m of clearance either
side. LIGHT_BAND is deliberately loose: s05 can move its line +-0.35 m before
anything here needs a change. It cannot simply be imported, because s05 imports
this module.

s07_props owns the dressing and reached the same conclusions independently, so
two things proposed for this module have been withdrawn rather than built
through. It puts a datum ring on the turntable at r = 3.180..3.220, so the
matching perimeter groove is no longer cut into the deck profile - a recess and
a boss at one radius means their ring bridges the groove and floats over it.
And it hangs a wordmark and a gantry off the back wall at z = 2.6..3.8, 136-190
mm proud, which is past this panel's own fin tips, so the upper back-wall run
stops short of them. See build_platform() and build_wall_panels().

Verified after every edit by rebuilding room-only and testing the result rather
than the intent: panel normals, one shared fin grid, and triangle-level overlap
against every mesh in PROPS and LIGHTS.
"""

import math

import bmesh
import bpy

import common as C
import s03_materials as M

ROOM_X = 15.0          # walls at +/- ROOM_X
ROOM_Y = 11.0
CEIL_Z = 6.2
WALL_T = 0.25

DAIS_R = 3.70
TT_R = 3.45
TT_TOP = 0.340         # tyre contact plane
WELL_Z = 0.100
TT_ROT_DEG = 12.0      # deck yaw, so the circular brushed grain is off-axis

# --- fluted wall panels ---------------------------------------------------- #
# 1.20 m bay measures 110 px at 1080p / 220 px at 4K on the back wall from
# FrontQuarter, so the light/dark cycle is nowhere near Nyquist and cannot alias
# into a shimmering picket. The 30 mm chamfers are what keep it from doing so at
# the fin itself: they turn a 2-tone edge into a 3-tone one 20 px wide.
FLUTE_BAY = 1.20
FLUTE_W = 0.130        # flat fin face
FLUTE_D = 0.100        # fin projection past the panel field
FLUTE_CHAMFER = 0.030
PANEL_STANDOFF = 0.040  # panel field proud of the structural wall face, so a
                        # reveal can cut 30 mm back and still stay 10 mm clear
PANEL_BASE_GAP = 0.035  # floor shadow gap depth
PANEL_REVEAL = 0.030
PANEL_REVEAL_H = 0.030
PANEL_GAP_TOP = 0.090   # top of the floor shadow gap
PANEL_GAP_LIP = 0.110   # where the panel steps back out to full projection
PANEL_BOTTOM = -0.020   # buried in the floor slab (top z = 0.0)
PANEL_TOP = 6.220       # buried in the ceiling slab (underside z = 6.2)
PANEL_UPPER_REVEAL_Z = 4.600
LIGHT_BAND = (1.80, 3.00)   # see the module docstring

# --- floor datum ------------------------------------------------------------ #
# r = 7.30 sits 0.20 m outside the bollard practicals s05 puts at r = 6.95
# (rings out to 7.10), so the ring reads as the line those bollards stand on.
# A second ring further out was designed and dropped: at r = 9.8-10.6 it runs
# within 0.1 m of s05's FloorGraze lamp and straight through the mirrored streak
# that lamp exists to make, at (3.2, -9.3).
FLOOR_RING_R = 7.300
FLOOR_RING_W = 0.030
# 0.30 m, not the 0.60 first drawn: s07's FlightCase_Stencil starts at r = 7.641
# and its floor decals sit at z = +-0.002, inside these strips' 7 mm section.
FLOOR_TICK_LEN = 0.300
FLOOR_TICK_W = 0.040
# Camera azimuths are -37.2 (FrontQuarter), -31.2 (HeroLow) and +142.0
# (RearQuarter) degrees; every tick below is at least 25 deg off all three.
FLOOR_TICK_AZ = (15.0, 75.0, 105.0, 195.0, 255.0, 285.0)
INLAY_PROUD = 0.003
INLAY_SINK = 0.004     # sunk below the host surface so no face is ever coplanar


def _coll():
    return C.collection("SHOWROOM")


# --------------------------------------------------------------------------- #
# materials this module owns
# --------------------------------------------------------------------------- #

def _mine(name):
    """True if this module may (re)build the material called `name`.

    s03_materials owns the shared registry and rebuild_scene runs it first, so
    anything the registry defines has to win: if SHOWROOM later grows its own
    WallBackX, clobbering it from here would silently replace a tuned tree with
    the fallback below. The marker distinguishes "s02 built this last run" from
    "s03 built this a moment ago".
    """
    mat = bpy.data.materials.get(name)
    return mat is None or mat.get("built_by") == "s02_showroom"


def wall_dark(name, ramp, rough):
    """Dark wall with a vertical luminance ramp, in OBJECT coordinates.

    Both solid walls shared one flat WallDark, so the corner where they meet
    read as a shading gradient and nothing else - the measured 0.0403 standard
    deviation over 643 k pixels. Splitting the material and giving each wall its
    own ramp turns that corner into a real tonal edge and gives each wall a
    direction, at zero polygon and zero render cost.

    `ramp` is albedo at z = 0 / z = 3.5 / z = CEIL_Z. Means are held within a few
    percent of the old 0.044 flat value on purpose: the fix for a dead wall is
    more variance at the same mean, not a brighter wall, and s05's clipping
    analysis is quoted against a 0.042 albedo. The ramp peak stays under 0.06 so
    the wall never starts competing with the dais.

    Object coordinates, not Generated: Generated normalises to each object's own
    bounding box, and the wall box, its two flute panels and the opposite wall
    all have different extents, so a Generated ramp would step at every join.
    Everything here is built from world coordinates and never transformed, so
    Object space is world space and the ramp is continuous across all of them.
    """
    if not _mine(name):
        return bpy.data.materials[name]
    mat, nt, b = C.material(name)
    mat["built_by"] = "s02_showroom"
    C.set_defaults(b, Base_Color=(ramp[1],) * 3 + (1.0,), Metallic=0.0,
                   Roughness=rough)

    texco = C.node(nt, "ShaderNodeTexCoord", (-1240, 0))
    sep = C.node(nt, "ShaderNodeSeparateXYZ", (-1060, 200))
    C.wire(nt, texco, "Object", sep, "Vector")
    height = C.node(nt, "ShaderNodeMapRange", (-880, 200))
    C.set_defaults(height, From_Min=0.0, From_Max=CEIL_Z, To_Min=0.0, To_Max=1.0)
    height.clamp = True
    C.wire(nt, sep, "Z", height, "Value")

    grad = C.node(nt, "ShaderNodeValToRGB", (-680, 200))
    el = grad.color_ramp.elements
    el[0].position = 0.0
    el[0].color = (ramp[0],) * 3 + (1.0,)
    el[1].position = 3.5 / CEIL_Z
    el[1].color = (ramp[1],) * 3 + (1.0,)
    top = grad.color_ramp.elements.new(1.0)
    top.color = (ramp[2],) * 3 + (1.0,)
    C.wire(nt, height, "Result", grad, "Fac")

    # Two noise scales, both as multipliers rather than colours: a ColorRamp
    # element clamps to 1.0, so a ramp cannot express "12 % brighter".
    fine = C.node(nt, "ShaderNodeTexNoise", (-880, -60))
    C.set_defaults(fine, Scale=14.0, Detail=4.0, Roughness=0.6)
    C.wire(nt, texco, "Object", fine, "Vector")
    fine_v = C.node(nt, "ShaderNodeMapRange", (-680, -60))
    C.set_defaults(fine_v, From_Min=0.30, From_Max=0.70, To_Min=0.82, To_Max=1.18)
    fine_v.clamp = True
    C.wire(nt, fine, "Fac", fine_v, "Value")

    # very large scale: panel-batch variation, +-8 % over ~8 m
    batch = C.node(nt, "ShaderNodeTexNoise", (-880, -320))
    C.set_defaults(batch, Scale=0.8, Detail=2.0, Roughness=0.5)
    C.wire(nt, texco, "Object", batch, "Vector")
    batch_v = C.node(nt, "ShaderNodeMapRange", (-680, -320))
    C.set_defaults(batch_v, From_Min=0.35, From_Max=0.65, To_Min=0.92, To_Max=1.08)
    batch_v.clamp = True
    C.wire(nt, batch, "Fac", batch_v, "Value")

    m1 = C.node(nt, "ShaderNodeMix", (-440, 100), data_type="RGBA",
                blend_type="MULTIPLY")
    m1.inputs["Factor"].default_value = 1.0
    C.wire(nt, grad, "Color", m1, 6)
    C.wire(nt, fine_v, "Result", m1, 7)

    m2 = C.node(nt, "ShaderNodeMix", (-240, 40), data_type="RGBA",
                blend_type="MULTIPLY")
    m2.inputs["Factor"].default_value = 1.0
    C.wire(nt, m1, 2, m2, 6)
    C.wire(nt, batch_v, "Result", m2, 7)
    C.wire(nt, m2, 2, b, "Base Color")
    return mat


def plinth_base(name="PlinthBase"):
    """Near-black matte for the dais skirt and the glazing base reveal.

    It must not be PlatformBody: tools/rebuild_scene.py rewrites that material's
    Base Color from --dais-albedo on every single rebuild, so a skirt sharing it
    would be dragged straight back to 0.40 and the whole point of the skirt -
    cutting the dais's bright area - would be silently undone.
    """
    if not _mine(name):
        return bpy.data.materials[name]
    mat, nt, b = C.material(name)
    mat["built_by"] = "s02_showroom"
    C.set_defaults(b, Base_Color=(0.045, 0.046, 0.050, 1.0), Metallic=0.0,
                   Roughness=0.55)
    return mat


def inlay_steel(name="InlaySteel"):
    """Dark brushed steel for the floor and deck datum inlays.

    Deliberately dark and deliberately not a mirror. Both hosts are specular:
    the floor is near-mirror and r = 7.30 is where s05's bollard practicals
    reflect, and the deck is Metallic 0.86 directly under the car. For a metal
    the base colour IS the reflectance, so 0.115 caps the mirrored radiance of a
    bollard at roughly 2 against the ~5.6 at which this project's AgX transform
    starts clipping - the albedo, not the roughness, is what makes it safe.

    0.115 against the deck's 0.048 is also the quiet 2:1 step TopDown needs; a
    bright steel there would out-shout the car in the only frame the deck owns.
    """
    if not _mine(name):
        return bpy.data.materials[name]
    mat, nt, b = C.material(name)
    mat["built_by"] = "s02_showroom"
    C.set_defaults(b, Base_Color=(0.115, 0.117, 0.122, 1.0), Metallic=1.0,
                   Roughness=0.38)
    texco = C.node(nt, "ShaderNodeTexCoord", (-880, 0))
    mapn = C.node(nt, "ShaderNodeMapping", (-700, 0))
    mapn.inputs["Scale"].default_value = (90.0, 90.0, 90.0)
    C.wire(nt, texco, "Object", mapn, "Vector")
    n = C.node(nt, "ShaderNodeTexNoise", (-520, 0))
    C.set_defaults(n, Scale=1.0, Detail=2.0, Roughness=0.5)
    C.wire(nt, mapn, "Vector", n, "Vector")
    ramp = C.node(nt, "ShaderNodeValToRGB", (-320, 0))
    ramp.color_ramp.elements[0].position = 0.38
    ramp.color_ramp.elements[0].color = (0.32, 0.32, 0.32, 1.0)
    ramp.color_ramp.elements[1].position = 0.64
    ramp.color_ramp.elements[1].color = (0.46, 0.46, 0.46, 1.0)
    C.wire(nt, n, "Fac", ramp, "Fac")
    C.wire(nt, ramp, "Color", b, "Roughness")
    return mat


def build_materials():
    """Materials assigned only by this module. s03 still owns the registry."""
    return {
        # The side wall reads about 17 % lighter and 0.15 rougher than the back
        # wall, so the corner is a tonal edge rather than a shading accident.
        "WallBackX": wall_dark("WallBackX", (0.030, 0.052, 0.038), 0.70).name,
        "WallSideY": wall_dark("WallSideY", (0.036, 0.058, 0.045), 0.55).name,
        "PlinthBase": plinth_base().name,
        "InlaySteel": inlay_steel().name,
    }


# --------------------------------------------------------------------------- #
# mesh helpers
# --------------------------------------------------------------------------- #

def _add_prism(verts, faces, plan, z0, z1):
    """Append an extruded convex plan polygon to shared vert/face accumulators.

    The datum inlays are dozens of 25 mm strips; batching them into one mesh
    keeps the object count honest and the outliner readable.
    """
    n = len(plan)
    i = len(verts)
    verts += [(x, y, z0) for x, y in plan]
    verts += [(x, y, z1) for x, y in plan]
    faces.append(tuple(range(i, i + n))[::-1])
    faces.append(tuple(range(i + n, i + 2 * n)))
    for k in range(n):
        k2 = (k + 1) % n
        faces.append((i + k, i + k2, i + n + k2, i + n + k))


def _face_outward(ob, outward):
    """Force an open lofted sheet to face `outward` (a unit vector tuple).

    common.new_obj runs recalc_face_normals, which needs an inside and an
    outside to work from. A sheet has no volume, so its choice is arbitrary and
    it is not even consistent between two sheets built by the same call: of the
    four wall panels it oriented three into the room and the fourth into the
    wall. Nothing raises, and a Principled BSDF still renders - the panel just
    shades as though lit from behind, which is a dark band across half of
    FrontQuarter that only a render would reveal. Area-weighting the test makes
    the fin faces, which are the ones that matter, outvote the chamfers.
    """
    me = ob.data
    ox, oy, oz = outward
    signed = sum((p.normal[0] * ox + p.normal[1] * oy + p.normal[2] * oz) * p.area
                 for p in me.polygons)
    if signed < 0.0:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.update()
    return ob


# --------------------------------------------------------------------------- #
# floor
# --------------------------------------------------------------------------- #

def build_floor(coll):
    """Interior floor + a large, darker exterior ground seen through the glass."""
    f = C.box("Floor", -ROOM_X, ROOM_X, -ROOM_Y, ROOM_Y, -0.06, 0.0, coll=coll)
    C.assign(f, bpy.data.materials["FloorPolished"])

    g = C.box("ExteriorGround", -160, 160, -160, 160, -0.14, -0.08, coll=coll)
    mat, nt, b = C.material("ExteriorGround")
    C.set_defaults(b, Base_Color=(0.020, 0.021, 0.024, 1.0), Roughness=0.80)
    C.assign(g, mat)
    return f, g


def build_floor_datum(coll):
    """One concentric steel datum ring on the floor, with outward ticks.

    The floor was a single uniform mirror from the dais to the walls, so the dais
    read as a white disc floating on black glass with nothing tying the two
    together. A ring at r = 7.30 gives the floor a measurable radius and gives
    the reflections a boundary: FrontQuarter sees it as an arc across frame
    x = 11-95 % at y = 46-49 %, and RearQuarter picks it up at (66 %, 44 %).

    3 mm proud and sunk 4 mm into the slab. Never coplanar with the floor top -
    a flush inlay is an invitation to z-fight across the largest specular
    surface in the room, and the shader-mask version of this idea belongs to
    s03_materials, not here.
    """
    made = []
    steel = bpy.data.materials["InlaySteel"]
    half = FLOOR_RING_W * 0.5
    ring = C.revolve("Floor_Datum_Ring", [
        (FLOOR_RING_R - half, -INLAY_SINK), (FLOOR_RING_R - half, INLAY_PROUD),
        (FLOOR_RING_R + half, INLAY_PROUD), (FLOOR_RING_R + half, -INLAY_SINK)],
        segments=192, coll=coll, smooth=False, auto_smooth=None)
    C.assign(ring, steel)
    made.append(ring)

    verts, faces = [], []
    hw = FLOOR_TICK_W * 0.5
    r0 = FLOOR_RING_R + half
    r1 = r0 + FLOOR_TICK_LEN
    for az in FLOOR_TICK_AZ:
        a = math.radians(az)
        ca, sa = math.cos(a), math.sin(a)
        plan = [(r * ca - t * sa, r * sa + t * ca)
                for r, t in ((r0, -hw), (r1, -hw), (r1, hw), (r0, hw))]
        _add_prism(verts, faces, plan, -INLAY_SINK, INLAY_PROUD)
    ticks = C.new_obj("Floor_Datum_Ticks", verts, faces, coll=coll, smooth=False)
    C.assign(ticks, steel)
    made.append(ticks)
    return made


# --------------------------------------------------------------------------- #
# shell + fluted wall panels
# --------------------------------------------------------------------------- #

def _flute_plan(length, u_offset, bay, fin_w, fin_d, chamfer, standoff):
    """Plan polyline of one wall run in (along, out-of-wall) metres.

    Four points per fin: field -> chamfer out -> fin face -> chamfer back. The
    field spans come free from the gaps between them.

    Fins sit on ONE global grid per wall, `u_offset` metres from the run's start
    back to the wall's anchor, rather than being spread evenly over whatever
    length each run happens to have. The runs are interrupted in several places
    by other modules' fixtures, and dividing each fragment's own length into
    bays would give every fragment a slightly different pitch - three visibly
    different rhythms stacked up the same wall.
    """
    width = 2.0 * chamfer + fin_w
    if width >= bay:
        raise ValueError(f"fin {width:.3f} m does not fit a {bay:.3f} m bay")
    pts = [(0.0, standoff)]
    k = int(math.ceil(u_offset / bay))
    while True:
        u = k * bay - u_offset
        if u >= length:
            break
        if u >= 0.0 and u + width <= length:
            pts += [(u, standoff), (u + chamfer, standoff + fin_d),
                    (u + chamfer + fin_w, standoff + fin_d),
                    (u + width, standoff)]
        k += 1
    pts.append((length, standoff))
    # A fin landing exactly on a run end would duplicate a point, and C.loft
    # would happily build a ring of zero-area quads out of it.
    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) > 1e-9 or abs(p[1] - out[-1][1]) > 1e-9:
            out.append(p)
    return out


def _panel_stations(z0, z1, base_gap=False, reveal_z=(), cap_top=False):
    """(z, inset, flatten) rings for one panel, bottom to top.

    Reveals are FOUR rings, not two: a pair of rings sharing a z is what makes
    a 30 mm step instead of a metre-and-a-half-long taper, because a loft
    between two rings at different depths is a ramp, not a shoulder.
    """
    st = []
    if base_gap:
        st += [(z0, PANEL_BASE_GAP, False),
               (PANEL_GAP_TOP, PANEL_BASE_GAP, False),
               (PANEL_GAP_LIP, 0.0, False)]
    else:
        st.append((z0, 0.0, False))
    for z in reveal_z:
        st += [(z, 0.0, False), (z, PANEL_REVEAL, False),
               (z + PANEL_REVEAL_H, PANEL_REVEAL, False),
               (z + PANEL_REVEAL_H, 0.0, False)]
    st.append((z1, 0.0, False))
    if cap_top:
        # fold the sheet flat onto the structural wall face so the panel ends in
        # a head return instead of a zero-thickness top edge
        st.append((z1, 0.0, True))
    return st


def flute_panel(name, p0, p1, outward, anchor, stations, coll, mat,
                bay=FLUTE_BAY):
    """A run of vertical fins swept up through `stations`.

    p0 -> p1 are the run's endpoints in plan and `outward` is the unit direction
    into the room. The two are given independently rather than deriving one from
    the other: the runs have to be ordered so that u increases away from
    `anchor` to keep the fin grid in phase, and that ordering does not always
    agree with the winding the normal would otherwise come from.

    Flat-shaded on purpose. Every face here is planar and every edge between
    them turns through 73 deg or more, so auto-smoothing would mark all of them
    sharp anyway and only cost a bmesh pass. The three tones inside each fin -
    field, lit chamfer, shadowed chamfer - are the whole effect.
    """
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    nx, ny = outward

    plan = _flute_plan(length, math.dist(anchor, p0), bay, FLUTE_W, FLUTE_D,
                       FLUTE_CHAMFER, PANEL_STANDOFF)
    rings = []
    for z, inset, flat in stations:
        ring = []
        for u, n in plan:
            # the clamp is a guard, not a working value: at standoff 0.040 the
            # deepest inset in use leaves 5 mm of clearance
            d = 0.0 if flat else max(n - inset, 0.004)
            ring.append((x0 + ux * u + nx * d, y0 + uy * u + ny * d, z))
        rings.append(ring)

    verts, faces = C.loft(rings, closed=False)
    ob = C.new_obj(name, verts, faces, coll=coll, smooth=False)
    _face_outward(ob, (nx, ny, 0.0))
    C.assign(ob, mat)
    return ob


def build_shell(coll):
    """Two solid walls (-X feature wall, +Y side wall) plus the ceiling slab."""
    made = []
    w1 = C.box("Wall_BackX", -ROOM_X - WALL_T, -ROOM_X, -ROOM_Y - WALL_T, ROOM_Y + WALL_T,
               0.0, CEIL_Z, coll=coll)
    C.assign(w1, bpy.data.materials["WallBackX"])
    w2 = C.box("Wall_SideY", -ROOM_X - WALL_T, ROOM_X + WALL_T, ROOM_Y, ROOM_Y + WALL_T,
               0.0, CEIL_Z, coll=coll)
    C.assign(w2, bpy.data.materials["WallSideY"])
    made += [w1, w2]

    ceil = C.box("Ceiling", -ROOM_X - WALL_T, ROOM_X + WALL_T,
                 -ROOM_Y - WALL_T, ROOM_Y + WALL_T, CEIL_Z, CEIL_Z + 0.30, coll=coll)
    C.assign(ceil, bpy.data.materials["CeilingMat"])
    made.append(ceil)
    made += build_wall_panels(coll)
    return made


def build_wall_panels(coll):
    """Fluted panels over both solid walls, split around s05's light line.

    Frame positions, measured, of every horizontal this creates:

        z          FrontQuarter        HeroLow        keep-out band
        0.110      33.3 - 41.6 %       49.9 - 52.0 %  FQ 27-36, HL 18-26
        1.800      18.9 - 19.3 %       33.9 - 37.7 %
        3.000       5.5 -  8.5 %       21.0 - 29.0 %
        4.600      off frame            3.3 - 17.4 %

    The keep-out bands are where a horizontal line would run tangent to the
    car's silhouette (FrontQuarter 31.1 %, HeroLow 22.1 %) and read as a
    mistake. Every line above clears FrontQuarter's band, which is the one that
    matters: FrontQuarter's wall lines vary by under 0.5 % of frame height
    across the whole width, so they really are horizontal. HeroLow's sweep 6-8 %
    across the frame - the 3.00 m panel base runs 21.0 to 29.0 % - so it reads
    as a converging diagonal behind the subject, not as a tangent.

    z = 0.110 is the exception and it is not optional: the wall meets the floor
    at 34-42 % whatever happens, so that line already exists. The 35 mm shadow
    gap only gives the junction a thickness of about 11 px.

    WHERE THE UPPER RUN STOPS, AND WHY
    ----------------------------------
    Everything other modules hang on these walls lives between z = 2.6 and 3.8,
    which is signage height. Measured off the built scene, not guessed:

        s05 WallLine_*    both walls                    z 2.35 .. 2.53
        s07 WallSign_*    back wall  y  4.10 ..  6.70   z 2.62 .. 3.15
        s07 Gantry_*      back wall  y  7.19 ..  8.01   z 2.70 .. 3.78

    The last two project 136-190 mm off the wall, past this panel's own 140 mm
    fin tips, so the upper back-wall run stops at y = 0.90 and leaves that half
    of the wall to them. Below z = 1.80 nothing is contested on either wall and
    the lower runs go the full length - which is the band that pays anyway, at
    FrontQuarter frame 19-31 % against the upper run's 1.4-8 %.

    s02 builds third of six and s07 sixth, so s07 can inspect what is here and
    this module cannot inspect s07. The convention that follows is that the
    architecture is built first and the dressing is placed clear of it; these
    bounds exist only to avoid what already existed at the time of writing, and
    a room-only rebuild is 0.5 s if they need re-measuring.
    """
    made = []
    lo, hi = LIGHT_BAND
    back = bpy.data.materials["WallBackX"]
    side = bpy.data.materials["WallSideY"]
    corner = (-ROOM_X, ROOM_Y)
    lower = _panel_stations(PANEL_BOTTOM, lo, base_gap=True, cap_top=True)
    upper = [(hi, 0.0, True)] + _panel_stations(
        hi, PANEL_TOP, reveal_z=(PANEL_UPPER_REVEAL_Z,))

    # Every run is ordered so u grows away from the room corner, which is what
    # keeps one 1.20 m fin grid running continuously through all of them and
    # symmetrical about the corner itself. Ends stop clear of the curtain-wall
    # end mullions (within 75 mm of x = 15 and y = -11) so the sheet does not
    # shave past a mullion face by 2 mm.
    runs = [
        ("Wall_BackX_FluteLo", (-ROOM_X, ROOM_Y), (-ROOM_X, -ROOM_Y + 0.20),
         (1.0, 0.0), back, lower),
        ("Wall_BackX_FluteHi", (-ROOM_X, 0.90), (-ROOM_X, -ROOM_Y + 0.20),
         (1.0, 0.0), back, upper),
        ("Wall_SideY_FluteLo", (-ROOM_X + 0.15, ROOM_Y), (ROOM_X - 0.20, ROOM_Y),
         (0.0, -1.0), side, lower),
        ("Wall_SideY_FluteHi", (-ROOM_X + 0.15, ROOM_Y), (ROOM_X - 0.20, ROOM_Y),
         (0.0, -1.0), side, upper),
    ]
    for name, p0, p1, outward, mat, stations in runs:
        made.append(flute_panel(name, p0, p1, outward, corner, stations,
                                coll, mat))
    return made


# --------------------------------------------------------------------------- #
# glazing
# --------------------------------------------------------------------------- #

def curtain_wall(name, p0, p1, z0, z1, coll, panel_w=2.0,
                 mull_w=0.075, mull_d=0.16, rail_h=0.11,
                 transom_z=(1.35, 2.85, 4.35), reveal_h=0.055, reveal_back=0.045,
                 bar_u0=0.0):
    """A run of glass panes with aluminium mullions, transoms and rails.

    p0/p1 are (x, y) endpoints in plan; panes are vertical.

    RearQuarter's whole background is this glazing and it was a bare vertical
    grid - a fence, not a facade. The transoms put horizontal architecture
    across it at measured frame heights of 23.2 % / 22.2 % (z = 1.35), 6.7 % /
    8.2 % (z = 2.85) and off frame (z = 4.35) for the front and right runs. The
    car's silhouette tops out at 18.2 %, so the lower transom passes behind the
    body and is interrupted by it, which reads as depth rather than as a line
    grazing the subject.

    The panes are deliberately NOT split at the transoms. Thin-wall glass has no
    thickness and no visible edge, so subdividing one quad into four changes
    nothing a camera can see while quadrupling the pane count that
    transmission_bounces = 32 has to walk. The transoms interpenetrate the glass
    exactly as the existing vertical mullions already do.
    """
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux                      # in-plane normal

    n_panels = max(1, int(round(length / panel_w)))
    step = length / n_panels
    glass_mat = bpy.data.materials["GlassPanel"]
    alu = bpy.data.materials["MullionAlu"]
    made = []

    def bar(tag, rz0, rz1, half_depth, mat, bevel):
        """One horizontal member spanning the run, less any bar_u0 inset."""
        v = []
        for zz in (rz0, rz1):
            for (su, sn) in ((bar_u0, -half_depth), (length, -half_depth),
                             (length, half_depth), (bar_u0, half_depth)):
                v.append((x0 + ux * su + nx * sn, y0 + uy * su + ny * sn, zz))
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
             (2, 3, 7, 6), (3, 0, 4, 7)]
        ob = C.new_obj(f"{name}_{tag}", v, f, coll=coll, smooth=False)
        C.assign(ob, mat)
        if bevel:
            C.add_bevel(ob, width=bevel, segments=2)
        made.append(ob)
        return ob

    # panes
    for i in range(n_panels):
        a = i * step + mull_w * 0.5
        b = (i + 1) * step - mull_w * 0.5
        pa = (x0 + ux * a, y0 + uy * a)
        pb = (x0 + ux * b, y0 + uy * b)
        v = [(pa[0], pa[1], z0 + rail_h), (pb[0], pb[1], z0 + rail_h),
             (pb[0], pb[1], z1 - rail_h), (pa[0], pa[1], z1 - rail_h)]
        ob = C.new_obj(f"{name}_Glass_{i:02d}", v, [(0, 1, 2, 3)], coll=coll, smooth=False)
        C.assign(ob, glass_mat)
        made.append(ob)

    # vertical mullions (one per join, plus the two ends)
    for i in range(n_panels + 1):
        a = i * step
        cx, cy = x0 + ux * a, y0 + uy * a
        hw, hd = mull_w * 0.5, mull_d * 0.5
        v = []
        for (su, sn) in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)):
            v.append((cx + ux * su + nx * sn, cy + uy * su + ny * sn, z0))
        for (su, sn) in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)):
            v.append((cx + ux * su + nx * sn, cy + uy * su + ny * sn, z1))
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        ob = C.new_obj(f"{name}_Mull_{i:02d}", v, f, coll=coll, smooth=False)
        C.assign(ob, alu)
        C.add_bevel(ob, width=0.004, segments=2)
        made.append(ob)

    # head and sill rails; the sill now lands on a recessed base channel
    bar("Sill", z0 + reveal_h, z0 + rail_h, mull_d * 0.5, alu, 0.005)
    bar("Head", z1 - rail_h, z1, mull_d * 0.5, alu, 0.005)
    if reveal_h > 0.0:
        bar("BaseReveal", z0, z0 + reveal_h, mull_d * 0.5 - reveal_back,
            bpy.data.materials["PlinthBase"], 0.0)

    for i, tz in enumerate(transom_z):
        if not (z0 + rail_h < tz - mull_w * 0.5 and tz + mull_w * 0.5 < z1 - rail_h):
            continue                      # would collide with a rail
        bar(f"Transom_{i}", tz - mull_w * 0.5, tz + mull_w * 0.5,
            mull_d * 0.5, alu, 0.004)
    return made


def build_glass(coll):
    """Front and right glazing runs, meeting at the (15, -11) corner.

    The front run owns the corner and the right run's horizontal members start
    1 mm clear of it. Both runs' sills, transoms and base reveals are 0.16 m
    deep, so left to span their full length they would overlap in an 80 mm patch
    with coplanar top AND bottom faces - three exposed z-fights in mid-air at a
    corner both RearQuarter and the floor reflection can see. Same fix, and the
    same 1 mm, that s05_lighting uses where its two wall lines meet.
    """
    made = []
    made += curtain_wall("GW_Front", (-ROOM_X, -ROOM_Y), (ROOM_X, -ROOM_Y),
                         0.0, CEIL_Z, coll, panel_w=2.14)
    made += curtain_wall("GW_Right", (ROOM_X, -ROOM_Y), (ROOM_X, ROOM_Y),
                         0.0, CEIL_Z, coll, panel_w=2.20, bar_u0=0.081)
    return made


# --------------------------------------------------------------------------- #
# platform + turntable
# --------------------------------------------------------------------------- #

def build_platform(coll):
    """Dais with a recessed well; the turntable deck sits proud inside it.

    The dais used to be a solid white drum sitting flat on the floor, and in
    RearQuarter its flank is the largest bright surface in frame. Three edits
    give it a plinth's silhouette instead of a bathtub's:

      * the skirt steps 55 mm back below z = 0.062 and the body overhangs it, so
        the drum reads as floating on a shadow gap rather than resting on the
        floor. Measured at FrontQuarter frame 52.1-53.6 %, RearQuarter 50.2-51.6 %;
      * that skirt band is a separate material slot, which cuts the bright flank
        by 38 % - the surface s05 still measures at 0.434 % clipped;
      * a 12 mm undercut at z = 0.166 separates the flank panel from the rim cap.

    The skirt cannot share PlatformBody: rebuild_scene.py rewrites that
    material's Base Color from --dais-albedo on every run. A second material
    SLOT rather than a second object also avoids putting two surfaces in the
    same place at the base of the frame's brightest object.
    """
    dais_profile = [
        (0.000, 0.000), (2.600, 0.000), (3.400, 0.000), (3.645, 0.000),
        (3.645, 0.062),                                  # recessed skirt face
        (3.700, 0.082),                                  # overhang casting the gap
        (3.700, 0.166), (3.688, 0.166), (3.688, 0.178),  # top-edge undercut
        (3.700, 0.180), (3.697, 0.232), (3.684, 0.264),
        (3.661, 0.286), (3.630, 0.297), (3.596, 0.300), (3.560, 0.300),
        (3.534, 0.299), (3.518, 0.293), (3.510, 0.280), (3.508, 0.250),
        (3.508, 0.130), (3.492, 0.110), (3.440, 0.100), (3.100, 0.100),
        (1.800, 0.100), (0.000, 0.100),
    ]
    dais = C.revolve("Platform_Dais", dais_profile, segments=192, coll=coll,
                     auto_smooth=26.0)
    C.assign(dais, bpy.data.materials["PlatformBody"])
    C.assign(dais, bpy.data.materials["PlinthBase"], slot=1)
    for p in dais.data.polygons:
        cx, cy, cz = p.center
        if cz < 0.075 and math.hypot(cx, cy) > 3.40:
            p.material_index = 1

    # A 16 x 4 mm perimeter groove was cut here at r = 3.20 to give CAM_TopDown
    # a datum, and has been taken back out: s07_props now builds Deck_DatumRing,
    # a proud ring at r = 3.180-3.220, in exactly that place. A recess and a
    # boss at the same radius means their ring bridges this groove and floats
    # 2 mm over its floor. The deck profile is deliberately back to stock.
    tt_profile = [
        (0.000, 0.118), (1.800, 0.118), (3.200, 0.118), (3.404, 0.119),
        (3.440, 0.128), (3.450, 0.146), (3.450, 0.300), (3.448, 0.318),
        (3.440, 0.330), (3.424, 0.338), (3.402, 0.340), (3.200, 0.340),
        (1.800, 0.340), (0.000, 0.340),
    ]
    tt = C.revolve("Turntable_Deck", tt_profile, segments=192, coll=coll,
                   auto_smooth=26.0)
    C.assign(tt, bpy.data.materials["TurntableTop"])
    # real turntables creep; a few degrees keeps the brushed grain off-axis
    tt.rotation_euler[2] = math.radians(TT_ROT_DEG)

    # glow strip hidden in the 5.8 cm seam between deck and dais
    seam_profile = [(3.487, 0.150), (3.487, 0.285)]
    seam = C.revolve("Turntable_SeamGlow", seam_profile, segments=192, coll=coll,
                     auto_smooth=None, smooth=True)
    C.assign(seam, bpy.data.materials["SeamEmit"])
    seam.visible_shadow = False
    return dais, tt, seam


# --------------------------------------------------------------------------- #

def build():
    coll = _coll()
    C.purge_collection("SHOWROOM")
    coll = C.collection("SHOWROOM")
    M.build_showroom_materials()
    build_materials()

    build_floor(coll)
    build_floor_datum(coll)
    build_shell(coll)
    build_glass(coll)
    build_platform(coll)

    return {
        "objects": len(coll.objects),
        "polys": sum(len(o.data.polygons) for o in coll.objects
                     if o.type == "MESH"),
        "tt_top": TT_TOP,
        "names": sorted({o.name.rsplit("_", 1)[0] for o in coll.objects}),
    }
