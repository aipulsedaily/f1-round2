"""THE SHOWROOM'S PRACTICALS, LEVELLED TO THE FILM'S EXPOSURE.

    import showroom_lighting                  # world/ is already on sys.path
    showroom_lighting.apply(scene)            # after the SET has been appended

    python3 world/showroom_lighting.py --selftest       # arithmetic + controls
    blender -b <film scene> --factory-startup \
        -P world/showroom_lighting.py -- --dry-run      # the manifest, no edit
    blender -b <film scene> --factory-startup \
        -P world/showroom_lighting.py -- --out <blend>  # apply and save


WHY THIS FILE EXISTS
--------------------
The showroom's light rig is round 1's — `/home/zany/opus5-car-render/build/
s05_lighting_v2.py`, baked into `f1_showroom.blend` and carried forward through
`beat1_anim.blend` -> `car_anim.blend` -> the film scene, where
`tools/build_film_scene.py` appends its `LIGHTS` collection whole.

**IT WAS AUTHORED AGAINST A VIEW EXPOSURE OF 0.000.**  s05_lighting_v2's own
docstring quotes its transfer curve "for this project's exact view transform
(AgX + Medium High Contrast, exposure 0)" and every wattage in it was picked off
that curve.  The film does not grade at 0.000.  It grades at
`film_exposure.FILM_EXPOSURE` = -3.628, because beats 3-6 are outdoors and -3.628
is what an 18 % card MEASURES at under `build_sky`'s light.

So the room is rendered 3.628 stops below the level it was lit for, and the
bottom of it falls off the end of the encoding.  MEASURED in the joined film
scene, beat 1 frame 400: 5 % of the frame at 0/0/0.  Not dark -- *no detail
recorded at all*, and one grade for 2,978 cut-free frames means there is no
second pass in which to get it back.

THE FIX IS THE ROOM, NOT THE CAMERA.  A grade cannot do it (one take, one
grade, and the camera drives straight through the glass with no cut to hide a
change behind) and a camera ramp only moves the problem: an iris that opens for
the interior has to close again across the breach, on screen, in shot.  The
practicals are simply set to the level the room needs at the exposure the film
is actually graded at.

WHAT "THE LEVEL THE ROOM NEEDS" IS, EXACTLY
-------------------------------------------
    LIFT_STOPS = -FILM_EXPOSURE = +3.628

and that is not a taste number, it is an identity.  Multiplying every practical
by 2**3.628 and viewing at -3.628 reproduces, pixel for pixel, what the same
practicals produced at 0.000 -- which is the look s05_lighting_v2 was tuned
against, clip thresholds and all.  The scheme's whole argument ("clipping starts
at scene radiance ~5.6", "widening a source divides the specular peak") is
preserved unchanged, because both sides of every one of those comparisons move
together.

The one term that does NOT move is the daylight coming through the glass, and
that is the point: it is already correct at -3.628 and it is left alone.  After
this, interior surfaces read at their authored level and the world outside the
window reads at the daylight level, in the same frame, with no ramp between
them.

WHAT IS TOUCHED AND WHAT IS NOT
-------------------------------
Touched: every lamp and every emissive material that belongs to the SHOWROOM
INTERIOR, decided by geometry rather than by a hand-written list, so a prop
another agent adds to the room next week is included and one they add to the
forecourt is not.  A thing is interior when its bounding-box centre lies inside
the round-1 pavilion shell that `build_architecture` measured
(`R1_SHELL` = x -15.25..15.00, y -11.25..11.25, plus the wall height).

NOT touched, each for a stated reason:

  * `SKY_*` lamps and the world.  That is `build_sky`, it is the exterior, and
    FILM_EXPOSURE was measured under it.  Moving it moves beats 3-6.
  * anything in the `CAR` collection or parented to `CAR_ROOT`.  The car starts
    inside the shell and ends up at 330 km/h in daylight; a material scaled
    while it is indoors is 12x too bright the moment it is outdoors.
  * any emissive material with even ONE user outside the shell.  Materials are
    shared datablocks: `PropPoleEmit` lights the forecourt lamp posts as well,
    and scaling it would put 12x on an exterior practical.  Mixed materials are
    reported, never silently half-applied.
  * lamps and emission sockets that are node-LINKED.  There is no scalar to
    scale; a driven value is somebody else's control loop.

IDEMPOTENT, AND RE-TARGETABLE
-----------------------------
The first apply records each value it touches as `_sl_base` on the datablock and
thereafter always writes `base * 2**stops`.  Running it twice does not give
24.7x, and running it again with a different `stops` re-aims from the original
rather than compounding.  `revert()` puts every base back and removes the marks.
"""

