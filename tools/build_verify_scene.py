"""VERIFICATION SCENE — the rig, plus a car you can SEE, in a world you can see.

    /opt/blender-5.2.0-linux-x64/blender -b <world.blend> --factory-startup \
        -P tools/build_verify_scene.py -- --out world/verify_world.blend \
        [--sheet ...] [--telemetry ...]

WHY THIS EXISTS
---------------
The aim gate says the camera is pointed at the car. That is a number, and this
project has shipped seven numbers that were true about the wrong quantity. The
only check that has reliably caught those is opening the image.

So this builds the same rig into a world blend and adds ONE extra object: a
telemetry-driven proxy of the car — the measured 5.698 x 2.005 x 0.992 m box,
on the racing line, at the world time the film's time map says that frame is at,
lit emissive so it reads at 200 m. If a rendered frame shows the box where the
gate says the car is, the gate and the picture agree. If it shows sky, they do
not, and the picture wins.

The proxy exists ONLY here. `world/camera_rig.blend`, the deliverable, has no
proxy in it — a stand-in that leaks into the film would be a much worse defect
than the one it was built to catch.

THE GRADE — WHY THIS FILE NOW ASSERTS IT
----------------------------------------
This rig used to set NO exposure at all. It is opened on a world blend, and the
assembly blends carry view exposure +0.000 (only render_setup2/3 ever wrote the
film's grade, and they do not run here), so every frame an agent looked at came
out of this instrument at +0.000 against the film's measured -3.628: **3.628
stops over**. Correct work looked blown out, and work was "fixed" that was never
broken. That is the instrument being the defect, which on this project has now
happened two dozen times.

Setting the number here would only move the problem: a rig that silently sets a
constant can drift back out of agreement with the film and nothing would notice.
So this file does BOTH — it applies `world/film_exposure.py`'s grade before the
rig is built (the ramp in build_camera_rig is a DELTA from the scene's own
exposure, so the daylight end must already be right when it runs), and then, on
the built scene, it ASSERTS that every place exposure can enter agrees with that
one file, and raises if any of them does not.

The assertion is proven, not assumed: `--control-break-exposure` and
`--control-break-view-transform` exist so anyone can watch it fire. An assertion
nobody has seen fail has not been shown to work.
"""

import argparse
import importlib.util
import math
import os
import sys

import bpy
from mathutils import Vector

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "anim"))
import filmtime as FT                                              # noqa: E402
from carpath import Car, CAR_LEN, CAR_HALF_W, CAR_TOP_Z            # noqa: E402

# THE ONE SOURCE OF THE GRADE. Imported hard, not in a try/except: a verify rig
# that cannot reach the film's exposure has nothing useful to show anybody, and
# falling back to "whatever the blend had" is exactly the failure being fixed.
sys.path.insert(0, os.path.join(R2, "world"))
import film_exposure as FX                                         # noqa: E402

#: How far the rig's grade may sit from the film's before this build fails, in
#: stops. This is NOT the measurement's resolution (0.05 stops, which is how
#: well -3.628 itself is known) — the rig and the film read the SAME constant,
#: so their only legitimate difference is float32 round-trip through an F-curve
#: keyframe, ~2e-7. Anything above 0.001 stops means two numbers, not one.
GRADE_TOL_STOPS = 1e-3


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    p.add_argument("--telemetry", default=os.path.join(R2, "telemetry/telemetry.csv"))
    p.add_argument("--spec", default=os.path.join(R2, "docs/circuit_spec.json"))
    p.add_argument("--out", required=True)
    p.add_argument("--no-proxy", action="store_true")
    p.add_argument("--shutter-mode", choices=("flat", "world"), default="flat",
                   help="passed straight through to build_camera_rig; the A/B "
                        "that R2-037's shutter decision is measured on")
    p.add_argument("--control-break-exposure", type=float, default=None,
                   metavar="STOPS",
                   help="POSITIVE CONTROL ONLY. Grade the scene at this "
                        "exposure instead of film_exposure.FILM_EXPOSURE, so "
                        "the grade assertion can be SEEN to fail (try 0.0, or "
                        "-3.048, the refuted contract value). Never use this "
                        "for a verify build you intend to look at.")
    p.add_argument("--control-break-view-transform", default=None,
                   metavar="NAME",
                   help="POSITIVE CONTROL ONLY. Same idea for the view "
                        "transform (try 'Standard' or 'Filmic'): an exposure "
                        "match under the wrong transform is still a lying "
                        "instrument, so that has to be seen to fail too.")
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
#  THE GRADE: applied from world/film_exposure.py, then asserted against it
# ---------------------------------------------------------------------------

def _looks_same(a, b):
    """Blender spells 'no look' as 'None', 'NONE' or '' depending on version."""
    na = (a or "").strip().upper().replace(" ", "")
    nb = (b or "").strip().upper().replace(" ", "")
    return (na in ("", "NONE") and nb in ("", "NONE")) or na == nb


