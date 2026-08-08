"""THE COMPARISON RIG, REBUILT FROM THE FILM'S OWN LIGHTING.  R2-3121.

    /opt/blender-5.2.0-linux-x64/blender -b world/surface_test_filmpose.blend \
        --factory-startup -noaudio -P world/build_rig_filmpose.py

WHY THIS FILE EXISTS
====================
`world/surface_test_filmpose.blend` is the rig every number in R2-1036 and
R2-1042 was measured on, and **it had no saved builder** (R2-1078).  It could
not be rebuilt, audited or diffed, and what it actually contained was:

    TEST_Sun      direction to sun (0.000000,  0.976407, 0.215939)
    the film's                     (0.517854, -0.827767, 0.215939)
                  -- 139.61 deg apart in bearing, and IDENTICAL in elevation
                     to six decimals, which is exactly why it survived two
                     investigations: elevation is invariant under precisely
                     this rotation.
    exposure      -3.048, the value R2-071 measured as over-exposing by 0.586
                  stops and replaced with -3.628
    TEST_Sky      a bare 3-node Sky Texture: no cloud decks, no atmosphere
    Light         a factory-default 1000 W POINT lamp, still in the file

It produced two confident wrong verdicts that were relayed to the client.
R2-2821 finally got `tools/rig_preflight.py` to execute and it returned FAIL
with those three findings; R2-3121's choice was rebuild or delete, because the
one thing not available is leaving a rig on disk that disagrees with the film
by 139.61 deg for the next agent to measure on.

WHAT IS AND IS NOT REBUILT
==========================
The rig's SUBJECT -- the `W_Surface` collection, 60 meshes, and the four
`CAM_filmpose_*` poses -- is what the rig is FOR, and it is untouched.  Only
the LIGHTING is rebuilt, and it is rebuilt by calling `world/build_sky.py`,
**the module the film itself is lit by**, rather than by setting a sun
rotation by hand.  A rig lit by a hand-typed copy of the film's sun is a rig
that will drift from the film again the first time the film's sun moves; a rig
lit by the film's own builder cannot.

NOTHING IS RETYPED.  The three numbers this file checks its own output against
come from `world/world_contract.py` (`SUN_DIR`) and `world/film_exposure.py`
(`FILM_EXPOSURE`) at run time -- the same two modules `tools/rig_preflight.py`
reads.  A rebuild that carried its own copy of the constant it is matching
would be checking itself, which is R2-1078's finding one level up.

THE VERIFICATION IS BEFORE THE SAVE, NOT AFTER IT
=================================================
This asserts the rebuilt sun, grade and world against those constants and
REFUSES TO WRITE THE BLEND if any of them is out.  A builder that saves first
and reports afterwards leaves a wrong rig on disk next to a log saying it is
wrong, which is the state this file exists to end.  One `>> STAGE RESULT:`
line is printed, at the end, and the exit code comes from the same string.
"""
import math
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (R2, os.path.join(R2, "tools"), os.path.join(R2, "world")):
    if p not in sys.path:
        sys.path.insert(0, p)

import gate_exit                                                 # noqa: E402

#: rig_preflight's own tolerances, imported so the builder and the guard
#: cannot disagree about what "agrees with the film" means.
import rig_preflight as RP                                       # noqa: E402

RIG = os.path.join(R2, "world", "surface_test_filmpose.blend")


