"""The F1 car: 2024-spec ground-effect single seater, real dimensions in metres.

    wheelbase          3.600
    overall length     5.63   (nose tip x=+3.00 .. rear wing TE x=-2.63)
    overall width      2.000  (tyre outer faces at y=+/-1.000)
    tyre diameter      0.720   front width 0.305, rear width 0.405
    rim                18 in  (0.4572 dia)
    roll hoop top      ~0.95 above the reference plane

The monocoque is ONE lofted manifold rather than a pile of overlapping solids, so
there are no intersection seams to show up at the silhouette. Each station is a
closed section built from a 7-point half profile:

    belly centre -> belly edge -> undercut waist -> sidepod max -> sidepod
    shoulder -> tub side -> tub shoulder -> centre top

The undercut point sits *inboard* of the sidepod point, which is what gives the
section its concave ground-effect waist. The cockpit is not a separate part: for
stations over the opening the centre-top z is pushed BELOW the tub shoulder z, so
the section carries a real trough and the surface stays manifold.
"""

import math

import bpy

import common as C

GROUND = 0.340          # turntable deck top = tyre contact plane

FRONT_AXLE = 1.80
REAR_AXLE = -1.80
TYRE_R = 0.360
RIM_R = 0.2286
FRONT_HW = 0.1525       # half width, 305 mm
REAR_HW = 0.2025        # half width, 405 mm
FRONT_Y = 1.000 - FRONT_HW
REAR_Y = 1.000 - REAR_HW

# x, bw, bz, uw, uz, pw, pz, ptw, ptz, tw, tz, ttw, ttz, ctz
BODY_STATIONS = [
    # D012: the tip started 36 mm wide, which rendered as a needle. The FIA
    # crash structure makes a real nose tip ~150 mm wide and ~130 mm tall.
    (3.000, 0.062, 0.232, 0.072, 0.252, 0.078, 0.282, 0.074, 0.312, 0.064, 0.332, 0.038, 0.346, 0.356),
    (2.820, 0.082, 0.220, 0.096, 0.246, 0.106, 0.280, 0.100, 0.314, 0.086, 0.338, 0.050, 0.354, 0.366),
    (2.600, 0.104, 0.206, 0.122, 0.238, 0.136, 0.276, 0.128, 0.314, 0.110, 0.342, 0.062, 0.360, 0.374),
    (2.340, 0.126, 0.190, 0.150, 0.234, 0.168, 0.282, 0.158, 0.330, 0.136, 0.364, 0.076, 0.384, 0.398),
    (2.060, 0.132, 0.166, 0.168, 0.232, 0.196, 0.296, 0.186, 0.356, 0.152, 0.396, 0.084, 0.420, 0.434),
    (1.780, 0.162, 0.136, 0.204, 0.236, 0.238, 0.316, 0.226, 0.388, 0.186, 0.436, 0.104, 0.464, 0.480),
    (1.500, 0.188, 0.098, 0.236, 0.238, 0.276, 0.334, 0.262, 0.418, 0.216, 0.474, 0.122, 0.506, 0.524),
    (1.220, 0.212, 0.074, 0.264, 0.240, 0.310, 0.352, 0.294, 0.446, 0.244, 0.510, 0.138, 0.546, 0.566),
    # D022: the cockpit trough ramped in from x=0.96 over 0.9 m, which read in
    # plan as a long pointed almond instead of an opening. It now starts abruptly
    # at x=0.78 and the tub shoulder widens so the aperture is ~0.46 m across,
    # which is what a real cockpit opening measures.
    # D021: sidepods likewise blended in far too gradually - real pods have a
    # distinct inlet face around x=0.75 and a much harder coke-bottle taper.
    (0.960, 0.234, 0.064, 0.290, 0.242, 0.330, 0.370, 0.300, 0.470, 0.268, 0.542, 0.170, 0.582, 0.598),
    (0.780, 0.250, 0.060, 0.314, 0.244, 0.470, 0.384, 0.420, 0.488, 0.282, 0.566, 0.198, 0.596, 0.580),
    (0.560, 0.268, 0.058, 0.350, 0.246, 0.640, 0.396, 0.560, 0.504, 0.294, 0.586, 0.222, 0.610, 0.522),
    (0.340, 0.286, 0.056, 0.398, 0.248, 0.706, 0.406, 0.616, 0.516, 0.302, 0.602, 0.232, 0.622, 0.506),
    (0.120, 0.298, 0.056, 0.430, 0.250, 0.720, 0.412, 0.628, 0.524, 0.308, 0.614, 0.234, 0.632, 0.502),
    (-0.100, 0.304, 0.056, 0.442, 0.250, 0.718, 0.414, 0.626, 0.526, 0.310, 0.622, 0.228, 0.646, 0.540),
    (-0.190, 0.304, 0.056, 0.442, 0.250, 0.716, 0.414, 0.622, 0.526, 0.308, 0.634, 0.178, 0.700, 0.742),
    (-0.270, 0.304, 0.056, 0.440, 0.250, 0.714, 0.413, 0.620, 0.525, 0.307, 0.650, 0.177, 0.762, 0.898),
    (-0.360, 0.303, 0.056, 0.437, 0.250, 0.710, 0.412, 0.616, 0.523, 0.305, 0.662, 0.175, 0.800, 0.936),
    (-0.560, 0.298, 0.056, 0.422, 0.248, 0.686, 0.406, 0.592, 0.514, 0.294, 0.672, 0.168, 0.790, 0.892),
    (-0.820, 0.286, 0.056, 0.394, 0.246, 0.624, 0.394, 0.536, 0.498, 0.280, 0.640, 0.158, 0.740, 0.834),
    (-1.080, 0.268, 0.056, 0.350, 0.242, 0.470, 0.376, 0.408, 0.474, 0.262, 0.592, 0.146, 0.678, 0.766),
    (-1.340, 0.244, 0.056, 0.298, 0.236, 0.330, 0.350, 0.292, 0.440, 0.238, 0.532, 0.132, 0.604, 0.690),
    (-1.600, 0.214, 0.058, 0.248, 0.226, 0.238, 0.318, 0.216, 0.398, 0.208, 0.466, 0.114, 0.526, 0.606),
    (-1.840, 0.178, 0.060, 0.202, 0.212, 0.242, 0.282, 0.224, 0.350, 0.172, 0.398, 0.094, 0.446, 0.512),
    (-2.060, 0.138, 0.062, 0.154, 0.196, 0.178, 0.246, 0.166, 0.298, 0.132, 0.334, 0.072, 0.372, 0.412),
    (-2.240, 0.098, 0.066, 0.108, 0.178, 0.122, 0.212, 0.114, 0.250, 0.092, 0.276, 0.050, 0.302, 0.324),
    (-2.380, 0.058, 0.072, 0.064, 0.148, 0.070, 0.170, 0.066, 0.192, 0.054, 0.208, 0.030, 0.226, 0.238),
    (-2.470, 0.022, 0.082, 0.024, 0.116, 0.026, 0.128, 0.024, 0.138, 0.020, 0.146, 0.011, 0.156, 0.162),
]