def _scene_fcurves(scene):
    """Every F-curve on the SCENE, across Blender 4.x and 5.x action layouts."""
    ad = getattr(scene, "animation_data", None)
    act = getattr(ad, "action", None)
    if act is None:
        return []
    if hasattr(act, "fcurves"):                       # legacy (Blender <= 4.x)
        return list(act.fcurves)
    out = []
    slot = getattr(ad, "action_slot", None)
    for layer in act.layers:
        for strip in layer.strips:
            bags = []
            if slot is not None:
                bag = strip.channelbag(slot)
                if bag:
                    bags.append(bag)
            if not bags:
                bags = list(getattr(strip, "channelbags", []))
            for bag in bags:
                out += list(bag.fcurves)
    return out


def apply_film_grade(scene, break_exposure=None, break_view_transform=None):
    """Put the FILM's grade on the scene BEFORE the rig is built.

    Order matters. build_camera_rig keys its interior->daylight ramp as a DELTA
    from `scene.view_settings.exposure` as it finds it, so if this ran after the
    rig the ramp's daylight end would still be the blend's stale value.
    """
    got = FX.apply(scene)
    print(">> GRADE from world/film_exposure.py: exposure %+.3f, "
          "view_transform %s, look %s  (%s)"
          % (got["exposure"], got["view_transform"], got["look"],
             got["derivation"]))
    if break_exposure is not None:
        scene.view_settings.exposure = float(break_exposure)
        print("   !! POSITIVE CONTROL: exposure deliberately broken to "
              "%+.3f. The grade assertion MUST fail below." % break_exposure)
    if break_view_transform is not None:
        scene.view_settings.view_transform = break_view_transform
        print("   !! POSITIVE CONTROL: view transform deliberately broken to "
              "%r. The grade assertion MUST fail below." % break_view_transform)
    return got


