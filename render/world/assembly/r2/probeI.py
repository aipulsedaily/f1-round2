"""PROBE I — are terrain's library source objects parked at the world origin,
which is INSIDE the round-1 showroom, and are they rendered?

Probe F found 35 vegetation instances inside the round-1 `Floor` footprint
(x -15..15, y -11..11) and most of the examples were at exactly (0.00, 0.00) —
the signature of a source/library object rather than a scattered instance.  The
world origin is the showroom floor, and Beats 1-3 are shot inside it.
"""
import os
exec(open(os.path.expanduser("~/f1-round2/render/world/assembly/r2/lib_probe.py")).read())

# ------------------------------------------------- WHERE THIS PROBE WRITES --
# Was `save("probeI.json", ...)`. `save()` joins its argument onto
# lib_probe's hardcoded OUT_DIR, so this probe could only ever write to
# probeI.json in the assembly root, whatever it was asked for.
# Every run of it, against any assembly and from any directory,
# landed on that one path -- so a re-run silently destroyed the
# previous run's evidence and no output said which blend it read.
#
# It now takes `--out PATH` (a bare positional *.json still works for the
# older chain scripts) and REFUSES to run without one. resolve_out() never
# invents a destination and never strips the directory off the one it was
# given -- the three faults probe_pitexit.py had at once.
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="probeI")
print("[I] output ->", OUT)

# Blender 5.2 returns 0 for a script that raised, so a probe that died halfway
# was indistinguishable from one that finished.  install() arms sys.excepthook
# and an atexit sentinel; done() on the last line disarms it.
sys.path.insert(0, os.path.expanduser("~/f1-round2/tools"))
import gate_exit                                                 # noqa: E402
gate_exit.install(tool="probeI")


R = {}
T0 = time.time()

near = []
for ob in bpy.data.objects:
    if ob.type != "MESH":
        continue
    t = ob.matrix_world.translation
    if abs(t.x) <= 15.0 and abs(t.y) <= 11.0:
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        near.append({
            "name": ob.name, "owner": owner(ob.name), "role": role(ob.name),
            "loc": [round(t.x, 3), round(t.y, 3), round(t.z, 3)],
            "bb_z": [round(min(p.z for p in bb), 3), round(max(p.z for p in bb), 3)],
            "bb_xy": [round(min(p.x for p in bb), 2), round(max(p.x for p in bb), 2),
                      round(min(p.y for p in bb), 2), round(max(p.y for p in bb), 2)],
            "hide_render": bool(ob.hide_render),
            "hide_viewport": bool(ob.hide_viewport),
            "visible_camera": bool(getattr(ob, "visible_camera", True)),
            "in_collections": [c.name for c in ob.users_collection],
            "instancing": ob.instance_type,
            "verts": len(ob.data.vertices) if ob.data else 0})

vis = [n for n in near if not n["hide_render"] and n["visible_camera"]]
veg = [n for n in vis if n["role"] == "vegetation"]
R["objects_inside_showroom_footprint"] = {
    "box": "x -15..15, y -11..11 (round-1 `Floor`)",
    "objects": len(near),
    "render_visible": len(vis),
    "render_visible_vegetation": len(veg),
    "vegetation": veg[:40],
    "by_owner": {},
    "non_vegetation_visible": [n for n in vis if n["role"] != "vegetation"][:30]}
h = {}
for n in vis:
    h[n["owner"]] = h.get(n["owner"], 0) + 1
R["objects_inside_showroom_footprint"]["by_owner"] = h
print("[I] inside the showroom footprint: %d objects, %d render-visible, "
      "%d of them vegetation" % (len(near), len(vis), len(veg)))
print("    by owner:", json.dumps(h))
for n in veg[:12]:
    print("    VEG %-34s loc %s  bb_z %s  hide_render %s  coll %s"
          % (n["name"], n["loc"], n["bb_z"], n["hide_render"], n["in_collections"]))
sys.stdout.flush()

# collection-level exclusion: a source collection can be hidden as a whole
colls = {}
for c in bpy.data.collections:
    colls[c.name] = {"objects": len(c.objects),
                     "hide_render": bool(c.hide_render),
                     "hide_viewport": bool(c.hide_viewport)}
R["collections"] = {k: v for k, v in colls.items()
                    if v["hide_render"] or v["hide_viewport"] or "VEG" in k
                    or "LIB" in k.upper() or "SRC" in k.upper()}
print("[I] collections of interest:", json.dumps(R["collections"])[:900])

# view-layer exclusion
vl = bpy.context.view_layer
def walk(lc, out):
    out[lc.name] = {"exclude": bool(lc.exclude), "hide_viewport": bool(lc.hide_viewport)}
    for ch in lc.children:
        walk(ch, out)
lcs = {}
walk(vl.layer_collection, lcs)
R["layer_collections_excluded"] = {k: v for k, v in lcs.items() if v["exclude"]}
print("[I] excluded layer collections:", json.dumps(R["layer_collections_excluded"]))

R["total_secs"] = round(time.time() - T0, 1)
write_out(OUT, R)
print("[I] DONE %.1fs" % R["total_secs"])
gate_exit.done()