# Single source of truth: parts are placed with spec.body_surface_point(), which
# reads spec.BODY_STATIONS. If this module kept its own copy they could drift and
# every surface-mounted part would float off the skin. Verified identical before
# this override was added, so the geometry is unchanged.
import spec as S  # noqa: E402
BODY_STATIONS = S.BODY_STATIONS
station_half = S.station_half


def _coll():
    return C.collection("CAR")


def station_half(st):
    """7-point half profile, bottom centre -> outboard -> top centre."""
    (_x, bw, bz, uw, uz, pw, pz, ptw, ptz, tw, tz, ttw, ttz, ctz) = st
    return [
        (0.0, bz),
        (bw, bz),
        (uw, uz),
        (pw, pz),
        (ptw, ptz),
        (tw, tz),
        (ttw, ttz),
        (0.0, ctz),
    ]


def build_body(coll, samples=47, lengthwise=94):
    """Loft the body.

    D120: at 25 stations x 33 half-samples the surface is smooth enough in
    silhouette but far too coarse for a 0.028-roughness clearcoat - straight
    lines reflected in the flank broke into visible stair-steps. Reflections
    magnify facet size, so the mesh has to be denser than the shape alone needs.
    The whole 14-component station tuple is Catmull-Rom interpolated (x included,
    so uneven station spacing stays smooth) before any ring is built.
    """
    dense = C.catmull_rom(BODY_STATIONS, lengthwise)
    rings = [C.ring_from_half(st[0], station_half(st), samples=samples)
             for st in dense]
    verts, faces = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = C.new_obj("Car_Body", verts, faces, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-5)
    # D058: at 42 deg the nearly-flat nose deck had edges marked sharp, which
    # showed as a bright crease running down the spine. The body is one smooth
    # skin - only genuinely hard folds should break.
    C.shade_auto_smooth(ob, 62.0)
    return ob


