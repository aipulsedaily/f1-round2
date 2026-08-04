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
import eastframe as EF                                            # noqa: E402
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
            need="round 1's GW_Right_Mull_* / GW_Right_Transom_* are present "
                 "and unmodified, so this module can cut them into the pieces "
                 "the bake moves.  SATISFIED BY THIS MODULE since 2026-08-04 "
                 "(R2-266): `sim/eastframe.py` binds geometry to the MUL*/TRN* "
                 "names in sim/out/breach_film.npz.",
            why="R6 asked somebody else to do this and for four film builds "
                "nobody did, so build() counted 152 frame bodies and wrote "
                "none of them: the film rendered a static, undeformed "
                "aluminium grid straight across a 2.15 x 6.00 m hole for the "
                "whole take.  Naming a requirement is not the same as meeting "
                "it, and a count that is printed and then discarded looks "
                "exactly like a count that was used."),
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


def _tris_hit_box(V, loops, box_lo, box_hi):
    """Do any of this mesh's TRIANGLES intersect the axis-aligned box?

    Exact, by the separating-axis theorem (Akenine-Moller): 3 box axes, the
    triangle's own normal, and the 9 edge-cross-products.  Vectorised over all
    triangles at once.

    WHY NOT VERTICES, AND WHY NOT EDGES.  The pocket is a 24 mm slab in x.
    Round 1's east mullion is a solid box spanning x 14.920..15.080 -- through
    the slab -- with all eight vertices outside it (a vertex test sees
    nothing) AND all twelve edges outside it, because the x-running edges sit
    at z = 0.0 and z = 6.2, beyond the pocket's z range, and the z-running
    edges sit at x = 14.920 and 15.080, beyond its x range.  What passes
    through the pocket is the mullion's SIDE FACES.  A solid is not its
    vertices and it is not its edges either.
    """
    if not len(loops):
        return 0
    tri = []
    for f in loops:
        for k in range(1, len(f) - 1):
            tri.append((f[0], f[k], f[k + 1]))
    if not tri:
        return 0
    T = V[np.asarray(tri, np.int32)]                       # (n,3,3)
    c = 0.5 * (np.asarray(box_lo) + np.asarray(box_hi))
    h = 0.5 * (np.asarray(box_hi) - np.asarray(box_lo))
    T = T - c                                              # box at origin
    ok = np.ones(len(T), bool)
    # 3 box axes
    for ax in range(3):
        ok &= ~((T[:, :, ax].min(1) > h[ax]) | (T[:, :, ax].max(1) < -h[ax]))
    E = np.stack([T[:, 1] - T[:, 0], T[:, 2] - T[:, 1], T[:, 0] - T[:, 2]], 1)
    # the triangle's own plane
    N = np.cross(E[:, 0], E[:, 1])
    d = (N * T[:, 0]).sum(-1)
    r = (np.abs(N) * h).sum(-1)
    ok &= np.abs(d) <= r
    # 9 edge cross products
    for i in range(3):
        for j in range(3):
            a = np.zeros((len(T), 3))
            a[:, (j + 1) % 3] = -E[:, i, (j + 2) % 3]
            a[:, (j + 2) % 3] = E[:, i, (j + 1) % 3]
            pr = (T * a[:, None, :]).sum(-1)
            rr = (np.abs(a) * h).sum(-1)
            ok &= ~((pr.min(1) > rr) | (pr.max(1) < -rr))
    return int(ok.sum())


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
    # the CLEAR OPENINGS: each bay's cut size inset by the 22.5 mm edge that is
    # meant to be captured in the mullion.
    # 22.5 mm of captured edge, plus 1 mm so that a member whose face lands
    # EXACTLY on the clear-opening boundary is not charged with obstructing it.
    # The separating-axis test counts touching as intersecting, correctly, and
    # round 1's mullion face sits exactly on bay 4's clear edge at y = -0.0375.
    EDGE = 0.0225 + 0.001
    try:
        _plan = FR.load(os.path.join(R2, "sim/out/fracture_wall.npz"))
        clear_rects = {b: (r[0] + EDGE, r[1] - EDGE, r[2] + EDGE, r[3] - EDGE)
                       for b, r in _plan["rects"].items()}
    except Exception:                                          # noqa: BLE001
        clear_rects = {0: (-11.0 + EDGE, 11.0 - EDGE,
                           0.0870 + EDGE, 6.1120 - EDGE)}
    intr, captured = [], []
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
        n_in = int(m.sum())
        # A VERTEX TEST IS VACUOUS AGAINST THE THING IT WAS WRITTEN FOR.
        # The pocket is 24 mm deep in x.  Round 1's east mullions are solid
        # boxes spanning x 14.920..15.080 -- straight THROUGH the pocket --
        # and their eight vertices are all OUTSIDE it, four at 14.920 and four
        # at 15.080.  So `V inside pocket` is empty and R5 reported "clear" on
        # 29,387 meshes with eleven aluminium bars lying through the glass.
        # A solid is not its vertices.
        #
        # The fix is to test the EDGES as segments against the pocket box.  A
        # convex member that straddles a 24 mm slab must have an edge crossing
        # it, which is exactly the case the vertex test cannot see.  Slab
        # method, vectorised over all edges at once.
        loops = [list(pl.vertices) for pl in o.data.polygons]
        n_tri = _tris_hit_box(V, loops,
                              (POCKET_LO[0], -11.0, POCKET_LO[2]),
                              (POCKET_HI[0], 11.0, POCKET_HI[2]))
        if not (n_in or n_tri):
            continue
        # THROUGH THE GLASS, OR CAPTURING ITS EDGE?  These are not the same
        # thing and only one of them is a defect.
        #
        # Every pane is cut 22.5 mm oversize on all four sides -- the CUT SIZE
        # 2.170 x 6.025 against the CLEAR OPENING 2.125 x 5.980 -- and that
        # 22.5 mm is MEANT to be buried in the mullion.  That is what a glazing
        # pocket IS.  So a member that meets the pocket only inside the capture
        # band is doing its job, and refusing on it would refuse on correctly
        # glazed glass.  A member that reaches into the CLEAR OPENING is
        # standing in front of the picture.
        #
        # So the test is run again against the clear openings alone, and only
        # that arm can refuse.  The capture-band hits are reported, loudly,
        # because they are how you find out WHICH frame is in the scene.
        n_clear = 0
        for _b, (_u0, _u1, _v0, _v1) in clear_rects.items():
            n_clear += _tris_hit_box(V, loops,
                                     (POCKET_LO[0], _u0, _v0),
                                     (POCKET_HI[0], _u1, _v1))
            if n_clear:
                break
        if n_clear:
            intr.append((o.name, n_in, n_tri, n_clear))
        else:
            captured.append((o.name, n_tri))
    out["pocket_aabb_candidates"] = cand
    out["pocket_intruders_in_the_clear_opening"] = [list(x) for x in intr]
    out["pocket_capture_band_only"] = [list(x) for x in sorted(captured)[:20]]
    out["pocket_capture_band_only_n"] = len(captured)
    out["R5_measures"] = ("vertices inside the pocket, AND triangles "
                          "intersecting it by the separating-axis theorem. "
                          "The triangle arm exists because round 1's east "
                          "mullions pass through the pocket with every vertex "
                          "AND every edge outside it -- it is their side FACES "
                          "that cross -- and the vertex-only test reported "
                          "`clear` on 29,387 meshes.")
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
    # THIS LOOP USED TO COUNT THEM AND WRITE NOTHING.  R2-266.
    frame = build_frame(args, film, C_frame)
    stats["objects"] += frame["objects"]
    stats["keys"] += frame["keys"]
    stats["frame"] = frame

    log("built %d objects, %d tris, %d keys"
        % (stats["objects"], stats["tris"], stats["keys"]))
    return stats, C_shard, C_pane, C_frame


