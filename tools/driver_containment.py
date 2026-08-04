"""R2-242 -- does the driver appear ANYWHERE he should not?

The driver's hip sits 0.229 m below round 1's seat pan, because round 1's
cockpit tub offers 0.249 m of hip-to-headrest rise where a 1.78 m man needs
0.552 m and the car is READ-ONLY (`tools/place_driver.py`).  Everything below
the cockpit rim is therefore INSIDE the monocoque.  That is only acceptable if
it is also invisible, and "the tub is opaque" is an assumption, not a
measurement -- a knee through a sidepod or a boot through the floor would be
exactly the kind of defect this project keeps shipping because nobody looked.

THE INSTRUMENT
    Cycles renders the OBJECT INDEX pass with every `DRV_*` object at index 7
    and the car at 0.  A pixel reads 7 only where the driver is the FRONTMOST
    surface, so the pass is a direct map of where the driver reaches the film.
    Filter width is forced to 0.01 px so no pixel is a blend of two indices.

THE GATE
    Every driver pixel must fall inside the projection of the COCKPIT APERTURE
    VOLUME -- the box above the cockpit rim that the opening looks into,
    measured off `CI_seal` / `CI_sidehead` rather than declared -- dilated by
    `--margin` px.

BOTH CONTROLS, because a containment test that cannot fail proves nothing:
    POSITIVE  `--control-displace 0.45` shoves the driver 0.45 m to his left,
              through the side of the tub.  The gate MUST fail.  If it passes,
              the gate is blind and its verdict on the real driver is worthless.
    NEGATIVE  the driver is hidden and the pass must contain ZERO index-7
              pixels, and the real run must contain MANY.  A metric that reads
              the same present-or-absent is not a measurement.
"""

import argparse
import json
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES_X, RES_Y, SENSOR = 3840, 2160, 36.0
DRV_INDEX = 7


def log(m):
    sys.stdout.write("[containment] %s\n" % m)
    sys.stdout.flush()


