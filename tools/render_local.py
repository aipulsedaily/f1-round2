"""Local fallback / cheap-preview renderer for the macro audit.

    /opt/blender-5.2.0-linux-x64/blender -b <blend> --factory-startup \
        -P tools/render_local.py -- --cam MACRO_SW --res 1920 1080 \
        --samples 96 -o /path/out.png [--standard] [--isolate SW_]

The 5090 does the final 4K/512 frames. This exists for the two jobs that do not
justify farm time: mask calibration (emission-only, so 32 samples is exact) and
a fallback if the broker is unavailable. It never substitutes for a full-quality
frame in a verdict.
"""
import argparse
import os
import sys

import bpy


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--cam", required=True)
    p.add_argument("--res", type=int, nargs=2, default=[1920, 1080])
    p.add_argument("--samples", type=int, default=128)
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--standard", action="store_true",
                   help="Standard view transform (mask renders must be linear)")
    p.add_argument("--no-dof", action="store_true")
    p.add_argument("--denoise", action="store_true")
    p.add_argument("--isolate", default=None,
                   help="comma list of object-name prefixes to keep in CAR/PROPS")
    p.add_argument("--device", default="GPU")
    p.add_argument("--depth", default="16", choices=["8", "16"])
    p.add_argument("--alpha", action="store_true",
                   help="transparent film + RGBA, so masks can be measured")
    p.add_argument("--nocomp", action="store_true",
                   help="bypass the scene's compositor (it is a Glare node)")
    a = p.parse_args(argv)

    sc = bpy.context.scene
    cam = bpy.data.objects.get(a.cam)
    if cam is None:
        raise SystemExit(f"no camera {a.cam}; have "
                         f"{[o.name for o in bpy.data.objects if o.type=='CAMERA']}")
    sc.camera = cam
    if a.no_dof:
        cam.data.dof.use_dof = False

    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = "CUDA"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = (d.type == "CUDA")
    except Exception as e:
        print(f"!! GPU setup: {e}")
    sc.cycles.device = a.device
    sc.render.resolution_x, sc.render.resolution_y = a.res
    sc.render.resolution_percentage = 100
    sc.cycles.samples = a.samples
    sc.cycles.use_denoising = a.denoise
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = a.depth
    if a.alpha:
        # a mask render must be measurable, and "which pixels are the part"
        # cannot be inferred from a threshold on the mask itself
        sc.render.film_transparent = True
        sc.render.image_settings.color_mode = "RGBA"
    if a.nocomp:
        sc.render.use_compositing = False
        sc.render.use_sequencer = False
    if a.standard:
        sc.view_settings.view_transform = "Standard"
        sc.view_settings.look = "None"

    # THE GRADE IS REPORTED, ALWAYS, AND LOUDLY WHEN IT IS WRONG.
    #
    # This tool renders whatever grade the blend carries and never touched
    # `view_settings.exposure`. That is CORRECT for a measurement render -- half
    # this project's instruments deliberately measure at exposure 0 -- so it is
    # not fixed by forcing a number. It is fixed by making the number visible,
    # because the defect it enabled was invisible: `build_verify_scene.py` set
    # no exposure at all, the assembly blends carry +0.000, and every frame an
    # agent looked at through that rig came out 3.628 stops over the film's
    # measured grade. Correct work looked blown out and verdicts were read off
    # frames with a quarter of their pixels saturated. Nothing in any log said
    # what grade had been used.
    try:
        _w = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "world")
        if _w not in sys.path:
            sys.path.insert(0, _w)
        import film_exposure as _FX
        _film = _FX.FILM_EXPOSURE
    except Exception:                                            # noqa: BLE001
        _film = None
    _exp = float(sc.view_settings.exposure)
    print(">> GRADE OF THIS RENDER: view_transform %r, look %r, exposure %+.3f"
          % (sc.view_settings.view_transform, sc.view_settings.look, _exp))
    if _film is None:
        print("   !! could not import world/film_exposure.py, so this render's "
              "grade cannot be compared to the film's. Say so in whatever you "
              "conclude from the picture.")
    elif abs(_exp - _film) > 0.001:
        print("   !! THIS IS NOT THE FILM'S GRADE. The film renders at %+.3f "
              "(world/film_exposure.FILM_EXPOSURE, MEASURED on the 5090). This "
              "frame is %+.3f stops from it." % (_film, _exp - _film))
        print("   !! That is fine for a MEASUREMENT (item_gate, winding_probe "
              "and idpass_emissive all measure at exposure 0 on purpose). It is "
              "NOT fine for a picture anyone is going to form a judgement from: "
              "at +0.000 on this world a frame that clips 0.000 % of its pixels "
              "at the film's grade clips 23.6 % of them (measured, "
              "render/exposure_beats/cal_960.png vs render/shutter_ab/*_f960.png).")

    if a.isolate:
        # Strict: hides the room too. This is a DIAGNOSTIC switch — a mask has to
        # be measured against transparent film, and the showroom shell filled
        # 90% of the frame with black, which then dominated every percentile.
        # Beauty renders never use it: the room is what lights the car.
        pfx = tuple(x.strip() for x in a.isolate.split(","))
        n = 0
        for ob in sc.objects:
            if ob.type != "MESH":
                continue
            keep = ob.name.startswith(pfx)
            ob.hide_render = not keep
            n += 0 if keep else 1
        print(f">> isolated {pfx}: hid {n} meshes (strict)")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    sc.render.filepath = os.path.abspath(a.out)
    bpy.ops.render.render(write_still=True)
    print(f">> wrote {a.out}")
    print(">> STAGE RESULT: RENDER_LOCAL_OK")



# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised: `blender -b -P x.py`
    # prints the traceback and exits 0, MEASURED on this box. A gate that
    # crashed was indistinguishable from one that passed. guard() makes an
    # uncaught exception a status 2 and passes any real verdict through
    # unchanged. One shared helper, not N copies -- see tools/gate_exit.py.
    gate_exit.guard(main, tool="render_local")
