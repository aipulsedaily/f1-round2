"""A REAL negative control for depth_probe — the one v120 never had.

    blender -b --factory-startup -P v121/make_depth_true_neg.py

SUPERSEDED 2026-08-02: THE GENERATOR ITSELF IS NOW FIXED.
-----------------------------------------------------------------------------
v120/make_controls.py no longer builds the fake pair described below.  Its depth
section now writes THREE scenes — ctl_depth_pos.blend (dz = -0.200, sunk, must
FAIL), ctl_depth_float_pos.blend (dz = +0.200, the old mislabelled "neg",
renamed to say what it is, must FAIL) and ctl_depth_neg.blend (dz = 0.0, seated,
must PASS) — so the case this file was written to supply is generated in the
battery's own control set and no longer has to be bolted on afterwards.  All
three were run against tools/depth_probe.py on 2026-08-02 and produced FAIL /
FAIL / OK respectively.

This file is KEPT, unchanged in behaviour, as the record of how the defect was
found.  Its output ctl_depth_true_neg.blend is geometrically identical to the
repaired v120/ctl_depth_neg.blend; either may be used, and if the two ever
disagree, that disagreement is itself a finding.

v120/make_controls.py built its depth pair as (wheel 200 mm BELOW the deck top,
wheel 200 mm ABOVE it) and called the second one the negative control.  Under
the depth_probe of the day it printed DEPTH_PROBE_OK, so it looked like a
negative control that passes.  It was not one: a wheel 200 mm in the air is a
FLOATING car, which is a failure too — the instrument simply could not see it.
The repaired `tools/depth_probe.py` (2026-08-02) calls it, correctly,
DEPTH_PROBE_FAIL, which leaves the battery with two positive controls and none
that must pass.

This builds the missing one: the SAME scene with the wheel resting exactly on
the deck.  It must come back DEPTH_PROBE_OK and exit 0.  If it does not, the
probe cannot tell a seated car from a broken one and no verdict it gives about
the world means anything.

Geometry copied from v120/make_controls.py so the only thing that differs
between the three controls is dz.
"""
import sys, os
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def cube(name, loc, size=1.0, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc)
    ob = bpy.context.object
    ob.name = name
    ob.data.name = name + "_mesh"
    ob.scale = scale
    return ob


def coll(name, objs):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    for ob in objs:
        for oc in list(ob.users_collection):
            oc.objects.unlink(ob)
        c.objects.link(ob)
    return c


fresh()
deck = cube("Turntable_Deck", (0.0, 0.0, 0.0), size=1.0, scale=(6.9, 6.9, 0.340))
deck.location = (0.0, 0.0, 0.340 - 0.170)          # deck top at z = 0.340
# dz = 0.0: the wheel's underside sits exactly on the deck top.
part = cube("CAR_Wheel", (0.0, 0.0, 0.340 + 0.0 + 0.25), size=0.5)
coll("CAR", [part])
coll("SHOWROOM", [deck])
p = os.path.join(HERE, "ctl_depth_true_neg.blend")
bpy.ops.wm.save_as_mainfile(filepath=p, compress=True)
print("[CTL] wrote", p, os.path.getsize(p))
