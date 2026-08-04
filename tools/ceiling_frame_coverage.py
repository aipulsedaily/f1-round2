"""HOW MUCH CEILING IS IN EACH FRAME.  The instrument behind R2-622.

    blender -b world/camera_rig.blend --factory-startup \
        -P tools/ceiling_frame_coverage.py -- --out cover.json --end 800

Ray-casts a grid of image-plane directions against the plane z = 6.200, clipped
to the room footprint, per frame.  Answers "is the ceiling in shot, and how
much of the frame is it" without rendering anything.

IT UNDERSTATES THE ANSWER AND YOU MUST NOT FORGET THAT.  Two of the showroom's
four walls are a specular curtain wall, and the rendered frames at f300 and
f320 show the cove rings REFLECTED across most of the picture in frames this
instrument scores at 8.8 % and 15.8 %.  A ceiling can be in a shot without
being in the ceiling plane's solid angle.  See R2-622.
"""
import json, math, sys, traceback
import bpy
from mathutils import Vector

argv = sys.argv; argv = argv[argv.index("--")+1:] if "--" in argv else []
def opt(k, d):
    return argv[argv.index(k)+1] if k in argv else d
out = opt("--out", "/tmp/campath.json")
f0  = int(opt("--start", "1")); f1 = int(opt("--end", "800"))

CEIL_Z = 6.20
ROOM = {"x": (-15.25, 15.25), "y": (-11.25, 11.25)}
NX, NY = 33, 19        # NDC sample grid

TOKEN = "CAMPATH_FAIL"
rep = {"ceil_z": CEIL_Z, "room": ROOM, "frames": {}}
try:
    sc = bpy.context.scene
    cam = sc.camera
    if cam is None:
        for ob in sc.objects:
            if ob.type == "CAMERA": cam = ob; break
    rep["camera_name"] = cam.name
    rep["scene_frames"] = [sc.frame_start, sc.frame_end]
    best = []
    for f in range(f0, f1+1):
        sc.frame_set(f)
        M = cam.matrix_world
        loc = M.translation.copy()
        cd = cam.data
        # sensor
        rx, ry = sc.render.resolution_x, sc.render.resolution_y
        ar = rx / ry
        sw, sh = cd.sensor_width, cd.sensor_height
        fit = cd.sensor_fit
        if fit == "AUTO":
            if ar >= 1.0: sw_eff, sh_eff = sw, sw/ar
            else:         sw_eff, sh_eff = sw*ar, sw
        elif fit == "HORIZONTAL": sw_eff, sh_eff = sw, sw/ar
        else:                     sw_eff, sh_eff = sh*ar, sh
        lens = cd.lens
        R = M.to_3x3()
        fwd = R @ Vector((0,0,-1))
        hit = 0; tot = 0
        for iy in range(NY):
            vy = (iy + 0.5)/NY*2 - 1
            for ix in range(NX):
                vx = (ix + 0.5)/NX*2 - 1
                d = R @ Vector((vx*sw_eff/2.0, vy*sh_eff/2.0, -lens))
                d.normalize()
                tot += 1
                if d.z <= 1e-9: continue
                t = (CEIL_Z - loc.z)/d.z
                if t <= 0: continue
                p = loc + d*t
                if ROOM["x"][0] <= p.x <= ROOM["x"][1] and ROOM["y"][0] <= p.y <= ROOM["y"][1]:
                    hit += 1
        elev = math.degrees(math.asin(max(-1,min(1,fwd.z))))
        vhalf = math.degrees(math.atan((sh_eff/2.0)/lens))
        rec = {"loc":[round(v,4) for v in loc], "lens":round(lens,3),
               "elev_deg":round(elev,3), "vhalf_deg":round(vhalf,3),
               "top_edge_elev_deg":round(elev+vhalf,3),
               "ceil_frac":round(hit/tot,4)}
        rep["frames"][str(f)] = rec
        best.append((rec["ceil_frac"], f))
    best.sort(reverse=True)
    rep["top20_by_ceiling"] = [{"frame":f,"frac":c} for c,f in best[:20]]
    rep["n_frames_with_ceiling"] = sum(1 for c,f in best if c > 0)
    rep["max_frac"] = best[0][0] if best else None
    TOKEN = "CAMPATH_OK"
except Exception:
    traceback.print_exc(); rep["traceback"] = traceback.format_exc()
finally:
    json.dump(rep, open(out,"w"), indent=1)
    print(">> wrote %s" % out)
    print(">> STAGE RESULT: %s" % TOKEN)
