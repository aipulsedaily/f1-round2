"""The four deliverable cameras.

Car is nose-+X, centred on the platform, tyres touching z = S.TT_TOP.
"""

import math

import bpy
from mathutils import Vector

import common as C
import s02_showroom as S

CAR_MID = Vector((0.10, 0.0, S.TT_TOP + 0.42))


def _coll():
    return C.collection("CAMERAS")


def make_cam(name, loc, target, lens, coll, sensor=36.0,
             dof=False, fstop=4.0, focus_offset=0.0, roll=0.0):
    cd = bpy.data.cameras.get(name)
    if cd is None:
        cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.clip_start = 0.05
    cd.clip_end = 500.0

    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, cd)
    else:
        ob.data = cd
    if ob.name not in coll.objects:
        for c in list(ob.users_collection):
            c.objects.unlink(ob)
        coll.objects.link(ob)

    loc_v, tgt_v = Vector(loc), Vector(target)
    ob.location = loc_v
    d = tgt_v - loc_v
    eul = d.to_track_quat("-Z", "Y").to_euler()
    if roll:
        eul.rotate_axis("Z", 0.0)
    ob.rotation_euler = eul

    cd.dof.use_dof = dof
    cd.dof.focus_distance = d.length + focus_offset
    cd.dof.aperture_fstop = fstop
    cd.dof.aperture_blades = 8
    return ob


SPECS = [
    # name, location, target, lens, dof, fstop
    # Framing is set from frame_width = sensor * distance / lens against the car's
    # 5.63 m length: 55 mm on the front quarter only covered 5.8 m and clipped the
    # wings, and 62 mm on the rear quarter covered 4.7 m.
    ("CAM_FrontQuarter", (7.05, -5.35, 1.95), (0.05, 0.0, S.TT_TOP + 0.38), 47.0, True, 5.6),
    ("CAM_RearQuarter", (-7.10, 5.55, 1.98), (-0.55, 0.0, S.TT_TOP + 0.34), 45.0, True, 5.6),
    # D076: at z=0.545 and 6.2 m out, the dais top annulus and flank filled the
    # bottom 40 % of frame and the car sat small and high. Move in close and lift
    # just enough to shoot over the rim while staying below the car's shoulder.
    # f/3.2 was far too shallow. Measured at 8K on a matched centre crop, this frame
    # scored 1.858 on a high-frequency detail proxy against 6.32 and 6.03 for the
    # other two DOF cameras - the wheel face and the tyre sidewall lettering were
    # both mush at 1:1. A car is a large subject shot close; automotive work sits
    # at f/8-f/16 so the car is sharp end to end and only the room falls away.
    ("CAM_HeroLow", (4.05, -2.45, 0.700), (0.15, 0.05, S.TT_TOP + 0.24), 34.0, True, 9.0),
    # D011: this was at z=9.60 with the ceiling slab at 6.2, so it rendered the
    # underside of the ceiling - a flat brown field. Orthographic sits below the
    # coves and gives a true plan view with no perspective distortion.
    ("CAM_TopDown", (0.05, 0.0, 5.85), (0.05, 0.0, S.TT_TOP + 0.30), 50.0, False, 8.0),
]


def build():
    coll = _coll()
    made = []
    for name, loc, tgt, lens, dof, fstop in SPECS:
        ob = make_cam(name, loc, tgt, lens, coll, dof=dof, fstop=fstop)
        made.append(ob)

    # top-down: orthographic plan view. A camera at identity rotation already
    # looks down -Z with +Y up, so world +X (the car's length) maps to the frame's
    # wide axis - the extra 90 deg roll I first applied stood the car on end.
    td = bpy.data.objects["CAM_TopDown"]
    td.rotation_euler = (0.0, 0.0, 0.0)
    td.data.type = "ORTHO"
    td.data.ortho_scale = 6.60

    bpy.context.scene.camera = bpy.data.objects["CAM_FrontQuarter"]
    return {"cameras": [o.name for o in made],
            "active": bpy.context.scene.camera.name}
