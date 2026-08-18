"""THE NARROW STRIP SOURCE -- the second half of R2-1146, and the first round-2
light that has a path to a frame.

    import showroom_strip
    showroom_strip.ensure(scene)      # after the SET/LIGHTS have been appended,
                                      # BEFORE showroom_lighting.apply()

    python3 world/showroom_strip.py --selftest     # arithmetic + controls

WHAT IT IS FOR
--------------
R2-1146 prescribed TWO things for the carbon bodywork -- *"`Mapping.Scale`
190.0 -> 62.832, and one narrow strip source added to the rig with the four
clipping-tuned lamps untouched."*  R2-2041 landed the constant (twill pitch
1.6535 -> 5.000 mm, 0.87 -> 2.63 px at 526 px/m) and reported the lamp as
BLOCKED.  This is the lamp.

The constant makes the weave BIG ENOUGH to resolve.  It does not make it
VISIBLE, and those are different problems.  A twill reads through the way its
0.0475 mm bump modulates a specular highlight, and the width of that
modulation is set by the ANGULAR SIZE OF THE SOURCE.  The weave's surface slope
is about 2.2 deg (2 x 0.0475 mm over a 2.5 mm half-pitch); a source subtending
much more than that at the bodywork smears the highlight across many weave
cells and the structure averages to flat.

MEASURED off `world/R22041_car_anim_driver_CS.blend`, which is where the
shipped lamps actually come from, every source in the rig is far too broad:

    Key    4.60 x 3.40 m    narrow axis 3.40 m    radiance 22.3
    Fill   5.00 x 3.40 m                3.40 m             13.9
    Rim    4.80 x 0.62 m                0.62 m             32.1
    Kick   3.00 x 0.62 m                0.62 m             24.4
    walls 11.0-11.5 x 0.12 m            0.12 m           8.6-10.2   (at the wall)
    bollards      0.60 m disk           0.60 m             18.2

At the ~3 m the Rim and Kick work from, 0.62 m subtends 11.8 deg -- five times
the slope the weave has to write into.  AND THAT IS NOT AN ACCIDENT: round 1
WIDENED both of them on purpose.  `s05_lighting.py` records the Rim going
3.6 x 0.35 -> 4.8 x 0.62 and the Kick 2.6 x 0.5 -> 3.0 x 0.62, both to pull peak
radiance under the ~60 at which a clearcoat highlight clips.  That was the
right call for the clearcoat and it is exactly what removed the only sources
narrow enough to write a weave.

So the prescription is precise: do not un-widen them -- *add* one narrow source
that plays the role they gave up, at a radiance that still cannot clip.

THE NUMBERS, AND WHY EACH ONE
-----------------------------
    3.60 x 0.10 m      NARROW AXIS 0.10 m = 1.9 deg at 3 m, just under the
                       weave's own 2.2 deg slope, so the highlight rolls
                       across individual cells instead of averaging them.
                       3.60 m long because the car is 5 m long and a specular
                       streak has to run along the bodywork, not dot it.
    50.0 W nominal     divided by the colour's luma exactly as round 1's
                       `area_light` does, so colour changes hue and never
                       level:  50.0 / 0.931576 = 53.6725 W.
    radiance 47.5      = W / (area * pi).  UNDER the ~60 clip bound with 21 %
                       to spare, and 1.48x the Rim's 32.1 -- deliberately the
                       highest-radiance source in the rig, because that is the
                       whole job.  It is +1.4 % on a 3,737 W rig, so it is a
                       specular instrument and not a fill: it must not move the
                       exposure and it does not.
    COLD (.88,.94,1)   the same separation colour the Rim uses -- the rig's
                       other specular-role source.  Carbon is near-black; a
                       cool rake reads as a highlight rather than as more key.
    spread 100 deg     the Key's, for the Key's stated reason: less of it lands
                       on walls that now have their own light.
    (0.60, 6.40, 2.55) +Y side, above the car's waistline, aimed at
    -> (0.15, 0, 0.85) (0.15, 0, 0.85) -- round 1's own `focus` raised 70 mm so
                       the rake biases onto bodywork instead of the dais top.
                       +Y is the side the camera is on through the beat-2 orbit
                       (f599 at (1.66, 6.81, 3.14), f661 at (7.08, 2.61, 2.50)),
                       which are the two frames R2-2041 proved the twill on.

WHERE IT IS ADDED, AND WHY NOT UPSTREAM
---------------------------------------
`build_three_point` in `~/opus5-car-render/build/s05_lighting.py` is
where the four lamps are authored, and EDITING IT HAS NO PATH TO A FRAME: round
2 never runs round 1's lighting stage.  The lamps reach the film as baked
datablocks inside the car blend, appended whole by `tools/build_film_scene.py`.
Writing the strip there would be writing to a file nobody reads -- the film18
shape.

So it is added HERE, downstream of the append, from
`showroom_lighting.apply()`, which is the one round-2 function that owns the
interior rig's final state in the film scene and already runs at exactly the
right moment: after the SET is in, before the levelling, before every save.
The strip is levelled by the same pass and stamped with the same `_sl_base`, so
it is not a special case in any gate.

A NOTE ON THE UPSTREAM THAT WAS SAID TO DISAGREE
------------------------------------------------
R2-2041 recorded that the shipped energies *"are scaled off source by a
non-uniform factor (Key x1.09751, Fill x1.23841, Rim x1.07345, Kick x1.09751)
that appears nowhere in round-1 source."*  THAT IS WITHDRAWN, and the selftest
below is the withdrawal: those four factors are `1 / _luma(colour)`, computed
by round 1's own `area_light`, three lines from the call.  1/luma(WARM) =
1.09751, 1/luma(COOL) = 1.23841, 1/luma(COLD) = 1.07345.  The artefact and the
source agree to the last digit.

What was really wrong is the FILE: the shipped rig is `s05_lighting.py`, not
`s05_lighting_v2.py`.  Fill ships at 743.049 W = 600/luma(COOL) at spread 120,
which is v1's; v2 says 540 W at spread 140 = 668.75 W.  Despite the name, `_v2`
is 27 minutes OLDER and superseded.  The disagreement was with the wrong file.
"""

