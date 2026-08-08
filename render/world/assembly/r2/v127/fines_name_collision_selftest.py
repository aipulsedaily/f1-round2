"""R2-2101 -- THE `BREACH_Fines` NAME COLLISION, REPRODUCED IN 3 SECONDS.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -noaudio \
        -P render/world/assembly/r2/v127/fines_name_collision_selftest.py

`run_rebuild21` died in `sim/apply_breach.py` with
`KeyError: bpy.data.collections["BREACH_Fines"]` after 1,234 s of fines work,
and `film21_breach.blend` does not exist.  Paying 1,234 s and 102 MB to see the
mechanism again would be absurd, and the mechanism does not need any of it: it
is a NAME COLLISION between a placeholder collection the applier makes itself
and the collection it then appends.

WHY THE LIBRARY'S OWN VERIFIER COULD NOT HAVE CAUGHT IT.
`sim/build_fines_lib.py --verify` runs the same three append lines and then
does `bpy.data.collections[COLL]` -- the identical lookup -- and it PASSES,
because it runs them in a scene wiped to FACTORY SETTINGS.  With no placeholder
there is no collision, the appended collection keeps its plain name, and the
lookup finds it.  The verifier reproduces the mechanism and not the CONTEXT,
so it proves the mechanism only.  That is why the round trip could read
"11,246 of 11,246 objects, worst error 1.70e-06 m" and the applier still die on
the same three lines.

This file supplies the context: it appends WITH the placeholder present, which
is what `apply_breach.build()` does.

TWO CASES, AND THE FIRST ONE MUST FAIL.
  CONTROL   the shipped lookup -- must raise KeyError.  If it ever stops
            raising, this test is worthless and says so out loud, because a
            reproduction that cannot reproduce is not evidence that a fix fixed
            anything.
  FIXED     carry the datablock through and take the placeholder's name back --
            must end with exactly one collection called `BREACH_Fines`, holding
            the appended objects, with the placeholder freed.

Nothing here touches `world/breach_fines.blend`, `sim/out/breach_film.npz` or
any film.  It writes one ~100 KB library into a temp dir and deletes nothing
else.
"""
import os
import sys
import tempfile

import bpy

COLL = "BREACH_Fines"
N_OBJ = 3
bad = []


def log(msg):
    print("   " + msg)


def wipe():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def write_library(path):
    """A tiny stand-in for world/breach_fines.blend: same collection NAME.

    The name is the whole mechanism.  Geometry and key counts are irrelevant to
    it, so this ships three cubes rather than 11,246 puffs.
    """
    wipe()
    c = bpy.data.collections.new(COLL)
    bpy.context.scene.collection.children.link(c)
    for i in range(N_OBJ):
        me = bpy.data.meshes.new("DB_p%05d" % i)
        me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [[0, 1, 2]])
        me.update()
        ob = bpy.data.objects.new("DB_p%05d" % i, me)
        c.objects.link(ob)
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=False)
    log("wrote stand-in library %s (%d objects in %r)"
        % (os.path.basename(path), N_OBJ, COLL))


def append_with_placeholder(path):
    """Exactly what `apply_breach.build()` does, in the same order.

    Returns (placeholder, appended).  The placeholder is created FIRST, which
    is the entire point -- `build()` makes all four BREACH_* collections up
    front and only decides how to fill the fines one 190 lines later.
    """
    wipe()
    root = bpy.data.collections.new("BREACH")
    bpy.context.scene.collection.children.link(root)
    placeholder = bpy.data.collections.new(COLL)          # <-- takes the name
    root.children.link(placeholder)
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = [COLL]
    appended = dst.collections[0]
    root.children.link(appended)
    log("placeholder is %r; the append landed as %r"
        % (placeholder.name, appended.name))
    return placeholder, appended


def case_control(path):
    """The SHIPPED code.  Must raise KeyError."""
    print("\n== CONTROL: the shipped lookup, which must FAIL ==")
    placeholder, appended = append_with_placeholder(path)
    if appended.name == COLL:
        bad.append("CONTROL: the append did NOT collide (it is %r), so this "
                   "test cannot reproduce the defect and proves nothing"
                   % appended.name)
        return
    bpy.data.collections.remove(placeholder)
    log("freed the placeholder; the survivor is still %r" % appended.name)
    try:
        got = bpy.data.collections[COLL]
        bad.append("CONTROL: bpy.data.collections[%r] RESOLVED to %r. Freeing "
                   "the placeholder renamed the survivor after all, so the "
                   "shipped code would have worked and the reproduction is "
                   "wrong." % (COLL, got.name))
        log("!! resolved -- THIS TEST IS WORTHLESS")
    except KeyError as exc:
        log("KeyError: %s   <-- R2-2101, reproduced" % exc)


def case_fixed(path):
    """The FIX.  Must end with one BREACH_Fines holding the appended objects."""
    print("\n== FIXED: carry the datablock, take the name back ==")
    placeholder, appended = append_with_placeholder(path)
    names_in = sorted(o.name for o in appended.all_objects)
    bpy.data.collections.remove(placeholder)
    appended.name = COLL
    if appended.name != COLL:
        bad.append("FIXED: the appended collection could not take the name "
                   "(it is %r)" % appended.name)
        return
    log("survivor renamed to %r" % appended.name)

    same = [c for c in bpy.data.collections if c.name == COLL]
    if len(same) != 1:
        bad.append("FIXED: %d collections are called %r" % (len(same), COLL))
    found = bpy.data.collections[COLL]
    if found is not appended:
        bad.append("FIXED: the name resolves to a different datablock")
    got = sorted(o.name for o in found.all_objects)
    if got != names_in or len(got) != N_OBJ:
        bad.append("FIXED: %r holds %r, expected the %d appended objects %r"
                   % (COLL, got, N_OBJ, names_in))
    else:
        log("%r holds the %d appended objects %s" % (COLL, len(got), got))
    # the placeholder must be GONE, not merely unlinked -- `main()` puts this
    # collection through `prove_curves`, and a freed datablock there is a crash
    if len(found.objects) == 0:
        bad.append("FIXED: the survivor is EMPTY, so prove_curves would be "
                   "handed nothing to prove")


def main():
    d = tempfile.mkdtemp(prefix="r2_2101_fines_")
    path = os.path.join(d, "stand_in_fines.blend")
    print("R2-2101 fines name-collision selftest")
    write_library(path)
    case_control(path)
    case_fixed(path)
    print()
    for b in bad:
        print("   FAIL " + b)
    ok = not bad
    print(">> STAGE RESULT: %s"
          % ("FINES_COLLISION_SELFTEST_OK" if ok
             else "FINES_COLLISION_SELFTEST_FAIL"))
    return 0 if ok else 1


sys.exit(main())
