"""A REAL Cycles per-object ID pass, without the compositor.

    blender -b -noaudio -P tools/idpass_emissive.py -- \
        --blend world/verify_surface.blend --path world/camera_rig_path.json \
        --frames 950,1250,... --res 960 540 --out out/idpass.json

WHY EMISSION AND NOT `IndexOB`
------------------------------
The IndexOB pass exists and is the right pass, but getting its float buffer out
of a background render needs the compositor's File Output node, and Blender 5.x
moved the compositor: `Scene.node_tree` no longer exists (it is a node GROUP
now), which is the same 5.x change already logged for this project.  Rather than
fight that, every object is given a unique FLAT EMISSION colour and the scene is
lit by nothing else, so the ordinary combined render IS the ID pass -- written
to a 32-bit EXR, loaded back, and decoded exactly.

This is a real render.  Cycles does the frustum test, the occlusion and the
sub-pixel coverage, which is precisely the part `screen_presence.py` models and
the part that therefore needs an independent witness.

WHAT IT DOES NOT GIVE
---------------------
Motion.  The Vector pass needs the compositor too.  Motion blur is left OFF so
the ID colours stay pure; the smear figures in `screen_presence.py` are not
cross-checked by this and that is stated rather than glossed.

DECODING
--------
Object i gets colour ((i % 64)/64, ((i // 64) % 64)/64, ((i // 4096) % 64)/64)
plus a half-step, exact in float32 and separable to 262,144 objects.  Filter
width 0.01 px makes the film filter effectively nearest-neighbour so edge pixels
are one object's colour rather than a blend of two -- a blend would decode to a
third, nonexistent object, which is the failure mode this encoding has to avoid.
"""
import sys, os, json, time, argparse
import bpy
import numpy as np

T0 = time.time()
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--blend", required=True)
ap.add_argument("--path", required=True)
ap.add_argument("--frames", required=True)
ap.add_argument("--res", type=int, nargs=2, default=[960, 540])
ap.add_argument("--out", required=True)
ap.add_argument("--budget", type=float, default=1200.0)
a = ap.parse_args(argv)

RX, RY = a.res
WANT = [int(x) for x in a.frames.split(",") if x.strip()]
res = {"blend": os.path.abspath(a.blend), "res": [RX, RY], "frames_requested": WANT,
       "frames_done": [], "per_frame": {}, "note": ""}


def flush(note=""):
    if note:
        res["note"] = note
    res["seconds"] = round(time.time() - T0, 1)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)


bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a.blend))
scene = bpy.context.scene
print(f"[IDE] opened {len(bpy.data.objects)} objects in {time.time()-T0:.1f}s", flush=True)


def code(i):
    return ((i % 64) + 0.5) / 64.0, (((i // 64) % 64) + 0.5) / 64.0, \
           (((i // 4096) % 64) + 0.5) / 64.0


names = []
for ob in list(scene.objects):
    if ob.type != "MESH":
        continue
    i = len(names) + 1                      # 0 is reserved for "nothing"
    names.append(ob.name)
    mat = bpy.data.materials.new(f"ID_{i:05d}")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    em = nt.nodes.new("ShaderNodeEmission")
    r, g, b = code(i)
    em.inputs[0].default_value = (r, g, b, 1.0)
    em.inputs[1].default_value = 1.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    ob.data.materials.clear()
    ob.data.materials.append(mat)
res["objects"] = names
print(f"[IDE] encoded {len(names)} objects", flush=True)

# nothing else may emit: no world, no lights
if scene.world:
    scene.world.use_nodes = True
    bgn = scene.world.node_tree.nodes.get("Background")
    if bgn:
        bgn.inputs[0].default_value = (0, 0, 0, 1)
        bgn.inputs[1].default_value = 0.0
for ob in list(scene.objects):
    if ob.type == "LIGHT":
        bpy.data.objects.remove(ob, do_unlink=True)

path = {p["f"]: p for p in json.load(open(os.path.abspath(a.path)))["path"]}
cd = bpy.data.cameras.new("IDCAM")
cam = bpy.data.objects.new("IDCAM", cd)
scene.collection.objects.link(cam)
cam.rotation_mode = "QUATERNION"
cd.sensor_fit, cd.sensor_width = "AUTO", 36.0
cd.dof.use_dof = False
scene.camera = cam

scene.render.engine = "CYCLES"
scene.cycles.samples = 1
scene.cycles.use_denoising = False
scene.cycles.use_adaptive_sampling = False
scene.cycles.max_bounces = 0
scene.render.use_motion_blur = False
scene.render.filter_size = 0.01
scene.render.resolution_x, scene.render.resolution_y = RX, RY
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.view_settings.view_transform = "Standard"      # no tone curve on the codes
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
scene.render.image_settings.color_mode = "RGB"

tmp = os.path.abspath("tmp/idframe.exr")
os.makedirs(os.path.dirname(tmp), exist_ok=True)
flush("set up")

for fno in WANT:
    if time.time() - T0 > a.budget:
        flush(f"budget stop after {len(res['frames_done'])} frames")
        break
    p = path.get(fno)
    if p is None:
        continue
    cam.location = p["p"]
    cam.rotation_quaternion = p["q"]
    cd.lens = p["lens"]
    scene.frame_set(fno)
    cam.location = p["p"]
    cam.rotation_quaternion = p["q"]
    cd.lens = p["lens"]
    bpy.context.view_layer.update()
    scene.render.filepath = tmp[:-4]
    t = time.time()
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(tmp)
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    bpy.data.images.remove(img)
    px = buf.reshape(h * w, 4)[:, :3]
    idx = (np.rint(px * 64.0 - 0.5).astype(np.int64))
    ids = idx[:, 0] + idx[:, 1] * 64 + idx[:, 2] * 4096
    ids[(px.max(axis=1) <= 1e-6)] = 0
    rows = {}
    for oid, cnt in zip(*np.unique(ids, return_counts=True)):
        if oid <= 0 or oid > len(names):
            continue
        rows[names[oid - 1]] = {"px": int(cnt),
                                "frac_of_frame": round(float(cnt) / (w * h), 6),
                                "px_4k_equiv": int(cnt * (3840.0 / RX) * (2160.0 / RY))}
    res["per_frame"][str(fno)] = {"render_s": round(time.time() - t, 1),
                                  "empty_px": int((ids == 0).sum()),
                                  "objects_hit": len(rows), "objects": rows}
    res["frames_done"].append(fno)
    print(f"[IDE] frame {fno}: {len(rows)} objects on screen, "
          f"{100.0*(ids>0).mean():.1f} % of frame covered, {time.time()-t:.1f}s", flush=True)
    flush()

flush(res["note"] or f"completed {len(res['frames_done'])} frames")
print(f"[IDE] wrote {a.out} in {time.time()-T0:.1f}s", flush=True)
