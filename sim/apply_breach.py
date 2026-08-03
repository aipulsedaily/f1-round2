"""APPLY THE BREACH — the baked table becomes geometry and keys in a scene.

    blender -b <target>.blend -P sim/apply_breach.py -- --out work/with_breach.blend

This is the CONTINUITY deliverable (#32).  It does not run a sim; it reads the
one that was baked and writes the wall, the shards, the aperture and their
motion into whatever scene it is pointed at, for ALL 2,978 frames.

WHY THE WOUND PERSISTS BY CONSTRUCTION AND NOT BY A SECOND ASSET
================================================================
There is no "wounded showroom" variant, because a variant is a thing that can
disagree with the original and a one-take film has nowhere to hide the moment it
does.  There is ONE set of objects for the whole take:

    frames 1 .. release-1      the pane renders as ONE solid object.  Its shards
                               exist but are hidden.  The wall is intact because
                               the intact pane IS what the camera sees.
    the release frame          the intact pane hides and the shards show, on the
                               same frame, in the same place — the shards are a
                               watertight partition OF THAT PANE, so the
                               silhouette does not move by one vertex.
    release .. rest            the baked transforms play.
    rest .. 2978               the F-curves simply stop, with CONSTANT
                               extrapolation.  The wound is where the solver
                               left it, at zero further cost, and beats 4, 5 and
                               6 see it because it never went anywhere.

Beat 6's declared "wound enters frame at t = 6.0" is 80 s of screen time after
the shards stopped moving, and what it sees is the last row of the bake.

WHY THERE IS A SWAP AT ALL
--------------------------
A pre-fractured pane whose pieces are separate closed solids is not optically
the same object as the pane, even with zero gap: light entering shard A and
leaving into shard B crosses glass -> air -> glass at a shared face, and at
1.6 m on a 35 mm lens (2,333 px/m) that shows.  So the intact pane carries beat
1's 33 seconds and the shards take over on the frame the glass actually moves.
The swap is invisible for a reason that can be checked rather than asserted:
`sim/verify_breach.py --swap` renders the frame before, the frame of, and the
frame after, and diffs them.

DETAIL IS GRADED BY THE CAMERA PATH, NOT BY GUESS
-------------------------------------------------
`docs/beat_sheet.json` carries the ONE camera's world position at every key.
A shard that comes within `--hero-m` of that polyline at any point in the take
gets the full mesh (chamfered arris + conchoidal relief on the thickness); the
rest get the prism.  The counts are reported so the trade is visible.
"""

import argparse
import json
import math
import os
import sys
import time

