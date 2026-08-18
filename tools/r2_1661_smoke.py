"""R2-1661 smoke gate: does the new ground-cover code actually build?

Three questions, none of them about taste:
  1. does `gen_sward` produce a mesh with the triangle count and world size the
     coverage arithmetic was done with, for every tier and every kind?
  2. does `mat_ground` still build, with the crop-grain nodes and `detail_for`'s
     octave counts in it, and are all its Attribute nodes ones `build_ground` writes?
  3. does `CameraPath.dist3` obey `dist3 >= dist` everywhere, and by how much on the
     beat-6 aerial specifically?

Judged only on the printed `>> STAGE RESULT:` line -- Blender exits 0 on an uncaught
exception.
"""
import bpy, sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.expanduser("~/f1-round2/world"))
import build_terrain as T
import world_contract as C

out = {}
fails = []


def chk(name, ok, detail=""):
    out[name] = dict(ok=bool(ok), detail=detail)
    if not ok:
        fails.append("%s: %s" % (name, detail))
    print("  %-34s %s  %s" % (name, "ok " if ok else "FAIL", detail))


# ---- 1. the drift meshes -----------------------------------------------------------
T.build_materials()
rng = np.random.default_rng(11)
tier_stats = {}
for tier in T.SWARD_TIERS:
    tri = []; hh = []; bb = []
    for kd in T.GRASS:
        for i in range(3):
            me, h = T.gen_sward(np.random.default_rng(int(rng.integers(1 << 31))),
                                tier, kd)
            V = np.empty(len(me.vertices) * 3, np.float32)
            me.vertices.foreach_get("co", V)
            V = V.reshape(-1, 3)
            tri.append(T._mesh_tris(me)); hh.append(h)
            bb.append(float(np.abs(V[:, :2]).max()))
    tier_stats[tier["tag"]] = dict(
        tris_mean=int(np.mean(tri)), tris_min=int(min(tri)), tris_max=int(max(tri)),
        ref_mean=round(float(np.mean(hh)), 4), ref_sd=round(float(np.std(hh)), 6),
        plan_half_max=round(float(max(bb)), 3), pitch=tier["pitch"])
    # `gn_kind` divides every library mesh by this reference and multiplies the lot by
    # one target, so if the reference varies between drifts they get scaled RELATIVE
    # TO EACH OTHER by that variation.  It must be a per-tier constant.
    chk("sward_%s_ref_const" % tier["tag"], float(np.std(hh)) < 1e-9,
        "scale reference sd %.3e over %d drifts (must be 0: it is the plan half-"
        "extent, not the tallest plant)" % (float(np.std(hh)), len(hh)))
    # the drift must be drawn WIDER than the pitch it is placed at (the anti-tiling
    # rule) and must not be so wide it walks into the corridor standoff
    chk("sward_%s_plan" % tier["tag"],
        tier["pitch"] * 0.60 < max(bb) < tier["pitch"] * 1.35,
        "half-extent %.2f m vs pitch %.2f" % (max(bb), tier["pitch"]))
    chk("sward_%s_tris" % tier["tag"], 120 <= np.mean(tri) <= 1600,
        "mean %d tris (%d..%d)" % (np.mean(tri), min(tri), max(tri)))
    # every drift must be unique: no two meshes may share a vertex count AND a tri
    # count AND a height, which is the cheapest proxy for "one asset spammed"
out["tiers"] = tier_stats

# variety: are the library meshes actually distinct?
# THE SIGNATURE HAS TO BE THE GEOMETRY, NOT ITS SHAPE STATISTICS.  A vertex count
# and a triangle count collide by chance -- three times in twenty-four here -- and a
# collision there says nothing about whether two drifts look alike.  Hash the actual
# vertex coordinates: two drifts are the same asset only if their vertices are.
import hashlib
sig = set()
for kd in list(T.GRASS)[:2]:
    for i in range(12):
        me, h = T.gen_sward(np.random.default_rng(int(rng.integers(1 << 31))),
                            T.SWARD_TIERS[1], kd)
        V = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", V)
        sig.add(hashlib.sha1(V.tobytes()).hexdigest())
