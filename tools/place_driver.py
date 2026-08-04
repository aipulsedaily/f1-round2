"""place_driver -- put `world/items/driver_figure.py` into the car's cockpit.

R2-241.  The car is round-1 geometry and `/home/zany/opus5-car-render` is
READ-ONLY, so nothing here modifies the car.  It ADDS `DRV_*` objects to the
`CAR` collection of a COPY of `world/car_anim.blend` and writes
`world/car_anim_driver.blend`.  `tools/build_film_scene.py` already takes the
car blend as `--car`, so the film picks the driver up with

    tools/build_film_scene.py --car world/car_anim_driver.blend ...

and `tools/build_film_scene.py` itself is untouched (hard constraint 7).

WHY NOT THE WORLD PLACEMENT STAGE
---------------------------------
R2-182's `world/items/` -> `assemble.py` stage places items into the WORLD.
The driver does not go into the world; he goes into the car, and the car is
appended into the film from `world/car_anim.blend` as its own `CAR` collection
(`tools/build_film_scene.py` line ~244).  A driver placed by the world stage
would sit at a fixed world point while the car drove away from him.  This is
therefore a SECOND, car-local placement path and not a duplicate of R2-182.

THE FIT IS MEASURED OFF THE CAR, NOT ASSUMED
--------------------------------------------
Every number below is read out of the car mesh at an ASSEMBLED frame.  Frame 1
is NOT assembled -- the beat-1 explode holds the cockpit interior 2.443 m above
its home until about frame 500 -- and a fit solved at frame 1 lands the driver
in mid-air.  That is the first thing this file checks.

`driver_figure.PACKAGE['round1_note']` already recorded that round 1's cockpit
tub is longitudinally right and VERTICALLY COMPRESSED: it offers 0.249 m of
hip-to-headrest rise where a 1.78 m man needs 0.552 m.  It recommended H-point
(0.200, 0.000, 0.520) in the car_anim world frame and then said the CAR would
have to move.  The car cannot move.  So the H-point is kept and the DRIVER is
re-solved onto the car's real wheel instead: `WHEEL_C` is overridden with the
measured `SW_Shell` centre and `WHEEL_TILT_DEG` with the measured lean.  The
hip then sits ~0.23 m below the seat pan, i.e. inside the monocoque, which is
invisible from outside and is checked as such by the silhouette gate rather
than asserted.

USE
    blender -b --factory-startup -noaudio -P tools/place_driver.py -- \
        --out world/car_anim_driver.blend
"""

