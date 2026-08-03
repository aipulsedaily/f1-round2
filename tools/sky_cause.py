"""WHICH SKY IS `C.SKY_IRRADIANCE` A DESCRIPTION OF?

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/sky_cause.py -- world/sky_cause.json

`world/film_exposure.py --selftest` reads the result and gates on it.

`world/build_sky.calibrate()` bakes SKY_IRRADIANCE from a throwaway `CAL_world`
that holds ONE bare `ShaderNodeTexSky` node.  `build_sky.build_world()` -- the
world the film is actually rendered in -- is that same node with an aerosol
mottle and THREE alpha-composited cloud decks over it.  The exposure calibration
measured the FILM's world and got 11.1818 W/m2 against the constant's 8.4593.

So the hypothesis is: the constant is not wrong about the sky it was baked from,
it is a description of a sky the film does not build.  That is measurable and it
is measured here, on calibrate()'s own rig, with three worlds:

  BARE        a fresh bare Sky Texture at the contract's parameters.
              POSITIVE CONTROL -- it must reproduce the BAKED CONSTANT. If it
              does not, calibrate() is not reproducible and nothing else here
              means anything.
  SHIPPED     build_sky.build_world(), untouched. The film's own world.
  NOCLOUD     build_world() with every deck's composite factor forced to 0.
              If the decks are the whole cause this must land back on BARE.

E = pi * L on an albedo-1.0 lambertian plane, exactly calibrate()'s inversion.
No sun lamp and no atmosphere geometry exist in this scene at all, so "sky
alone" is not a hide_render claim, it is the whole scene.
"""
import json, math, os, sys
import numpy as np
import bmesh, bpy

ROOT = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(ROOT, "world"))
import build_sky as BS                                            # noqa: E402
import world_contract as C                                        # noqa: E402

OUT = (sys.argv[sys.argv.index("--") + 1:] or
       [os.path.join(ROOT, "world/sky_cause.json")])[0]
SAMPLES = int(os.environ.get("SKY_SAMPLES", "3000"))
TMP = os.path.join(ROOT, "work", "_sky_cause_shot.exr")


def log(*a): print(*a, flush=True)


sc = bpy.context.scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_adaptive_sampling = False
sc.cycles.use_denoising = False
sc.cycles.sample_clamp_indirect = 0.0
sc.render.resolution_x = sc.render.resolution_y = 48
sc.render.image_settings.file_format = "OPEN_EXR"
sc.render.image_settings.color_depth = "32"
sc.view_settings.view_transform = "Standard"
sc.view_settings.exposure = 0.0

me = bpy.data.meshes.new("CAL_plane")
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=400.0)
bm.to_mesh(me); bm.free()
po = bpy.data.objects.new("CAL_plane", me)
sc.collection.objects.link(po)
mat = bpy.data.materials.new("CAL_white")
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (1, 1, 1, 1)
b.inputs["Roughness"].default_value = 1.0
b.inputs["Metallic"].default_value = 0.0
if "Specular IOR Level" in b.inputs:
    b.inputs["Specular IOR Level"].default_value = 0.0
me.materials.append(mat)
cd = bpy.data.cameras.new("CAL_cam"); cd.lens = 50.0; cd.clip_end = 1e7
co = bpy.data.objects.new("CAL_cam", cd)
sc.collection.objects.link(co); co.location = (0, 0, 40)
sc.camera = co


def shoot():
    sc.render.filepath = TMP
    bpy.ops.render.render(write_still=True)
    import OpenImageIO as oiio
    i = oiio.ImageInput.open(TMP)
    s = i.spec()
    a = np.array(i.read_image(format="float")).reshape(
        s.height, s.width, s.nchannels)[:, :, :3]
    i.close()
    return a[6:-6, 6:-6].reshape(-1, 3).mean(0)


def bare_world():
    w = bpy.data.worlds.new("W_BARE")
    tree = w.node_tree
    bg = [n for n in tree.nodes if n.type == "BACKGROUND"][0]
    sky = tree.nodes.new("ShaderNodeTexSky")
    tree.links.new(sky.outputs["Color"], bg.inputs[0])
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_size = BS.SUN_ANGULAR_DIAM
    sky.sun_elevation = BS.SUN_ELEV
    sky.sun_rotation = BS.SKY_SUN_ROTATION
    sky.altitude = BS.SKY_ALTITUDE
    sky.air_density = BS.SKY_AIR
    sky.aerosol_density = BS.SKY_AEROSOL
    sky.ozone_density = BS.SKY_OZONE
    sky.sun_disc = False                    # calibrate()'s B shot
    return w