# --------------------------------------------------------------------------- #

def build_frame(args, film, coll):
    """Round 1's east frame, cut into the bake's own pieces and keyed.

    The geometry is round 1's, to the vertex — see `sim/eastframe.py` for why
    it is not the section's, and for the 80 mm / 250 mm the two disagree by.
    What this adds is the PARTITION and the MOTION.

    THERE IS NO SWAP AND NOTHING HIDES.  Every piece exists on all 2,978
    frames.  Before its first key the F-curve extrapolates CONSTANT backwards
    to the home pose, which is exactly where round 1's solid stood, so beat 1
    and beat 2 are unchanged by construction rather than by a keyed visibility
    that somebody has to get right.  That is a stronger continuity guarantee
    than the glass gets, and it is available here only because a mullion does
    not have to stop being one object and start being 3,796.
    """
    if args.no_frame:
        log("--no-frame: round 1's static grid is left standing across the "
            "aperture.  This is the shipped defect, kept as a control.")
        return dict(objects=0, keys=0, skipped=True)

    names = film["names"]
    idx = {n: i for i, n in enumerate(names)}
    home = np.array([film["keys_of"](i)[1][0] for i in range(len(names))],
                    float)
    pl = EF.plan(names, film["release"], home)
    cov = EF.coverage(pl)
    if not cov["PASS"]:
        raise SystemExit(
            "REFUSING: the east-frame plan does not tile round 1's members: "
            "%s.  Writing it would delete aluminium and not put it back, "
            "which is exactly how R2-124 shipped." % json.dumps(cov))

    mat = bpy.data.materials.get(EF.R1_MATERIAL)
    if mat is None:
        raise SystemExit(
            "REFUSING: material %r is not in this scene.  It is round 1's, it "
            "is what every other east-wall member is shaded with, and "
            "inventing a lookalike would put two aluminiums in one elevation."
            % EF.R1_MATERIAL)

    # ---- delete round 1's unbroken solids ---------------------------------
    gone, absent = [], []
    for nm in pl["delete"]:
        ob = bpy.data.objects.get(nm)
        if ob is None:
            absent.append(nm)
            continue
        bpy.data.objects.remove(ob, do_unlink=True)
        gone.append(nm)
    if absent:
        raise SystemExit(
            "REFUSING: %s not in the target scene.  This module replaces "
            "round 1's east frame; if it is already missing then something "
            "else has taken it and the two answers would both be in the "
            "elevation." % absent)

    # ---- build the pieces -------------------------------------------------
    n_obj = n_keys = 0
    div = []
    for p in pl["pieces"]:
        V, F = EF.box_mesh(p["boxes"], p["pivot"])
        me = bpy.data.meshes.new(p["name"])
        me.from_pydata(V, [], F)
        me.validate(verbose=False)
        me.update()
        me.materials.append(mat)
        ob = bpy.data.objects.new(p["name"], me)
        coll.objects.link(ob)
        ob.rotation_mode = "QUATERNION"
        ob.location = tuple(p["pivot"])
        n_obj += 1
        if p["driver"] is None:
            continue
        j = idx[p["driver"]]
        fk, kl, kq = film["keys_of"](j)
        act, slot, fcs = make_action("BF_%s" % p["name"],
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
        n_keys += 7 * len(fk)
        ob.animation_data_create()
        ob.animation_data.action = act
        ob.animation_data.action_slot = slot
        # THE COVER CAP IS ITS OWN BODY IN THE SIM AND ROUND 1'S IS NOT.
        # Every mullion and transom is TWO bodies in the bake — the extrusion
        # `X` and the pressure plate `X_P`, joined at ten times the mullion's
        # own threshold.  Round 1's member is one 160 mm solid, so it can only
        # follow one of them, and it follows the extrusion.  Measure how far
        # the two part company so the error is a number and not a shrug.
        pj = idx.get(p["driver"] + "_P")
        if pj is not None:
            f2, l2, _q2 = film["keys_of"](pj)
            fu = np.union1d(fk, f2)

            def _ev(f, l):
                if len(f) == 1:
                    return np.repeat(l, len(fu), axis=0)
                i = np.searchsorted(f, fu).clip(1, len(f) - 1)
                a = ((fu - f[i - 1]) /
                     np.maximum(f[i] - f[i - 1], 1e-9)).clip(0.0, 1.0)
                return l[i - 1] * (1 - a)[:, None] + l[i] * a[:, None]

            d = np.linalg.norm((_ev(f2, l2) - _ev(fk, kl))
                               - (l2[0] - kl[0]), axis=1).max()
            div.append((p["driver"], float(d)))
    div.sort(key=lambda t: -t[1])

    trav = {}
    for p in pl["pieces"]:
        if p["driver"] is None:
            continue
        _f, l, _q = film["keys_of"](idx[p["driver"]])
        trav[p["name"]] = float(np.linalg.norm(l - l[0], axis=1).max())

    rep = dict(objects=n_obj, keys=n_keys,
               deleted=gone, coverage=cov,
               mullions_replaced=pl["mullions_replaced"],
               n_transom_pieces=len([p for p in pl["pieces"]
                                     if p["kind"] == "transom"]),
               max_travel_m={k: round(v, 4) for k, v in
                             sorted(trav.items(), key=lambda t: -t[1])[:8]},
               cap_divergence_m=[[n, round(v, 4)] for n, v in div[:5]],
               measured_from=pl["measured_from"], rule=pl["rule"])
    log("east frame: deleted %d round-1 solids, built %d pieces, %d keys; "
        "worst travel %s"
        % (len(gone), n_obj, n_keys, json.dumps(rep["max_travel_m"])))
    return rep


def frame_census(film, at_frame=1):
    """IS THE EAST WALL'S ALUMINIUM ALL THERE, IN THE SCENE, AT `at_frame`?

    The plan-level check in `eastframe.coverage` proves the ARITHMETIC tiles.
    This one proves the SCENE does — it reads the objects back out of
    `bpy.data` after they have been built, which is the step that R2-124 shows
    nobody had between "the module supplies it" and "the film has it".

    It counts `BF_*` and round 1's survivors together, because either alone
    reads the same for a correct scene and a stripped one.
    """
    names = film["names"]
    home = np.array([film["keys_of"](i)[1][0] for i in range(len(names))],
                    float)
    pl = EF.plan(names, film["release"], home)
    want = {p["name"] for p in pl["pieces"]}
    have = {o.name for o in bpy.data.objects if o.name.startswith(EF.PIECE_PREFIX)}
    stale = [n for n in pl["delete"] if bpy.data.objects.get(n) is not None]
    survivors = [n for n in pl["untouched"] if n.startswith("GW_Right_Mull_")
                 and bpy.data.objects.get(n) is None]
    # aluminium visible in the wall plane at `at_frame`, by z band, as a
    # crude but PRESENT-vs-ABSENT quantity: total y-length of transom at each
    # level, taken from the objects themselves
    lens = {}
    for lvl in range(len(EF.R1_TRANSOM_Z)):
        tot = 0.0
        for o in bpy.data.objects:
            if not o.name.startswith("%sTRN%d" % (EF.PIECE_PREFIX, lvl)):
                continue
            V = np.array([tuple(o.matrix_world @ Vector(v.co))
                          for v in o.data.vertices])
            # only pieces still at home count toward the intact length
            tot += float(V[:, 1].max() - V[:, 1].min())
        lens["transom_%d_total_y_m" % lvl] = round(tot, 4)
    return dict(
        criterion="every piece eastframe.plan() names is an object in the "
                  "scene, every round-1 solid it replaces is gone, and every "
                  "mullion it does NOT replace is still there",
        pieces_wanted=len(want), pieces_built=len(want & have),
        pieces_missing=sorted(want - have),
        round1_solids_not_deleted=stale,
        untouched_mullions_missing=survivors,
        transom_length=lens,
        note="counting GW_Right_Transom_* would read 0 for a correct scene "
             "and 0 for a stripped one.  R2-124.",
        PASS=bool(not (want - have) and not stale and not survivors))


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

    # ---- R5, THE POCKET, AND THE VERTEX TEST THAT COULD NOT SEE A BOX ---- #
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)

    def box(name, x0, x1, y0, y1, z0, z1):
        me = bpy.data.meshes.new(name)
        V = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        F = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1],
             [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
        me.from_pydata(V, [], F)
        me.validate(verbose=False)
        me.update()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob

    # ROUND 1'S ACTUAL EAST MULLION: solid, x 14.920..15.080, straight through
    # the 24 mm pocket, and not one vertex inside it.
    ob = box("GW_Right_Mull_05", 14.920, 15.080, -0.0375, 0.0375, 0.0, 6.2)
    V = _world_verts(ob)
    inside = ((V[:, 0] > 14.9455) & (V[:, 0] < 14.9695)).sum()
    pre = preflight(bpy.context.scene, strict=False)
    r5 = [c for c in pre["checks"] if c["id"] == "glazing_pocket_clear"][0]
    check("+ve control: a SOLID BOX through the pocket with ZERO vertices "
          "inside it is SEEN", (inside == 0) and (
              pre.get("pocket_capture_band_only_n", 0)
              + len(pre.get("pocket_intruders_in_the_clear_opening", []))) == 1,
          "%d verts inside, seen=%s"
          % (inside, pre.get("pocket_capture_band_only")))

    # ...and the same box moved 200 mm INTO bay 4 is a bar across the picture.
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    box("Bar_across_bay4", 14.920, 15.080, -1.30, -1.20, 0.0, 6.2)
    pre = preflight(bpy.context.scene, strict=False)
    r5 = [c for c in pre["checks"] if c["id"] == "glazing_pocket_clear"][0]
    check("+ve control: a bar across the middle of bay 4 is caught",
          not r5["passed"],
          str(pre.get("pocket_intruders_in_the_clear_opening")))

    # THE DISCRIMINATION THAT MATTERS: round 1's mullion sits ON a bay
    # boundary, so it meets the pocket only in the 22.5 mm capture band.  That
    # is a glazing pocket doing its job and it must NOT refuse -- but it must
    # be REPORTED, because it is how you find out which frame is in the scene.
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    box("GW_Right_Mull_05", 14.920, 15.080, -0.0375, 0.0375, 0.0, 6.2)
    pre = preflight(bpy.context.scene, strict=False)
    r5 = [c for c in pre["checks"] if c["id"] == "glazing_pocket_clear"][0]
    check("-ve/report: a mullion ON a bay boundary captures the edge, does "
          "not refuse, and IS reported",
          r5["passed"] and pre.get("pocket_capture_band_only_n") == 1,
          "capture-band %s" % pre.get("pocket_capture_band_only"))

    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    box("Bar_east_of_the_pocket", 14.980, 15.080, -1.0, 1.0, 0.0, 6.2)
    pre = preflight(bpy.context.scene, strict=False)
    r5 = [c for c in pre["checks"] if c["id"] == "glazing_pocket_clear"][0]
    check("-ve control: a bar entirely EAST of the pocket is not charged",
          r5["passed"] and not pre.get("pocket_capture_band_only_n"),
          str(pre.get("pocket_capture_band_only")))

    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    box("Bar_below_the_pocket", 14.90, 15.08, -1.0, 1.0, -1.0, 0.080)
    pre = preflight(bpy.context.scene, strict=False)
    r5 = [c for c in pre["checks"] if c["id"] == "glazing_pocket_clear"][0]
    check("-ve control: a bar below the pocket's z range is not charged",
          r5["passed"] and not pre.get("pocket_capture_band_only_n"),
          str(pre.get("pocket_capture_band_only")))

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
    p.add_argument("--no-frame", action="store_true",
                   help="do NOT supply the east frame; leave round 1's static "
                        "grid standing across the aperture.  This reproduces "
                        "the shipped defect and exists to be a control, not a "
                        "fallback.")
    return p.parse_args(argv)


def main():
    a = parse_args()
    if a.selftest:
        print("--- sim/eastframe.py (the east frame plan, no bpy) ---")
        rc = EF.selftest()
        print("--- east wall census ---")
        sys.exit(census_selftest() or rc)
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
    stats, C_shard, C_pane, C_frame = build(a)
    proof = prove_curves(C_shard)
    log("curve proof: %s" % json.dumps(proof))
    if proof["flags"]["other"] or not proof["control_fires"] or \
            proof["max_linear_eval_err"] > 1e-4:
        raise SystemExit("REFUSING: the applied curves are not LINEAR by "
                         "evaluation: %s" % proof)
    fproof = prove_curves(C_frame) if len(C_frame.objects) else None
    if fproof is not None:
        log("frame curve proof: %s" % json.dumps(fproof))
        if fproof["flags"]["other"] or fproof["max_linear_eval_err"] > 1e-4:
            raise SystemExit("REFUSING: the east frame's curves are not "
                             "LINEAR by evaluation: %s" % fproof)
    # R5 AGAIN, ON THE SCENE THAT WILL RENDER.  The preflight above measures
    # the target as it arrived; this measures it as it leaves.  Round 1's three
    # east transoms are named in `pocket_intruders_in_the_clear_opening` on
    # every apply this project has ever run, and `land_breach.sh` says in as
    # many words that the refusal is true and that the geometry "is not ours".
    # It is ours now (R6), so the same instrument has to be able to say so.
    # AND THE CLASSIFICATION IS BY WHERE THE INTRUDER IS, NOT BY ITS NAME.
    # `BF_TRN*_STATIC` is the same aluminium as `GW_Right_Transom_*`; filtering
    # on the round 1 prefix would have reported "0 east-wall intruders" while
    # three of this module's own objects lay in the pocket.  That is R2-124's
    # mistake in a fresh coat of paint.  What R6 claims to have cleared is the
    # WOUND -- bays 4 and 5, y -2.1625 .. 2.1625 -- and nowhere else: the six
    # retained bays keep round 1's transoms across their glass on purpose.
    # AN AABB WOULD GET THIS WRONG IN BOTH DIRECTIONS.  `BF_TRN*_STATIC` is one
    # mesh holding TWO boxes, y -10.919..-4.3625 and 4.3625..11.0; its bounding
    # box spans the gap between them and would report it standing in a hole it
    # is nowhere near.  Round 1's single 21.9 m transom has the opposite
    # problem -- it really does cross the wound and its eight vertices are 11 m
    # away at the ends.  So this asks the same question R5 asks, triangles
    # against the box, restricted to bays 4 and 5's clear openings.
    EDGE_ = 0.0225 + 0.001
    _pl = FR.load(a.shards)
    WOUND_BOXES = [((14.9455, r[0] + EDGE_, r[2] + EDGE_),
                    (14.9695, r[1] - EDGE_, r[3] - EDGE_))
                   for b, r in _pl["rects"].items() if b in (4, 5)]
    post = preflight(bpy.context.scene)
    over_wound, elsewhere = [], []
    for x in post["pocket_intruders_in_the_clear_opening"]:
        ob = bpy.data.objects.get(str(x[0]))
        hit = 0
        if ob is not None and ob.type == "MESH":
            V = _world_verts(ob)
            loops = [list(pl.vertices) for pl in ob.data.polygons]
            for blo, bhi in WOUND_BOXES:
                hit += _tris_hit_box(V, loops, blo, bhi)
        (over_wound if hit else elsewhere).append(list(x) + [hit])
    log("R5 after the build: %d intruders in the clear opening OVER THE WOUND "
        "(was 3 -- GW_Right_Transom_0/1/2), %d elsewhere on this and the "
        "south wall, deliberately unchanged: %s"
        % (len(over_wound), len(elsewhere), [x[0] for x in elsewhere]))
    east_intr = over_wound
    import resample as _RS
    fcen = (frame_census(_RS.read_film(a.film)) if not a.no_frame
            else dict(PASS=True, skipped=True))
    fcen["R5_intruders_over_the_wound_after"] = east_intr
    fcen["R5_intruders_elsewhere_after"] = elsewhere
    log("east frame census: %s" % json.dumps(fcen, default=float))
    if not fcen["PASS"] and not a.force:
        raise SystemExit(
            "REFUSING: after applying, the east wall's aluminium is not all "
            "there: missing %s, round-1 solids left behind %s, untouched "
            "mullions gone %s."
            % (fcen["pieces_missing"], fcen["round1_solids_not_deleted"],
               fcen["untouched_mullions_missing"]))
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
    rep = dict(stats=stats, proof=proof, frame_proof=fproof, preflight=pre,
               east_wall=east, east_frame=fcen, out=a.out,
               bytes=os.path.getsize(a.out), origin_rule=SM.ORIGIN_RULE)
    with open(a.report, "w") as fh:
        json.dump(rep, fh, indent=1, default=float)
    log("wrote %s (%.1f MB)" % (a.out, rep["bytes"] / 1e6))


if __name__ == "__main__":
    main()
