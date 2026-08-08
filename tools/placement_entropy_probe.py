"""R2-2341 -- WHERE DOES THE PLACEMENT REPORT'S SCATTER COME FROM?

    /opt/blender-5.2.0-linux-x64/blender -b <world.blend> --factory-startup \
        -noaudio -P tools/placement_entropy_probe.py -- --out probe.json \
        [--spec ... --telemetry ... --sheet ... --campath ...] [--repeats 3]

This is a DIAGNOSTIC, not a gate. It re-runs `placement_gate.measure()` inside
one Blender process and records, for every run, the things a differ of two
`placement_report.json` files cannot see:

  * the ORDER of `scene.objects`, hashed -- if the scene walk reorders between
    processes, every tie in `closest_approach` flips with it;
  * the ORDER of `bpy.data.objects`, hashed, for the same reason;
  * the full RANKING of the top approaches per volume, not just the winner, so
    a tie can be told apart from a real change;
  * every object the gate SILENTLY SKIPPED -- `bbox_world()` and `to_mesh()`
    are both wrapped in `except: continue`, and a skip under memory pressure
    would move the answer with nothing recorded;
  * `tested` / `coarse_rejected`, which must be identical run to run.

Writing this before theorising is the point. The distribution decides which
family of cause is even possible.
"""
import argparse
import hashlib
import json
import os
import sys

import bpy
from mathutils import Vector

R2 = "/home/zany/f1-round2"
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import placement_gate as PG                                       # noqa: E402


def _h(names):
    return hashlib.sha256("\n".join(names).encode()).hexdigest()[:16]


