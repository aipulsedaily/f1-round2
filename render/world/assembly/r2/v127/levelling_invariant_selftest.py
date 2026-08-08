"""R2-2101 -- THE LEVELLING INVARIANT, WITH THE CONTROLS THAT MAKE IT MEAN
SOMETHING, in a 5-lamp scene instead of a 10 GB film.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -noaudio \
        -P render/world/assembly/r2/v127/levelling_invariant_selftest.py

`showroom_lighting.assert_levelled` used to check two things -- the mark is
there, and it is the right number -- and the rig's real shape was carried
around beside it as prose: *"46,203.313 W over 23 lamps"*, restated in
`docs/NEXT-REBUILD.md`, in three verify scripts, and as a REFUSAL in
`tools/build_film_scene.py:481` (*"a 24th lamp breaks it"*).

R2-2101 replaced the count with the two properties the count was standing in
for.  This file is the evidence that the replacement is stronger and not
merely different, because an assertion nobody has ever seen FAIL is not an
assertion:

  A  a levelled rig                                     must PASS
  B  a lamp added AFTER levelling, so it never got a
     stamp and sits 3.628 stops under the room          must REFUSE   (film9,
                                                        one lamp at a time)
  C  a lamp that was stamped and then EDITED, so the
     stamp is right and the watts are not               must REFUSE   (this is
                                                        the case a stamp count
                                                        can never catch)
  D  a 24th lamp added the CORRECT way -- before the
     levelling -- must PASS.  This is the change the
     old rule refused for 955 defect entries.
  E  the strip is NOT added to a scene that is not the
     showroom                                           must add nothing

Nothing here opens a film, and it writes no blend at all.
"""
import os
import sys

import bpy

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "world"))

import showroom_lighting as SL                                   # noqa: E402
import showroom_strip as ST                                      # noqa: E402

bad = []


def log(m):
    print("   " + m)


def lamp(name, loc, watts, coll, size=1.0, size_y=1.0):
    ld = bpy.data.lights.new(name, "AREA")
    ld.shape = "RECTANGLE"
    ld.size, ld.size_y = size, size_y
    ld.energy = watts
    ob = bpy.data.objects.new(name, ld)
    coll.objects.link(ob)
    ob.location = loc
    return ob


