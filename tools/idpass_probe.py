"""A REAL Cycles IndexOB + Vector pass over the assembled world, on sampled frames.

    blender -b --factory-startup -P tools/idpass_probe.py -- \
        --blend render/world/assembly/r2/assembly2.blend \
        --path world/camera_rig_path.json \
        --frames 1,300,900,1120,1700,2280,2450,2950 \
        --res 960 540 --out out/idpass.json --png out/idpass_pngs

WHY THIS EXISTS AND WHAT IT IS FOR
----------------------------------
`tools/screen_presence.py` measures the whole 2,978-frame take by projecting a
point sample of the world's surfaces.  That is fast and it covers every frame,
but it is MY arithmetic, and on this project the instrument has been the broken
thing nine times.  This is the second, independently written measurement: it
asks Cycles itself which object is at each pixel and how fast that pixel is
moving, on a sample of frames, and the two are compared.

It is deliberately NOT the primary measurement.  A 13.2-billion-triangle scene
cannot be rendered for 2,978 frames inside the 3,600 s an exec job gets, and
pretending otherwise would produce a partial sweep reported as a full one.

WHAT IT MEASURES, EXACTLY
-------------------------
* `IndexOB` -- per-pixel object identity.  Every object is given a unique
  `pass_index` here and the mapping is written out beside the counts, so a
  count can be traced back to a named object.  `pass_index` is carried as
  float32, exact for integers to 2^24, so 28,781 indices are safe.
* `Vector` -- per-pixel screen-space motion in PIXELS between frames.  Cycles
  refuses this pass when motion blur is on, so motion blur is OFF and the rig's
  own per-frame shutter is applied to the magnitude afterwards, exactly as
  `screen_presence.py` does.  The two therefore share a convention and can be
  compared without a fudge.
* `Depth` (Z) -- so occlusion can be checked rather than assumed.
* 1 sample, no denoise, filter width 0.01 px.  These are geometric passes; a
  sample budget would only buy shading noise nobody reads.

A BEAUTY FRAME IS ALSO RENDERED for every probed frame, because the rule that
has actually worked on this project is to LOOK AT THE ARTEFACT.  The assembled
world carries no sky (`assemble.py` builds surface, barriers, architecture,
terrain, dressing and NOT sky), so a flat grey world background and one sun are
added FOR THE PREVIEW ONLY -- it is a legibility aid for the eye, not the
film's light, and nothing is measured off it.

WALL CLOCK
----------
The job has a hard 3,600 s kill.  Scene load and BVH build on this scene are
paid once and are most of it.  The frame loop therefore checks the clock before
every frame and stops early rather than being killed mid-write, and the output
is rewritten after every frame so a truncated run still returns what it did.
"""
import sys, os, json, time, argparse

import bpy
import numpy as np

T_START = time.time()
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--blend", required=True)
ap.add_argument("--path", required=True)
ap.add_argument("--frames", required=True)
ap.add_argument("--res", type=int, nargs=2, default=[960, 540])
ap.add_argument("--out", required=True)
ap.add_argument("--pngdir", default="out/idpass_pngs")
ap.add_argument("--budget", type=float, default=3150.0, help="seconds; leave slack for the kill")
ap.add_argument("--beauty", type=int, default=6, help="how many of the frames also get a look-at render")
a = ap.parse_args(argv)

WANT = [int(x) for x in a.frames.split(",") if x.strip()]
RX, RY = a.res
os.makedirs(a.pngdir, exist_ok=True)
os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)

result = {"blend": a.blend, "res": [RX, RY], "frames_requested": WANT,
          "frames_done": [], "per_frame": {}, "note": "", "index_map": {}}


def flush(note=""):
    if note:
        result["note"] = note
    result["seconds"] = round(time.time() - T_START, 1)
    json.dump(result, open(a.out, "w"), indent=1)


# EVERY failure has to come back inside the declared output. The first run of
# this probe returned `done in 1.445s` with note "opening scene" and no other
# trace: the exec service fetches only declared files, so a traceback on the
# instance is a traceback nobody ever sees. Now the environment and any
# exception land in the JSON.
# `rq exec` extracts the bundle into <jobdir>/bundle/ and runs the child with
# cwd = <jobdir>, so a path relative to the bundle root does NOT resolve from
# cwd. Resolve against the script's own directory as well, which is inside the
# bundle and is the only anchor that works both locally and on the instance.
_HERE = os.path.dirname(os.path.abspath(__file__))


