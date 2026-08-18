"""GLASS WINDING A/B, take 2 -- ONE VARIANT PER BLEND, ALL AT THE SAME PLACE.

    blender -b --factory-startup -P tools/glass_winding_ab_build.py -- \
        <film.blend> <variant> <out.blend>

WHY TAKE 1 WAS THROWN AWAY.  Take 1 put five copies of the wall in one blend at
world offsets of 2-8 km so the broker would only have to push one scene.  The
east test survived it; the SOUTH test did not, and its POSITIVE CONTROL SAID SO:
turning all fourteen panes inside out moved the picture by 1.583 levels against
a NULL -- two identical, correctly wound copies -- of 1.618.  The instrument's
floor was above its own signal, so the south rows measured nothing.

The cause is the offsets.  The south view is a dim interior lit by 24 practical
lamps through many bounces; at x = 8 km, float32 spacing is ~1 mm, and a
many-bounce path diverges chaotically from the same path at the origin.  Cycles'
per-pixel sampling is deterministic, but only if the geometry it traverses is
bit-identical -- and a translated copy is not.  The east view is direct sun
through glass at two or three bounces and it separated 28x regardless.

So: one variant per blend, every variant at the SAME world coordinates, and the
null becomes a re-render of the control.  Four 0.5 MB pushes instead of one, and
the noise cancels exactly instead of being hoped away.
"""
import json, os, re, sys
import numpy as np
import bpy
from mathutils import Quaternion, Vector

ROOT = os.path.expanduser("~/f1-round2")
sys.path.insert(0, os.path.join(ROOT, "world"))
import film_exposure as FX                                        # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, VARIANT, OUT = argv[0], argv[1], argv[2]
assert VARIANT in ("CTL", "LIVE", "NEG", "GPFLIP", "NOGLASS", "NOGP"), VARIANT
# NOGLASS / NOGP are the SENSITIVITY CONTROLS. "Flipping the panes changed
# nothing" and "this camera cannot see the panes" produce the same number, and
# only deleting the glass tells them apart. Without this the south verdict is
# indistinguishable from a vacuous test.
PATHJSON = os.path.join(ROOT, "render", "film13_path.json")
F_SOUTH, F_EAST = 645, 863
OBJ_RE = re.compile(r"^(GW_Front_|GW_Right_|GP_b\d\d$|Wall_BackX|Wall_SideY|Floor)")

def log(*a): print(*a, flush=True)

with bpy.data.libraries.load(SRC, link=False) as (df, dt):
    allobj = list(df.objects)
    worlds = list(df.worlds)
    want = sorted([o for o in allobj if OBJ_RE.match(o)])
    lamps = sorted([o for o in allobj
                    if re.match(r"^(WallWash_|Spot_\d|Rim$|Kick$|Key$|Fill$|"
                                r"FloorGraze$|Bollard_Lamp_\d|SKY_Sun$)", o)])
    lamps = [o for o in lamps if o not in set(want)]
    dt.objects = want + lamps
    dt.worlds = list(worlds)
    want, lamps = list(want), list(lamps)

sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.name in ("Cube", "Light", "Camera"):
        bpy.data.objects.remove(o, do_unlink=True)
# APPENDING IS NOT LINKING.  `libraries.load(link=False)` creates the
# datablocks and puts them in NO collection; take 1 linked its copies into new
# collections and never noticed.  Without this the scene holds two cameras and
# nothing else: the east camera renders bare sky (which the broker's blank-check
# scores as a valid picture, mean 55.97, 204 levels) and the south camera
# renders black (which it correctly refuses).  A blank guard that passes an
# empty scene from one angle and fails it from another is exactly why the
# EMPTY_SCENE assert below exists.
objs = []
for nm in want + lamps:
    ob = bpy.data.objects.get(nm)
    if ob is None:
        continue
    ob.parent = None
    ob.animation_data_clear()
    ob.hide_render = ob.hide_viewport = False
    sc.collection.objects.link(ob)
    objs.append(ob)
n_mesh = sum(1 for o in objs if o.type == "MESH")
n_lamp = sum(1 for o in objs if o.type == "LIGHT")
log("linked into the scene: %d objects (%d meshes, %d lamps)"
    % (len(objs), n_mesh, n_lamp))
assert n_mesh >= 60 and n_lamp >= 20, (
    "EMPTY SCENE: %d meshes, %d lamps linked. The subject is not in the render."
    % (n_mesh, n_lamp))
for w in bpy.data.worlds:
    if w.use_nodes and any(n.type == "TEX_SKY" for n in w.node_tree.nodes):
        sc.world = w
        break

# the pavilion's interior centroid, from the shell. No pane name in the rule.
shell = [o for o in objs if o.type == "MESH"
         and re.match(r"^(Floor|Wall_BackX|Wall_SideY)", o.name)]
pts = []
for o in shell:
    M = np.array(o.matrix_world)
    pts += [np.array(c) @ M[:3, :3].T + M[:3, 3] for c in o.bound_box]
INTERIOR = np.array(pts).mean(axis=0)


def arrays(me):
    nv, nl, nf = len(me.vertices), len(me.loops), len(me.polygons)
    co = np.empty(nv * 3, np.float32); me.vertices.foreach_get("co", co)
    lv = np.empty(nl, np.int32); me.loops.foreach_get("vertex_index", lv)
    ls = np.empty(nf, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, np.int32); me.polygons.foreach_get("loop_total", lt)
    return co.reshape(-1, 3).astype(np.float64), lv, ls, lt


