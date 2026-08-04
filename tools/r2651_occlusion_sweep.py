#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2651_occlusion_sweep.py — IS THE CAR ACTUALLY HIDDEN, AND BY WHAT NAMED THING?

    blender -b --factory-startup -P tools/r2651_occlusion_sweep.py -- --selftest
    blender -b --factory-startup -P tools/r2651_occlusion_sweep.py -- \
        --mods surface,barriers,architecture --beats 4,5,6 --out out/occlusion.json

WHY IT EXISTS
-------------
At film frame 2190 the car projects to screen centre (x 0.500, y 0.493) at
183 m and the centre of the delivered frame is a parapet.  Nothing in this
project has ever asked whether the SUBJECT IS VISIBLE.  `lap_shotscale` reports
the projected size of the car's box whether or not you can see it;
`r2581_nearfield_sweep` measures how much of the frame is filled by things
NEARER than the car, and its own docstring says it "IS blind to the car being
hidden BEHIND a structure".  So a run of frames in which the shot's only
subject is behind concrete looks, to every instrument that exists, like a
perfectly composed shot.

WHAT THIS DOES INSTEAD
----------------------
For each film frame it takes the camera's own keyed pose and lens out of
`world/camera_rig_path.json`, the car's MEASURED pose out of
`world/car_anim_measured.json` (measured off the built `car_anim.blend`; the
telemetry table is NOT used, and the +973 telemetry-to-film offset is not
applied anywhere here), builds 58 sample points on the car, and fires one ray
per sample from the camera origin.  A sample is OCCLUDED if the first thing the
ray hits sits closer to the camera than the sample does.  The occluder is
reported BY NAME.

    occ_frac        occluded / 58, over the whole oriented box
    occ_frac_front  the same over the camera-facing samples only — the ones
                    that would form the silhouette.  This is the honest one:
                    the far side of the car is hidden by the car itself and no
                    world geometry is needed for that.
    owner           the single named object that owns the most occluded samples
    owner_dist      how far away it is, metres
    channel         solid / fence / veg / surface, NEVER pooled

FOUR CHANNELS AND WHY THEY ARE NOT ONE NUMBER
---------------------------------------------
A raycast cannot see through a catch fence.  A real catch fence is 40 mm of
wire at 100 mm pitch and the delivered frame sees the car straight through it;
to a BVH it is a solid wall.  So fence hits go in their own channel and are
never added to concrete.  The same for vegetation, which whips past, and for
the racing surface itself, which occludes only when a crest genuinely gets in
the way and would otherwise be manufactured by a grazing ray landing on the
road it is aimed at.

AND A BRIDGE IS NOT A WALL
--------------------------
`ARCH_PontPlongee` spans the track.  "The bridge is between the camera and the
car" is not the same statement as "the car is hidden": a bridge has an opening
under its deck and the shot is normally taken through it.  The raycast settles
this by construction — a ray through the opening hits nothing — and
`--selftest` contains that exact case as a control, because a metric that
cannot fail is not a measurement.

THE CONTROLS (`--selftest`), which this project has learnt to insist on
-----------------------------------------------------------------------
    clear        empty scene                    -> occ_frac == 0 exactly
    blocker      plane between camera and car   -> occ_frac == 1 exactly,
                                                   and it is NAMED
    behind       the same plane BEHIND the car  -> occ_frac == 0   (the depth
                                                   test is the whole finding)
    self         a car-shaped mesh AT the car   -> 0 when excluded by name,
                                                   1 when not, so the exclusion
                                                   is shown to do something
    bridge gap   deck + pylons, car under the deck   -> occ_frac == 0
    bridge pier  the same object, car behind a pylon -> occ_frac == 1
    partial      half-width plane               -> 0 < occ_frac < 1
    ground       road plane under the car       -> occ_frac == 0 (a grazing ray
                                                   must not be occluded by the
                                                   surface it is aimed at)
    offframe     camera turned 180 degrees      -> in_frame False
    behind-cam   car behind the camera          -> in_frame False

WHAT IT IS NOT
--------------
Geometry at the shutter's centre instant: the delivered frames carry a
180-degree shutter, so an edge measured here as just-clear may still smear over
the car.  Alpha-blind: it does not know a fence, a mesh grille or a leaf is
see-through, which is exactly why those live in their own channels.  And the
car is represented by its oriented box (`world_contract.CAR_BODY_*`, the same
box `tools/lap_shotscale.py` uses), which is larger than an F1 car — a nose and
an open wheel do not fill their bounding box — so `occ_frac` between 0 and 1 is
a bracket on the real silhouette, not a pixel count.

