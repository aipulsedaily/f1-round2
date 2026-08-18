"""Per-object vertex fingerprint of an item test scene, for the #76 before/after.

    blender -b <scene.blend> --factory-startup -P v120/vertex_fingerprint.py -- OUT.json

#76 claims that repairing the collapsed hash in three modules moved EVERY built
vertex.  That is a claim about geometry, and it is checkable directly rather
than inferred from a variation statistic: dump, per object, the vertex count and
a checksum of the coordinates, then diff two scenes.

The checksum is a float64 sum of the coordinates and their squares plus a
quantised order-independent hash, so it is insensitive to the order Blender
happens to write vertices in but changes if any coordinate moves by more than
0.1 micron.  Object BOUNDS are reported beside it, because a checksum that
differs tells you nothing about how far anything moved.
"""
import sys, os, re, json, hashlib
import bpy
import numpy as np

# WHERE THIS WRITES.  Was the copy-pasted `sys.argv[-1] if ... else
# "vertex_fingerprint.json"` idiom (fixed 2026-08-02): it took the LAST argument
# whatever it was, and given nothing usable it silently invented a relative
# filename resolved against the caller's CWD -- and this script is the one run
# TWICE per item to produce an old/new pair, so a mis-resolved path here means
# comparing a file with itself.  See the note in lib_probe.py.  It execs ONLY
# the marked resolver block: this script must keep running on standalone item
# blends that know nothing about world_contract.
_LIB = os.path.expanduser("~/f1-round2/render/world/assembly/r2/lib_probe.py")
_BLK = re.search(r"^# --- BEGIN resolve_out.*?^# --- END resolve_out.*?$",
                 open(_LIB).read(), re.S | re.M)
if not _BLK:
    raise SystemExit("[VF] no resolve_out block in %s" % _LIB)
exec(compile(_BLK.group(0), _LIB, "exec"))
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="vertex_fingerprint")
print("[VF] output ->", OUT)

rows = {}
tot_v = 0
for ob in bpy.data.objects:
    if ob.type != "MESH" or ob.data is None:
        continue
    me = ob.data
    n = len(me.vertices)
    if n == 0:
        continue
    buf = np.empty(n * 3, dtype=np.float64)
    me.vertices.foreach_get("co", buf)
    v = buf.reshape(n, 3)
    M = np.array(ob.matrix_world, dtype=np.float64)
    w = v @ M[:3, :3].T + M[:3, 3]
    q = np.round(w * 1e7).astype(np.int64)          # 0.1 micron
    h = hashlib.sha1(np.sort(q.sum(axis=1)).tobytes()).hexdigest()[:16]
    rows[ob.name] = {
        "verts": n,
        "sum": [round(float(x), 6) for x in w.sum(axis=0)],
        "sumsq": round(float((w * w).sum()), 6),
        "bbox_min": [round(float(x), 6) for x in w.min(axis=0)],
        "bbox_max": [round(float(x), 6) for x in w.max(axis=0)],
        "hash": h,
    }
    tot_v += n

# WHAT THIS FINGERPRINT IS OF.
# `"scene": <path>` was already here, and a path is not enough: this script is
# run TWICE to make an old/new pair which is then diffed, and two runs against
# the SAME path at different times produce different fingerprints for reasons
# the diff cannot see. The stamp hashes the blend, so "these two fingerprints
# differ" can be told apart from "these two fingerprints are of two different
# builds of the same filename". That distinction is the whole point of a
# before/after -- on 2026-08-02 four before/after pairs on this project turned
# out not to be frames of the same object at all.
sys.path.insert(0, os.path.expanduser("~/f1-round2/tools"))
import provenance as _prov                                       # noqa: E402
R = {_prov.STAMP_KEY: _prov.stamp(
        tool_file=__file__, tool_version="vertex_fingerprint",
        inputs=[("blend", bpy.data.filepath or None)]),
     "scene": bpy.data.filepath, "objects": len(rows), "total_verts": tot_v,
     "rows": rows}
json.dump(R, open(OUT, "w"), indent=0)
print("[VF] %d mesh objects, %d vertices -> %s" % (len(rows), tot_v, OUT))