def build_floor(coll):
    """Flat ground-effect floor with edge fences and a rising rear diffuser."""
    # (x, half width, z at inner, z at outer edge)
    plan = [
        (1.560, 0.300, 0.050, 0.062),
        (1.300, 0.470, 0.048, 0.060),
        (1.000, 0.640, 0.046, 0.058),
        (0.600, 0.780, 0.044, 0.056),
        (0.100, 0.860, 0.043, 0.055),
        (-0.500, 0.885, 0.043, 0.055),
        (-1.100, 0.880, 0.044, 0.058),
        (-1.500, 0.845, 0.052, 0.070),
        (-1.800, 0.780, 0.082, 0.104),
        (-2.050, 0.700, 0.132, 0.156),
        (-2.230, 0.630, 0.180, 0.204),
    ]
    rows_top, rows_bot = [], []
    for x, hw, zi, zo in plan:
        top, bot = [], []
        n = 9
        for i in range(n):
            t = i / (n - 1)
            y = -hw + 2 * hw * t
            edge = abs(y) / hw if hw else 0.0
            z = zi + (zo - zi) * (edge ** 2.2)
            top.append((x, y, z))
            bot.append((x, y, z - 0.016))
        rows_top.append(top)
        rows_bot.append(bot)

    verts, faces = [], []

    def add_sheet(rows, flip):
        base = len(verts)
        v, f = C.grid_surface(rows)
        verts.extend(v)
        for q in f:
            q = tuple(i + base for i in q)
            faces.append(q[::-1] if flip else q)
        return base

    top_base = add_sheet(rows_top, False)
    bot_base = add_sheet(rows_bot, True)

    n = len(rows_top[0])
    rowsN = len(rows_top)
    # stitch the rim all the way round so the plate is a closed solid
    for i in range(rowsN - 1):
        for side, j in ((0, 0), (1, n - 1)):
            a0 = top_base + i * n + j
            a1 = top_base + (i + 1) * n + j
            b0 = bot_base + i * n + j
            b1 = bot_base + (i + 1) * n + j
            faces.append((a0, a1, b1, b0) if side == 0 else (a1, a0, b0, b1))
    for i, row_i in ((0, 0), (1, rowsN - 1)):
        for j in range(n - 1):
            a0 = top_base + row_i * n + j
            a1 = top_base + row_i * n + j + 1
            b0 = bot_base + row_i * n + j
            b1 = bot_base + row_i * n + j + 1
            faces.append((a1, a0, b0, b1) if i == 0 else (a0, a1, b1, b0))

    ob = C.new_obj("Car_Floor", verts, faces, coll=coll, smooth=False)
    C.merge_doubles(ob, 1e-5)
    C.shade_auto_smooth(ob, 30.0)
    return ob


def tyre_profile(hw):
    """Slick tyre cross-section: (radial, axial). Closed loop incl. the bore.

    D045: the first profile bulged to 1.05x half-width and only held full radius
    over the middle third, so it rendered as a doughnut. A real 18 in slick has a
    broad flat tread with defined shoulders and only a slight sidewall bulge.
    """
    sh = hw
    bulge = hw * 1.012
    return [
        (RIM_R, -sh),
        (RIM_R + 0.018, -sh - 0.002),
        (0.2740, -bulge),
        (0.3120, -bulge * 0.985),
        (0.3420, -sh * 0.950),
        (0.3560, -sh * 0.876),
        (0.3595, -sh * 0.772),
        (TYRE_R, -sh * 0.620),
        (TYRE_R, sh * 0.620),
        (0.3595, sh * 0.772),
        (0.3560, sh * 0.876),
        (0.3420, sh * 0.950),
        (0.3120, bulge * 0.985),
        (0.2740, bulge),
        (RIM_R + 0.018, sh + 0.002),
        (RIM_R, sh),
        (RIM_R, sh * 0.5),
        (RIM_R, -sh * 0.5),
        (RIM_R, -sh),
    ]


def rim_profile(hw):
    """18 in rim barrel plus the modern machined aero cover, as one solid.

    D043: a plain dish read as a featureless blob. Stepped concentric terraces
    catch the light the way a machined cover does. The barrel is 1 mm proud of
    the tyre bore (D046) so the two seat together instead of leaving a black
    gap ring where coincident surfaces fight.
    """
    sh = hw
    r_out = RIM_R + 0.001
    # D047: six concentric terraces made the cover read as a speaker cone. A real
    # aero cover is a broad flat annulus with ONE step down to the centre boss.
    return [
        (0.0000, -sh * 0.560),
        (0.0480, -sh * 0.560),
        (0.0545, -sh * 0.520),
        (0.1290, -sh * 0.505),
        (0.1375, -sh * 0.440),
        (0.1960, -sh * 0.418),
        (0.2075, -sh * 0.300),
        (0.2150, -sh * 0.120),
        (0.2195, -sh * 0.020),
        (r_out, -sh * 0.005),
        (r_out, sh),
        (0.2195, sh),
        (0.2120, sh * 0.945),
        (0.2040, sh * 0.862),
        (0.1960, sh * 0.812),
        (0.1375, sh * 0.790),
        (0.1290, sh * 0.726),
        (0.0545, sh * 0.712),
        (0.0480, sh * 0.672),
        (0.0000, sh * 0.672),
    ]


