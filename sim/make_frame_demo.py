"""THE DEMONSTRATOR.  NOT A CANDIDATE FOR THE FILM.  R2-273.

    blender -b render/film14_breach_r6.blend -P sim/make_frame_demo.py -- \
        --out render/film14_breach_r6_DEMO.blend

It exists to answer ONE question with a picture instead of an argument:

    IF the frame across the aperture broke, would the aperture read at 595 m?

The re-bake that would make it break costs 2h25m and is the coordinator's to
schedule.  Spending it on a hypothesis nobody has looked at is exactly the
mistake the six refuted beat-5 sightings were: a geometric prediction believed
without a render.  So this scene simply DELETES the members the re-bake would
be expected to remove, renders the closing frame, and prices the change.

WHY IT MUST NEVER SHIP.  A member that is deleted is a member that was never
there -- it does not fall on camera, it is absent in beat 1 as well, and the
film has no cuts to hide that in.  Every object it removes is removed on ALL
2,978 frames.  The blend is named _DEMO, this docstring is in the file, and a
marker object `DEMO_DO_NOT_SHIP` is added so that anything reading the scene
back can see it.

WHAT IT REMOVES, AND WHY THOSE
    BF_MUL05_S02..S07   mullion 5 above z 1.550.  The bake threw S00 and S01
                        (z 0.000..1.550) 4.7 m; the remaining 4.65 m stayed
                        only because `CON_MUL05_HEAD` holds it at 38.4 kN
                        against a 214 N dead load, across a head joint the
                        wall interface itself records as a 17.2 mm EXPANSION
                        GAP.  A stick curtain wall is bottom-anchored; a
                        mullion whose base has left does not hang from its
                        head.
    BF_TRN{0,1,2}_b04   the six transom stubs in bays 4 and 5.  Each has one
    BF_TRN{0,1,2}_b05   end bolted into mullion 5.  When mullion 5 goes they
                        lose half their support.

It removes nothing else, so the same negative controls hold: bays 0-3 and 6-9
must be pixel-identical to the R6 build.
"""
import argparse
import sys

import bpy

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
a = ap.parse_args(argv)

WANT = (["BF_MUL05_S%02d" % k for k in range(2, 8)]
        + ["BF_TRN%d_b%02d" % (l, b) for l in range(3) for b in (4, 5)])

gone, missing = [], []
for n in WANT:
    o = bpy.data.objects.get(n)
    if o is None:
        missing.append(n)
        continue
    bpy.data.objects.remove(o, do_unlink=True)
    gone.append(n)

if missing:
    print("STAGE RESULT: demo FAIL -- not in the scene: %s" % missing)
    raise SystemExit(1)

# a marker so nothing can mistake this scene for a delivery
me = bpy.data.meshes.new("DEMO_DO_NOT_SHIP")
me.from_pydata([(0.0, 0.0, -900.0)], [], [])
me.update()
mk = bpy.data.objects.new("DEMO_DO_NOT_SHIP", me)
bpy.context.scene.collection.objects.link(mk)
mk.hide_render = True

left = [o.name for o in bpy.data.objects if o.name.startswith("BF_")]
print("removed %d: %s" % (len(gone), gone))
print("BF_* still in the scene: %d  %s" % (len(left), sorted(left)))
bpy.ops.wm.save_as_mainfile(filepath=a.out)
print("STAGE RESULT: demo PASS -- wrote %s (NOT A DELIVERY)" % a.out)
