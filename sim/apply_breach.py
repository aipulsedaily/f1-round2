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

That frame is ONE frame per bay and both sides key off it — see `bay_swap`.
It used to be two different frames: the pane hid at min(release) over the bay
and each shard appeared at its own release, so nine shards in bays 5 and 7
arrived a frame after the pane covering them had gone.  R2-098.

`sim/verify_breach.py --swap` is the guard, and unlike the four previous
revisions of this sentence, it exists.  It reads the TABLE apply_breach keys
from, so it fires before a 4 GB scene is written rather than after a frame is
rendered, and it carries four controls including a fractured-bay shard that
never releases at all.  It is a table check, not a render-and-diff: what a
diff of frames r-1, r, r+1 would show is dominated by the field's own motion,
which is the shot.

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
from mathutils import Vector                                      # noqa: E402

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
#  WHAT THIS APPLIER NEEDS FROM THE SCENE IT IS POINTED AT
# --------------------------------------------------------------------------- #
#  It does NOT build a target.  `tools/build_film_scene.py` owns the join, and a
#  second joiner would be a second answer to "where is the showroom".  What this
#  publishes is the contract that join has to satisfy, machine-readable, plus a
#  preflight that checks it and REFUSES rather than writing a plausible wrong
#  scene.
#
#  The load-bearing one is R3.  Round 1's east wall is `GW_Right_Glass`, a
#  ZERO-THICKNESS PLANE ON x = 15.000.  This applier supplies the glazing
#  itself — ten panes with the real 11.5 mm laminate make-up, outer face at
#  14.96650 — because `mullion_intact.section()` is explicit that "Glass is at
#  14.96650 / 14.95500, NOT at 15.000" and that nothing in the assembly may sit
#  east of the breach plane.  If the join brings round 1's plane too, the film
#  has two east walls 33.5 mm apart: coplanar-ish transmissive surfaces that
#  z-fight in beat 1 and leave a ghost pane hanging in the aperture for the rest
#  of the take.  So the plane must be removed, and the 33.5 mm move is a real,
#  intended change to beat 1's reflections that somebody should look at.

REQUIREMENTS = dict(
    R1=dict(id="frame_range", need="scene.frame_start == 1 and frame_end == "
                                   "2978 at 24 fps",
            why="every curve written here is keyed in film frames and "
                "extrapolates CONSTANT to the last one"),
    R2=dict(id="units_metres", need="scene.unit_settings.scale_length == 1.0",
            why="every transform in the bake is world metres"),
    R3=dict(id="no_round1_east_glass",
            need="DELETE the ten objects GW_Right_Glass_00 .. GW_Right_Glass_09"
                 " (4 verts each, zero-thickness planes on x = 15.000) from "
                 "world/verify_showroom.blend before applying.  Measured "
                 "2026-08-03; everything else in that file stays.",
            correspondence="round 1's ten panes are this module's ten bays, "
                           "one for one: GW_Right_Glass_04 is y -2.1625.. "
                           "-0.0375, bay 4 is y -2.1850..-0.0150.  Round 1 cut "
                           "them to the CLEAR OPENING (2.125 x 5.980); this "
                           "module cuts them to the CUT SIZE (2.170 x 6.025), "
                           "bigger by exactly the 22.5 mm hidden edge on all "
                           "four sides that glazing_pockets() specifies.  That "
                           "agreement was not arranged and is the best "
                           "independent check that these rects are right.",
            visible_change="the glass surface the camera sees moves 33.5 mm "
                           "INBOARD, from a zero-thickness plane on 15.000 to "
                           "an 11.5 mm laminate at 14.96650/14.95500.  Beat 1 "
                           "spends 33 s looking at its reflections and "
                           "somebody should look at that change on purpose.",
            why="this applier supplies that glazing at 14.95500..14.96650 "
                "with real thickness; two east walls 33.5 mm apart z-fight in "
                "beat 1 and leave a ghost pane in the aperture afterwards",
            note="GW_Front_Glass (the SOUTH wall, y = -11.000) is NOT ours "
                 "and must stay"),
    R4=dict(id="floor_top_z_zero",
            need="showroom floor top at z = 0.000 and forecourt top at "
                 "z = 0.000 for x in [15, 46], |y| <= 14",
            why="the shards' resting transforms were baked against those two "
                "planes; a floor 20 mm low leaves 3,796 shards hovering"),
    R5=dict(id="glazing_pocket_clear",
            need="nothing occupying x 14.945..14.970 between z 0.0865 and "
                 "6.1125 across the ten bays",
            why="that is the pocket the glass lives in; a solid mullion or "
                "sill laid through it starts every clamped shard inside "
                "metal, which is exactly what the null control caught"),
    R6=dict(id="frame_transform_binding",
            need="whoever meshes mullion_intact / mullion_bent_stub / "
                 "curtain_wall_transom binds to the MUL*/TRN* names in "
                 "sim/out/breach_film.npz",
            why="this module writes those bodies' TRANSFORMS; their geometry "
                "belongs to world/items/"),
    R7=dict(id="no_parent_on_breach",
            need="the BREACH collection is not parented or offset",
            why="the keys are absolute world transforms, not local"),
)