COCKPIT_RIM = [
    # x, half width  (front of the opening -> back)
    (0.762, 0.048), (0.690, 0.118), (0.585, 0.172), (0.430, 0.203),
    (0.240, 0.216), (0.040, 0.213), (-0.070, 0.192), (-0.132, 0.140),
    (-0.168, 0.062),
]


def _cockpit_rim_z(x):
    """Follow the trough floor the body sections carve at the centreline."""
    table = [(0.780, 0.580), (0.560, 0.522), (0.340, 0.506),
             (0.120, 0.502), (-0.100, 0.540), (-0.190, 0.742)]
    if x >= table[0][0]:
        return table[0][1]
    for (x0, z0), (x1, z1) in zip(table, table[1:]):
        if x1 <= x <= x0:
            t = (x0 - x) / (x0 - x1)
            return C.lerp(z0, z1, t)
    return table[-1][1]


def build_cockpit(coll):
    """Open cockpit recess with seat back and headrest.

    The body loft carves a real trough at the centreline, so this is a shell that
    drops into it - walls plus a floor, open at the top - not a lid sitting on a
    closed surface.
    """
    made = []
    rim, floor = [], []
    for (x, hw) in COCKPIT_RIM:
        z = _cockpit_rim_z(x) - 0.004
        rim.append((x, hw, z))
        floor.append((x, hw * 0.70, z - 0.118))

    def closed_ring(pts):
        ring = [(x, y, z) for (x, y, z) in pts]
        ring += [(x, -y, z) for (x, y, z) in reversed(pts[1:-1])]
        return ring

    r0, r1 = closed_ring(rim), closed_ring(floor)
    verts, faces = C.loft([r0, r1], closed=True, cap_start=False, cap_end=True)
    ob = C.new_obj("Cockpit_Recess", verts, faces, coll=coll, smooth=False)
    C.merge_doubles(ob, 1e-5)
    # give the shell wall thickness rather than flipping normals: an open shell
    # lit from one side shades wrong on its back faces.
    m = C.add_solidify(ob, thickness=0.010, offset=1.0)
    m.use_even_offset = True
    C.shade_auto_smooth(ob, 34.0)
    made.append(ob)

    # seat back / headrest padding behind the driver
    head = C.box("Cockpit_Headrest", -0.145, 0.045, -0.175, 0.175, 0.470, 0.612,
                 coll=coll)
    C.add_bevel(head, width=0.045, segments=4)
    made.append(head)

    # steering wheel hint, angled back the way a real one sits
    wheel = C.box("Cockpit_Wheel", 0.492, 0.520, -0.115, 0.115, 0.462, 0.560,
                  coll=coll)
    C.add_bevel(wheel, width=0.020, segments=3)
    wheel.rotation_euler = (0.0, math.radians(-22.0), 0.0)
    made.append(wheel)
    return made


def build_wheel(name, x, y, hw, coll, steer=0.0):
    tyre = C.revolve(f"{name}_Tyre", tyre_profile(hw), segments=96, coll=coll,
                     auto_smooth=34.0)
    rim = C.revolve(f"{name}_Rim", rim_profile(hw), segments=72, coll=coll,
                    auto_smooth=32.0)
    for ob in (tyre, rim):
        ob.rotation_euler = (math.radians(90.0), 0.0, math.radians(steer))
        ob.location = (x, y, TYRE_R)
    return tyre, rim


def build_wheels(coll):
    made = []
    for tag, x, y, hw in (
        ("WheelFL", FRONT_AXLE, FRONT_Y, FRONT_HW),
        ("WheelFR", FRONT_AXLE, -FRONT_Y, FRONT_HW),
        ("WheelRL", REAR_AXLE, REAR_Y, REAR_HW),
        ("WheelRR", REAR_AXLE, -REAR_Y, REAR_HW),
    ):
        made += list(build_wheel(tag, x, y, hw, coll))
    return made


# --------------------------------------------------------------------------- #
# aerodynamic surfaces
# --------------------------------------------------------------------------- #

def airfoil(chord, thick, camber, n=32):
    """Closed inverted-aerofoil loop in local (chordwise u, vertical v).

    F1 wings are upside-down aircraft wings, so camber is negative: the suction
    surface is underneath. u runs 0 (leading edge) -> chord (trailing edge).
    """
    pts_up, pts_lo = [], []
    for i in range(n + 1):
        s = i / n
        u = chord * s
        zc = camber * chord * 4.0 * s * (1.0 - s)
        # elliptical thickness, tapered to a sharp trailing edge
        zt = 0.5 * thick * chord * math.sqrt(max(0.0, 1.0 - (2.0 * s - 1.0) ** 2)) * (1.0 - s * 0.55)
        pts_up.append((u, zc + zt))
        pts_lo.append((u, zc - zt))
    return pts_up + list(reversed(pts_lo[1:-1]))


