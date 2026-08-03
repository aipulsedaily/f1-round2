"""PROBE D — triangle-level BVH interpenetration across module boundaries.

tools/collision_gate.py is written for the SHOWROOM/CAR scene (clusters from
explode_plan.json vs the SHOWROOM/PROPS/LIGHTS collections) and is vacuous on a
world-only assembly.  This is the same question asked of the world: does any
module's solid pass through another module's solid where they meet?
"""
exec(open("/home/zany/f1-round2/render/world/assembly/r2/lib_probe.py").read())

# ------------------------------------------------- WHERE THIS PROBE WRITES --
# Was `save("probeD.json", ...)`. `save()` joins its argument onto
# lib_probe's hardcoded OUT_DIR, so this probe could only ever write to
# probeD.json in the assembly root, whatever it was asked for.
# v120/battery.sh and v121/battery.sh BOTH run this probe with no
# output argument at all, so the v121 run overwrote the probeD.json that
# v120/collect.py reads, and the two versions were then compared
# against each other. Cross-version contamination by design.
#
# It now takes `--out PATH` (a bare positional *.json still works for the
# older chain scripts) and REFUSES to run without one. resolve_out() never
# invents a destination and never strips the directory off the one it was
# given -- the three faults probe_pitexit.py had at once.
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="probeD")
print("[D] output ->", OUT)

# Blender 5.2 returns 0 for a script that raised, so a probe that died halfway
# was indistinguishable from one that finished.  install() arms sys.excepthook
# and an atexit sentinel; done() on the last line disarms it.
sys.path.insert(0, "/home/zany/f1-round2/tools")
import gate_exit                                                 # noqa: E402
gate_exit.install(tool="probeD")

from mathutils.bvhtree import BVHTree

R = {}
T0 = time.time()
D = dg()


def tris(ob, filt=None):
    ev = ob.evaluated_get(D)
    me = ev.to_mesh()
    if me is None:
        return None, None
    me.calc_loop_triangles()
    M = ob.matrix_world
    vs = [M @ v.co for v in me.vertices]
    fs = [tuple(t.vertices) for t in me.loop_triangles]
    if filt is not None:
        keep = []
        for f in fs:
            c = (vs[f[0]] + vs[f[1]] + vs[f[2]]) / 3.0
            if filt(c):
                keep.append(f)
        fs = keep
    ev.to_mesh_clear()
    return vs, fs


def bvh(ob, filt=None):
    vs, fs = tris(ob, filt)
    if not fs:
        return None, 0
    return BVHTree.FromPolygons(vs, fs, all_triangles=True, epsilon=0.0), len(fs)


NAMES = {ob.name for ob in bpy.data.objects if ob.type == "MESH"}
print("[D] meshes", len(NAMES))


def get(nm):
    return bpy.data.objects.get(nm)


PAIRS = []
track = get("SURF_Track")
kerbs = [ob for ob in bpy.data.objects if ob.name.startswith("SURF_Kerb")]
joint = get("SURF_ApronJoint")
access = get("SURF_AccessRoad")
apron = get("ARCH_Paving_ApronPlatform")
struct = [ob for ob in bpy.data.objects
          if ob.type == "MESH" and role(ob.name) == "barrier_struct"]
verge = [ob for ob in bpy.data.objects if ob.name.startswith("BR_Verge")]
ter = get("TER_Ground")

res = {}