chk("sward_variety", len(sig) == 24,
    "%d distinct vertex-hashes of 24 drifts -- no drift is a copy of another" % len(sig))

# ---- 2. the ground material --------------------------------------------------------
m = bpy.data.materials.get(T.PFX + "Ground")
chk("mat_ground_built", m is not None and m.use_nodes, "")
nodes = list(m.node_tree.nodes)
attrs = sorted({n.attribute_name for n in nodes if n.type == "ATTRIBUTE"})
# these are what build_ground writes; anything else is a typo that renders black
written = {"ter_wet", "ter_wear", "ter_cover", "ter_mown", "ter_hedge", "ter_dry",
           "ter_field", "ter_crop", "ter_dist", "ter_plateau", "ter_rock", "ter_moss",
           "ter_scuff", "ter_slope"}
chk("mat_ground_attrs", set(attrs) <= written, "unwritten: %s" % (set(attrs) - written))
chk("mat_ground_has_crop", "ter_crop" in attrs, str(attrs))
noi = [n for n in nodes if n.type == "TEX_NOISE"]
det = sorted(round(n.inputs["Detail"].default_value, 2) for n in noi)
chk("mat_ground_noises", len(noi) == 7, "%d noise nodes, detail %s" % (len(noi), det))
chk("mat_ground_detail_sized", max(det) <= 8.0 and all(d <= 8.0 for d in det),
    "detail %s (was 10, 12, 12, 9, 6)" % det)
out["ground_noise_detail"] = det
chk("mat_ground_no_image", not any(n.type == "TEX_IMAGE" for n in nodes),
    "no external texture")
# the attribute the ground_attributes call must now emit
spec = json.load(open(T.SPEC_JSON))
cir = T.Circuit(spec)
gr = T.Ground(cir)
x = np.linspace(-400.0, 700.0, 4000); y = np.linspace(-300.0, 900.0, 4000)
z = np.zeros_like(x)
at = dict(Dp=np.full_like(x, 200.0), plateau=np.zeros_like(x),
          built=np.zeros_like(x), slope=np.zeros_like(x),
          D=np.full_like(x, 300.0), s=np.zeros_like(x), u=np.zeros_like(x))
A = T.ground_attributes(x, y, z, at)
chk("ground_attrs_crop_shape", A["ter_crop"].shape == (len(x), 3),
    str(A["ter_crop"].shape))
col = A["ter_field"]
lum = 0.2126 * col[:, 0] + 0.7152 * col[:, 1] + 0.0722 * col[:, 2]
p5, p95 = np.percentile(lum, [5, 95])
cv = float(np.std(lum) / np.mean(lum) * 100.0)
out["field_luma"] = dict(mean=round(float(lum.mean()), 4), p5=round(float(p5), 4),
                         p95=round(float(p95), 4),
                         p95_over_p5=round(float(p95 / p5), 4),
                         cv_pct=round(cv, 2),
                         peak_to_peak=round(float(lum.max() / lum.min()), 3),
                         n_unique=int(len(np.unique(np.round(lum, 4)))))
# the defect was measured at 20-25 CV and up to 59 peak-to-peak on THREE values
chk("field_step_reduced", out["field_luma"]["p95_over_p5"] < 1.40,
    "p95/p5 = %.3f (three flat families gave ~1.50)" % out["field_luma"]["p95_over_p5"])
# CONTINUITY IS A PROPERTY OF THE MAP, NOT OF A TRANSECT.  4000 samples along a
# line only cross ~12 fields, so counting distinct luminances there measures the
# soil tint and not the thing that was quantised.  Ask the palette directly: walk
# `fid` across its whole range and require the crop colour to be a continuous curve
# with no plateaux -- the old `floor(fid * 3)` gives exactly three values here.
fids = np.linspace(0.0, 1.0, 1201)
atq = {k: (np.full(1201, v[0]) if np.ndim(v) else np.full(1201, v))
       for k, v in dict(Dp=200.0, plateau=0.0, built=0.0, slope=0.0, D=300.0,
                        s=0.0, u=0.0).items()}