def _elev_bearing(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    x, y, z = (c / n for c in v)
    return math.degrees(math.asin(max(-1.0, min(1.0, z)))), \
        math.degrees(math.atan2(y, x))


def rebuild():
    import bpy
    import world_contract as WC
    import film_exposure as FE
    import build_sky as SKY

    sun_ref = tuple(WC.SUN_DIR)
    exp_ref = float(FE.FILM_EXPOSURE)
    scene = bpy.context.scene

    print(">> RIG    %s" % bpy.data.filepath)
    print(">> BEFORE sun %s  exposure %.4f  world %s"
          % (_sun_of(bpy), scene.view_settings.exposure,
             scene.world.name if scene.world else None))

    # ---- 1. remove the lighting that was wrong -----------------------------
    # NOT the surface, NOT the camera poses.  `read_rig()` takes the FIRST SUN
    # lamp it finds, so leaving TEST_Sun in the file would let the old sun be
    # measured again even with the film's sun sitting beside it.
    removed = []
    for name in ("TEST_Sun", "Light"):
        ob = bpy.data.objects.get(name)
        if ob is not None:
            removed.append("%s (%s)" % (name, ob.type))
            bpy.data.objects.remove(ob, do_unlink=True)
    for w in list(bpy.data.worlds):
        if w.name.startswith("TEST_"):
            removed.append("world %s" % w.name)
            bpy.data.worlds.remove(w)
    for lt in list(bpy.data.lights):
        if lt.users == 0:
            bpy.data.lights.remove(lt)
    print(">> PURGED %s" % (removed or "nothing",))

    # ---- 2. build the film's sky, with the film's own builder --------------
    summary = SKY.build(scene, camera=scene.camera)
    if scene.camera is not None:
        SKY.bind_camera(scene.camera)

    # ---- 3. the grade, from the film's module -------------------------------
    # build_sky.py deliberately never writes `scene.view_settings` ("exposure
    # is the camera's"), so the grade is set here -- from FILM_EXPOSURE, not
    # from a literal.
    vs = scene.view_settings
    vs.view_transform = "AgX"
    vs.look = "None"
    vs.exposure = exp_ref

    # ---- 4. the checks, BEFORE the save -------------------------------------
    # THE DEPSGRAPH UPDATE IS LOAD-BEARING, AND ITS ABSENCE WAS CAUGHT BY THIS
    # BLOCK RATHER THAN BY A RENDER.  `build_sun()` sets the lamp's
    # `rotation_quaternion`; `read_rig()` reads `matrix_world`, which is
    # evaluated data and still holds the IDENTITY until the view layer is
    # updated.  The first run of this file therefore measured its own freshly
    # built sun as (-0.0, -0.0, 1.0) -- straight up, 77.53 deg from the film --
    # and refused to save, which is exactly the behaviour the docstring
    # promises: a builder that saved first would have put a SECOND wrong rig on
    # disk, with a different wrong sun, and the log saying so would have been
    # read by nobody.
    bpy.context.view_layer.update()
    rig = RP.read_rig()
    bad = RP.evaluate(rig, sun_ref, exp_ref)
    el_r, bg_r = _elev_bearing(rig["sun_dir"])
    el_f, bg_f = _elev_bearing(sun_ref)
    print(">> AFTER  sun rig  %s" % (tuple(round(c, 6) for c in rig["sun_dir"]),))
    print(">> AFTER  sun film %s" % (tuple(round(c, 6) for c in sun_ref),))
    print(">> AFTER  elevation %+.6f deg (film %+.6f), bearing %+.6f deg "
          "(film %+.6f), total %.6f deg apart"
          % (el_r, el_f, bg_r, bg_f, RP._ang(rig["sun_dir"], sun_ref)))
    print(">> AFTER  grade %.4f / %s / look %s   film %.3f / AgX / look None"
          % (rig["exposure"], rig["view_transform"], rig["look"], exp_ref))
    print(">> AFTER  world %d nodes, %d sky objects, %d tris"
          % (len(rig["world_nodes"]), summary["objects"],
             summary["triangles"]))
    for f in bad:
        print("   FAIL %-14s %s" % (f["check"], f["detail"]))
    if bad:
        # NOT SAVED.  See the docstring.
        return 1, len(bad)

    bpy.ops.wm.save_as_mainfile(filepath=RIG, compress=False)
    print(">> SAVED  %s (%.1f MB)"
          % (RIG, os.path.getsize(RIG) / 1e6))
    return 0, 0


def _sun_of(bpy):
    from mathutils import Vector
    for o in bpy.data.objects:
        if o.type == "LIGHT" and o.data.type == "SUN":
            d = (o.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
            return tuple(round(c, 6) for c in (-d.x, -d.y, -d.z))
    return None


# THE EXIT IS OUTSIDE THE `try`.  R2-2108: `SystemExit` derives from
# `BaseException`, so an exit raised inside the handler's own scope gets caught
# by the handler and the file prints TWO verdicts.  Exactly one is printed here.
rc = None
try:
    rc, n = rebuild()
except BaseException as exc:                                     # noqa: BLE001
    import traceback
    traceback.print_exc()
    print(">> STAGE RESULT: RIG_REBUILD_FAIL (builder raised %r)" % (exc,))
    raise SystemExit(1)

print(">> STAGE RESULT: %s"
      % ("RIG_REBUILD_OK" if rc == 0 else
         "RIG_REBUILD_FAIL (%d finding(s); blend NOT written)" % n))
raise SystemExit(rc)
