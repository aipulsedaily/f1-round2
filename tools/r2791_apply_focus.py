"""Re-author beat 1's FOCUS and APERTURE on an already-built camera rig.

    /opt/blender-5.2.0-linux-x64/blender -b <rig-or-film>.blend --factory-startup \
        -P tools/r2791_apply_focus.py -- --out <out>.blend

Pipeline position: AFTER `anim/build_camera_rig.py`, BEFORE
`tools/build_film_scene.py` bakes the rig into a film scene.

WHY A POST-PASS AND NOT AN EDIT TO build_camera_rig.py
------------------------------------------------------
Because another agent owns that file right now. Beat 1's PACING and FRAMING are
being re-authored in the same window as this fix, and `build_camera_rig.py` is
where the camera path lives -- two agents editing one 1,600-line file is how a
one-shot film acquires a merge conflict at the exact place it can least afford
one. This runs after them, reads what they authored, and writes two channels
they do not touch.

It is also the more robust shape, independently of the collision. This pass reads
the camera's OWN EVALUATED TRANSFORM, frame by frame, out of whatever rig it is
handed. It therefore cannot go stale against a re-timed tour, a re-stationed
corner, or a moved seat schedule: re-run it and the focus is re-derived from the
camera that actually exists. There are no frame numbers in the solution.

WHAT IT WRITES, AND WHAT IT REFUSES TO
--------------------------------------
Writes: `camera.data.dof.focus_distance` and `camera.data.dof.aperture_fstop`,
over frames `--first .. --closeout-1`, plus a `--handoff` ramp back onto the
sheet's own values.

Refuses: everything else. `location`, `rotation_quaternion` and `lens` are
snapshotted before the pass and re-verified after it, and a difference of any
size fails the run rather than shipping a camera this file moved.

Also left alone deliberately: frames from `--closeout` on. `render/film14_path.json`'s
f648-792 is the material a review called the best in the film, it is the range
the R2-451 re-aim was forbidden to move, and ITS FOCUS IS ALREADY CORRECT --
measured error 0.28 m at f700 and 0.02 m at f792 against 0.25-2.34 m over the
tour. A fix has no business in there.

Blender 5.2 exits 0 on an uncaught exception. Judge on STAGE RESULT only.
"""

import json
import os
import sys
import traceback

import bpy
from mathutils import Vector

R2 = os.path.expanduser("~/f1-round2")
sys.path.insert(0, os.path.join(R2, "tools"))
import r2791_beat1_focus as SOLVE                                 # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default


def dof_curves(cam_data):
    ad = cam_data.animation_data
    if not ad:
        return []
    out = []
    for act in [ad.action] + [s.action for t in ad.nla_tracks for s in t.strips]:
        if not act:
            continue
        curves = list(getattr(act, "fcurves", []) or [])
        if not curves:
            for lay in getattr(act, "layers", []) or []:
                for st in getattr(lay, "strips", []) or []:
                    for cb in getattr(st, "channelbags", []) or []:
                        curves.extend(list(cb.fcurves))
        for fc in curves:
            if fc.data_path in ("dof.focus_distance", "dof.aperture_fstop"):
                out.append(fc)
    return out


def snapshot(scene, cam, frames):
    out = {}
    for f in frames:
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        ce = cam.evaluated_get(dg)
        m = ce.matrix_world
        out[f] = (tuple(m.translation), tuple(m.to_quaternion()), ce.data.lens)
    return out


