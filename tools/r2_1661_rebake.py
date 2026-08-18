"""R2-1661: re-bake the camera set into an already-built terrain blend.

    blender -b --factory-startup -noaudio -P tools/r2_1661_rebake.py -- \
        --module world/_b6_before_terrain.py --load IN.blend --save OUT.blend \
        --cams b6_2811,b6_2978,t5_verge,esses

`bake_cameras` deletes cameras that do NOT start with `CAM_` and then creates the
ones it was asked for, so running it twice on the same blend collides names and
leaves `CAM_b6_2811.001` behind while its return value still says `CAM_b6_2811` --
and the broker discovers cameras by name.  Everything `CAM_*` is therefore removed
first, so the bake starts from nothing and the names it reports are the names in the
file.

The A/B arms must be baked from their OWN module: the before arm's view table has to
be the before arm's, or the comparison is not at a matched camera.
"""
import bpy, sys, os, json, importlib.util

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


mod_path = arg("--module")
spec = importlib.util.spec_from_file_location("ter_arm", mod_path)
T = importlib.util.module_from_spec(spec)
sys.modules["ter_arm"] = T
spec.loader.exec_module(T)

src = arg("--load")
dst = arg("--save")
names = arg("--cams").split(",")

bpy.ops.wm.open_mainfile(filepath=src)
gone = [o.name for o in list(bpy.data.objects) if o.type == "CAMERA"]
for o in list(bpy.data.objects):
    if o.type == "CAMERA":
        bpy.data.objects.remove(o, do_unlink=True)
print("[rebake] removed %d existing cameras: %s" % (len(gone), gone))

made = T.bake_cameras(names)
have = sorted(o.name for o in bpy.data.objects if o.type == "CAMERA")
ok = sorted(made) == have and all(("CAM_" + n) in have for n in names)
bpy.ops.wm.save_as_mainfile(filepath=dst)
sz = os.path.getsize(dst) / 1e6
print(">> STAGE RESULT: %s %s"
      % ("R2_1661_REBAKE_OK" if ok else "R2_1661_REBAKE_FAIL",
         json.dumps(dict(module=mod_path, src=src, dst=dst, mb=round(sz, 1),
                         requested=names, made=made, in_file=have))))