def fresh(with_rig=False):
    """An empty scene with a few lamps inside SL.SHELL.

    `with_rig=True` reproduces the four lamps `showroom_strip` measures for, at
    the sizes and energies it demands, so the strip will be added.
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    coll = bpy.data.collections.new(ST.RIG_COLLECTION)
    sc.collection.children.link(coll)
    if with_rig:
        for nm, w in ST.UNTOUCHED.items():
            lamp(nm, (0.0, 0.0, 3.0), w["energy"], coll,
                 size=w["size"], size_y=w["size_y"])
    else:
        lamp("Practical_A", (0.0, 0.0, 3.0), 100.0, coll)
        lamp("Practical_B", (2.0, 1.0, 2.0), 250.0, coll)
        lamp("Practical_C", (-3.0, -1.0, 1.0), 30.0, coll)
    # a lamp OUTSIDE the shell, which must never be counted or stamped
    lamp("Forecourt_Post", (18.0, 0.0, 3.0), 500.0, coll)
    bpy.context.view_layer.update()
    return sc, coll


def verdict(sc, want_pass, label):
    try:
        SL.assert_levelled(sc)
        got = "PASS"
        why = ""
    except SystemExit as exc:
        got = "REFUSED"
        why = str(exc).split(".")[0]
    ok = (got == ("PASS" if want_pass else "REFUSED"))
    log("%-56s %-8s (want %s) %s"
        % (label, got, "PASS" if want_pass else "REFUSED",
           "OK" if ok else "<<<< WRONG"))
    if why:
        log("      %s" % why[:150])
    if not ok:
        bad.append(label)
    return got


# --------------------------------------------------------------------------- #
print("R2-2101 levelling-invariant selftest\n")

print("== A: a levelled rig ==")
sc, coll = fresh()
man = SL.apply(sc, verbose=False)
m = SL.measure(sc)
log("interior lamps %d, stamps %d, base %.3f W x %.6f = %.3f W, on the "
    "datablocks %.3f W, residual %+.6f"
    % (m["n_interior_lamps"], m["n_lamp_stamps"], m["base_watts_from_stamps"],
       m["lift_multiplier"], m["identity_base_x_lift"],
       m["stamped_watts_now"], m["identity_residual_w"]))
if m["n_interior_lamps"] != 3:
    bad.append("A: expected 3 interior lamps, got %d" % m["n_interior_lamps"])
if "Forecourt_Post" in m["unstamped_interior_lamps"]:
    bad.append("A: the forecourt lamp was classified interior")
if bpy.data.lights["Forecourt_Post"].keys() and \
        SL.MARK + "energy" in bpy.data.lights["Forecourt_Post"].keys():
    bad.append("A: the forecourt lamp got a stamp")
verdict(sc, True, "a levelled rig")

print("\n== B: a lamp added AFTER levelling (film9, one lamp at a time) ==")
lamp("Practical_LATE", (1.0, 1.0, 2.0), 400.0, coll)
bpy.context.view_layer.update()
m = SL.measure(sc)
log("interior lamps %d, stamps %d, unstamped %s"
    % (m["n_interior_lamps"], m["n_lamp_stamps"],
       m["unstamped_interior_lamps"]))
verdict(sc, False, "an unstamped interior lamp")
# ...and the OLD rule could not have caught this: it only ever read the mark,
# which is still perfectly correct on this scene.
log("the old rule read only the mark, which is still %r here -- it could not "
    "see this at all" % sc.get(SL.SCENE_MARK))

print("\n== C: a stamped lamp EDITED after levelling ==")
sc, coll = fresh()
SL.apply(sc, verbose=False)
before = float(bpy.data.lights["Practical_B"].energy)
bpy.data.lights["Practical_B"].energy = before * 1.10
m = SL.measure(sc)
log("Practical_B %.3f -> %.3f W; stamps still %d of %d, residual %+.4f W"
    % (before, before * 1.10, m["n_lamp_stamps"], m["n_interior_lamps"],
       m["identity_residual_w"]))
verdict(sc, False, "a stamped lamp whose watts were edited")
log("a COUNT of stamps is %d here and %d in case A -- identical. Only the "
    "identity separates them." % (m["n_lamp_stamps"], 3))

print("\n== D: the 24th lamp, added the correct way (this is R2-1146) ==")
sc, coll = fresh(with_rig=True)
n_before = len([o for o in sc.objects if o.type == "LIGHT"])
man = SL.apply(sc, verbose=False)
strip = man.get("strip", {})
m = SL.measure(sc)
n_after = len([o for o in sc.objects if o.type == "LIGHT"])
log("lamps %d -> %d; strip added=%s at %.4f W, radiance %s"
    % (n_before, n_after, strip.get("added"), strip.get("energy_w", 0.0),
       strip.get("radiance")))
sm = ST.measure(sc)
log("strip in the scene: %s" % sm)
if not strip.get("added"):
    bad.append("D: the strip was NOT added to a scene carrying the four lamps")
if sm.get("sl_base_energy") is None:
    bad.append("D: the strip carries no _sl_base stamp, so it was not levelled")
elif abs(sm["energy_w"] - sm["sl_base_energy"] * m["lift_multiplier"]) > 1e-4:
    bad.append("D: the strip was not lifted with the rest of the rig")
else:
    log("the strip was levelled with the rig: %.4f x %.6f = %.4f W"
        % (sm["sl_base_energy"], m["lift_multiplier"], sm["energy_w"]))
if m["n_interior_lamps"] != 5:
    bad.append("D: expected 5 interior lamps (4 + strip), got %d"
               % m["n_interior_lamps"])
verdict(sc, True, "a rig with one MORE lamp than it was described with")
log("THE POINT: the count moved and the invariant did not care. The old rule "
    "refused exactly this.")

print("\n== E: apply() on a scene that is not the showroom ==")
sc, coll = fresh()
man = SL.apply(sc, verbose=False)
if man["strip"].get("added"):
    bad.append("E: the strip was added to a scene with no three-point rig")
else:
    log("strip not added: %s" % man["strip"]["why"])
if ST.measure(sc).get("present"):
    bad.append("E: the strip is in a scene it should not be in")

print("\n== F: idempotence -- apply twice must equal apply once ==")
sc, coll = fresh(with_rig=True)
SL.apply(sc, verbose=False)
once = SL.measure(sc)["interior_lamp_watts"]
SL.apply(sc, verbose=False)
twice = SL.measure(sc)["interior_lamp_watts"]
# the precise idempotence question is "is there exactly ONE strip", not "how
# many lights are in the scene" -- the scene also carries Forecourt_Post, which
# is deliberately exterior and is not part of this count
n_strip = len([o for o in sc.objects
               if o.type == "LIGHT" and o.name.startswith(ST.NAME)])
log("once %.3f W, twice %.3f W, objects named %s*: %d"
    % (once, twice, ST.NAME, n_strip))
if abs(once - twice) > 1e-6:
    bad.append("F: apply is not idempotent (%.3f vs %.3f)" % (once, twice))
if n_strip != 1:
    bad.append("F: a second apply left %d strip object(s), not 1" % n_strip)
verdict(sc, True, "after two applies")

print()
for b in bad:
    print("   FAIL " + b)
print(">> STAGE RESULT: %s" % ("LEVELLING_INVARIANT_OK" if not bad
                               else "LEVELLING_INVARIANT_FAIL"))
sys.exit(0 if not bad else 1)
