"""THE CONTRACT. Every part module must obey this file.

Coordinate system (CAR-LOCAL, metres)
-------------------------------------
    +X  forward, toward the nose      nose tip      x = +3.00
    +Y  to the car's LEFT             rear wing TE  x = -2.63
    +Z  up                            tyre contact  z =  0.00

The whole car is parented to an empty `CAR_ROOT` sitting at world
(0, 0, 0.340) - the turntable deck. So a part authored with wheels touching
z = 0 lands correctly on the platform. NEVER bake the 0.340 into a part.

Part module interface
---------------------
A part lives at `build/parts/<name>.py` and exposes:

    NAME = "steering_wheel"
    def build(coll, ctx=None) -> list[bpy.types.Object]

`build` creates its objects, links them into `coll`, assigns materials by name
via `spec.mat(...)`, and returns the list it created. It must NOT touch render
settings, cameras, lights, the world, or any other collection. It must be
idempotent: calling it twice must not duplicate or error (use unique names -
`common.new_obj` already replaces same-named objects).

Detail expectations
-------------------
This is a hero close-up asset, not a game model. Chamfer every edge a machinist
would break. Model fasteners, seams, weave direction changes, rivets, vents,
lettering relief. Assume a 3840x2160 render with the camera 400 mm from the
part. A flat untextured face bigger than ~15 mm is a defect.

Rough per-part poly budgets (total car target ~4-6 M):
    steering wheel      120-260 k        brake duct assembly   150-320 k
    front wing          250-500 k        rear wing             200-400 k
    floor + diffuser    200-400 k        suspension corner     120-260 k
    cockpit interior    150-350 k        sidepod               150-300 k
"""

import math

import bpy

import common as C

# --------------------------------------------------------------------------- #
# principal dimensions - 2024 regulations
# --------------------------------------------------------------------------- #

GROUND = 0.340              # world z of the tyre contact plane (CAR_ROOT.z)

WHEELBASE = 3.600
FRONT_AXLE = 1.800
REAR_AXLE = -1.800

OVERALL_LENGTH = 5.630
OVERALL_WIDTH = 2.000
NOSE_TIP_X = 3.000
REAR_WING_TE_X = -2.630

TYRE_R = 0.360              # 720 mm diameter, front and rear
FRONT_TYRE_HW = 0.1525      # 305 mm section
REAR_TYRE_HW = 0.2025       # 405 mm section
FRONT_TYRE_Y = 1.000 - FRONT_TYRE_HW      # centre plane of the front tyre
REAR_TYRE_Y = 1.000 - REAR_TYRE_HW
RIM_R = 0.2286              # 18 in
RIM_INNER_R = 0.2296        # barrel sits 1 mm proud of the tyre bore (D046)

BRAKE_DISC_R = 0.1400       # 280 mm carbon disc
BRAKE_DISC_T = 0.032
UPRIGHT_Y_INSET = 0.085     # hub face inboard of the tyre centre plane

FLOOR_Z = 0.050             # underfloor reference plane
PLANK_Z = 0.040
DIFFUSER_EXIT_X = -2.230
ROLL_HOOP_TOP_Z = 0.950
COCKPIT_FRONT_X = 0.780     # front of the opening
COCKPIT_REAR_X = -0.168

FRONT_WING_SPAN = 2.000
FRONT_WING_LE_X = 3.020
REAR_WING_SPAN = 1.050
REAR_WING_TOP_Z = 0.950
BEAM_WING_Z = 0.436

# --------------------------------------------------------------------------- #
# body loft stations - the single source of truth for the monocoque surface
# x, bw, bz, uw, uz, pw, pz, ptw, ptz, tw, tz, ttw, ttz, ctz
#
#   (0, bz)      belly centreline        (ptw, ptz)  sidepod shoulder
#   (bw, bz)     belly edge              (tw,  tz)   tub side
#   (uw, uz)     undercut waist          (ttw, ttz)  tub shoulder
#   (pw, pz)     sidepod max width       (0,   ctz)  centre top
#
# uw < pw is what creates the concave ground-effect waist.
# Over the cockpit, ctz < ttz, so the section carries a real trough.
# --------------------------------------------------------------------------- #