def sweep_wing(name, stations, coll, smooth_angle=52.0):
    """stations: (y, le_x, le_z, chord, thick, camber, twist_deg) -> lofted solid."""
    rings, n_pts = [], None
    for (y, le_x, le_z, chord, thick, camber, twist) in stations:
        loop = airfoil(chord, thick, camber)
        if n_pts is None:
            n_pts = len(loop)
        ca, sa = math.cos(math.radians(twist)), math.sin(math.radians(twist))
        ring = []
        for (u, v) in loop:
            ur = u * ca - v * sa
            vr = u * sa + v * ca
            ring.append((le_x - ur, y, le_z + vr))
        rings.append(ring)
    verts, faces = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = C.new_obj(name, verts, faces, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, smooth_angle)
    return ob


def _fw_span(n=17):
    """Front wing span stations: neutral section at centre, full chord outboard."""
    out = []
    for i in range(n):
        t = i / (n - 1)
        y = -1.0 + 2.0 * t
        a = abs(y)
        neutral = C.smoothstep(min(1.0, a / 0.42))          # flat centre section
        tip = 1.0 - 0.16 * C.smoothstep(max(0.0, (a - 0.72) / 0.28))
        out.append((y, 0.60 + 0.40 * neutral, tip, a))
    return out


def build_front_wing(coll):
    """Four-element 2022-spec front wing, 2.0 m span, plus endplates."""
    made = []
    elements = [
        # le_x,  le_z,  chord, thick, camber, twist
        (3.020, 0.072, 0.300, 0.075, -0.075, -2.0),
        (2.902, 0.136, 0.262, 0.070, -0.105, -5.5),
        (2.792, 0.199, 0.236, 0.066, -0.130, -9.0),
        (2.690, 0.263, 0.214, 0.062, -0.150, -13.0),
    ]
    for idx, (le_x, le_z, chord, thick, camber, twist) in enumerate(elements):
        stations = []
        for (y, cscale, tipscale, a) in _fw_span():
            stations.append((
                y,
                le_x - 0.028 * a,                 # slight sweep back at the tips
                le_z + 0.020 * a * a,             # tips lift toward the endplate
                chord * cscale * tipscale,
                thick,
                camber * (0.45 + 0.55 * C.smoothstep(min(1.0, a / 0.42))),
                twist * (0.5 + 0.5 * C.smoothstep(min(1.0, a / 0.42))),
            ))
        made.append(sweep_wing(f"FW_Element_{idx}", stations, coll))

    # endplates
    for side in (1, -1):
        y = 1.000 * side
        # D077: the first endplate was 0.60 x 0.31 m of blank plate in gloss
        # livery, and from the hero camera it read as a paddle the size of a
        # wheel. Real 2022 endplates are shorter, taper up toward the tyre, and
        # are mostly bare carbon with the colour carried on the wing itself.
        outline = [
            (2.986, 0.040), (3.002, 0.098), (2.992, 0.176), (2.952, 0.234),
            (2.878, 0.268), (2.772, 0.278), (2.676, 0.264), (2.612, 0.230),
            (2.582, 0.176), (2.580, 0.114), (2.606, 0.062), (2.680, 0.036),
            (2.820, 0.028), (2.930, 0.031),
        ]
        verts = [(x, y, z) for (x, z) in outline]
        faces = [tuple(range(len(outline)))]
        ob = C.new_obj(f"FW_Endplate_{'L' if side > 0 else 'R'}", verts, faces,
                       coll=coll, smooth=False)
        m = C.add_solidify(ob, thickness=0.011, offset=-1.0 * side)
        m.use_even_offset = True
        C.add_bevel(ob, width=0.005, segments=2)
        made.append(ob)

    # nose pylons tying the wing to the underside of the nose
    for side in (1, -1):
        y = 0.115 * side
        ob = C.box(f"FW_Pylon_{'L' if side > 0 else 'R'}",
                   2.640, 2.980, y - 0.014, y + 0.014, 0.150, 0.268, coll=coll)
        C.add_bevel(ob, width=0.006, segments=2)
        made.append(ob)
    return made


