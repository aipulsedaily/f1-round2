"""PROBE H — what is the black line in CAM_APRON_EDGE.png?

The rendered apron frame has 3 390 pixels below 0.02 luminance, all of them on
one diagonal line in the near field (image x 244-1189, y 1510-2159).  Every
other joint in the same frame reads as a thin grey line.  This casts the camera
ray through those pixels and reports the object, the joint's width and its depth
so the finding is a measurement and not an impression.
"""
exec(open("/home/zany/f1-round2/render/world/assembly/r2/lib_probe.py").read())

# ------------------------------------------------- WHERE THIS PROBE WRITES --
# Was `save("probeH.json", ...)`. `save()` joins its argument onto
# lib_probe's hardcoded OUT_DIR, so this probe could only ever write to
# probeH.json in the assembly root, whatever it was asked for.
# Every run of it, against any assembly and from any directory,
# landed on that one path -- so a re-run silently destroyed the
# previous run's evidence and no output said which blend it read.
#
# It now takes `--out PATH` (a bare positional *.json still works for the
# older chain scripts) and REFUSES to run without one. resolve_out() never
# invents a destination and never strips the directory off the one it was
# given -- the three faults probe_pitexit.py had at once.
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="probeH")
print("[H] output ->", OUT)

# Blender 5.2 returns 0 for a script that raised, so a probe that died halfway
# was indistinguishable from one that finished.  install() arms sys.excepthook
# and an atexit sentinel; done() on the last line disarms it.
sys.path.insert(0, "/home/zany/f1-round2/tools")
import gate_exit                                                 # noqa: E402
gate_exit.install(tool="probeH")


R = {}
T0 = time.time()
hide(lambda o: o.type == "MESH" and role(o.name) == "vegetation")
D = dg()

scn = bpy.context.scene
cam = bpy.data.objects.get("CAM_APRON_EDGE")
if cam is None:
    print("[H] CAM_APRON_EDGE not in this blend - reconstructing it")
    import numpy as _np
    e_ap = float(C.verge_edge(_np.array([3260.0]))[0])
    x0, y0, z0 = C.su_to_world(3232.0, e_ap + 0.75, +1)
    x1, y1, z1 = C.su_to_world(3350.0, e_ap + 0.10, +1)
    cd = bpy.data.cameras.new("CAM_APRON_EDGE")
    cd.lens = 85.0; cd.sensor_width = 36.0
    cd.clip_start, cd.clip_end = 0.05, 60000.0
    cam = bpy.data.objects.new("CAM_APRON_EDGE", cd)
    scn.collection.objects.link(cam)
    cam.location = Vector((x0, y0, z0 + 0.55))
    d = Vector((x1, y1, z1 + 0.02)) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    D = dg()

W, H = 3840, 2160
sw = cam.data.sensor_width
f = cam.data.lens
M = cam.matrix_world
org = M.translation


def ray_dir(px, py):
    # Blender: sensor fit AUTO, W > H so sensor_width maps to X
    x = (px + 0.5 - W * 0.5) / W * sw
    y = -(py + 0.5 - H * 0.5) / W * sw
    v = Vector((x, y, -f))
    return (M.to_3x3() @ v).normalized()


def shoot(px, py):
    d = ray_dir(px, py)
    ok, loc, nrm, idx, ob, m = scn.ray_cast(D, org, d, distance=4000.0)
    if not ok:
        return None
    s, u = C.project(np.array([loc.x]), np.array([loc.y]))
    return {"px": px, "py": py, "obj": ob.name,
            "world": [round(loc.x, 4), round(loc.y, 4), round(loc.z, 4)],
            "dist_m": round((loc - org).length, 3),
            "s": round(float(s[0]), 2), "u": round(float(u[0]), 3),
            "datum_z": round(float(C.ground_z(s, u)[0]), 4),
            "below_datum_mm": round((float(C.ground_z(s, u)[0]) - loc.z) * 1000, 2)}


