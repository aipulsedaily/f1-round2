#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2366_swing.py — RENDER a height texture alone and MEASURE its peak-to-peak.

WHY. `itemkit.bump_relief_report` computes `amp_mm = Distance * Strength *
height_pp * 1000` and defaults `height_pp = 1.0` because that is the
CONSERVATIVE assumption — its own docstring says a raw Noise swings about 0.6 of
that, so a stage it reports at m = 2.3 is "at least 1.4".

That is fine for an audit. It is NOT fine for AUTHORING. If I want a stage to
land at m = 0.55 I have to know what the height signal actually swings, or the
amplitude I set is off by whatever the real swing is and the number I report is
a guess wearing a measurement's clothes. Substituting a plausible 0.75 would be
exactly the failure this project keeps logging.

So this does what `itemkit.emitted_wavelength_m` does for wavelength, for
amplitude: it renders the texture alone, through Cycles, and reads the swing.

    ITS OWN SCENE. Never the caller's, and it refuses unless the scene holds
    only its own plane and camera — `--factory-startup` is not an empty scene.
    1 sample, max_bounces 0, DENOISER OFF, view_transform 'Standard', 32-bit
    EXR. A denoiser and a tone curve both attack precisely the quantity being
    measured.

Reports p-p over the full render and over the 1st..99th percentile. THE
PERCENTILE ONE IS THE HONEST FIGURE for a bump amplitude: a fractal noise has
rare spikes that set the full range but carry no area, and sizing a surface to
them under-drives everything that is actually visible.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/r2366_swing.py -- [--json OUT]

Blender 5.2 exits 0 on an uncaught script exception; judge on `STAGE RESULT`.
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))

import bpy                                                   # noqa: E402
import numpy as np                                           # noqa: E402

# (label, node kind, scale, detail, roughness, distortion) — the height sources
# the paving materials use or will use. `span` is the plane's world size, chosen
# so each texture gets >= 40 cycles across the frame and is sampled at >= 16 px
# per cycle: too few cycles and the p-p is a sample of a short window, too few
# pixels per cycle and the render itself low-passes what is being measured.
PROBES = [
    # the SHIPPED stages, so the audit's conservative numbers can be corrected
    ("shipped_forecourt_agg", 85.0, 10.0, 0.70, 0.0, 1.0),
    ("shipped_apron_agg", 85.0, 10.0, 0.70, 0.0, 1.0),
    ("shipped_paddock_agg", 55.0, 10.0, 0.72, 0.0, 1.5),
    # the stages this task adds, one per readable octave
    ("r2366_aggregate", 62.0, 8.0, 0.62, 0.0, 1.4),
    ("r2366_float", 7.0, 6.0, 0.55, 0.0, 12.0),
    ("r2366_screed", 1.15, 5.0, 0.52, 0.0, 70.0),
    ("r2366_settle", 0.30, 4.0, 0.48, 0.0, 260.0),
]


def render_fac(scale, detail, rough, dist, span, px=1024):
    """Render one Noise Fac over a plane and return the raw float image."""
    sc = bpy.data.scenes.new("R2366_SWING")
    tmp = tempfile.mkdtemp(prefix="r2366_swing_")
    try:
        sc.render.engine = 'CYCLES'
        sc.cycles.samples = 1
        sc.cycles.use_denoising = False
        sc.cycles.max_bounces = 0
        sc.render.resolution_x = sc.render.resolution_y = int(px)
        sc.render.resolution_percentage = 100
        sc.render.image_settings.file_format = 'OPEN_EXR'
        sc.render.image_settings.color_depth = '32'
        sc.render.film_transparent = False
        sc.view_settings.view_transform = 'Standard'
        sc.view_settings.look = 'None'
        sc.view_settings.exposure = 0.0
        wd = bpy.data.worlds.new("R2366_SWING_W")
        sc.world = wd
        wd.use_nodes = True
        bn = wd.node_tree.nodes.get("Background")
        if bn:
            bn.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
            bn.inputs["Strength"].default_value = 0.0

        me = bpy.data.meshes.new("R2366_SWING_M")
        h = span * 0.5
        me.from_pydata([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)],
                       [], [(0, 1, 2, 3)])
        me.update()
        pl = bpy.data.objects.new("R2366_SWING_PLANE", me)
        sc.collection.objects.link(pl)
        cd = bpy.data.cameras.new("R2366_SWING_CAM")
        cd.type = 'ORTHO'
        cd.ortho_scale = span
        cam = bpy.data.objects.new("R2366_SWING_CAM", cd)
        sc.collection.objects.link(cam)
        cam.location = (0.0, 0.0, 5.0)
        sc.camera = cam
        # The guard compares the datablock IDENTITY, not the name: Blender
        # uniquifies to `...PLANE.001` on the second call and a name-equality
        # guard then refuses its own valid scene from the second probe onward.
        got = set(sc.collection.all_objects)
        if got != {pl, cam}:
            raise RuntimeError("swing probe REFUSES: its scene holds %r, not "
                               "just its own plane and camera"
                               % (sorted(o.name for o in got),))

        m = bpy.data.materials.new("R2366_SWING_MAT")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        # object coordinates, exactly as the paving materials drive their noise
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.noise_dimensions = '3D'
        # SOCKETS BY NAME. `Normal` moved 5 -> 6 in 5.2 and index pinning cost
        # this project 20 materials.
        nz.inputs["Scale"].default_value = float(scale)
        nz.inputs["Detail"].default_value = float(detail)
        nz.inputs["Roughness"].default_value = float(rough)
        if "Distortion" in nz.inputs:
            nz.inputs["Distortion"].default_value = float(dist)
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = 1.0
        nt.links.new(nz.outputs["Fac"], em.inputs["Color"])
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
        me.materials.append(m)

        fp = os.path.join(tmp, "swing.exr")
        sc.render.filepath = fp
        bpy.ops.render.render(write_still=True, scene=sc.name)
        img = bpy.data.images.load(fp)
        a = np.array(img.pixels[:], dtype=np.float64).reshape(-1, 4)[:, 0]
        bpy.data.images.remove(img)
        return a
    finally:
        bpy.data.scenes.remove(sc)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    jout = argv[argv.index("--json") + 1] if "--json" in argv else None
    import itemkit as K

    rows = []
    print("  %-24s %8s %9s %9s %9s %9s"
          % ("stage", "scale", "lam_mm", "pp_full", "pp_1_99", "span_m"))
    for name, scale, detail, rough, dist, span in PROBES:
        lam = K.NOISE_WAVELENGTH_FACTOR / scale
        a = render_fac(scale, detail, rough, dist, span)
        pp = float(a.max() - a.min())
        lo, hi = np.percentile(a, [1.0, 99.0])
        pp99 = float(hi - lo)
        rows.append(dict(stage=name, scale=scale, detail=detail,
                         roughness=rough, distortion=dist, span_m=span,
                         wavelength_m=lam, pp_full=pp, pp_1_99=pp99,
                         p1=float(lo), p99=float(hi), mean=float(a.mean())))
        print("  %-24s %8.2f %9.2f %9.4f %9.4f %9.2f"
              % (name, scale, lam * 1000.0, pp, pp99, span))

    if jout:
        os.makedirs(os.path.dirname(jout) or ".", exist_ok=True)
        json.dump({"note": "pp_1_99 is the figure to size a bump with",
                   "probes": rows}, open(jout, "w"), indent=1)
        print("\nwrote %s" % jout)
    print("STAGE RESULT: r2366_swing PASS (%d stages measured)" % len(rows))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        print("STAGE RESULT: r2366_swing FAIL (uncaught exception)")
        sys.exit(1)
