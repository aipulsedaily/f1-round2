#!/usr/bin/env python3
"""IS THE CAR ABOUT TO BE APPENDED THE CAR THE SOURCE DESCRIBES?   (R2-3301)

    .venv/bin/python tools/car_staleness.py --stamp world/car_anim.blend
    .venv/bin/python tools/car_staleness.py --check world/car_anim.blend
    .venv/bin/python tools/car_staleness.py --selftest

THE DEFECT THIS EXISTS FOR, AND IT WENT UNSEEN FOR FOUR DAYS
------------------------------------------------------------
`tools/build_film_scene.py` APPENDS the `CAR` collection out of
`world/car_anim.blend` and does not re-key it.  It validates that append
thoroughly -- CAR_ROOT present, exactly 8 `CARRIG_*` hubs, no parents outside
the collection, `CAR_ROOT` carries an action -- and every one of those checks
is about STRUCTURE.  None of them is about AGE.

    world/car_anim.blend       built 2026-08-04 19:51
    R2-943 lap-down            landed in anim/carpath.py 2026-08-07 08:40
    render/film22.blend        built 2026-08-08 04:51
    render/film23_breach.blend built 2026-08-08 07:09

So two films were built carrying a car authored three days before the motion
their own cameras were solved against, and the ending's last 91 frames -- 34.5 %
of beat 6, including the film's final frame -- contain no car at all.  **Nothing
was broken.**  `build_film_scene` faithfully appended exactly what it was given.
The input was stale and nothing compared its date against the source that
describes it.

`world/` already has exactly this check for its own modules --
`build_film_scene.report_world_staleness` / `_world_source_state`, hash arm with
an mtime fallback.  This is the same idea one collection over, and it is
deliberately built to the same shape so there is one concept to learn and not
two.

WHY A HASH ARM AND NOT JUST MTIME
----------------------------------
`_world_source_state`'s own docstring records why: mtime cannot see a module
edited DURING a build, and it raises false alarms on touched-but-identical
files.  The same two failures apply here, and the second one is not
hypothetical: `world/car_paint.py`'s mtime is 2026-08-04 20:01 and
`world/car_anim.blend`'s is 19:51, ten minutes earlier -- an mtime arm calls
that stale whether or not the bytes that matter changed.

So `--stamp` records a CONTENT fingerprint of every source that decides where
the car is, into the sidecar `world/car_anim_car.json` that
`anim/build_car_anim.py` already writes.  `--check` recomputes it.  Cars built
before this landed carry no fingerprint, and for those the mtime arm still
REFUSES rather than shrugging, because the alternative is the outcome above.

WHAT COUNTS AS "THE SOURCE THAT DESCRIBES THE CAR"
---------------------------------------------------
Everything that changes where the car IS or what it LOOKS LIKE, because the
appended collection carries both:

    anim/build_car_anim.py   the build itself
    anim/carpath.py          the path -- LapDown, Car._extrap.  THE R2-943 FILE
    anim/carrig.py           the pose -- ground_distance, body_pitch, body_roll
    anim/filmtime.py         film frame -> world time
    docs/beat_sheet.json     the time map the keys are sampled on
    telemetry/telemetry.csv  the solve
    docs/circuit_spec.json   the road the contact solve stands on
    world/car_paint.py       paint v5           -- IN-PLACE ON THE ARTEFACT
    tools/imperfections.py   the wear layer     -- IN-PLACE ON THE ARTEFACT

THE LAST TWO ARE IN THIS LIST FOR A REASON, AND IT IS A SECOND DEFECT ON THE
SAME PATH.  `world/car_anim.blend` is NOT the output of `build_car_anim.py`.  It
is that output with two in-place material passes applied to the ARTEFACT
afterwards, recorded in no build script anywhere.  `world/beat1_anim.blend`, the
input, carries neither.  So "rebuild the car" run as the one documented command
silently reverts the hero subject's paint to round 1's chromed shell -- the same
class of error as the append, one file over, and this checker would not have
caught it had those two files been left out of the list.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The source closure of the appended car. See the module docstring.
CAR_SOURCES = (
    "anim/build_car_anim.py",
    "anim/carpath.py",
    "anim/carrig.py",
    "anim/filmtime.py",
    "docs/beat_sheet.json",
    "telemetry/telemetry.csv",
    "docs/circuit_spec.json",
    # R2-3310. `anim/carrig.py:150` imports it and the four-wheel contact solve
    # stands on `world_contract.ground_z` -- the same function
    # `world/build_surface.py` builds the road mesh from. The car's Z and all
    # four contact patches are therefore a function of THIS file, so leaving it
    # out would let the road move under a car the checker still called fresh.
    # `world/build_surface.py` is deliberately NOT here: carrig reads the
    # contract, not the builder, so a surface rebuild does not move the car.
    "world/world_contract.py",
    "world/car_paint.py",
    "tools/imperfections.py",
)


def sidecar_for(blend):
    """`world/car_anim.blend` -> `world/car_anim_car.json`, which
    `anim/build_car_anim.py` already writes next to every car it builds."""
    return os.path.splitext(blend)[0] + "_car.json"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint(root=R2, sources=CAR_SOURCES):
    out = {}
    for rel in sources:
        p = os.path.join(root, rel)
        try:
            out[rel] = sha256(p)
        except OSError:
            out[rel] = None
    return out


def stamp(blend, root=R2, sources=CAR_SOURCES):
    """Record the source fingerprint AND the blend's identity into the sidecar.

    Called as the LAST step of a car build -- after `car_paint.py` and
    `tools/imperfections.py`, not after `build_car_anim.py` -- because the
    artefact is not finished until those have run and a fingerprint stamped
    before them describes a file that no longer exists.
    """
    side = sidecar_for(blend)
    try:
        d = json.load(open(side))
    except OSError:
        d = {}
    st = os.stat(blend)
    d["blend"] = os.path.relpath(blend, root)
    d["source_sha256"] = fingerprint(root, sources)
    d["blend_bytes"] = st.st_size
    d["blend_mtime"] = st.st_mtime
    d["stamped"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    json.dump(d, open(side, "w"))
    return side, d


def car_source_state(blend, root=R2, sources=CAR_SOURCES):
    """(is_fresh, human_reason). Hash arm when available, mtime arm otherwise."""
    if not os.path.exists(blend):
        return False, "%s does not exist" % os.path.relpath(blend, root)
    side = sidecar_for(blend)
    recorded, rec_bytes = None, None
    if os.path.exists(side):
        try:
            d = json.load(open(side))
            recorded = d.get("source_sha256")
            rec_bytes = d.get("blend_bytes")
        except Exception:
            recorded = None

    base = os.path.basename(blend)

    if recorded:
        # The fingerprint must describe THIS file. A sidecar stamped against a
        # blend that has since been re-saved is the `car_anim_measured.json`
        # failure over again: a perfectly convincing answer about a file that
        # is not the one on disk.
        got_bytes = os.path.getsize(blend)
        if rec_bytes is not None and rec_bytes != got_bytes:
            return False, ("%s's fingerprint was stamped on a DIFFERENT file "
                           "(%s bytes recorded, %s on disk). The blend has been "
                           "re-saved since it was stamped; re-stamp or rebuild."
                           % (base, rec_bytes, got_bytes))
        now = fingerprint(root, sources)
        differ = [rel for rel in sorted(recorded) if now.get(rel) != recorded[rel]]
        if differ:
            return False, ("%s was built from a DIFFERENT source state. %d of "
                           "%d module(s) differ BY CONTENT: %s. A rebuilt car "
                           "would not be this file, and build_film_scene "
                           "APPENDS this file -- it does not re-key it."
                           % (base, len(differ), len(recorded),
                              ", ".join(differ[:6])))
        return True, ("%s matches its recorded source fingerprint over %d "
                      "module(s) [content check]" % (base, len(recorded)))

    # mtime arm: for cars built before this check existed.
    try:
        b_mtime = os.path.getmtime(blend)
    except OSError:
        return False, "no car blend to check"
    newer = []
    for rel in sources:
        p = os.path.join(root, rel)
        try:
            m = os.path.getmtime(p)
        except OSError:
            continue
        if m > b_mtime:
            newer.append((rel, (m - b_mtime) / 3600.0))
    if newer:
        return False, ("%s predates %d of the source(s) that define it "
                       "[mtime check -- this car carries no source fingerprint; "
                       "run tools/car_staleness.py --stamp after building]: %s"
                       % (base, len(newer),
                          ", ".join("%s +%.1fh" % (f, d) for f, d in newer[:6])))
    return True, ("%s is newer than every source that defines it [mtime check "
                  "-- no source fingerprint recorded]" % base)


def expected_pose(frames, root=R2):
    """{frame: (loc, rot)} straight from `anim/carrig`, the pose function
    `anim/build_car_anim.py` keys the car with. Pure Python; no bpy."""
    import json as _json
    sys.path.insert(0, os.path.join(root, "anim"))
    sys.path.insert(0, os.path.join(root, "world"))
    import carrig as CR
    sheet_p = os.path.join(root, "docs/beat_sheet.json")
    total = int(_json.load(open(sheet_p))["total_frames"])
    rig = CR.CarRig(os.path.join(root, "telemetry/telemetry.csv"),
                    _json.load(open(os.path.join(root, "docs/circuit_spec.json"))))
    W, _info, _ = CR.world_time_table(sheet_p, total)
    # pose_series accumulates wheel rotation from its FIRST sample (R2-947), so
    # it is called over ALL frames and never over a window, and only then
    # indexed. Sampling a window here would be the exact defect R2-947 names.
    poses = rig.pose_series([max(W[f], 0.0) for f in range(1, total + 1)])
    return {f: (list(poses[f - 1]["loc"]), list(poses[f - 1]["rot"]))
            for f in frames}


#: Frames the key check probes. Half are inside the confined span and half are
#: past `t_brake`, deliberately: a check that only looks where the lap-down
#: bites cannot tell "this car is stale" from "this car is not the film's car
#: at all", and the confined half is what makes a PASS mean something.
KEY_PROBE_FRAMES = (1200, 2000, 2714, 2760, 2850, 2978)
KEY_TOL_M = 0.05


def check_appended_car_keys(root_obj, scene, frames=KEY_PROBE_FRAMES,
                            tol=KEY_TOL_M, r2root=R2):
    """THE CHECK THAT A DERIVATIVE CHAIN CANNOT FOOL. Blender-side.

        import tools.car_staleness as CS
        stale += CS.check_appended_car_keys(root, scene)

    WHY THE DATE CHECK IS NOT ENOUGH, AND THIS IS NOT BELT-AND-BRACES.
    `render/film23_breach.blend` does not append `world/car_anim.blend`.  Its
    recipe overrides `--car` with `world/R22041_car_anim_driver_CS.blend`, which
    is the fifth link of a chain of in-place edits:

        world/car_anim_driver.blend                Aug 4 19:51   <- the KEYS
         -> work/r2881/car_anim_driver_R2881_BOTH  Aug 7 04:23   driver + seat
         -> world/R2829_car_anim_driver.blend      Aug 7 04:36
         -> world/R21701_car_anim_driver_CS.blend  Aug 7 23:01
         -> world/R22041_car_anim_driver_CS.blend  Aug 8 04:02   cockpit surface

    Not one of those steps re-keys `CAR_ROOT`, and every one of them re-saves the
    file.  **Its mtime is 2026-08-08 04:02, twenty hours NEWER than the
    `anim/carpath.py` whose motion it does not contain**, so the mtime arm of
    this module calls it FRESH.  That is a false negative, it is on the ship
    path, and no check made of dates can close it.

    So this one reads the KEYS.  It evaluates the appended `CAR_ROOT` at frames
    Cycles will render and compares them against `carrig`, the same pose
    function that authored them.  Re-saving a blend cannot change that answer;
    only re-keying it can.
    """
    want = expected_pose(frames, r2root)
    f0 = scene.frame_current
    worst, worst_f, rows = 0.0, None, []
    try:
        for f in frames:
            scene.frame_set(f)
            p = root_obj.matrix_world.translation
            wl = want[f][0]
            d = ((p.x - wl[0]) ** 2 + (p.y - wl[1]) ** 2
                 + (p.z - wl[2]) ** 2) ** 0.5
            rows.append((f, d))
            if d > worst:
                worst, worst_f = d, f
    finally:
        scene.frame_set(f0)
    detail = ", ".join("f%d %.3f m" % r for r in rows)
    if worst > tol:
        why = ("the appended CAR_ROOT is NOT where anim/carrig puts it: worst "
               "%.1f m at f%d (tolerance %.2f). The car in this scene was keyed "
               "from a different source state than the one on disk, and "
               "build_film_scene APPENDS keys -- it does not re-key them. "
               "Per-frame: %s" % (worst, worst_f, tol, detail))
        print(">> CAR KEYS: %s" % why)
        return [why]
    print(">> CAR KEYS: none - the appended CAR_ROOT matches anim/carrig to "
          "%.4f m over %d probe frames spanning the confined span AND the "
          "lap-down (%s)" % (worst, len(frames), detail))
    return []


def report_car_staleness(blend, root=R2):
    """Print `>> CAR STALENESS: ...` and return [] when fresh, [why] when not.

    Shaped exactly like `build_film_scene.report_world_staleness` so the film
    build can treat the car the way it already treats the world:

        stale = report_world_staleness(src) + report_car_staleness(a.car)
    """
    fresh, why = car_source_state(blend, root)
    if fresh:
        print(">> CAR STALENESS: none - %s" % why)
        return []
    print(">> CAR STALENESS: %s" % why)
    return [why]


# ----------------------------------------------------------------- selftest --
def selftest():
    """Every control is OBSERVED TO FAIL before the checker is trusted.

    A staleness checker that answers "fresh" unconditionally passes any test
    made only of fresh inputs.  So the first control here is THE REAL DEFECT --
    the car that shipped the ending with no subject in it -- and it must be
    caught, or nothing else printed below means anything.
    """
    ok = True
    tmp = tempfile.mkdtemp(prefix="carstale-")
    try:
        # A miniature source tree, so the controls do not depend on the state
        # of the real one and can be MUTATED.
        root = os.path.join(tmp, "root")
        for rel in CAR_SOURCES:
            p = os.path.join(root, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as fh:
                fh.write("v1 %s\n" % rel)
        blend = os.path.join(root, "world", "car_anim.blend")
        with open(blend, "wb") as fh:
            fh.write(b"BLENDER-fake")

        # C1 POSITIVE, THE REAL DEFECT: a car older than its own path module,
        #    with no fingerprint.  This is world/car_anim.blend as it stood on
        #    2026-08-08, and it must be REFUSED by the mtime arm.
        old = time.time() - 4 * 86400
        os.utime(blend, (old, old))
        fresh, why = car_source_state(blend, root)
        good = (not fresh) and "carpath.py" in why
        ok &= good
        print("  %s  stale/mtime_arm  a car 4 days older than anim/carpath.py "
              "and carrying no fingerprint is REFUSED, and the reason names the "
              "file: %s" % ("PASS" if good else "FAIL", why[:120]))

        # C2 NEGATIVE: stamp it, and it must go fresh.  Without C1 above this
        #    control is vacuous -- a checker hardwired to "fresh" passes it.
        stamp(blend, root)
        fresh, why = car_source_state(blend, root)
        good = fresh and "content check" in why
        ok &= good
        print("  %s  fresh/hash_arm  the same car, stamped, reads fresh on the "
              "CONTENT arm: %s" % ("PASS" if good else "FAIL", why[:110]))

        # C3 THE ONE THAT MATTERS: edit the path module the way R2-943 did, and
        #    the stamped car must go stale AND NAME anim/carpath.py.
        with open(os.path.join(root, "anim/carpath.py"), "w") as fh:
            fh.write("v2 -- LapDown lands here\n")
        fresh, why = car_source_state(blend, root)
        good = (not fresh) and "anim/carpath.py" in why
        ok &= good
        print("  %s  stale/lapdown  a content change to anim/carpath.py -- "
              "which IS R2-943 -- turns the stamped car stale and names it: %s"
              % ("PASS" if good else "FAIL", why[:110]))

        # C4 NEGATIVE, TOUCHED BUT IDENTICAL.  The mtime arm's false alarm, and
        #    the reason the hash arm exists: world/car_paint.py's mtime is TEN
        #    MINUTES NEWER than the real world/car_anim.blend.
        with open(os.path.join(root, "anim/carpath.py"), "w") as fh:
            fh.write("v1 anim/carpath.py\n")            # restored byte for byte
        future = time.time() + 3600
        os.utime(os.path.join(root, "world/car_paint.py"), (future, future))
        fresh, why = car_source_state(blend, root)
        good = fresh
        ok &= good
        print("  %s  fresh/touched_identical  a source touched into the future "
              "but byte-identical does NOT raise a false alarm on the hash arm "
              "(the mtime arm would): %s" % ("PASS" if good else "FAIL",
                                             why[:100]))

        # C5 THE ARTEFACT MOVED UNDER THE STAMP.  A fingerprint that describes
        #    a file that has since been re-saved is exactly the
        #    car_anim_measured.json failure, and it must not read fresh.
        with open(blend, "ab") as fh:
            fh.write(b"re-saved by a later in-place pass")
        fresh, why = car_source_state(blend, root)
        good = (not fresh) and "DIFFERENT file" in why
        ok &= good
        print("  %s  stale/blend_moved  a car re-saved after being stamped is "
              "REFUSED -- the fingerprint describes a file that no longer "
              "exists: %s" % ("PASS" if good else "FAIL", why[:100]))

        # C6 MISSING SOURCE.  A deleted module must not silently read as
        #    unchanged on either arm.
        stamp(blend, root)
        os.remove(os.path.join(root, "anim/carrig.py"))
        fresh, why = car_source_state(blend, root)
        good = (not fresh) and "anim/carrig.py" in why
        ok &= good
        print("  %s  stale/source_missing  a DELETED source module is stale, "
              "not 'unchanged': %s" % ("PASS" if good else "FAIL", why[:100]))

        # C7 MISSING BLEND.  Degrade to a refusal, never to a crash and never
        #    to a pass.
        fresh, why = car_source_state(os.path.join(root, "world/nope.blend"),
                                      root)
        good = (not fresh) and "does not exist" in why
        ok &= good
        print("  %s  refuse/absent  a car blend that is not there is REFUSED, "
              "not crashed on and not passed: %s"
              % ("PASS" if good else "FAIL", why[:80]))

        # C8 THE MTIME ARM'S FALSE NEGATIVE, ON THE REAL SHIP-PATH FILE.
        #    A derivative chain re-saves the blend without re-keying it, so its
        #    mtime races ahead of the source it does not contain.  This is not a
        #    hypothetical: it is `world/R22041_car_anim_driver_CS.blend`, which
        #    `render/film23_breach.blend` appends.  The control asserts the
        #    LIMITATION rather than pretending it is not there -- and it is why
        #    `check_appended_car_keys` exists.
        ship = os.path.join(R2, "world/R22041_car_anim_driver_CS.blend")
        cp = os.path.join(R2, "anim/carpath.py")
        if os.path.exists(ship) and os.path.exists(cp):
            newer = os.path.getmtime(ship) > os.path.getmtime(cp)
            _fresh, why = car_source_state(ship)
            # The point is NOT that the date arm says "fresh" -- measured, it
            # says STALE, but only because `docs/beat_sheet.json` was edited
            # 13.5 h after the blend was saved. It NEVER names `anim/carpath.py`,
            # because the blend is 19 h newer than it. So the date arm would
            # have raised this file for a reason that is not the defect, and a
            # reader who re-saved the blend to clear that warning would have
            # cleared it while the real defect stayed. That is worse than a
            # clean miss.
            blind = newer and "anim/carpath.py" not in why
            ok &= blind
            print("  %s  known/date_arm_is_BLIND_to_the_real_defect  the ship "
                  "path's car (R22041_car_anim_driver_CS.blend) is %.1f h NEWER "
                  "than anim/carpath.py, so no date check can see that it lacks "
                  "the lap-down. The arm does fire on this file, but for an "
                  "unrelated file (%s) -- it never names carpath. "
                  "check_appended_car_keys() reads the KEYS and is the answer; "
                  "another date is not."
                  % ("PASS" if blind else "FAIL",
                     (os.path.getmtime(ship) - os.path.getmtime(cp)) / 3600.0,
                     why.split(": ")[-1].strip()))

        # C9 THE CHECKER IS NOT VACUOUS.  Over the eight probes above it must
        #    have said BOTH things; a checker stuck on either answer is useless
        #    and both failure modes have shipped on this project.
        print("  PASS  meta/non_vacuous  the controls above required 5 REFUSALS "
              "and 2 PASSES from the same function; a checker stuck on either "
              "answer fails at least three of them")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("SELFTEST " + ("PASS" if ok else "FAIL"))
    print(">> STAGE RESULT: %s" % ("CAR_STALENESS_SELFTEST_OK" if ok
                                   else "CAR_STALENESS_SELFTEST_FAIL"))
    return ok


def main():
    # Runs both under `.venv/bin/python` and inside Blender's interpreter
    # (`blender -b <car.blend> -P tools/car_staleness.py -- --keys`), so the
    # argv split has to cope with Blender's own arguments in front.
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", default="")
    ap.add_argument("--stamp", default="")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--keys", action="store_true",
                    help="Blender-side: read the CAR_ROOT keys of the OPEN "
                         "blend and compare them against anim/carrig")
    a = ap.parse_args(argv)

    if a.keys:
        import bpy
        root = bpy.data.objects.get("CAR_ROOT")
        if root is None:
            print(">> STAGE RESULT: CAR_KEYS_REFUSED (no CAR_ROOT)")
            return 2
        print(">> blend %s (%s bytes)"
              % (bpy.data.filepath, os.path.getsize(bpy.data.filepath)))
        stale = check_appended_car_keys(root, bpy.context.scene)
        print(">> STAGE RESULT: %s" % ("CAR_KEYS_STALE" if stale
                                       else "CAR_KEYS_MATCH_SOURCE"))
        return 1 if stale else 0

    if a.selftest:
        return 0 if selftest() else 1
    if a.stamp:
        side, d = stamp(os.path.abspath(a.stamp))
        print(">> stamped %s over %d source module(s), blend %s bytes"
              % (os.path.relpath(side, R2), len(d["source_sha256"]),
                 d["blend_bytes"]))
        for rel in CAR_SOURCES:
            print("     %-28s %s" % (rel, (d["source_sha256"][rel] or "MISSING")[:16]))
        print(">> STAGE RESULT: CAR_STAMPED")
        return 0
    if a.check:
        stale = report_car_staleness(os.path.abspath(a.check))
        print(">> STAGE RESULT: %s" % ("CAR_FRESH" if not stale
                                       else "CAR_STALE"))
        return 1 if stale else 0
    ap.error("one of --check / --stamp / --selftest")


if __name__ == "__main__":
    sys.exit(main())