def build_rear_wing(coll):
    """Two-element rear wing on a swan-neck pylon, plus beam wing and endplates."""
    made = []
    half = 0.525
    elements = [
        # le_x,  le_z,  chord, thick, camber, twist
        (-2.215, 0.800, 0.300, 0.085, -0.090, -6.0),
        (-2.410, 0.876, 0.190, 0.070, -0.150, -22.0),
    ]
    for idx, (le_x, le_z, chord, thick, camber, twist) in enumerate(elements):
        stations = []
        n = 11
        for i in range(n):
            t = i / (n - 1)
            y = -half + 2 * half * t
            a = abs(y) / half
            stations.append((y, le_x, le_z + 0.010 * a * a,
                             chord * (1.0 - 0.06 * a * a), thick, camber, twist))
        made.append(sweep_wing(f"RW_Element_{idx}", stations, coll))

    # beam wing under the main plane
    stations = []
    for i in range(9):
        t = i / 8
        y = -0.44 + 0.88 * t
        stations.append((y, -2.245, 0.436, 0.170, 0.085, -0.120, -14.0))
    made.append(sweep_wing("RW_BeamWing", stations, coll))

    # endplates
    for side in (1, -1):
        y = half * side
        # D104: the first endplate ran from z=0.372 to 0.958 - 0.59 m tall and
        # dropping well below the beam wing, so from behind it was a slab that
        # swallowed the whole wing. Real endplates sit above the beam wing.
        outline = [
            (-2.140, 0.596), (-2.128, 0.700), (-2.136, 0.812), (-2.160, 0.892),
            (-2.216, 0.938), (-2.340, 0.958), (-2.500, 0.952), (-2.620, 0.920),
            (-2.664, 0.860), (-2.670, 0.760), (-2.652, 0.668), (-2.596, 0.598),
            (-2.470, 0.560), (-2.310, 0.552),
        ]
        verts = [(x, y, z) for (x, z) in outline]
        faces = [tuple(range(len(outline)))]
        ob = C.new_obj(f"RW_Endplate_{'L' if side > 0 else 'R'}", verts, faces,
                       coll=coll, smooth=False)
        m = C.add_solidify(ob, thickness=0.016, offset=-1.0 * side)
        m.use_even_offset = True
        C.add_bevel(ob, width=0.005, segments=2)
        made.append(ob)

    # swan-neck pylon from the engine cover up to the main plane
    pylon = [
        (-1.900, 0.470), (-2.010, 0.560), (-2.090, 0.680), (-2.130, 0.790),
        (-2.150, 0.860), (-2.190, 0.862), (-2.176, 0.780), (-2.140, 0.668),
        (-2.062, 0.552), (-1.946, 0.452),
    ]
    verts = [(x, 0.0, z) for (x, z) in pylon]
    ob = C.new_obj("RW_Pylon", verts, [tuple(range(len(pylon)))], coll=coll, smooth=False)
    m = C.add_solidify(ob, thickness=0.038, offset=0.0)
    m.use_even_offset = True
    C.add_bevel(ob, width=0.008, segments=2)
    made.append(ob)
    return made


def tube(name, path, radius, coll, segments=14, close_caps=True, smooth_angle=60.0):
    """Sweep a circle along a polyline using parallel-transport frames."""
    from mathutils import Vector
    pts = [Vector(p) for p in path]
    tangents = []
    for i, p in enumerate(pts):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == len(pts) - 1:
            t = pts[-1] - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        tangents.append(t.normalized())

    ref = Vector((0.0, 0.0, 1.0))
    if abs(tangents[0].dot(ref)) > 0.95:
        ref = Vector((0.0, 1.0, 0.0))
    normal = (ref - tangents[0] * ref.dot(tangents[0])).normalized()

    rings = []
    for i, (p, t) in enumerate(zip(pts, tangents)):
        if i > 0:
            # parallel transport: project the previous normal onto the new plane
            normal = (normal - t * normal.dot(t)).normalized()
        binormal = t.cross(normal).normalized()
        ring = []
        for k in range(segments):
            a = C.TAU * k / segments
            off = normal * (math.cos(a) * radius) + binormal * (math.sin(a) * radius)
            ring.append(tuple(p + off))
        rings.append(ring)

    verts, faces = C.loft(rings, closed=True, cap_start=close_caps, cap_end=close_caps)
    ob = C.new_obj(name, verts, faces, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, smooth_angle)
    return ob


def build_halo(coll):
    """Titanium halo: centre pillar plus the hoop over the cockpit shoulders."""
    made = []
    hoop = []
    n = 41
    for i in range(n):
        t = i / (n - 1)
        ang = math.pi * t                        # sweep one side to the other
        y = -0.335 * math.cos(ang)
        # anchored low behind each shoulder, arcing forward and up over the head
        f = math.sin(ang)
        x = -0.075 + 0.965 * f
        z = 0.690 + 0.245 * f - 0.075 * f * f
        hoop.append((x, y, z))
    made.append(tube("Halo_Hoop", hoop, 0.0225, coll, segments=16))

    # pillar top must land on the hoop's front-most point (0.890, 0, 0.860)
    pillar = [(0.905, 0.0, 0.612), (0.900, 0.0, 0.700), (0.895, 0.0, 0.782),
              (0.891, 0.0, 0.834), (0.890, 0.0, 0.862)]
    made.append(tube("Halo_Pillar", pillar, 0.0235, coll, segments=14))
    return made