import json
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import film_exposure as FX                                        # noqa: E402

# --------------------------------------------------------------------------- #
#  THE ONE EXPRESSION
# --------------------------------------------------------------------------- #

#: How far the practicals are lifted, in stops.  An identity, not a taste
#: number: the rig was authored at view exposure 0.000 and the film grades at
#: FILM_EXPOSURE, so lifting by exactly that difference reproduces the authored
#: image at the film's grade.  See the module docstring.
LIFT_STOPS = round(-FX.FILM_EXPOSURE, 3)                          # +3.628

#: Linear multiplier applied to every lamp watt and every emission strength.
LIFT = 2.0 ** LIFT_STOPS                                          # 12.363

#: The round-1 pavilion shell, MEASURED, quoted by `build_architecture.R1_SHELL`
#: from `/home/zany/opus5-car-render/f1_showroom.blend`.  x, y from the walls;
#: z from the floor soffit (-0.060) and the wall head (6.200), with 0.30 m of
#: slack at each end so a cove fixture pushed into the ceiling void or a floor
#: emitter recessed into the slab is still counted as being in the room.
SHELL = {"x": (-15.55, 15.30), "y": (-11.55, 11.55), "z": (-0.40, 6.50)}

#: Collections whose contents are never interior practicals no matter where
#: they sit.  `CAR` leaves the room; `WORLD_SKY` is the exterior light itself.
EXCLUDED_COLLECTIONS = ("CAR", "WORLD_SKY")

#: Object-name prefixes that are exterior by construction.
EXCLUDED_PREFIXES = ("SKY_", "CARPROXY")

#: The datablock key that makes this idempotent.
MARK = "_sl_base"
SCENE_MARK = "showroom_lighting_stops"


# --------------------------------------------------------------------------- #
#  CLASSIFICATION  --  geometry, not a hand list
# --------------------------------------------------------------------------- #

def _bbox(ob):
    """World-space corners of the object's bounding box, or its origin.

    An empty (a lamp, a hub) has a degenerate bound_box, so it falls back to
    the object's own world position — which is the right answer for a lamp.
    """
    from mathutils import Vector
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    if not pts or all(p == pts[0] for p in pts):
        return [ob.matrix_world.translation]
    return pts


def _in_shell(p):
    return (SHELL["x"][0] <= p.x <= SHELL["x"][1] and
            SHELL["y"][0] <= p.y <= SHELL["y"][1] and
            SHELL["z"][0] <= p.z <= SHELL["z"][1])


def _wholly_in_shell(ob):
    """EVERY corner inside, not just the centre.

    The centre alone is not a test.  `WORLD_TERRAIN` spans about +/-1000 m and
    is centred on the world origin, which is the middle of the showroom floor:
    a centre test calls the entire landscape an interior practical.  Requiring
    the whole bounding box keeps `Floor` (x -15..15, y -11..11) and the glass
    at x = 15.000 inside while rejecting anything that reaches past the walls.
    """
    return all(_in_shell(p) for p in _bbox(ob))