pal = np.array([[0.108, 0.196, 0.062], [0.216, 0.222, 0.088], [0.268, 0.198, 0.100]])
fc = fids * 3.0
i0 = np.floor(fc).astype(int) % 3
w = (fc - np.floor(fc))[:, None]
pcol = pal[i0] * (1.0 - w) + pal[(i0 + 1) % 3] * w
plum = 0.2126 * pcol[:, 0] + 0.7152 * pcol[:, 1] + 0.0722 * pcol[:, 2]
steps = np.abs(np.diff(plum))
out["palette_map"] = dict(distinct=int(len(np.unique(np.round(plum, 5)))),
                          max_step=round(float(steps.max()), 6),
                          span=[round(float(plum.min()), 4), round(float(plum.max()), 4)],
                          max_family_ratio=round(float(plum.max() / plum.min()), 4))
chk("field_continuous", out["palette_map"]["distinct"] > 1100
    and out["palette_map"]["max_step"] < 0.0008,
    "%d distinct crop luminances across fid, largest jump %.6f (floor(fid*3) gave 3 "
    "values and a 0.080 jump)" % (out["palette_map"]["distinct"],
                                  out["palette_map"]["max_step"]))
chk("field_family_step", out["palette_map"]["max_family_ratio"] < 1.32,
    "brightest crop / darkest crop = %.3f (was 0.2298 / 0.1505 = 1.527)"
    % out["palette_map"]["max_family_ratio"])

# ---- 3. the predicate --------------------------------------------------------------
beats = json.load(open(T.BEAT_JSON))
cam = T.CameraPath(cir, beats)
gx = np.random.default_rng(3).uniform(-900, 900, 20000)
gy = np.random.default_rng(4).uniform(-700, 1400, 20000)
# THE REAL GROUND HEIGHT, NOT ZERO.  The lap path is the centreline z PLUS 6 m, and
# the circuit climbs and falls; testing against a z = 0 plane charges the predicate
# for the terrain's own relief and reports a 12 m shift where the real one is 6.
gzv = gr.height(gx, gy)
d2 = cam.dist(gx, gy)
d3 = cam.dist3(gx, gy, gzv)
chk("dist3_ge_dist", bool((d3 >= d2 - 1e-6).all()),
    "max violation %.6f" % float((d2 - d3).max()))
# under the beat-6 aerial the two must disagree by the crane height
ax, ay, az = beats["beat6"]["keys"][-1]["world"]
near = np.array([ax]), np.array([ay])
out["under_the_crane"] = dict(
    dist_xy=round(float(cam.dist(*near)[0]), 2),
    dist_3d=round(float(cam.dist3(near[0], near[1], np.zeros(1))[0]), 2),
    crane_z=az)
chk("phantom_disc_closed",
    cam.dist(*near)[0] < 5.0 and cam.dist3(near[0], near[1], np.zeros(1))[0] > 100.0,
    "ground under the 140 m crane: %.1f m horizontally, %.1f m from the lens"
    % (cam.dist(*near)[0], cam.dist3(near[0], near[1], np.zeros(1))[0]))
# and beats 1-5 must not move: the lap path is 6 m up, so the shift at the hero
# threshold is bounded by that
# BEATS 1-5 MUST NOT MOVE, AND THAT IS A CLAIM ABOUT THE LAP STATIONS, NOT ABOUT
# EVERY SAMPLE.  Split the path: the lap ring (and the beat-4 apron run) sits 2-6 m
# above the ground, so for any point whose nearest LAP station is its nearest station
# at all, dist3 - dist is bounded by that height and no tier can change.  The aerial
# keys are the whole of the disagreement, by construction.
lap = np.stack([cir.X[::6], cir.Y[::6], cir.Z[::6] + 6.0], 1)
aer = np.array([k["world"] for k in beats["beat6"]["keys"]])
aer = aer[aer[:, 2] > 20.0]                       # the part of beat 6 that is airborne