# Objects that supply round 1's east wall.  Matched by name AND by geometry, so
# a rename does not silently defeat the check.
R1_EAST_GLASS_HINTS = ("GW_Right_Glass",)
R1_EAST_GLASS_MEASURED = ["GW_Right_Glass_%02d" % i for i in range(10)]


def requirements_json(path=None):
    path = path or os.path.join(R2, "sim", "out", "apply_requirements.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(dict(module="sim/apply_breach.py",
                       requirements=REQUIREMENTS,
                       breach_plane_x=15.0,
                       delete_from_target=R1_EAST_GLASS_MEASURED,
                       target_measured="world/verify_showroom.blend, "
                                       "949 objects, 2026-08-03",
                       glass_faces_x=[GLASS_X_IN, GLASS_X_OUT],
                       supplies=["GP_b00..GP_b09 (ten panes)",
                                 "GS_b*_* (the shards)"],
                       consumes=["sim/out/breach_film.npz",
                                 "sim/out/fracture_wall.npz"],
                       origin_rule=SM.ORIGIN_RULE), fh, indent=1)
    return path


def _world_aabb(o):
    """World-space AABB from the object's 8 bound-box corners.  Cheap: 8 points
    per object regardless of mesh size."""
    import numpy as _np
    bb = _np.array([tuple(o.matrix_world @ Vector(c)) for c in o.bound_box])
    return bb.min(axis=0), bb.max(axis=0)


def _world_verts(o):
    """All vertices in world space, via foreach_get and ONE matrix multiply.

    NOT `[o.matrix_world @ v.co for v in o.data.vertices]`.  That is a Python
    loop per vertex, and the scene this has to check is 28,781 objects and
    1.28e9 vertices — the loop version does not finish, ever, which meant R5
    was uncheckable by the very tool that publishes it.
    """
    n = len(o.data.vertices)
    flat = np.empty(3 * n, dtype=np.float32)
    o.data.vertices.foreach_get("co", flat)
    V = flat.reshape(n, 3).astype(np.float64)
    m = np.array(o.matrix_world)
    return V @ m[:3, :3].T + m[:3, 3]


def _aabb_hits(lo, hi, box_lo, box_hi):
    return bool(np.all(hi >= np.asarray(box_lo))
                and np.all(lo <= np.asarray(box_hi)))


