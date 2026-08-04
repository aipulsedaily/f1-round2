"""HOW MUCH GLASS ENDS UNDER THE FLOOR, IN THE SCENE THAT RENDERS.

    blender -b render/film14_breach.blend -P work/r2187/scene_sink.py -- --out X.json

Two measures of the same thing, both taken here, because the difference between
them IS the open item:

  AXIS-ALIGNED   origin_z - max|local v_z|.  A shard's local z is the PANE's
                 vertical.  A shard lying flat on the forecourt has that axis
                 HORIZONTAL, so this bound charges it half its height in the
                 wall.  This is the measure behind the standing "627".

  ROTATED        min over vertices of (R . v)_z + origin_z, using the shard's
                 own applied quaternion.  This is where the glass actually is.

Another agent is fixing the verifier's copy of this right now (R2-196 in
`sim/verify_breach.py`, and their figure is 70).  Nothing here touches their
file: this reads the applied scene, through the applied f-curves, so it is an
independent route to the same quantity rather than a re-run of their code.
"""
import argparse
import json
import sys

import numpy as np

import bpy
from mathutils import Quaternion

SINK_M = 0.004


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--frame", type=int, default=1165)
    return p.parse_args(argv)


def curves(o):
    ad = o.animation_data
    if ad is None or ad.action is None:
        return None
    out = {}
    for layer in ad.action.layers:
        for strip in layer.strips:
            cb = strip.channelbag(ad.action_slot)
            if cb is None:
                continue
            for fc in cb.fcurves:
                out.setdefault(fc.data_path, {})[fc.array_index] = fc
    return out


def main():
    a = parse()
    sc = bpy.context.scene
    lo_true, lo_axis, names = [], [], []
    for o in sc.objects:
        if not o.name.startswith("GS_b"):
            continue
        c = curves(o)
        if c is None or "location" not in c or "rotation_quaternion" not in c:
            continue
        n = len(o.data.vertices)
        flat = np.empty(3 * n, dtype=np.float32)
        o.data.vertices.foreach_get("co", flat)
        V = flat.reshape(n, 3).astype(np.float64)
        P = np.array([c["location"][i].evaluate(a.frame) for i in range(3)])
        q = Quaternion([c["rotation_quaternion"][i].evaluate(a.frame)
                        for i in range(4)])
        q.normalize()
        R = np.array(q.to_matrix())
        lo_true.append(float((V @ R.T)[:, 2].min() + P[2]))
        lo_axis.append(float(P[2] - np.abs(V[:, 2]).max()))
        names.append(o.name)

    lo_true = np.array(lo_true)
    lo_axis = np.array(lo_axis)
    bad, old = lo_true < -SINK_M, lo_axis < -SINK_M
    spur = old & ~bad
    out = dict(
        frame=a.frame, n=len(lo_true),
        rotated=dict(below_floor=int(bad.sum()),
                     pct=round(100.0 * float(bad.mean()), 2),
                     worst_m=round(float(-lo_true.min()), 3)),
        axis_aligned=dict(below_floor=int(old.sum()),
                          pct=round(100.0 * float(old.mean()), 2),
                          worst_m=round(float(-lo_axis.min()), 3)),
        dropped_by_the_rotation=int(spur.sum()),
        found_only_by_the_rotation=int((bad & ~old).sum()),
        highest_dropped_m=(round(float(lo_true[spur].max()), 4)
                           if spur.any() else None),
        lowest_dropped_m=(round(float(lo_true[spur].min()), 4)
                          if spur.any() else None),
        worst_offenders=[[names[i], round(float(lo_true[i]), 3)]
                         for i in np.argsort(lo_true)[:6]],
        note="measured on the applied f-curves of the scene that renders")
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))
    print("STAGE RESULT: scene_sink done")


if __name__ == "__main__":
    main()
