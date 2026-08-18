"""SELF-INTERSECTION AUDIT -- WITHIN a connected piece, or BETWEEN pieces?

    blender -b --factory-startup -P tools/selfintersect_audit.py -- <out.json>

Defect #120. Edit TARGETS, or import `analyse()`.

A raw self-intersecting-face-pair count over a whole object is not evidence of a
defect. `HD_Deck_*` are 2-4.8 M-triangle ASSEMBLIES -- boards, composite, trim,
stainless, glass, cable, grit -- welded into one object. A cable passing through
a deck board is two parts touching, which is what assembled geometry looks like.
Counting those as self-intersections would be a fabricated defect on geometry
that is right, which is the exact false positive `winding_audit._material_between`
was written to kill.

The question with an actual answer is:

    do faces of the SAME connected piece cross each other?

That is where inside/outside genuinely has no answer, because a single shell that
passes through itself has no consistent parity and no consistent winding number.
Between two pieces, inside/outside is perfectly well defined for each piece
separately.

KNOWN LIMIT, AND IT IS DISQUALIFYING: this is a BROAD-PHASE detector. Control
K4 fails deliberately -- two sub-parts sitting exactly flush, with zero
penetration, are reported as 7 crossings. Numbers from this tool are an upper
bound contaminated by flush and grazing contact, not self-intersection counts.
The controls gate the artefact run, so it refuses rather than reporting one.

Judge only on the printed `>> STAGE RESULT:` line.
"""
import os
import sys
import json
import time

import bpy
import bmesh
import numpy as np
from mathutils.bvhtree import BVHTree

OUT = sys.argv[-1]
ctrl, rows = [], []


def components(nv, E, tag=""):
    """Connected-component label per vertex. Shiloach-Vishkin pointer jumping.

    Convergence is ASSERTED, not assumed: a component finder that quietly
    returns a half-merged labelling would split single pieces into many and
    report every real self-intersection as a between-piece contact -- i.e. it
    would silently produce the reassuring answer.
    """
    p = np.arange(nv, dtype=np.int64)
    if len(E) == 0:
        return p
    for it in range(200):
        a, b = p[E[:, 0]], p[E[:, 1]]
        np.minimum.at(p, a, b)
        np.minimum.at(p, b, a)
        for _ in range(64):
            q = p[p]
            if np.array_equal(q, p):
                break
            p = q
        a, b = p[E[:, 0]], p[E[:, 1]]
        if np.array_equal(a, b):
            return p
    raise RuntimeError("component finder did not converge%s" % tag)


def analyse(verts, polys, name):
    """-> (total crossing pairs, pairs within one piece, n pieces)."""
    V = np.asarray(verts, dtype=np.float64)
    F = np.asarray(polys, dtype=np.int64)
    # weld by position: `extrude` gives caps their own vertices, so index
    # identity understates connectivity and would inflate the piece count.
    _, wid = np.unique(np.round(V, 6), axis=0, return_inverse=True)
    W = wid[F]
    E = np.concatenate([W[:, (0, 1)], W[:, (1, 2)], W[:, (2, 0)]])
    lab = components(int(wid.max()) + 1, E, " on " + name)
    fcomp = lab[W[:, 0]]

    bvh = BVHTree.FromPolygons([tuple(v) for v in verts],
                               [tuple(p) for p in polys],
                               all_triangles=False, epsilon=0.0)
    pv = [set(p) for p in polys]
    tot = within = 0
    for a, b in bvh.overlap(bvh):
        if a >= b or (pv[a] & pv[b]):
            continue
        tot += 1
        if fcomp[a] == fcomp[b]:
            within += 1
    return tot, within, len(np.unique(fcomp))


def cube(ox=0.0, oy=0.0):
    v = [(ox + x, oy + y, z) for x in (0., 1.) for y in (0., 1.) for z in (0., 1.)]
    f = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1),
         (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4), (1, 5, 7), (1, 7, 3)]
    return v, f


def control(name, verts, polys, want, note):
    tot, within, npieces = analyse(verts, polys, name)
    ok = want(tot, within, npieces)
    ctrl.append({"control": name, "total": tot, "within": within,
                 "pieces": npieces, "pass": ok, "note": note})
    print("   %-4s %-52s total=%-5d within=%-5d pieces=%-3d  %s"
          % ("PASS" if ok else "FAIL", name, tot, within, npieces, note))
    return ok


print(">> CONTROLS: the WITHIN arm must be able to say both 0 and not-0")

v, f = cube()
control("K1 clean closed box", v, f,
        lambda t, w, n: t == 0 and w == 0 and n == 1, "one piece, no crossings")