BODY_STATIONS = [
    (3.000, 0.062, 0.232, 0.072, 0.252, 0.078, 0.282, 0.074, 0.312, 0.064, 0.332, 0.038, 0.346, 0.356),
    (2.820, 0.082, 0.220, 0.096, 0.246, 0.106, 0.280, 0.100, 0.314, 0.086, 0.338, 0.050, 0.354, 0.366),
    (2.600, 0.104, 0.206, 0.122, 0.238, 0.136, 0.276, 0.128, 0.314, 0.110, 0.342, 0.062, 0.360, 0.374),
    (2.340, 0.126, 0.190, 0.150, 0.234, 0.168, 0.282, 0.158, 0.330, 0.136, 0.364, 0.076, 0.384, 0.398),
    (2.060, 0.132, 0.166, 0.168, 0.232, 0.196, 0.296, 0.186, 0.356, 0.152, 0.396, 0.084, 0.420, 0.434),
    (1.780, 0.162, 0.136, 0.204, 0.236, 0.238, 0.316, 0.226, 0.388, 0.186, 0.436, 0.104, 0.464, 0.480),
    (1.500, 0.188, 0.098, 0.236, 0.238, 0.276, 0.334, 0.262, 0.418, 0.216, 0.474, 0.122, 0.506, 0.524),
    (1.220, 0.212, 0.074, 0.264, 0.240, 0.310, 0.352, 0.294, 0.446, 0.244, 0.510, 0.138, 0.546, 0.566),
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


def station_half(st):
    """7-point half profile for one station, bottom centre -> top centre."""
    (_x, bw, bz, uw, uz, pw, pz, ptw, ptz, tw, tz, ttw, ttz, ctz) = st
    return [(0.0, bz), (bw, bz), (uw, uz), (pw, pz),
            (ptw, ptz), (tw, tz), (ttw, ttz), (0.0, ctz)]


def station_at(x):
    """Interpolated 14-tuple station at an arbitrary x (nose +3.0 -> tail -2.47)."""
    xs = [s[0] for s in BODY_STATIONS]
    if x >= xs[0]:
        return BODY_STATIONS[0]
    if x <= xs[-1]:
        return BODY_STATIONS[-1]
    for i in range(len(xs) - 1):
        if xs[i] >= x >= xs[i + 1]:
            t = (xs[i] - x) / (xs[i] - xs[i + 1])
            a, b = BODY_STATIONS[i], BODY_STATIONS[i + 1]
            return tuple(C.lerp(a[k], b[k], t) for k in range(len(a)))
    return BODY_STATIONS[-1]


def body_surface_point(x, frac):
    """A point on the body's half section at station x.

    frac 0..1 walks the 7-point half profile from belly centre (0) to centre
    top (1). Use this to land a part exactly on the skin instead of guessing.
    Returns (y, z).
    """
    half = station_half(station_at(x))
    pts = C.catmull_rom(half, 65)
    i = max(0, min(len(pts) - 1, int(round(frac * (len(pts) - 1)))))
    return pts[i]


def body_top_z(x):
    """Centreline top of the body at station x (the cockpit trough floor over
    the opening, the airbox crown behind it)."""
    return station_at(x)[13]


def body_max_halfwidth(x):
    st = station_at(x)
    return max(st[1], st[3], st[5], st[7], st[9], st[11])


# --------------------------------------------------------------------------- #
# materials - ask for these by name, never invent your own tree
# --------------------------------------------------------------------------- #

MATERIALS = (
    "CarbonFibre",      # lacquered 2x2 twill, ~5 mm pitch
    "CarbonMatte",      # unlacquered structural weave
    "LiveryPaint",      # metallic team blue with panel lines
    "TyreRubber",       # slick compound + sidewall band
    "Titanium",         # brushed titanium
    "WheelRim",         # dark anodised wheel
    "MatteBlack",       # rubber seals, interior, halo
    "SteelFastener",    # bolts, rod ends, clips
    "CarbonCeramic",    # brake disc
    "AnodisedRed",      # anodised accents
    "AnodisedGold",     # heat-shield gold
    "DisplayGlass",     # screen glass
    "DisplayEmit",      # emissive screen face
    "SuedeGrip",        # steering wheel grips
)


def mat(name):
    """Fetch a shared material, building it on first use."""
    import s03_materials as M
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    builder = getattr(M, "EXTRA_MATERIALS", {}).get(name)
    if builder is not None:
        return builder()
    if name in M.CAR:
        return M.CAR[name]()
    if name in M.SHOWROOM:
        return M.SHOWROOM[name]()
    raise KeyError(f"unknown material {name!r}; declare it in s03_materials")


def assign(ob, name, slot=0):
    return C.assign(ob, mat(name), slot=slot)