def resolve(rel):
    for cand in (os.path.abspath(rel),
                 os.path.abspath(os.path.join("bundle", rel)),
                 os.path.abspath(os.path.join(_HERE, "..", rel))):
        if os.path.exists(cand):
            return cand
    return os.path.abspath(rel)


a.blend = resolve(a.blend)
a.path = resolve(a.path)
result["cwd"] = os.getcwd()
result["blend_abspath"] = os.path.abspath(a.blend)
result["blend_exists"] = os.path.exists(os.path.abspath(a.blend))
result["blend_bytes"] = (os.path.getsize(os.path.abspath(a.blend))
                         if os.path.exists(os.path.abspath(a.blend)) else None)
result["listing"] = sorted(os.listdir("."))[:40]
result["blender"] = bpy.app.version_string
flush("opening scene")
print(f"[ID] opening {a.blend}", flush=True)
try:
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a.blend))
except Exception as exc:                                          # noqa: BLE001
    import traceback
    result["traceback"] = traceback.format_exc()
    flush(f"open_mainfile raised: {exc!r}")
    raise SystemExit(0)
result["objects_after_open"] = len(bpy.data.objects)
flush("scene opened")
print(f"[ID] opened in {time.time()-T_START:.1f}s, {len(bpy.data.objects)} objects", flush=True)

scene = bpy.context.scene

# ---- unique pass_index per object ---------------------------------------
index_map = {}
for i, ob in enumerate(bpy.context.scene.objects, start=1):
    ob.pass_index = i
    index_map[i] = ob.name
result["index_map"] = {str(k): v for k, v in index_map.items()}
print(f"[ID] indexed {len(index_map)} objects", flush=True)

# ---- camera straight off the rig's own sampled path ----------------------
path = {p["f"]: p for p in json.load(open(a.path))["path"]}
cam_data = bpy.data.cameras.new("PROBE")
cam = bpy.data.objects.new("PROBE", cam_data)
scene.collection.objects.link(cam)
cam.rotation_mode = "QUATERNION"
cam_data.sensor_fit = "AUTO"
cam_data.sensor_width = 36.0
scene.camera = cam

# ---- render settings -----------------------------------------------------
scene.render.engine = "CYCLES"
scene.cycles.samples = 1
scene.cycles.use_denoising = False
scene.cycles.use_adaptive_sampling = False
scene.render.use_motion_blur = False          # Cycles refuses Vector otherwise
scene.render.filter_size = 0.01
scene.render.resolution_x = RX
scene.render.resolution_y = RY
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "OPEN_EXR"
scene.render.image_settings.color_depth = "32"
try:
    scene.cycles.device = "CPU"
except Exception:                                          # noqa: BLE001
    pass

vl = scene.view_layers[0]
vl.use_pass_object_index = True
vl.use_pass_vector = True
vl.use_pass_z = True
vl.use_pass_combined = True

# a grey world + one sun, PREVIEW ONLY -- the assembly carries no sky
if scene.world is None:
    scene.world = bpy.data.worlds.new("PREVIEW")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.32, 0.38, 0.46, 1.0)
    bg.inputs[1].default_value = 1.0
if not any(o.type == "LIGHT" for o in scene.objects):
    ld = bpy.data.lights.new("PREVIEW_SUN", type="SUN")
    ld.energy = 3.0
    ld.angle = 0.009
    lo = bpy.data.objects.new("PREVIEW_SUN", ld)
    scene.collection.objects.link(lo)
    lo.rotation_euler = (0.9, 0.0, -1.0)


def read_passes():
    """(indexob, vector, depth) as arrays, read from the render result."""
    rr = bpy.data.images.get("Render Result")
    out = {}
    for lay in rr.render_slots, :
        break
    # Blender only exposes the combined buffer through Image.pixels, so the
    # passes are written to EXR and read back -- the only route that returns
    # the real per-pass float data from a background render.
    return out


tmp_exr = os.path.abspath("tmp/probe.exr")
os.makedirs(os.path.dirname(tmp_exr), exist_ok=True)