# the dark pixels, precomputed from the render (Blender's python has no PIL)
dark = []
try:
    dj = json.load(open("/home/zany/f1-round2/render/world/assembly/r2/darkpx.json"))
    dark = [tuple(p) for p in dj["pts"]]
    print("[H] %d dark pixels total, %d sampled" % (dj["n"], len(dark)))
    R["dark_pixels_below_0.02"] = dj["n"]
except Exception as e:
    print("[H] no dark pixel list:", e)

hits = []
for px, py in dark:
    h = shoot(px, py)
    if h:
        hits.append(h)
R["dark_pixel_rays"] = {"n": len(hits),
                        "objects": sorted({h["obj"] for h in hits}),
                        "dist_m": stats([h["dist_m"] for h in hits], 3),
                        "below_datum_mm": stats([h["below_datum_mm"] for h in hits], 2),
                        "s_range": ([min(h["s"] for h in hits), max(h["s"] for h in hits)]
                                    if hits else None),
                        "u_range": ([min(h["u"] for h in hits), max(h["u"] for h in hits)]
                                    if hits else None),
                        "examples": hits[:20]}
print("[H] dark rays land on:", R["dark_pixel_rays"]["objects"])
print("    dist", R["dark_pixel_rays"]["dist_m"])
print("    below datum mm", R["dark_pixel_rays"]["below_datum_mm"])
print("    s", R["dark_pixel_rays"]["s_range"], "u", R["dark_pixel_rays"]["u_range"])
sys.stdout.flush()

# a horizontal scanline across the black line, at 0.2 px, to get its true width
if hits:
    py = int(np.median([h["py"] for h in hits]))
    row = []
    for px in range(0, W, 2):
        h = shoot(px, py)
        row.append([px, (h["obj"] if h else None),
                    (h["below_datum_mm"] if h else None)])
    lows = [r for r in row if r[2] is not None and r[2] > 5.0]
    R["scanline"] = {"py": py, "samples": len(row),
                     "columns_more_than_5mm_low": len(lows),
                     "deepest_mm": (max(r[2] for r in lows) if lows else 0.0),
                     "examples": lows[:20]}
    print("[H] scanline py=%d: %d of %d columns >5 mm low, deepest %.2f mm"
          % (py, len(lows), len(row), R["scanline"]["deepest_mm"]))

# and a 0.5 mm cross-section of the joint on the ground
if hits:
    s0 = float(np.median([h["s"] for h in hits]))
    u0 = float(np.median([h["u"] for h in hits]))
    prof = []
    for du in np.arange(-0.15, 0.15001, 0.0005):
        x, y, _z = C.su_to_world(s0, u0 + du)
        z, nm = top_hit(float(x), float(y), D=D)
        dat = float(C.ground_z(np.array([s0]), np.array([u0 + du]))[0])
        prof.append([round(float(du), 4), (round(float(z), 5) if z is not None else None),
                     nm, (round((dat - z) * 1000, 2) if z is not None else None)])
    dd = [p[3] for p in prof if p[3] is not None]
    R["joint_cross_section"] = {"s": round(s0, 2), "u": round(u0, 3),
                                "step_mm": 0.5,
                                "deepest_mm": round(max(dd), 2) if dd else None,
                                "width_over_5mm_deep_mm": round(
                                    sum(1 for d in dd if d > 5.0) * 0.5, 2),
                                "width_over_20mm_deep_mm": round(
                                    sum(1 for d in dd if d > 20.0) * 0.5, 2),
                                "profile": prof}
    print("[H] joint at s=%.1f u=%.3f: deepest %.2f mm, %.1f mm wide over 5 mm deep"
          % (s0, u0, R["joint_cross_section"]["deepest_mm"] or 0,
             R["joint_cross_section"]["width_over_5mm_deep_mm"] or 0))

R["total_secs"] = round(time.time() - T0, 1)
write_out(OUT, R)
print("[H] DONE %.1fs" % R["total_secs"])
gate_exit.done()
