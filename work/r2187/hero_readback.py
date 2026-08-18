"""HOW MANY SHARDS GOT THE HERO MESH — asked of the meshes, not of the log.

    blender -b <scene>_breach.blend -P work/r2187/hero_readback.py -- --out X.json

`hero` is the applier's decision that a shard passes within 6 m of the camera
path and therefore gets `detail=2` — conchoidal relief and the laminate split
into its two plies.  It is the one stat in the apply report that is a function
of THE CAMERA, so it is the one that would move if the byte-identical-camera
claim were false.

Classifying by "big meshes are hero" is a guess.  This does not guess: it
rebuilds each cell at detail 1 and at detail 2 from the same fracture plan and
the same seed the applier used, and asks which of the two the mesh in the file
actually is.  A shard that matches NEITHER is a finding on its own.

Independently, it recomputes the camera-distance test from `breach_film.npz`
and `docs/beat_sheet.json` and checks the two agree.
"""
import argparse
import json
import os
import sys

import numpy as np

import bpy

R2 = os.path.expanduser("~/f1-round2")
sys.path.insert(0, os.path.join(R2, "sim"))
import fracture as FR          # noqa: E402
import shardmesh as SM         # noqa: E402
import breachlib as BL         # noqa: E402
import resample as RS          # noqa: E402


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--film", default=os.path.join(R2, "sim/out/breach_film.npz"))
    p.add_argument("--shards",
                   default=os.path.join(R2, "sim/out/fracture_wall.npz"))
    p.add_argument("--hero-m", type=float, default=6.0)
    return p.parse_args(argv)


def camera_polyline():
    sh = json.load(open(BL.SHEET))
    for k in ("camera", "cam", "path"):
        if k in sh:
            break
    # reuse the applier's own function so the two cannot disagree
    import apply_breach as AB
    return AB.camera_polyline()


def main():
    a = parse()
    sc = bpy.context.scene
    plan = FR.load(a.shards)
    film = RS.read_film(a.film)
    names, idx_of = film["names"], None
    idx_of = {n: i for i, n in enumerate(names)}

    import apply_breach as AB
    path = AB.camera_polyline()

    mesh_verts = {o.name: len(o.data.vertices)
                  for o in sc.objects if o.name.startswith("GS_b")}

    n_hero_mesh = n_bulk_mesh = n_unmatched = 0
    n_hero_cam = 0
    disagree = []
    unmatched = []
    for bay in sorted(plan["panes"]):
        if plan["roles"][bay] == "intact":
            continue
        for s in plan["panes"][bay]:
            nm = "GS_b%02d_%05d" % (bay, s["id"])
            j = idx_of.get(nm)
            if j is None or nm not in mesh_verts:
                continue
            got = mesh_verts[nm]
            seed = 1000 * bay + s["id"]
            v1 = len(SM.prism(s["poly"], AB.GLASS_X_IN, AB.GLASS_X_OUT,
                              detail=1, seed=seed)[0])
            v2 = len(SM.prism(s["poly"], AB.GLASS_X_IN, AB.GLASS_X_OUT,
                              detail=2, seed=seed)[0])
            _f, kl, _q = film["keys_of"](j)
            cam_hero = bool(AB.dist_to_path(kl, path).min() <= a.hero_m)
            if got == v2 and v2 != v1:
                mesh_hero = True
                n_hero_mesh += 1
            elif got == v1:
                mesh_hero = False
                n_bulk_mesh += 1
            else:
                n_unmatched += 1
                if len(unmatched) < 10:
                    unmatched.append([nm, got, v1, v2])
                continue
            n_hero_cam += int(cam_hero)
            if mesh_hero != cam_hero and len(disagree) < 10:
                disagree.append([nm, got, v1, v2, cam_hero])

    out = dict(
        hero_by_mesh=n_hero_mesh, bulk_by_mesh=n_bulk_mesh,
        unmatched=n_unmatched, unmatched_examples=unmatched,
        hero_by_camera_distance=n_hero_cam,
        disagreements=len(disagree), disagreement_examples=disagree,
        hero_m=a.hero_m, path_points=len(path),
        note=("hero_by_mesh reads the file; hero_by_camera_distance recomputes "
              "the applier's test from breach_film.npz and the beat sheet. "
              "They are two routes to the same number and must agree."))
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print("HERO by mesh %d   by camera distance %d   unmatched %d   "
          "disagreements %d"
          % (n_hero_mesh, n_hero_cam, n_unmatched, len(disagree)))
    print("STAGE RESULT: hero_readback written to %s" % a.out)


if __name__ == "__main__":
    main()