import argparse
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "world"), os.path.join(R2, "world", "items"),
           os.path.join(R2, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FIT_FRAME = 1200          # any frame after the beat-1 explode has landed
EXPLODE_LANDED = 500      # measured: cockpit interior is home by here


def log(m):
    sys.stdout.write("[place_driver] %s\n" % m)
    sys.stdout.flush()


# --------------------------------------------------------------------------- #
#  1.  measure the car                                                          #
# --------------------------------------------------------------------------- #

def _local_points(ob, dg, Minv):
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    M = Minv @ ob.matrix_world
    P = np.array([list(M @ v.co) for v in me.vertices], dtype=np.float64)
    ev.to_mesh_clear()
    return P


def measure_car(frame=FIT_FRAME):
    """Cockpit geometry in CAR_ROOT-LOCAL metres, read off the mesh."""
    sc = bpy.context.scene
    root = bpy.data.objects.get("CAR_ROOT")
    if root is None:
        raise SystemExit("no CAR_ROOT in this blend")
    sc.frame_set(frame)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    Minv = root.matrix_world.inverted()

    def P(name):
        ob = bpy.data.objects.get(name)
        if ob is None:
            raise SystemExit("the car has no %r -- refusing to guess its cockpit"
                             % name)
        return _local_points(ob, dg, Minv)

    m = {}
    sw = P("SW_Shell")
    c = sw.mean(axis=0)
    n = np.linalg.svd(sw - c)[2][2]
    if n[0] < 0:
        n = -n
    m["wheel_centre"] = c
    m["wheel_normal"] = n
    # the wheel plane's lean from vertical == the normal's rise above horizontal
    m["wheel_lean_deg"] = -math.degrees(math.atan2(n[2], n[0]))
    gl = P("SW_GripL").mean(axis=0)
    m["grip_l"] = gl
    d = gl - c
    m["grip_offset"] = float(np.linalg.norm(d - np.dot(d, n) * n))

    for nm in ("CI_seal", "CI_seatpad", "CI_headrest", "CI_sidehead",
               "CI_pedals", "CI_liner", "halo_assembly_HoopTube"):
        Q = P(nm)
        m[nm] = (Q.min(axis=0), Q.max(axis=0))

    # is this frame actually assembled?  the explode offsets every interior
    # part together, so seat-vs-chassis separation is the tell.
    seat = bpy.data.objects.get("CI_seat")
    off = (Minv @ seat.matrix_world).translation
    m["interior_offset_at_fit_frame"] = float(Vector(off).length)
    if m["interior_offset_at_fit_frame"] > 0.02:
        raise SystemExit(
            "frame %d is MID-EXPLODE: the cockpit interior is %.3f m off its "
            "home. Solving the fit here puts the driver in mid-air."
            % (frame, m["interior_offset_at_fit_frame"]))
    return m


# --------------------------------------------------------------------------- #
#  2.  solve the H-point                                                        #
# --------------------------------------------------------------------------- #

def solve_hpoint(m, DF):
    """-> (H, wheel_c_rel, lean_deg, report).  All CAR_ROOT-local.

    x  from the wheel: the module's own `WHEEL_C.x` measured back from the car's
       real steering wheel, so the reach is right by construction.
    z  the module's published `round1_h_point_recommendation`, which is stated
       in the car_anim WORLD frame (CAR_ROOT sits at z = 0.340 there).  It is
       corroborated independently below against the halo and the pedal box; if
       either check fails this raises rather than shipping a guess.
    """
    rec = np.array(DF.PACKAGE["round1_h_point_recommendation"], float)
    root_z = 0.340        # CAR_ROOT's rest height in world/car_anim.blend
    H = np.array([m["wheel_centre"][0] - DF.WHEEL_C[0],
                  0.0,
                  rec[2] - root_z])

    crown = H[2] + DF.PACKAGE["hip_to_helmet_crown_m"]
    rim = float(m["CI_seal"][1][2])
    halo_top = float(m["halo_assembly_HoopTube"][1][2])
    ankle_z = H[2] + 0.215                      # anchors['ankle_l'].o.z
    ped_lo, ped_hi = float(m["CI_pedals"][0][2]), float(m["CI_pedals"][1][2])
    ped_x_lo, ped_x_hi = float(m["CI_pedals"][0][0]), float(m["CI_pedals"][1][0])
    ankle_x = H[0] + 0.755

    rep = {
        "H_local": H.tolist(),
        "helmet_crown_z": crown,
        "cockpit_rim_z": rim,
        "crown_above_rim_m": crown - rim,
        "halo_apex_z": halo_top,
        "crown_below_halo_apex_m": halo_top - crown,
        "ankle_z": ankle_z, "pedal_box_z": [ped_lo, ped_hi],
        "ankle_x": ankle_x, "pedal_box_x": [ped_x_lo, ped_x_hi],
        "seat_pan_z": float(m["CI_seatpad"][0][2]),
        "hip_below_seat_pan_m": float(m["CI_seatpad"][0][2]) - H[2],
    }
    fail = []
    if not (0.08 <= crown - rim <= 0.22):
        fail.append("helmet crown %.3f m above the cockpit rim -- outside "
                    "0.08..0.22; the silhouette will not read" % (crown - rim))
    if crown > halo_top + 0.01:
        fail.append("helmet crown %.4f is above the halo apex %.4f -- the head "
                    "is outside the survival cell" % (crown, halo_top))
    if not (ped_lo <= ankle_z <= ped_hi):
        fail.append("ankle z %.4f is outside the pedal box %.4f..%.4f"
                    % (ankle_z, ped_lo, ped_hi))
    if not (ped_x_lo - 0.05 <= ankle_x <= ped_x_hi + 0.05):
        fail.append("ankle x %.4f is outside the pedal box %.4f..%.4f"
                    % (ankle_x, ped_x_lo, ped_x_hi))
    rep["fit_failures"] = fail

    wheel_rel = m["wheel_centre"] - H
    return H, wheel_rel, m["wheel_lean_deg"], rep


# --------------------------------------------------------------------------- #
#  3.  install                                                                  #
# --------------------------------------------------------------------------- #

def share_action(src, dst):
    """Give `dst` `src`'s action, on Blender 5.x's slotted-action API.

    Returns the slot identifier used, or None.  The CALLER MUST VERIFY by
    evaluating both objects: a slot that silently fails to bind leaves `dst`
    at rest, which is exactly the failure this whole file exists to avoid.
    """
    ad_s = src.animation_data
    if ad_s is None or ad_s.action is None:
        return None
    # A COPY, NEVER THE SHARED DATABLOCK.  R2-245.  The first cut assigned
    # CI_seat's own action to the empty.  Anything later written through the
    # empty -- `key_appearance` inserted hide_render keys and then forced every
    # keyframe in the action to CONSTANT -- landed in the CAR's action, on the
    # CAR's seat, in a blend the car is supposed to pass through untouched.
    # MEASURED: `verify_install`'s explode-offset control went from 2.518 m to
    # 104.398 m, i.e. the seat's assembly flight had been rewritten.  The car
    # is READ-ONLY; a copy costs one datablock.
    act = ad_s.action.copy()
    act.name = "DRV_Install_" + ad_s.action.name
    ad = dst.animation_data_create()
    ad.action = act
    slot = None
    try:
        cands = list(ad.action_suitable_slots)
    except AttributeError:
        cands = []
    if cands:
        want = getattr(ad_s, "action_slot", None)
        for s in cands:
            if want is not None and s.identifier == getattr(want, "identifier", None):
                slot = s
                break
        if slot is None:
            slot = cands[0]
        ad.action_slot = slot
    return getattr(slot, "identifier", None)



def figure_offscreen(H, path_json, car_json, frames, margin_px=40.0):
    """Is the WHOLE figure outside the 4K frame at every one of `frames`?

    The driver may not simply pop into an occupied frame.  This projects a
    12-point hull of the figure -- helmet crown, shoulders, wrists, knees,
    ankles, pelvis -- through the film's own camera at the car's own transform
    and returns the frames at which any of them is on screen.
    """
    import numpy as _np
    cp = json.load(open(path_json))["path"]
    car = json.load(open(car_json))["samples"]
    RX, RY, SEN = 3840.0, 2160.0, 36.0
    off = _np.array([
        (-0.2254, -0.0483, 0.7134), (-0.2254, -0.0483, 0.5585),
        (-0.2504, 0.1518, 0.3455), (-0.1665, -0.2226, 0.3703),
        (0.2652, 0.2027, 0.3100), (0.2706, -0.2028, 0.2969),
        (0.3452, 0.2073, 0.2270), (0.3473, -0.2055, 0.2247),
        (0.7550, 0.0750, 0.2150), (0.7576, -0.0750, 0.2128),
        (-0.3358, -0.0172, 0.2527), (0.1180, 0.0000, -0.1280)], float)
    P = off + _np.asarray(H, float)
    onscreen = []
    for f in frames:
        c = cp[f - 1]
        p = _np.array(c["p"]); w, x, y, z = c["q"]
        R = _np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                       [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                       [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
        s = car[f - 1]
        loc = _np.array(s["loc"]); rx, ry, rz = s["rot"]
        cx, cy, cz = math.cos(rx), math.cos(ry), math.cos(rz)
        sx, sy, sz = math.sin(rx), math.sin(ry), math.sin(rz)
        M = (_np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
             @ _np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
             @ _np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]))
        W = (M @ P.T).T + loc
        d = W - p
        dep = -(d @ R[:, 2])
        ok = dep > 0.02
        if not ok.any():
            continue
        S = RX * float(c["lens"]) / SEN
        px = RX / 2 + S * (d[ok] @ R[:, 0]) / dep[ok]
        py = RY / 2 + S * (d[ok] @ R[:, 1]) / dep[ok]
        if ((px >= -margin_px) & (px < RX + margin_px)
                & (py >= -margin_px) & (py < RY + margin_px)).any():
            onscreen.append(int(f))
    return onscreen


def key_appearance(objs, appear, hidden_from=1):
    """Hide every DRV_* object until `appear`, with CONSTANT interpolation."""
    for o in objs:
        for attr in ("hide_render", "hide_viewport"):
            setattr(o, attr, True)
            o.keyframe_insert(attr, frame=hidden_from)
            o.keyframe_insert(attr, frame=appear - 1)
            setattr(o, attr, False)
            o.keyframe_insert(attr, frame=appear)
        ad = o.animation_data
        act = ad.action if ad else None
        if act is None:
            continue
        for layer in getattr(act, "layers", []):
            for strip in getattr(layer, "strips", []):
                for cb in getattr(strip, "channelbags", []):
                    for fc in cb.fcurves:
                        for k in fc.keyframe_points:
                            k.interpolation = 'CONSTANT'


CAR_WITNESS = ("CI_seat", "CI_seatpad", "CI_headrest", "SW_Shell", "CI_liner",
               "MB_chassis_cockpit", "halo_assembly_HoopTube")
CAR_WITNESS_FRAMES = (1, 120, 300, 420, 500, 580, 792, 1200, 2632, 2978)


def car_witness():
    """Sample the car's own animation. Compared before and after everything
    this file does, because the car is READ-ONLY and `car_anim_driver.blend`
    must differ from `car_anim.blend` by ADDITIONS only."""
    sc = bpy.context.scene
    root = bpy.data.objects["CAR_ROOT"]
    out = {}
    for f in CAR_WITNESS_FRAMES:
        sc.frame_set(f)
        bpy.context.view_layer.update()
        Minv = root.matrix_world.inverted()
        for n in CAR_WITNESS:
            o = bpy.data.objects.get(n)
            if o is None:
                continue
            M = Minv @ o.matrix_world
            out["%s@%d" % (n, f)] = ([round(v, 9) for v in M.translation]
                                     + [round(v, 9) for v in M.to_euler()]
                                     + [bool(o.hide_render)])
    return out


def install(drv_objs, root, car_coll, install_src="CI_seat"):
    """Parent DRV_* under an empty that rides the seat's own assembly path.

    THE PARENT INVERSE MUST NOT BE SAMPLED FROM A LIVE FRAME.  The first cut
    set `e.matrix_parent_inverse = root.matrix_world.inverted()` while the
    scene was still on the fit frame, where CAR_ROOT is 400 m down the circuit;
    that inverse was then baked in and the driver rode 408 m behind the car for
    the whole film.  `verify_install` caught it.  The empty copies the SEAT's
    own parent inverse instead, so its local-to-CAR_ROOT is the seat's by
    construction, and the DRV_* objects hang off it with an IDENTITY inverse so
    their built world matrices -- which `build(place=...)` already left in
    CAR_ROOT-local coordinates -- pass straight through.
    """
    src = bpy.data.objects.get(install_src)
    if src is None:
        raise SystemExit("no %r to ride" % install_src)
    e = bpy.data.objects.new("DRV_Install", None)
    e.empty_display_type = 'PLAIN_AXES'
    e.empty_display_size = 0.25
    car_coll.objects.link(e)
    e.parent = root
    e.matrix_parent_inverse = src.matrix_parent_inverse.copy()
    e.rotation_mode = src.rotation_mode
    slot = share_action(src, e)
    log("DRV_Install rides %s's action (slot %r)" % (install_src, slot))

    for o in drv_objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        car_coll.objects.link(o)
        o.parent = e
        o.matrix_parent_inverse = Matrix.Identity(4)
    return e


def verify_install(e, install_src, frames=(1, 300, 600, 1200, 2632)):
    """CONTROL: the empty must track the seat at EVERY frame, not just rest.

    Both controls in one test:  the POSITIVE one is that the two agree at the
    landed frames; the NEGATIVE one is that at frame 1 they are BOTH 2.443 m
    from home -- if the action failed to bind, the empty reads 0.000 there
    while the seat reads 2.443, and the test fails loudly instead of shipping
    a driver who never leaves the cockpit while the car explodes around him.
    """
    sc = bpy.context.scene
    root = bpy.data.objects.get("CAR_ROOT")
    src = bpy.data.objects.get(install_src)
    worst = 0.0
    spread = 0.0
    rows = []
    for f in frames:
        sc.frame_set(f)
        bpy.context.view_layer.update()
        Minv = root.matrix_world.inverted()
        a = (Minv @ e.matrix_world).translation
        b = (Minv @ src.matrix_world).translation
        d = (a - b).length
        worst = max(worst, d)
        spread = max(spread, b.length)
        rows.append((f, [round(v, 4) for v in a], [round(v, 4) for v in b],
                     round(d, 5)))
    for r in rows:
        log("  install f%-5d empty %s  %s %s  delta %.5f m" %
            (r[0], r[1], install_src, r[2], r[3]))
    return worst, spread, rows


# --------------------------------------------------------------------------- #

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(R2, "world/car_anim_driver.blend"))
    ap.add_argument("--pose", default="straight")
    ap.add_argument("--uid", type=int, default=0)
    ap.add_argument("--report", default=os.path.join(R2, "docs/driver_placement.json"))
    ap.add_argument("--fit-frame", type=int, default=FIT_FRAME)
    ap.add_argument("--appear", type=int, default=580,
                    help="frame the driver becomes visible. Must sit inside a "
                         "measured off-screen run AFTER the cockpit interior "
                         "has landed, or this refuses: the driver may not pop "
                         "into an occupied frame.")
    ap.add_argument("--allow-fit-failure", action="store_true",
                    help="downgrade the mesh checks to warnings and save anyway "
                         "-- for diagnosing a failure, never for shipping")
    ap.add_argument("--crown-correction", action="store_true", default=True,
                    help="after building, translate the figure so the MEASURED "
                         "helmet crown lands where the fit predicted")
    ap.add_argument("--no-crown-correction", dest="crown_correction",
                    action="store_false")
    ap.add_argument("--dry-fit", action="store_true",
                    help="measure and solve, build nothing, save nothing")
    a = ap.parse_args(argv)

    import driver_figure as DF

    before = car_witness()
    log("car witness: %d samples of %d objects at %d frames"
        % (len(before), len(CAR_WITNESS), len(CAR_WITNESS_FRAMES)))

    m = measure_car(a.fit_frame)
    log("MEASURED at frame %d (interior %.4f m off home -> assembled)"
        % (a.fit_frame, m["interior_offset_at_fit_frame"]))
    log("  steering wheel centre  %s" % np.round(m["wheel_centre"], 4).tolist())
    log("  steering wheel lean    %.2f deg   (module WHEEL_TILT_DEG %.1f)"
        % (m["wheel_lean_deg"], DF.WHEEL_TILT_DEG))
    log("  grip offset            %.4f m     (module WHEEL_GRIP_OFF %.4f)"
        % (m["grip_offset"], DF.WHEEL_GRIP_OFF))
    log("  cockpit rim z          %.4f   halo apex z %.4f"
        % (m["CI_seal"][1][2], m["halo_assembly_HoopTube"][1][2]))

    H, wheel_rel, lean, rep = solve_hpoint(m, DF)
    log("SOLVED H-point (CAR_ROOT-local) %s" % np.round(H, 4).tolist())
    for k in ("crown_above_rim_m", "crown_below_halo_apex_m",
              "hip_below_seat_pan_m"):
        log("  %-26s %+.4f m" % (k, rep[k]))
    log("  ankle z %.4f in pedal box %.4f..%.4f ; x %.4f in %.4f..%.4f"
        % (rep["ankle_z"], rep["pedal_box_z"][0], rep["pedal_box_z"][1],
           rep["ankle_x"], rep["pedal_box_x"][0], rep["pedal_box_x"][1]))
    if rep["fit_failures"]:
        for f in rep["fit_failures"]:
            log("  FIT FAILURE: %s" % f)
        print("STAGE RESULT: FAIL -- fit rejected")
        return 1
    log("  fit accepted on all four checks")

    # --- re-solve the driver onto the car's REAL wheel ---------------------
    old_c, old_t = DF.WHEEL_C.copy(), DF.WHEEL_TILT_DEG
    DF.WHEEL_C = np.array(wheel_rel, dtype=float)
    DF.WHEEL_TILT_DEG = float(lean)
    DF.WHEEL_GRIP_OFF = float(m["grip_offset"])
    log("OVERRIDE WHEEL_C   %s -> %s  (%.1f mm)" %
        (np.round(old_c, 4).tolist(), np.round(DF.WHEEL_C, 4).tolist(),
         1000 * np.linalg.norm(DF.WHEEL_C - old_c)))
    log("OVERRIDE WHEEL_TILT_DEG %.2f -> %.2f" % (old_t, DF.WHEEL_TILT_DEG))
    rep["wheel_c_override"] = DF.WHEEL_C.tolist()
    rep["wheel_c_module_default"] = old_c.tolist()
    rep["wheel_tilt_deg"] = DF.WHEEL_TILT_DEG
    rep["wheel_grip_off"] = DF.WHEEL_GRIP_OFF
    rep["measured"] = {k: (np.asarray(v).tolist() if isinstance(v, (np.ndarray, tuple))
                           else v) for k, v in m.items()}
    rep["pose"] = a.pose
    rep["fit_frame"] = a.fit_frame

    if a.dry_fit:
        json.dump(rep, open(a.report, "w"), indent=1, default=float)
        print("STAGE RESULT: OK (dry fit, nothing built)")
        return 0

    place = np.eye(4)
    place[:3, 3] = H
    d = DF.build(coll_name="DRV_Driver", pose=a.pose, uid=a.uid, place=place)
    log("built %d objects, %d triangles in %.1f s"
        % (d.stats["objects"], d.stats["triangles"], d.stats["seconds"]))
    rep["stats"] = d.stats

    root = bpy.data.objects["CAR_ROOT"]
    car = bpy.data.collections.get("CAR")
    if car is None:
        raise SystemExit("this blend has no CAR collection")
    e = install(d.objs, root, car)

    # --- the fit was a prediction; measure it on the EMITTED MESH ----------
    sc = bpy.context.scene
    sc.frame_set(a.fit_frame)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    Minv = root.matrix_world.inverted()
    helm = bpy.data.objects.get("DRV_Helmet")
    P = _local_points(helm, dg, Minv)
    got_crown = float(P[:, 2].max())
    log("MESH CHECK  helmet crown predicted %.4f, measured on DRV_Helmet %.4f "
        "(delta %+.1f mm)" % (rep["helmet_crown_z"], got_crown,
                              1000 * (got_crown - rep["helmet_crown_z"])))
    rep["helmet_crown_measured_z"] = got_crown
    rep["helmet_crown_delta_mm"] = 1000 * (got_crown - rep["helmet_crown_z"])
    rep["helmet_bounds_local"] = [P.min(0).tolist(), P.max(0).tolist()]
    if a.crown_correction and abs(got_crown - rep["helmet_crown_z"]) > 0.002:
        dz = rep["helmet_crown_z"] - got_crown
        log("CROWN CORRECTION: PACKAGE['hip_to_helmet_crown_m'] understates the "
            "emitted helmet by %.1f mm; translating the figure %+.1f mm in z so "
            "the crown lands on the solved height" % (-1000 * dz, 1000 * dz))
        for o in d.objs:
            o.matrix_basis = Matrix.Translation(Vector((0.0, 0.0, dz))) @ o.matrix_basis
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        P = _local_points(helm, dg, Minv)
        got_crown = float(P[:, 2].max())
        rep["crown_correction_mm"] = 1000 * dz
        rep["helmet_crown_measured_z"] = got_crown
        rep["helmet_crown_delta_mm"] = 1000 * (got_crown - rep["helmet_crown_z"])
        rep["helmet_bounds_local"] = [P.min(0).tolist(), P.max(0).tolist()]
        log("  crown now %.4f (delta %+.2f mm)"
            % (got_crown, 1000 * (got_crown - rep["helmet_crown_z"])))
    if abs(got_crown - rep["helmet_crown_z"]) > 0.030:
        print("STAGE RESULT: FAIL -- the emitted helmet is %+.1f mm from where "
              "the fit put it; the placement and the geometry disagree"
              % (1000 * (got_crown - rep["helmet_crown_z"])))
        return 1
    # gloves must actually reach the car's own wheel grips.  EXACT, via a
    # KD-tree over every grip vertex -- the first cut subsampled 4000 of each
    # and could not tell a 5 mm contact from a 100 mm miss.
    # where the module THINKS the hands are, in CAR_ROOT-local
    try:
        A = d.anchors
        Ht = np.array(H, float)
        for k in ("wheel", "grip_l", "grip_r", "wrist_l", "wrist_r"):
            if k in A:
                o = np.array(A[k]["o"] if isinstance(A[k], dict) else A[k].o, float)
                log("  ANCHOR %-8s driver-frame %s  -> CAR_ROOT-local %s"
                    % (k, np.round(o, 4).tolist(), np.round(o + Ht, 4).tolist()))
        rep["anchors_local"] = {k: (np.array(A[k]["o"] if isinstance(A[k], dict)
                                             else A[k].o, float) + Ht).tolist()
                                for k in A}
    except Exception as _e:
        log("  (anchors unavailable: %s)" % _e)
    for n in ("SW_GripL", "SW_GripR", "SW_Shell"):
        Q = _local_points(bpy.data.objects[n], dg, Minv)
        log("  CAR    %-9s centroid %s" % (n, np.round(Q.mean(0), 4).tolist()))

    from mathutils.kdtree import KDTree
    def nearest(A, B):
        t = KDTree(len(B))
        for i, p in enumerate(B):
            t.insert(Vector(p), i)
        t.balance()
        return min(t.find(Vector(p))[2] for p in A)
    grips = {n: _local_points(bpy.data.objects[n], dg, Minv)
             for n in ("SW_GripL", "SW_GripR")}
    gaps = {}
    for lab, gob in (("L", "DRV_Glove_L"), ("R", "DRV_Glove_R")):
        _o = bpy.data.objects[gob]
        _ev = _o.evaluated_get(dg); _me = _ev.to_mesh()
        _raw = np.array([list(v.co) for v in _me.vertices]); _ev.to_mesh_clear()
        log("  DEBUG %s raw-centroid %s  basis_t %s  basis_rot %s  mods %s"
            % (gob, np.round(_raw.mean(0), 4).tolist(),
               [round(v, 4) for v in _o.matrix_basis.translation],
               [round(v, 4) for v in _o.matrix_basis.to_euler()],
               [m.type for m in _o.modifiers]))
        G = _local_points(_o, dg, Minv)
        best = min((nearest(G, B), n) for n, B in grips.items())
        gaps[lab] = best
        log("MESH CHECK  %s: %d verts, centroid %s -> nearest %s %.1f mm "
            "(that grip's centroid %s)"
            % (gob, len(G), np.round(G.mean(0), 4).tolist(), best[1],
               1000 * best[0], np.round(grips[best[1]].mean(0), 4).tolist()))
    rep["glove_grip_gap_mm"] = {k: [1000 * v[0], v[1]] for k, v in gaps.items()}
    worst_gap = max(v[0] for v in gaps.values())
    if worst_gap > 0.020 and not a.allow_fit_failure:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out) + ".reject.blend",
                                    compress=False, copy=True)
        log("saved the rejected artefact to %s.reject.blend for inspection" % a.out)
        print("STAGE RESULT: FAIL -- a glove is %.1f mm off the wheel; the "
              "hands are not on the car's own steering wheel" % (1000 * worst_gap))
        return 1

    # --- when he appears --------------------------------------------------
    win = list(range(a.appear - 8, a.appear + 9))
    on = figure_offscreen(H, os.path.join(R2, "render/film14_path.json"),
                          os.path.join(R2, "world/car_anim_car.json"), win)
    log("APPEARANCE frame %d; figure on screen at %d of the %d frames %d..%d"
        % (a.appear, len(on), len(win), win[0], win[-1]))
    if on:
        print("STAGE RESULT: FAIL -- the driver would pop into an occupied "
              "frame; he is on screen at %s" % on[:12])
        return 1
    if a.appear <= EXPLODE_LANDED:
        print("STAGE RESULT: FAIL -- appear frame %d is before the cockpit "
              "interior lands (%d)" % (a.appear, EXPLODE_LANDED))
        return 1
    key_appearance(d.objs, a.appear)   # NOT the empty: see share_action
    sc = bpy.context.scene
    seen = {}
    for f in (1, 300, a.appear - 1, a.appear, 1200, 2632):
        sc.frame_set(f)
        bpy.context.view_layer.update()
        seen[f] = [bool(o.hide_render) for o in d.objs]
    for f in sorted(seen):
        log("  visibility f%-5d hidden=%s" % (f, all(seen[f])))
    if not (all(seen[1]) and all(seen[a.appear - 1])
            and not any(seen[a.appear]) and not any(seen[2632])):
        print("STAGE RESULT: FAIL -- the visibility keys do not read back")
        return 1
    rep["appear_frame"] = a.appear
    rep["appear_offscreen_window"] = [win[0], win[-1]]

    worst, spread, rows = verify_install(e, "CI_seat")
    rep["install_worst_delta_m"] = worst
    rep["install_max_offset_m"] = spread
    rep["install_rows"] = rows
    log("install tracking: worst delta %.5f m, max explode offset seen %.4f m"
        % (worst, spread))
    if worst > 1e-4:
        print("STAGE RESULT: FAIL -- DRV_Install does not track CI_seat")
        return 1
    if spread < 1.0:
        print("STAGE RESULT: FAIL -- the seat never leaves home in the sampled "
              "frames, so the tracking test proved nothing (negative control)")
        return 1

    # tidy: the DRV_Driver collection was created by build(); drop the now
    # empty scene-level link so CAR owns the objects.
    dc = bpy.data.collections.get("DRV_Driver")
    if dc is not None and len(dc.objects) == 0:
        for p in list(bpy.data.collections) + [bpy.context.scene.collection]:
            if dc.name in [c.name for c in p.children]:
                p.children.unlink(dc)
        bpy.data.collections.remove(dc)

    after = car_witness()
    drift = {k: (before[k], after[k]) for k in before if before[k] != after[k]}
    rep["car_witness_samples"] = len(before)
    rep["car_witness_drift"] = {k: v for k, v in list(drift.items())[:20]}
    log("CAR GUARD: %d of %d witness samples changed" % (len(drift), len(before)))
    if drift:
        for k, (b, af) in list(drift.items())[:8]:
            log("   %s  %s -> %s" % (k, b, af))
        print("STAGE RESULT: FAIL -- this run MOVED the car. The car is "
              "read-only and only additions are allowed.")
        return 1

    bpy.context.scene.frame_set(1)
    names = sorted(o.name for o in car.all_objects if o.name.startswith("DRV_"))
    log("CAR now carries %d DRV_* objects: %s" % (len(names), names))
    rep["objects"] = names

    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out),
                                compress=False, copy=False)
    log("wrote %s (%.1f MB)" % (a.out, os.path.getsize(a.out) / 1e6))
    json.dump(rep, open(a.report, "w"), indent=1, default=float)
    log("wrote %s" % a.report)
    print("STAGE RESULT: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