def _excluded(ob):
    """Why this object can never be an interior practical, or None."""
    for pre in EXCLUDED_PREFIXES:
        if ob.name.startswith(pre):
            return "name starts %r" % pre
    names = set(c.name for c in ob.users_collection)
    hit = names & set(EXCLUDED_COLLECTIONS)
    if hit:
        return "in collection %s" % sorted(hit)[0]
    a = ob
    seen = 0
    while a.parent is not None and seen < 64:
        a = a.parent
        seen += 1
        if a.name.startswith("CAR_ROOT") or a.name.startswith("CARRIG_"):
            return "parented under %s" % a.name
        for pre in EXCLUDED_PREFIXES:
            if a.name.startswith(pre):
                return "parented under %s" % a.name
    return None


def _emission_sockets(mat):
    """Every settable emission strength socket in a material, with its colour.

    Returns [(node, strength_socket, colour_or_None)].  A socket whose Strength
    is node-LINKED is skipped: there is no scalar there to scale, and driving it
    is somebody else's control loop.
    """
    # `Material.use_nodes` is deprecated in Blender 5.2 and goes away in 6.0;
    # a material either has a node tree or it does not, and that is the test.
    out = []
    if mat is None or mat.node_tree is None:
        return out
    for n in mat.node_tree.nodes:
        if n.type == "EMISSION":
            s = n.inputs.get("Strength")
        elif n.type == "BSDF_PRINCIPLED":
            s = n.inputs.get("Emission Strength")
        else:
            continue
        if s is None or s.is_linked:
            continue
        if float(s.default_value) <= 0.0:
            continue
        out.append((n, s))
    return out


def classify(scene=None):
    """Decide, from the scene as it stands, what is an interior practical.

    Everything here is MEASURED off the evaluated scene.  Nothing is assumed
    from a name except the two exclusion prefixes, which are named in the
    module docstring with a reason each.
    """
    import bpy
    scene = scene or bpy.context.scene
    bpy.context.view_layer.update()

    objs = list(scene.objects)
    interior, exterior = {}, {}
    for ob in objs:
        why = _excluded(ob)
        if why is not None:
            exterior[ob.name] = why
            continue
        if _wholly_in_shell(ob):
            interior[ob.name] = True
        else:
            exterior[ob.name] = "reaches outside the shell"

    lamps, lamps_skipped = [], []
    for ob in objs:
        if ob.type != "LIGHT":
            continue
        if ob.name not in interior:
            lamps_skipped.append({"obj": ob.name,
                                  "why": exterior.get(ob.name, "not interior")})
            continue
        if ob.data.animation_data is not None:
            lamps_skipped.append({"obj": ob.name,
                                  "why": "the lamp's energy is animated; a "
                                         "scale would fight the curve"})
            continue
        lamps.append({"obj": ob.name, "light": ob.data.name,
                      "type": ob.data.type,
                      "energy": float(ob.data.energy)})

    # materials: only when EVERY user of the material is interior
    users = {}
    for ob in objs:
        if ob.type != "MESH":
            continue
        for sl in ob.material_slots:
            if sl.material is not None:
                users.setdefault(sl.material.name, []).append(ob.name)

    mats, mats_skipped = [], []
    for name, us in sorted(users.items()):
        mat = bpy.data.materials.get(name)
        socks = _emission_sockets(mat)
        if not socks:
            continue
        outside = [u for u in us if u not in interior]
        if outside:
            # Say WHICH rule rejected them. "outside the shell" is not the same
            # statement as "it is bolted to the car", and a manifest that
            # conflates the two is a misleading instrument.
            reasons = sorted(set(exterior.get(u, "not interior")
                                 for u in outside))
            mats_skipped.append({"mat": name, "n_users": len(us),
                                 "why": "%d of %d user(s) are not interior: %s"
                                        % (len(outside), len(us),
                                           "; ".join(reasons[:3])),
                                 "example": outside[:4]})
            continue
        mats.append({"mat": name, "n_users": len(us),
                     "users": sorted(us)[:6],
                     "sockets": [{"node": n.name,
                                  "strength": float(s.default_value)}
                                 for n, s in socks]})

    # a material can be emissive and used by nothing in the scene; say so
    orphan = [m.name for m in bpy.data.materials
              if m.name not in users and _emission_sockets(m)]

    return {"lamps": lamps, "lamps_skipped": lamps_skipped,
            "materials": mats, "materials_skipped": mats_skipped,
            "emissive_materials_with_no_user_in_scene": sorted(orphan),
            "n_interior_objects": len(interior),
            "n_objects": len(objs)}


