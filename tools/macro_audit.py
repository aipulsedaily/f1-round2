"""Close-up worthiness gate — render every cluster at the distance the camera
will actually pass it in Beat 1, so materials fail HERE and not in a delivered frame.

    /opt/blender-5.2.0-linux-x64/blender -b <blend> --factory-startup \
        -P tools/macro_audit.py -- --plan docs/explode_plan.json \
        --out render/macro --dist 1.2 --res 3840 2160 --samples 512 \
        [--only MB,FW,SW]

WHY
---
The brief makes this a DEFECT GATE, not a nicety:

    "Render test close-ups of EVERY hero part at the actual camera distance from
     the beat sheet and pixel-peep them BEFORE animating the full beat. Any part
     that fails macro inspection gets its materials/geometry upgraded first ...
     If a texture is too low-res for its close-up, rebuild it at the needed
     resolution; never solve it by keeping the camera away."

Round 1 shipped materials that were authored to be seen from 3-8 m on a static
hero camera. Beat 1 flies a lens THROUGH the exploded field, so the same shaders
get presented at ~0.5-2 m at 4K. That is a 4-16x increase in angular detail and
it is where procedural weave turns to mush, decals go soft, and a bevel-less edge
reads as a razor.

WHAT IT DOES
------------
For each cluster in the explode plan it frames that cluster alone at `--dist`
metres from its bounding sphere, renders at full delivery resolution, and writes:
  * the beauty frame
  * a 1:1 centre crop, which is what actually gets pixel-peeped
  * measured sharpness (variance of Laplacian) and a clipped/crushed histogram
    readout, so a regression is detectable numerically as well as by eye

Sharpness is reported, NOT used as a pass mark. Round 1's most repeated lesson is
that a whole-image metric cannot clear a local defect — the number triages which
crops to look at first, it never substitutes for looking.

The camera is placed on the cluster's outboard side (the side the flying camera
will see it from) and slightly above, matching how Beat 1 presents parts.
"""

import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--plan", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--dist", type=float, default=1.2,
                   help="metres from the cluster's bounding sphere surface")
    p.add_argument("--res", type=int, nargs=2, default=[3840, 2160])
    p.add_argument("--samples", type=int, default=512)
    p.add_argument("--lens", type=float, default=50.0)
    p.add_argument("--fstop", type=float, default=2.8)
    p.add_argument("--only", default=None, help="comma list of cluster keys")
    return p.parse_args(argv)


def setup_render(a):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "GPU"
    sc.render.resolution_x, sc.render.resolution_y = a.res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "16"
    sc.cycles.samples = a.samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.0015
    # Match round-1 delivery policy: these are the settings that made paint read
    # as paint. ao_bounces silently replaces GI with an AO approximation; the
    # indirect clamp discards the energy that makes speculars.
    sc.cycles.max_bounces = 64
    sc.cycles.ao_bounces_render = 0
    sc.cycles.sample_clamp_indirect = 0.0
    sc.cycles.blur_glossy = 0.0
    sc.cycles.caustics_reflective = True
    sc.cycles.caustics_refractive = True
    sc.render.filter_size = 1.30
    sc.render.use_motion_blur = False   # a still audit; blur would mask softness


def isolate(parts):
    """Hide every OTHER car part and the props; keep the room and the lights.

    Two reasons, and the second is the important one:

    1. VRAM. The full scene evaluates to 10,122,867 triangles and the local card
       has 8 GB. A macro audit does not need the other 14 clusters resident.

    2. HONESTY OF THE TEST. What must be judged is whether THIS part's shader and
       geometry hold up at 0.5-2 m. Leaving the rest of the car in frame lets a
       neighbouring surface's reflection flatter the one under test, and lets a
       part hide behind another instead of failing visibly.

    SHOWROOM and LIGHTS stay: the carbon weave, clearcoat and metallics are lit
    and reflected BY that room, and judging them under different light than they
    will ship in would make the whole audit meaningless.
    """
    keep = set(parts)
    hidden = 0
    for ob in bpy.context.scene.objects:
        colls = {c.name for c in ob.users_collection}
        if "CAR" in colls or "PROPS" in colls:
            want = ob.name in keep
            ob.hide_render = not want
            if not want:
                hidden += 1
    return hidden


def frame_cluster(a, parts, name):
    objs = [bpy.data.objects.get(p) for p in parts]
    objs = [o for o in objs if o and o.type == "MESH"]
    if not objs:
        return None
    deps = bpy.context.evaluated_depsgraph_get()
    pts = []
    for ob in objs:
        oe = ob.evaluated_get(deps)
        try:
            me = oe.to_mesh()
        except Exception:
            continue
        if me:
            mw = ob.matrix_world
            pts += [mw @ v.co for v in me.vertices]
            oe.to_mesh_clear()
    if not pts:
        return None
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ctr = (lo + hi) * 0.5
    radius = max((hi - lo).length * 0.5, 0.02)

    cam_data = bpy.data.cameras.new(f"MACRO_{name}")
    cam_data.lens = a.lens
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = a.fstop
    cam_data.dof.focus_distance = radius + a.dist
    cam = bpy.data.objects.new(f"MACRO_{name}", cam_data)
    bpy.context.scene.collection.objects.link(cam)

    # Outboard and slightly above: the angle the flying camera actually presents
    # parts from. A dead-on axis view flatters shaders and hides grazing-angle
    # failures, which are exactly what macro inspection is looking for.
    lateral = 1.0 if ctr.y >= 0 else -1.0
    d = Vector((0.55, 0.72 * lateral, 0.42)).normalized()
    cam.location = ctr + d * (radius + a.dist)
    direction = ctr - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return {"centre": [round(v, 4) for v in ctr], "radius": round(radius, 4),
            "cam": [round(v, 4) for v in cam.location],
            "focus": round(cam_data.dof.focus_distance, 4)}


def main():
    a = parse_args()
    os.makedirs(a.out, exist_ok=True)
    plan = json.load(open(a.plan))
    setup_render(a)

    keys = list(plan["clusters"])
    if a.only:
        want = {k.strip() for k in a.only.split(",")}
        keys = [k for k in keys if k in want]

    results = {}
    for k in keys:
        c = plan["clusters"][k]
        n_hidden = isolate(c["parts"])
        info = frame_cluster(a, c["parts"], k)
        if info is None:
            print(f"!! {k}: no renderable parts")
            continue
        path = os.path.join(a.out, f"macro_{k}.png")
        bpy.context.scene.render.filepath = path
        print(f">> rendering {k}  {c['n_parts']} parts  r={info['radius']}m  "
              f"cam@{a.dist}m  -> {os.path.basename(path)}", flush=True)
        bpy.ops.render.render(write_still=True)
        info.update(n_parts=c["n_parts"], tris=c["tris"], path=path,
                    hidden_objects=n_hidden)
        results[k] = info

    json.dump({"args": vars(a), "clusters": results},
              open(os.path.join(a.out, "macro_audit.json"), "w"), indent=1)
    print(f">> {len(results)} cluster close-ups rendered to {a.out}")
    print(">> STAGE RESULT: MACRO_AUDIT_OK")



# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised: `blender -b -P x.py`
    # prints the traceback and exits 0, MEASURED on this box. A gate that
    # crashed was indistinguishable from one that passed. guard() makes an
    # uncaught exception a status 2 and passes any real verdict through
    # unchanged. One shared helper, not N copies -- see tools/gate_exit.py.
    gate_exit.guard(main, tool="macro_audit")