def build_suspension(coll):
    """Front and rear wishbones, pushrods and track rods as tapered tubes."""
    made = []
    specs = []
    for side in (1, -1):
        yw = FRONT_Y * side
        hub = (FRONT_AXLE, yw - 0.085 * side, TYRE_R)
        specs += [
            (f"SusF{'L' if side > 0 else 'R'}_UpperFwd",
             [(2.030, 0.190 * side, 0.430), hub], 0.0165),
            (f"SusF{'L' if side > 0 else 'R'}_UpperAft",
             [(1.560, 0.205 * side, 0.448), hub], 0.0165),
            (f"SusF{'L' if side > 0 else 'R'}_LowerFwd",
             [(2.070, 0.185 * side, 0.176), (FRONT_AXLE, yw - 0.085 * side, 0.238)], 0.0185),
            (f"SusF{'L' if side > 0 else 'R'}_LowerAft",
             [(1.520, 0.200 * side, 0.168), (FRONT_AXLE, yw - 0.085 * side, 0.238)], 0.0185),
            (f"SusF{'L' if side > 0 else 'R'}_Pushrod",
             [(1.640, 0.222 * side, 0.470), (FRONT_AXLE - 0.030, yw - 0.095 * side, 0.245)], 0.0135),
            (f"SusF{'L' if side > 0 else 'R'}_TrackRod",
             [(1.610, 0.215 * side, 0.300), (FRONT_AXLE + 0.075, yw - 0.090 * side, 0.290)], 0.0125),
        ]
        yr = REAR_Y * side
        hub_r = (REAR_AXLE, yr - 0.105 * side, TYRE_R)
        specs += [
            (f"SusR{'L' if side > 0 else 'R'}_UpperFwd",
             [(-1.520, 0.175 * side, 0.400), hub_r], 0.0175),
            (f"SusR{'L' if side > 0 else 'R'}_UpperAft",
             [(-2.020, 0.150 * side, 0.392), hub_r], 0.0175),
            (f"SusR{'L' if side > 0 else 'R'}_LowerFwd",
             [(-1.540, 0.190 * side, 0.190), (REAR_AXLE, yr - 0.105 * side, 0.250)], 0.0195),
            (f"SusR{'L' if side > 0 else 'R'}_LowerAft",
             [(-2.060, 0.170 * side, 0.196), (REAR_AXLE, yr - 0.105 * side, 0.250)], 0.0195),
            (f"SusR{'L' if side > 0 else 'R'}_Pushrod",
             [(-1.600, 0.196 * side, 0.212), (REAR_AXLE + 0.040, yr - 0.110 * side, 0.430)], 0.0145),
        ]

    for name, path, r in specs:
        made.append(tube(name, path, r, coll, segments=10))
    return made


def build_details(coll):
    """Mirrors, engine-cover fin, sidepod inlets, hub caps."""
    made = []

    # mirror pods on stalks
    for side in (1, -1):
        s = "L" if side > 0 else "R"
        stalk = [(0.700, 0.196 * side, 0.588), (0.678, 0.300 * side, 0.606),
                 (0.660, 0.392 * side, 0.616)]
        made.append(tube(f"Mirror_Stalk_{s}", stalk, 0.0145, coll, segments=10))
        pod = C.box(f"Mirror_Pod_{s}", 0.596, 0.700, 0.376 * side - 0.026,
                    0.376 * side + 0.026, 0.600, 0.658, coll=coll)
        C.add_bevel(pod, width=0.014, segments=3)
        made.append(pod)

    # shark fin on the engine cover
    fin = [(-0.900, 0.836), (-1.180, 0.792), (-1.460, 0.720), (-1.700, 0.630),
           (-1.880, 0.530), (-1.880, 0.470), (-1.700, 0.560), (-1.460, 0.650),
           (-1.180, 0.724), (-0.900, 0.780)]
    verts = [(x, 0.0, z) for (x, z) in fin]
    ob = C.new_obj("EngineCover_Fin", verts, [tuple(range(len(fin)))], coll=coll, smooth=False)
    m = C.add_solidify(ob, thickness=0.016, offset=0.0)
    m.use_even_offset = True
    made.append(ob)

    # sidepod inlet mouths
    for side in (1, -1):
        s = "L" if side > 0 else "R"
        ob = C.box(f"Sidepod_Inlet_{s}", 0.700, 0.792, 0.340 * side, 0.660 * side,
                   0.318, 0.454, coll=coll)
        C.add_bevel(ob, width=0.028, segments=4)
        made.append(ob)

    # D107: the tail ended in a bare cone. D110/D111: the first exhaust was
    # 104 mm across, protruded 0.21 m and floated across the beam wing. It now
    # sits at the very end of the tapering tail cone, barely proud of it.
    exh = C.revolve("Exhaust_Tail", [
        (0.000, 0.000), (0.026, 0.000), (0.031, 0.010), (0.034, 0.062),
        (0.036, 0.084), (0.030, 0.084), (0.028, 0.062), (0.024, 0.010),
        (0.000, 0.010)],
        segments=28, coll=coll, auto_smooth=34.0)
    exh.rotation_euler = (0.0, math.radians(-93.0), 0.0)
    exh.location = (-2.438, 0.0, 0.196)
    made.append(exh)

    # wheel hub caps
    for tag, x, y, hw in (("FL", FRONT_AXLE, FRONT_Y, FRONT_HW),
                          ("FR", FRONT_AXLE, -FRONT_Y, FRONT_HW),
                          ("RL", REAR_AXLE, REAR_Y, REAR_HW),
                          ("RR", REAR_AXLE, -REAR_Y, REAR_HW)):
        # D044: the first cap was a 52 mm light-titanium dome that read as a
        # plastic knob. A centre-lock nut is small, dark and flat-topped.
        sgn = 1.0 if y > 0 else -1.0
        cap = C.revolve(f"HubCap_{tag}", [
            (0.000, 0.000), (0.031, 0.000), (0.037, 0.007), (0.037, 0.017),
            (0.030, 0.021), (0.000, 0.021)],
            segments=24, coll=coll, auto_smooth=26.0)
        cap.rotation_euler = (math.radians(90.0), 0.0, 0.0)
        cap.location = (x, y + sgn * hw * 0.505, TYRE_R)
        made.append(cap)
    return made


