exec(open("/home/zany/f1-round2/render/world/assembly/r2/lib_probe.py").read())

# ------------------------------------------------- WHERE THIS PROBE WRITES --
# Was `save("apron_uv_map.json", ...)`. `save()` joins its argument onto
# lib_probe's hardcoded OUT_DIR, so this probe could only ever write to
# apron_uv_map.json in the assembly root, whatever it was asked for.
# Every run of it, against any assembly and from any directory,
# landed on that one path -- so a re-run silently destroyed the
# previous run's evidence and no output said which blend it read.
#
# It now takes `--out PATH` (a bare positional *.json still works for the
# older chain scripts) and REFUSES to run without one. resolve_out() never
# invents a destination and never strips the directory off the one it was
# given -- the three faults probe_pitexit.py had at once.
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="probeK")
print("[K] output ->", OUT)

# Blender 5.2 returns 0 for a script that raised, so a probe that died halfway
# was indistinguishable from one that finished.  install() arms sys.excepthook
# and an atexit sentinel; done() on the last line disarms it.
sys.path.insert(0, "/home/zany/f1-round2/tools")
import gate_exit                                                 # noqa: E402
gate_exit.install(tool="probeK")

hide(lambda o: o.type == "MESH" and role(o.name) == "vegetation")
D = dg()
scn = bpy.context.scene
cam = bpy.data.objects["CAM_APRON_EDGE"]
W, H = 3840, 2160
sw = cam.data.sensor_width; f = cam.data.lens
M = cam.matrix_world; org = M.translation
def shoot(px, py):
    x = (px + 0.5 - W*0.5)/W*sw; y = -(py + 0.5 - H*0.5)/W*sw
    d = (M.to_3x3() @ Vector((x, y, -f))).normalized()
    ok, loc, nrm, i, ob, m = scn.ray_cast(D, org, d, distance=4000.0)
    if not ok: return None
    s, u = C.project(np.array([loc.x]), np.array([loc.y]))
    return [px, py, ob.name, round(float(s[0]), 2), round(float(u[0]), 4),
            round(float(loc.z), 5),
            round((float(C.ground_z(s, u)[0]) - loc.z)*1000, 2)]
rows = []
for py in range(900, 2160, 20):
    for px in range(0, W, 4):
        r = shoot(px, py)
        if r: rows.append(r)
write_out(OUT, {"rows": rows, "cam": [round(v,3) for v in tuple(org)]})
print("[K] mapped %d pixels" % len(rows))
gate_exit.done()
