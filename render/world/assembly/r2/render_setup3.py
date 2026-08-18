"""render_setup3 = render_setup2 + the two v1.1.1 defect cameras.

Light the reassembled world with build_sky and plant the cameras that have to
answer for the five defects, then save a render blend for tools/r5090.

    blender -b -noaudio <assembly2.blend> -P render_setup2.py -- --out=<render.blend>

Camera list is deliberately short: the 5090 worker prewarms EVERY camera at load.
Three of them (CAM_T4_INTRUSION, CAM_GLASS_GAP, CAM_TRANSIT_BLOCK) are placed at
BIT-IDENTICAL positions to the assembly review's frames so the before/after is a
pixel comparison and not an impression.
"""
import sys, os, json, math
import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.expanduser("~/f1-round2/world"))
import world_contract as C
import film_exposure as FX          # THE film's exposure, derived from C, one place

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(n, d=None):
    for a in argv:
        if a.startswith("--%s=" % n):
            return a.split("=", 1)[1]
    return d


OUT = opt("out", os.path.expanduser("~/f1-round2/render/world/assembly/r2/render3.blend"))
# NOT A LITERAL ANY MORE.  This file used to hardcode -3.628 with no comment
# while world_contract derived -3.048, and nothing could notice the 0.580-stop
# disagreement because the two numbers never met.  `world/film_exposure.py` is
# now the one expression: C.REFERENCE_EXPOSURE_EXTERIOR plus the two MEASURED
# corrections its inputs omit (SKY_Atmosphere's airlight, and C.SKY_IRRADIANCE's
# own shortfall).  It selftests against a rendered 18 % card.  The measurement
# says -3.6343 and this file's old literal was right to 0.006 stops; the
# contract's derived value was 0.586 stops OVER.
EXPOSURE = float(opt("exposure", str(FX.FILM_EXPOSURE)))

scn = bpy.context.scene

_veg = [o for o in bpy.data.objects
        if o.name.startswith("VEG_") or (o.name.startswith("TER_")
                                         and not o.name.startswith("TER_Ground"))]
for o in _veg:
    o.hide_viewport = True
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()


def ground(x, y, nmax=12):
    z = 900.0
    for _ in range(nmax):
        hit, loc, nor, i, ob, m = scn.ray_cast(dg, Vector((x, y, z)),
                                               Vector((0, 0, -1)),
                                               distance=z + 400.0)
        if not hit:
            return None, None
        if not ob.name.startswith("SKY_"):
            return loc.z, ob.name
        z = loc.z - 2e-4
    return None, None


def P(s, u, side=+1, dz=0.0):
    x, y, z = C.su_to_world(float(s), float(u), side)
    return Vector((float(x), float(y), float(z) + dz))


def aim(ob, loc, tgt):
    ob.location = Vector(loc)
    d = Vector(tgt) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def mk(name, loc, tgt, lens=35.0):
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start, cd.clip_end = 0.05, 60000.0
    cd.dof.use_dof = False
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, cd)
        scn.collection.objects.link(ob)
    ob.data = cd
    aim(ob, loc, tgt)
    return ob


rep = {}

# 1. THE T4 INTRUSION FRAME — byte-identical placement to the review's camera
mk("CAM_T4_INTRUSION", P(872.0, -1.5, +1, 2.30), P(918.0, 2.0, +1, 0.60),
   lens=40.0)

# 2. the same braking zone at KERB HEIGHT, which is where Beat 5 drives
mk("CAM_T4_KERB", P(860.0, 4.5, +1, 0.34), P(930.0, 6.5, +1, 0.30), lens=50.0)

# 3. THE GLASS MOUTH — byte-identical placement to the review's camera
gz, gn = ground(12.0, 0.0)
mk("CAM_GLASS_GAP", Vector((11.2, -1.6, (gz or 0.0) + 0.85)),
   Vector((15.6, 0.4, (gz or 0.0) - 0.10)), lens=50.0)
rep["glass_ground_at_x12"] = [None if gz is None else round(gz, 4), gn]