def preflight(scene, strict=True):
    """Check what can be checked in the target scene.  Refuse, do not adapt."""
    import bpy as _b
    out = {"checks": [], "ok": True}

    def chk(rid, cond, detail=""):
        out["checks"].append(dict(id=REQUIREMENTS[rid]["id"], passed=bool(cond),
                                  detail=detail,
                                  why=REQUIREMENTS[rid]["why"]))
        if not cond:
            out["ok"] = False

    total = int(json.load(open(BL.SHEET))["total_frames"])
    chk("R1", scene.frame_end >= total,
        "frame_end = %d, need >= %d" % (scene.frame_end, total))
    chk("R2", abs(scene.unit_settings.scale_length - 1.0) < 1e-9,
        "scale_length = %s" % scene.unit_settings.scale_length)

    # R3: anything that looks like round 1's east wall — by name OR by being a
    # flat object standing on x = 15.000 over the wall's own y/z extent
    sus = []
    scanned = 0
    for o in scene.objects:
        if any(h in o.name for h in R1_EAST_GLASS_HINTS):
            sus.append((o.name, "name"))
            continue
        if o.type != "MESH" or o.data is None or not len(o.data.vertices):
            continue
        scanned += 1
        lo, hi = _world_aabb(o)          # 8 corners, not every vertex
        if (abs(lo[0] - 15.0) < 0.02 and hi[0] - lo[0] < 0.02
                and hi[1] - lo[1] > 8.0 and hi[2] - lo[2] > 4.0):
            sus.append((o.name, "a flat object on x = 15.000, %.2f x %.2f m"
                        % (hi[1] - lo[1], hi[2] - lo[2])))
    out["meshes_scanned"] = scanned
    chk("R3", not sus, "found %d: %s" % (len(sus), sus[:4]) if sus else "clear")

    # R5: nothing in the glazing pocket
    # THE POCKET: x 14.945..14.970, z 0.0865..6.1125, |y| < 11.  Two stages,
    # because the target is 4.5 GB and a per-vertex sweep of it does not
    # terminate: reject on the world AABB first (8 corners an object), then
    # test vertices only for the handful that survive.
    POCKET_LO = (14.9455, -11.0, 0.0870)
    POCKET_HI = (14.9695, 11.0, 6.1120)
    intr = []
    cand = 0
    for o in scene.objects:
        if o.type != "MESH" or o.data is None or not len(o.data.vertices):
            continue
        if o.name.startswith(("GP_b", "GS_b")):
            continue
        lo, hi = _world_aabb(o)
        if not _aabb_hits(lo, hi, POCKET_LO, POCKET_HI):
            continue
        cand += 1
        V = _world_verts(o)
        m = ((V[:, 0] > POCKET_LO[0]) & (V[:, 0] < POCKET_HI[0])
             & (V[:, 2] > POCKET_LO[2]) & (V[:, 2] < POCKET_HI[2])
             & (np.abs(V[:, 1]) < 11.0))
        if m.any():
            intr.append((o.name, int(m.sum())))
    out["pocket_aabb_candidates"] = cand
    chk("R5", not intr, "found %d: %s" % (len(intr), intr[:4]) if intr
        else "clear")
    return out


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

    # -- THE ONE FRAME EACH BAY SWAPS ON.  R2-098. ---------------------------- #
    # This used to be computed twice, differently.  The intact PANE hid at
    # min(release) over its bay; each SHARD appeared at ITS OWN release.  Those
    # are not the same frame, and between them nothing renders at all: in the
    # shipped table, 9 shards in bays 5 and 7 arrive one frame after the pane
    # covering them has gone.  A hole, in a film with no cuts.
    #
    # One frame and nine shards is small, and it was small BY LUCK -- the gap is
    # bounded by the spread of release frames inside a bay and nothing enforced
    # that spread.  A bay whose corner lets go twelve frames after its centre
    # would have shown twelve frames of the plaza through the wall.
    #
    # So the swap frame is now computed ONCE, per bay, and BOTH sides key off
    # it.  A shard that has not moved yet at `r_bay` simply renders at its home
    # transform, which is where the pane's glass was: identical silhouette,
    # nothing to see.  `sim/verify_breach.py --swap` is the guard, and it has
    # four controls.
    bay_swap = {}
    for i, (bay, s, nm, j) in enumerate(keyset):
        r = int(rel[j])
        if r > span[0]:
            bay_swap[bay] = min(bay_swap.get(bay, r), r)
    log("swap frames per bay (R2-098: ONE frame per bay, both sides): %s"
        % json.dumps({str(k): v for k, v in sorted(bay_swap.items())}))

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
        # visibility: hidden until THIS BAY's pane hides, not until this shard
        # personally moves.  R2-098 -- see `bay_swap` above.
        r = int(bay_swap.get(bay, -1))
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
        # R2-098: the SAME frame the shards use.  Computed once, above.
        r = int(bay_swap.get(bay, -1))
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