def main():
    out_path = arg("--out")
    cam_name = arg("--cam", "ONER")
    lo = int(arg("--first", "1"))
    closeout = int(arg("--closeout", str(SOLVE.CLOSEOUT_F)))
    handoff = int(arg("--handoff", str(SOLVE.HANDOFF_FRAMES)))
    rack = int(arg("--rack-frames", "9"))
    grid_path = arg("--grid")
    report = arg("--report")

    scene = bpy.context.scene
    cam = bpy.data.objects.get(cam_name)
    if cam is None:
        print("STAGE RESULT R2791_APPLY_FAIL no camera %r" % cam_name)
        return 1
    cd = cam.data
    hi = min(int(arg("--last", "792")), scene.frame_end)

    # ---- read the camera that actually exists, per frame -------------------
    cams, shipped_focus, shipped_fstop = [], {}, {}
    for f in range(lo, hi + 1):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        ce = cam.evaluated_get(dg)
        m = ce.matrix_world
        q = m.to_quaternion()
        cams.append({"f": f,
                     "p": list(m.translation),
                     "fwd": list(q @ Vector((0.0, 0.0, -1.0))),
                     "lens": ce.data.lens})
        shipped_focus[f] = ce.data.dof.focus_distance
        shipped_fstop[f] = ce.data.dof.aperture_fstop
    print(">> read %d frames of camera %s from %s"
          % (len(cams), cam_name, bpy.data.filepath or "<current>"))

    guard_frames = list(range(lo, hi + 1, max(1, (hi - lo) // 40)))
    before = snapshot(scene, cam, guard_frames)

    # ---- solve --------------------------------------------------------------
    sub = bg = None
    if grid_path and os.path.exists(grid_path):
        sub, bg = SOLVE.depth_from_grid(json.load(open(grid_path)))
        print(">> subject/background depth MEASURED from %s (%d/%d frames)"
              % (grid_path, len(sub), len(bg)))
    else:
        print(">> no depth grid given — subject depth from the geometric field "
              "model and the aperture ceiling unbounded by background")
    rows = SOLVE.solve(cams, SOLVE.load_field(), shipped_focus, shipped_fstop,
                       rack_frames=rack, closeout_f=closeout, handoff=handoff,
                       subject_depth=sub, bg_depth=bg)

    # ---- rewrite ONLY the two DOF channels ---------------------------------
    for fc in dof_curves(cd):
        doomed = [kp for kp in fc.keyframe_points if lo <= kp.co[0] < closeout]
        for kp in reversed(doomed):
            fc.keyframe_points.remove(kp)
        print(">> cleared %d key(s) from %s over f%d-%d"
              % (len(doomed), fc.data_path, lo, closeout - 1))

    cd.dof.use_dof = True
    n = 0
    for r in rows:
        if r["f"] >= closeout:
            continue
        cd.dof.focus_distance = float(r["focus_m"])
        cd.dof.keyframe_insert("focus_distance", frame=r["f"])
        cd.dof.aperture_fstop = float(r["fstop"])
        cd.dof.keyframe_insert("aperture_fstop", frame=r["f"])
        n += 1
    print(">> wrote %d focus/aperture keys over f%d-%d" % (n, lo, closeout - 1))

    # ---- THE GUARD. Position, rotation and lens must be untouched. ----------
    after = snapshot(scene, cam, guard_frames)
    worst_p = worst_q = worst_l = 0.0
    for f in guard_frames:
        pb, qb, lb = before[f]
        pa, qa, la = after[f]
        worst_p = max(worst_p, max(abs(pa[i] - pb[i]) for i in range(3)))
        worst_q = max(worst_q, max(abs(qa[i] - qb[i]) for i in range(4)))
        worst_l = max(worst_l, abs(la - lb))
    print(">> GUARD: position %.3e m, rotation %.3e, lens %.3e mm over %d frames"
          % (worst_p, worst_q, worst_l, len(guard_frames)))
    if max(worst_p, worst_q, worst_l) > 0.0:
        print("STAGE RESULT R2791_APPLY_FAIL this pass moved the camera")
        return 1

    # ---- continuity, measured on the curve that was actually written -------
    vals = []
    for f in range(lo, hi + 1):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        vals.append(cam.evaluated_get(dg).data.dof.focus_distance)
    step = [abs(vals[i + 1] - vals[i]) for i in range(len(vals) - 1)]
    sec = [abs(vals[i + 1] - 2 * vals[i] + vals[i - 1])
           for i in range(1, len(vals) - 1)]
    sec_s = sorted(sec)
    print(">> continuity as EVALUATED: max step %.4f m, second difference "
          "median %.5f p99 %.5f max %.5f"
          % (max(step), sec_s[len(sec_s) // 2],
             sec_s[int(0.99 * len(sec_s))], sec_s[-1]))

    if report:
        os.makedirs(os.path.dirname(report) or ".", exist_ok=True)
        json.dump({"rows": rows,
                   "evaluated_focus": [round(v, 5) for v in vals],
                   "guard": {"pos": worst_p, "quat": worst_q, "lens": worst_l}},
                  open(report, "w"))
        print(">> wrote %s" % report)

    if out_path:
        bpy.ops.wm.save_as_mainfile(filepath=out_path, compress=False)
        print(">> wrote %s (%.0f MB)" % (out_path, os.path.getsize(out_path) / 1e6))

    print("STAGE RESULT R2791_APPLY_OK keys=%d guard=clean maxstep=%.4f"
          % (n, max(step)))
    return 0


try:
    rc = main()
except Exception:
    traceback.print_exc()
    print("STAGE RESULT R2791_APPLY_FAIL uncaught exception")
    rc = 1
sys.stdout.flush()