# --------------------------------------------------------------------------- #
#  APPLY
# --------------------------------------------------------------------------- #

def _base(db, key, live):
    """The value before this module ever touched it."""
    if MARK + key not in db.keys():
        db[MARK + key] = float(live)
    return float(db[MARK + key])


def apply(scene=None, stops=None, verbose=True):
    """Set every interior practical to `base * 2**stops`.  Idempotent.

    Returns the manifest: what moved, from what to what, and what did not.
    """
    import bpy
    scene = scene or bpy.context.scene
    stops = LIFT_STOPS if stops is None else float(stops)
    k = 2.0 ** stops

    # ---- THE ONE PRACTICAL ROUND 2 AUTHORS -------------------------------- #
    # R2-2101.  The second half of R2-1146's prescription is a narrow strip
    # source, and it is added HERE rather than in round 1's `build_three_point`
    # because round 2 never runs round 1's lighting stage: the lamps arrive as
    # baked datablocks inside the car blend.  Editing the upstream author has no
    # path to a frame -- the film18 shape.
    #
    # It goes BEFORE `classify()` so the strip is picked up by the same
    # geometric test, stamped with the same `_sl_base` and levelled by the same
    # multiplier as the 23 it joins.  A lamp added after this call would render
    # 3.628 stops under the rig it is supposed to be part of.
    #
    # `ensure` is idempotent, it never edits an existing lamp, and it does
    # nothing at all unless the four lamps it is designed to sit beside are
    # measurably present -- so calling `apply` on a probe scene with no showroom
    # in it still adds nothing.  See world/showroom_strip.py.
    import showroom_strip as ST
    strip = ST.ensure(scene, verbose=verbose)

    plan = classify(scene)
    moved_lamps, moved_mats = [], []

    for row in plan["lamps"]:
        ld = bpy.data.lights[row["light"]]
        b = _base(ld, "energy", ld.energy)
        before = float(ld.energy)
        ld.energy = b * k
        moved_lamps.append({"obj": row["obj"], "type": row["type"],
                            "base": round(b, 4), "before": round(before, 4),
                            "after": round(float(ld.energy), 4)})

    for row in plan["materials"]:
        mat = bpy.data.materials[row["mat"]]
        for n, s in _emission_sockets(mat):
            key = "emit:%s" % n.name
            b = _base(mat, key, s.default_value)
            before = float(s.default_value)
            s.default_value = b * k
            moved_mats.append({"mat": mat.name, "node": n.name,
                               "n_users": row["n_users"],
                               "base": round(b, 5), "before": round(before, 5),
                               "after": round(float(s.default_value), 5)})

    scene[SCENE_MARK] = stops
    man = {"stops": stops, "multiplier": round(k, 6),
           "film_exposure": FX.FILM_EXPOSURE,
           "strip": strip,
           "lamps_scaled": moved_lamps, "materials_scaled": moved_mats,
           "lamps_left_alone": plan["lamps_skipped"],
           "materials_left_alone": plan["materials_skipped"],
           "emissive_materials_with_no_user_in_scene":
               plan["emissive_materials_with_no_user_in_scene"],
           "n_interior_objects": plan["n_interior_objects"],
           "n_objects": plan["n_objects"],
           "total_lamp_watts_before":
               round(sum(r["base"] for r in moved_lamps), 2),
           "total_lamp_watts_after":
               round(sum(r["after"] for r in moved_lamps), 2)}
    if verbose:
        print(">> showroom_lighting: %+.3f stops (x%.4f) on %d lamp(s) and %d "
              "emission socket(s) over %d material(s)"
              % (stops, k, len(moved_lamps), len(moved_mats),
                 len(set(r["mat"] for r in moved_mats))))
        print("   interior lamp load %.0f W -> %.0f W"
              % (man["total_lamp_watts_before"], man["total_lamp_watts_after"]))
        for r in man["lamps_left_alone"]:
            print("   LEFT ALONE lamp %-22s %s" % (r["obj"], r["why"]))
        for r in man["materials_left_alone"]:
            print("   LEFT ALONE mat  %-22s %s %s"
                  % (r["mat"], r["why"], r["example"]))
    return man