import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

#: Round 1's separation colour, quoted from `s05_lighting.py`.
COLD = (0.88, 0.94, 1.00)

#: The object/datablock name.  `R2_` marks it as the one lamp in the rig that
#: round 1 did not author, so a reader diffing against `f1_showroom.blend`
#: knows immediately which one is new.
NAME = "R2_Strip"

#: The collection the rest of the rig lives in.
RIG_COLLECTION = "LIGHTS"

SPEC = {
    "size": 3.60,          # m, along the car
    "size_y": 0.10,        # m, THE narrow axis -- the whole point
    "power_w": 50.0,       # nominal, pre-luma, exactly as round 1 quotes power
    "color": COLD,
    "spread_deg": 100.0,
    "location": (0.60, 6.40, 2.55),
    "target": (0.15, 0.00, 0.85),
    "shape": "RECTANGLE",
}

#: Peak radiance at which a clearcoat highlight clips, quoted from
#: `s05_lighting.py`'s Rim comment.  The strip must stay under it.
CLIP_RADIANCE = 60.0

#: The four lamps R2-1146 says to leave alone, with the shape and energy they
#: MUST still have.  Measured off `world/R22041_car_anim_driver_CS.blend`, not
#: quoted from round-1 source -- see R2-517.
UNTOUCHED = {
    "Key":  {"size": 4.60, "size_y": 3.40, "energy": 1097.512},
    "Fill": {"size": 5.00, "size_y": 3.40, "energy": 743.049},
    "Rim":  {"size": 4.80, "size_y": 0.62, "energy": 300.566},
    "Kick": {"size": 3.00, "size_y": 0.62, "energy": 142.677},
}


def luma(c):
    """Round 1's `_luma`, reproduced so this file does not import round 1.

    `~/opus5-car-render` is READ-ONLY round-1 material and importing
    from it at film-build time would make the film depend on a tree nothing
    else in round 2 executes.
    """
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def energy_w(spec=None):
    """Watts on the datablock: nominal power divided by the colour's luma.

    This is round 1's convention (`area_light`), kept so the strip is
    commensurable with the four lamps beside it -- and so the rig's energies
    still all reduce to one rule.
    """
    s = spec or SPEC
    return s["power_w"] / max(luma(s["color"]), 1e-6)


def area_m2(spec=None):
    s = spec or SPEC
    return s["size"] * s["size_y"]


def radiance(spec=None):
    """W / (m^2 sr) for a Lambertian rectangle -- power / (area * pi).

    Checked against the rig in the selftest: this expression reproduces round
    1's own published radiances for the Rim (280 W / 2.976 m2 -> 30) and the
    Kick (130 / 1.86 -> 22), so it is the same quantity their clip bound is in.
    """
    return energy_w(spec) / (area_m2(spec) * math.pi)