def kill_decks(w):
    """Force every deck's alpha-composite factor to 0. Reports what it hit, so a
    rename that makes this a no-op shows up as `decks_zeroed: 0` and not as a
    silent pass."""
    hit = []
    for n in w.node_tree.nodes:
        lbl = (n.label or "")
        if lbl.startswith("over ") and n.type in ("MIX_RGB", "MIX"):
            s = n.inputs.get("Fac") or n.inputs.get("Factor")
            for lk in list(s.links):
                w.node_tree.links.remove(lk)
            s.default_value = 0.0
            hit.append(lbl)
    return hit


results = {}

# ---- 1. BARE: the positive control ---------------------------------------- #
sc.world = bare_world()
B = shoot(); E = B * math.pi
results["BARE"] = [float(v) for v in E]
log("BARE      E = %s   mean %.4f" % (np.round(E, 4).tolist(), E.mean()))

# ---- 2. SHIPPED: build_world(), untouched --------------------------------- #
w_ship = BS.build_world(camera=co)
if not isinstance(w_ship, bpy.types.World):
    w_ship = sc.world
sc.world = w_ship
log("SHIPPED world: %s  (%d nodes)" % (w_ship.name, len(w_ship.node_tree.nodes)))
B = shoot(); E = B * math.pi
results["SHIPPED"] = [float(v) for v in E]
log("SHIPPED   E = %s   mean %.4f" % (np.round(E, 4).tolist(), E.mean()))

# ---- 3. NOCLOUD ----------------------------------------------------------- #
hit = kill_decks(w_ship)
log("decks zeroed: %s" % hit)
B = shoot(); E = B * math.pi
results["NOCLOUD"] = [float(v) for v in E]
results["decks_zeroed"] = hit
log("NOCLOUD   E = %s   mean %.4f" % (np.round(E, 4).tolist(), E.mean()))

# ---- verdict -------------------------------------------------------------- #
baked = np.array(C.SKY_IRRADIANCE, float)
mb, ms, mn = (np.array(results[k]).mean() for k in ("BARE", "SHIPPED", "NOCLOUD"))
kb = float(np.array(baked).mean())
RES = 0.05
def st(a, b): return math.log2(a / b)
lines = [
    ("baked C.SKY_IRRADIANCE mean", kb, None),
    ("BARE    (positive control)", mb, st(mb, kb)),
    ("SHIPPED (the film's world)", ms, st(ms, kb)),
    ("NOCLOUD (decks off)",        mn, st(mn, kb)),
]
log("")
log("%-32s %10s %12s" % ("", "W/m2 mean", "stops vs baked"))
for nm, v, s in lines:
    log("%-32s %10.4f %12s" % (nm, v, "--" if s is None else "%+.4f" % s))
log("")
log("measured by the exposure calibration, sky alone : 11.1818  (%+.4f stops vs baked)"
    % st(11.1818, kb))
log("SHIPPED vs BARE                                 : %+.4f stops" % st(ms, mb))
log("the decks alone                                 : %+.4f stops" % st(ms, mn))

ctl_ok = abs(st(mb, kb)) <= RES
bad = []
if not ctl_ok:
    bad.append("POSITIVE CONTROL FAILED: a bare sky node at the contract's own "
               "parameters reads %.4f against the baked %.4f (%+.4f stops). "
               "calibrate() is not reproducible and every other row here is "
               "uninterpretable." % (mb, kb, st(mb, kb)))
if not hit:
    bad.append("NOCLOUD zeroed 0 decks -- the label this looks for has moved, "
               "so NOCLOUD is a second copy of SHIPPED and not a control")
for x in bad:
    log("FAIL " + x)
results["baked_mean"] = kb
results["measured_calibration_skyonly"] = 11.1818
results["samples"] = SAMPLES
results["per_channel_stops_shipped_vs_baked"] = [float(v) for v in np.log2(np.array(results["SHIPPED"]) / baked)]
results["sky_tint_published"] = [float(v) for v in C.SKY_TINT]
results["sky_tint_shipped"] = [float(v) for v in (np.array(results["SHIPPED"]) / max(results["SHIPPED"]))]
json.dump(results, open(OUT, "w"), indent=1)
log(">> STAGE RESULT: SKY_CAUSE_%s" % ("OK" if not bad else "FAIL"))
