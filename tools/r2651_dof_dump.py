#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2651_dof_dump.py — dump the ONER camera's DOF and shutter per frame.

`world/camera_rig_path.json` publishes p / q / lens and NOTHING ELSE, so any
argument about whether the circuit is soft because of depth of field has no
input. This reads the built rig and writes fstop, focus_distance and the scene
shutter for every frame, so the blur budget can be computed without Blender.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        world/camera_rig.blend -P tools/r2651_dof_dump.py -- --out render/r2651/dof.json

Judge on the printed STAGE RESULT line. Blender 5.2 exits 0 on an exception.
"""
import json
import os
import sys

import bpy

TOKEN_OK = "R2651_DOF_DUMP_OK"


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = "render/r2651/dof.json"
    for a in argv:
        if a.startswith("--out="):
            out = a.split("=", 1)[1]

    scene = bpy.context.scene
    cam = scene.camera
    if cam is None:
        cams = [o for o in scene.objects if o.type == "CAMERA"]
        cam = cams[0] if cams else None
    if cam is None:
        print(">> STAGE RESULT: R2651_DOF_DUMP_NO_CAMERA")
        return

    rows = []
    f0, f1 = scene.frame_start, scene.frame_end
    for f in range(f0, f1 + 1):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        ce = cam.evaluated_get(dg)
        d = ce.data
        rows.append(dict(
            f=f,
            lens=round(float(d.lens), 5),
            fstop=round(float(d.dof.aperture_fstop), 5),
            focus=round(float(d.dof.focus_distance), 5),
            use_dof=bool(d.dof.use_dof),
            blades=int(d.dof.aperture_blades),
            shutter=round(float(getattr(scene.render, "motion_blur_shutter", -1.0)), 6),
        ))

    rd = scene.render
    meta = dict(
        camera=cam.name,
        sensor_width=float(cam.data.sensor_width),
        sensor_fit=str(cam.data.sensor_fit),
        res_x=int(rd.resolution_x), res_y=int(rd.resolution_y),
        res_pct=int(rd.resolution_percentage),
        fps=int(rd.fps),
        # Blender 5.2 keeps motion blur on scene.render, not scene.cycles.
        motion_blur=bool(getattr(rd, "use_motion_blur",
                                 getattr(scene.cycles, "use_motion_blur", False))),
        shutter=float(getattr(rd, "motion_blur_shutter",
                              getattr(scene.cycles, "motion_blur_shutter", -1.0))),
        shutter_position=str(getattr(rd, "motion_blur_position",
                                     getattr(scene.cycles, "motion_blur_position", "?"))),
        use_curve=bool(getattr(rd, "use_motion_blur_shutter_curve", False)),
        frame_start=f0, frame_end=f1,
        clip_start=float(cam.data.clip_start), clip_end=float(cam.data.clip_end),
    )

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(dict(meta=meta, frames=rows), fh)

    fs = [r["fstop"] for r in rows]
    fo = [r["focus"] for r in rows]
    print(">> camera %s  sensor %.1f  %dx%d @%d%%  fps %d"
          % (meta["camera"], meta["sensor_width"], meta["res_x"], meta["res_y"],
             meta["res_pct"], meta["fps"]))
    print(">> motion_blur %s  shutter %.4f  position %s"
          % (meta["motion_blur"], meta["shutter"], meta["shutter_position"]))
    print(">> fstop  min %.3f  max %.3f  distinct %d"
          % (min(fs), max(fs), len(set(round(v, 3) for v in fs))))
    print(">> focus  min %.3f  max %.3f  m" % (min(fo), max(fo)))
    print(">> wrote %d frames -> %s" % (len(rows), out))
    print(">> STAGE RESULT: %s" % TOKEN_OK)


main()