# A PAIR LABEL NAMES EXACTLY THE OBJECTS MEASURED.                (R2, 2026-08-02)
#
# The row `ARCH_ApronPlatform x SURF_Track+Joint` lumped TWO different objects
# into one B side, and the conflation nearly produced a false alarm: the row went
# 0 -> 4,624 triangle pairs between assembly2 and assembly5 and read as a rebuild
# regression. Split, it is
#
#     ARCH_Paving_ApronPlatform x SURF_Track        0
#     ARCH_Paving_ApronPlatform x SURF_ApronJoint   4,624
#
# and SURF_ApronJoint did not exist at contract 1.0.1 -- it is the DELIBERATE
# 50 mm apron lap joint added at 1.1.1. Nothing regressed; a new object appeared
# and the row could not say so, because its label named a set instead of a pair.
#
# `test()` now records every constituent object pair in `all_object_pairs`,
# whether or not it overlaps, so a zero is stated rather than inferred from an
# absence -- and a `+` in a label is refused outright.
def test(label, A, B, note=""):
    """A, B are lists of objects.  Reports triangle-pair overlaps."""
    if "+" in label:
        raise SystemExit(
            "REFUSING: pair label %r joins objects with '+'. A label must name "
            "exactly the objects measured, or a count cannot be attributed to "
            "one of them -- see the apron-joint note above." % label)
    t = time.time()
    tot = 0; pairs = []; every = []
    Bt = []
    for b in B:
        if b is None:
            continue
        tb, nb = bvh(b)
        if tb is not None:
            Bt.append((b.name, tb, nb))
    for a in A:
        if a is None:
            continue
        ta, na = bvh(a)
        if ta is None:
            continue
        for bn, tb, nb in Bt:
            ov = ta.overlap(tb)
            every.append({"a": a.name, "b": bn, "tri_pairs": len(ov)})
            if ov:
                tot += len(ov)
                pairs.append({"a": a.name, "b": bn, "tri_pairs": len(ov)})
    res[label] = {"objects_a": len([a for a in A if a]), "objects_b": len(Bt),
                  "objects_a_names": sorted(a.name for a in A if a),
                  "objects_b_names": sorted(bn for bn, _t, _n in Bt),
                  "intersecting_object_pairs": len(pairs),
                  "triangle_pairs": tot,
                  "pairs": sorted(pairs, key=lambda p: -p["tri_pairs"])[:15],
                  # EVERY constituent pair, including the zeros, when the row is
                  # small enough for that to be readable. 101 barriers x 35 kerbs
                  # is 3,535 rows of noise; 1 x 1 is the answer.
                  "all_object_pairs": (sorted(every, key=lambda p: -p["tri_pairs"])
                                       if len(every) <= 40 else None),
                  "note": note, "secs": round(time.time() - t, 1)}
    print("[D] %-42s %6d tri-pairs over %d object pairs (%.1fs)"
          % (label, tot, len(pairs), time.time() - t))
    for p in sorted(every, key=lambda p: -p["tri_pairs"])[:4]:
        if len(every) <= 40:
            print("        %-30s x %-26s %8d" % (p["a"], p["b"], p["tri_pairs"]))
    sys.stdout.flush()


test("barrier_struct x SURF_Track", struct, [track],
     "a barrier passing through the racing surface")
test("barrier_struct x SURF_Kerb", struct, kerbs,
     "a barrier passing through a kerb")
test("BR_Verge x SURF_AccessRoad", verge, [access],
     "barriers' platform vs the Beat-4 ribbon (was 282.4 m2 coplanar)")
test("ARCH_Paving_ApronPlatform x SURF_Track", [apron], [track],
     "the apron platform against the racing surface itself")
test("ARCH_Paving_ApronPlatform x SURF_ApronJoint", [apron], [joint],
     "the pit-exit apron edge joint. SURF_ApronJoint is the DELIBERATE 50 mm "
     "lap joint introduced at contract 1.1.1; it did not exist at 1.0.1, so a "
     "0 -> N step here is the object appearing, not a regression.")
test("TER_Ground x SURF_Track", [ter], [track],
     "terrain through the racing surface")
test("TER_Ground x ARCH_Paving_ApronPlatform", [ter], [apron],
     "terrain through the apron")

R["bvh"] = res

# ---------------------------------------------------------------- CONTROLS --
# Every zero above is only worth what the check's ability to produce a non-zero
# is worth. Two cubes 12 km from anything: one pair interpenetrating, one pair
# 5 m apart. Same `bvh()`, same `BVHTree.overlap`, same code path as the rows.
CTL = {}
_c = []
for _n, _loc in (("SURF_BvhControlA", (12000.0, 12000.0, 50.0)),
                 ("BR_BvhControlB", (12000.0, 12000.0, 50.0))):
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=_loc)
    _o = bpy.context.object
    _o.name = _n
    _c.append(_o)
for _tag, _dx, _want in (("positive_interpenetrating", 0.5, True),
                         ("negative_separated", 5.0, False)):
    _c[1].location = (12000.0 + _dx, 12000.0, 50.0)
    bpy.context.view_layer.update()
    D = dg()
    _ta, _ = bvh(_c[0])
    _tb, _ = bvh(_c[1])
    _n_ov = len(_ta.overlap(_tb)) if (_ta and _tb) else 0
    _ok = (_n_ov > 0) == _want
    CTL[_tag] = {"separation_m": _dx, "must_overlap": _want,
                 "triangle_pairs": _n_ov, "ok": _ok}
    print("[D] CONTROL %-26s dx %.1f m -> %d tri-pairs   %s"
          % (_tag, _dx, _n_ov, "PASS" if _ok else "FAIL"))
for _o in _c:
    bpy.data.objects.remove(_o, do_unlink=True)
CTL["all_ok"] = all(CTL[k]["ok"] for k in
                    ("positive_interpenetrating", "negative_separated"))
if not CTL["all_ok"]:
    print("[D] !! THE BVH CHECK'S OWN CONTROLS MISBEHAVED -- every zero above "
          "is unsupported")
R["controls"] = CTL

R["total_secs"] = round(time.time() - T0, 1)
write_out(OUT, R)
print("[D] DONE %.1fs" % R["total_secs"])
gate_exit.done()
