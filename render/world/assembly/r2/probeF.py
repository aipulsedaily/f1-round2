"""PROBE F — the void probe A found at the PIT EXIT, characterised.

Probe A's D4 sweep says the T3 void (s 702-746, the worst of the original 658 m2)
is gone, and that what is left has MOVED: 26 of 26 affected stations are now
s 3436-3512 on side +1 at u 11-13 m, i.e. the strip between the track edge
(verge_edge 10.5) and the pit wall (C.PIT_WALL_Y = +11.5) over the pit exit.
This maps it at 0.5 m x 0.10 m and names what bounds it.
"""
exec(open("/home/zany/f1-round2/render/world/assembly/r2/lib_probe.py").read())

# ------------------------------------------------- WHERE THIS PROBE WRITES --
# Was `save("probeF.json", ...)`. `save()` joins its argument onto
# lib_probe's hardcoded OUT_DIR, so this probe could only ever write to
# probeF.json in the assembly root, whatever it was asked for.
# Every run of it, against any assembly and from any directory,
# landed on that one path -- so a re-run silently destroyed the
# previous run's evidence and no output said which blend it read.
#
# It now takes `--out PATH` (a bare positional *.json still works for the
# older chain scripts) and REFUSES to run without one. resolve_out() never
# invents a destination and never strips the directory off the one it was
# given -- the three faults probe_pitexit.py had at once.
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="probeF")
print("[F] output ->", OUT)

# Blender 5.2 returns 0 for a script that raised, so a probe that died halfway
# was indistinguishable from one that finished.  install() arms sys.excepthook
# and an atexit sentinel; done() on the last line disarms it.
sys.path.insert(0, "/home/zany/f1-round2/tools")
import gate_exit                                                 # noqa: E402
gate_exit.install(tool="probeF")


R = {}
T0 = time.time()
hide(lambda o: o.type == "MESH" and role(o.name) == "vegetation")
D = dg()

hole = []; rows = {}
nsamp = 0
for s0 in np.arange(3400.0, 3560.0 + 1e-9, 0.5):
    row = []
    for uu in np.arange(9.0, 16.0 + 1e-9, 0.10):
        x, y, _z = C.su_to_world(s0, uu)
        z, nm = top_hit(float(x), float(y), D=D)
        nsamp += 1
        row.append((round(float(uu), 2), (round(float(z), 4) if z is not None else None), nm))
        if z is None:
            hole.append({"s": round(float(s0), 1), "u": round(float(uu), 2)})
    rows["s=%.1f" % s0] = row

# widest continuous hole per station
per_s = {}
for h in hole:
    per_s.setdefault(h["s"], []).append(h["u"])
widest = []
for s0, us in per_s.items():
    us = sorted(us)
    a = b = us[0]; w = 0.0; seg = []
    for u in us[1:]:
        if u - b <= 0.1001:
            b = u
        else:
            seg.append((a, b)); a = b = u
    seg.append((a, b))
    ww = max(b - a for a, b in seg) + 0.10
    widest.append({"s": s0, "widest_m": round(ww, 2), "segments": seg})
widest.sort(key=lambda r: -r["widest_m"])

# what bounds it: the objects immediately inboard and outboard
bounds = []
for w in widest[:12]:
    row = rows["s=%.1f" % w["s"]]
    a, b = w["segments"][0]
    ib = ob = None
    for uu, z, nm in row:
        if uu < a and z is not None:
            ib = (uu, round(z, 4), nm)
        if uu > b and z is not None and ob is None:
            ob = (uu, round(z, 4), nm)
    bounds.append({"s": w["s"], "hole_u": [a, b], "widest_m": w["widest_m"],
                   "inboard": ib, "outboard": ob})