Blender 5.2 exits 0 on an uncaught script exception.  Judge on STAGE RESULT.
"""

import argparse
import gc
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

T0 = time.time()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, "world"), os.path.join(ROOT, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

W, H = 3840, 2160
SENSOR = 36.0                       # mm, sensor_fit AUTO -> long axis is W
FPS = 24

# The car's oriented box.  Same numbers and same convention as
# tools/lap_shotscale.py, which is the instrument every other size statement in
# this round was made with; taking a second opinion here would make this
# report incomparable with those.
CAR_LEN = 5.698
CAR_W = 2.005
CAR_TOP_Z = 0.992
# NOT 0.0.  A sample sitting exactly on the road is coplanar with the road, and
# a ray fired at it from 183 m at two degrees of incidence lands on the asphalt
# a hair early through nothing but float noise.  20 mm lifts the bottom face
# clear of that without lifting it clear of anything that could really hide it.
CAR_BOT_Z = 0.020
RIDE_H = 0.340                      # recorded, not used: the box is the hull

# Depth tolerance.  A hit must be at least this much CLOSER than the sample to
# count as occluding it.
EPS_M = 0.10

BEATS = [("1_assembly", 1, 792), ("2_launch", 793, 864), ("3_breach", 865, 1056),
         ("4_transit", 1057, 1190), ("5_lap", 1191, 2714), ("6_ending", 2715, 2978)]

MODULE_ORDER = ["surface", "barriers", "architecture", "terrain", "dressing",
                "items"]


def log(m):
    print("[occ %7.1fs] %s" % (time.time() - T0, m))
    sys.stdout.flush()


def beat_of(f):
    for n, a, b in BEATS:
        if a <= f <= b:
            return n
    return "?"


# ---------------------------------------------------------------------------
# CHANNELS.  The rule table is here, in one place, and the sweep prints the
# full census of every occluder name it ever saw so the classification can be
# audited against the names rather than trusted.
# ---------------------------------------------------------------------------
FENCE_TOKENS = ("fence", "catchfence", "cfp_", "debris", "mesh_", "netting",
                "chainlink", "palisade")
# THE MATERIAL DECIDES, NOT THE OBJECT, and this is not a refinement — it is
# the difference between a right and a wrong answer.  `ARCH_PontPlongee` is ONE
# object carrying concrete abutments, a concrete parapet, steel plate girders
# AND an `A_MeshDark` screen panel above the parapet.  Classifying by object
# name would call the screen concrete and report a solid occlusion at a frame
# where the delivered pixels show the car straight through the mesh — which is
# exactly what f2180 is.
SEETHRU_MAT_TOKENS = ("mesh", "screen", "glass", "net", "grille", "grating",
                      "louvre", "perf", "lattice")
VEG_PREFIX = ("VEG_",)
SURF_PREFIX = ("SURF_", "TER_")


def channel_of(name, mat=None):
    if mat:
        ml = mat.lower()
        for t in SEETHRU_MAT_TOKENS:
            if t in ml:
                return "fence"
    low = name.lower()
    for t in FENCE_TOKENS:
        if t in low:
            return "fence"
    for p in VEG_PREFIX:
        if name.startswith(p):
            return "veg"
    for p in SURF_PREFIX:
        if name.startswith(p):
            return "surface"
    return "solid"


# ---------------------------------------------------------------------------
# Poses
# ---------------------------------------------------------------------------
def qn(q):
    w, x, y, z = q
    n = math.sqrt(w * w + x * x + y * y + z * z) or 1.0
    return w / n, x / n, y / n, z / n


def cam_basis(q):
    """Camera right / up / forward in world space, from [w,x,y,z].

    Blender's camera looks down its own -Z with +Y up.  Lifted verbatim from
    tools/lap_shotscale.py:basis so the two agree by construction.
    """
    w, x, y, z = qn(q)
    right = Vector((1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y)))
    up = Vector((2 * (x * y - w * z), 1 - 2 * (x * x + z * z), 2 * (y * z + w * x)))
    fwd = Vector((-(2 * (x * z + w * y)), -(2 * (y * z - w * x)),
                  -(1 - 2 * (x * x + y * y))))
    return right, up, fwd


def car_matrix(rot):
    """Car body axes from the measured euler (rx, ry, rz), Blender XYZ order.

    Blender's 'XYZ' euler is R = Rz @ Ry @ Rx, which is the Z(yaw) Y(pitch)
    X(roll) product tools/lap_shotscale.py:obb_corners writes out longhand.
    Local +X is forward, +Y is left, +Z is up — confirmed against the measured
    `chassis_corners` at f2190: FL-RL bears -1.874 rad against a keyed yaw of
    -1.887, and FL-FR is 89.3 degrees to its left.
    """
    rx, ry, rz = rot
    cy, sy = math.cos(rz), math.sin(rz)
    cp, sp = math.cos(ry), math.sin(ry)
    cr, sr = math.cos(rx), math.sin(rx)
    return (
        Vector((cy * cp, sy * cp, -sp)),                                  # +X
        Vector((cy * sp * sr - sy * cr, sy * sp * sr + cy * cr, cp * sr)),  # +Y
        Vector((cy * sp * cr + sy * sr, sy * sp * cr - cy * sr, cp * cr)),  # +Z
    )


# 3 x 3 on each of the six faces at 0.1 / 0.5 / 0.9 of the face, so no sample
# lands on an edge or a corner where "which side is it on" is a coin toss.
_FACE_UV = [(a, b) for a in (0.1, 0.5, 0.9) for b in (0.1, 0.5, 0.9)]


def car_samples(loc, rot, contacts):
    """[(world point, world outward normal, tag)] — 54 hull + 4 wheels.

    The four wheel points are `contacts` STRAIGHT OUT OF THE MEASURED TABLE.
    They are labelled "contacts" there but `tools/car_anim_gate.py:392` calls
    the same array "the wheel CENTRE, keyed", and the numbers agree with that:
    at f2190 they sit 0.345 m ABOVE the chassis corners, which is a tyre
    radius, not a contact patch.  They are used as four more points ON THE CAR
    and nothing here depends on them being at road level.
    """
    ax, ay, az = car_matrix(rot)
    o = Vector(loc)
    hx, hy = CAR_LEN * 0.5, CAR_W * 0.5
    lo, hi = CAR_BOT_Z, CAR_TOP_Z
    out = []
    # (axis index of the face normal, sign, the two in-plane extents)
    faces = [(0, +1), (0, -1), (1, +1), (1, -1), (2, +1), (2, -1)]
    for axis, sgn in faces:
        for u, v in _FACE_UV:
            if axis == 0:
                lx = sgn * hx
                ly = -hy + 2 * hy * u
                lz = lo + (hi - lo) * v
            elif axis == 1:
                ly = sgn * hy
                lx = -hx + 2 * hx * u
                lz = lo + (hi - lo) * v
            else:
                lz = hi if sgn > 0 else lo
                lx = -hx + 2 * hx * u
                ly = -hy + 2 * hy * v
            p = o + ax * lx + ay * ly + az * lz
            n = (ax, ay, az)[axis] * sgn
            out.append((p, n, "hull"))
    for c in ("FL", "FR", "RL", "RR"):
        if c in contacts:
            p = Vector(contacts[c])
            out.append((p, (p - o).normalized() if (p - o).length > 1e-6
                        else az, "wheel_" + c))
    return out


def project(pt, eye, right, up, fwd, lens):
    """(px, py, z) in delivered pixels; z is depth along the view axis."""
    v = pt - eye
    z = v.dot(fwd)
    if z <= 1e-6:
        return None, None, z
    fpx = (lens / SENSOR) * W
    return (v.dot(right) / z * fpx + W * 0.5,
            -v.dot(up) / z * fpx + H * 0.5, z)


# ---------------------------------------------------------------------------
# The raycast
# ---------------------------------------------------------------------------
def first_hit(sc, dg, origin, direction, maxd, excluded, tries=8):
    """First hit within `maxd`, skipping objects whose name is excluded.

    The skip is a re-cast from just past the ignored hit, not a filter applied
    afterwards, so an excluded object standing in front of a real one does not
    hide it.
    """
    o = Vector(origin)
    rem = float(maxd)
    for _ in range(tries):
        if rem <= 0.0:
            return None
        ok, loc, nor, idx, ob, mw = sc.ray_cast(dg, o, direction, distance=rem)
        if not ok:
            return None
        if ob.name not in excluded:
            # The face index belongs to the EVALUATED object, so the material
            # is resolved against that; an unresolvable slot is "?" and never
            # guessed at.  Same handling as tools/r2366_crop_owner.py.
            mn = "?"
            try:
                obe = ob.evaluated_get(dg)
                if obe.type == 'MESH' and idx >= 0 and idx < len(obe.data.polygons):
                    mi = obe.data.polygons[idx].material_index
                    if 0 <= mi < len(obe.material_slots):
                        m = obe.material_slots[mi].material
                        mn = m.name if m else "?"
            except Exception:                                  # noqa: BLE001
                mn = "?"
            return ob.name, loc, (loc - Vector(origin)).length, mn
        step = (loc - o).length + 1e-3
        o = loc + direction * 1e-3
        rem -= step
    return None


def frame_result(sc, dg, cam, car, excluded, prev=None):
    """One frame.  `prev` is an earlier pass's result, min-combined into this."""
    eye = Vector(cam["p"])
    right, up, fwd = cam_basis(cam["q"])
    lens = float(cam["lens"])
    samples = car_samples(car["loc"], car["rot"], car.get("contacts", {}))

    n = len(samples)
    occ = [None] * n            # (name, dist) or None
    front = [False] * n
    inview = 0
    dists = []
    xs, ys = [], []
    for i, (p, nrm, tag) in enumerate(samples):
        d = p - eye
        dist = d.length
        if dist < 1e-6:
            continue
        dn = d / dist
        dists.append(dist)
        front[i] = nrm.dot(dn) < 0.0 or tag != "hull"
        px, py, z = project(p, eye, right, up, fwd, lens)
        if px is not None:
            xs.append(px)
            ys.append(py)
            if -W * 0.02 <= px <= W * 1.02 and -H * 0.02 <= py <= H * 1.02:
                inview += 1
        h = first_hit(sc, dg, eye, dn, dist - EPS_M, excluded)
        if h is not None:
            occ[i] = (h[0], h[2], h[1].z, h[3])

    if prev is not None:
        pocc = prev.get("_occ")
        if pocc:
            for i in range(n):
                a, b = occ[i], pocc[i]
                if b is not None and (a is None or b[1] < a[1]):
                    occ[i] = tuple(b)

    nf = sum(1 for f in front if f) or 1
    n_occ = sum(1 for o in occ if o is not None)
    n_occ_f = sum(1 for i, o in enumerate(occ) if o is not None and front[i])

    by_owner = {}
    by_chan = {"solid": 0, "fence": 0, "veg": 0, "surface": 0}
    by_chan_f = {"solid": 0, "fence": 0, "veg": 0, "surface": 0}
    for i, o in enumerate(occ):
        if o is None:
            continue
        rec = by_owner.setdefault(o[0], [0, 0.0, 0.0, {}])
        rec[0] += 1
        rec[1] += o[1]
        rec[2] += o[2]
        rec[3][o[3]] = rec[3].get(o[3], 0) + 1
        ch = channel_of(o[0], o[3])
        by_chan[ch] += 1
        if front[i]:
            by_chan_f[ch] += 1

    owner = owner_n = owner_mat = None
    owner_d = owner_z = None
    if by_owner:
        owner = max(by_owner, key=lambda k: (by_owner[k][0], -by_owner[k][1]))
        owner_n = by_owner[owner][0]
        owner_d = by_owner[owner][1] / owner_n
        owner_z = by_owner[owner][2] / owner_n
        owner_mat = max(by_owner[owner][3], key=by_owner[owner][3].get)

    res = {
        "f": car["f"],
        "beat": beat_of(car["f"]),
        "n": n,
        "n_front": sum(1 for f in front if f),
        "in_frame": inview > 0,
        "in_frame_n": inview,
        "dist": round(sum(dists) / max(1, len(dists)), 3),
        "occ_frac": round(n_occ / float(n), 4),
        "occ_frac_front": round(n_occ_f / float(nf), 4),
        "ch": {k: round(v / float(n), 4) for k, v in by_chan.items()},
        "ch_front": {k: round(v / float(nf), 4) for k, v in by_chan_f.items()},
        "owner": owner,
        "owner_n": owner_n,
        "owner_dist": None if owner_d is None else round(owner_d, 2),
        "owner_z": None if owner_z is None else round(owner_z, 2),
        "owner_mat": owner_mat,
        "owner_ch": None if owner is None else channel_of(owner, owner_mat),
        "cx": None if not xs else round((min(xs) + max(xs)) * 0.5 / W, 4),
        "cy": None if not ys else round((min(ys) + max(ys)) * 0.5 / H, 4),
        "_occ": occ,
    }
    return res


