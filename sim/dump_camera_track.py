"""THE ONE CAMERA'S TRANSFORM AT EVERY FRAME, from whichever scene is current.

    blender -b <film>.blend -P sim/dump_camera_track.py -- \
        --out sim/out/oner_camera_track.json

WHY THIS FILE EXISTS
====================
`sim/out/oner_camera_track.json` is what `sim/sagpx.py` and
`build_breach_sim.camera_ranges()` project through.  EVERY pixel figure about
this wall -- the sag on the panes that stay, the size of the wound on screen,
which bay is the worst bay -- is that table times a displacement.  It was
produced once, by hand, from `render/film9.blend` at 15:13 on 2026-08-03.

The camera has moved twice since: film11 carries a relit scene with a new
camera and film11_r2085cam a newer one again, and film12 is being built on
assembly8.  A hand-made table with no recorded provenance, feeding every pixel
number in the report, is the same shape of defect as `camera_ranges` charging
bay 2 at 3.52 m -- an instrument nobody re-derived because nobody could see
where it came from.

So it is a script, it records which scene and which camera it came from, and
it refuses rather than guessing when the scene does not have exactly one.

WHAT IT WRITES
    one row per frame: [frame, x, y, z, qw, qx, qy, qz, lens_mm]
    plus a sidecar .meta.json naming the blend, its size, the camera, the
    frame range and the sensor width -- because a track that does not say
    which sensor it assumes cannot be checked against a render.
"""
import argparse
import json
import os
import sys

import bpy                                                        # noqa: E402

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out",
                    default=os.path.join(R2, "sim/out/oner_camera_track.json"))
    ap.add_argument("--camera", default=None,
                    help="object name; default is the scene's own camera")
    a = ap.parse_args(argv)

    sc = bpy.context.scene
    cam = bpy.data.objects.get(a.camera) if a.camera else sc.camera
    if cam is None or cam.type != "CAMERA":
        raise SystemExit("REFUSING: no camera. scene.camera = %r, asked for "
                         "%r.  Guessing which camera a one-take film is shot "
                         "on is not something this script may do."
                         % (getattr(sc.camera, "name", None), a.camera))
    cams = [o for o in sc.objects if o.type == "CAMERA"]
    if len(cams) != 1:
        print("NOTE: %d cameras in the scene (%s); using %s"
              % (len(cams), [o.name for o in cams], cam.name))

    rows = []
    for f in range(sc.frame_start, sc.frame_end + 1):
        sc.frame_set(f)
        m = cam.matrix_world
        q = m.to_quaternion()
        t = m.to_translation()
        rows.append([f, t.x, t.y, t.z, q.w, q.x, q.y, q.z,
                     cam.data.lens])
    with open(a.out, "w") as fh:
        json.dump(rows, fh)

    meta = dict(
        blend=bpy.data.filepath,
        blend_bytes=(os.path.getsize(bpy.data.filepath)
                     if bpy.data.filepath and os.path.exists(bpy.data.filepath)
                     else None),
        camera=cam.name, n_cameras_in_scene=len(cams),
        frame_start=sc.frame_start, frame_end=sc.frame_end, rows=len(rows),
        sensor_width_mm=cam.data.sensor_width,
        sensor_fit=cam.data.sensor_fit,
        res_x=sc.render.resolution_x, res_y=sc.render.resolution_y,
        res_pct=sc.render.resolution_percentage,
        lens_mm_first=rows[0][8], lens_mm_last=rows[-1][8],
        lens_is_animated=bool(len({round(r[8], 6) for r in rows}) > 1),
        note="sim/sagpx.py assumes SENSOR = 36.0 and 3840x2160.  If "
             "sensor_width_mm or res_x above disagree with that, every pixel "
             "figure taken through this track is wrong by the ratio, and "
             "sagpx must be corrected rather than the track.")
    with open(a.out.replace(".json", ".meta.json"), "w") as fh:
        json.dump(meta, fh, indent=1)

    agree = (abs(meta["sensor_width_mm"] - 36.0) < 1e-6
             and meta["res_x"] == 3840 and meta["res_y"] == 2160)
    print(json.dumps(meta, indent=1))
    print("STAGE RESULT: camera track %s -- %d rows from %s, camera %s, "
          "sagpx assumptions %s"
          % ("written" if rows else "EMPTY", len(rows),
             os.path.basename(meta["blend"] or "?"), cam.name,
             "AGREE" if agree else "DISAGREE (see note)"))


if __name__ == "__main__":
    main()