def east_wall_census(plan, at_frame=1):
    """IS THERE ANY GLASS IN THE EAST WALL AT ALL?

    Defect number PENDING.  The block issued to the breach, R2-092..R2-099,
    was fully consumed by the eight findings inherited with this work, and
    R2-100 was claimed by another agent while this was being written.  The
    log's owner assigns it; this note is here so the citation is not silently
    wrong.

    This check exists because the answer was NO, in the shipping film, for
    beats 1 to 3 — roughly a third of a film that has no cuts to hide it in.

    HOW THAT HAPPENED, since no single step was wrong.  `tools/build_film_scene`
    executes this module's own requirement R3 and deletes round 1's ten
    `GW_Right_Glass_*` planes.  It is right to: they are zero-thickness, they
    sit 33.5 mm proud of where the glass really is, and two east walls that
    close together z-fight through beat 1.  R3 is written on the understanding
    that THIS module supplies the replacement — and it does, all ten bays,
    including the four the car never touches.  But this module is a SEPARATE
    invocation on an already-built blend, and the joiner has no way to know
    whether it was ever run.  So every time the world is rebuilt, the film comes
    out of the joiner with the panes deleted and nothing put back, and stays
    that way until somebody remembers to re-apply.  It shipped that way twice.

    The count that was being watched, `n_GW_Right_Glass`, is a name-prefix query
    for round 1's names.  It reads 0 for a correctly applied scene as well as
    for an empty wall, because the replacements are called `GP_b*`.  A metric
    that cannot tell the fixed state from the broken one was never going to
    raise this.

    So: count the glazing that is actually THERE and visible at `at_frame`,
    by bay, and refuse on an empty wall.
    """
    want = sorted(plan["panes"])
    got, hidden, missing = [], [], []
    for bay in want:
        ob = bpy.data.objects.get("GP_b%02d" % bay)
        if ob is None:
            missing.append(bay)
            continue
        got.append(bay)
        # hide_render may be animated; ask the curve, not the current value.
        h = ob.hide_render
        ad = ob.animation_data
        if ad and ad.action:
            for lay in ad.action.layers:
                for st in lay.strips:
                    cb = st.channelbag(ad.action_slot)
                    if not cb:
                        continue
                    for fc in cb.fcurves:
                        if fc.data_path == "hide_render":
                            h = fc.evaluate(at_frame) > 0.5
        if h:
            hidden.append(bay)
    shards = len([o for o in bpy.data.objects if o.name.startswith("GS_b")])
    r1 = [o.name for o in bpy.data.objects
          if o.name.startswith("GW_Right_Glass")]
    return dict(
        criterion="the east wall must contain glass at frame %d: every bay in "
                  "the plan has a GP_b* pane and it is not hidden there"
                  % at_frame,
        bays_wanted=want, panes_built=got, panes_missing=missing,
        panes_hidden_at_frame=hidden, shards=shards,
        round1_planes_still_present=r1,
        note="n_GW_Right_Glass counts ROUND 1's names and reads 0 for a "
             "correct scene as well as an empty one.  Count GP_b*.",
        PASS=bool(not missing and not hidden and not r1))


