import os
exec(open(os.path.expanduser("~/f1-round2/render/world/assembly/r2/lib_probe.py")).read())

# ------------------------------------------------- WHERE THIS PROBE WRITES --
# Was `save("probeJ.json", ...)`. `save()` joins its argument onto
# lib_probe's hardcoded OUT_DIR, so this probe could only ever write to
# probeJ.json in the assembly root, whatever it was asked for.
# Every run of it, against any assembly and from any directory,
# landed on that one path -- so a re-run silently destroyed the
# previous run's evidence and no output said which blend it read.
#
# It now takes `--out PATH` (a bare positional *.json still works for the
# older chain scripts) and REFUSES to run without one. resolve_out() never
# invents a destination and never strips the directory off the one it was
# given -- the three faults probe_pitexit.py had at once.
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="probeJ")
print("[J] output ->", OUT)

# Blender 5.2 returns 0 for a script that raised, so a probe that died halfway
# was indistinguishable from one that finished.  install() arms sys.excepthook
# and an atexit sentinel; done() on the last line disarms it.
sys.path.insert(0, os.path.expanduser("~/f1-round2/tools"))
import gate_exit                                                 # noqa: E402
gate_exit.install(tool="probeJ")

scn = bpy.context.scene
D = dg()
libs = [o for o in bpy.data.objects
        if o.type == "MESH" and o.name.startswith("VEG_")
        and any(c.name.endswith("_lib") for c in o.users_collection)]
print("[J] %d VEG library objects in bpy.data" % len(libs))
in_scene = [o for o in libs if o.name in scn.objects]
print("[J] %d of them are in scene.objects (i.e. in the view layer)" % len(in_scene))
vis = [o for o in in_scene if not o.hide_render and o.visible_camera]
print("[J] %d are render-visible" % len(vis))
# what does a ray find at the world origin with NOTHING hidden?
for (x, y) in ((0.0, 0.0), (0.5, 0.5), (-0.5, 0.3), (2.0, 0.0), (-2.0, 1.0)):
    st = stack(x, y, D=D, maxhits=8)
    print("[J] stack at (%.1f, %.1f): %s" % (x, y, [(round(z, 3), n) for z, n in st]))
# highest VEG library geometry over the showroom
hi = []
for o in vis:
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    if (min(p.x for p in bb) < 15 and max(p.x for p in bb) > -15
            and min(p.y for p in bb) < 11 and max(p.y for p in bb) > -11):
        hi.append((round(max(p.z for p in bb), 3), o.name,
                   [round(min(p.x for p in bb), 2), round(max(p.x for p in bb), 2)]))
hi.sort(reverse=True)
print("[J] %d render-visible library objects whose BOX overlaps the showroom; tallest:" % len(hi))
for h in hi[:15]:
    print("    ", h)
write_out(OUT, {"lib_objects": len(libs), "in_scene": len(in_scene),
                     "render_visible": len(vis), "tallest_over_showroom": hi[:60]})
gate_exit.done()