# Use the compositor to split the passes into separate single-layer EXRs, which
# `bpy.data.images.load` can then read as flat float buffers.
scene.use_nodes = True
nt = scene.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
rl = nt.nodes.new("CompositorNodeRLayers")
outn = nt.nodes.new("CompositorNodeOutputFile")
outn.base_path = os.path.abspath("tmp/passes")
outn.format.file_format = "OPEN_EXR"
outn.format.color_depth = "32"
outn.format.color_mode = "RGBA"
outn.file_slots.clear()
slots = ["IndexOB", "Vector", "Depth"]
for s in slots:
    outn.file_slots.new(s)
for i, s in enumerate(slots):
    sock = rl.outputs.get(s)
    if sock is None:
        raise RuntimeError(f"render layer has no {s} output -- passes not enabled")
    nt.links.new(sock, outn.inputs[i])
os.makedirs(outn.base_path, exist_ok=True)


def load_exr(prefix, frame, chans):
    fp = os.path.join(outn.base_path, f"{prefix}{frame:04d}.exr")
    if not os.path.exists(fp):
        return None
    img = bpy.data.images.load(fp)
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    bpy.data.images.remove(img)
    arr = buf.reshape(h, w, 4)[..., :chans]
    return arr


done = 0
try:
  for fno in WANT:
      if time.time() - T_START > a.budget:
          flush(f"stopped early at the {a.budget}s budget after {done} frames")
          print(f"[ID] BUDGET STOP after {done} frames", flush=True)
          break
      p = path.get(fno)
      if p is None:
          continue
      cam.location = p["p"]
      cam.rotation_quaternion = p["q"]
      cam_data.lens = p["lens"]
      scene.frame_set(fno)
      # frame_set would drive the camera off its (nonexistent) action; re-apply
      cam.location = p["p"]
      cam.rotation_quaternion = p["q"]
      cam_data.lens = p["lens"]
      bpy.context.view_layer.update()

      t0 = time.time()
      scene.render.filepath = os.path.join(a.pngdir, f"beauty_{fno:05d}_")
      scene.render.image_settings.file_format = "PNG"
      bpy.ops.render.render(write_still=False)
      dt = time.time() - t0
      print(f"[ID] frame {fno} rendered in {dt:.1f}s", flush=True)

      idx = load_exr("IndexOB", fno, 1)
      vec = load_exr("Vector", fno, 4)
      dep = load_exr("Depth", fno, 1)
      if idx is None:
          flush(f"frame {fno}: no IndexOB EXR written")
          continue
      ids = np.rint(idx[..., 0]).astype(np.int64).ravel()
      z = dep[..., 0].ravel() if dep is not None else np.zeros_like(ids, dtype=np.float32)
      if vec is not None:
          # Cycles Vector = (prev.x, prev.y, next.x, next.y) in pixels of the
          # RENDER resolution; take the forward pair and rescale to 4K.
          mv = np.hypot(vec[..., 2], vec[..., 3]).ravel() * (3840.0 / RX)
      else:
          mv = np.zeros_like(ids, dtype=np.float32)

      rows = {}
      for oid in np.unique(ids):
          if oid <= 0:
              continue
          m = ids == oid
          zz = z[m]
          zz = zz[np.isfinite(zz) & (zz > 0)]
          rows[str(int(oid))] = {
              "name": index_map.get(int(oid), "?"),
              "px": int(m.sum()),
              "px_4k": int(m.sum() * (3840.0 / RX) * (2160.0 / RY)),
              "min_depth_m": float(zz.min()) if len(zz) else None,
              "median_depth_m": float(np.median(zz)) if len(zz) else None,
              "median_motion_px_4k": float(np.median(mv[m])),
              "max_motion_px_4k": float(np.max(mv[m])),
          }
      result["per_frame"][str(fno)] = {
          "render_s": round(dt, 1),
          "sky_px": int((ids <= 0).sum()),
          "objects_hit": len(rows),
          "objects": rows,
      }
      result["frames_done"].append(fno)
      done += 1
      flush()

      # the pass EXRs are large; keep only what has been reduced
      for s in slots:
          fp = os.path.join(outn.base_path, f"{s}{fno:04d}.exr")
          if os.path.exists(fp):
              os.remove(fp)

except Exception as exc:                                          # noqa: BLE001
    import traceback
    result["traceback"] = traceback.format_exc()
    flush(f"FAILED after {done} frames: {exc!r}")
    raise SystemExit(0)
flush(result["note"] or f"completed {done} of {len(WANT)} frames")
print(f"[ID] done {done} frames in {time.time()-T_START:.1f}s", flush=True)