def census_selftest():
    """The east-wall census against four synthetic scenes.  Cheap: it builds
    ten 4-vert boxes in an empty file, so it does not need a 5 GB blend.

        blender -b --factory-startup -P sim/apply_breach.py -- --selftest
    """
    fails = []

    def check(name, cond, detail=""):
        print("  %-62s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        if not cond:
            fails.append(name)

    plan = dict(panes={b: [] for b in range(10)})

    def rebuild():
        for o in list(bpy.data.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        for b in range(10):
            me = bpy.data.meshes.new("GP_b%02d" % b)
            me.from_pydata([(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)], [],
                           [[0, 1, 2, 3]])
            me.update()
            bpy.context.scene.collection.objects.link(
                bpy.data.objects.new("GP_b%02d" % b, me))

    rebuild()
    c0 = east_wall_census(plan)
    check("-ve control: ten panes, none hidden, is a wall",
          c0["PASS"] and len(c0["panes_built"]) == 10, str(c0["panes_missing"]))

    rebuild()
    bpy.data.objects.remove(bpy.data.objects["GP_b04"], do_unlink=True)
    c1 = east_wall_census(plan)
    check("+ve control: one missing pane is caught",
          (not c1["PASS"]) and c1["panes_missing"] == [4],
          str(c1["panes_missing"]))

    rebuild()
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    c2 = east_wall_census(plan)
    check("+ve control: THE DEFECT ITSELF -- no east glazing at all is caught",
          (not c2["PASS"]) and len(c2["panes_missing"]) == 10,
          "%d missing" % len(c2["panes_missing"]))

    rebuild()
    ob = bpy.data.objects["GP_b02"]
    act, slot, _f = make_action("CENSUS_TEST", [])
    fc = act.layers[0].strips[0].channelbag(slot).fcurves.new("hide_render",
                                                              index=0)
    key_constant(fc, [1, 40], [1.0, 0.0])
    ob.animation_data_create()
    ob.animation_data.action = act
    ob.animation_data.action_slot = slot
    c3 = east_wall_census(plan, at_frame=1)
    c4 = east_wall_census(plan, at_frame=41)
    check("+ve control: a pane that EXISTS but is hidden at frame 1 is caught",
          (not c3["PASS"]) and c3["panes_hidden_at_frame"] == [2],
          str(c3["panes_hidden_at_frame"]))
    check("-ve control: the same pane visible at frame 41 is not charged",
          c4["PASS"], str(c4["panes_hidden_at_frame"]))

    rebuild()
    me = bpy.data.meshes.new("GW_Right_Glass_00")
    me.from_pydata([(0, 0, 0), (0, 1, 0), (0, 1, 1)], [], [[0, 1, 2]])
    me.update()
    bpy.context.scene.collection.objects.link(
        bpy.data.objects.new("GW_Right_Glass_00", me))
    c5 = east_wall_census(plan)
    check("+ve control: a surviving round-1 plane is caught (it z-fights)",
          (not c5["PASS"]) and c5["round1_planes_still_present"],
          str(c5["round1_planes_still_present"]))

    print("\nSTAGE RESULT: census selftest %s (%d failed)"
          % ("FAIL" if fails else "PASS", len(fails)))
    return 1 if fails else 0


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
    p.add_argument("--out", default="")
    p.add_argument("--report",
                   default=os.path.join(R2, "sim/out/apply_breach.json"))
    p.add_argument("--glass-material", default="BREACH_Glass")
    p.add_argument("--hero-m", type=float, default=6.0)
    p.add_argument("--detail-hero", type=int, default=2)
    p.add_argument("--detail-bulk", type=int, default=1)
    p.add_argument("--selftest", action="store_true",
                   help="the east-wall census against six synthetic scenes. "
                        "Needs no target blend.")
    p.add_argument("--preflight-only", action="store_true",
                   help="report what this scene would need and write nothing")
    p.add_argument("--force", action="store_true",
                   help="apply even though preflight failed.  Deliberate, "
                        "logged, and never the default.")
    return p.parse_args(argv)


def main():
    a = parse_args()
    if a.selftest:
        sys.exit(census_selftest())
    rq = requirements_json()
    pre = preflight(bpy.context.scene)
    log("requirements published to %s" % rq)
    for c in pre["checks"]:
        log("  preflight %-24s %s  %s"
            % (c["id"], "PASS" if c["passed"] else "FAIL", c["detail"]))
    if a.preflight_only:
        with open(a.report, "w") as fh:
            json.dump(dict(preflight=pre, requirements=REQUIREMENTS,
                           scene=bpy.data.filepath), fh, indent=1)
        log("preflight-only: wrote %s" % a.report)
        return
    if not pre["ok"] and not a.force:
        raise SystemExit(
            "REFUSING: the target scene does not satisfy this applier's "
            "requirements (see %s).  Writing into it would produce a scene "
            "that looks right and is not.  --force to override deliberately."
            % rq)
    stats, C_shard, C_pane = build(a)
    proof = prove_curves(C_shard)
    log("curve proof: %s" % json.dumps(proof))
    if proof["flags"]["other"] or not proof["control_fires"] or \
            proof["max_linear_eval_err"] > 1e-4:
        raise SystemExit("REFUSING: the applied curves are not LINEAR by "
                         "evaluation: %s" % proof)
    east = east_wall_census(FR.load(a.shards))
    log("east wall census: %s" % json.dumps(east, default=float))
    if not east["PASS"] and not a.force:
        raise SystemExit(
            "REFUSING: after applying, the east wall does not contain glass "
            "at frame 1: missing %s, hidden %s, round-1 planes still present "
            "%s.  Beats 1-3 are the showroom and would render an open wall."
            % (east["panes_missing"], east["panes_hidden_at_frame"],
               east["round1_planes_still_present"]))
    bpy.ops.wm.save_as_mainfile(filepath=a.out)
    rep = dict(stats=stats, proof=proof, preflight=pre, east_wall=east,
               out=a.out,
               bytes=os.path.getsize(a.out), origin_rule=SM.ORIGIN_RULE)
    with open(a.report, "w") as fh:
        json.dump(rep, fh, indent=1, default=float)
    log("wrote %s (%.1f MB)" % (a.out, rep["bytes"] / 1e6))


if __name__ == "__main__":
    main()
