"""R2-1078: a comparison rig inherits NONE of the film's correctness by looking
like it.

`world/surface_test_filmpose.blend` had the film's elevation, the film's
resolution and the film's frame numbers, and its sun bearing was **139.61 deg
wrong**.  It also carried a bare Sky Texture and a -3.048 grade -- the exact
exposure R2-071 refuted.  It has no saved builder, so it cannot be rebuilt,
audited or diffed, and it produced **two confident wrong verdicts** (R2-1036 and
R2-1042) that were relayed to the client before anyone thought to ask what the
rig was lit by.

The builder is not recoverable.  What IS recoverable is the guarantee that no
rig gets used silently while it disagrees with the film -- so this refuses to
proceed rather than reporting a difference into a log nothing gates on.  That
distinction is R2-1051: `horizon_gate.py` printed an accurate description of a
live defect on every run for three days, as a `print()` that touched neither the
verdict nor the exit code.  **A detection that does not reach an exit code is a
rumour.**

    blender -b world/surface_test_filmpose.blend -P tools/rig_preflight.py
    blender -b <any rig>                         -P tools/rig_preflight.py -- --json out.json
    .venv/bin/python tools/rig_preflight.py --selftest      (no Blender needed)

WHAT IT CHECKS, AND WHY EACH ONE EXISTS
=======================================
SUN_BEARING   the failure that caused this.  Elevation alone passes on a rig
              rotated 139.61 deg about Z, because elevation is invariant under
              exactly that rotation -- which is why "the sun looked right" held
              for two investigations.  Bearing is checked SEPARATELY from
              elevation for that reason, and the full angle is reported too.
EXPOSURE      the rig graded at -3.048.  R2-071 measured that value as
              over-exposing by 0.586 stops and settled on -3.628.  A rig may not
              disagree with the film about the film's own grade.
VIEW_TRANSFORM delivery is AgX / look None.  A rig on Standard or Filmic
              measures a different curve's shoulder and calls it the film's.
WORLD_SKY     a bare Sky Texture is not the film's sky: no cloud decks, no
              atmosphere geometry.  Into-sun frames are exactly where that
              matters, and exactly where the wrong verdicts landed.

TOLERANCES are deliberately tight.  A rig is not an approximation of the film;
it is the film with one thing changed, and anything else that differs is a
confound waiting to be reported as a finding.
"""
import argparse
import json
import math
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if R2 not in sys.path:
    sys.path.insert(0, R2)
if os.path.join(R2, "tools") not in sys.path:
    sys.path.insert(0, os.path.join(R2, "tools"))

import gate_exit                                                 # noqa: E402

#: from `world/world_contract.py` SUN_DIR and `world/film_exposure.py`
#: FILM_EXPOSURE.  Imported at run time, not typed -- a preflight that carries
#: its own copy of the constant it is checking is checking itself.
TOL_SUN_DEG = 0.05
TOL_EXPOSURE = 0.005


def film_constants():
    """(sun_dir, exposure) from the film's own modules.  No literals."""
    from world import world_contract as WC
    from world import film_exposure as FE
    return tuple(WC.SUN_DIR), float(FE.FILM_EXPOSURE)


def _ang(a, b):
    """Angle between two 3-vectors, degrees."""
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    d = sum(x * y for x, y in zip(a, b)) / (na * nb)
    return math.degrees(math.acos(max(-1.0, min(1.0, d))))


def _elev_bearing(v):
    """Elevation above horizon and compass bearing, both degrees."""
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    x, y, z = (c / n for c in v)
    return math.degrees(math.asin(max(-1.0, min(1.0, z)))), \
        math.degrees(math.atan2(y, x))


def evaluate(rig, sun_ref, exposure_ref):
    """The whole judgement, as data.  `rig` is a plain dict so this runs
    without Blender -- a checker that can only be exercised by opening a 58 MB
    blend is a checker nobody proves."""
    fails = []

    sun = rig.get("sun_dir")
    if sun is None:
        fails.append(dict(check="SUN_BEARING", detail="no sun found in rig"))
    else:
        el_r, bg_r = _elev_bearing(sun)
        el_f, bg_f = _elev_bearing(sun_ref)
        dbg = abs((bg_r - bg_f + 180.0) % 360.0 - 180.0)
        full = _ang(sun, sun_ref)
        if full > TOL_SUN_DEG:
            fails.append(dict(
                check="SUN_BEARING", detail=(
                    "sun is %.2f deg from the film's "
                    "(elevation %+.3f deg, bearing %+.3f deg). "
                    "Elevation alone is invariant under exactly this error"
                    % (full, el_r - el_f, dbg))))

    exp = rig.get("exposure")
    if exp is None or abs(exp - exposure_ref) > TOL_EXPOSURE:
        fails.append(dict(check="EXPOSURE", detail=(
            "rig grades at %s, the film at %.3f" % (exp, exposure_ref))))

    vt, look = rig.get("view_transform"), rig.get("look")
    if vt != "AgX" or look not in (None, "None", ""):
        fails.append(dict(check="VIEW_TRANSFORM", detail=(
            "rig is %s / look %s, delivery is AgX / look None" % (vt, look))))

    nodes = rig.get("world_nodes") or []
    if "ShaderNodeTexSky" in nodes and len(nodes) <= 3:
        fails.append(dict(check="WORLD_SKY", detail=(
            "world is a bare Sky Texture (%d node(s)); the film's sky carries "
            "cloud decks and atmosphere geometry, and into-sun frames are "
            "exactly where that matters" % len(nodes))))
    return fails


