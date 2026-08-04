#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_items.py — THE MISSING STAGE: built item modules into the assembled world.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P assemble.py -- \
        --out X.blend --mods surface,barriers,architecture,terrain,dressing,items

    # standalone, on any scene, for a test build:
    /opt/blender-5.2.0-linux-x64/blender -b <scene.blend> --factory-startup \
        -P world/build_items.py -- --place crew_figure,tyre_wall_tyre \
        --out work/x.blend --report work/x.json

WHY THIS FILE EXISTS
====================
`docs/ITEM-PRESENCE-CENSUS.md`: **0 of 41 item modules contribute a single
datablock to `assembly9.blend` or `film14.blend`.**  31 items are gated AND
tiered AND scored with their module output absent from every artefact.  The
cause is not 36 oversights:

    "assemble.py builds five modules -- surface, barriers, architecture,
     terrain, dressing -- and none of the five imports anything from
     world/items/.  There is no code path by which an item module's geometry
     can reach the ship."                                   -- census §1.1

Nothing failed, because there was nothing to fail.  This is that code path.

WHAT AN ITEM MODULE ACTUALLY HANDS OVER — MEASURED, NOT ASSUMED
===============================================================
The census says the docs record no placement data for any item, and that is
true of the docs.  It is not true of the artefacts.  Measured by
`work/r2226/inventory_item.py` over the built test blends:

    item                  objects   distinct meshes   centroid extent (world)
    armco_post              3,236           3,236     x[-716.9  552.7]  y[-256.8  926.9]
    catch_fence_post          676             676     x[-716.9  625.8]  y[-257.2  983.9]
    crew_figure               120             120     x[ -58.8  -30.1]  y[ -64.3  -37.3]
    heras_fence_panel         771             771     x[-109.9  377.8]  y[-105.5  320.0]
    timing_stand               10              10     x[ 161.9  317.2]  y[  47.3  177.7]
    tyre_wall_tyre            338             338     x[ 246.6  267.3]  y[ 895.6  928.1]

Those are CIRCUIT coordinates, not a bench layout.  The modules import
`world_contract` and resolve every unit through `C.su_to_world(s, u)` /
`C.world_ground_z(x, y)` **at build time**.  Their `.blend` already holds the
item standing where it belongs.

**So the stage is a TRANSFER, not a transform.**  It reads the item's declared
collection out of its own built blend and links it into the world at identity.
That is why this file is 600 lines and not a placement solver: the placement
was solved by the item's author, through the same contract every class-level
builder reads, and then thrown away at the door.

HOW IT FITS THE EXISTING BUILDERS
=================================
Exactly as `build_dressing` fits.  `assemble.py` calls `build()`; `build()`
returns a summary dict of ints and strings; every datablock this module owns is
under the `R2_Items` root and is purged before a rebuild, so two consecutive
calls give an identical scene.  It runs LAST, after `architecture` and
`barriers`, because an item may SUPERSEDE class-level geometry and can only
remove what has already been built.

It owns no datum.  `build_dressing`'s rule -- "ground_z(s, lat, side) is
world_contract's, and `anchor()` is the only way anything in this file touches
the ground" -- has an exact analogue here, and it is stricter: **this file
computes no position at all.**  Every coordinate it ships was computed by the
item module against the contract.  The only spatial thing this file does is
CHECK: it projects every placed object back onto the centreline with
`C.project()` and refuses a population that does not land on the circuit.

THE FIVE THINGS IT REFUSES TO DO, EACH A DEFECT ALREADY PAID FOR
================================================================
1.  GUESS A CONVENTION.  There are four collection naming schemes in the corpus
    (`W_Item_TimingStand` / `ITEM_MARSHAL_POST_DECK` / `PDS_Deck` + `PGD_Girders`
    / `CFO_Crew`).  R2-180: a detector fell through to "any item collection,
    biggest wins" and silently measured ANOTHER ITEM'S FLOOR.  This file has no
    auto-detection and no fallback.  An item not in `PLACEMENT.json`, or a
    declared collection not present in the source blend, is a hard refusal that
    prints what IS there.  `armco_post_test.blend` contains a foreign
    `W_Item_ArmcoWBeam` collection with 33 objects -- exactly the geometry a
    fall-through would have eaten.

2.  PLACE A PARTIAL BUILD.  Several blends on disk are gating samples built
    with `--limit`.  The registry records the population the item's own
    interface declares and the count the gate measured, and a row whose
    `expect_objects` does not match what the blend holds is refused.