def assert_grade_is_the_films(scene, total_frames):
    """RAISE unless every place exposure enters this scene equals the film's.

    Checked, because each of them is a way the picture can lie on its own:
      * view_settings.view_transform / .look — an exposure match under the
        wrong transform is still a lying instrument.
      * view_settings.exposure, the static value.
      * the exposure F-curve build_camera_rig keys: its daylight end must BE
        FILM_EXPOSURE and its interior end FILM_EXPOSURE - INTERIOR_STOPS,
        and it must evaluate to FILM_EXPOSURE on the last frame.
      * cycles.film_exposure, a linear multiplier ahead of the view transform.
      * a compositor exposure node, which would be a third grade again.
    """
    vs = scene.view_settings
    film = FX.FILM_EXPOSURE
    interior = film - FX.INTERIOR_STOPS
    src = "world/film_exposure.py (FILM_EXPOSURE, MEASURED on the 5090 — see " \
          "render/exposure_cal/expcal_measured.json)"
    bad = []

    print(">> GRADE ASSERTION — the rig's grade against %s" % src)
    print("   view_transform   rig %-12r   film %r" % (vs.view_transform,
                                                       FX.VIEW_TRANSFORM))
    if vs.view_transform != FX.VIEW_TRANSFORM:
        bad.append("view_transform is %r on the built rig; the film's is %r, "
                   "from world/film_exposure.VIEW_TRANSFORM (= "
                   "world_contract.VIEW_TRANSFORM). An exposure match under "
                   "the wrong transform is still a lying instrument."
                   % (vs.view_transform, FX.VIEW_TRANSFORM))
    print("   look             rig %-12r   film %r" % (vs.look, FX.VIEW_LOOK))
    if not _looks_same(vs.look, FX.VIEW_LOOK):
        bad.append("look is %r on the built rig; the film's is %r, from "
                   "world/film_exposure.VIEW_LOOK (= world_contract.VIEW_LOOK, "
                   "'ONE lens, ONE grade')." % (vs.look, FX.VIEW_LOOK))

    print("   exposure static  rig %+.4f       film %+.4f" % (vs.exposure, film))
    if abs(float(vs.exposure) - film) > GRADE_TOL_STOPS:
        bad.append("scene.view_settings.exposure is %+.4f on the built rig; "
                   "the film's is %+.4f, from %s. That is %+.4f stops off "
                   "(tolerance %.4f). %s"
                   % (vs.exposure, film, src, vs.exposure - film,
                      GRADE_TOL_STOPS, _diagnose(float(vs.exposure), film)))

    fc = None
    for c in _scene_fcurves(scene):
        if c.data_path == "view_settings.exposure":
            fc = c
            break
    if fc is None:
        bad.append("the built scene has NO `view_settings.exposure` F-curve. "
                   "build_camera_rig keys the interior->daylight ramp on every "
                   "run, so its absence means the rig did not build the ramp "
                   "and this scene's grade is unverifiable.")
    else:
        vals = sorted(float(kp.co[1]) for kp in fc.keyframe_points)
        lo, hi = vals[0], vals[-1]
        ev = float(fc.evaluate(total_frames))
        print("   ramp interior    rig %+.4f       film %+.4f" % (lo, interior))
        print("   ramp daylight    rig %+.4f       film %+.4f" % (hi, film))
        print("   ramp @ frame %-4d rig %+.4f       film %+.4f"
              % (total_frames, ev, film))
        if abs(hi - film) > GRADE_TOL_STOPS:
            bad.append("the exposure ramp's DAYLIGHT end is %+.4f; the film's "
                       "is %+.4f, from %s. That is %+.4f stops off. The ramp "
                       "is a delta from the scene's exposure at the moment "
                       "build_camera_rig runs, so this means the grade was not "
                       "applied before the rig was built."
                       % (hi, film, src, hi - film))
        if abs(lo - (interior)) > GRADE_TOL_STOPS:
            bad.append("the exposure ramp's INTERIOR end is %+.4f; the film's "
                       "is %+.4f = FILM_EXPOSURE %+.3f - INTERIOR_STOPS %.3f, "
                       "both from world/film_exposure.py. That is %+.4f stops "
                       "off." % (lo, interior, film, FX.INTERIOR_STOPS,
                                 lo - interior))
        if abs(ev - film) > GRADE_TOL_STOPS:
            bad.append("the exposure ramp evaluates to %+.4f on the last frame "
                       "(%d); the film's daylight grade is %+.4f, from %s."
                       % (ev, total_frames, film, src))

    cy = getattr(scene, "cycles", None)
    cfe = getattr(cy, "film_exposure", 1.0) if cy else 1.0
    print("   cycles.film_exposure rig %.4f       expected 1.0 (neutral; the "
          "film grades in view_settings, not here)" % cfe)
    if abs(float(cfe) - 1.0) > 1e-4:
        bad.append("cycles.film_exposure is %.4f, not 1.0. That is a LINEAR "
                   "multiplier applied before the view transform, so it is a "
                   "second exposure the film does not know about: %+.4f stops "
                   "on top of view_settings.exposure."
                   % (cfe, math.log2(max(float(cfe), 1e-12))))

    ng = getattr(scene, "compositing_node_group", None)
    if ng is None and getattr(scene, "use_nodes", False):
        ng = getattr(scene, "node_tree", None)
    hits = [n for n in (getattr(ng, "nodes", []) or [])
            if n.bl_idname == "CompositorNodeExposure"
            or "exposure" in n.bl_idname.lower()
            or "exposure" in (n.name or "").lower()]
    print("   compositor exposure nodes  %d" % len(hits))
    for n in hits:
        v = None
        for inp in n.inputs:
            if inp.name.lower() == "exposure":
                v = float(inp.default_value)
        if v is None or abs(v) > 1e-6:
            bad.append("the compositor carries an exposure node %r (%s) set to "
                       "%s. That is a third grade on top of "
                       "view_settings.exposure and the film has only one."
                       % (n.name, n.bl_idname,
                          "%+.4f" % v if v is not None else "an unread value"))

    if bad:
        msg = ["GRADE MISMATCH — this verify rig would render a picture that "
               "is not the film's. Refusing to hand it to anyone.",
               "  the film's grade  : exposure %+.3f, view_transform %r, "
               "look %r" % (film, FX.VIEW_TRANSFORM, FX.VIEW_LOOK),
               "  it comes from     : %s" % src,
               "  NOT -3.048        : that is world_contract."
               "REFERENCE_EXPOSURE_EXTERIOR, DERIVED not measured, and "
               "refuted — it over-exposes by 0.586 stops (film_exposure.py, "
               "'WHICH ONE WAS RIGHT')."]
        for b in bad:
            msg.append("  FAIL " + b)
        print(">> STAGE RESULT: VERIFY_GRADE_FAIL")
        raise RuntimeError("\n".join(msg))
    print(">> STAGE RESULT: VERIFY_GRADE_MATCHES_FILM")
    return True


def _diagnose(found, film):
    """Name the wrong number if it is one of the two known wrong numbers."""
    if abs(found - FX.CONTRACT_EXPOSURE) <= GRADE_TOL_STOPS:
        return ("That is world_contract.REFERENCE_EXPOSURE_EXTERIOR, which is "
                "DERIVED, not measured, and is refuted: it over-exposes by "
                "0.586 stops.")
    if abs(found) <= GRADE_TOL_STOPS:
        return ("That is no exposure at all — the blend's default. It is %.3f "
                "stops over the film." % (-film))
    return ""