def revert(scene=None, verbose=True):
    """Put every touched value back to its recorded base and drop the marks."""
    import bpy
    scene = scene or bpy.context.scene
    n = 0
    for ld in bpy.data.lights:
        if MARK + "energy" in ld.keys():
            ld.energy = float(ld[MARK + "energy"])
            del ld[MARK + "energy"]
            n += 1
    for mat in bpy.data.materials:
        for key in [k for k in list(mat.keys()) if k.startswith(MARK + "emit:")]:
            node = key[len(MARK + "emit:"):]
            for nd, s in _emission_sockets(mat):
                if nd.name == node:
                    s.default_value = float(mat[key])
                    n += 1
            del mat[key]
    if SCENE_MARK in scene.keys():
        del scene[SCENE_MARK]
    if verbose:
        print(">> showroom_lighting: reverted %d value(s)" % n)
    return n


def assert_levelled(scene=None, stops=None):
    """RAISE unless this scene's practicals are at the film's level.

    For a scene build to call after appending the set, so "the showroom was
    never levelled" is a refusal at build time and not a 2.5 %-black frame
    discovered in a 2,978-frame render.  Checks the mark AND the watts, because
    a mark can be copied and a watt cannot.

    WHAT THIS PROTECTS, AND WHAT IT DELIBERATELY DOES NOT.  R2-2101.
    ---------------------------------------------------------------
    Until now the rig was described everywhere -- `docs/NEXT-REBUILD.md`, three
    verify scripts, `tools/build_film_scene.py:481` -- by two numbers:

        46,203.313 W interior      23 _sl_base stamps

    and `build_film_scene.py:481` turned the second one into a refusal in so
    many words: *"the interior load is 46,203.313 W over 23 lamps ... a 24th
    lamp breaks it."*  **THE COUNT WAS NEVER THE INVARIANT.**  23 was a
    description of the rig round 1 happened to build, and an assertion that
    encodes an incidental number refuses every future correct change -- which
    it then did, to R2-1146's strip source, for 955 defect entries.

    The two things that are actually true of a levelled rig, and stay true
    whatever anybody adds to it, are:

      1. EVERY interior lamp carries a `_sl_base` stamp.  An unstamped interior
         lamp is one this module has never touched, so it is sitting 3.628 stops
         under the rest of the room -- exactly `film9`'s defect, one lamp at a
         time instead of all of them.
      2. THE IDENTITY CLOSES.  sum(base) x 2**stops == the watts actually on the
         datablocks.  A stamp can be copied; this cannot: it re-derives the
         levelled load from the recorded pre-levelling values and the scene's
         own mark, so a lamp that was stamped and then edited fails here.

    Neither mentions a count, a total, or a lamp by name, and both would have
    caught `film9` (no stamps at all, identity 0 != 46,203).  The literal
    46,203.313 W and the stamp COUNT stay in the film's verification script,
    where they belong: they are facts about one delivered artefact, checked
    against a figure a human predicted in advance, and that is a different job
    from an invariant that gates every save in the pipeline.
    """
    scene = scene or _bpy_scene(scene)
    want = LIFT_STOPS if stops is None else float(stops)
    m = measure(scene)
    if m["scene_mark"] is None:
        raise SystemExit(
            "REFUSING: the showroom practicals have not been levelled. They "
            "were authored at view exposure 0.000 and this film grades at "
            "%+.3f, so beat 1 would render %.3f stops under the level the set "
            "was lit for. Call world/showroom_lighting.apply(scene) after the "
            "SET is appended." % (FX.FILM_EXPOSURE, -FX.FILM_EXPOSURE))
    if abs(float(m["scene_mark"]) - want) > 1e-3:
        raise SystemExit(
            "REFUSING: the showroom practicals are levelled to %+.3f stops, "
            "not the %+.3f this film needs."
            % (float(m["scene_mark"]), want))
    if m["n_interior_lamps"] == 0:
        raise SystemExit(
            "REFUSING: the scene is marked as levelled and carries NO interior "
            "lamps. The mark is on a scene with no showroom in it.")
    # 1. every interior lamp has been through this module
    if m["n_unstamped_interior_lamps"]:
        raise SystemExit(
            "REFUSING: %d of %d interior lamp(s) carry no %r stamp, so this "
            "module has never touched them and they are sitting %+.3f stops "
            "under the rest of the room: %s. That is film9's defect one lamp "
            "at a time. Call showroom_lighting.apply(scene) AFTER every lamp "
            "is in the scene."
            % (m["n_unstamped_interior_lamps"], m["n_interior_lamps"],
               MARK + "energy", FX.FILM_EXPOSURE,
               ", ".join(m["unstamped_interior_lamps"][:6])))
    # 2. the identity closes, re-derived from the scene's own recorded bases
    if m["identity_residual_w"] is None:
        raise SystemExit(
            "REFUSING: the levelling identity could not be recomputed from "
            "this scene's own stamps.")
    # THE TOLERANCE IS RELATIVE, AND THAT IS NOT A LOOSENING.  `Light.energy`
    # is a float32; the base is recorded from one and the levelled value is
    # computed in double and stored back into one, so each lamp carries up to
    # 1.19e-7 of relative rounding and the sum of 24 of them is bounded by
    # 1.19e-7 x total ~ 0.006 W at this rig's 46,867 W.  A fixed 1e-3 W bound
    # PASSED the 5-lamp selftest at 4,698 W (residual 1.2e-4) and would have
    # REFUSED the real film for arithmetic that is exactly right -- caught in
    # the selftest before it reached a 10 GB build.  1 ppm is ~8x the float32
    # bound and still 6,600x tighter than the edited-lamp control, which sits
    # at 6.6e-2 relative.
    tol = max(1e-3, 1e-6 * abs(m["identity_base_x_lift"]))
    if abs(m["identity_residual_w"]) > tol:
        raise SystemExit(
            "REFUSING: the levelling identity does not close. %d stamp(s) "
            "record %.3f W before levelling; x 2**%.3f that is %.3f W, and the "
            "lamps actually carry %.3f W -- a residual of %+.4f W. A stamp can "
            "be copied and this cannot: some lamp was stamped and then edited. "
            "Tolerance was %.6f W (1 ppm, ~8x the float32 rounding of %d lamp "
            "energies)."
            % (m["n_lamp_stamps"], m["base_watts_from_stamps"], want,
               m["identity_base_x_lift"], m["stamped_watts_now"],
               m["identity_residual_w"], tol, m["n_lamp_stamps"]))
    return m