def wnormal(ob):
    P, lv, ls, lt = arrays(ob.data)
    M = np.array(ob.matrix_world); det = float(np.linalg.det(M[:3, :3]))
    P = P @ M[:3, :3].T + M[:3, 3]
    N = np.zeros(3)
    for f in range(len(lt)):
        s, c = int(ls[f]), int(lt[f]); idx = lv[s:s + c]
        for k in range(1, c - 1):
            n = np.cross(P[idx[k]] - P[idx[0]], P[idx[k + 1]] - P[idx[0]])
            N += -n if det < 0 else n
    return N, P.mean(axis=0)


def svol(ob):
    P, lv, ls, lt = arrays(ob.data)
    v = 0.0
    for f in range(len(lt)):
        s, c = int(ls[f]), int(lt[f]); idx = lv[s:s + c]
        for k in range(1, c - 1):
            v += float(np.dot(P[idx[0]], np.cross(P[idx[k]], P[idx[k + 1]]))) / 6.0
    return v


def flip(ob):
    _, lv, ls, lt = arrays(ob.data)
    out = lv.copy()
    for f in range(len(lt)):
        s, c = int(ls[f]), int(lt[f])
        out[s:s + c] = lv[s:s + c][::-1]
    ob.data.loops.foreach_set("vertex_index", out.astype(np.int32))
    ob.data.update(); ob.data.update_tag()


SOUTH = sorted([o for o in objs if o.name.startswith("GW_Front_Glass")],
               key=lambda o: o.name)
EAST = sorted([o for o in objs if re.match(r"^GP_b\d\d$", o.name)],
              key=lambda o: o.name)
rep = {"variant": VARIANT, "interior_centroid": INTERIOR.tolist(),
       "south": {}, "east": {}, "flipped": []}
for o in SOUTH:
    N, c = wnormal(o)
    u = N / np.linalg.norm(N)
    d = c - INTERIOR; d /= np.linalg.norm(d)
    is_out = bool(np.dot(u, d) > 0)
    rep["south"][o.name] = {"shipped_outward": is_out,
                            "dot": float(np.dot(u, d))}
    if VARIANT in ("LIVE", "NOGP"):
        continue
    want_out = (VARIANT != "NEG")
    if is_out != want_out:
        flip(o); rep["flipped"].append(o.name)
for o in EAST:
    v = svol(o)
    rep["east"][o.name] = {"signed_volume": v, "outward": bool(v > 0)}
    if VARIANT == "GPFLIP":
        flip(o); rep["flipped"].append(o.name)

if VARIANT == "NOGLASS":
    for o in list(SOUTH):
        bpy.data.objects.remove(o, do_unlink=True)
    SOUTH = []
    rep["deleted"] = "all 14 GW_Front_Glass panes"
if VARIANT == "NOGP":
    for o in list(EAST):
        bpy.data.objects.remove(o, do_unlink=True)
    EAST = []
    rep["deleted"] = "all 10 GP_b panes"

# verify AFTER authoring
bad = []
for o in SOUTH:
    N, c = wnormal(o)
    u = N / np.linalg.norm(N)
    d = c - INTERIOR; d /= np.linalg.norm(d)
    got = bool(np.dot(u, d) > 0)
    want = (rep["south"][o.name]["shipped_outward"]
            if VARIANT in ("LIVE", "NOGP") else (VARIANT != "NEG"))
    if got != want:
        bad.append(o.name)
for o in EAST:
    got = svol(o) > 0
    want = (VARIANT != "GPFLIP")
    if got != want:
        bad.append(o.name)
rep["verify_bad"] = bad
log("%s: %d flipped, verify %s" % (VARIANT, len(rep["flipped"]),
                                   "ok" if not bad else "FAILED %s" % bad))

path = {int(k["f"]): k for k in json.load(open(PATHJSON))["path"]}
for tag, fr in (("S", F_SOUTH), ("E", F_EAST)):
    k = path[fr]
    cd = bpy.data.cameras.new("CAM_" + tag)
    cd.lens = float(k["lens"]); cd.sensor_width = 36.0; cd.dof.use_dof = False
    c = bpy.data.objects.new("CAM_" + tag, cd)
    c.location = Vector(tuple(k["p"]))
    c.rotation_mode = "QUATERNION"
    c.rotation_quaternion = Quaternion(k["q"])
    sc.collection.objects.link(c)

sc.render.engine = "CYCLES"
sc.cycles.seed = 0
sc.cycles.use_animated_seed = False
sc.cycles.use_adaptive_sampling = False
sc.cycles.use_denoising = False
sc.cycles.max_bounces = 32
sc.cycles.transmission_bounces = 24
sc.cycles.transparent_max_bounces = 24
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.render.resolution_percentage = 100
sc.render.use_persistent_data = True
sc.frame_start = sc.frame_end = sc.frame_current = 1
FX.apply(sc)
sc.camera = bpy.data.objects["CAM_S"]
json.dump(rep, open(os.path.splitext(OUT)[0] + ".json", "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
log(">> STAGE RESULT: GLASS_AB2_BUILD_%s (%s)"
    % ("OK" if not bad else "FAIL", VARIANT))