# 4. THE APRON EDGE, raking down the pit straight into the 12.47 deg sun.
#    Sun bearing is C.SUN_BEARING_DEG; a joint reads darkest when the lens looks
#    along the joint with the sun near-grazing across it.
e_ap = float(C.verge_edge(np.array([3260.0]))[0])
mk("CAM_APRON_EDGE", P(3232.0, e_ap + 0.75, +1, 0.55),
   P(3350.0, e_ap + 0.10, +1, 0.02), lens=85.0)
rep["apron_verge_edge"] = round(e_ap, 4)

# 5. THE DOPPLER HOVER — the beat sheet's own station, 4K, for the grass crop
bs = json.load(open(os.path.expanduser("~/f1-round2/docs/beat_sheet.json")))
dp = bs["doppler"]
dcam = Vector(dp["camera_world"])
dtgt = P(float(dp["station_s"]), 0.0, +1, 0.6)
mk("CAM_DOPPLER", dcam, dtgt, lens=35.0)
rep["doppler"] = {"cam": [round(v, 3) for v in tuple(dcam)],
                  "station_s": dp["station_s"],
                  "tgt": [round(v, 3) for v in tuple(dtgt)]}

# 6. THE WIDE — the whole circuit from the Beat-6 hold key
b6 = bs["beat6"]
mk("CAM_WIDE", Vector(b6["hold_world"]), P(1500.0, 0.0, +1, 0.0),
   lens=float(b6["hold_lens_mm"]))
rep["wide"] = {"cam": [round(v, 2) for v in b6["hold_world"]],
               "lens": b6["hold_lens_mm"]}

# 7. THE BEAT-4 PIT-EXIT ROAD — byte-identical to the review's camera
X, Y, H = C.access_route_arrays(np.array([112.0]))
x0, y0, h0 = float(X[0]), float(Y[0]), float(H[0])
X2, Y2, H2 = C.access_route_arrays(np.array([140.0]))
gz2, _ = ground(x0, y0)
tz, _ = ground(float(X2[0]), float(Y2[0]))
mk("CAM_TRANSIT_BLOCK", Vector((x0, y0, (gz2 or 0.0) + 1.55)),
   Vector((float(X2[0]) - math.sin(float(H2[0])) * 4.5,
           float(Y2[0]) + math.cos(float(H2[0])) * 4.5, (tz or 0.0) + 0.60)),
   lens=45.0)

# 8. EXPOSURE CALIBRATION — an 18 % lambertian card on real open ground
best = None
for cx, cy in ((900.0, -300.0), (-900.0, 600.0), (700.0, -420.0),
               (-300.0, 1250.0), (1000.0, 300.0)):
    zs = []
    ok = True
    for dx in (-8, 0, 8):
        for dy in (-8, 0, 8):
            z, nm = ground(cx + dx, cy + dy)
            if z is None or nm is None:
                ok = False; break
            zs.append((z, nm))
        if not ok:
            break
    if not ok or not zs:
        continue
    if any(not n.startswith("TER_Ground") for _z, n in zs):
        continue
    zz = np.array([z for z, _n in zs])
    flat = float(zz.max() - zz.min())
    if best is None or flat < best[0]:
        best = (flat, cx, cy, float(zz.mean()))
flat, cx, cy, cz = best
me = bpy.data.meshes.new("CAL_Card")
sz = 6.0
me.from_pydata([(-sz, -sz, 0), (sz, -sz, 0), (sz, sz, 0), (-sz, sz, 0)], [],
               [(0, 1, 2, 3)])
me.update()
card = bpy.data.objects.new("CAL_Card", me)
card.location = Vector((cx, cy, cz + 0.30))
scn.collection.objects.link(card)
m = bpy.data.materials.new("CAL_Grey18")
m.use_nodes = True
nt = m.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
d = nt.nodes.new("ShaderNodeBsdfDiffuse")
d.inputs["Color"].default_value = (0.18, 0.18, 0.18, 1.0)
d.inputs["Roughness"].default_value = 0.0
o = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(d.outputs[0], o.inputs["Surface"])
card.data.materials.append(m)
mk("CAM_CAL", Vector((cx, cy - 2.6, cz + 3.8)), Vector((cx, cy, cz + 0.30)),
   lens=50.0)
