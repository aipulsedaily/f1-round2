#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2651_agx_curve.py — THE FILM'S OWN TRANSFER CURVE, MEASURED, NOT ASSUMED.

Every contrast number in `build_surface.md` is a LINEAR ALBEDO ratio taken from
a plan view under a uniform dome. Every contrast number a pixel gate can take is
a DISPLAY luminance ratio out of a delivered PNG. Comparing the two directly is
meaningless, and doing it anyway is how a material gets condemned for something
the view transform did.

This builds the exact map between them for THIS film's grade — AgX, look None,
exposure -3.628 — by pushing a known linear ramp through Blender's own colour
management and reading back what it wrote. No formula, no approximation of AgX,
no assumption about where the toe is.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/r2651_agx_curve.py -- --out=render/r2651/agx.json

Judge on the printed STAGE RESULT line.
"""
import json
import os
import sys

TOKEN_OK = "R2651_AGX_CURVE_OK"
EXPOSURE = -3.628


def main():
    import bpy
    import numpy as np

    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "render/r2651/agx.json")
    for a in argv:
        if a.startswith("--out="):
            out = os.path.join(root, a.split("=", 1)[1])

    # A log-spaced linear ramp, written into a float image, saved through the
    # film's view transform, and read back as 8-bit display values.
    N = 4096
    lin = np.geomspace(1e-5, 64.0, N)
    img = bpy.data.images.new("ramp", width=N, height=1, float_buffer=True,
                              is_data=False)
    px = np.zeros((N, 4), dtype=np.float32)
    px[:, 0] = lin
    px[:, 1] = lin
    px[:, 2] = lin
    px[:, 3] = 1.0
    img.pixels.foreach_set(px.ravel())

    scene = bpy.context.scene
    vs = scene.view_settings
    vs.view_transform = "AgX"
    vs.look = "None"
    vs.exposure = EXPOSURE
    vs.gamma = 1.0
    scene.display_settings.display_device = "sRGB"
    scene.sequencer_colorspace_settings.name = "sRGB"

    tmp = os.path.join(root, "render/r2651/_agx_ramp.png")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "16"
    img.save_render(tmp, scene=scene)

    back = bpy.data.images.load(tmp)
    ob = np.empty(back.size[0] * back.size[1] * 4, dtype=np.float32)
    back.pixels.foreach_get(ob)
    ob = ob.reshape(-1, 4)
    # `pixels` of a loaded PNG are already linearised from sRGB by Blender, so
    # re-encode to get the DISPLAY code value the audience actually sees.
    d = ob[:, 0]
    disp = np.where(d <= 0.0031308, d * 12.92, 1.055 * np.power(np.maximum(d, 0), 1 / 2.4) - 0.055)

    data = dict(exposure=EXPOSURE, view_transform="AgX", look="None",
                lin=[float(v) for v in lin],
                disp=[round(float(v), 6) for v in disp])
    json.dump(data, open(out, "w"))

    def d_of(x):
        return float(np.interp(x, lin, disp))

    def l_of(y):
        return float(np.interp(y, disp, lin))

    print(">> AgX, look None, exposure %.3f" % EXPOSURE)
    print("   linear 0.18 -> display %.4f" % d_of(0.18))
    print("   linear 1.00 -> display %.4f" % d_of(1.0))
    print("   display 0.200 -> linear %.6f" % l_of(0.200))
    print("   display 0.268 -> linear %.6f" % l_of(0.268))
    print("   the f2000 cross-section, 0.268 : 0.200 display, is a LINEAR ratio "
          "of %.3f : 1" % (l_of(0.268) / max(l_of(0.200), 1e-12)))
    for r in (1.5, 2.0, 2.4, 2.9, 3.3):
        # what a linear ratio r delivers on screen, anchored so the DARK side
        # sits where the measured rubbered heart sits
        lo = l_of(0.200)
        print("   linear %.1f : 1 anchored at the measured heart -> display "
              "%.4f vs %.4f = %.3f : 1"
              % (r, d_of(lo * r), 0.200, d_of(lo * r) / 0.200))
    print(">> wrote %s" % out)
    print(">> STAGE RESULT: %s" % TOKEN_OK)


main()