# prefix -> material name; first match wins, so order matters
MATERIAL_RULES = [
    ("Car_Body", "LiveryPaint"),
    ("Car_Floor", "CarbonFibre"),
    ("HubCap_", "WheelRim"),
    ("WheelFL_Tyre", "TyreRubber"), ("WheelFR_Tyre", "TyreRubber"),
    ("WheelRL_Tyre", "TyreRubber"), ("WheelRR_Tyre", "TyreRubber"),
    ("WheelFL_Rim", "WheelRim"), ("WheelFR_Rim", "WheelRim"),
    ("WheelRL_Rim", "WheelRim"), ("WheelRR_Rim", "WheelRim"),
    ("FW_Element", "CarbonFibre"),
    ("FW_Endplate", "CarbonFibre"),
    ("FW_Pylon", "CarbonFibre"),
    ("RW_Element_0", "LiveryPaint"),
    ("RW_Element_1", "CarbonFibre"),
    ("RW_BeamWing", "CarbonFibre"),
    ("RW_Endplate", "LiveryPaint"),
    ("RW_Pylon", "CarbonFibre"),
    ("Halo_", "MatteBlack"),
    ("Cockpit_", "MatteBlack"),
    ("Sus", "CarbonFibre"),
    ("Mirror_Pod", "LiveryPaint"),
    ("Mirror_Stalk", "CarbonFibre"),
    ("EngineCover_Fin", "LiveryPaint"),
    ("Sidepod_Inlet", "MatteBlack"),
    ("Exhaust_Tail", "Titanium"),
]


def assign_materials(parts):
    import s03_materials as M
    M.build_car_materials()
    unmatched = []
    for ob in parts:
        if ob.type != "MESH":
            continue
        for prefix, mat_name in MATERIAL_RULES:
            if ob.name.startswith(prefix):
                C.assign(ob, bpy.data.materials[mat_name])
                break
        else:
            unmatched.append(ob.name)
            C.assign(ob, bpy.data.materials["CarbonFibre"])
    return unmatched


def build():
    C.purge_collection("CAR")
    coll = C.collection("CAR")

    root = bpy.data.objects.get("CAR_ROOT")
    if root is None:
        root = bpy.data.objects.new("CAR_ROOT", None)
    if root.name not in coll.objects:
        for c in list(root.users_collection):
            c.objects.unlink(root)
        coll.objects.link(root)
    root.empty_display_size = 0.4
    root.location = (0.0, 0.0, GROUND)

    parts = [build_body(coll), build_floor(coll)]
    parts += build_wheels(coll)
    parts += build_front_wing(coll)
    parts += build_rear_wing(coll)
    parts += build_cockpit(coll)
    parts += build_halo(coll)
    parts += build_suspension(coll)
    parts += build_details(coll)
    assign_materials(parts)

    for ob in parts:
        if ob.parent is None:
            ob.parent = root

    return {"parts": [o.name for o in parts],
            "tris": sum(len(o.data.polygons) for o in parts),
            "root_z": root.location[2]}
