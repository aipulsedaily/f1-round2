"""IS THERE GLASS IN THE EAST WALL, AS SEEN FROM THE CAMERA?

    blender -b <scene>.blend -P work/r2187/glass_raycast.py -- \
        --frame 858 --out X.json

The metric that is supposed to answer this is broken: `n_GW_Right_Glass` counts
ROUND ONE's object names and reads 0 for a correct scene exactly as it does for
an empty one.  Looking at a 1920x1080 render is the fallback, and at this range,
through motion blur, clear glass and no glass are genuinely hard to tell apart
by eye -- which is how the wall shipped bare through film10, 11, 12 and 13.

So: cast rays from the film's own camera, at the film's own frame, and ask how
many of them meet a `GP_b*` pane, where the pane is, and which panes.

WHY NOT `scene.ray_cast`.  Tried first, and abandoned after 25 minutes without
a result: the film scene is 33,221 objects and 4.99 GB and the whole-scene BVH
does not build in any time worth spending.  A BVH over the ten panes alone is
120 triangles and builds instantly, and it answers the question that is
actually being asked -- IS THE GLAZING THERE AND IN FRONT OF THE CAMERA.

THE CONTROL IS THE SAME SCRIPT ON THE UNAPPLIED FILM.  `render/film14.blend`
must report ZERO, on the same rays, from the same camera, at the same frame.
That is not a trivial pass: it is the defect itself, and it is what film10-13
would all return.
"""
import argparse
import json
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--frame", type=int, default=858)
    p.add_argument("--out", required=True)
    p.add_argument("--grid", type=int, default=64)
    return p.parse_args(argv)


def main():
    a = parse()
    sc = bpy.context.scene
    sc.frame_set(a.frame)
    bpy.context.view_layer.update()
    sc.frame_set(a.frame)
    bpy.context.view_layer.update()
    cam = sc.camera

    panes = [o for o in sc.objects if o.name.startswith("GP_b")]
    verts, faces, owner = [], [], []
    xs = []
    for o in panes:
        if o.hide_render:
            continue                      # a hidden pane is not glazing
        m = o.matrix_world
        base = len(verts)
        for v in o.data.vertices:
            w = m @ v.co
            verts.append(w)
            xs.append(w.x)
        for p in o.data.polygons:
            idx = [base + i for i in p.vertices]
            for k in range(1, len(idx) - 1):
                faces.append((idx[0], idx[k], idx[k + 1]))
                owner.append(o.name)

    out = dict(blend=bpy.data.filepath, frame=a.frame, camera=cam.name,
               panes_in_scene=len(panes),
               panes_visible_at_frame=len({o.name for o in panes
                                           if not o.hide_render}),
               glass_x_range=[round(min(xs), 5), round(max(xs), 5)] if xs else None,
               materials=sorted({ms.material.name for o in panes
                                 for ms in o.material_slots if ms.material}),
               rays=a.grid ** 2, glass_hits=0, glass_pct=0.0,
               panes_hit=[], raster_bbox=None, hit_range_m=None)

    if faces:
        tree = BVHTree.FromPolygons([tuple(v) for v in verts], faces,
                                    all_triangles=True)
        corners = [cam.matrix_world @ v for v in cam.data.view_frame(scene=sc)]
        tr, br, bl, tl = corners
        org = cam.matrix_world.translation.copy()
        n = a.grid
        hit, seen, us, vs, dists = 0, set(), [], [], []
        for j in range(n):
            for i in range(n):
                u, v = (i + 0.5) / n, (j + 0.5) / n
                top = tl.lerp(tr, u)
                bot = bl.lerp(br, u)
                d = (bot.lerp(top, 1.0 - v) - org).normalized()
                loc, _nrm, idx, dist = tree.ray_cast(org, d)
                if loc is None:
                    continue
                hit += 1
                seen.add(owner[idx])
                us.append(u)
                vs.append(v)
                dists.append(dist)
        out["glass_hits"] = hit
        out["glass_pct"] = round(100.0 * hit / (n * n), 2)
        out["panes_hit"] = sorted(seen)
        if hit:
            out["raster_bbox"] = dict(x=[round(min(us), 3), round(max(us), 3)],
                                      y=[round(min(vs), 3), round(max(vs), 3)])
            out["hit_range_m"] = [round(min(dists), 2), round(max(dists), 2)]

    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))
    print("GLASS HITS %d of %d rays (%.2f %%), %d distinct panes"
          % (out["glass_hits"], out["rays"], out["glass_pct"],
             len(out["panes_hit"])))
    print("STAGE RESULT: glass_raycast done")


if __name__ == "__main__":
    main()