3.  PLACE OVER GEOMETRY IT SUPERSEDES.  Census §3.2: "a module for an item the
    world already builds must be integrated against existing geometry, and the
    moment it is placed the old version has to come out."  Every row declares
    `supersedes` -- object names, exactly, never patterns that could sweep a
    neighbour.  If the superseded thing is a WHOLE OBJECT the stage removes it
    and reports the removal.  If it is welded inside a shared class mesh
    (`ARCH_PitWall` carries `pit_wall_stands = 5` inside one mesh) the stage
    REFUSES and reports `REBUILD_OWED`, because taking it out is a change to
    the class module and a full assembly, which this stage may not do.

4.  INSTANCE ANYTHING.  See THE NO-REPEATS LINE below.

5.  PLACE SILENTLY.  Every placed object carries a provenance stamp naming the
    item, the source blend and its sha256.  Census §1.5: 168 of 435 items are
    UNDET because "the ship carries no per-item provenance ... anyone who wants
    those 168 resolved needs a provenance attribute written at build time, not
    a better grep."  This writes that attribute for everything it places.

THE NO-REPEATS LINE, AND WHERE IT IS WON
========================================
`WAVE2-SCOPE.md` §4.2: the world-level spam check CANNOT FIRE.  One mesh
instanced 500,000 times scores 7.01 % against a 40 % threshold, because the
denominator is 4.7 M grass instances.  "The named failure the user drew a red
line around is invisible to the instrument that carries its name."

Placement is the exact stage where that line is won or lost, because placement
is the only stage at which a "one mesh, many transforms" shortcut can enter.
This file holds it three ways, in increasing order of how much they are worth:

  (a) STRUCTURALLY.  It copies object datablocks one for one out of the source
      blend.  There is no code path here that creates an instance, a linked
      duplicate, a particle system or a geometry-node emitter.  It cannot take
      the shortcut because the shortcut is not written.

  (b) BY ASSERTION, EVERY RUN.  After placement, per item:
          distinct source meshes == objects placed
          every mesh datablock has exactly one user
          no object has instance_type != 'NONE'
      Measured on the six candidates above: 3236/3236, 676/676, 120/120,
      771/771, 10/10, 338/338, and zero shared meshes and zero instancers in
      all six.  A violation is a refusal, not a warning.

  (c) BY MEASUREMENT, PER FAMILY, AT THE PER-FAMILY BOUND.  `top_share` is
      computed over the item's OWN family, never globally, and gated at
      `FAMILY_TOP_SHARE_MAX = 0.10` -- `WAVE2-SCOPE.md` §4.3's per-family bound,
      not the global 0.40 that provably cannot fire.  The six candidates score
      0.031 %, 0.148 %, 0.833 %, 0.130 %, 10.000 % and 0.296 %.
      `timing_stand` at exactly 1/10 is the honest edge of a ten-unit
      population and is admitted by `min_units_for_share`, not by loosening the
      bound -- a share bound is meaningless below 1/bound units.

  `tools/item_placement_gate.py --selftest` builds a family of N objects
  sharing ONE mesh and requires (b) and (c) to FAIL on it.  A check that has
  never been shown to fail is not a check.