# ---------------------------------------------------------------------------
# Visibility hygiene.  What the raycast sees must be what the frame renders.
# ---------------------------------------------------------------------------
def align_visibility(sc):
    """Make the depsgraph agree with the render, and say what it changed.

    `scene.ray_cast` evaluates the VIEW LAYER depsgraph.  An object with
    hide_viewport set is not in it and would be silently invisible to every ray
    even though it renders; an object with hide_render set IS in it and would
    be counted as an occluder even though it never appears in a frame.  Both
    are instrument bugs of exactly the kind this project keeps finding after
    the fact, so both are handled and both are counted.
    """
    revealed = hidden = 0
    excluded = set()

    def coll_render_hidden(ob):
        for c in ob.users_collection:
            if c.hide_render:
                return True
        return False

    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        if ob.hide_render or coll_render_hidden(ob):
            excluded.add(ob.name)
            hidden += 1
            continue
        if ob.hide_viewport:
            ob.hide_viewport = False
            revealed += 1
        try:
            if ob.name in sc.view_layer.objects and ob.hide_get():
                ob.hide_set(False)
                revealed += 1
        except Exception:                                     # noqa: BLE001
            pass
    for c in bpy.data.collections:
        if c.hide_viewport and not c.hide_render:
            c.hide_viewport = False
            revealed += 1
    log("visibility: %d render-hidden objects EXCLUDED from the raycast, "
        "%d viewport-hidden revealed" % (hidden, revealed))
    return excluded


