"""From which direction is each cluster MOST LEGIBLE? Measured, by sampling.

    /opt/blender-5.2.0-linux-x64/blender -b /home/zany/opus5-car-render/work/iter.blend \
        --factory-startup -P tools/presentation_normals.py -- \
        --plan docs/explode_plan.json --out docs/presentation_normals.json

TWO WRONG ANSWERS BEFORE THIS ONE
---------------------------------
1. A generic azimuth spiral placed the camera at `i/n * 2pi * 1.35 + 0.6` around
   each cluster. Even coverage of the field, zero knowledge of the parts — and it
   presented the STEERING WHEEL FROM BEHIND. Sharp, well lit, carbon weave
   resolving, and showing the column stub while the display, LED strip and every
   button faced away.

2. The area-weighted mean face normal. Reasonable-sounding, and mathematically
   guaranteed to fail here: **the area-weighted normal of any closed watertight
   mesh is exactly zero** (divergence theorem). Every one of the 15 clusters duly
   reported confidence < 0.02 and "symmetric". The metric was not measuring the
   parts, it was measuring the fact that they are solids.

WHAT THIS MEASURES INSTEAD
--------------------------
The actual question is not "which way does it face" but "from which direction do
I see the most of it". So: sample directions on a sphere and score each by what a
lens there would actually receive.

    projected_area(d) = sum over faces of max(0, dot(normal, d)) * area

That is the real projected area of the cluster from direction `d`, and it is
maximised looking face-on at a disc, broadside at a wing, and so on.

Projected area alone cannot separate the front of a steering wheel from its back —
both project the same disc. So the score is also weighted by MATERIAL RICHNESS:
how many distinct materials contribute meaningful projected area from that
direction. The front of a wheel shows a display, an LED strip, buttons, grips and
carbon; the back shows one carbon shell. Richness is what "the interesting side"
actually means, and unlike a hand-written rule it generalises to parts nobody
anticipated.

    score(d) = projected_area(d) * (1 + 0.45 * distinct_materials(d))

Directions below the floor are discarded — the camera cannot fly under the dais —
and the winning direction is reported with a margin over the runner-up so a
genuinely ambiguous cluster is visible as ambiguous rather than silently decided.
"""

import argparse
import json
import math
import os
import sys
from collections import defaultdict

import bpy
from mathutils import Vector


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--plan", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--dirs", type=int, default=192)
    p.add_argument("--min-elev-deg", type=float, default=-8.0,
                   help="reject directions below this; the camera cannot fly "
                        "under the showroom floor")
    return p.parse_args(argv)


def sphere_dirs(n, min_elev_deg):
    """Fibonacci sphere, filtered to directions a camera could actually occupy."""
    out = []
    ga = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(n):
        z = 1.0 - (2.0 * i + 1.0) / n
        r = math.sqrt(max(0.0, 1.0 - z * z))
        th = ga * i
        v = Vector((math.cos(th) * r, math.sin(th) * r, z))
        if math.degrees(math.asin(max(-1.0, min(1.0, v.z)))) >= min_elev_deg:
            out.append(v.normalized())
    return out


def main():
    a = parse_args()
    plan = json.load(open(a.plan))
    deps = bpy.context.evaluated_depsgraph_get()
    dirs = sphere_dirs(a.dirs, a.min_elev_deg)

    out = {}
    for key, c in plan["clusters"].items():
        # gather (normal, area, material) once; scoring is then pure arithmetic
        faces = []
        for pname in c["parts"]:
            ob = bpy.data.objects.get(pname)
            if ob is None or ob.type != "MESH":
                continue
            oe = ob.evaluated_get(deps)
            try:
                me = oe.to_mesh()
            except Exception:
                continue
            if me is None:
                continue
            mw = ob.matrix_world
            nm = mw.to_3x3().inverted_safe().transposed()
            slots = [ms.material.name if ms.material else "?"
                     for ms in ob.material_slots] or ["?"]
            for poly in me.polygons:
                mat = slots[min(poly.material_index, len(slots) - 1)]
                faces.append(((nm @ poly.normal).normalized(), poly.area, mat))
            oe.to_mesh_clear()

        if not faces:
            out[key] = {"normal": [0, 0, 1], "score": 0.0, "note": "no geometry"}
            continue

        scored = []
        for d in dirs:
            proj = 0.0
            per_mat = defaultdict(float)
            for n, area, mat in faces:
                dot = n.dot(d)
                if dot > 0.0:
                    contrib = dot * area
                    proj += contrib
                    per_mat[mat] += contrib
            if proj <= 0.0:
                continue
            # a material counts as "visible" only if it is more than 2% of what
            # the lens sees — otherwise a single stray fastener inflates richness
            rich = sum(1 for v in per_mat.values() if v > 0.02 * proj)
            scored.append((proj * (1.0 + 0.45 * rich), proj, rich, d))

        scored.sort(key=lambda x: -x[0])
        best = scored[0]
        runner = scored[1] if len(scored) > 1 else best
        margin = (best[0] - runner[0]) / max(best[0], 1e-9)

        # RANKED ALTERNATIVES, not just the winner.
        #
        # The best direction is not always USABLE: SP's highest-scoring view is
        # straight up, and its exploded centre sits at z 4.2 m, so a 2.54 m
        # standoff put the lens at z 6.7 m — through the 6.5 m ceiling. That
        # render came back as a flat grey frame of the ceiling slab's underside.
        #
        # The camera placer therefore needs somewhere to go next. Emitting the
        # top 16 lets it walk down the ranking until a station fits inside the
        # room, instead of clamping the winner to the wall and re-aiming, which
        # silently changes the framing the score was computed for.
        alts = [{"normal": [round(v, 5) for v in d],
                 "score": round(sc, 5),
                 "projected_area_m2": round(pa, 5),
                 "distinct_materials": rich}
                for sc, pa, rich, d in scored[:16]]

        out[key] = {
            "normal": [round(v, 5) for v in best[3]],
            "ranked": alts,
            "score": round(best[0], 5),
            "projected_area_m2": round(best[1], 5),
            "distinct_materials": best[2],
            "margin_over_runner_up": round(margin, 5),
            "n_parts": c["n_parts"],
        }

    json.dump(out, open(a.out, "w"), indent=1)
    print(f">> {'cluster':<16}{'proj m2':>9}{'mats':>5}{'margin':>8}   direction")
    for k, v in sorted(out.items(), key=lambda x: -x[1].get("projected_area_m2", 0)):
        print(f"   {k:<16}{v.get('projected_area_m2',0):>9.4f}"
              f"{v.get('distinct_materials',0):>5}{v.get('margin_over_runner_up',0):>8.4f}"
              f"   {v['normal']}")
    print(f">> wrote {a.out}")
    print(">> STAGE RESULT: PRESENTATION_NORMALS_OK")



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
    gate_exit.guard(main, tool="presentation_normals")