def _bpy_scene(scene):
    import bpy
    return scene or bpy.context.scene


def measure(scene=None):
    """What the scene currently carries, for a gate to compare against.

    R2-2101 added the stamp terms.  They are what `assert_levelled` now judges
    on, so they have to come from the same reading of the same scene rather
    than from a second walk somebody else writes -- `work/r2100/
    measure_film_extra.py` had already had to compute them itself, over
    `bpy.data.lights` rather than over the INTERIOR lamps, which counts a
    stamped exterior lamp and misses an unstamped interior one.
    """
    import bpy
    scene = scene or bpy.context.scene
    plan = classify(scene)
    key = MARK + "energy"

    # distinct light DATABLOCKS, not objects: two objects can share one lamp
    # and the stamp lives on the datablock, so counting objects would demand
    # two stamps where one is correct.
    seen, stamped, unstamped = {}, {}, []
    for r in plan["lamps"]:
        ld = bpy.data.lights.get(r["light"])
        if ld is None or ld.name in seen:
            continue
        seen[ld.name] = r["obj"]
        if key in ld.keys():
            stamped[ld.name] = (float(ld[key]), float(ld.energy))
        else:
            unstamped.append(r["obj"])

    mark = scene.get(SCENE_MARK)
    lift = None if mark is None else 2.0 ** float(mark)
    base_sum = round(sum(b for b, _n in stamped.values()), 6)
    now_sum = round(sum(n for _b, n in stamped.values()), 6)
    predicted = None if lift is None else round(base_sum * lift, 6)

    return {"scene_mark": mark,
            "interior_lamp_watts": round(sum(r["energy"] for r in plan["lamps"]), 3),
            "n_interior_lamps": len(plan["lamps"]),
            "n_interior_light_datablocks": len(seen),
            "n_lamp_stamps": len(stamped),
            "n_unstamped_interior_lamps": len(unstamped),
            "unstamped_interior_lamps": sorted(unstamped),
            "base_watts_from_stamps": base_sum,
            "stamped_watts_now": now_sum,
            "lift_multiplier": None if lift is None else round(lift, 9),
            "identity_base_x_lift": predicted,
            "identity_residual_w": (None if predicted is None
                                    else round(now_sum - predicted, 6)),
            "n_interior_emissive_materials": len(plan["materials"]),
            "interior_emission_strength_sum":
                round(sum(s["strength"] for m in plan["materials"]
                          for s in m["sockets"]), 4)}