rep["cal"] = dict(xy=[cx, cy], ground_z=round(cz, 3),
                  flatness_over_16m=round(flat, 3))


# --------------------------------------------------------------------------- #
#  v1.1.1 ADDITIONS — the two frames that have to answer for #46 and #47/#48.   #
#  Placed AFTER the original list so every camera above keeps its bit-identical  #
#  placement and the before/after stays a pixel comparison.                      #
# --------------------------------------------------------------------------- #

# 9. THE PIT WALL'S WEST TERMINAL, from the transit lane, at car height.  This is
#    the object the placement gate measured 1.067 m inside the car's swept volume.
_s_nose = float(getattr(C, "PIT_WALL_S0", 3430.0))
mk("CAM_PIT_NOSE", P(_s_nose - 26.0, 13.6, +1, 0.65),
   P(_s_nose + 9.0, 11.5, +1, 0.60), lens=50.0)
rep["pit_nose"] = {"s0": round(_s_nose, 3),
                   "circuit_x": round(_s_nose - C.LAP, 3)}

# 10. THE PIT-EXIT SEAM, raking east along the strip between the track edge and
#     the apron platform — the 32 m2 of unwelded rim and the black line at
#     platform_edge, in one frame, at a grazing 12.47 deg sun.
_e_px = float(C.verge_edge(np.array([3470.0]))[0])
mk("CAM_PITEXIT_SEAM", P(3436.0, _e_px + 1.30, +1, 0.42),
   P(3556.0, _e_px + 0.55, +1, 0.02), lens=85.0)
rep["pitexit_seam"] = {"verge_edge": round(_e_px, 4)}

scn.camera = bpy.data.objects["CAM_T4_INTRUSION"]

import build_sky as SKY
sky_stats = SKY.build(scn, scn.camera)

scn.render.engine = 'CYCLES'
scn.cycles.device = 'GPU'
scn.cycles.use_adaptive_sampling = True
scn.cycles.adaptive_threshold = 0.005
scn.cycles.max_bounces = 8
scn.cycles.diffuse_bounces = 4
scn.cycles.glossy_bounces = 4
scn.cycles.transmission_bounces = 8
scn.cycles.transparent_max_bounces = 24
scn.cycles.use_denoising = True
scn.render.resolution_x = 3840
scn.render.resolution_y = 2160
scn.render.resolution_percentage = 100
scn.render.film_transparent = False
scn.view_settings.view_transform = FX.VIEW_TRANSFORM
scn.view_settings.look = FX.VIEW_LOOK
scn.view_settings.exposure = EXPOSURE
scn.render.image_settings.file_format = 'PNG'
scn.render.image_settings.color_depth = '16'

for o in _veg:
    o.hide_viewport = False
for ob in bpy.data.objects:
    if ob.type == 'CAMERA':
        ob.data.dof.use_dof = False
bpy.context.view_layer.update()

os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=False)
rep["out"] = OUT
rep["mb"] = round(os.path.getsize(OUT) / 1048576.0, 1)
rep["cameras"] = sorted(o.name for o in bpy.data.objects if o.type == 'CAMERA')
rep["exposure"] = EXPOSURE
rep["exposure_source"] = {
    "module": "world/film_exposure.py",
    "film_exposure": FX.FILM_EXPOSURE,
    "contract": FX.CONTRACT_EXPOSURE,
    "atmosphere_stops": FX.ATMOSPHERE_STOPS,
    "sky_shortfall_stops": FX.SKY_SHORTFALL_STOPS,
    "overridden_on_command_line": abs(EXPOSURE - FX.FILM_EXPOSURE) > 1e-9}
rep["sun"] = {"elev_deg": C.SUN_ELEV_DEG, "bearing_deg": C.SUN_BEARING_DEG,
              "shadow_ratio": C.SUN_SHADOW_RATIO}
rep["veg_restored"] = len(_veg)
print("[RENDER-SETUP2] " + json.dumps(rep, indent=1, default=str))
with open(OUT.replace(".blend", "_setup.json"), "w") as f:
    json.dump(rep, f, indent=1, default=str)