# K4 IS THE ONE THAT MATTERS AND IT FAILS. Added after the fact, when a peer
# session's #120 answer showed this tool's numbers were inflated.
#
# `BVHTree.overlap` is a BROAD PHASE. It reports every pair whose triangles'
# bounds meet -- including two sub-parts sitting exactly FLUSH, which is not a
# self-intersection at all and is how this deck is built: thousands of closed
# solids accumulated by `acc.solid(...)`, bolts proud of tread pans, tubes
# socketed into posts, never booleaned. Blender stores coordinates as float32,
# so faces MEANT to be flush land ~1e-6 m apart while their intersection segment
# is still tens of centimetres long: length cannot separate contact from
# penetration, only DEPTH can.
#
# This tool has no narrow phase and no depth gate, so it cannot make that
# distinction, and on this geometry that distinction is the whole question.
# K1-K3 could not catch it: they test whether a real crossing is seen and
# whether piece-splitting works, and every one of them uses PENETRATING boxes.
# The control set had a hole exactly where the real geometry lives.
#
# It is left FAILING on purpose. Until a Moller narrow phase and a penetration
# -depth gate are added, this tool must not report an artefact number, and a
# failing control is the only honest way to say so. See tools/winding_audit.py,
# whose `_material_between` solved the same problem from the other direction.
v1, f1 = cube(0.0)
vf, ff = cube(0.0)
vf = [(x, y, z + 1.0) for x, y, z in vf]          # sits EXACTLY on top
control("K4 two sub-parts FLUSH, ZERO penetration -> must be 0",
        v1 + vf, f1 + [(a + 8, b + 8, c + 8) for a, b, c in ff],
        lambda t, w, n: t == 0,
        "BROAD PHASE ONLY: reports 7. No narrow phase, no depth gate.")

v2, f2 = cube(0.5)
control("K2 two boxes overlapping, SEPARATE pieces", v1 + v2,
        f1 + [(a + 8, b + 8, c + 8) for a, b, c in f2],
        lambda t, w, n: t > 0 and w == 0 and n == 2,
        "crossings exist but NONE within a piece -- normal assembly")

# K3, second attempt. THE FIRST ONE FAILED AND WAS RIGHT TO.
#
# It dragged one corner of a cube through the opposite face and expected
# crossings. It got zero -- because in a 12-triangle cube nearly every face pair
# SHARES A VERTEX, and shared-vertex pairs are excluded (adjacent faces always
# "overlap" at their shared edge; counting those would call every closed mesh in
# existence self-intersecting). A control too small to have any non-adjacent
# face pairs cannot fire, whatever the geometry does.
#
# So: the two overlapping boxes of K2, BRIDGED into a single connected component
# by a strip of triangles. The crossing faces are now in one piece and still
# share no vertices. Same geometry as K2, one topological change, opposite
# verdict -- which is what makes the pair worth having.
vb = v1 + v2
fb = f1 + [(a + 8, b + 8, c + 8) for a, b, c in f2]
vb = vb + [(0.0, 0.0, 2.0), (1.5, 1.5, 2.0)]
BR0, BR1 = 16, 17
fb = fb + [(0, BR0, BR1), (0, BR1, 8), (BR0, 8, BR1)]
control("K3 the SAME two boxes, BRIDGED into one piece", vb, fb,
        lambda t, w, n: w > 0 and n == 1,
        "the case with no inside/outside answer -- MUST fire")

if not all(c["pass"] for c in ctrl):
    print(">> STAGE RESULT: FAIL (controls failed; no artefact number is trustworthy)")
    json.dump({"controls": ctrl, "rows": []}, open(OUT, "w"), indent=1)
    raise SystemExit(0)
print(">> controls pass: 'within' distinguishes assembly contact from a folded shell\n")

bpy.ops.wm.open_mainfile(filepath=os.path.expanduser("~/f1-round2/world/items/"
                                  "hospitality_deck_test.blend"))
dg = bpy.context.evaluated_depsgraph_get()

TARGETS = ["HD_Deck_1_Versant", "HD_Deck_2_Ardent", "HD_Deck_3_Zephyr",
           "HD_Deck_4_Pallas", "HD_Deck_5_Halcyon", "CTX_Apron"]
for nm in TARGETS:
    o = bpy.data.objects.get(nm)
    if o is None:
        rows.append({"object": nm, "status": "ABSENT"})
        print("   ABSENT %s" % nm)
        continue
    t0 = time.time()
    me = o.evaluated_get(dg).to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    verts = [x.co[:] for x in bm.verts]
    polys = [tuple(x.index for x in fa.verts) for fa in bm.faces]
    bm.free()
    try:
        tot, within, npieces = analyse(verts, polys, nm)
        rows.append({"object": nm, "tris": len(polys), "total_pairs": tot,
                     "within_piece_pairs": within, "pieces": npieces,
                     "status": "OK", "seconds": round(time.time() - t0, 1)})
        print("   %-20s %9d tris  pieces=%-6d total=%-8d WITHIN=%d  (%.0fs)"
              % (nm, len(polys), npieces, tot, within, time.time() - t0))
    except Exception as exc:                                      # noqa: BLE001
        rows.append({"object": nm, "status": "ERROR", "why": repr(exc)})
        print("   ERROR %-20s %r" % (nm, exc))

json.dump({"controls": ctrl, "rows": rows}, open(OUT, "w"), indent=1)
okr = [r for r in rows if r.get("status") == "OK"]
bad = [r for r in okr if r["within_piece_pairs"] > 0]
print("\n>> STAGE RESULT: I120_WITHIN_DONE (%d of %d objects have within-piece "
      "crossings)" % (len(bad), len(okr)))