# --------------------------------------------------------------------------- #
#  Reading a live .blend.  Only this part needs Blender.
# --------------------------------------------------------------------------- #

def read_rig():
    import bpy
    from mathutils import Vector
    sc = bpy.context.scene
    sun = None
    for o in bpy.data.objects:
        if o.type == "LIGHT" and o.data.type == "SUN":
            d = (o.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
            sun = (-d.x, -d.y, -d.z)          # direction TO the sun
            break
    vs = sc.view_settings
    w = sc.world
    nodes = [n.bl_idname for n in w.node_tree.nodes] \
        if (w and w.use_nodes) else []
    return dict(sun_dir=sun, exposure=float(vs.exposure),
                view_transform=vs.view_transform, look=vs.look,
                world_nodes=nodes,
                blend=bpy.data.filepath)


# --------------------------------------------------------------------------- #

def selftest():
    fails = []

    def check(name, cond, detail=""):
        print("  %-56s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            fails.append(name)

    sun_f, exp_f = film_constants()
    ok = dict(sun_dir=sun_f, exposure=exp_f, view_transform="AgX", look="None",
              world_nodes=["ShaderNodeTexSky", "ShaderNodeBackground",
                           "ShaderNodeOutputWorld", "ShaderNodeMixRGB",
                           "ShaderNodeTexNoise"])

    check("CLEAN: a rig matching the film passes",
          evaluate(ok, sun_f, exp_f) == [])

    # THE REAL RIG, as it sits on disk.  Values from R2-1061's probe.
    real = dict(ok, sun_dir=(0.00000, 0.97641, 0.21594), exposure=-3.048,
                world_nodes=["ShaderNodeTexSky", "ShaderNodeBackground",
                             "ShaderNodeOutputWorld"])
    got = {f["check"] for f in evaluate(real, sun_f, exp_f)}
    check("REAL_RIG: surface_test_filmpose.blend as it is now FAILS",
          got == {"SUN_BEARING", "EXPOSURE", "WORLD_SKY"},
          "fired: %s" % sorted(got))

    # The one that matters most: elevation is invariant under the error, so a
    # check written on elevation would have passed this rig for two months.
    el_r, _ = _elev_bearing(real["sun_dir"])
    el_f, _ = _elev_bearing(sun_f)
    check("ELEVATION_TRAP: the broken rig's ELEVATION matches the film's",
          abs(el_r - el_f) < 1e-3,
          "%.5f deg vs %.5f -- identical, and the bearing is %.2f deg out"
          % (el_r, el_f, _ang(real["sun_dir"], sun_f)))

    got = {f["check"] for f in evaluate(dict(ok, exposure=-3.048), sun_f, exp_f)}
    check("EXPOSURE_ONLY: a rig wrong only in grade fires only EXPOSURE",
          got == {"EXPOSURE"}, "fired: %s" % sorted(got))

    got = {f["check"] for f in
           evaluate(dict(ok, view_transform="Filmic"), sun_f, exp_f)}
    check("TRANSFORM: a rig on Filmic fires only VIEW_TRANSFORM",
          got == {"VIEW_TRANSFORM"}, "fired: %s" % sorted(got))

    got = {f["check"] for f in evaluate(dict(ok, sun_dir=None), sun_f, exp_f)}
    check("NO_SUN: a rig with no sun at all FAILS rather than passing",
          got == {"SUN_BEARING"}, "fired: %s" % sorted(got))

    # A rig 0.04 deg off must pass: the tolerance is tight, not zero, or float
    # round-trips through a .blend would make the gate unusable.
    import math as _m
    a = _m.radians(0.04)
    tilt = (sun_f[0] * _m.cos(a) - sun_f[1] * _m.sin(a),
            sun_f[0] * _m.sin(a) + sun_f[1] * _m.cos(a), sun_f[2])
    check("TOLERANCE: a rig 0.04 deg off passes; the tolerance is not zero",
          evaluate(dict(ok, sun_dir=tilt), sun_f, exp_f) == [],
          "%.4f deg" % _ang(tilt, sun_f))

    check("CONSTANTS: the reference comes from the film's own modules",
          abs(exp_f + 3.628) < 1e-9 and abs(sun_f[0] - 0.5178540) < 1e-9,
          "FILM_EXPOSURE %.3f  SUN_DIR %s" % (exp_f, tuple(round(c, 6) for c in sun_f)))

    print("\n>> STAGE RESULT: RIG_PREFLIGHT_SELFTEST %s (%d failed)"
          % ("FAIL" if fails else "PASS", len(fails)))
    return 1 if fails else 0


def _argv():
    """THIS TOOL'S ARGUMENTS, WHICH ARE NOT BLENDER'S FLAGS.  R2-2821.

    The very first usage line in this file's docstring is

        blender -b world/surface_test_filmpose.blend -P tools/rig_preflight.py

    and until R2-2821 that command line KILLED IT.  There is no `--`, so the
    old fallback -- "every argv entry that is not a .py" -- handed argparse

        -b world/surface_test_filmpose.blend --factory-startup -noaudio -P

    argparse called that a usage error and exited 2 BEFORE `evaluate()` was
    reached, so the run produced no `>> STAGE RESULT:` line at all.  A caller
    grepping for the verdict saw nothing; a caller reading `$?` saw 2, which is
    CRASH, not FAIL.  The guard could not fire even once it was being invoked
    correctly.

    Inside Blender with no `--`, this tool takes NO arguments.  That is the
    only reading of `sys.argv` that is safe, because everything before the `--`
    belongs to Blender by definition.
    """
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1:]
    if "bpy" in sys.modules or \
            os.path.basename(sys.argv[0]).lower().startswith("blender"):
        return []
    return [a for a in sys.argv[1:] if not a.endswith(".py")]


def main():
    argv = _argv()
    ap = argparse.ArgumentParser(prog="rig_preflight")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", default="")
    # argparse exits 2 on a usage error and prints NOTHING this project can
    # read.  That is how the guard spent its whole life invisible: exit 2, no
    # `>> STAGE RESULT:` line, and a caller that greps for the verdict sees
    # silence.  `return`, not `sys.exit`, inside this `except`: R2-2108's two
    # instruments both printed a second verdict because `sys.exit` raises
    # `SystemExit` and their `except BaseException` caught it.
    try:
        a = ap.parse_args(argv)
    except SystemExit:
        print(">> STAGE RESULT: RIG_PREFLIGHT_CRASH (unusable arguments %r)"
              % (argv,))
        return gate_exit.CRASH

    if a.selftest:
        return selftest()

    sun_f, exp_f = film_constants()
    rig = read_rig()
    bad = evaluate(rig, sun_f, exp_f)
    print(">> RIG   %s" % rig.get("blend"))
    # NB: a tuple on the right of `%` is UNPACKED, so both of these are wrapped
    # in a 1-tuple.  The first version of this line raised TypeError -- and
    # Blender exited 0 on it, which is the whole reason this file judges on a
    # printed `>> STAGE RESULT:` line and never on `$?`.
    print(">> SUN   rig %s" % ((tuple(round(c, 6) for c in rig["sun_dir"])
                                if rig.get("sun_dir") else None),))
    print(">> SUN   film %s" % (tuple(round(c, 6) for c in sun_f),))
    print(">> GRADE rig %.4f / %s / look %s   film %.3f / AgX / look None"
          % (rig["exposure"], rig["view_transform"], rig["look"], exp_f))
    for f in bad:
        print("   FAIL %-14s %s" % (f["check"], f["detail"]))
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(dict(rig=rig, failures=bad), fh, indent=1, default=float)
    # ONE string produces both the printed verdict and the exit code, so the
    # two cannot disagree -- `gate_exit`'s whole reason for existing.  The
    # token is `RIG_PREFLIGHT_OK`, with an underscore: `gate_exit.code_for`
    # matches on the substrings `_OK` / `PASS` / `FAIL`, and the old
    # space-separated "RIG_PREFLIGHT OK" mapped to CRASH.
    return gate_exit.verdict("RIG_PREFLIGHT_%s" % ("FAIL" if bad else "OK"))


if __name__ == "__main__":
    gate_exit.guard(main, tool="RIG_PREFLIGHT")
