"""Assemble the monocoque plus every part module into one car.

The old s04_car.build() made the whole car itself. Now it only supplies the
lofted monocoque skin; everything else - wings, wheels, brakes, suspension,
cockpit, bodywork detail - comes from independently authored modules in
build/parts/, each of which was iterated against its own renders.

A part that fails to import or build is reported and skipped rather than taking
the whole assembly down, so one bad module never blocks a render.
"""

import importlib
import os
import sys
import traceback

import bpy

import common as C
import spec as S

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
PARTS_DIR = os.path.join(BUILD_DIR, "parts")
if PARTS_DIR not in sys.path:
    sys.path.insert(0, PARTS_DIR)

# Parts that replace what the old monolithic builder used to make. Anything the
# old s04_car still emits that a part now owns must NOT be built twice.
SKIP_MODULES = {"_smoke"}

# Three rival monocoque rebuilds live in build/parts/ while the judge decides.
# Building all of them would stack three bodies in the same space, so exactly one
# is ever assembled: set this to the winner's module name. None => keep the old
# s04_car loft.
MONOCOQUE_CHOICE = "monocoque_b"   # workflow judge winner, score 7.6/10


def discover_parts():
    if not os.path.isdir(PARTS_DIR):
        return []
    names = []
    for fn in sorted(os.listdir(PARTS_DIR)):
        if not fn.endswith(".py"):
            continue
        name = fn[:-3]
        # Anything underscore-prefixed is scratch: agents drop probe//harness
        # files here while iterating (_smoke, _swprobe). Only real parts assemble.
        if name in SKIP_MODULES or name.startswith("_"):
            continue
        names.append(name)
    return names


def car_root(coll):
    root = bpy.data.objects.get("CAR_ROOT")
    if root is None:
        root = bpy.data.objects.new("CAR_ROOT", None)
    for c in list(root.users_collection):
        c.objects.unlink(root)
    coll.objects.link(root)
    root.empty_display_size = 0.4
    root.location = (0.0, 0.0, S.GROUND)
    return root


def build(include_monocoque=None, only=None, verbose=True):
    C.purge_collection("CAR")
    coll = C.collection("CAR")
    root = car_root(coll)

    made, report = [], {}

    # A dedicated `monocoque` part supersedes s04_car's loft. Build the old body
    # only when no replacement exists, otherwise the two occupy the same space.
    parts = discover_parts()
    # keep at most one monocoque: the chosen winner, or none at all
    parts = [p for p in parts
             if not p.startswith("monocoque") or p == MONOCOQUE_CHOICE]
    if include_monocoque is None:
        include_monocoque = MONOCOQUE_CHOICE is None

    if include_monocoque:
        import s04_car
        importlib.reload(s04_car)
        try:
            body = s04_car.build_body(coll)
            made.append(body)
            C.assign(body, S.mat("LiveryPaint"))
            report["monocoque"] = {"ok": True, "objects": 1,
                                   "polys": len(body.data.polygons)}
        except Exception:
            report["monocoque"] = {"ok": False, "error": traceback.format_exc()[-600:]}

    for name in parts:
        if only and name not in only:
            continue
        try:
            mod = importlib.import_module(name)
            importlib.reload(mod)
            before = set(coll.objects.keys())
            objs = mod.build(coll)
            if not objs:
                objs = [o for o in coll.objects if o.name not in before]
            polys = sum(len(o.data.polygons) for o in objs
                        if getattr(o, "type", None) == "MESH")
            made.extend(objs)
            report[name] = {"ok": True, "objects": len(objs), "polys": polys}
        except Exception:
            report[name] = {"ok": False, "error": traceback.format_exc()[-600:]}

    for ob in made:
        try:
            if ob.parent is None and ob.name != "CAR_ROOT":
                ob.parent = root
        except (ReferenceError, AttributeError):
            pass

    total = sum(v.get("polys", 0) for v in report.values() if v.get("ok"))
    failed = [k for k, v in report.items() if not v.get("ok")]
    if verbose:
        for k, v in report.items():
            if v.get("ok"):
                print(f"  OK   {k:20s} objects={v['objects']:4d} polys={v['polys']}")
            else:
                print(f"  FAIL {k:20s}\n{v['error']}")
    return {"total_polys": total, "parts_ok": len(report) - len(failed),
            "parts_failed": failed, "report": report}