def film_camera(path_json, frame):
    d = json.load(open(path_json))["path"]
    p = d[frame - 1]
    assert p["f"] == frame, "path frame %s != %s" % (p["f"], frame)
    cam = bpy.data.cameras.new("CAM_Probe")
    cam.sensor_fit = 'AUTO'
    cam.sensor_width = SENSOR
    cam.lens = float(p["lens"])
    cam.clip_start = 0.02
    cam.clip_end = 6000.0
    ob = bpy.data.objects.new("CAM_Probe", cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_mode = 'QUATERNION'
    ob.location = Vector(p["p"])
    ob.rotation_quaternion = Quaternion(p["q"])
    return ob, float(p["lens"])


def aperture_hull(root, cam, m_lo, m_hi):
    """Screen-space convex hull of the cockpit aperture volume."""
    sc = bpy.context.scene
    corners = []
    for x in (m_lo[0], m_hi[0]):
        for y in (m_lo[1], m_hi[1]):
            for z in (m_lo[2], m_hi[2]):
                corners.append(root.matrix_world @ Vector((x, y, z)))
    from bpy_extras.object_utils import world_to_camera_view
    P = []
    for w in corners:
        c = world_to_camera_view(sc, cam, w)
        if c.z <= 0:
            return None            # volume straddles the camera plane
        P.append((c.x * RES_X, (1.0 - c.y) * RES_Y))
    P = np.array(P)
    # monotone chain
    pts = sorted(map(tuple, P))
    def half(ps):
        h = []
        for q in ps:
            while len(h) >= 2 and ((h[-1][0]-h[-2][0])*(q[1]-h[-2][1])
                                   - (h[-1][1]-h[-2][1])*(q[0]-h[-2][0])) <= 0:
                h.pop()
            h.append(q)
        return h
    hull = half(pts)[:-1] + half(pts[::-1])[:-1]
    return np.array(hull)


def inside_hull(px, py, hull, margin):
    """Signed-distance containment; +margin px of slack."""
    n = len(hull)
    ok = np.ones(len(px), bool)
    for i in range(n):
        a = hull[i]; b = hull[(i + 1) % n]
        e = b - a
        L = math.hypot(e[0], e[1])
        if L < 1e-9:
            continue
        # outward normal for a CCW hull in screen coords
        nx, ny = e[1] / L, -e[0] / L
        d = (px - a[0]) * nx + (py - a[1]) * ny
        ok &= (d <= margin)
    return ok


def _flat_override():
    """One opaque diffuse material for everything, so ALPHA is pure coverage.

    Without it the visor is a transmissive surface and its alpha is a shading
    result rather than a yes/no.  The gate needs coverage, not appearance.
    """
    m = bpy.data.materials.get("DRVGATE_Flat")
    if m is None:
        m = bpy.data.materials.new("DRVGATE_Flat")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        d = nt.nodes.new("ShaderNodeBsdfDiffuse")
        nt.links.new(d.outputs[0], out.inputs["Surface"])
    return m


def render_mask(cam, frame, out_png):
    """-> boolean array, True where a DRIVER surface is FRONTMOST.

    NO COMPOSITOR.  Blender 5.2 removed `Scene.node_tree` (it is now a
    compositing node GROUP, and a group whose input is not a Render Layers node
    renders black -- the trap already on record for this project), so the first
    cut of this gate died on `sc.node_tree` and Blender still exited 0.

    The mask is built out of ALPHA instead: every CAR mesh is set to
    `is_holdout`, so it punches a transparent hole while still OCCLUDING.  With
    `film_transparent` the alpha channel is then 1 exactly where an unoccluded
    driver surface is in front, and 0 for sky, car, and anything the car hides.
    At 1 sample with a 0.01 px filter that is binary, with no denoiser and no
    noise to threshold.
    """
    sc = bpy.context.scene
    sc.frame_set(frame)
    sc.camera = cam
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 1
    sc.cycles.use_denoising = False
    sc.cycles.use_adaptive_sampling = False
    sc.cycles.max_bounces = 0
    sc.render.resolution_x = RES_X
    sc.render.resolution_y = RES_Y
    sc.render.resolution_percentage = 100
    sc.render.filter_size = 0.01
    sc.render.film_transparent = True
    sc.render.use_motion_blur = False
    sc.view_layers[0].material_override = _flat_override()
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0.0
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '8'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(out_png)
    a = np.array(im.pixels[:], dtype=np.float32).reshape(RES_Y, RES_X, 4)
    bpy.data.images.remove(im)
    return (a[..., 3] > 0.5)[::-1]          # blender rows are bottom-up


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, nargs="+", default=[2632, 2625, 828, 700])
    ap.add_argument("--path", default=os.path.join(R2, "render/film14_path.json"))
    ap.add_argument("--outdir", default=os.path.join(R2, "render/driver"))
    ap.add_argument("--margin", type=float, default=8.0)
    ap.add_argument("--report", default=os.path.join(R2, "docs/driver_containment.json"))
    ap.add_argument("--control-displace", type=float, default=0.0,
                    help="POSITIVE CONTROL: shove the driver this many metres "
                         "in +y, through the side of the tub. The gate must fail.")
    a = ap.parse_args(argv)
    os.makedirs(a.outdir, exist_ok=True)

    root = bpy.data.objects.get("CAR_ROOT")
    drv = [o for o in bpy.data.objects if o.name.startswith("DRV_")
           and o.type == 'MESH']
    if not drv:
        raise SystemExit("no DRV_* meshes in this blend")
    log("%d DRV_* meshes" % len(drv))
    # The DRV_* objects carry KEYED hide_render (they are hidden until the
    # cockpit is built -- tools/place_driver.py --appear).  This gate drives
    # hide_render by hand, so the keys would silently overwrite it on every
    # frame_set and the "driver absent" pass would come back WITH the driver
    # at frames >= appear.  Drop the visibility animation in this in-memory
    # copy only; nothing here ever saves.
    #
    # BUT RESTORE WHAT WAS AUTHORED, NOT `False`.  The first cut forced every
    # DRV_* object visible for the "driver present" pass, which switched the
    # BOOTS back on -- the very objects place_driver had just excluded from the
    # render.  The gate then reported the identical 12 px / 211 px leak before
    # and after the fix and looked like a fix that did nothing.  A gate that
    # overrides the thing it is measuring is measuring itself.
    shown = {}
    for o in drv:
        keyed = bool(o.animation_data and o.animation_data.action)
        shown[o.name] = (False if keyed else bool(o.hide_render))
        o.animation_data_clear()
    log("authored visibility: %d of %d DRV_* meshes render; hidden: %s"
        % (sum(1 for v in shown.values() if not v), len(drv),
           sorted(k for k, v in shown.items() if v)))
    drvset = set(o.name for o in drv)
    ncar = 0
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name not in drvset:
            o.is_holdout = True
            ncar += 1
        elif o.name in drvset:
            o.is_holdout = False
    log("%d car meshes set to holdout; the alpha channel is now the driver mask"
        % ncar)
    if a.control_displace:
        log("POSITIVE CONTROL: displacing the driver %+.3f m in +y" % a.control_displace)
        for o in drv:
            o.location.y += a.control_displace

    # aperture volume, measured -- CI_seal's own extent, from the rim up to
    # clear above the helmet crown.
    def bounds(name):
        ob = bpy.data.objects[name]
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg); me = ev.to_mesh()
        M = root.matrix_world.inverted() @ ob.matrix_world
        P = np.array([list(M @ v.co) for v in me.vertices])
        ev.to_mesh_clear()
        return P.min(0), P.max(0)
    bpy.context.scene.frame_set(1200)
    bpy.context.view_layer.update()
    slo, shi = bounds("CI_seal")
    hlo, hhi = bounds("CI_sidehead")
    m_lo = np.array([min(slo[0], hlo[0]), min(slo[1], hlo[1]), float(slo[2])])
    m_hi = np.array([max(shi[0], hhi[0]), max(shi[1], hhi[1]), float(shi[2]) + 0.20])
    log("aperture volume (CAR_ROOT-local) %s .. %s"
        % (np.round(m_lo, 4).tolist(), np.round(m_hi, 4).tolist()))

    cam, _ = film_camera(a.path, a.frames[0])
    rows = []
    ok_all = True
    for f in a.frames:
        d = json.load(open(a.path))["path"][f - 1]
        cam.location = Vector(d["p"])
        cam.rotation_quaternion = Quaternion(d["q"])
        cam.data.lens = float(d["lens"])
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()

        for o in drv:
            o.hide_render = True
        m0 = render_mask(cam, f, os.path.join(a.outdir, "mask_f%04d_nodrv.png" % f))
        for o in drv:
            o.hide_render = shown[o.name]
        m = render_mask(cam, f, os.path.join(a.outdir, "mask_f%04d_drv.png" % f))

        n0 = int(m0.sum())
        n1 = int(m.sum())
        hull = aperture_hull(root, cam, m_lo, m_hi)
        ys, xs = np.nonzero(m)
        if hull is None:
            inside = np.zeros(len(xs), bool)
            nout = len(xs)
        else:
            inside = inside_hull(xs.astype(float), ys.astype(float), hull, a.margin)
            nout = int((~inside).sum())
        bbox = [int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())] if n1 else None
        # the NEGATIVE control and the presence check, in one line
        # The NEGATIVE control is per frame: with the driver hidden the mask
        # must be empty.  PRESENCE is NOT a per-frame gate -- at frame 1200 the
        # camera is not on the car at all and 0 driver pixels is the correct
        # answer -- but at least one frame in the run must show a large driver,
        # or the whole instrument could be reading nothing.  That is checked
        # once, over the run, below.
        neg_ok = (n0 == 0)
        present = (n1 > 2000)
        contained = (nout == 0)
        rows.append(dict(frame=f, driver_px=n1, driver_px_without=n0,
                         outside_aperture_px=nout, bbox=bbox,
                         hull=None if hull is None else hull.tolist(),
                         negative_control_ok=neg_ok, present=present,
                         contained=contained))
        log("f%-5d driver px %8d (absent-run %d)  outside aperture %6d  bbox %s  %s"
            % (f, n1, n0, nout, bbox,
               "OK" if (neg_ok and contained) else "FAIL"))
        ok_all &= (neg_ok and contained)

    live = max(r["driver_px"] for r in rows)
    log("instrument live-check: the largest driver mask over %d frames is "
        "%d px (need > 2000, or this gate measured nothing)" % (len(rows), live))
    ok_all &= (live > 2000)
    rep = dict(frames=rows, margin_px=a.margin, largest_driver_px=live,
               aperture_volume=[m_lo.tolist(), m_hi.tolist()],
               control_displace=a.control_displace)
    json.dump(rep, open(a.report, "w"), indent=1)
    if a.control_displace:
        # the POSITIVE control inverts the verdict: it must FAIL
        print("STAGE RESULT: %s (positive control: displaced driver %s)"
              % ("OK" if not ok_all else "FAIL -- the gate is BLIND, it passed a "
                 "driver shoved through the side of the car",
                 "escaped as required" if not ok_all else "was not caught"))
        return 0 if not ok_all else 1
    print("STAGE RESULT: %s" % ("OK" if ok_all else "FAIL"))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