def measure_verbose(scene, volumes, allow, context_names):
    """`placement_gate.measure()`, re-implemented ONLY so far as it needs to be
    to record what it skipped and the full ranking. The decision arithmetic is
    the gate's own `intrusion()` -- this must not become a second opinion."""
    deps = bpy.context.evaluated_depsgraph_get()
    skipped_bbox, skipped_mesh, empty_mesh = [], [], []
    ranking = {}                       # volume -> [(intrusion, object, at)]
    tested = coarse_rejected = 0
    matrix_mismatch = []
    max_r = max(max(v["radius"]) for v in volumes.values())

    for ob in scene.objects:
        if ob.type != "MESH" or ob.name.startswith(allow):
            continue
        oe = ob.evaluated_get(deps)
        try:
            lo, hi = PG.bbox_world(oe)
        except Exception as e:                                    # noqa: BLE001
            skipped_bbox.append([ob.name, repr(e)[:120]])
            continue
        tested += 1

        centre = (lo + hi) * 0.5
        reach = (hi - lo).length * 0.5 + max_r
        near = {}
        for vname, vol in volumes.items():
            if vol["kd"].find_range((centre.x, centre.y, 0.0), reach):
                near[vname] = vol
        if not near:
            coarse_rejected += 1
            continue

        try:
            me = oe.to_mesh()
        except Exception as e:                                    # noqa: BLE001
            skipped_mesh.append([ob.name, repr(e)[:120]])
            continue
        if me is None or not me.polygons:
            empty_mesh.append(ob.name)
            continue

        # THE GATE MEASURES WITH `ob.matrix_world` BUT REJECTS WITH
        # `oe.matrix_world`. Record every object where the two disagree.
        d_mw = max(abs(a - b) for ra, rb in zip(ob.matrix_world, oe.matrix_world)
                   for a, b in zip(ra, rb))
        if d_mw > 1e-9:
            matrix_mismatch.append([ob.name, round(d_mw, 6)])

        mw = ob.matrix_world
        worst = {}
        for v in me.vertices:
            p = mw @ v.co
            for vname, vol in near.items():
                d = PG.intrusion(vol, p)
                if d > worst.get(vname, (-1e9,))[0]:
                    worst[vname] = (d, (round(p.x, 3), round(p.y, 3),
                                        round(p.z, 3)))
        oe.to_mesh_clear()

        is_ground = ob.name.startswith(PG.GROUND_FAMILIES)
        is_ctx = ob.name in context_names
        for vname, (d, at) in worst.items():
            if vname == "car_path" and is_ground:
                continue
            if is_ctx:
                continue
            ranking.setdefault(vname, []).append([d, ob.name, at])

    for k in ranking:
        # Sort by intrusion only, PRESERVING the scene order among equals, so a
        # tie is visible as adjacent equal values rather than hidden by a
        # name-sort. `sorted` is stable.
        ranking[k].sort(key=lambda r: -r[0])
    return {"ranking": {k: v[:25] for k, v in ranking.items()},
            "tested": tested, "coarse_rejected": coarse_rejected,
            "skipped_bbox": skipped_bbox, "skipped_to_mesh": skipped_mesh,
            "empty_mesh": empty_mesh,
            "matrix_world_mismatch": matrix_mismatch[:50],
            "matrix_world_mismatch_total": len(matrix_mismatch)}


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--repeats", type=int, default=2)
    p.add_argument("--subject", default=None)
    p.add_argument("--allow", default=",".join(PG.DEFAULT_ALLOW))
    p.add_argument("--spec", default=os.path.join(R2, "docs/circuit_spec.json"))
    p.add_argument("--telemetry",
                   default=os.path.join(R2, "telemetry/telemetry.csv"))
    p.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    p.add_argument("--campath",
                   default=os.path.join(R2, "world/camera_rig_path.json"))
    p.add_argument("--step", type=float, default=4.0)
    a = p.parse_args(argv)

    spec = json.load(open(a.spec))
    scene = bpy.context.scene

    doc = {"blend": bpy.data.filepath,
           "scene": scene.name,
           "frame_current": scene.frame_current,
           "scene_objects_order_sha": _h([o.name for o in scene.objects]),
           "scene_objects_n": len(scene.objects),
           "data_objects_order_sha": _h([o.name for o in bpy.data.objects]),
           "data_objects_n": len(bpy.data.objects),
           "collections_order_sha": _h([c.name for c in bpy.data.collections]),
           "pythonhashseed": os.environ.get("PYTHONHASHSEED"),
           "half_width_source": None,
           "runs": []}

    # WHICH half_width DID WE GET? `half_width_fn` swallows an ImportError and
    # falls back to a CONSTANT width off the spec. Two runs on either side of
    # that fallback measure different corridors and nothing in the report says so.
    try:
        sys.path.insert(0, os.path.join(R2, "world"))
        import world_contract as WC                                # noqa
        doc["half_width_source"] = ("world_contract.half_width"
                                    if hasattr(WC, "half_width") else
                                    "world_contract present, no half_width")
    except Exception as e:                                         # noqa: BLE001
        doc["half_width_source"] = "FALLBACK constant: %r" % (repr(e)[:160],)

    for i in range(a.repeats):
        volumes = PG.build_volumes(a, spec, verbose=(i == 0))
        sub, ctx, why = PG.split_subject_context(scene, a.subject)
        allow = tuple(x.strip() for x in a.allow.split(",") if x.strip())
        r = measure_verbose(scene, volumes, allow, ctx)
        r["subject_n"] = len(sub)
        r["context_n"] = len(ctx)
        r["subject_why"] = why
        r["road_radius_min"] = round(min(volumes["road_corridor"]["radius"]), 6)
        r["road_radius_max"] = round(max(volumes["road_corridor"]["radius"]), 6)
        r["volume_names"] = sorted(volumes)
        doc["runs"].append(r)
        top = {k: (round(v[0][0], 6), v[0][1]) for k, v in r["ranking"].items()}
        print(">> probe pass %d: tested=%d coarse=%d skipped_bbox=%d "
              "skipped_to_mesh=%d empty=%d mw_mismatch=%d top=%s"
              % (i, r["tested"], r["coarse_rejected"], len(r["skipped_bbox"]),
                 len(r["skipped_to_mesh"]), len(r["empty_mesh"]),
                 r["matrix_world_mismatch_total"], top))

    json.dump(doc, open(a.out, "w"), indent=1)
    print(">> wrote %s" % a.out)
    print(">> STAGE RESULT: PROBE_OK")


if __name__ == "__main__":
    main()