def add_car_proxy(sheet, car, W, total_frames):
    """A box the size of the car, keyed to the telemetry, on every frame."""
    me = bpy.data.meshes.new("CARPROXY_mesh")
    hx, hy, hz = CAR_LEN / 2.0, CAR_HALF_W, CAR_TOP_Z
    verts = [(sx * hx, sy * hy, 0.0 if sz < 0 else hz)
             for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    # index order above is (x,y,z) nested; build faces from it explicitly
    v = {(sx, sy, sz): i for i, (sx, sy, sz) in enumerate(
        [(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])}
    faces = []
    for a, b, c, d in (((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1)),
                       ((-1, -1, 1), (-1, 1, 1), (1, 1, 1), (1, -1, 1)),
                       ((-1, -1, -1), (-1, -1, 1), (1, -1, 1), (1, -1, -1)),
                       ((-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)),
                       ((-1, -1, -1), (-1, 1, -1), (-1, 1, 1), (-1, -1, 1)),
                       ((1, -1, -1), (1, -1, 1), (1, 1, 1), (1, 1, -1))):
        faces.append([v[a], v[b], v[c], v[d]])
    me.from_pydata(verts, [], faces)
    me.update()

    mat = bpy.data.materials.new("CARPROXY_mat")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.15, 0.02, 1.0)
    em.inputs["Strength"].default_value = 45.0
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    me.materials.append(mat)

    ob = bpy.data.objects.new("CARPROXY", me)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_mode = "XYZ"
    for f in range(1, total_frames + 1):
        p, h, _v = car.state(max(W[f], 0.0))
        ob.location = Vector(p)
        ob.rotation_euler = (0.0, 0.0, h)
        ob.keyframe_insert("location", frame=f)
        ob.keyframe_insert("rotation_euler", frame=f)
    for fc in ob.animation_data.action.layers[0].strips[0].channelbags[0].fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    print(f">> CARPROXY: {CAR_LEN:.3f} x {2 * CAR_HALF_W:.3f} x {CAR_TOP_Z:.3f} m, "
          f"emissive, keyed on all {total_frames} frames from the telemetry")
    return ob


def main():
    a = parse_args()
    import json
    sheet = json.load(open(a.sheet))
    spec = json.load(open(a.spec))
    total = int(sheet["total_frames"])
    scales, _ = FT.build_time_map(sheet, total)
    W = FT.world_time_table(scales, total)
    car = Car(a.telemetry, spec)

    if not a.no_proxy:
        add_car_proxy(sheet, car, W, total)

    # THE GRADE, BEFORE THE RIG. build_camera_rig's exposure ramp is a delta
    # from whatever it finds on the scene, so the film's daylight exposure has
    # to be on the scene already or the ramp is keyed off a stale number — the
    # +0.000 that made every verify frame 3.628 stops over.
    apply_film_grade(bpy.context.scene,
                     break_exposure=a.control_break_exposure,
                     break_view_transform=a.control_break_view_transform)

    # Build the rig with the real thing, not a copy of it.
    spec_mod = importlib.util.spec_from_file_location(
        "build_camera_rig", os.path.join(R2, "anim/build_camera_rig.py"))
    mod = importlib.util.module_from_spec(spec_mod)
    sys.argv = ["blender", "--", "--sheet", a.sheet, "--telemetry", a.telemetry,
                "--spec", a.spec, "--out", a.out,
                "--shutter-mode", a.shutter_mode]
    spec_mod.loader.exec_module(mod)
    mod.main()

    # THE ASSERTION. Measured on the BUILT scene, not on the calls made to get
    # there. build_camera_rig has already saved by now, so a scene that fails
    # this has left a mis-graded blend on disk under a name people trust; it is
    # deleted, because the whole defect this fixes is agents believing a picture
    # that was lying to them.
    try:
        assert_grade_is_the_films(bpy.context.scene, total)
    except RuntimeError:
        if os.path.exists(a.out):
            os.remove(a.out)
            print(">> removed %s: it does not carry the film's grade and must "
                  "not be inspected as if it did." % a.out)
        raise


if __name__ == "__main__":
    # Blender 5.2 running `-b -P` SWALLOWS an unhandled exception from a script:
    # no traceback on stdout or stderr, and `blender` still exits 0. MEASURED —
    # the first positive-control run of the grade assertion below raised, and
    # the shell saw success and no message. An assertion whose failure is
    # invisible and exits 0 is not an assertion, so the message and the non-zero
    # status are printed and set here, by hand.
    try:
        main()
    except Exception:                                   # noqa: BLE001
        import traceback
        sys.stdout.flush()      # stdout is block-buffered into a log file and
        sys.stderr.flush()      # stderr is not; without this the failure lands
        traceback.print_exc()   # at the TOP of the log, above its own evidence.
        sys.stderr.flush()
        sys.exit(1)