# --------------------------------------------------------------------------- #
#  THE BUILD
# --------------------------------------------------------------------------- #

def _aim(ob, target):
    """Round 1's `_aim`: point local -Z at the target."""
    from mathutils import Vector
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def rig_present(scene):
    """Are the four lamps this strip is designed to sit beside actually here?

    Decided by MEASURING them, not by the presence of a collection called
    LIGHTS.  A scene with a `Key` at some other size is not the rig this was
    computed against and must not get the strip silently.
    """
    import bpy
    have, wrong = [], []
    for nm, want in UNTOUCHED.items():
        ob = scene.objects.get(nm)
        if ob is None or ob.type != "LIGHT" or ob.data.type != "AREA":
            continue
        ld = ob.data
        if (abs(ld.size - want["size"]) > 1e-3
                or abs(ld.size_y - want["size_y"]) > 1e-3
                or abs(ld.energy - want["energy"]) > 1e-2):
            wrong.append({"lamp": nm,
                          "want": want,
                          "got": {"size": round(ld.size, 4),
                                  "size_y": round(ld.size_y, 4),
                                  "energy": round(ld.energy, 4)}})
            continue
        have.append(nm)
    return sorted(have), wrong


def narrowest_other(scene):
    """The narrowest axis of every OTHER area source in the scene.

    Returns (name, metres) for the narrowest.  "Narrow strip" is a claim about
    this scene, so it is measured against this scene rather than asserted from
    the module docstring.
    """
    import bpy
    best = None
    for ob in scene.objects:
        if ob.type != "LIGHT" or ob.name == NAME:
            continue
        ld = ob.data
        if ld.type != "AREA":
            continue
        w = min(ld.size, ld.size_y) if ld.shape in ("RECTANGLE", "ELLIPSE") \
            else ld.size
        if best is None or w < best[1]:
            best = (ob.name, w)
    return best


def ensure(scene=None, spec=None, verbose=True):
    """Add the strip if it is not there.  Idempotent, and it never edits a lamp.

    Returns a manifest.  `added` is False both when the strip is already there
    and when this scene is not the showroom -- `why` says which, because a
    silent skip is how the first half of this prescription went missing for
    955 defect entries.
    """
    import bpy
    from mathutils import Vector
    scene = scene or bpy.context.scene
    s = dict(SPEC)
    if spec:
        s.update(spec)

    existing = scene.objects.get(NAME)
    if existing is not None:
        man = {"added": False, "present": True, "name": NAME,
               "why": "already in the scene",
               "energy_w": round(float(existing.data.energy), 6)}
        if verbose:
            print(">> showroom_strip: %s already present at %.4f W"
                  % (NAME, man["energy_w"]))
        return man

    have, wrong = rig_present(scene)
    if len(have) != len(UNTOUCHED):
        man = {"added": False, "present": False, "name": NAME,
               "why": "the three-point rig is not in this scene "
                      "(found %s of %s)" % (have, sorted(UNTOUCHED)),
               "rig_mismatched": wrong}
        if verbose:
            print(">> showroom_strip: NOT ADDED -- %s" % man["why"])
            for w in wrong:
                print("   rig mismatch %s: want %s got %s"
                      % (w["lamp"], w["want"], w["got"]))
        return man

    r = radiance(s)
    if r >= CLIP_RADIANCE:
        raise SystemExit(
            "REFUSING: the strip would sit at radiance %.2f, at or over the "
            "%.1f at which a clearcoat highlight clips. Round 1 widened the "
            "Rim and the Kick specifically to get under that bound and this "
            "lamp exists to be narrow, not to be bright: take watts out, do "
            "not take width out." % (r, CLIP_RADIANCE))

    ld = bpy.data.lights.new(NAME, "AREA")
    ld.shape = s["shape"]
    ld.size = s["size"]
    ld.size_y = s["size_y"]
    ld.energy = energy_w(s)
    ld.color = s["color"]
    ld.spread = math.radians(s["spread_deg"])
    ld.use_shadow = True
    ob = bpy.data.objects.new(NAME, ld)

    coll = bpy.data.collections.get(RIG_COLLECTION)
    if coll is not None and coll.name in {c.name for c
                                          in scene.collection.children_recursive}:
        coll.objects.link(ob)
        where = coll.name
    else:
        scene.collection.objects.link(ob)
        where = scene.collection.name
    ob.location = Vector(s["location"])
    _aim(ob, s["target"])
    # The four it joins are all `visible=False`: the fixture a viewer is meant
    # to see is the emissive line, not the lamp doing the work.  A 3.6 m white
    # rectangle hanging at y = 6.4 would be in shot through the beat-2 orbit.
    ob.visible_camera = False

    narrow = narrowest_other(scene)
    if narrow is not None and s["size_y"] >= narrow[1]:
        raise SystemExit(
            "REFUSING: the strip's narrow axis is %.3f m and %s is already "
            "%.3f m. This lamp's ONLY justification is being the narrowest "
            "source in the rig; if it is not, it is just more light."
            % (s["size_y"], narrow[0], narrow[1]))

    man = {"added": True, "present": True, "name": NAME,
           "collection": where,
           "size": s["size"], "size_y": s["size_y"],
           "area_m2": round(area_m2(s), 6),
           "power_nominal_w": s["power_w"],
           "energy_w": round(energy_w(s), 6),
           "radiance": round(r, 4),
           "clip_bound": CLIP_RADIANCE,
           "spread_deg": s["spread_deg"],
           "location": list(s["location"]),
           "target": list(s["target"]),
           "color": list(s["color"]),
           "untouched_verified": have,
           "narrowest_other_source": (None if narrow is None
                                      else {"lamp": narrow[0],
                                            "narrow_axis_m": round(narrow[1], 4)})}
    if verbose:
        print(">> showroom_strip: ADDED %s  %.2f x %.2f m (%.4f m2), "
              "%.4f W, radiance %.2f (bound %.1f), spread %.0f deg, in %r"
              % (NAME, s["size"], s["size_y"], area_m2(s), energy_w(s), r,
                 CLIP_RADIANCE, s["spread_deg"], where))
        print("   the four clipping-tuned lamps verified untouched: %s"
              % ", ".join(have))
        if narrow:
            print("   narrowest other source in the rig: %s at %.3f m, "
                  "against this strip's %.3f m"
                  % (narrow[0], narrow[1], s["size_y"]))
    return man


