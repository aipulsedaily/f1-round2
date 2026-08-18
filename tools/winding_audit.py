"""Winding audit — which side of every built surface does the renderer get?

    blender -b <file.blend> --factory-startup -P tools/winding_audit.py -- \
            --item <id> [--collection <NAME>] [--rays 600] [--out <json>]
            [--fix --save <out.blend>]

WHY. An orientation audit of a finished human figure found 54 of 318 emitted
pieces facing INWARD -- head shell, ears, hair, both shoe uppers, both soles and
all 22 tread bars. Cycles flips a back-facing normal for diffuse, so none of it
rendered black; it rendered with every bump INVERTED, a brow ridge lit as a
groove. Every check in the project passed, because every check measured the
MODEL and none measured the SIDE.

The idioms that produce it -- lofting rings, sweeping profiles, capping
boundary loops, and above all MIRRORING ACROSS AN AXIS, which reverses winding
by construction -- are the idioms all 28 wave-1 item modules are built from.
This runs itemkit's `winding_audit` over every mesh in a built blend, so the
question gets an answer per module without re-running 28 builders.

WHAT IT REPORTS, per object and summed per module:

    pieces / inward         connected components, and how many face inward
    inward_tri_frac         the number that says whether it MATTERS -- a
                            reversed washer is not a reversed head shell
    inconsistent_edges      pieces wound inconsistently WITHIN themselves,
                            which signed volume cannot see and which no flip
                            can repair
    mirrored_by_matrix      objects whose own matrix has a negative
                            determinant: correct geometry, reversed on arrival
    inside_out_fraction     rays cast, first hit taken, back faces counted --
                            the only statistic that measures the picture

`--fix` repairs the meshes in place and `--save` writes the result; the audit is
re-run afterwards and BOTH numbers are in the report, because a repair that is
not measured after the fact is a hope.
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

import bpy

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "world"))
import itemkit as K                                          # noqa: E402

CONTEXT_TOKENS = ("standin", "context", "ctx", "ground", "camera", "cam_",
                  "sun", "light", "world")


def _is_context(name):
    n = name.lower()
    return any(t in n for t in CONTEXT_TOKENS)


#: The item collection naming convention, MEASURED rather than assumed. It is
#: not one convention: `timing_stand` builds `W_Item_TimingStand`,
#: `marshal_post_deck` builds `ITEM_MARSHAL_POST_DECK`, and `pont_deck_slab`
#: builds `PDS_Deck` / `PGD_Girders` with no item prefix at all.
ITEM_PREFIXES = ("W_Item_", "ITEM_")


def _mesh_objs(obs):
    return [o for o in obs if o.type == "MESH" and o.data
            and len(o.data.polygons) and not _is_context(o.name)]


def collect(collection=None, item=None, why=None):
    """Mesh objects of the item, excluding standins the gate also excludes.

    `why` is an optional dict this fills in with HOW the subject was chosen.

    THE SUBSTITUTION THIS USED TO MAKE, AND WHAT IT COST. The old rule was
    `cands = [c for c in collections if c.name.startswith("W_Item_")]`, then
    `pick = [those whose name ends with the item key]`, then `cands = pick or
    cands` -- so when the name filter matched NOTHING it fell back to "any
    W_Item_ collection at all" and took the biggest.

    On `hospitality_deck` that is not hypothetical. Its own objects live in
    `ITEM_HOSPITALITY_DECK`, which has no `W_Item_` prefix, while its CONTEXT
    paving ships 41 `W_Item_PaddockPavingBay*` collections. So the sweep picked
    `W_Item_PaddockPavingBay` -- another item's floor -- whose 54 members are
    instancer empties holding no polygons, and reported
    `SHEET_FACING_UNMEASURED, 0 objects` for a module with five decks in it.

    A wrong subject that happens to be empty and a right subject that happens
    to be clean produce the same line of output. So: an `--item` that matches
    no collection is never a licence to measure a DIFFERENT item. The fallback
    is the whole scene, which at least contains the subject, and the choice is
    recorded and printed either way.
    """
    why = {} if why is None else why
    if collection:
        c = bpy.data.collections.get(collection)
        if c is None:
            raise SystemExit("no collection %r; have %s"
                             % (collection, [x.name for x in bpy.data.collections]))
        why.update(source="explicit --collection", collection=c.name)
        return _mesh_objs(c.all_objects)

    key = item.replace("_", "").lower() if item else None
    named = []
    if key:
        for c in bpy.data.collections:
            n = c.name.replace("_", "").lower()
            for p in ITEM_PREFIXES:
                pn = p.replace("_", "").lower()
                if n.startswith(pn) and key in n[len(pn):]:
                    named.append(c)
                    break
    # only a collection that actually HOLDS the subject can be the subject
    named = [c for c in named if _mesh_objs(c.all_objects)]
    if named:
        c = max(named, key=lambda c: len(_mesh_objs(c.all_objects)))
        why.update(source="collection matched --item", collection=c.name,
                   candidates=[x.name for x in named])
        return _mesh_objs(c.all_objects)

    prefixed = [c for c in bpy.data.collections
                if c.name.startswith(ITEM_PREFIXES) and _mesh_objs(c.all_objects)]
    if key and prefixed:
        # THE OLD CODE TOOK THE BIGGEST OF THESE. It is the wrong item.
        why.update(source="whole scene (no collection matches --item)",
                   collection=None, item_key=key,
                   rejected_other_items=[c.name for c in prefixed][:20],
                   note="an item-prefixed collection exists but none names "
                        "this item; measuring the scene rather than another "
                        "item's geometry")
        return _mesh_objs(bpy.context.scene.objects)
    if len(prefixed) == 1:
        c = prefixed[0]
        why.update(source="the only item collection in the file",
                   collection=c.name)
        return _mesh_objs(c.all_objects)
    why.update(source="whole scene (no item collection)", collection=None)
    return _mesh_objs(bpy.context.scene.objects)


def audit(objs, rays=0, fix=False):
    tot = {"objects": 0, "pieces": 0, "inward": 0, "faces": 0,
           "inward_faces": 0, "triangles": 0, "inward_triangles": 0,
           "flat": 0, "inconsistent_edges": 0, "mirrored_by_matrix": 0,
           "flipped": 0, "statistics_disagree": 0}
    per = []
    seen = {}
    for ob in objs:
        me = ob.data
        # one datablock can be shared by many objects; audit it once
        if me.name in seen:
            r = dict(seen[me.name])
        else:
            r = K.mesh_winding_report(me, apply=fix)
            seen[me.name] = dict(r)
        det = float(np.linalg.det(np.array(ob.matrix_world.to_3x3())))
        tot["objects"] += 1
        tot["pieces"] += r["pieces"]
        tot["inward"] += r["inward"]
        tot["faces"] += r["faces"]
        tot["inward_faces"] += r["inward_faces"]
        tot["triangles"] += r["triangles"]
        tot["inward_triangles"] += int(round(r["inward_area_frac"]
                                             * r["triangles"]))
        tot["flat"] += r["flat"]
        tot["sheet_pieces"] = tot.get("sheet_pieces", 0) + r.get("sheet_pieces", 0)
        tot["undecidable"] = tot.get("undecidable", 0) + r.get("undecidable", 0)
        tot["inconsistent_edges"] += r["inconsistent_edge_pairs"]
        tot["flipped"] += r.get("flipped", 0)
        tot["mirrored_by_matrix"] += 1 if det < 0 else 0
        tot["statistics_disagree"] += 0 if r["statistics_agree"] else 1
        if r["inward"] or r["inconsistent_edge_pairs"] or det < 0:
            per.append({"object": ob.name, "mesh": me.name,
                        "pieces": r["pieces"], "inward": r["inward"],
                        "inward_faces": r["inward_faces"],
                        "inward_area_frac": round(r["inward_area_frac"], 6),
                        "inconsistent_edge_pairs": r["inconsistent_edge_pairs"],
                        "matrix_det": round(det, 6)})
    tot["inward_area_frac"] = (tot["inward_faces"] / tot["faces"]
                               if tot["faces"] else 0.0)
    if rays:
        # THE QUESTION A COUNT CANNOT ANSWER. An inward piece BURIED inside
        # solid geometry costs nothing; a cavity liner emitted as its own closed
        # shell is LEGITIMATELY inward and flipping it would BE the defect; a
        # reversed head shell is the whole reason this file exists. Only a first
        # hit tells them apart, so every back-facing hit is attributed to the
        # piece it came from.
        #
        # Scoped by OBJECT, never by triangle: a subsample makes "first hit"
        # mean nothing, so it takes whole objects, largest first, up to a cap.
        big = sorted(objs, key=lambda o: len(o.data.polygons), reverse=True)
        pick, n = [], 0
        for o in big:
            if n + len(o.data.polygons) > 400000 and pick:
                break
            pick.append(o)
            n += len(o.data.polygons)
        tot["ray"] = ray_attribute(pick, rays)
        tot["ray"]["objects"] = len(pick)
    return tot, per


def plant_fault(objs):
    """Reverse the biggest piece of the biggest object. Positive control."""
    if not objs:
        return None
    ob = max(objs, key=lambda o: len(o.data.polygons))
    me = ob.data
    r = K.mesh_winding_report(me)
    pf = r["piece_of_face"]
    big = int(np.bincount(pf, minlength=r["pieces"]).argmax())
    nl, nf = len(me.loops), len(me.polygons)
    lv = np.empty(nl, np.int32); me.loops.foreach_get("vertex_index", lv)
    ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
    sel = np.flatnonzero(pf == big)
    out = lv.copy()
    for f in sel:
        s, c = int(ls[f]), int(lt[f])
        out[s:s + c] = lv[s:s + c][::-1]
    me.loops.foreach_set("vertex_index", out)
    me.update()
    me.update_tag()
    return {"object": ob.name, "piece": big, "faces_reversed": int(len(sel)),
            "of_faces": int(nf)}


def ray_attribute(objs, n_rays, seed=7):
    """inside_out_fraction, but every back-facing hit is named."""
    VS, FS, lab, base = [], [], [], 0
    for ob in objs:
        r = K.mesh_winding_report(ob.data, with_tri_piece=True)
        if not r.get("triangles"):
            continue
        P = r["verts"]
        M = np.array(ob.matrix_world)
        P = P @ M[:3, :3].T + M[:3, 3]
        T = r["tri_index"].astype(np.int64)
        # SAME COMPENSATION AS itemkit._world_triangles, AND IT WAS MISSING HERE
        # FOR ONE PASS. A negative-determinant matrix reverses winding in world
        # space and Cycles flips the normal back, so not doing this read
        # `grandstand_riser_unit` -- the one object in 30 modules with a
        # mirrored matrix -- as 96 % back-facing on geometry the renderer is
        # perfectly happy with. Two code paths, one rule.
        if float(np.linalg.det(M[:3, :3])) < 0.0:
            T = T[:, ::-1].copy()
        VS.append(P)
        FS.append(T + base)
        base += len(P)
        lab.append((ob.name, r["tri_piece"], r["inward_mask"]))
    if not VS:
        return {"rays": 0, "hits": 0, "back": 0, "fraction": 0.0}
    V = np.concatenate(VS)
    F = np.concatenate(FS)
    out = K.inside_out_fraction(n_rays=n_rays, seed=seed, verts=V, tris=F,
                                return_hits=True)
    # attribute
    offs, acc = [], 0
    for (nm, tp, inw), f in zip(lab, FS):
        offs.append((acc, acc + len(f), nm, tp, inw))
        acc += len(f)
    named = {}
    for idx, isback in zip(out.pop("hit_tri", []), out.pop("hit_back", [])):
        if not isback:
            continue
        for a, b, nm, tp, inw in offs:
            if a <= idx < b:
                key = "%s#piece%d" % (nm, int(tp[idx - a]))
                named[key] = named.get(key, 0) + 1
                break
    out["back_by_piece"] = dict(sorted(named.items(), key=lambda kv: -kv[1])[:20])
    return out


def _welded_components(wid, T):
    """Connected components of the surface AFTER welding by position.

    `mesh_winding_report`'s `tri_piece` cannot be used for this. It labels the
    raw index space, and `extrude` deliberately gives each end cap its own
    copy of the ring vertices, so every solid in `timing_stand` arrives split
    into three "pieces": an open side tube and two loose fans. Ask whether the
    piece holding a facet is closed and the answer is always no.

    Label propagation with pointer jumping, because a Python union-find over
    three million triangles costs half a minute and this costs a second.
    """
    E = np.concatenate([T[:, (0, 1)], T[:, (1, 2)], T[:, (2, 0)]])
    a, b = wid[E[:, 0]], wid[E[:, 1]]
    lab = np.arange(int(wid.max()) + 1, dtype=np.int64)
    for _ in range(64):
        prev = lab
        m = np.minimum(lab[a], lab[b])
        lab = lab.copy()
        np.minimum.at(lab, a, m)
        np.minimum.at(lab, b, m)
        lab = lab[lab]                                  # pointer jumping
        if np.array_equal(lab, prev):
            break
    return lab[wid[T[:, 0]]]


def _piece_is_outward_solid(Pw, T, pc, p):
    """Is connected piece `p` a CLOSED surface wound outward?

    THE ONE QUESTION THAT SPLITS A GROOVE FROM AN UPSIDE-DOWN SLAB, and it
    took three wrong answers to find. A cavity milled into a member has an
    up-facing floor under a down-facing lip -- the exact signature of an
    inverted slab -- and neither footprint, nor separation, nor a parity ray
    tells them apart. What does: the piece the facets belong to. If that piece
    is a closed solid whose own volume comes out POSITIVE, the member is right
    way round and the pair is a feature of it, not a defect in it.

    `enclosure_q` cannot stand in for this and I tried it first. It is
    `|vol| / area**1.5`, so it measures CHUNKINESS, not closure: a 4.5 m
    purlin scores 0.0025 against a `q_min` of 0.005 and is classed a sheet
    despite being a perfectly closed extrusion. Closure is the property that
    makes a volume sign mean something, and it is exact and cheap -- every
    welded edge used exactly twice.

    And it leaves the case this file exists for untouched, which is the test
    of the rule: `extrude` gives each cap its own vertices, so a deck slab's
    top face is its own OPEN piece, closure fails, and the question stays open
    for the parity arm. `pont_deck_slab`'s welded slab is closed but its
    volume is negative when it is inverted, so that fails too. One rule, three
    geometries, right answer on each.
    """
    s = np.flatnonzero(pc == p)
    if not len(s):
        return False
    F = T[s]
    V = Pw
    sub = np.unique(F)
    _, wid = np.unique(np.round(V[sub], 6), axis=0, return_inverse=True)
    ren = np.zeros(int(sub.max()) + 1, np.int64)
    ren[sub] = np.asarray(wid).ravel()
    W = ren[F]
    E = np.concatenate([W[:, (0, 1)], W[:, (1, 2)], W[:, (2, 0)]])
    E = E[E[:, 0] != E[:, 1]]
    if not len(E):
        return False
    nw = int(W.max()) + 1
    key = np.sort(E, axis=1)
    ukey = key[:, 0] * nw + key[:, 1]
    _, cnt = np.unique(ukey, return_counts=True)
    if not np.all(cnt == 2):
        return False                       # open or non-manifold: no volume
    # and wound consistently: every directed edge exactly once
    _, dcnt = np.unique(E[:, 0] * nw + E[:, 1], return_counts=True)
    if not np.all(dcnt == 1):
        return False
    P = V[F]
    c = P.reshape(-1, 3).mean(0)
    vol = float(np.einsum("ij,ij->i", P[:, 0] - c,
                          np.cross(P[:, 1] - c, P[:, 2] - c)).sum()) / 6.0
    return vol > 0.0


def _column(Pw, T):
    """Precompute what every ray in this mesh needs. Hoisted out of the probe
    loop because `Pw[T]` on a 4.8 M triangle deck is 350 MB a call."""
    tri = Pw[T]
    x = tri[:, :, 0]
    y = tri[:, :, 1]
    # the ray only ever hits a triangle with area in plan
    ar2 = ((x[:, 1] - x[:, 0]) * (y[:, 2] - y[:, 0])
           - (x[:, 2] - x[:, 0]) * (y[:, 1] - y[:, 0]))
    return (tri, x.min(1), x.max(1), y.min(1), y.max(1),
            np.abs(ar2) > 1e-12)


def _ray_crossings(col, px, py):
    """Every z at which the vertical line through (px, py) meets the mesh.

    ONE implementation, so the controls in `sheet_facing_selftest` count with
    exactly the arithmetic the audit uses and cannot drift away from it.

    NOTE THE INCLUSIVE `>= 0`: a hit landing on an edge shared by two
    triangles satisfies it for BOTH and is counted twice. That is not
    hypothetical -- it is what makes `hospitality_deck` report an odd
    crossing count on a mesh with zero boundary edges. Left as it is here
    because changing it changes every live gate verdict at once; the count
    is now reported rather than diagnosed. See `_material_between`.
    """
    tri, xmin, xmax, ymin, ymax, live = col
    m = live & (xmin <= px) & (px <= xmax) & (ymin <= py) & (py <= ymax)
    idx = np.flatnonzero(m)
    if not len(idx):
        return np.zeros(0)
    tt = tri[idx]
    x0, y0 = tt[:, 0, 0], tt[:, 0, 1]
    x1, y1 = tt[:, 1, 0], tt[:, 1, 1]
    x2, y2 = tt[:, 2, 0], tt[:, 2, 1]
    d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    ok = np.abs(d) > 1e-15
    a = np.where(ok, ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2))
                 / np.where(ok, d, 1.0), -1.0)
    b = np.where(ok, ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2))
                 / np.where(ok, d, 1.0), -1.0)
    c = 1.0 - a - b
    hit = ok & (a >= 0) & (b >= 0) & (c >= 0)
    if not hit.any():
        return np.zeros(0)
    return (a * tt[:, 0, 2] + b * tt[:, 1, 2] + c * tt[:, 2, 2])[hit]


def _material_between(Pw, T, lo, hi, n_probe=5, note=None):
    """Is there SOLID between these two facets, or is it a groove?

    THE FALSE POSITIVE THIS EXISTS TO KILL. "Upper facet faces down, lower
    facet faces up" is the signature of a slab built upside down. It is ALSO
    the signature of a perfectly correct SLOT: the floor of a groove faces up
    and the underside of the lip above it faces down, and the two have the same
    footprint and the same area. Measured on `timing_stand`: the T-slot
    extrusion its purlins are swept from produced 15 such pairs, on five
    stands, and calling them inverted would have been a fabricated defect on
    geometry that is right.

    The two cases differ in exactly one way and it has nothing to do with
    winding -- which matters, because winding is the thing under test. Between
    the faces of a slab there is MATERIAL; between the faces of a slot there is
    AIR. So: fire a vertical ray from between them and count crossings above
    it. Odd is inside. Parity does not care which way any face is wound, so
    this arm cannot be fooled by the defect it is helping to find.

    Sampled at several points and taken by majority, because a single probe on
    a facet edge or through a bolt hole is a coin toss.

    RETURNS `True` / `False` / `None`. Parity is only meaningful on a surface
    that bounds a region, and the caller establishes that separately with
    a closure test on the pair's own welded component before trusting an
    answer -- see `_piece_is_outward_solid` and `sheet_facing`. This
    returns `None` when its own probes disagree or cannot find the column.

    AND IT SAYS WHICH, into `note`, BECAUSE THE THREE CAUSES NEED OPPOSITE
    FIXES AND THE VERDICT USED TO NAME A FOURTH THAT IS NOT MEASURED HERE.
    Until R2-1861 the `UNDECIDED` line reported every abstention as "sit on
    self-intersecting geometry where no inside/outside answer exists", which
    this function never looks for and which CANNOT produce the abstention:
    parity's crossing count is a mod-2 invariant, so two interpenetrating
    CLOSED solids still cross a ray an even number of times.  Measured, with
    this counter, in the controls below: a self-intersection gives 4
    crossings and a WRONG answer, never an odd count.

    THE REASONS ARE NAMED FOR WHAT WAS COUNTED, NOT FOR A CAUSE, which is the
    whole lesson.  `ODD_CROSSING_COUNT` is deliberately not called "not
    watertight": measured on `hospitality_deck`, the five pairs that set it
    are on meshes with **0 boundary edges and 0 edges used an odd number of
    times** -- mod-2 closed, so no generic ray can cross them an odd number
    of times.  What happens instead is that the probe lands exactly on a
    shared triangle edge, where `a >= 0 and b >= 0 and c >= 0` is true for
    BOTH adjacent triangles and one crossing is counted twice.  Move the ray
    0.5 mm and 12 of 12 jittered rays counted 6 where the probe counted 7.

        DECIDED                  parity ruled
        ODD_CROSSING_COUNT       odd count on most probes -- a hit counted
                                 twice, or a surface that really is open;
                                 this arm does not distinguish them
        PROBES_DISAGREE          probes split evenly, inside vs outside
        NO_PROBE_FOUND_A_COLUMN  no probe found any triangle to cross
    """
    zq = 0.5 * (lo["z"] + hi["z"])
    col = _column(Pw, T)
    inside = outside = leaky = 0
    ups = hi["tris"]
    step = max(1, len(ups) // n_probe)
    probes = ups[::step][:n_probe]
    for t in probes:
        p = Pw[T[t]].mean(0)                      # centroid of a real facet tri
        zh = _ray_crossings(col, float(p[0]), float(p[1]))
        if not len(zh):
            continue
        if len(zh) % 2:
            leaky += 1                 # not watertight along this ray
            continue
        if int((zh > zq + 1e-7).sum()) % 2:
            inside += 1
        else:
            outside += 1
    if note is not None:
        note.update(inside=inside, outside=outside, leaky=leaky,
                    probes=int(len(probes)))
    if leaky > inside + outside:
        if note is not None:
            note["reason"] = "ODD_CROSSING_COUNT"
        return None
    if inside == outside:
        if note is not None:
            note["reason"] = ("NO_PROBE_FOUND_A_COLUMN" if inside == 0
                              else "PROBES_DISAGREE")
        return None
    if note is not None:
        note["reason"] = "DECIDED"
    return inside > outside


def _facets(tris):
    """Label connected runs of triangles. `tris` is (k, 3) WELDED indices.

    Label propagation with pointer jumping, not a union-find. The union-find
    this replaced was a Python loop over every triangle, which is fine on a
    timing stand and is not fine on `pont_deck_slab`, whose deck carries
    104,236 displaced blowholes -- a detector nobody can afford to run is a
    detector nobody runs.
    """
    if not len(tris):
        return np.zeros(0, np.int64)
    idx, ren = np.unique(tris, return_inverse=True)
    W = np.asarray(ren).reshape(-1, 3)
    a = np.concatenate([W[:, 0], W[:, 1], W[:, 2]])
    b = np.concatenate([W[:, 1], W[:, 2], W[:, 0]])
    lab = np.arange(len(idx), dtype=np.int64)
    for _ in range(64):
        prev = lab
        m = np.minimum(lab[a], lab[b])
        lab = lab.copy()
        np.minimum.at(lab, a, m)
        np.minimum.at(lab, b, m)
        lab = lab[lab]
        if np.array_equal(lab, prev):
            break
    _, out = np.unique(lab[W[:, 0]], return_inverse=True)
    return np.asarray(out).ravel()


def sheet_facing(objs, cos_flat=0.99, min_area=0.05):
    """THE CLASS SIGNED VOLUME CANNOT SEE, AND THIS FILE'S REPAIR ABSTAINS ON.

    `winding_audit` decides inward/outward from the SIGN OF A PIECE'S VOLUME,
    and a zero-thickness sheet has no volume -- `enclosure_q` falls under
    `q_min`, the piece is classed `sheet`/`undecidable`, and `--fix` correctly
    leaves it alone.  That is the right call for a lone plate whose "correct"
    side is genuinely undefined.  It is the WRONG call for a plate that is one
    face of a slab, because there the correct side IS defined: by the other
    face.

    MEASURED, `timing_stand`: the repair flipped 1,310 pieces and drove
    `inward_area_frac` 0.3436 -> 0.0, and afterwards `TS_Stand00_BOREAL#piece4721`
    was STILL the largest single back-face contributor in the ray attribution --
    28 of 500 hits, UP from 26.  The number that was being watched went to zero
    while the defect it was watching for got worse.

    So: find every horizontal FACET, pair the ones that share a footprint and
    are separated in z, and report a pair as INVERTED when the UPPER facet
    faces down and the LOWER faces up.  A slab built the right way round is
    silent here; a slab built upside down is a named pair with an area
    attached, and neither verdict depends on a piece being closed.

    FACET, NOT PIECE -- AND THAT CHANGE IS R2-181.
    -----------------------------------------------
    The first version grouped by CONNECTED COMPONENT and took each component's
    area-weighted mean normal.  That only ever works where the walking surface
    happens to BE its own component, which in `timing_stand` it is, because
    `extrude` gives every cap its own copy of the ring vertices.  A module that
    builds its slab as one welded manifold puts the top, the soffit and four
    sides in ONE component whose mean normal cancels to about zero, so the
    component is rejected as "not horizontal" and the module reports **0 flat
    pieces** -- which is what `pont_deck_slab` reported, on a bridge deck.

    Zero because there is nothing wrong and zero because the instrument cannot
    see this shape of geometry are the same line of output, and that is the
    exact failure this file was written to stop making.  So the grouping is now
    over connected runs of NEAR-HORIZONTAL TRIANGLES OF THE SAME SIGN, which
    finds a separate-cap slab and a welded slab alike, and every rejection is
    counted and reported instead of vanishing.
    """
    rows, mesh = [], {}
    rej = {"objects_with_geometry": 0, "triangles": 0,
           "tilted_area_m2": 0.0, "facets_found": 0,
           "facets_under_min_area": 0, "area_under_min_area_m2": 0.0,
           "largest_rejected_facet_m2": 0.0}
    for ob in objs:
        me = ob.data
        r = K.mesh_winding_report(me, with_tri_piece=True)
        if not r.get("triangles"):
            continue
        P = r["verts"]
        T = r["tri_index"].astype(np.int64)
        M = np.array(ob.matrix_world)
        det = float(np.linalg.det(M[:3, :3]))
        Pw = P @ M[:3, :3].T + M[:3, 3]
        n = np.cross(Pw[T[:, 1]] - Pw[T[:, 0]], Pw[T[:, 2]] - Pw[T[:, 0]])
        if det < 0.0:
            n = -n
        L = np.linalg.norm(n, axis=1)
        area = 0.5 * L
        u = n / np.maximum(L, 1e-30)[:, None]
        rej["objects_with_geometry"] += 1
        rej["triangles"] += int(len(T))
        rej["tilted_area_m2"] += float(area[np.abs(u[:, 2]) < cos_flat].sum())
        # weld by position: a facet must not be split by the duplicate ring
        # vertices `extrude` emits for its caps
        _, wid = np.unique(np.round(Pw, 6), axis=0, return_inverse=True)
        wid = np.asarray(wid).ravel()
        for sign in (1.0, -1.0):
            sel = np.flatnonzero(u[:, 2] * sign > cos_flat)
            if not len(sel):
                continue
            lab = _facets(wid[T[sel]])
            for f in np.unique(lab):
                s = sel[lab == f]
                A = float(area[s].sum())
                rej["facets_found"] += 1
                if A < min_area:
                    rej["facets_under_min_area"] += 1
                    rej["area_under_min_area_m2"] += A
                    rej["largest_rejected_facet_m2"] = max(
                        rej["largest_rejected_facet_m2"], A)
                    continue
                mu = float((u[s, 2] * area[s]).sum() / A)
                pts = Pw[T[s].ravel()]
                rows.append({"object": ob.name, "piece": int(f), "area_m2": A,
                             "mean_nz": mu, "tris": s,
                             "z": float(0.5 * (pts[:, 2].min()
                                               + pts[:, 2].max())),
                             "xy": [float(v) for v in
                                    (pts[:, 0].min(), pts[:, 1].min(),
                                     pts[:, 0].max(), pts[:, 1].max())]})
        mesh[ob.name] = [Pw, T, wid, None]
    # pair by footprint
    pairs, used = [], set()
    for i, a in enumerate(rows):
        if i in used:
            continue
        for j in range(i + 1, len(rows)):
            if j in used or rows[j]["object"] != a["object"]:
                continue
            b = rows[j]
            if abs(b["area_m2"] - a["area_m2"]) > 0.02 * max(a["area_m2"], 1e-9):
                continue
            if max(abs(np.array(a["xy"]) - np.array(b["xy"]))) > 0.02:
                continue
            if not (1e-5 < abs(a["z"] - b["z"]) < 0.30):
                continue
            lo, hi = (a, b) if a["z"] < b["z"] else (b, a)
            suspect = bool(hi["mean_nz"] < 0 and lo["mean_nz"] > 0)
            solid = True
            enclosed = False
            note = {"reason": "NOT_SUSPECT"}
            if suspect:
                ent = mesh[a["object"]]
                # IF THE FACETS BELONG TO A CLOSED SOLID THAT VOLUME ALREADY
                # SETTLED AS OUTWARD, THE PAIR CANNOT BE AN INVERTED SLAB.
                #
                # This is the case `sheet_facing` was never meant to judge and
                # must not: a groove, rebate or T-slot cavity inside a member
                # that is demonstrably right way round. `timing_stand`'s
                # purlins are swept from `tslot_section(b, b * 0.62, ...)`,
                # 18.6 mm tall with opposing slots cut deeper than half of
                # that, so the two cavities MEET and the profile runs back
                # along itself at a = +/-0.0081. A vertical ray through the
                # overlap crosses two faces and PARITY DUTIFULLY ANSWERS
                # "inside", on a region both slots have declared void -- 15
                # pairs on five stands, on members that build in isolation as
                # consistent, positive-volume, top-face-up solids.
                #
                # The deck slabs this file exists for are NOT cleared by this,
                # and that is the point: `extrude` gives each cap its own
                # vertices, so a deck slab's top face is its own OPEN piece,
                # closure fails, and the question stays open for parity to
                # answer. One rule, and it splits the two cases exactly.
                Pw, T = ent[0], ent[1]
                if ent[3] is None:      # lazy: only objects with a suspect
                    ent[3] = _welded_components(ent[2], T)
                wc = ent[3]
                enclosed = _piece_is_outward_solid(
                    Pw, T, wc, int(wc[hi["tris"][0]]))
                if enclosed:
                    note["reason"] = "INSIDE_AN_OUTWARD_SOLID"
                else:
                    solid = _material_between(Pw, T, lo, hi, note=note)
            pairs.append({"object": a["object"], "parity": note,
                          "lower_piece": lo["piece"], "upper_piece": hi["piece"],
                          "z_lower": lo["z"], "z_upper": hi["z"],
                          "area_m2": round(a["area_m2"], 5),
                          "lower_nz": round(lo["mean_nz"], 4),
                          "upper_nz": round(hi["mean_nz"], 4),
                          "material_between": solid,
                          "suspect": suspect,
                          "inside_outward_solid": enclosed,
                          "inverted": bool(suspect and not enclosed
                                           and solid is True)})
            used.add(i); used.add(j)
            break
    tot = sum(r["area_m2"] for r in rows)
    down = sum(r["area_m2"] for r in rows if r["mean_nz"] < 0)
    inv = [p for p in pairs if p["inverted"]]
    # NAMED, NOT DISCARDED. These looked like the defect and were cleared by
    # the parity arm; printing the count is how a reader can tell "nothing
    # looked wrong" from "15 things looked wrong and were checked".
    slots = [p for p in pairs if p.get("suspect") and not p["inverted"]
             and (p["inside_outward_solid"] or p["material_between"] is False)]
    undec = [p for p in pairs if p.get("suspect") and not p["inverted"]
             and not p["inside_outward_solid"]
             and p["material_between"] is None]
    # WHY EACH ABSTENTION HAPPENED, COUNTED. `undecidable_pairs: 6` with no
    # cause attached is what let the verdict line invent one -- see
    # `_material_between`. These are the reasons the arm itself recorded.
    reasons = {}
    for p in undec:
        r = p.get("parity", {}).get("reason", "UNRECORDED")
        reasons[r] = reasons.get(r, 0) + 1
    out = {"groove_pairs_cleared": len(slots),
           "undecidable_pairs": len(undec),
           "undecidable_reasons": reasons,
           "undecidable_area_m2": round(sum(p["area_m2"] for p in undec)
                                        * 2.0, 4),
           "undecidable": sorted(undec, key=lambda p: -p["area_m2"])[:20],
           "flat_pieces": len(rows), "flat_area_m2": round(tot, 4),
           "down_facing_area_m2": round(down, 4),
           "slab_pairs": len(pairs), "inverted_pairs": len(inv),
           "inverted_area_m2": round(sum(p["area_m2"] for p in inv) * 2.0, 4),
           "inverted": sorted(inv, key=lambda p: -p["area_m2"])[:40]}
    # WHAT THE THRESHOLDS THREW AWAY. Without this a `flat_pieces: 0` is a
    # dead end -- nobody can tell whether the subject has no horizontal
    # surface, or has one that `cos_flat` called tilted, or has one that
    # `min_area` called small. Now the line says which.
    for k, v in rej.items():
        out[k] = round(v, 4) if isinstance(v, float) else v
    out["cos_flat"] = cos_flat
    out["min_area_m2"] = min_area
    return out


def sheet_facing_selftest():
    """Both controls, on synthetic slabs, before any module is believed.

    A slab built right way round must be SILENT; the same slab with both faces
    swapped must be NAMED. A checker that only ever ran on the broken case
    cannot tell you the broken case is broken.
    """
    import bmesh
    ok = True
    # IT BUILDS AND REMOVES ONLY ITS OWN OBJECTS. The first version wiped the
    # scene, so it ran before `collect()` and the audit then measured an EMPTY
    # blend and printed SHEET_FACING_OK on a module with 20.3 m2 of upside-down
    # deck in it -- a verdict that reads the same whether the subject is present
    # or absent, which is this project's most expensive recurring mistake.
    for tag, invert in (("correct", False), ("inverted", True)):
        me = bpy.data.meshes.new("CTL_slab")
        bm = bmesh.new()
        for z, up in ((0.0, False), (0.028, True)):
            f = 1.0 if (up != invert) else -1.0
            vs = [bm.verts.new((x, y, z)) for x, y in
                  ((0, 0), (2, 0), (2, 2), (0, 2))]
            bm.faces.new(vs if f > 0 else vs[::-1])
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new("CTL_slab", me)
        bpy.context.scene.collection.objects.link(ob)
        r = sheet_facing([ob])
        want = 1 if invert else 0
        got = r["inverted_pairs"]
        print("   CONTROL %-9s slab -> %d inverted pair(s), expected %d  %s"
              % (tag, got, want, "ok" if got == want else "FAIL"))
        ok = ok and got == want
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)

    # A WELDED slab -- top, soffit and four sides in ONE component, which is
    # how `pont_deck_slab` builds a bridge deck. The component-mean-normal
    # version of `sheet_facing` scored this 0 flat pieces and printed
    # UNMEASURED, indistinguishably from a module with no deck at all. Both
    # directions, so the control cannot expire into a pass (R2-072).
    for tag, invert in (("correct", False), ("inverted", True)):
        me = bpy.data.meshes.new("CTL_welded")
        bm = bmesh.new()
        vs0 = [bm.verts.new((x, y, 0.0)) for x, y in
               ((0, 0), (2, 0), (2, 2), (0, 2))]
        vs1 = [bm.verts.new((x, y, 0.028)) for x, y in
               ((0, 0), (2, 0), (2, 2), (0, 2))]
        top, bot = (vs1[::-1], vs0) if invert else (vs1, vs0[::-1])
        bm.faces.new(top)
        bm.faces.new(bot)
        for i in range(4):
            j = (i + 1) % 4
            side = [vs0[i], vs0[j], vs1[j], vs1[i]]
            bm.faces.new(side if not invert else side[::-1])
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new("CTL_welded", me)
        bpy.context.scene.collection.objects.link(ob)
        r = sheet_facing([ob])
        want = 1 if invert else 0
        got = r["inverted_pairs"]
        good = got == want and r["flat_pieces"] == 2
        print("   CONTROL %-9s WELDED slab -> %d flat facet(s), %d inverted "
              "pair(s), expected 2 and %d  %s"
              % (tag, r["flat_pieces"], got, want, "ok" if good else "FAIL"))
        ok = ok and good
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)

    # THE GROOVE. A slot's floor faces up and the lip above it faces down --
    # the same signature as an upside-down slab, and the reason the parity arm
    # exists. A correct grooved bar must be SILENT, and the slab sitting in the
    # same file must still be NAMED, or the arm has simply been turned off.
    # The profile is a 2.0 m bar, 0.30 x 0.10, with a REBATE cut in from one
    # side: an up-facing strip at z 0.030 and a down-facing strip of exactly
    # the same width 6.4 mm above it, with AIR between. That is the shape
    # `timing_stand`'s T-slot purlins actually produce, reproduced here rather
    # than described. Its outer top/bottom pair is a genuine slab, so the same
    # object carries both cases.
    PROF = [(-0.15, 0.0), (0.15, 0.0), (0.15, 0.030), (0.05, 0.030),
            (0.05, 0.0364), (0.15, 0.0364), (0.15, 0.10), (-0.15, 0.10)]
    for tag, flip, want_inv, want_cleared in (
            ("grooved bar", False, 0, 1),
            ("grooved bar FLIPPED", True, 1, 0)):
        me = bpy.data.meshes.new("CTL_slot")
        bm = bmesh.new()
        rings = [[bm.verts.new((x, y, z)) for y, z in PROF]
                 for x in (-1.0, 1.0)]
        mm = len(PROF)
        for i in range(mm):
            j = (i + 1) % mm
            f = [rings[0][i], rings[0][j], rings[1][j], rings[1][i]]
            bm.faces.new(f[::-1] if flip else f)
        bm.faces.new(rings[0] if flip else rings[0][::-1])
        bm.faces.new(rings[1][::-1] if flip else rings[1])
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new("CTL_slot", me)
        bpy.context.scene.collection.objects.link(ob)
        r = sheet_facing([ob], min_area=0.02)
        got, cleared = r["inverted_pairs"], r["groove_pairs_cleared"]
        good = got >= want_inv and cleared >= want_cleared \
            and (got == 0 or want_inv)
        print("   CONTROL %-20s -> %d inverted pair(s) (want %d), %d groove "
              "pair(s) cleared by parity (want %d)  %s"
              % (tag, got, want_inv, cleared, want_cleared,
                 "ok" if good else "FAIL"))
        ok = ok and good
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)

    # WHAT AN ABSTENTION MEANS, AND WHAT IT IS NOT (R2-1861). The verdict
    # line used to report every `UNDECIDED` as "sit on self-intersecting
    # geometry where no inside/outside answer exists" -- a cause
    # `_material_between` never measures, and one that CANNOT produce an
    # abstention: ray-crossing parity is a mod-2 invariant, so two
    # interpenetrating CLOSED solids cross a ray an even number of times and
    # the arm answers (wrongly) rather than abstaining.
    #
    # Three columns, hand counted, driven straight into the parity arm so no
    # tessellation choice can move them. The pair is a plate at z 0.40 facing
    # up under a plate at z 0.44 facing down, inside a 1 m box:
    #
    #   A  box with NO LID      floor, 0.40, 0.44                  = 3, ODD
    #                           -> abstains, ODD_CROSSING_COUNT
    #   B  box CLOSED           floor, 0.40, 0.44, lid             = 4, even
    #                           -> DECIDED
    #   C  box CLOSED, with a second CLOSED BOX DRIVEN THROUGH ITS LID, on
    #      the probe line -- a textbook self-intersection --
    #                           floor, 0.40, 0.44, 0.60, lid, 1.40 = 6, even
    #                           -> DECIDED
    #
    # C is the arm that matters: it is exactly the geometry the old message
    # blamed, and it does not produce the verdict the old message explained.
    # A is the arm that fires. An abstention may never again be reported as a
    # self-intersection without one of these three moving.
    def _quads(qs):
        t = []
        for a, b, c, d in qs:
            t += [(a, b, c), (a, c, d)]
        return t

    def _prism(x0, y0, x1, y1, z0, z1, lid=True):
        V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        q = [(0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5),
             (2, 3, 7, 6), (3, 0, 4, 7)]
        if lid:
            q.append((4, 5, 6, 7))
        return V, _quads(q)

    for tag, lid, intruder, want_reason, want_n in (
            ("plate pair in a box with NO LID", False, False,
             "ODD_CROSSING_COUNT", 3),
            ("plate pair in a CLOSED box", True, False, "DECIDED", 4),
            ("...and a CLOSED BOX DRIVEN THROUGH IT (self-intersecting)",
             True, True, "DECIDED", 6)):
        V, T = [], []

        def add(vt):
            o = len(V)
            V.extend(vt[0])
            T.extend([(a + o, b + o, c + o) for a, b, c in vt[1]])
        add(_prism(0.0, 0.0, 1.0, 1.0, 0.0, 1.0, lid=lid))
        # the lower plate is deliberately NOT congruent with the upper one.
        # Congruent rectangles put the upper triangle's centroid exactly on
        # the lower one's diagonal, where `a >= 0 and b >= 0 and c >= 0` is
        # true for BOTH adjacent triangles and one crossing is counted twice
        # -- which is the real fault behind `hospitality_deck`'s six pairs,
        # and would silently make this control count 4 where it says 3.
        add(([(0.15, 0.20, 0.40), (0.85, 0.20, 0.40),
              (0.85, 0.80, 0.40), (0.15, 0.80, 0.40)], _quads([(0, 1, 2, 3)])))
        base = len(T)
        add(([(0.20, 0.20, 0.44), (0.80, 0.20, 0.44),
              (0.80, 0.80, 0.44), (0.20, 0.80, 0.44)], _quads([(0, 3, 2, 1)])))
        if intruder:
            add(_prism(0.30, 0.30, 0.70, 0.70, 0.60, 1.40))
        Pw = np.array(V, float)
        Ti = np.array(T, np.int64)
        hi = {"z": 0.44, "tris": np.array([base, base + 1])}
        note = {}
        got = _material_between(Pw, Ti, {"z": 0.40}, hi, note=note)
        n = len(_ray_crossings(_column(Pw, Ti), 0.6, 0.4))
        good = note.get("reason") == want_reason and n == want_n \
            and (got is None) == (want_reason == "ODD_CROSSING_COUNT")
        print("   CONTROL %-56s -> %d crossings (want %d), reason %-18s "
              "(want %-18s) %s"
              % (tag, n, want_n, note.get("reason"), want_reason,
                 "ok" if good else "FAIL"))
        ok = ok and good

    # THE THRESHOLDS, STATED RATHER THAN ASSUMED. `cos_flat` and `min_area`
    # are the two ways a real deck can be excluded without a word being
    # printed, so both are exercised on either side of their own bound. This
    # is what `pont_deck_slab`'s "0 flat pieces" needed and did not have.
    for tag, tilt_deg, side, want_seen in (("just inside cos_flat", 6.0,
                                            "inside", True),
                                           ("just outside cos_flat", 10.0,
                                            "outside", False)):
        me = bpy.data.meshes.new("CTL_tilt")
        bm = bmesh.new()
        t = math.tan(math.radians(tilt_deg))
        for z in (0.0, 0.028):
            vs = [bm.verts.new((x, y, z + x * t)) for x, y in
                  ((0, 0), (2, 0), (2, 2), (0, 2))]
            bm.faces.new(vs if z > 0 else vs[::-1])
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new("CTL_tilt", me)
        bpy.context.scene.collection.objects.link(ob)
        r = sheet_facing([ob])
        seen = r["flat_pieces"] > 0
        print("   CONTROL %-22s (%.1f deg, %s the %.2f bound) -> %d facet(s) "
              "seen, expected %s  %s"
              % (tag, tilt_deg, side, math.degrees(math.acos(0.99)),
                 r["flat_pieces"], "some" if want_seen else "none",
                 "ok" if seen == want_seen else "FAIL"))
        ok = ok and seen == want_seen
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)

    for tag, side_m, want_seen in (("just over min_area", 0.30, True),
                                   ("just under min_area", 0.20, False)):
        me = bpy.data.meshes.new("CTL_small")
        bm = bmesh.new()
        for z in (0.0, 0.028):
            vs = [bm.verts.new((x, y, z)) for x, y in
                  ((0, 0), (side_m, 0), (side_m, side_m), (0, side_m))]
            bm.faces.new(vs if z > 0 else vs[::-1])
        bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new("CTL_small", me)
        bpy.context.scene.collection.objects.link(ob)
        r = sheet_facing([ob])
        seen = r["flat_pieces"] > 0
        print("   CONTROL %-22s (%.3f m2 vs the 0.05 m2 bound) -> %d facet(s) "
              "seen, expected %s  %s"
              % (tag, side_m * side_m, r["flat_pieces"],
                 "some" if want_seen else "none",
                 "ok" if seen == want_seen else "FAIL"))
        ok = ok and seen == want_seen
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)
    return ok


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--item", default=None)
    ap.add_argument("--collection", default=None)
    ap.add_argument("--rays", type=int, default=0)
    ap.add_argument("--plant-fault", action="store_true",
                    help="POSITIVE CONTROL, IN SITU. Reverse the winding of "
                         "the largest piece of the largest object and audit "
                         "that. A synthetic sphere proves the arithmetic; this "
                         "proves the instrument fires on THIS module's real "
                         "geometry, at its real scale, through the same code "
                         "path -- and that the ray statistic moves with it. "
                         "Never saved.")
    ap.add_argument("--sheet-facing", action="store_true",
                    help="report horizontal SHEETS whose normal points at the "
                         "ground, and slab pairs built upside down. See "
                         "`sheet_facing` -- signed volume is blind to this "
                         "class and `--fix` abstains on it by design.")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--cos-flat", type=float, default=0.99,
                    help="how far from horizontal a facet may lean and still "
                         "count. 0.99 = 8.1 deg. Both sides of this bound are "
                         "exercised by the controls every run.")
    ap.add_argument("--min-area", type=float, default=0.05,
                    help="smallest facet worth pairing, m2. What it drops is "
                         "COUNTED and printed, so a zero can be explained.")
    ap.add_argument("--save", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    t0 = time.time()
    if a.sheet_facing:
        why = {}
        objs = collect(a.collection, a.item, why)
        sf = sheet_facing(objs, cos_flat=a.cos_flat, min_area=a.min_area)
        sf["controls_pass"] = sheet_facing_selftest()
        sf["objects_audited"] = len(objs)
        sf["subject"] = why
        ctl = sf["controls_pass"]
        txt = json.dumps({"item": a.item, "blend": bpy.data.filepath,
                          "sheet_facing": sf,
                          "seconds": round(time.time() - t0, 1)}, indent=1)
        print(txt)
        if a.out:
            os.makedirs(os.path.dirname(a.out), exist_ok=True)
            open(a.out, "w", encoding="utf-8").write(txt)
        # FOUR OUTCOMES, NOT THREE, BECAUSE "COULD NOT LOOK" HAS TWO CAUSES
        # AND THEY NEED OPPOSITE FIXES. `NO_SUBJECT` means the sweep never
        # read the module -- fix the sweep. `UNMEASURED` means it read it and
        # found nothing horizontal -- fix the thresholds, or the module has no
        # deck. R2-117: a field with fewer cells than there are outcomes
        # writes two different findings to disk as the same word.
        if not ctl:
            verdict, why_txt = "CONTROL_FAIL", "the synthetic controls failed"
        elif not sf["objects_audited"]:
            verdict = "NO_SUBJECT"
            why_txt = ("0 mesh objects collected; subject chosen by %s"
                       % why.get("source"))
        elif not sf["flat_pieces"]:
            verdict = "UNMEASURED"
            why_txt = ("%d objects / %d triangles read, %d facets found, "
                       "%d dropped under min_area=%.3f m2 (largest dropped "
                       "%.4f m2), %.3f m2 rejected as tilted beyond "
                       "cos_flat=%.3f"
                       % (sf["objects_with_geometry"], sf["triangles"],
                          sf["facets_found"], sf["facets_under_min_area"],
                          sf["min_area_m2"], sf["largest_rejected_facet_m2"],
                          sf["tilted_area_m2"], sf["cos_flat"]))
        elif sf["inverted_pairs"]:
            verdict, why_txt = "DIRTY", "upper facet faces the ground"
        elif sf["undecidable_pairs"]:
            # NOT a pass. The pairs look like the defect and the parity arm
            # would not rule either way. IT NOW SAYS WHY IT WOULD NOT, in its
            # own words. This line used to assert "self-intersecting geometry
            # where no inside/outside answer exists" for every abstention --
            # a cause `_material_between` never measures and, worse, one that
            # cannot produce an abstention at all: a ray through two
            # interpenetrating CLOSED solids crosses 4 faces, which is even,
            # so parity answers (wrongly) rather than abstaining. Both arms
            # are controls below. Reported as UNDECIDED_*, never diagnosed.
            verdict = "UNDECIDED"
            why_txt = ("%d pair(s), %.3f m2, look inverted and the parity arm "
                       "abstained -- %s; %d groove pair(s) cleared"
                       % (sf["undecidable_pairs"], sf["undecidable_area_m2"],
                          ", ".join("%s x%d" % kv for kv in
                                    sorted(sf["undecidable_reasons"].items()))
                          or "no reason recorded",
                          sf["groove_pairs_cleared"]))
        else:
            verdict = "OK"
            why_txt = ("%d slab pairs, all upper faces up; %d groove pair(s) "
                       "cleared by parity"
                       % (sf["slab_pairs"], sf["groove_pairs_cleared"]))
        print(">> SUBJECT: %s%s" % (why.get("source"),
                                    "" if not why.get("collection")
                                    else " -> %s" % why["collection"]))
        if why.get("rejected_other_items"):
            print(">> NOTE: item-prefixed collections exist but none names "
                  "%r: %s" % (a.item, why["rejected_other_items"]))
        print(">> STAGE RESULT: SHEET_FACING_%s (%d objects, %d flat facets, "
              "%d inverted slab pairs, %.3f m2) -- %s"
              % (verdict, sf["objects_audited"], sf["flat_pieces"],
                 sf["inverted_pairs"], sf["inverted_area_m2"], why_txt))
        return
    objs = collect(a.collection, a.item)
    planted = None
    if a.plant_fault:
        planted = plant_fault(objs)
    before, per_before = audit(objs, rays=a.rays, fix=False)
    if planted:
        before["planted_fault"] = planted
    rep = {"item": a.item, "blend": bpy.data.filepath, "before": before,
           "offenders": per_before[:200], "n_offenders": len(per_before)}
    if a.fix:
        after, per_after = audit(objs, rays=a.rays, fix=True)
        # audit() with fix=True reports the state it FOUND; re-run clean
        after2, per_after2 = audit(objs, rays=a.rays, fix=False)
        rep["repaired"] = after["flipped"]
        rep["after"] = after2
        rep["n_offenders_after"] = len(per_after2)
        if a.save:
            bpy.ops.wm.save_as_mainfile(filepath=a.save)
            rep["saved"] = a.save
    elif a.plant_fault and a.save:
        # the control scene, for rendering. Never overwrites the source.
        bpy.ops.wm.save_as_mainfile(filepath=a.save)
        rep["saved"] = a.save
    rep["seconds"] = round(time.time() - t0, 1)
    txt = json.dumps(rep, indent=1)
    print("WINDING_AUDIT_JSON_BEGIN")
    print(txt)
    print("WINDING_AUDIT_JSON_END")
    if a.out:
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(txt)



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
    gate_exit.guard(main, tool="winding_audit")