R["pit_exit_void"] = {
    "grid": "s 3400-3560 step 0.5 m, u 9.0-16.0 step 0.10 m, side +1",
    "samples": nsamp,
    "hole_samples": len(hole),
    "hole_area_m2": round(len(hole) * 0.5 * 0.10, 2),
    "stations_with_hole": len(per_s),
    "s_range": ([min(per_s), max(per_s)] if per_s else None),
    "u_range": ([min(h["u"] for h in hole), max(h["u"] for h in hole)]
                if hole else None),
    "widest": widest[:20],
    "bounds": bounds,
    "PIT_WALL_Y": C.PIT_WALL_Y,
    "verge_edge_3470": round(float(C.verge_edge(np.array([3470.0]))[0]), 4),
    "platform_edge_3470": round(float(C.platform_edge(np.array([3470.0]), +1)[0]), 4)}
print("[F] pit exit: %d hole samples = %.2f m2 over %d stations, u %s"
      % (len(hole), len(hole) * 0.05, len(per_s), R["pit_exit_void"]["u_range"]))
for b in bounds[:8]:
    print("    s=%.1f hole u %.2f-%.2f (%.2f m)  inboard %s  outboard %s"
          % (b["s"], b["hole_u"][0], b["hole_u"][1], b["widest_m"],
             b["inboard"], b["outboard"]))
sys.stdout.flush()

# the other isolated station probe A found
iso = []
for s0 in np.arange(1250.0, 1275.0 + 1e-9, 0.5):
    for uu in np.arange(35.0, 45.0 + 1e-9, 0.10):
        x, y, _z = C.su_to_world(s0, uu)
        z, nm = top_hit(float(x), float(y), D=D)
        if z is None:
            iso.append([round(float(s0), 1), round(float(uu), 2)])
R["s1262_void"] = {"hole_samples": len(iso),
                   "hole_area_m2": round(len(iso) * 0.05, 3),
                   "examples": iso[:20]}
print("[F] s~1262: %d hole samples = %.2f m2" % (len(iso), len(iso) * 0.05))

# ---- who owns the ground inside the round-1 showroom footprint? ------------
# Probe B found TER_Ground topmost over part of x 9.4-15.0, |y| <= 11, where
# C.world_ground_z names build_architecture:paving the owner.  Round-1's `Floor`
# (top z = 0.000) will cover it, but grass 40-200 mm tall would grow through a
# 10 mm gap, so this asks BOTH questions.
t = time.time()
own = {}; zs = []
for x in np.arange(-15.0, 15.01, 0.5):
    for y in np.arange(-11.0, 11.01, 0.5):
        z, nm = top_hit(float(x), float(y), D=D)
        own[nm] = own.get(nm, 0) + 1
        if z is not None:
            zs.append(float(z))
R["showroom_footprint_ground"] = {
    "box": "x -15..15, y -11..11 (round-1 `Floor` footprint), 0.5 m grid",
    "samples": sum(own.values()),
    "topmost_histogram": dict(sorted(own.items(), key=lambda kv: -kv[1])),
    "z": stats(zs, 4),
    "note": "round-1 `Floor` top is z = 0.000; anything at or above 0 here would "
            "poke through it"}
print("[F] showroom footprint owners:", json.dumps(R["showroom_footprint_ground"]["topmost_histogram"]))

# vegetation instances inside the showroom footprint
show_all()
D3 = dg()
nveg = 0; inside = 0; ex = []
for inst in D3.object_instances:
    ob = inst.object
    if ob is None or not ob.name.startswith("VEG_"):
        continue
    m = inst.matrix_world
    x, y = m[0][3], m[1][3]
    nveg += 1
    if -15.0 <= x <= 15.0 and -11.0 <= y <= 11.0:
        inside += 1
        if len(ex) < 20:
            ex.append([round(float(x), 2), round(float(y), 2), ob.name])
R["vegetation_in_showroom"] = {
    "vegetation_instances_total": nveg,
    "inside_round1_Floor_footprint": inside,
    "examples": ex,
    "secs": round(time.time() - t, 1)}
print("[F] vegetation inside the showroom footprint: %d of %d" % (inside, nveg))

R["total_secs"] = round(time.time() - T0, 1)
write_out(OUT, R)
print("[F] DONE %.1fs" % R["total_secs"])
gate_exit.done()