Design notes: `world/build_items.md`.  Registry: `world/items/PLACEMENT.json`.
"""

import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ITEMS_DIR = os.path.join(HERE, "items")
REGISTRY = os.path.join(ITEMS_DIR, "PLACEMENT.json")
GATE_DIR = os.path.join(ROOT, "render", "items")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

ROOT_COLL = "R2_Items"

#: Stage version. Stamped onto every placed object; bump it when the placement
#: SEMANTICS change, so an object in an old blend can be told from a new one.
STAGE_VERSION = "1.0.0"

#: `WAVE2-SCOPE.md` §4.3: a family's commonest source mesh is bounded at 10 %,
#: not the global instrument's 40 %, "chosen because the world's healthiest
#: family today runs at 1.99 %".
FAMILY_TOP_SHARE_MAX = 0.10

#: A share bound cannot mean anything below 1/bound units: a population of 4
#: has a floor of 25 % however perfect it is. Below this the SHARE test is
#: reported and not gated -- (a) and (b) still gate, and they are the ones that
#: catch spam.
MIN_UNITS_FOR_SHARE = int(round(1.0 / FAMILY_TOP_SHARE_MAX))

#: How far off the lap centreline a placed unit may sit before the stage calls
#: the population "not on this circuit". The world's own terrain reaches ~1 km;
#: this is a sanity bound against a local-frame blend placed at identity, whose
#: signature is a population collapsed onto the origin, not a wide one.
MAX_ABS_U_M = 900.0

#: A local-frame item placed at identity lands in a tight knot at the world
#: origin. If a multi-unit population's centroids all fall inside this radius
#: of (0, 0) the stage refuses: the registry said `frame: world` and the
#: artefact disagrees.
LOCAL_FRAME_BLOB_R_M = 25.0


# --------------------------------------------------------------------------- #
#  0.  registry                                                                 #
# --------------------------------------------------------------------------- #

class PlacementRefusal(RuntimeError):
    """A refusal, never a fallback. Raised where an older tool would guess."""


def load_registry(path=REGISTRY):
    with open(path) as fh:
        reg = json.load(fh)
    if reg.get("schema") != "f1-round2/item_placement/1.0":
        raise PlacementRefusal("registry %s: unknown schema %r"
                               % (path, reg.get("schema")))
    rows = {}
    for r in reg["items"]:
        # Keyed on the MODULE, not the manifest id: `pit_wall_unit_itemkit` and
        # `pit_wall_unit` declare the same id and the same collection, and so do
        # `showroom_facade_panel_v2` and `showroom_facade_panel`. A registry
        # keyed on the id would have silently dropped one of each pair.
        k = r.get("key") or r["item"]
        if k in rows:
            raise PlacementRefusal("registry: duplicate row for %r" % k)
        rows[k] = r
    return reg, rows


def sha256(path, cap=None):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _abs(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


# --------------------------------------------------------------------------- #
#  1.  what the registry says vs what the artefact says                         #
# --------------------------------------------------------------------------- #

def source_collections(blend):
    """The collection names a blend actually holds, without opening the scene.

    Asked BEFORE any append, so an unrecognised convention is a refusal with
    the real list printed rather than a fall-through to whatever is biggest.
    """
    import bpy
    with bpy.data.libraries.load(blend, link=True) as (df, _dt):
        return sorted(df.collections)


def check_row(row, strict_sha=False):
    """Everything that can be judged before a single datablock is read.

    -> (list of fatal refusals, list of non-fatal findings)
    """
    fatal, notes = [], []
    blend = _abs(row["source_blend"])
    if not os.path.exists(blend):
        fatal.append("source blend absent: %s" % blend)
        return fatal, notes

    got = sha256(blend)
    want = row.get("source_sha256")
    if want and got != want:
        msg = ("source blend has CHANGED since the registry was written "
               "(%s -> %s). Everything downstream would be measuring a file "
               "this registry did not describe -- R2-108's shape."
               % (want[:16], got[:16]))
        (fatal if strict_sha else notes).append(msg)
    row["_sha_now"] = got

    # Staleness against the whole import closure, not the module's own mtime.
    # R2-119: 30 of 32 by the closure rule against 0 of 32 by the own-module
    # rule. Reported, never fatal: it is a list of things nobody has a reason
    # to believe, and refusing on it would block the assembly on a condition
    # the campaign already owns.
    closure = [os.path.join(HERE, f) for f in
               ("world_contract.py", "itemkit.py", "humankit.py")]
    closure.append(os.path.join(ITEMS_DIR,
                                (row.get("key") or row["item"]) + ".py"))
    bs = os.path.getmtime(blend)
    stale = [os.path.basename(c) for c in closure
             if os.path.exists(c) and os.path.getmtime(c) > bs]
    if stale:
        notes.append("STALE_CLOSURE: blend predates %s" % ", ".join(sorted(stale)))
    row["_stale_against"] = sorted(stale)

    # The gate's own verdict, read from the canonical path.
    g = os.path.join(GATE_DIR, row["item"], "gate.json")
    row["_gate_result"] = None
    if os.path.exists(g):
        try:
            row["_gate_result"] = json.load(open(g)).get("result")
        except Exception as e:                          # pragma: no cover
            notes.append("gate.json unreadable: %r" % e)
    if row.get("require_gate_accepted", True) and row["_gate_result"] != "ITEM_ACCEPTED":
        fatal.append("gate verdict is %r, not ITEM_ACCEPTED. A placement stage "
                     "that ships un-accepted geometry makes the gate optional."
                     % row["_gate_result"])
    return fatal, notes


# --------------------------------------------------------------------------- #
#  2.  supersede — the old version has to come out, or the stage says so        #
# --------------------------------------------------------------------------- #

def resolve_supersede(row):
    """-> (objects to unlink, list of REBUILD_OWED findings)

    `supersedes` is a list of records, each either

        {"object": "BR_TyreWall_T4", "reason": "..."}          removable here
        {"welded_in": "ARCH_PitWall", "counter": "pit_wall_stands",
         "n": 5, "reason": "..."}                              NOT removable here

    An exact object name, never a pattern. A pattern that swept one object too
    many would delete a neighbour's work, and this stage runs after every
    class-level builder.
    """
    import bpy
    drop, owed = [], []
    for s in row.get("supersedes", []):
        if "object" in s:
            ob = bpy.data.objects.get(s["object"])
            if ob is None:
                owed.append({"kind": "SUPERSEDE_TARGET_ABSENT",
                             "target": s["object"],
                             "note": "declared superseded but not in this scene; "
                                     "nothing removed, nothing double-built"})
            else:
                drop.append(ob)
        elif "welded_in" in s:
            host = bpy.data.objects.get(s["welded_in"])
            owed.append({"kind": "REBUILD_OWED",
                         "target": s["welded_in"],
                         "present": host is not None,
                         "counter": s.get("counter"), "n": s.get("n"),
                         "note": s.get("reason", "")})
        else:
            raise PlacementRefusal("registry %s: supersede record has neither "
                                   "`object` nor `welded_in`: %r"
                                   % (row["item"], s))
    return drop, owed


# --------------------------------------------------------------------------- #
#  3.  the transfer                                                             #
# --------------------------------------------------------------------------- #

_RIG_SUFFIX = ("/Cameras", "/Standins", "_Cameras", "_Standins",
               "_Context", "/Context")


def _is_rig(name, row):
    declared = row.get("rig_subcollections")
    if declared is not None:
        return name in declared
    return any(name.endswith(s) for s in _RIG_SUFFIX)


def place_one(row, scene=None):
    """Append one item's declared collection and verify what landed.

    Returns a per-item report. Raises PlacementRefusal on anything that would
    put geometry into the ship that nobody can account for.
    """
    import bpy
    scene = scene or bpy.context.scene
    key = row.get("key") or row["item"]
    item, coll_name, pfx = key, row["collection"], row["prefix"]
    blend = _abs(row["source_blend"])
    t0 = time.time()

    present = source_collections(blend)
    if coll_name not in present:
        raise PlacementRefusal(
            "%s: the registry declares collection %r and %s does not contain "
            "it.\n  the blend holds: %s\n"
            "  REFUSING rather than choosing one. R2-180 is what choosing "
            "looks like: a detector fell through to 'any item collection, "
            "biggest wins' and measured another item's floor."
            % (item, coll_name, os.path.basename(blend), present))

    before_obj = set(bpy.data.objects.keys())
    before_mesh = set(bpy.data.meshes.keys())
    before_mat = set(bpy.data.materials.keys())
    before_coll = set(bpy.data.collections.keys())

    with bpy.data.libraries.load(blend, link=False) as (df, dt):
        if coll_name not in df.collections:                 # pragma: no cover
            raise PlacementRefusal("%s: %r vanished between the read and the "
                                   "append" % (item, coll_name))
        dt.collections = [coll_name]

    new_colls = [bpy.data.collections[n] for n in bpy.data.collections.keys()
                 if n not in before_coll]
    top = [c for c in new_colls if c.name == coll_name]
    if not top:
        # Blender suffixed it because the name was taken -- which would mean the
        # world already carries this item. That is a finding, not a rename.
        raise PlacementRefusal(
            "%s: appended %r but the scene already had a collection of that "
            "name, so Blender created a suffixed copy. The item is already in "
            "this world; placing it twice is the defect this stage exists to "
            "prevent." % (item, coll_name))
    top = top[0]

    # --- drop the test rig ------------------------------------------------- #
    # The rig's MESHES go with its objects. A standin ground plane whose object
    # is deleted and whose mesh is left behind is a zero-user datablock that
    # survives until the next save, and it made this stage non-idempotent
    # inside a session: build() twice gave 122 meshes then 123 on an identical
    # 120-object scene. Same rule as purge() -- scoped to what THIS append
    # brought in, never a sweep of bpy.data.
    orphaned = set()

    def _drop(ob):
        if ob.type == "MESH" and ob.data is not None:
            orphaned.add(ob.data.name)
        bpy.data.objects.remove(ob, do_unlink=True)

    dropped_rig = []
    for ch in list(top.children):
        if _is_rig(ch.name, row):
            dropped_rig.append((ch.name, len(ch.objects)))
            for ob in list(ch.all_objects):
                _drop(ob)
            bpy.data.collections.remove(ch)
    # Cameras and lamps ride along in the top collection on some modules.
    stripped = []
    for ob in list(top.all_objects):
        if ob.type in ("CAMERA", "LIGHT", "EMPTY", "SPEAKER"):
            stripped.append((ob.name, ob.type))
            _drop(ob)
    for nm in orphaned:
        me = bpy.data.meshes.get(nm)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)

    objs = [o for o in top.all_objects if o.type == "MESH"]

    # --- link under the stage root, THEN evaluate -------------------------- #
    # An appended object that is in no view layer carries an IDENTITY
    # matrix_world. Measuring world position before this line reports every
    # population as a knot at the origin -- which is precisely the local-frame
    # signature `_check_on_circuit` exists to detect, so the check would have
    # fired on its own instrument rather than on the geometry. Link first,
    # update the depsgraph, and only then ask where anything is.
    root = bpy.data.collections.get(ROOT_COLL)
    if root is None:
        root = bpy.data.collections.new(ROOT_COLL)
        scene.collection.children.link(root)
    for c in list(scene.collection.children):
        if c.name == top.name:
            scene.collection.children.unlink(c)
    if top.name not in root.children:
        root.children.link(top)
    bpy.context.view_layer.update()

    # --- the refusals ------------------------------------------------------ #
    off = [o.name for o in objs if not o.name.startswith(pfx)]
    if off:
        raise PlacementRefusal(
            "%s: %d of %d appended objects do not carry the declared prefix "
            "%r: %s%s. A collection holding a foreign prefix is another item's "
            "geometry riding along."
            % (item, len(off), len(objs), pfx, sorted(off)[:8],
               " ..." if len(off) > 8 else ""))

    want = row["expect_objects"]
    if len(objs) != want:
        raise PlacementRefusal(
            "%s: registry expects %d objects, the blend delivered %d. A blend "
            "built with --limit is a gating sample, not the shipping "
            "population; placing it ships a silent shortfall."
            % (item, want, len(objs)))

    inst = [o.name for o in objs if o.instance_type != "NONE"]
    if inst:
        raise PlacementRefusal(
            "%s: %d objects are instancers (%s). This stage transfers object "
            "datablocks one for one; an instancer is the shape of the repeated "
            "asset the brief draws a red line around."
            % (item, len(inst), sorted(inst)[:6]))

    meshes = [o.data for o in objs]
    shared = sorted({m.name for m in meshes if m.users > 1})
    distinct = len({m.name for m in meshes})
    if shared:
        raise PlacementRefusal(
            "%s: %d mesh datablocks have more than one user (%s). One mesh "
            "worn by many objects is one tree spammed a hundred times with "
            "extra steps." % (item, len(shared), shared[:6]))
    if distinct != len(objs):
        raise PlacementRefusal(
            "%s: %d objects share %d distinct meshes. The no-repeats rule is "
            "one source mesh per placed unit."
            % (item, len(objs), distinct))

    # --- per-family variety, at the PER-FAMILY bound ----------------------- #
    from collections import Counter
    cnt = Counter(m.name for m in meshes)
    top_mesh, top_n = cnt.most_common(1)[0]
    top_share = top_n / float(len(objs))
    share_gated = len(objs) >= MIN_UNITS_FOR_SHARE
    if share_gated and top_share > FAMILY_TOP_SHARE_MAX:
        raise PlacementRefusal(
            "%s: commonest source mesh %r is %.2f %% of the family, over the "
            "per-family bound of %.0f %% (WAVE2-SCOPE §4.3). The GLOBAL 40 %% "
            "check cannot fire here -- one mesh at half a million copies "
            "scores 7.01 %% of this world -- so the family bound is the only "
            "one that means anything."
            % (item, top_mesh, 100 * top_share, 100 * FAMILY_TOP_SHARE_MAX))

    # --- did it land on the circuit? --------------------------------------- #
    onlap = _check_on_circuit(item, row, objs)

    # --- provenance --------------------------------------------------------- #
    stamp = {"r2_item": item,
             "r2_item_collection": coll_name,
             "r2_manifest_item": row["item"],
             "r2_src_blend": os.path.relpath(blend, ROOT),
             "r2_src_sha8": row.get("_sha_now", "")[:16],
             "r2_gate": row.get("_gate_result") or "none",
             "r2_stage": "build_items " + STAGE_VERSION,
             "r2_placed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for ob in objs:
        for k, v in stamp.items():
            ob[k] = v
        # Also on the mesh, so a later weld/join that keeps the target's data
        # keeps the attribution with it.
        ob.data["r2_item"] = item
    for k, v in stamp.items():
        top[k] = v

    # --- supersede ---------------------------------------------------------- #
    drop, owed = resolve_supersede(row)
    removed = []
    for ob in drop:
        removed.append({"object": ob.name,
                        "tris": sum(max(0, len(p.vertices) - 2)
                                    for p in ob.data.polygons)
                                if ob.type == "MESH" and ob.data else 0})
        bpy.data.objects.remove(ob, do_unlink=True)

    new_mat = sorted(set(bpy.data.materials.keys()) - before_mat)
    suffixed = [m for m in new_mat if m[-4:-3] == "." and m[-3:].isdigit()]

    tris = sum(sum(max(0, len(p.vertices) - 2) for p in o.data.polygons)
               for o in objs)
    return {
        "key": key, "item": row["item"], "collection": coll_name,
        "prefix": pfx,
        "source_blend": os.path.relpath(blend, ROOT),
        "source_sha256": row.get("_sha_now"),
        "gate_result": row.get("_gate_result"),
        "stale_against": row.get("_stale_against", []),
        "objects": len(objs), "distinct_meshes": distinct, "triangles": tris,
        "top_source_mesh": top_mesh, "top_share": round(top_share, 6),
        "top_share_gated": share_gated,
        "shared_meshes": 0, "instancers": 0,
        "materials_added": len(new_mat),
        "materials_name_collided": suffixed,
        "rig_subcollections_dropped": dropped_rig,
        "non_mesh_stripped": stripped,
        "superseded_removed": removed,
        "rebuild_owed": owed,
        "on_circuit": onlap,
        "objects_added_total": len(set(bpy.data.objects.keys()) - before_obj),
        "meshes_added_total": len(set(bpy.data.meshes.keys()) - before_mesh),
        "secs": round(time.time() - t0, 1),
    }


def _check_on_circuit(item, row, objs):
    """Did the population land on this circuit, or at the world origin?

    The registry declares `frame: "world"`. That is a CLAIM about the artefact
    and this is the measurement of it. A blend built in a local frame (three
    items publish `place=(R, t)` and build at a local origin) placed at identity
    lands in a knot at (0, 0) -- a signature this can see and a bounding box
    cannot.
    """
    try:
        import numpy as np
        import world_contract as C
    except Exception as e:                                  # pragma: no cover
        return {"checked": False, "why": repr(e)}
    from mathutils import Vector
    pts = []
    for o in objs:
        mw = o.matrix_world
        cs = [mw @ Vector(v) for v in o.bound_box]
        pts.append((sum(c.x for c in cs) / 8.0, sum(c.y for c in cs) / 8.0))
    X = np.array([p[0] for p in pts]); Y = np.array([p[1] for p in pts])
    S, U = C.project(X, Y)
    r0 = np.hypot(X, Y)
    blob = bool(len(objs) > 1 and r0.max() < LOCAL_FRAME_BLOB_R_M)
    far = int((np.abs(U) > MAX_ABS_U_M).sum())
    rep = {"checked": True, "frame_declared": row.get("frame", "world"),
           "s_min": round(float(S.min()), 1), "s_max": round(float(S.max()), 1),
           "u_min": round(float(U.min()), 2), "u_max": round(float(U.max()), 2),
           "units_beyond_u_%d_m" % MAX_ABS_U_M: far,
           "max_radius_from_origin_m": round(float(r0.max()), 1),
           "collapsed_at_origin": blob}
    if blob:
        raise PlacementRefusal(
            "%s: the registry declares frame 'world' but all %d units sit "
            "within %.0f m of the world origin (max radius %.1f m). That is "
            "the signature of a LOCAL-frame blend placed at identity. Three "
            "items in this corpus build local and publish place=(R, t); this "
            "one has not been given its transform."
            % (item, len(objs), LOCAL_FRAME_BLOB_R_M, r0.max()))
    if far:
        raise PlacementRefusal(
            "%s: %d of %d units project more than %.0f m off the lap "
            "centreline. Either the frame is wrong or this is not this "
            "circuit." % (item, far, len(objs), MAX_ABS_U_M))
    return rep


# --------------------------------------------------------------------------- #
#  4.  build() — the entry point assemble.py calls                              #
# --------------------------------------------------------------------------- #

def purge():
    """Idempotence, `build_dressing`'s rule: everything this stage owns goes.

    It has to take the MESH datablocks with it, not just the objects. Removing
    120 objects and leaving their 120 meshes behind gives a scene that looks
    right -- the object names are even reused, because Blender freed them --
    and a `bpy.data.meshes` that has doubled. Measured before this line
    existed: build() twice in one session gave 122 meshes then 243, on an
    identical 120-object scene. Blender drops zero-user datablocks on save, so
    it would never have reached a shipped blend; it would have made every
    in-session mesh count in this file wrong, and the mesh counts are how the
    no-repeats rule is enforced.

    Removal is scoped to what this stage placed -- meshes whose users fell to
    zero when OUR objects went. It never sweeps `bpy.data` for orphans: an
    orphan somebody else made is not this stage's to delete, and `purge(prefix)
    has no default prefix` is a rule this project already paid for.
    """
    import bpy
    root = bpy.data.collections.get(ROOT_COLL)
    if root is None:
        return 0
    n = 0
    mine = set()
    for ob in list(root.all_objects):
        if ob.type == "MESH" and ob.data is not None:
            mine.add(ob.data.name)
        bpy.data.objects.remove(ob, do_unlink=True)
        n += 1
    for c in list(root.children):
        bpy.data.collections.remove(c)
    bpy.data.collections.remove(root)
    for nm in mine:
        me = bpy.data.meshes.get(nm)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
    return n


def build(place=None, registry=REGISTRY, strict_sha=False, scene=None):
    """Place every item the registry marks PLACE (or every item named in
    `place`, for a test build).

    -> summary dict, `assemble.py`-shaped: ints and strings only at top level.
    """
    import bpy
    scene = scene or bpy.context.scene
    reg, rows = load_registry(registry)

    if place is None:
        want = [(r.get("key") or r["item"]) for r in reg["items"]
                if r.get("state") == "PLACE"]
        forced = []
    else:
        want, forced = list(place), list(place)

    print("[ITEMS] build_items %s, registry %s (%d rows), placing %d: %s"
          % (STAGE_VERSION, os.path.basename(registry), len(rows),
             len(want), ", ".join(want) or "-"))
    if forced:
        print("[ITEMS] NOTE: %d item(s) named on the command line, overriding "
              "the registry's state field. This is a TEST BUILD path."
              % len(forced))

    purged = purge()
    if purged:
        print("[ITEMS] purged %d objects from a previous %s" % (purged, ROOT_COLL))

    placed, refused, notes_all, owed_all = [], [], [], []
    for item in want:
        row = rows.get(item)
        if row is None:
            raise PlacementRefusal(
                "%r is not in %s. This stage has no auto-detection: an item "
                "with no registry row has no declared collection, no declared "
                "population and no declared supersede, and guessing any of the "
                "three is how R2-180 happened." % (item, os.path.basename(registry)))
        if row.get("state") not in ("PLACE",) and item not in forced:
            refused.append({"item": item, "why": "registry state is %r"
                            % row.get("state")})
            continue
        fatal, notes = check_row(row, strict_sha=strict_sha)
        for n in notes:
            print("[ITEMS] %s: %s" % (item, n))
            notes_all.append("%s: %s" % (item, n))
        if fatal:
            for f in fatal:
                print("[ITEMS] REFUSED %s: %s" % (item, f))
            refused.append({"item": item, "why": "; ".join(fatal)})
            continue
        rep = place_one(row, scene=scene)
        placed.append(rep)
        owed_all.extend(dict(r, item=item) for r in rep["rebuild_owed"])
        print("[ITEMS] placed %-24s %6d objects  %6d meshes  %10d tris  "
              "top_share %.4f%%  %.1fs"
              % (item, rep["objects"], rep["distinct_meshes"], rep["triangles"],
                 100 * rep["top_share"], rep["secs"]))
        for r in rep["superseded_removed"]:
            print("[ITEMS]   superseded: removed %s (%d tris)"
                  % (r["object"], r["tris"]))
        for r in rep["rebuild_owed"]:
            print("[ITEMS]   %s: %s %s" % (r["kind"], r["target"], r["note"]))

    summary = {
        "module": "world/build_items.py",
        "stage_version": STAGE_VERSION,
        "registry": os.path.relpath(registry, ROOT),
        "registry_rows": len(rows),
        "collection": ROOT_COLL,
        "items_placed": len(placed),
        "items_refused": len(refused),
        "objects": sum(p["objects"] for p in placed),
        "distinct_meshes": sum(p["distinct_meshes"] for p in placed),
        "triangles": sum(p["triangles"] for p in placed),
        "shared_meshes": 0,
        "instancers": 0,
        "superseded_objects_removed": sum(len(p["superseded_removed"])
                                          for p in placed),
        "rebuild_owed": len(owed_all),
        "stale_inputs": sum(1 for p in placed if p["stale_against"]),
        "placed": placed, "refused": refused, "notes": notes_all,
        "owed": owed_all,
    }
    if not want:
        result = "ITEMS_NOTHING_REQUESTED_VACUOUS"
    elif not placed:
        result = "ITEMS_NONE_PLACED_FAIL"
    else:
        result = "ITEMS_PLACED_OK"
    summary["result"] = result
    print("[ITEMS] %d item(s), %d objects, %d distinct meshes, %d tris; "
          "%d refused, %d rebuild owed"
          % (len(placed), summary["objects"], summary["distinct_meshes"],
             summary["triangles"], len(refused), len(owed_all)))
    # Staleness is REPORTED, never gated, and the split is deliberate.
    # R2-119: 30 of 32 item blends are stale against their whole import
    # closure, and 0 of 32 against their own module. That is the campaign's
    # standing condition, not a regression -- a verdict that failed on it
    # would fail every assembly and would be ignored within a week. It gets
    # its own greppable line instead, and the per-item list is in the report.
    if summary["stale_inputs"]:
        print(">> ITEMS STALE CLOSURE: %d of %d placed item(s) were built "
              "before something they import: %s"
              % (summary["stale_inputs"], len(placed),
                 "; ".join("%s < %s" % (p["key"], ",".join(p["stale_against"]))
                           for p in placed if p["stale_against"])))
    for o in owed_all:
        print(">> ITEMS REBUILD OWED: %s -> %s (%s)"
              % (o["item"], o["target"], o.get("counter")))
    print(">> STAGE RESULT: %s" % result)
    return summary


# --------------------------------------------------------------------------- #
#  5.  standalone CLI, for a test build against an existing scene               #
# --------------------------------------------------------------------------- #

def _main():
    import bpy
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    def opt(n, d=None):
        return argv[argv.index(n) + 1] if n in argv else d

    place = opt("--place")
    place = [s for s in place.split(",") if s] if place else None
    out = opt("--out")
    report = opt("--report")

    try:
        s = build(place=place, strict_sha=("--strict-sha" in argv))
        rc = 0
    except PlacementRefusal as e:
        print("\n[ITEMS] REFUSED\n%s" % e)
        print(">> STAGE RESULT: ITEMS_REFUSED_FAIL")
        s, rc = {"result": "ITEMS_REFUSED_FAIL", "why": str(e)}, 1

    if report:
        os.makedirs(os.path.dirname(_abs(report)) or ".", exist_ok=True)
        try:
            import provenance as P                          # noqa: F401
        except Exception:
            sys.path.insert(0, os.path.join(ROOT, "tools"))
            try:
                import provenance as P
            except Exception:
                P = None
        if P is not None and rc == 0:
            try:
                s["provenance"] = P.stamp(
                    tool_file=__file__,
                    tool_version="build_items " + STAGE_VERSION,
                    inputs=([("registry", REGISTRY)] +
                            [(p["item"], _abs(p["source_blend"]))
                             for p in s.get("placed", [])]),
                    describes=[("out_blend", _abs(out))] if out else [])
            except Exception as e:
                s["provenance_error"] = repr(e)
        with open(_abs(report), "w") as f:
            json.dump(s, f, indent=1, default=str)
        print("[ITEMS] report -> %s" % _abs(report))

    if out and rc == 0:
        os.makedirs(os.path.dirname(_abs(out)) or ".", exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=_abs(out), compress=False)
        print("[ITEMS] saved %s (%.1f MB)"
              % (_abs(out), os.path.getsize(_abs(out)) / 1048576.0))
    return rc


if __name__ == "__main__":
    sys.exit(_main())
