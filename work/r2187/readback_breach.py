"""READ THE APPLIED SCENE BACK, from the saved .blend, not from the apply log.

    blender -b <scene>_breach.blend -P work/r2187/readback_breach.py -- --out X.json

Nothing here is quoted from sim/out/apply_*.json.  Every number is recounted
from the datablocks in the file that will actually render.

WHY THIS EXISTS.  R2-071's rule: a source fix has an artefact downstream of it
and the fix is not landed until the artefact has been REBUILT AND RE-READ.  An
apply log is the builder's own account of what it meant to do.
"""
import argparse
import json
import os
import sys

import bpy


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def main():
    a = parse()
    sc = bpy.context.scene
    R = {"blend": bpy.data.filepath, "bytes": None}
    try:
        R["bytes"] = os.path.getsize(bpy.data.filepath)
    except OSError:
        pass

    # ---- the BREACH collections, by name, as they were linked -------------- #
    cols = {c.name: c for c in bpy.data.collections}
    R["collections_present"] = sorted(
        n for n in cols if n.startswith("BREACH"))

    shards, panes = [], []
    for o in sc.objects:
        if o.name.startswith("GS_b"):
            shards.append(o)
        elif o.name.startswith("GP_b"):
            panes.append(o)

    def tris(o):
        if o.type != "MESH" or o.data is None:
            return 0
        return sum(len(p.vertices) - 2 for p in o.data.polygons)

    def verts(o):
        return len(o.data.vertices) if (o.type == "MESH" and o.data) else 0

    n_tris = sum(tris(o) for o in shards) + sum(tris(o) for o in panes)

    # ---- keys: every keyframe point on every fcurve these objects drive ---- #
    n_keys = 0
    chan = {}
    acts_seen = set()
    for o in shards + panes:
        ad = o.animation_data
        if ad is None or ad.action is None:
            continue
        act = ad.action
        if act.name in acts_seen:
            continue
        acts_seen.add(act.name)
        slot = ad.action_slot
        for layer in act.layers:
            for strip in layer.strips:
                cb = strip.channelbag(slot) if slot else None
                if cb is None:
                    continue
                for fc in cb.fcurves:
                    n = len(fc.keyframe_points)
                    n_keys += n
                    chan[fc.data_path] = chan.get(fc.data_path, 0) + n
    R["stats"] = dict(objects=len(shards) + len(panes), tris=int(n_tris),
                      keys=int(n_keys), hero=None)
    R["keys_by_channel"] = chan
    R["n_shards"] = len(shards)
    R["n_panes"] = len(panes)
    R["n_actions"] = len(acts_seen)

    # ---- hero, classified from the MESH, not from the build ---------------- #
    # detail 2 adds conchoidal relief and splits the laminate into two plies:
    # it cannot produce the same vertex count as detail 1 for the same cell.
    # So the population is bimodal and the split is readable off the file.
    vc = sorted(verts(o) for o in shards)
    if vc:
        # find the largest gap in the sorted vertex counts
        gaps = [(vc[i + 1] - vc[i], i) for i in range(len(vc) - 1)]
        g, i = max(gaps)
        cut = 0.5 * (vc[i] + vc[i + 1])
        R["hero_split"] = dict(cut_verts=cut, gap=g,
                               bulk_max=vc[i], hero_min=vc[i + 1])
        hero = [o for o in shards if verts(o) > cut]
        R["stats"]["hero"] = len(hero)
        R["vert_range"] = [vc[0], vc[-1]]

    # ---- the swap, per bay, read off the pane curves ----------------------- #
    swap = {}
    for o in panes:
        bay = int(o.name[4:])
        ad = o.animation_data
        if ad is None or ad.action is None:
            swap[bay] = None
            continue
        fr = None
        for layer in ad.action.layers:
            for strip in layer.strips:
                cb = strip.channelbag(ad.action_slot)
                if cb is None:
                    continue
                for fc in cb.fcurves:
                    if fc.data_path != "hide_render":
                        continue
                    for kp in fc.keyframe_points:
                        if kp.co[1] > 0.5:
                            fr = int(kp.co[0]) if fr is None \
                                else min(fr, int(kp.co[0]))
        swap[bay] = fr
    R["pane_hide_frame"] = {str(k): v for k, v in sorted(swap.items())}

    # ---- is there glass in the east wall at frame 1? ----------------------- #
    sc.frame_set(1)
    bpy.context.view_layer.update()
    vis = {}
    for o in panes:
        vis[o.name] = dict(hide_render=bool(o.hide_render),
                           hide_viewport=bool(o.hide_viewport),
                           x=round(o.matrix_world.translation.x, 5))
    R["panes_at_frame_1"] = vis
    R["east_wall_glazed_at_f1"] = bool(
        len(panes) == 10 and not any(v["hide_render"] for v in vis.values()))

    # ---- scene-level facts ------------------------------------------------- #
    R["scene"] = dict(
        name=sc.name,
        frame_start=sc.frame_start, frame_end=sc.frame_end,
        fps=sc.render.fps,
        scale_length=sc.unit_settings.scale_length,
        camera=sc.camera.name if sc.camera else None,
        objects_total=len(sc.objects),
        meshes_total=len([o for o in sc.objects if o.type == "MESH"]),
        engine=sc.render.engine,
    )
    # round-1 east glazing must be gone; round-1 east FRAME is a known intruder
    R["round1_east_glass_present"] = sorted(
        o.name for o in sc.objects if "GW_Right_Glass" in o.name)
    R["round1_east_frame_present"] = sorted(
        o.name for o in sc.objects
        if o.name.startswith(("GW_Right_Transom", "WallLine_SideFin")))
    R["apron"] = None
    ap = sc.objects.get("ARCH_Paving_ApronPlatform")
    if ap is not None and ap.type == "MESH":
        R["apron"] = dict(verts=len(ap.data.vertices),
                          polys=len(ap.data.polygons))

    with open(a.out, "w") as fh:
        json.dump(R, fh, indent=1)
    print("READBACK objects=%d tris=%d keys=%d hero=%s"
          % (R["stats"]["objects"], R["stats"]["tris"], R["stats"]["keys"],
             R["stats"]["hero"]))
    print("READBACK east_wall_glazed_at_f1=%s panes=%d shards=%d"
          % (R["east_wall_glazed_at_f1"], len(panes), len(shards)))
    print("STAGE RESULT: readback written to %s" % a.out)


if __name__ == "__main__":
    main()