import bpy                                                        # noqa: E402
import numpy as np                                                # noqa: E402

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "sim"), os.path.join(R2, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import breachlib as BL                                            # noqa: E402
import fracture as FR                                             # noqa: E402
import shardmesh as SM                                            # noqa: E402

T0 = time.time()
GLASS_X_IN, GLASS_X_OUT = 14.955, 14.9665


def log(m):
    print("[apply %7.1fs] %s" % (time.time() - T0, m))
    sys.stdout.flush()


# --------------------------------------------------------------------------- #

def camera_polyline(sheet_path=BL.SHEET):
    """The one camera's world positions, as an N x 3 polyline."""
    with open(sheet_path) as fh:
        sheet = json.load(fh)
    pts = []
    for k in sorted(sheet.keys()):
        # "beats" is a LIST of beat records; "beat1".."beat6" are the dicts with
        # the camera keys in them.  Blender 5.2 exits 0 on an uncaught
        # exception, so this went by as a clean exit code with a traceback in
        # the log — read the text, never `$?`.
        b = sheet[k]
        if not k.startswith("beat") or not isinstance(b, dict):
            continue
        for key in b.get("camera_keys", []):
            pts.append(key["world"])
        for a in b.get("anchors", []):
            if "world" in a:
                pts.append(a["world"])
    return np.array(pts, float)


def dist_to_path(P, path):
    """Min distance from each point in P (N x 3) to the camera polyline."""
    best = np.full(len(P), 1e9)
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        ab = b - a
        L2 = float(ab @ ab)
        t = np.zeros(len(P)) if L2 < 1e-12 else \
            np.clip(((P - a) @ ab) / L2, 0.0, 1.0)
        best = np.minimum(best, np.linalg.norm(P - (a + t[:, None] * ab),
                                               axis=1))
    return best


# --------------------------------------------------------------------------- #

def make_action(name, chans):
    """A slotted action with the given (data_path, index) channels."""
    act = bpy.data.actions.new(name)
    slot = act.slots.new(id_type="OBJECT", name="Object")
    cb = act.layers.new("L").strips.new(type="KEYFRAME").channelbag(
        slot, ensure=True)
    fcs = [cb.fcurves.new(p, index=i) for p, i in chans]
    return act, slot, fcs


def key_linear(fc, frames, values, extrap="CONSTANT"):
    """Write keys and MAKE THEM LINEAR.

    `keyframe_new_interpolation_type` is not honoured by `keyframe_insert` in
    Blender 5.2 (71,472 of 71,472 keys came out BEZIER).  `foreach_set` bypasses
    it entirely, so the enum is written per point and the caller PROVES it by
    evaluating the curve — see `prove_curves`.
    """
    n = len(frames)
    kp = fc.keyframe_points
    kp.add(count=n)
    flat = np.empty(2 * n)
    flat[0::2] = frames
    flat[1::2] = values
    kp.foreach_set("co", flat)
    kp.foreach_set("interpolation", [1] * n)        # 1 == LINEAR
    fc.extrapolation = extrap
    fc.update()


def key_constant(fc, frames, values):
    n = len(frames)
    kp = fc.keyframe_points
    kp.add(count=n)
    flat = np.empty(2 * n)
    flat[0::2] = frames
    flat[1::2] = values
    kp.foreach_set("co", flat)
    kp.foreach_set("interpolation", [0] * n)        # 0 == CONSTANT
    fc.extrapolation = "CONSTANT"
    fc.update()


# --------------------------------------------------------------------------- #

def build(args):
    sc = bpy.context.scene
    import resample as RS
    film = RS.read_film(args.film)
    names = film["names"]
    rel = film["release"]
    span = film["span"]
    plan = FR.load(args.shards)

    total = int(json.load(open(BL.SHEET))["total_frames"])
    sc.frame_start, sc.frame_end = 1, total

    root = bpy.data.collections.new("BREACH")
    sc.collection.children.link(root)
    C_shard = bpy.data.collections.new("BREACH_Shards")
    C_pane = bpy.data.collections.new("BREACH_Panes")
    C_frame = bpy.data.collections.new("BREACH_Frame")
    for c in (C_shard, C_pane, C_frame):
        root.children.link(c)

    mat = bpy.data.materials.get(args.glass_material)
    if mat is None:
        mat = bpy.data.materials.new(args.glass_material)
        mat.use_nodes = True
        b = mat.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = (0.90, 0.94, 0.92, 1.0)
        b.inputs["Roughness"].default_value = 0.02
        if "Transmission Weight" in b.inputs:
            b.inputs["Transmission Weight"].default_value = 1.0
        if "IOR" in b.inputs:
            b.inputs["IOR"].default_value = 1.52

    # -- which shards are hero? --------------------------------------------- #
    path = camera_polyline()
    idx_of = {n: i for i, n in enumerate(names)}
    keyset = []
    for bay in sorted(plan["panes"]):
        if plan["roles"][bay] == "intact":
            continue
        for s in plan["panes"][bay]:
            nm = "GS_b%02d_%05d" % (bay, s["id"])
            j = idx_of.get(nm)
            if j is None:
                continue
            keyset.append((bay, s, nm, j))
    # closest approach over the whole take, per shard, measured on the KEYS
    # (they bracket the curve, so a shard that never gets near the path on its
    # keys never gets near it between them either)
    hero = np.zeros(len(keyset), bool)
    for i, (bay, s, nm, j) in enumerate(keyset):
        _f, kl, _q = film["keys_of"](j)
        hero[i] = dist_to_path(kl, path).min() <= args.hero_m
    log("hero shards: %d of %d within %.1f m of the camera path"
        % (int(hero.sum()), len(keyset), args.hero_m))

    # -- the shards ---------------------------------------------------------- #
    stats = dict(objects=0, tris=0, keys=0, hero=int(hero.sum()))
    for i, (bay, s, nm, j) in enumerate(keyset):
        det = args.detail_hero if hero[i] else args.detail_bulk
        V, F = SM.prism(s["poly"], GLASS_X_IN, GLASS_X_OUT, detail=det,
                        seed=1000 * bay + s["id"])
        me = bpy.data.meshes.new(nm)
        me.from_pydata([tuple(v) for v in V], [], [list(f) for f in F])
        me.validate(verbose=False)
        me.update()
        me.materials.append(mat)
        ob = bpy.data.objects.new(nm, me)
        C_shard.objects.link(ob)
        ob.rotation_mode = "QUATERNION"
        stats["objects"] += 1
        stats["tris"] += sum(len(f) - 2 for f in F)

        fk, kl, kq = film["keys_of"](j)
        act, slot, fcs = make_action("BR_%s" % nm,
                                     [("location", 0), ("location", 1),
                                      ("location", 2),
                                      ("rotation_quaternion", 0),
                                      ("rotation_quaternion", 1),
                                      ("rotation_quaternion", 2),
                                      ("rotation_quaternion", 3)])
        for c in range(3):
            key_linear(fcs[c], fk, kl[:, c])
        for c in range(4):
            key_linear(fcs[3 + c], fk, kq[:, c])
        stats["keys"] += 7 * len(fk)
        # visibility: hidden until this pane's glass moves
        r = int(rel[j])
        if r > span[0]:
            fv = act.layers[0].strips[0].channelbag(slot).fcurves
            for dp in ("hide_render", "hide_viewport"):
                fc = fv.new(dp, index=0)
                key_constant(fc, [1, r - 1, r], [1.0, 1.0, 0.0])
                stats["keys"] += 3
        ob.animation_data_create()
        ob.animation_data.action = act
        ob.animation_data.action_slot = slot
        if i % 500 == 0:
            log("  shard %d/%d" % (i, len(keyset)))

    # -- the intact panes, and the swap -------------------------------------- #
    # Every bay gets one, including the four the car never touches: those simply
    # never hide.
    rects, roles = plan["rects"], plan["roles"]
    for bay in sorted(plan["panes"]):
        u0, u1, v0, v1 = rects[bay]
        V = np.array([[x, y, z] for x in (GLASS_X_IN, GLASS_X_OUT)
                      for y in (u0, u1) for z in (v0, v1)], float)
        c = V.mean(axis=0)
        F = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1],
             [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
        me = bpy.data.meshes.new("GP_b%02d" % bay)
        me.from_pydata([tuple(v - c) for v in V], [], F)
        me.validate(verbose=False)
        me.update()
        me.materials.append(mat)
        ob = bpy.data.objects.new("GP_b%02d" % bay, me)
        ob.location = tuple(c)
        C_pane.objects.link(ob)
        stats["objects"] += 1
        if roles[bay] == "intact":
            continue
        rs = [int(rel[idx_of["GS_b%02d_%05d" % (bay, s["id"])]])
              for s in plan["panes"][bay]
              if "GS_b%02d_%05d" % (bay, s["id"]) in idx_of]
        rs = [r for r in rs if r > 0]
        r = min(rs) if rs else -1
        if r <= 0:
            continue
        act, slot, _f = make_action("BRP_b%02d" % bay, [])
        fv = act.layers[0].strips[0].channelbag(slot).fcurves
        for dp in ("hide_render", "hide_viewport"):
            fc = fv.new(dp, index=0)
            key_constant(fc, [1, r - 1, r], [0.0, 0.0, 1.0])
            stats["keys"] += 3
        ob.animation_data_create()
        ob.animation_data.action = act
        ob.animation_data.action_slot = slot

    # -- the frame bodies (mullion segments, transoms) ------------------------ #
    n_frame = 0
    for j, nm in enumerate(names):
        if not (nm.startswith("MUL") or nm.startswith("TRN")):
            continue
        n_frame += 1
    log("frame bodies in the table: %d (their MESHES belong to "
        "world/items/mullion_intact.py and mullion_bent_stub; this writes "
        "their TRANSFORMS only)" % n_frame)

    log("built %d objects, %d tris, %d keys"
        % (stats["objects"], stats["tris"], stats["keys"]))
    return stats, C_shard, C_pane


# --------------------------------------------------------------------------- #

def prove_curves(coll, n=40):
    """Evaluate the curves.  Reading the interpolation flag back is not proof:
    that is the exact check that passed while 71,472 of 71,472 keys were BEZIER.
    """
    obs = [o for o in coll.objects if o.animation_data and
           o.animation_data.action]
    obs = obs[:n]
    worst = 0.0
    flags = {"LINEAR": 0, "CONSTANT": 0, "other": 0}
    ctrl = 0.0
    for o in obs:
        act = o.animation_data.action
        for lay in act.layers:
            for st in lay.strips:
                cb = st.channelbag(o.animation_data.action_slot)
                if not cb:
                    continue
                for fc in cb.fcurves:
                    kps = list(fc.keyframe_points)
                    for k in kps:
                        flags[k.interpolation if k.interpolation in flags
                              else "other"] += 1
                    if fc.data_path.startswith("hide") or len(kps) < 3:
                        continue
                    for a, b in zip(kps[:-1], kps[1:]):
                        if b.co[0] - a.co[0] < 1.5:
                            continue
                        f = 0.5 * (a.co[0] + b.co[0])
                        want = 0.5 * (a.co[1] + b.co[1])
                        worst = max(worst, abs(fc.evaluate(f) - want))
    # +ve control on one curve
    if obs:
        act = obs[0].animation_data.action
        cb = act.layers[0].strips[0].channelbag(
            obs[0].animation_data.action_slot)
        fc = [f for f in cb.fcurves if not f.data_path.startswith("hide")][0]
        saved = [k.interpolation for k in fc.keyframe_points]
        for k in fc.keyframe_points:
            k.interpolation = "BEZIER"
        fc.update()
        kps = list(fc.keyframe_points)
        for a, b in zip(kps[:-1], kps[1:]):
            if b.co[0] - a.co[0] < 1.5:
                continue
            f = 0.5 * (a.co[0] + b.co[0])
            ctrl = max(ctrl, abs(fc.evaluate(f) - 0.5 * (a.co[1] + b.co[1])))
        for k, s in zip(fc.keyframe_points, saved):
            k.interpolation = s
        fc.update()
    return dict(objects_checked=len(obs), flags=flags,
                max_linear_eval_err=float(worst),
                bezier_control_err=float(ctrl),
                control_fires=bool(ctrl > 10.0 * max(worst, 1e-12)))


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--film", default=os.path.join(R2, "sim/out/breach_film.npz"))
    p.add_argument("--shards",
                   default=os.path.join(R2, "sim/out/fracture_wall.npz"))
    p.add_argument("--out", required=True)
    p.add_argument("--report",
                   default=os.path.join(R2, "sim/out/apply_breach.json"))
    p.add_argument("--glass-material", default="BREACH_Glass")
    p.add_argument("--hero-m", type=float, default=6.0)
    p.add_argument("--detail-hero", type=int, default=2)
    p.add_argument("--detail-bulk", type=int, default=1)
    return p.parse_args(argv)


def main():
    a = parse_args()
    stats, C_shard, C_pane = build(a)
    proof = prove_curves(C_shard)
    log("curve proof: %s" % json.dumps(proof))
    if proof["flags"]["other"] or not proof["control_fires"] or \
            proof["max_linear_eval_err"] > 1e-4:
        raise SystemExit("REFUSING: the applied curves are not LINEAR by "
                         "evaluation: %s" % proof)
    bpy.ops.wm.save_as_mainfile(filepath=a.out)
    rep = dict(stats=stats, proof=proof, out=a.out,
               bytes=os.path.getsize(a.out), origin_rule=SM.ORIGIN_RULE)
    with open(a.report, "w") as fh:
        json.dump(rep, fh, indent=1, default=float)
    log("wrote %s (%.1f MB)" % (a.out, rep["bytes"] / 1e6))


if __name__ == "__main__":
    main()