# --------------------------------------------------------------------------- #
#  SELFTEST  --  a positive control that FAILS and a negative that PASSES
# --------------------------------------------------------------------------- #

def selftest():
    """Arithmetic and shell classification, with controls, without Blender."""
    bad = []
    print("LIFT_STOPS = %+.3f  =  -FILM_EXPOSURE (%+.3f)   multiplier x%.4f"
          % (LIFT_STOPS, FX.FILM_EXPOSURE, LIFT))

    # 1. the identity the whole file rests on
    d = abs((LIFT_STOPS + FX.FILM_EXPOSURE))
    print("   LIFT_STOPS + FILM_EXPOSURE = %+.6f  (must be 0)" % (
        LIFT_STOPS + FX.FILM_EXPOSURE))
    if d > 1e-6:
        bad.append("LIFT_STOPS does not cancel FILM_EXPOSURE")

    # 2. a lamp at the authored level, viewed at FILM_EXPOSURE, must land on
    #    the same display value as the unscaled lamp viewed at 0.000
    for w in (18.0, 130.0, 1000.0):
        lit = w * LIFT * (2.0 ** FX.FILM_EXPOSURE)
        print("   %8.1f W -> x%.4f -> viewed at %+.3f = %8.4f  (want %8.4f)"
              % (w, LIFT, FX.FILM_EXPOSURE, lit, w))
        if abs(lit - w) > 1e-6 * max(w, 1.0):
            bad.append("the round trip does not close for %g W" % w)

    # 3. POSITIVE CONTROL: the value this replaces must FAIL the same test.
    #    Leaving the practicals alone is a lift of 0 stops.
    ctrl = 130.0 * (2.0 ** 0.0) * (2.0 ** FX.FILM_EXPOSURE)
    ok = abs(ctrl - 130.0) > 1.0
    print("   POSITIVE CONTROL: no lift at all puts 130 W at %.4f, %.2f stops "
          "under -> %s" % (ctrl, math.log2(130.0 / ctrl),
                           "REJECTED, as it must be" if ok else
                           "ACCEPTED -- THIS TEST IS WORTHLESS"))
    if not ok:
        bad.append("the selftest accepts doing nothing")

    # 4. shell classification, with a point that must be in and one that must
    #    be out.  The out-point is the forecourt lamp line at x = +18.
    class P:
        def __init__(s, x, y, z):
            s.x, s.y, s.z = x, y, z
    cases = [(P(6.95, 0.0, 0.45), True, "a bollard lamp on the r=6.95 ring"),
             (P(0.0, 0.0, 6.05), True, "a ceiling cove"),
             (P(-15.24, 5.25, 2.44), True, "the back-wall light line"),
             (P(15.0, 0.0, 3.1), True, "the breach glass plane x = 15.000"),
             (P(18.0, 0.0, 3.0), False, "a forecourt lamp post outside the "
                                        "glass"),
             (P(0.0, -40.0, 0.5), False, "anything out on the circuit")]
    for p, want, what in cases:
        got = _in_shell(p)
        print("   shell: %-46s %-5s (want %s)" % (what, got, want))
        if got != want:
            bad.append("%s classified %s" % (what, got))

    # 5. WHOLE-BBOX CONTAINMENT, with the case a centre test gets wrong.
    class Fake:
        def __init__(s, corners):
            s._c = corners

    def _corners(x0, x1, y0, y1, z0, z1):
        return [P(x, y, z) for x in (x0, x1) for y in (y0, y1)
                for z in (z0, z1)]
    box_cases = [
        (_corners(-15, 15, -11, 11, -0.06, 0.0), True,
         "the showroom Floor, 30 x 22 m"),
        (_corners(-1000, 1000, -1000, 1000, -50, 50), False,
         "WORLD_TERRAIN, +/-1000 m, CENTRED ON THE SHOWROOM FLOOR"),
        (_corners(21.8, 22.2, -16.1, -15.9, 3.4, 3.5), False,
         "a forecourt lamp head out on the apron"),
    ]
    for corners, want, what in box_cases:
        got = all(_in_shell(p) for p in corners)
        centre_says = _in_shell(P(
            sum(p.x for p in corners) / len(corners),
            sum(p.y for p in corners) / len(corners),
            sum(p.z for p in corners) / len(corners)))
        print("   bbox:  %-46s %-5s (want %s; a centre-only test would say %s)"
              % (what, got, want, centre_says))
        if got != want:
            bad.append("%s classified %s" % (what, got))
    # the terrain case must be one a centre test GETS WRONG, or it proves
    # nothing about why whole-bbox containment is used
    terrain = box_cases[1][0]
    if not _in_shell(P(sum(p.x for p in terrain) / len(terrain),
                       sum(p.y for p in terrain) / len(terrain),
                       sum(p.z for p in terrain) / len(terrain))):
        bad.append("the WORLD_TERRAIN case does not fool a centre test, so it "
                   "is not testing what whole-bbox containment is here for")

    for b in bad:
        print("   FAIL " + b)
    print(">> STAGE RESULT: " + ("SHOWROOM_LIGHTING_OK" if not bad
                                 else "SHOWROOM_LIGHTING_FAIL"))
    return 0 if not bad else 1


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #

def _main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    if "--selftest" in argv or not argv:
        return selftest()

    import bpy
    scene = bpy.context.scene
    stops = LIFT_STOPS
    if "--stops" in argv:
        stops = float(argv[argv.index("--stops") + 1])
    manifest_path = None
    if "--manifest" in argv:
        manifest_path = argv[argv.index("--manifest") + 1]

    if "--dry-run" in argv:
        man = {"stops": stops, "multiplier": 2.0 ** stops,
               "would_change": classify(scene), "measured_now": measure(scene)}
    elif "--revert" in argv:
        revert(scene)
        man = {"reverted": True, "measured_now": measure(scene)}
    else:
        man = apply(scene, stops=stops)
        man["measured_now"] = measure(scene)

    if "--out" in argv:
        out = os.path.abspath(argv[argv.index("--out") + 1])
        os.makedirs(os.path.dirname(out), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
        print(">> saved %s" % out)
        man["out"] = out
    if manifest_path:
        os.makedirs(os.path.dirname(os.path.abspath(manifest_path)),
                    exist_ok=True)
        json.dump(man, open(manifest_path, "w"), indent=1)
        print(">> manifest %s" % manifest_path)
    print(">> STAGE RESULT: SHOWROOM_LIGHTING_APPLIED")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
