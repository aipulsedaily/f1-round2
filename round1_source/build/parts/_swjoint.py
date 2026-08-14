"""Scratch harness: steering wheel + the bare CI_column, for looking at the QR
joint on its own. Underscore-prefixed, so s08_assemble skips it.

    tools/pv.sh --part _swjoint --centre 0.535 0 0.486 --radius 0.075 \
                --az -55 --el 40 --out /tmp/sw_hero.png

SWJOINT_ONLY=qr strips the wheel down to the four QR objects, which is what it
takes to get a clean side elevation of the joint (the 280 mm rim occludes any
view perpendicular to the column axis). SWJOINT_MOD names an alternative wheel
module, for rendering a before/after pair against the same camera.
"""

import importlib
import os

import bpy

NAME = "_swjoint"


def build(coll, ctx=None):
    wheel = os.environ.get("SWJOINT_MOD", "steering_wheel")
    only_qr = os.environ.get("SWJOINT_ONLY", "") == "qr"
    sw = list(importlib.import_module(wheel).build(coll) or [])
    ci = list(importlib.import_module("cockpit_interior").build(coll) or [])
    keep = []
    for ob in sw:
        if not only_qr or ob.name.split("_", 1)[1] in (
                "QRBody", "QRSpline", "QRCollar", "QRPins"):
            keep.append(ob)
        else:
            bpy.data.objects.remove(ob, do_unlink=True)
    for ob in ci:
        if ob.name == "CI_column":
            keep.append(ob)
        else:
            bpy.data.objects.remove(ob, do_unlink=True)
    return keep