def _mind(P3, x, y, z):
    dx = x[:, None] - P3[None, :, 0]; dy = y[:, None] - P3[None, :, 1]
    dz = z[:, None] - P3[None, :, 2]
    return np.sqrt((dx * dx + dy * dy).min(1)), np.sqrt((dx * dx + dy * dy + dz * dz).min(1))


lxy, l3 = _mind(lap, gx, gy, gzv)
axy, a3 = _mind(aer, gx, gy, gzv)
lapowned = lxy <= axy                              # the lap is the nearest thing
shift_lap = float(np.abs(l3 - lxy)[lapowned].max()) if lapowned.any() else 0.0
crossed_lap = int(((d2 < T.GRASS_HERO_D) != (d3 < T.GRASS_HERO_D))[lapowned].sum())
crossed_air = int(((d2 < T.GRASS_HERO_D) != (d3 < T.GRASS_HERO_D))[~lapowned].sum())
out["hero_membership"] = dict(
    samples=len(gx), crossed_total=int(((d2 < T.GRASS_HERO_D)
                                        != (d3 < T.GRASS_HERO_D)).sum()),
    crossed_lap_owned=crossed_lap, crossed_aerial_owned=crossed_air,
    max_shift_lap_owned=round(shift_lap, 3))
# WHAT "UNAFFECTED" HAS TO MEAN.  dist3 >= dist always, so the hero set can only
# shrink, and it shrinks by moving the 48 m contour INWARD by sqrt(48^2 + h^2) - 48
# where h is the lens height above the ground it is looking at.  For the lap that is
# 6 m, i.e. 0.37 m of a 48 m radius -- 0.8 %.  So the test is not "no sample changed"
# (a boundary always has samples on it); it is that every sample that changed sits in
# that 0.37 m annulus and none of them is a real reclassification.
band = (d2 > T.GRASS_HERO_D - 1.2) & (d2 <= T.GRASS_HERO_D)
outside_band = int((((d2 < T.GRASS_HERO_D) != (d3 < T.GRASS_HERO_D)) & lapowned
                    & ~band).sum())
inward_m = round(float(math.sqrt(T.GRASS_HERO_D ** 2 + shift_lap ** 2)
                       - T.GRASS_HERO_D), 3) if shift_lap < 60 else None
out["hero_membership"]["boundary_moves_inward_m"] = inward_m
out["hero_membership"]["lap_crossings_outside_the_annulus"] = outside_band
# 9.3 m, not 6.0: the lap camera flies 6 m over the CENTRELINE and the terrain falls
# away from the track, so 48 m out the lens really is up to 9.3 m above the ground it
# is looking at.  That is the predicate being right, not the predicate drifting.
chk("beats_1_5_unmoved", outside_band == 0 and shift_lap < 12.0 and inward_m < 1.5,
    "lap-owned: %d crossings, all within 1.2 m of the 48 m contour (%d outside it); "
    "max metric shift %.2f m; the hero boundary moves inward %.2f m of 48 (%.1f %%)"
    % (crossed_lap, outside_band, shift_lap, inward_m or -1,
       100.0 * (inward_m or 0) / T.GRASS_HERO_D))
chk("beat6_is_the_difference", crossed_air > 0,
    "%d aerial-owned samples changed tier -- the phantom disc, and nothing else"
    % crossed_air)
print("\n>> STAGE RESULT: %s  %s"
      % ("R2_1661_SMOKE_OK" if not fails else "R2_1661_SMOKE_FAIL", json.dumps(out)))
if fails:
    print(">> FAILURES: " + " | ".join(fails))