def measure(scene=None):
    """What the scene carries, for a gate to read.  Never writes."""
    import bpy
    scene = scene or bpy.context.scene
    ob = scene.objects.get(NAME)
    if ob is None or ob.type != "LIGHT":
        return {"present": False}
    ld = ob.data
    a = ld.size * ld.size_y
    base = (float(ld["_sl_baseenergy"]) if "_sl_baseenergy" in ld.keys()
            else None)
    # TWO RADIANCES, LABELLED, BECAUSE ONE OF THEM IS THE WRONG ONE TO COMPARE.
    # `CLIP_RADIANCE` is round 1's ~60, and round 1 authored at view exposure
    # 0.000.  After `showroom_lighting.apply` every practical carries
    # base x 2**3.628, so the levelled radiance is 12.36x the number the bound
    # is in and reads 587 against a bound of 60.  Reporting only that would be
    # an instrument that screams on a correct rig.  The comparable quantity is
    # the AUTHORED one, recomputed from the lamp's own `_sl_base` stamp.
    return {"present": True,
            "size": round(ld.size, 4), "size_y": round(ld.size_y, 4),
            "area_m2": round(a, 6),
            "energy_w": round(float(ld.energy), 6),
            "radiance_levelled": round(float(ld.energy) / (a * math.pi), 4),
            "radiance_authored": (None if base is None
                                  else round(base / (a * math.pi), 4)),
            "clip_bound_authored": CLIP_RADIANCE,
            "spread_deg": round(math.degrees(ld.spread), 3),
            "visible_camera": bool(ob.visible_camera),
            "location": [round(v, 4) for v in ob.location],
            "sl_base_energy": (float(ld["_sl_baseenergy"])
                               if "_sl_baseenergy" in ld.keys() else None)}


# --------------------------------------------------------------------------- #
#  SELFTEST  --  arithmetic and controls, without Blender
# --------------------------------------------------------------------------- #