def car_object_names():
    """Every name that could be the car, so it can never occlude itself.

    Verified by NAME and reported, not assumed.  In a module rebuild the car is
    not in the scene at all and this set is empty of matches — which is stated
    in the output rather than left to look like a successful exclusion.
    """
    pats = ("CAR_", "CARRIG_", "BB_", "EC_", "FW_", "MB_", "NOSE_", "RW_",
            "SP_", "SW_", "brake_assembly", "halo_assembly", "suspension_",
            "wheel_tyre", "DRV_", "driver_")
    got = set()
    for ob in bpy.data.objects:
        for p in pats:
            if ob.name.startswith(p):
                got.add(ob.name)
                break
    return got


# ---------------------------------------------------------------------------
# SELFTEST
# ---------------------------------------------------------------------------
def _mk_plane(name, centre, half_x, half_z, axis="y"):
    """An axis-aligned quad, as one object, named."""
    cx, cy, cz = centre
    if axis == "y":
        v = [(cx - half_x, cy, cz - half_z), (cx + half_x, cy, cz - half_z),
             (cx + half_x, cy, cz + half_z), (cx - half_x, cy, cz + half_z)]
    else:                                                     # horizontal
        v = [(cx - half_x, cy - half_z, cz), (cx + half_x, cy - half_z, cz),
             (cx + half_x, cy + half_z, cz), (cx - half_x, cy + half_z, cz)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _mk_box(name, centre, half, mesh=None):
    cx, cy, cz = centre
    hx, hy, hz = half
    vs = [(cx + sx * hx, cy + sy * hy, cz + sz * hz)
          for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    fs = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
          (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    if mesh is not None:
        base = len(mesh.vertices)
        return vs, [tuple(i + base for i in f) for f in fs]
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _mk_multibox(name, boxes):
    """Several boxes as ONE object — a bridge is one object, deck and piers."""
    vs, fs = [], []
    for centre, half in boxes:
        cx, cy, cz = centre
        hx, hy, hz = half
        base = len(vs)
        vs += [(cx + sx * hx, cy + sy * hy, cz + sz * hz)
               for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
        fs += [tuple(i + base for i in f) for f in
               [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
                (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]]
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _clean():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


# camera at the origin, 1.5 m up, looking down +Y (Blender -Z forward).
# q rotates -Z onto +Y and +Y onto +Z: a -90 degree turn about X... which is
# w = cos(45), x = sin(45).
_Q_LOOK_Y = (math.cos(math.radians(45.0)), math.sin(math.radians(45.0)), 0.0, 0.0)
_Q_LOOK_MY = (0.0, 0.0, math.cos(math.radians(45.0)), math.sin(math.radians(45.0)))


def _ctrl_cam(q=None, p=(0.0, 0.0, 1.5), lens=50.0):
    return {"p": list(p), "q": list(q or _Q_LOOK_Y), "lens": lens}


def _ctrl_car(y=50.0, x=0.0, z=0.0, yaw=math.pi * 0.5):
    """Car `y` metres down +Y, pointing along +Y, sitting on z."""
    loc = [x, y, z]
    rot = [0.0, 0.0, yaw]
    ax, ay, az = car_matrix(rot)
    o = Vector(loc)
    con = {}
    for nm, sx, sy in (("FL", 1, 1), ("FR", 1, -1), ("RL", -1, 1), ("RR", -1, -1)):
        con[nm] = list(o + ax * (sx * 1.8) + ay * (sy * 0.85) + az * 0.345)
    return {"f": 1, "loc": loc, "rot": rot, "contacts": con}


def selftest():
    fails = []
    ran = []

    def check(name, cond, detail):
        ran.append(name)
        if cond:
            print("  PASS  %-14s %s" % (name, detail))
        else:
            print("  FAIL  %-14s %s" % (name, detail))
            fails.append(name)

    def run(excluded=frozenset(), cam=None, car=None):
        sc = bpy.context.scene
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        return frame_result(sc, dg, cam or _ctrl_cam(), car or _ctrl_car(),
                            set(excluded))

    print("\n=== SELFTEST: the controls this sweep must fail if it is broken ===")

    # 1. clear line of sight, empty scene
    _clean()
    r = run()
    check("clear", r["occ_frac"] == 0.0 and r["in_frame"],
          "empty scene -> occ_frac=%.3f in_frame=%s" % (r["occ_frac"], r["in_frame"]))

    # 2. a plane deliberately between camera and car
    _clean()
    _mk_plane("CTRL_Blocker", (0.0, 25.0, 5.0), 30.0, 30.0)
    r = run()
    check("blocker", r["occ_frac"] == 1.0 and r["owner"] == "CTRL_Blocker",
          "wall at 25 m -> occ_frac=%.3f owner=%s dist=%s"
          % (r["occ_frac"], r["owner"], r["owner_dist"]))

    # 3. THE DEPTH TEST.  Same plane, behind the car.
    _clean()
    _mk_plane("CTRL_Behind", (0.0, 75.0, 5.0), 30.0, 30.0)
    r = run()
    check("behind", r["occ_frac"] == 0.0 and r["owner"] is None,
          "wall at 75 m (car at 50) -> occ_frac=%.3f owner=%s"
          % (r["occ_frac"], r["owner"]))

    # 3b. and a plane a hand's breadth in front of the car still counts, so
    #     "behind" is not passing because the depth test is simply dead.
    #
    #     46.8 m, not 49 m.  The car is 5.698 m long and pointing down +Y, so
    #     its rearmost sample is at y = 47.15 and a wall at 49 m stands INSIDE
    #     it.  The first draft of this control put the wall at 49, got
    #     occ_frac = 0.603, and was WRONG ITSELF: the instrument was correctly
    #     reporting that the back third of the car is nearer the camera than
    #     the wall.  Left here at 46.8 with the reason, because a control that
    #     is quietly corrected until it passes is not a control.
    _clean()
    _mk_plane("CTRL_Just", (0.0, 46.8, 5.0), 30.0, 30.0)
    r = run()
    check("just-in-front", r["occ_frac"] == 1.0 and r["owner"] == "CTRL_Just",
          "wall at 46.8 m, 0.35 m ahead of the car's rearmost sample -> "
          "occ_frac=%.3f owner=%s" % (r["occ_frac"], r["owner"]))

    # 4. the car may never occlude itself — shown BOTH ways round
    _clean()
    _mk_box("CAR_Proxy", (0.0, 50.0, 0.5), (1.1, 2.9, 0.55))
    r = run(excluded={"CAR_Proxy"})
    check("self-excluded", r["occ_frac"] == 0.0 and r["owner"] is None,
          "car-shaped mesh at the car, excluded by name -> occ_frac=%.3f owner=%s"
          % (r["occ_frac"], r["owner"]))
    r = run()
    check("self-included", r["occ_frac"] > 0.0 and r["owner"] == "CAR_Proxy",
          "the SAME mesh not excluded -> occ_frac=%.3f owner=%s (so the "
          "exclusion above did something)" % (r["occ_frac"], r["owner"]))

    # 4b. an excluded object in FRONT of a real occluder must not mask it
    _clean()
    _mk_plane("CAR_Screen", (0.0, 10.0, 5.0), 30.0, 30.0)
    _mk_plane("CTRL_Real", (0.0, 30.0, 5.0), 30.0, 30.0)
    r = run(excluded={"CAR_Screen"})
    check("skip-through", r["occ_frac"] == 1.0 and r["owner"] == "CTRL_Real",
          "excluded sheet at 10 m in front of a wall at 30 m -> owner=%s"
          % r["owner"])

    # 5. THE BRIDGE TRAP.  Deck at 5..7 m on two piers at x=+-8; the car sits
    #    in the opening.  The object IS between camera and car.
    _clean()
    _mk_multibox("CTRL_Bridge", [
        ((0.0, 25.0, 6.0), (12.0, 1.0, 1.0)),          # deck
        ((-8.0, 25.0, 3.0), (1.2, 1.0, 3.0)),          # pier L
        ((+8.0, 25.0, 3.0), (1.2, 1.0, 3.0)),          # pier R
    ])
    r = run()
    check("bridge-gap", r["occ_frac"] == 0.0,
          "car under the deck, through the opening -> occ_frac=%.3f (the deck "
          "is between camera and car and hides nothing)" % r["occ_frac"])
    #    x = -16, not x = -8.  The camera is at x = 0 and the bridge is at half
    #    the distance to the car, so the line of sight to a car at x = -8
    #    crosses the bridge plane at x = -4 and misses the pier entirely.  The
    #    first draft asked for x = -8, got occ_frac = 0.000, and the instrument
    #    was right: nothing was in the way.  Recorded rather than silently
    #    retuned.
    r = run(car=_ctrl_car(x=-16.0))
    check("bridge-pier", r["occ_frac"] == 1.0 and r["owner"] == "CTRL_Bridge",
          "the SAME object, car moved onto the sightline through the pier -> "
          "occ_frac=%.3f owner=%s" % (r["occ_frac"], r["owner"]))

    # 6. partial
    _clean()
    _mk_plane("CTRL_Half", (-3.0, 25.0, 5.0), 3.0, 30.0)
    r = run()
    check("partial", 0.0 < r["occ_frac"] < 1.0,
          "half-width wall -> occ_frac=%.3f front=%.3f"
          % (r["occ_frac"], r["occ_frac_front"]))

    # 7. the ground the car stands on must not occlude it
    _clean()
    _mk_plane("SURF_Road", (0.0, 30.0, 0.0), 200.0, 200.0, axis="z")
    r = run(cam=_ctrl_cam(p=(0.0, 0.0, 0.6)), car=_ctrl_car(y=183.0))
    check("ground", r["occ_frac"] == 0.0,
          "road plane under a car at 183 m, camera 0.6 m up -> occ_frac=%.3f "
          "owner=%s" % (r["occ_frac"], r["owner"]))

    # 7b. ... but a crest in that road still must
    _clean()
    _mk_plane("SURF_Road", (0.0, 30.0, 0.0), 200.0, 200.0, axis="z")
    _mk_box("SURF_Crest", (0.0, 90.0, 0.9), (200.0, 2.0, 0.9))
    r = run(cam=_ctrl_cam(p=(0.0, 0.0, 0.6)), car=_ctrl_car(y=183.0))
    check("crest", r["occ_frac"] > 0.0 and r["owner"] == "SURF_Crest"
          and r["owner_ch"] == "surface",
          "a 0.9 m crest at 90 m -> occ_frac=%.3f owner=%s channel=%s"
          % (r["occ_frac"], r["owner"], r["owner_ch"]))

    # 8. channels are not pooled
    _clean()
    _mk_plane("BR_CatchFence_R12", (0.0, 25.0, 5.0), 30.0, 30.0)
    r = run()
    check("fence-channel", r["ch"]["fence"] == 1.0 and r["ch"]["solid"] == 0.0
          and r["owner_ch"] == "fence",
          "a catch fence -> fence=%.2f solid=%.2f"
          % (r["ch"]["fence"], r["ch"]["solid"]))
    _clean()
    _mk_plane("VEG_Tree_0042", (0.0, 25.0, 5.0), 30.0, 30.0)
    r = run()
    check("veg-channel", r["ch"]["veg"] == 1.0 and r["ch"]["solid"] == 0.0,
          "a tree -> veg=%.2f solid=%.2f" % (r["ch"]["veg"], r["ch"]["solid"]))

    # 8b. THE MATERIAL, NOT THE OBJECT NAME.  One object with a concrete name
    #     and a mesh-screen material is a see-through occlusion; the identical
    #     object with a concrete material is not.  This is the f2180 case.
    _clean()
    ob = _mk_plane("ARCH_PontPlongee", (0.0, 25.0, 5.0), 30.0, 30.0)
    ob.data.materials.append(bpy.data.materials.new("A_MeshDark"))
    r = run()
    check("mat-seethrough",
          r["ch"]["fence"] == 1.0 and r["ch"]["solid"] == 0.0
          and r["owner_mat"] == "A_MeshDark",
          "a concrete-named object whose hit face is A_MeshDark -> fence=%.2f "
          "solid=%.2f mat=%s"
          % (r["ch"]["fence"], r["ch"]["solid"], r["owner_mat"]))
    _clean()
    ob = _mk_plane("ARCH_PontPlongee", (0.0, 25.0, 5.0), 30.0, 30.0)
    ob.data.materials.append(bpy.data.materials.new("A_ConcPrecast"))
    r = run()
    check("mat-solid",
          r["ch"]["solid"] == 1.0 and r["ch"]["fence"] == 0.0
          and r["owner_mat"] == "A_ConcPrecast",
          "the SAME object with A_ConcPrecast -> solid=%.2f fence=%.2f mat=%s"
          % (r["ch"]["solid"], r["ch"]["fence"], r["owner_mat"]))

    # 9. off-frame is not an occlusion
    _clean()
    _mk_plane("CTRL_Blocker", (0.0, 25.0, 5.0), 30.0, 30.0)
    r = run(cam=_ctrl_cam(q=_Q_LOOK_MY))
    check("offframe", not r["in_frame"],
          "camera turned 180 degrees -> in_frame=%s" % r["in_frame"])
    r = run(cam=_ctrl_cam(p=(0.0, 60.0, 1.5)))
    check("behind-cam", not r["in_frame"],
          "car behind the camera -> in_frame=%s" % r["in_frame"])

    # 10. a render-hidden object must not occlude
    _clean()
    ob = _mk_plane("CTRL_HiddenInRender", (0.0, 25.0, 5.0), 30.0, 30.0)
    ob.hide_render = True
    ex = align_visibility(bpy.context.scene)
    r = run(excluded=ex)
    check("hide-render", r["occ_frac"] == 0.0,
          "hide_render wall -> occ_frac=%.3f (excluded=%s)"
          % (r["occ_frac"], sorted(ex)))

    # 10b. a viewport-hidden but rendering object MUST occlude
    _clean()
    ob = _mk_plane("CTRL_HiddenInViewport", (0.0, 25.0, 5.0), 30.0, 30.0)
    ob.hide_viewport = True
    ex = align_visibility(bpy.context.scene)
    r = run(excluded=ex)
    check("hide-viewport", r["occ_frac"] == 1.0,
          "hide_viewport wall that still renders -> occ_frac=%.3f" % r["occ_frac"])

    # 11. the min-combine across build passes takes the NEARER hit
    _clean()
    _mk_plane("CTRL_Far", (0.0, 40.0, 5.0), 30.0, 30.0)
    a = run()
    _clean()
    _mk_plane("CTRL_Near", (0.0, 15.0, 5.0), 30.0, 30.0)
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    b = frame_result(sc, dg, _ctrl_cam(), _ctrl_car(), set(), prev=a)
    check("min-combine", b["owner"] == "CTRL_Near" and b["occ_frac"] == 1.0,
          "pass A wall at 40 m, pass B wall at 15 m -> owner=%s dist=%s"
          % (b["owner"], b["owner_dist"]))
    _clean()
    _mk_plane("CTRL_Far2", (0.0, 40.0, 5.0), 30.0, 30.0)
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    c = frame_result(sc, dg, _ctrl_cam(), _ctrl_car(), set(), prev=b)
    check("min-combine2", c["owner"] == "CTRL_Near",
          "the near hit survives a later pass that only sees a far wall -> "
          "owner=%s" % c["owner"])

    print("\n%d control(s), %d failed%s"
          % (len(ran), len(fails), (": " + ", ".join(fails)) if fails else ""))
    return not fails


# ---------------------------------------------------------------------------
# The sweep
# ---------------------------------------------------------------------------
def build_module(name, noverify=True):
    if name == "surface":
        import build_surface as B
        return B.build()
    if name == "barriers":
        import build_barriers as B
        return B.build()
    if name == "terrain":
        import build_terrain as B
        return B.build()
    if name == "architecture":
        import build_architecture as B
        return B.build(verify=not noverify)
    if name == "dressing":
        import build_dressing as B
        return B.build()
    if name == "items":
        import build_items as B
        return B.build()
    raise RuntimeError("unknown module " + name)


def station_of(x, y):
    try:
        import world_contract as C
        s, u = C.world_su(float(x), float(y))
        return round(float(s), 1), round(float(u), 2)
    except Exception:                                          # noqa: BLE001
        return None, None


def runs_of(rows, key, thr, owner_key="owner"):
    """Contiguous frame runs where `key` >= thr, split when the owner changes."""
    out = []
    cur = None
    for r in rows:
        hot = r["in_frame"] and r[key] >= thr
        own = r.get(owner_key)
        if hot and cur is not None and cur["owner"] == own and r["f"] == cur["f1"] + 1:
            cur["f1"] = r["f"]
            cur["vals"].append(r[key])
            cur["dists"].append(r["owner_dist"])
        else:
            if cur is not None:
                out.append(cur)
                cur = None
            if hot:
                cur = {"f0": r["f"], "f1": r["f"], "owner": own,
                       "ch": r["owner_ch"], "mat": r.get("owner_mat"),
                       "vals": [r[key]], "dists": [r["owner_dist"]]}
    if cur is not None:
        out.append(cur)
    for r in out:
        r["frames"] = r["f1"] - r["f0"] + 1
        r["seconds"] = round(r["frames"] / float(FPS), 2)
        r["mean"] = round(sum(r["vals"]) / len(r["vals"]), 3)
        r["max"] = round(max(r["vals"]), 3)
        d = [x for x in r["dists"] if x is not None]
        r["dist"] = round(sum(d) / len(d), 1) if d else None
        del r["vals"], r["dists"]
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--mods", default="surface,barriers,architecture")
    ap.add_argument("--beats", default="5")
    ap.add_argument("--frames", default=None,
                    help="a,b or a-b, overriding --beats")
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--out", default="out/occlusion.json")
    ap.add_argument("--cast-after", default="architecture,items",
                    help="modules after which to fire a ray pass; results are "
                         "min-combined, so a job killed by the clock still "
                         "returns everything the modules it finished can say")
    ap.add_argument("--budget", type=float, default=3200.0)
    ap.add_argument("--load", default=None, help="a prebuilt world .blend")
    a = ap.parse_args(argv)

    print(">> r2651_occlusion_sweep  blender %s" % bpy.app.version_string)
    ok = selftest()
    if not ok:
        print(">> STAGE RESULT: SELFTEST_FAIL")
        return
    if a.selftest:
        print(">> STAGE RESULT: SELFTEST_OK")
        return
    print(">> selftest passed; the sweep below is measured with the same code")

    # -- the frames -------------------------------------------------------
    if a.frames:
        t = a.frames.replace("-", ",").split(",")
        f0, f1 = int(t[0]), int(t[1])
        want = list(range(f0, f1 + 1, a.stride))
    else:
        want = []
        for b in a.beats.split(","):
            b = b.strip()
            for nm, x, y in BEATS:
                if nm.split("_")[0] == b or nm == b:
                    want += list(range(x, y + 1, a.stride))
    want = sorted(set(want))
    log("frames: %d (%d..%d)" % (len(want), want[0], want[-1]))

    path = json.load(open(os.path.join(ROOT, "world", "camera_rig_path.json")))["path"]
    cam_by_f = {int(e["f"]): e for e in path}
    car_raw = json.load(open(os.path.join(ROOT, "world", "car_anim_measured.json")))
    car_by_f = {int(e["f"]): e for e in car_raw["frames"]}
    missing = [f for f in want if f not in cam_by_f or f not in car_by_f]
    if missing:
        raise SystemExit("no pose for %d frame(s), first %s"
                         % (len(missing), missing[:5]))

    # -- the world --------------------------------------------------------
    mods = [m.strip() for m in a.mods.split(",") if m.strip()]
    bad = [m for m in mods if m not in MODULE_ORDER]
    if bad:
        raise SystemExit("unknown module(s) %s" % bad)
    mods.sort(key=MODULE_ORDER.index)
    cast_after = set(m.strip() for m in a.cast_after.split(","))
    cast_after.add(mods[-1])

    built = []
    passes = []
    results = {}
    census = {}

    if a.load:
        bpy.ops.wm.open_mainfile(filepath=a.load)
        built = ["<%s>" % os.path.basename(a.load)]
        mods, cast_after = [], set()
        passes.append(("load", None))
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)

    import world_contract as C
    contract = C.__version__
    log("world_contract v%s" % contract)

    def cast_pass(label):
        sc = bpy.context.scene
        excl = align_visibility(sc)
        carnames = car_object_names()
        excl |= carnames
        log("pass %s: %d objects in scene, %d car-named objects excluded "
            "(%s)" % (label, len(bpy.data.objects), len(carnames),
                      "none present — the car is not in this build"
                      if not carnames else sorted(carnames)[:4]))
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        t0 = time.time()
        for i, f in enumerate(want):
            r = frame_result(sc, dg, cam_by_f[f], car_by_f[f], excl,
                             prev=results.get(f))
            results[f] = r
            for o in r["_occ"]:
                if o is not None:
                    k = "%s | %s" % (o[0], o[3])
                    census[k] = census.get(k, 0) + 1
            if i and i % 250 == 0:
                log("  pass %s: %d/%d frames (%.1f s)"
                    % (label, i, len(want), time.time() - t0))
        n_hot = sum(1 for f in want if results[f]["occ_frac"] > 0)
        log("pass %s done in %.1f s: %d/%d frames with any occlusion"
            % (label, time.time() - t0, n_hot, len(want)))
        passes.append((label, len(bpy.data.objects)))

    for m in mods:
        if time.time() - T0 > a.budget:
            log("BUDGET: %.0f s elapsed, stopping before %s" % (time.time() - T0, m))
            break
        t0 = time.time()
        log("building %s ..." % m)
        try:
            build_module(m)
            built.append(m)
            log("built %s in %.1f s (%d objects)"
                % (m, time.time() - t0, len(bpy.data.objects)))
        except Exception as e:                                 # noqa: BLE001
            import traceback
            traceback.print_exc()
            log("MODULE FAILED: %s: %r" % (m, e))
            break
        gc.collect()
        if m in cast_after:
            cast_pass(m)
            write(a.out, want, results, built, passes, census, contract, a)

    if not passes:
        cast_pass("load" if a.load else "empty")
    if a.load:
        cast_pass("loaded")
    write(a.out, want, results, built, passes, census, contract, a)

    rows = [results[f] for f in want]
    summarise(rows, census, built)
    incomplete = [m for m in ([] if a.load else
                              [x.strip() for x in a.mods.split(",")])
                  if m not in built]
    print(">> modules built: %s" % ",".join(built))
    if incomplete:
        print(">> MODULES NOT BUILT (the answer is blind to them): %s"
              % ",".join(incomplete))
    print(">> STAGE RESULT: %s"
          % ("OCC_PARTIAL" if incomplete else "OCC_OK"))


def write(out, want, results, built, passes, census, contract, a):
    rows = []
    for f in want:
        r = dict(results[f])
        r.pop("_occ", None)
        rows.append(r)
    d = os.path.dirname(os.path.abspath(out))
    if d:
        os.makedirs(d, exist_ok=True)
    meta = {
        "tool": "tools/r2651_occlusion_sweep.py",
        "built_from": "world modules (a rebuild), not a .blend"
                      if not a.load else a.load,
        "modules_built": built,
        "modules_requested": a.mods,
        "passes": passes,
        "world_contract": contract,
        "car_pose": "world/car_anim_measured.json (measured off car_anim.blend)",
        "camera": "world/camera_rig_path.json",
        "car_box": [CAR_LEN, CAR_W, CAR_BOT_Z, CAR_TOP_Z],
        "ride_height_m": RIDE_H,
        "samples_per_frame": 58,
        "eps_m": EPS_M,
        "W": W, "H": H, "sensor_mm": SENSOR, "fps": FPS,
        "note": "occ_frac is the fraction of 58 sample points on the car's "
                "oriented box whose ray from the camera origin is blocked by "
                "world geometry nearer than the sample. occ_frac_front counts "
                "only the camera-facing samples. Channels are never pooled: a "
                "catch fence is opaque to a raycast and transparent in the "
                "delivered frame. Geometry at the shutter centre instant only.",
    }
    json.dump({"meta": meta, "frames": rows}, open(out, "w"))
    log("wrote %s (%d frames)" % (out, len(rows)))


def summarise(rows, census, built):
    print("\n=== PER BEAT ===")
    print("%-12s %6s %6s %8s %8s %8s %8s %8s"
          % ("beat", "n", "inframe", "any", "half", "total", "fence", "veg"))
    for nm, a0, b0 in BEATS:
        sub = [r for r in rows if r["beat"] == nm]
        if not sub:
            continue
        inf = [r for r in sub if r["in_frame"]]
        n = len(sub)
        print("%-12s %6d %6d %8d %8d %8d %8d %8d"
              % (nm, n, len(inf),
                 sum(1 for r in inf if r["occ_frac_front"] > 0.0),
                 sum(1 for r in inf if r["occ_frac_front"] >= 0.5),
                 sum(1 for r in inf if r["occ_frac_front"] >= 0.95),
                 sum(1 for r in inf if r["ch_front"]["fence"] > 0.0),
                 sum(1 for r in inf if r["ch_front"]["veg"] > 0.0)))

    for thr, lab in ((0.05, "ANY (>=5% of the silhouette)"),
                     (0.5, "HALF (>=50%)"),
                     (0.95, "WHOLLY HIDDEN (>=95%)")):
        rr = runs_of(rows, "occ_frac_front", thr)
        print("\n=== RUNS, %s ===" % lab)
        if not rr:
            print("  none")
        for r in rr:
            print("  f%-5d-%-5d %4d fr %6.2f s  mean %.2f max %.2f  %-24s "
                  "%-16s %-7s %sm"
                  % (r["f0"], r["f1"], r["frames"], r["seconds"], r["mean"],
                     r["max"], r["owner"], r["mat"] or "-", r["ch"], r["dist"]))

    print("\n=== OCCLUDER CENSUS (object | material, sample-hits over the sweep) ===")
    tot = sum(census.values()) or 1
    for k in sorted(census, key=lambda x: -census[x])[:40]:
        ob, _, mt = k.partition(" | ")
        print("  %-52s %8d  %5.1f%%  [%s]"
              % (k, census[k], 100.0 * census[k] / tot, channel_of(ob, mt)))
    if not census:
        print("  nothing ever occluded a sample")


main()