def selftest():
    bad = []
    print("R2-2101  showroom_strip selftest")

    # 1. THE RADIANCE EXPRESSION IS THE ONE ROUND 1'S CLIP BOUND IS IN.
    #    Reproduce two published figures from `s05_lighting.py` with it. If it
    #    cannot, comparing the strip to "~60" is comparing two different
    #    quantities and the whole safety argument is void.
    print("\n   the radiance expression, against round 1's OWN published numbers")
    # THE THIRD ROW HAS A LOOSER TOLERANCE AND THAT IS A FINDING, NOT A FUDGE.
    # `s05_lighting.py` publishes the Rim at 68.6 before widening and 30 after,
    # on areas of 1.26 and 2.976 m2.  Radiance from an area lamp goes exactly as
    # 1/area at fixed power, so those two figures imply a ratio of 2.362 and
    # they actually stand in a ratio of 2.287 -- ROUND 1'S OWN TWO NUMBERS
    # DISAGREE BY 3.1 %.  Both cannot come from this expression.  The two LIVE
    # figures are what the ~60 clip bound was calibrated against and they are
    # held to 0.6; the retired pre-widening figure is held to 5 %, which is the
    # tightest tolerance its own source supports.  A missing pi would be 3.14x
    # out, so 5 % still discriminates.
    for nm, w, a, want, tol in (
            ("Rim  4.8 x 0.62  (live)", 280.0, 4.8 * 0.62, 30.0, 0.6),
            ("Kick 3.0 x 0.62  (live)", 130.0, 3.0 * 0.62, 22.0, 0.6),
            ("Rim  3.6 x 0.35  (retired)", 280.0, 3.6 * 0.35, 68.6, 3.43)):
        got = w / (a * math.pi)
        ok = abs(got - want) <= tol
        print("      %-30s %6.2f   round 1 says %5.1f  +/- %-4.2f  %s"
              % (nm, got, want, tol, "OK" if ok else "MISMATCH"))
        if not ok:
            bad.append("the radiance expression does not reproduce %s" % nm)
    print("      NOTE round 1's own 68.6 and 30.0 imply an area ratio of "
          "%.3f; the areas are in ratio %.3f -- its two figures are "
          "mutually inconsistent by %.1f %%"
          % (68.6 / 30.0, 2.976 / 1.26,
             100.0 * abs((68.6 / 30.0) / (2.976 / 1.26) - 1.0)))

    # 2. 1/luma REPRODUCES THE FOUR "UNEXPLAINED" FACTORS.  This is the
    #    withdrawal of R2-2041's "appears nowhere in round-1 source".
    print("\n   R2-2041's four 'unexplained' factors are 1/_luma(colour)")
    WARM, COOL = (1.00, 0.90, 0.76), (0.70, 0.82, 1.00)
    for nm, col, want in (("Key  WARM", WARM, 1.09751), ("Fill COOL", COOL, 1.23841),
                          ("Rim  COLD", COLD, 1.07345), ("Kick WARM", WARM, 1.09751)):
        got = 1.0 / luma(col)
        ok = abs(got - want) < 1e-5
        print("      %-10s 1/luma = %.5f   R2-2041 measured %.5f  %s"
              % (nm, got, want, "OK" if ok else "MISMATCH"))
        if not ok:
            bad.append("1/luma does not reproduce the %s factor" % nm)

    # 3. and it reproduces the SHIPPED energies from round-1 source power.
    print("\n   round-1 nominal power / luma == the energy in the shipped blend")
    for nm, p, col, shipped in (("Key", 1000.0, WARM, 1097.512),
                                ("Fill", 600.0, COOL, 743.049),
                                ("Rim", 280.0, COLD, 300.566),
                                ("Kick", 130.0, WARM, 142.677)):
        got = p / luma(col)
        ok = abs(got - shipped) < 5e-3
        print("      %-5s %7.1f W / luma = %10.4f   blend has %10.4f  %s"
              % (nm, p, got, shipped, "OK" if ok else "MISMATCH"))
        if not ok:
            bad.append("%s does not reduce to power/luma" % nm)
    # the v2 control: Fill from s05_lighting_v2.py must NOT match the artefact,
    # which is what identifies WHICH source file ships.
    v2 = 540.0 / luma(COOL)
    print("      Fill from s05_lighting_v2.py: %.4f W -- blend has %.4f, so "
          "%s ships" % (v2, 743.049,
                        "v1 s05_lighting.py" if abs(v2 - 743.049) > 1.0
                        else "v2"))
    if abs(v2 - 743.049) < 1.0:
        bad.append("the v2 control matches the artefact, so this test cannot "
                   "tell the two source files apart")

    # 4. THE STRIP ITSELF
    print("\n   the strip")
    e, a, r = energy_w(), area_m2(), radiance()
    print("      %.2f x %.2f m = %.4f m2" % (SPEC["size"], SPEC["size_y"], a))
    print("      %.1f W nominal / luma(COLD) %.6f = %.4f W"
          % (SPEC["power_w"], luma(COLD), e))
    print("      radiance %.4f   bound %.1f   margin %.1f %%"
          % (r, CLIP_RADIANCE, 100.0 * (1 - r / CLIP_RADIANCE)))
    if r >= CLIP_RADIANCE:
        bad.append("the strip clips: radiance %.2f >= %.1f" % (r, CLIP_RADIANCE))

    # it must be the NARROWEST and the HIGHEST-RADIANCE thing in the rig
    rig = [("Key", 4.6, 3.4, 1097.512), ("Fill", 5.0, 3.4, 743.049),
           ("Rim", 4.8, 0.62, 300.566), ("Kick", 3.0, 0.62, 142.677),
           ("WallWash_BackUp", 11.5, 0.12, 42.106),
           ("WallWash_SideUp", 11.0, 0.12, 42.106),
           ("WallWash_BackDn", 11.5, 0.12, 37.152),
           ("WallWash_SideDn", 11.0, 0.12, 37.152),
           ("FloorGraze", 14.0, 0.3, 21.796),
           ("Bollard_Lamp_0", 0.6, 0.6, 20.564)]
    nb = min(rig, key=lambda t: min(t[1], t[2]))
    hb = max(rig, key=lambda t: t[3] / (t[1] * t[2] * math.pi))
    hbr = hb[3] / (hb[1] * hb[2] * math.pi)
    print("      narrowest shipped source  %-16s %.3f m  (strip %.3f m)"
          % (nb[0], min(nb[1], nb[2]), SPEC["size_y"]))
    print("      highest-radiance shipped  %-16s %.2f     (strip %.2f, %.2fx)"
          % (hb[0], hbr, r, r / hbr))
    if SPEC["size_y"] >= min(nb[1], nb[2]):
        bad.append("the strip is not the narrowest source in the rig")
    if r <= hbr:
        bad.append("the strip is not the highest-radiance source, so it cannot "
                   "do the job the widened Rim gave up")

    # 5. POSITIVE CONTROL: doing what the naive fix would do -- un-widen the Rim
    #    back to 3.6 x 0.35 -- must be REJECTED by the same bound.
    naive = 280.0 / (3.6 * 0.35 * math.pi)
    ok = naive >= CLIP_RADIANCE
    print("\n      POSITIVE CONTROL: un-widening the Rim to 3.6 x 0.35 puts it "
          "at %.1f (%.1f on the shipped 300.566 W datablock) -> %s"
          % (naive, 300.566 / (3.6 * 0.35 * math.pi),
             "REJECTED, as it must be" if ok
             else "ACCEPTED -- THIS BOUND IS WORTHLESS"))
    if not ok:
        bad.append("the clip bound accepts the change round 1 measured as "
                   "clipping, so it is not discriminating")

    # 6. the strip must land inside the shell showroom_lighting calls interior,
    #    or it is levelled by nothing and renders 3.628 stops under the rig.
    try:
        import showroom_lighting as SL
        x, y, z = SPEC["location"]
        inside = (SL.SHELL["x"][0] <= x <= SL.SHELL["x"][1]
                  and SL.SHELL["y"][0] <= y <= SL.SHELL["y"][1]
                  and SL.SHELL["z"][0] <= z <= SL.SHELL["z"][1])
        print("      inside showroom_lighting.SHELL (so it gets levelled): %s"
              % inside)
        if not inside:
            bad.append("the strip is outside SHELL and would not be levelled")
        lift = 2.0 ** SL.LIFT_STOPS
        print("      levelled: %.4f W x %.6f = %.4f W added to the interior load"
              % (e, lift, e * lift))
        print("      PREDICTION for the built film: interior_lamp_watts "
              "%.3f -> %.3f, n_lamp_stamps 23 -> 24"
              % (46203.313, 46203.313 + e * lift))
    except Exception as exc:                                     # noqa: BLE001
        bad.append("could not cross-check against showroom_lighting: %r" % exc)

    print()
    for b in bad:
        print("   FAIL " + b)
    print(">> STAGE RESULT: %s" % ("SHOWROOM_STRIP_OK" if not bad
                                   else "SHOWROOM_STRIP_FAIL"))
    return 0 if not bad else 1


def _main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    if "--selftest" in argv or not argv:
        return selftest()
    import bpy
    import json
    scene = bpy.context.scene
    man = ensure(scene)
    man["measured"] = measure(scene)
    if "--out" in argv:
        out = os.path.abspath(argv[argv.index("--out") + 1])
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
        print(">> saved %s" % out)
    print(json.dumps(man, indent=1))
    print(">> STAGE RESULT: SHOWROOM_STRIP_APPLIED")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
